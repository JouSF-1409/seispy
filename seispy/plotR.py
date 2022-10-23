import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
import numpy as np
from os.path import join


def init_figure():
    h = plt.figure(figsize=(8, 10))
    gs = GridSpec(15, 3)
    gs.update(wspace=0.25)
    axr = plt.subplot(gs[1:, 0:-1])
    axr.grid(color='gray', linestyle='--', linewidth=0.4, axis='x')
    axb = plt.subplot(gs[1:, -1])
    axb.grid(color='gray', linestyle='--', linewidth=0.4, axis='x')
    axs = plt.subplot(gs[0, 0:-1])
    axs.grid(color='gray', linestyle='--', linewidth=0.4, axis='x')
    return h, axr, axb, axs


def plot_waves(axr, axb, axs, stadata, enf=12):
    bound = np.zeros(stadata.rflength)
    for i in range(stadata.ev_num):
        datar = stadata.datar[i] * enf + (i + 1)
        # axr.plot(time_axis, stadata.datar[i], linewidth=0.2, color='black')
        axr.fill_between(stadata.time_axis, datar, bound + i+1, where=datar > i+1, facecolor='red',
                         alpha=0.7)
        axr.fill_between(stadata.time_axis, datar, bound + i+1, where=datar < i+1, facecolor='blue',
                         alpha=0.7)
    # rfsum, _ = moveoutcorrect_ref(stadata, 0.06, np.arange(300), sphere=False)
    rfsum = np.mean(stadata.datar, axis=0)
    axs.fill_between(stadata.time_axis, rfsum, 0, where=rfsum > 0, facecolor='red', alpha=0.7)
    axs.fill_between(stadata.time_axis, rfsum, 0, where=rfsum < 0, facecolor='blue', alpha=0.7)
    axs.plot(stadata.time_axis, rfsum, color='gray', lw=0.5)
    axb.scatter(stadata.bazi, np.arange(stadata.ev_num) + 1, s=7)
    # axp = axb.twiny()
    # axp.scatter(stadata.rayp, np.arange(stadata.ev_num) + 1, s=7)
    # return axp

def set_fig(axr, axb, axs, stadata, xmin=-2, xmax=80):
    y_range = np.arange(stadata.ev_num) + 1
    x_range = np.arange(0, xmax+2, 5)
    space = 2

    # set axr
    axr.set_xlim(xmin, xmax)
    axr.set_xticks(x_range)
    axr.set_xticklabels(x_range, fontsize=8)
    axr.set_ylim(0, stadata.ev_num + space)
    axr.set_yticks(y_range)
    axr.set_yticklabels(stadata.event, fontsize=5)
    axr.set_xlabel('Time after P (s)', fontsize=13)
    axr.set_ylabel('Event', fontsize=13)
    axr.add_line(Line2D([0, 0], axr.get_ylim(), color='black'))
    axr.set_title('R components ({})'.format(stadata.staname), fontsize=16)

    # set axb
    axb.set_xlim(0, 360)
    axb.set_xticks(np.linspace(0, 360, 7))
    axb.set_xticklabels(np.linspace(0, 360, 7, dtype='i'), fontsize=8)
    axb.set_ylim(0, stadata.ev_num + space)
    axb.set_yticks(y_range)
    axb.set_yticklabels(y_range, fontsize=5)
    axb.set_xlabel(r'Back-azimuth ($^\circ$)', fontsize=13)
    # axp.set_xlabel('Ray-parameter (s/km)', fontsize=13)

    axs.set_xlim(xmin, xmax)
    axs.set_xticks(x_range)
    axs.set_xticklabels([])


def plotr(rfsta, out_path='./', xlim=[-2, 80], key='bazi', enf=6, outformat='g', show=False):
    h, axr, axb, axs = init_figure()
    rfsta.sort(key)
    plot_waves(axr, axb, axs, rfsta, enf=enf)
    set_fig(axr, axb, axs, rfsta, xlim[0], xlim[1])
    if outformat is None and not show:
        return h
    elif outformat == 'g':
        h.savefig(join(out_path, rfsta.staname+'_R_{}order_{:.1f}.png'.format(key, rfsta.f0[0])),
                       dpi=400, bbox_inches='tight')
    elif outformat == 'f':
        h.savefig(join(out_path, rfsta.staname+'_R_{}order_{:.1f}.pdf'.format(key, rfsta.f0[0])),
                       format='pdf', bbox_inches='tight')
    if show:
        plt.show()
        return h


if __name__ == '__main__':
    pass