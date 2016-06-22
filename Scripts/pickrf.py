#!/usr/bin/env python
'''
This is a script to select receiver functions in GUI.
Usage:      python pickrf.py -Sstation_name para.cfg
Functions:  Click waveform to select good/bad RFs.
            Click "plotRF" to plot good RFs in a .ps file.
            Click "finish" to delete bad RFs and close the window.
'''

import matplotlib.pyplot as plt
import os, sys, glob, re, shutil
import obspy
import numpy as np
import getopt
from matplotlib.widgets import Button
from operator import itemgetter
import initopts
import plotrf
try:
    import configparser
    config = configparser.ConfigParser()
except:
    import ConfigParser
    config = ConfigParser.ConfigParser()

def Usage():
    print("Usage: python pickrf.py -S<station_name> para.cfg\n"
          "    -S<station> Specify station name as a directory name in specified \"RF_path\"\n"
          "                in \"para.cfg\"")
    print("     para.cfg The configuration file including out_path (the path of cut out data),\n"
          "              RF_path (the path of receiver functions), image_path (the path of out figure)")

def get_sac():
    if  sys.argv[1:] == []:
        Usage()
        sys.exit(1)
    for o in sys.argv[1:]:
        if os.path.isfile(o):
            head = o
            break
    try:
        opts, args = getopt.getopt(sys.argv[1:], "S:h")
    except:
        print("invalid argument")
        sys.exit(1)
    for op, value in opts:
        if op == "-S":
            staname = value
        elif op == "-h":
            Usage()
            sys.exit(1)
        else:
            print("invalid argument")
            sys.exit(1)
    config.read(head)
    image_path = config.get('path', 'image_path')
    path = config.get('path', 'RF_path')
    cut_path = config.get('path', 'out_path')
    path = os.path.join(path, staname)
    cut_path = os.path.join(cut_path, staname)
    files = glob.glob(os.path.join(path, '*_R.sac'))
    filenames = [re.match('\d{4}\D\d{3}\D\d{2}\D\d{2}\D\d{2}', os.path.basename(fl)).group() for fl in files]
    filenames.sort()
    rffiles = obspy.read(os.path.join(path, '*_R.sac'))
    trffiles = obspy.read(os.path.join(path, '*_T.sac'))
    return rffiles.sort(['starttime']), trffiles.sort(['starttime']), filenames, path, image_path, cut_path, staname

def indexpags(maxidx, evt_num):
    axpages = int(np.floor(evt_num/maxidx)+1)
    print('A total of '+str(evt_num)+' PRFs')
    rfidx = []
    for i in range(axpages-1):
        rfidx.append(range(maxidx*i, maxidx*(i+1)))
    rfidx.append(range(maxidx*(axpages-1), evt_num))
    return axpages, rfidx

