from os.path import exists, join, dirname

import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d

from seispy.utils import vs2vprho


def _search_vel_file(mode_name):
    """
    search vel file given by mode_name
        and try to open it with np.loadtxt:

    1. precise name of vel mod file
    2. default vel mod (containing iasp01
        default vel mod stored in seispy/data/modname.vel file

    do basic value evaluation, cal rho if not given in files
    Parameters
    ----------
    mode_name

    Returns
    ----------
    model matrix [layers:4]:
    depth   vp   vs   rho
    ....    ...  ...  ....
    """
    if not isinstance(mode_name, str):
        raise TypeError('velmod should be in str type')
    if exists(mode_name):
        filename = mode_name
    ## if not found, search in default vel model fold
    elif exists(join(dirname(__file__), '../data', mode_name.lower() + '.vel')):
        filename = join(dirname(__file__), '../data', mode_name.lower() + '.vel')
    else:
        raise ValueError('No such file of velocity model')

    try:
        raw_model = np.loadtxt(filename)
    except:
        raise IOError
    # check cols of file
    if raw_model.shape[1] < 3 or raw_model.shape[1] > 4:
        raise ValueError

    # cal rho if rho is not given in vel files.
    if raw_model.shape[1] == 3:
        model = np.zeros((raw_model.shape[0], 4))
        model[:3, :] = raw_model[:, :]
        _p, rho = vs2vprho(raw_model[:, 2])
        model[3, :] = rho

        return model
    else:
        return raw_model


def _layer2grid(dep_range, model):
    """
    trans model from layer_model to layer_grid

    leave stuffing and interp 2 discretize

    dep_range : grids at depth axis, np.ndarray
    h : thichness of each layer
    vp, vs, rho

    Returns
    -------

    """

    neo_model = np.zeros((len(dep_range), 4)).astype(float)
    # vp_dep = np.zeros_like(dep_range).astype(float)
    # vs_dep = np.zeros_like(dep_range).astype(float)
    # rho_dep = np.zeros_like(dep_range).astype(float)

    picks = np.searchsorted(model[:, 0], dep_range, side="left")
    for _i, _j in enumerate(picks):
        neo_model[_i, :] = model[_j, :]
    # return vp_dep, vs_dep, rho_dep
    return neo_model[:, 1], neo_model[:, 2], neo_model[:, 3]

def _intep_mod(model, depths_elev):
    vp = interp1d(model[:,0], model[:,1], bounds_error=False,
                       fill_value=model[0,1])(depths_elev)
    vs = interp1d(model[:,0], model[:,2], bounds_error=False,
                       fill_value=model[0,2])(depths_elev)
    rho = interp1d(model[:,0], model[:,3], bounds_error=False,
                        fill_value=model[0,3])(depths_elev)

    return vp, vs, rho