class plotrffig():    
    fig = plt.figure(figsize=(20, 11), dpi=60)
    axnext = plt.axes([0.81, 0.91, 0.07, 0.03])
    axprevious = plt.axes([0.71, 0.91, 0.07, 0.03])
    axfinish = plt.axes([0.91, 0.91, 0.07, 0.03])
    axenlarge = plt.axes([0.15, 0.91, 0.07, 0.03])
    axreduce = plt.axes([0.25, 0.91, 0.07, 0.03])
    axPlot = plt.axes([0.028, 0.91, 0.07, 0.03])
    ax = plt.axes([0.1, 0.05, 0.35, 0.84])
    axt = plt.axes([0.47, 0.05, 0.35, 0.84])
    ax_baz = plt.axes([0.855, 0.05, 0.12, 0.84])
    ax.grid()
    axt.grid()
    ax_baz.grid()
    ax.set_ylabel("Event", fontsize=20)
    ax.set_xlabel("Time after P (s)")
    ax.set_title("R component")
    axt.set_xlabel("Time after P (s)")
    axt.set_title("T component")
    ax_baz.set_xlabel("Backazimuth (\N{DEGREE SIGN})")
    bnext = Button(axnext, 'Next')
    bprevious = Button(axprevious, 'Previous')
    bfinish = Button(axfinish, 'Finish')
    bplot = Button(axPlot, 'Plot RFs')
    benlarge = Button(axenlarge, 'Amp enlarge')
    breduce = Button(axreduce, 'Amp reduce')

    def __init__(self, opts):
        self.opts = opts
        ax = self.ax
        axt = self.axt
        ax_baz = self.ax_baz
        axpages, rfidx = indexpags(opts.maxidx, opts.evt_num)
        self.axpages = axpages
        self.rfidx = rfidx
        self.ipage = 0
        self.goodrf = np.ones(opts.evt_num)
        self.lines = [[] for i in range(opts.evt_num)]
        self.tlines = [[] for i in range(opts.evt_num)]
        self.wvfillpos = [[] for i in range(opts.evt_num)]
        self.wvfillnag = [[] for i in range(opts.evt_num)]
        self.twvfillpos = [[] for i in range(opts.evt_num)]
        self.twvfillnag = [[] for i in range(opts.evt_num)]
        self.plotwave()
        self.plotbaz()
        self.fig.suptitle("%s (Latitude: %5.2f\N{DEGREE SIGN}, Longitude: %5.2f\N{DEGREE SIGN})" % (opts.staname, opts.stla, opts.stlo), fontsize=20)
        ax.set_ylim(rfidx[self.ipage][0], rfidx[self.ipage][-1]+2)
        ax.set_yticks(np.arange(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2))
        ylabels = opts.filenames[rfidx[self.ipage][0]::]
        ylabels.insert(0, '')
        ax.set_yticklabels(ylabels)
        axt.set_ylim(ax.get_ylim())
        axt.set_yticks(ax.get_yticks())
        ax_baz.set_ylim(ax.get_ylim())
        ax_baz.set_yticks(ax.get_yticks())
        self.azi_label = ['%5.2f' % opts.baz[i] for i in rfidx[self.ipage]]
        self.azi_label.insert(0, "")
        ax_baz.set_yticklabels(self.azi_label)
        self.bnext.on_clicked(self.butnext)
        self.bprevious.on_clicked(self.butprevious)
        self.bfinish.on_clicked(self.finish)
        self.bplot.on_clicked(self.plot)
        self.benlarge.on_clicked(self.enlarge)
        self.breduce.on_clicked(self.reduce)
        self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        ax.plot([0, 0], [0, axpages*opts.maxidx], color="black")
        axt.plot([0, 0], [0, axpages*opts.maxidx], color="black")
        ax.set_xlim(opts.xlim[0], opts.xlim[1])
        ax.set_xticks(np.arange(opts.xlim[0], opts.xlim[1]+1, 2))
        axt.set_xlim(opts.xlim[0], opts.xlim[1])
        axt.set_xticks(np.arange(opts.xlim[0], opts.xlim[1]+1, 2))
        ax_baz.set_xlim(0, 360)
        ax_baz.set_xticks(np.arange(0, 361, 60))

    def finish(self, event):
        opts = self.opts
        badidx = np.where(self.goodrf == 0)[0]
        print("%d RFs are rejected" % len(badidx))
        with open(os.path.join(opts.path, opts.staname+"finallist.dat"), 'w+') as fid:
            for i in range(opts.evt_num):
                evtname = os.path.basename(opts.filenames[i])
                evtname = re.split('[_|.]\w[_|.]',evtname)[0]
                if self.goodrf[i] == 0:
                    os.system("rm -f %s" % os.path.join(opts.path, evtname+'*.sac'))
                    os.system("rm -f %s" % os.path.join(opts.cut_path, evtname+'*.SAC'))
                    print("Reject PRF of "+evtname)
                    continue
                evla = opts.rffiles[i].stats.sac.evla
                evlo = opts.rffiles[i].stats.sac.evlo
                evdp = opts.rffiles[i].stats.sac.evdp
                dist = opts.rffiles[i].stats.sac.gcarc
                baz = opts.rffiles[i].stats.sac.baz
                rayp = opts.rffiles[i].stats.sac.user0
                mag = opts.rffiles[i].stats.sac.mag
                gauss = opts.rffiles[i].stats.sac.user1
                fid.write('%s %s %6.3f %6.3f %6.3f %6.3f %6.3f %8.7f %6.3f %6.3f\n' % (evtname, 'P', evla, evlo, evdp, dist, baz, rayp, mag, gauss))
        shutil.copy(os.path.join(opts.path, opts.staname+"finallist.dat"), os.path.join(opts.cut_path, opts.staname+"finallist.dat"))
        sys.exit(0)

    def onclick(self, event):
        if event.inaxes != self.ax and event.inaxes != self.axt:
            return
        click_idx = int(np.round(event.ydata))
        if click_idx > self.opts.evt_num:
            return
        if self.goodrf[click_idx-1] == 1:
            print("Selected "+os.path.basename(self.opts.filenames[click_idx-1]))
            self.goodrf[click_idx-1] = 0
            self.wvfillpos[click_idx-1].set_facecolor('gray')
            self.wvfillnag[click_idx-1].set_facecolor('gray')
            self.twvfillpos[click_idx-1].set_facecolor('gray')
            self.twvfillnag[click_idx-1].set_facecolor('gray')
        else:
            print("Canceled "+os.path.basename(self.opts.filenames[click_idx-1]))
            self.goodrf[click_idx-1] = 1
            self.wvfillpos[click_idx-1].set_facecolor('red')
            self.wvfillnag[click_idx-1].set_facecolor('blue')
            self.twvfillpos[click_idx-1].set_facecolor('red')
            self.twvfillnag[click_idx-1].set_facecolor('blue')
        plt.draw()

    def plotwave(self):
        ax = self.ax
        axt = self.axt
        opts = self.opts
        bound = np.zeros(opts.RFlength)
        time_axis = np.linspace(opts.b, opts.e, opts.RFlength)
        for i in range(opts.evt_num):
            rrf = opts.rffiles[i]
            trf = opts.trffiles[i]
            r_amp_axis = rrf.data*opts.enf+i+1
            t_amp_axis = trf.data*opts.enf+i+1
            self.lines[i], = ax.plot(time_axis, r_amp_axis, color="black", linewidth=0.2)            
            self.tlines[i], = axt.plot(time_axis, t_amp_axis, color="black", linewidth=0.2)
            self.wvfillpos[i] = ax.fill_between(time_axis, r_amp_axis, bound+i+1, where=r_amp_axis >i+1, facecolor='red', alpha=0.3)
            self.wvfillnag[i] = ax.fill_between(time_axis, r_amp_axis, bound+i+1, where=r_amp_axis <i+1, facecolor='blue', alpha=0.3)
            self.twvfillpos[i] = axt.fill_between(time_axis, t_amp_axis, bound+i+1, where=t_amp_axis >i+1, facecolor='red', alpha=0.3)
            self.twvfillnag[i] = axt.fill_between(time_axis, t_amp_axis, bound+i+1, where=t_amp_axis <i+1, facecolor='blue', alpha=0.3)

    def plotbaz(self):
        self.ax_baz.scatter(self.opts.baz, np.arange(self.opts.evt_num)+1)
    
    def plot(self, event):
        opts = self.opts
        rst = opts.rffiles.copy()
        tst = opts.trffiles.copy()
        filenames = opts.filenames.copy()
        print('Plotting Figure of '+opts.staname)
        for i in range(opts.evt_num):
            if self.goodrf[i] == 0:
                filenames.remove(opts.filenames[i])
                rst.remove(opts.rffiles[i])
                tst.remove(opts.trffiles[i])
        plotrf.plot_RT(rst, tst, filenames, opts.image_path, opts.staname)
        print("Figure has saved into %s" % opts.image_path)
        if sys.platform == 'darwin':
            os.system('open %s' % os.path.join(opts.image_path, opts.staname+'_RT.ps'))
        elif sys.platform == 'linux':
            os.system('xdg-open %s' % os.path.join(opts.image_path, opts.staname+'_RT.ps'))
        else:
            print('Cannot open the .ps file')
            return

        
    def butprevious(self, event):
        opts = self.opts
        ax = self.ax
        axt = self.axt
        ax_baz = self.ax_baz
        self.ipage -= 1
        if self.ipage < 0:
            self.ipage = 0
            return
        ax.set_ylim(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2)
        ax.set_yticks(np.arange(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2))
        ylabels = opts.filenames[self.rfidx[self.ipage][0]::]
        ylabels.insert(0, '')
        ax.set_yticklabels(ylabels)
        axt.set_ylim(ax.get_ylim())
        axt.set_yticks(ax.get_yticks())
        ax_baz.set_ylim(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2)
        ax_baz.set_yticks(ax.get_yticks())
        self.azi_label = ['%5.2f' % opts.baz[i] for i in self.rfidx[self.ipage]]
        self.azi_label.insert(0, "")
        ax_baz.set_yticklabels(self.azi_label)
        plt.draw()

    def butnext(self, event):
        opts = self.opts
        ax = self.ax
        axt = self.axt
        ax_baz = self.ax_baz
        self.ipage += 1
        if self.ipage >= self.axpages:
            self.ipage = self.axpages-1
            return
        if self.ipage == self.axpages-1:
            ymax = (self.ipage+1)*opts.maxidx
            ax.set_ylim(self.rfidx[self.ipage][0], ymax)
            ax.set_yticks(np.arange(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2))
            ylabels = opts.filenames[self.rfidx[self.ipage][0]::]
            ylabels.insert(0, '')
            ax.set_yticklabels(ylabels)
            self.azi_label = ['%5.2f' % opts.baz[i] for i in self.rfidx[self.ipage]]
        else:
            ax.set_ylim(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2)
            ax.set_yticks(np.arange(self.rfidx[self.ipage][0], self.rfidx[self.ipage][-1]+2))
            ylabels = opts.filenames[self.rfidx[self.ipage][0]::]
            ylabels.insert(0, '')
            ax.set_yticklabels(ylabels)
            self.azi_label = ['%5.2f' % opts.baz[i] for i in self.rfidx[self.ipage]]
        axt.set_ylim(ax.get_ylim())
        axt.set_yticks(ax.get_yticks())
        ax_baz.set_ylim(ax.get_ylim())
        self.azi_label.insert(0, "")
        ax_baz.set_yticklabels(self.azi_label)
        ax_baz.set_yticks(ax.get_yticks())
        plt.draw()

    def enlarge(self, event):
        ylim = self.ax.get_ylim()
        ytick_R = self.ax.get_yticks()
        ytick_T = self.axt.get_yticks()
        xlim = self.ax.get_xlim()
        xtick = self.ax.get_xticks()
        xlabel = self.ax.get_xlabel()
        ylabel_R = self.ax.get_ylabel()
        yticklabel_R = self.ax.get_yticklabels()
        title_R = self.ax.get_title()
        title_T = self.axt.get_title()
        self.ax.cla()
        self.axt.cla()
        self.opts.enf += 1
        self.plotwave()
        self.ax.set_title(title_R)
        self.ax.set_xlim(xlim)
        self.ax.set_xticks(xtick)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylim(ylim)
        self.ax.set_yticks(ytick_R)
        self.ax.set_yticklabels(yticklabel_R)
        self.ax.set_ylabel(ylabel_R)
        self.axt.set_title(title_T)
        self.axt.set_xlim(xlim)
        self.axt.set_xticks(xtick)
        self.axt.set_xlabel(xlabel)
        self.axt.set_ylim(ylim)
        self.axt.set_yticks(ytick_T)
        self.ax.grid()
        self.axt.grid()
        plt.draw()

    def reduce(self, event):
        ylim = self.ax.get_ylim()
        ytick_R = self.ax.get_yticks()
        ytick_T = self.axt.get_yticks()
        xlim = self.ax.get_xlim()
        xtick = self.ax.get_xticks()
        xlabel = self.ax.get_xlabel()
        ylabel_R = self.ax.get_ylabel()
        yticklabel_R = self.ax.get_yticklabels()
        title_R = self.ax.get_title()
        title_T = self.axt.get_title()
        self.ax.cla()
        self.axt.cla()
        if self.opts.enf > 1:
            self.opts.enf -= 1
        else:
            self.opts.enf = 1/(1/self.opts.enf + 1)
        self.plotwave()
        self.ax.set_title(title_R)
        self.ax.set_xlim(xlim)
        self.ax.set_xticks(xtick)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylim(ylim)
        self.ax.set_yticks(ytick_R)
        self.ax.set_yticklabels(yticklabel_R)
        self.ax.set_ylabel(ylabel_R)
        self.axt.set_title(title_T)
        self.axt.set_xlim(xlim)
        self.axt.set_xticks(xtick)
        self.axt.set_xlabel(xlabel)
        self.axt.set_ylim(ylim)
        self.axt.set_yticks(ytick_T)
        self.ax.grid()
        self.axt.grid()
        plt.draw()

def main():
    opts = initopts.opts()
    opts.maxidx = 20
    opts.enf = 5
    opts.xlim = [-2, 30]
    opts.ylim = [0, 22]
    opts.rffiles, opts.trffiles, opts.filenames, opts.path, opts.image_path, opts.cut_path, opts.staname = get_sac()
    opts.evt_num = len(opts.rffiles)
    rf = opts.rffiles[0]
    opts.b = rf.stats.sac.b
    opts.e = rf.stats.sac.e
    opts.stla = rf.stats.sac.stla
    opts.stlo = rf.stats.sac.stlo
    opts.RFlength = rf.data.shape[0]
    bazi = [tr.stats.sac.baz for tr in opts.rffiles]
    tmp_filenames = [[opts.filenames[i], bazi[i]] for i in range(opts.evt_num)]
    tmp_filenames = sorted(tmp_filenames, key=itemgetter(1))
    opts.filenames = [file[0] for file in tmp_filenames]
    opts.baz = np.sort(bazi)
    opts.idx_bazi = np.argsort(bazi)
    opts.rffiles = [opts.rffiles[i] for i in opts.idx_bazi]
    opts.trffiles = [opts.trffiles[i] for i in opts.idx_bazi]
    plotrffig(opts)


if __name__ == "__main__":
    main()
    plt.show()