class DepModel(object):
    """
    radiu_s is used to call piercing point
    tps,tpsps or so are used to cal displacement

    examples:
    >>> model = DepModel(np.array([0, 20.1, 35.1, 100]))
    >>> print(model.dz)
    [ 0.  20.1 15.  64.9]
    >>> print(model.vp)
    [5.8        6.5        8.04001059 8.04764706]
    >>> print(model.vs)
    [3.36       3.75       4.47003177 4.49294118]
    """

    def __init__(self, dep_range, velmod='iasp91', elevation=0., layer_mod=False):
        """Class for computing back projection of Ps Ray paths.

        Parameters
        ----------
        dep_range : numpy.ndarray
            Depth range for conversion
            Depth for each layer, not thickness
        velmod : str, optional
            Text file of 1D velocity model with first 3 columns of depth/thickness, Vp and Vs,
            by default 'iasp91'
        elevation : float, optional Elevation in km, by default 0.0
        layer_mod: True for search, and False for interp1d
        """
        self.isrho = False
        self.elevation = elevation
        self.layer_mod = layer_mod
        # dep layer for CCP or other purpose, relative to sea level, dont contain any depth infomation
        self.depths = dep_range.astype(float)
        self.dep_val = np.average(np.diff(self.depths))

        try:
            self.model_array = _search_vel_file(velmod)
        except (IOError, ValueError):
            raise IOError(" failed while loading vel model {}".format(velmod))
        else:
            self._elevation()
            if layer_mod:
                self.vp, self.vs, self.rho = \
                    _layer2grid(self.depths, self.model_array)
            else:
                self.vp, self.vs, self.rho = \
                    _intep_mod(self.model_array, self.depths_elev)

    @classmethod
    def read_layer_model(cls, dep_range, h, vp, vs, rho=None, elevation=0):
        mod = cls(dep_range, velmod=None, layer_mod=True, elevation=elevation)
        return mod

    def _elevation(self):
        """
        set all depth related values:
        1. depths_elev: depth array contains layer above sea level(represent by value lower than 0
        2. depths_extend: depth array contains layer above sea level( evaluate from 0 to original depth
        3. dz: 0, thick_1, thick_2....
        4. thickness: thick_1, thick_2, ... , 0
        requires elevation, depths_range or other component
        >>> model = DepModel(np.array([0, 20.1, 35.1, 100]))
        >>> model.depths_elev
        array([  0. ,  20.1,  35.1, 100. ])
        >>> model.depths_extend
        array([  0. ,  20.1,  35.1, 100. ])
        >>> model.dz
        array([ 0. , 20.1, 15. , 64.9])
        >>> model.thickness
        array([20.1, 15. , 64.9,  0. ])

        >>> model = DepModel(np.array([0, 20.1, 35.1, 100]),elevation=10.)
        >>> print(model.depths_elev)
        [-10.          10.1         25.1         90.         123.33333333]
        >>> print(model.depths_extend)
        [  0.          20.1         35.1        100.         133.33333333]
        >>> print(model.dz)
        [ 0.         20.1        15.         64.9        33.33333333]
        >>> print(model.thickness)
        [20.1        15.         64.9        33.33333333  0.        ]
        """
        if self.elevation == 0:
            self.depths_elev = self.depths
            self.depths_extend = self.depths
        else:


            depths_append = np.arange(self.depths[-1]+self.dep_val,
                               self.depths[-1]+self.dep_val+np.floor(self.elevation/self.dep_val+1), self.dep_val)

            self.depths_extend = np.append(self.depths, depths_append)
            self.depths_elev = np.append(self.depths, depths_append) - self.elevation


        self.dz = np.append(0, np.diff(self.depths_extend))
        self.thickness = np.append(np.diff(self.depths_extend), 0.)

        self.R = 6371.0 - self.depths_elev





    def plot_model(self, show=True):
        plt.style.use('bmh')
        if self.isrho:
            self.model_fig = plt.figure(figsize=(6, 6))
            fignum = 2
        else:
            self.model_fig = plt.figure(figsize=(4, 6))
            fignum = 1
        self.model_ax = self.model_fig.add_subplot(1, fignum, 1)
        self.model_ax.step(self.vp, self.depths, where='pre', label='Vp')
        self.model_ax.step(self.vs, self.depths, where='pre', label='Vs')
        self.model_ax.legend()
        self.model_ax.set_xlabel('Velocity (km/s)')
        self.model_ax.set_ylabel('Depth (km)')
        self.model_ax.set_ylim([self.depths[0], self.depths[-1]])
        self.model_ax.invert_yaxis()
        if self.isrho:
            self.rho_ax = self.model_fig.add_subplot(1, fignum, 2)
            self.rho_ax.step(self.rho, self.depths, where='pre', color='C2', label='Density')
            self.rho_ax.legend()
            self.rho_ax.set_xlabel('Density (km/s)')
            self.rho_ax.set_ylim([self.depths[0], self.depths[-1]])
            self.rho_ax.invert_yaxis()
        if show:
            plt.show()

    def tpds(self, rayps, raypp, sphere=True):
        if sphere:
            radius = self.R
        else:
            radius = 6371.
        tps = np.cumsum((np.sqrt((radius / self.vs) ** 2 - rayps ** 2) -
                         np.sqrt((radius / self.vp) ** 2 - raypp ** 2)) *
                        (self.dz / radius))
        return tps

    def tpppds(self, rayps, raypp, sphere=True):
        if sphere:
            radius = self.R
        else:
            radius = 6371.
        tps = np.cumsum((np.sqrt((radius / self.vs) ** 2 - rayps ** 2) +
                         np.sqrt((radius / self.vp) ** 2 - raypp ** 2)) *
                        (self.dz / radius))
        return tps

    def tpspds(self, rayps, sphere=True):
        if sphere:
            radius = self.R
        else:
            radius = 6371.
        tps = np.cumsum(2 * np.sqrt((radius / self.vs) ** 2 - rayps ** 2) *
                        (self.dz / radius))
        return tps

    def radius_s(self, rayp, phase='P', sphere=True):
        """
        calculate piercing point, P for Sp and S for Ps
        Parameters
        ----------
        rayp
        phase
        sphere

        Returns
        -------
        >>> model = DepModel(np.array([0, 20.1, 35.1, 100]))
        >>> model.dz
        array([ 0. , 20.1, 15. , 64.9])
        >>> model.R
        array([6371. , 6350.9, 6335.9, 6271. ])
        >>> model.radius_s(1.2,phase="S", sphere=False)*111.2
        array([0.        , 0.0002478 , 0.00046823, 0.00142685])


        """
        if phase == 'P':
            vel = self.vp
        else:
            vel = self.vs
        if sphere:
            radius = self.R
        else:
            radius = 6371.
        hor_dis = np.cumsum((self.dz / radius) / np.sqrt((1. / (rayp ** 2. * (radius / vel) ** -2)) - 1))
        #hor_dis = np.sqrt((1. / (rayp ** 2. * (radius / vel) ** -2)) - 1)
        return hor_dis

    def raylength(self, rayp, phase='P', sphere=True):
        if phase == 'P':
            vel = self.vp
        else:
            vel = self.vs
        if sphere:
            radius = self.R
        else:
            radius = 6371.
        raylen = (self.dz * radius) / (np.sqrt(((radius / self.vs) ** 2) - (rayp ** 2)) * vel)
        return raylen


if __name__ == "__main__":
    import doctest
    doctest.testmod()
