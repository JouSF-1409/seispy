import numpy as np
from numpy import pi, mod
from seispy import distaz
import math

def sind(deg):
    rad = math.radians(deg)
    return math.sin(rad)

def cosd(deg):
    rad = math.radians(deg)
    return math.cos(rad)

def tand(deg):
    rad = math.radians(deg)
    return math.tan(rad)

def cotd(deg):
    rad = math.radians(deg)
    return math.cos(rad) / math.sin(rad)

def asind(x):
    rad = math.asin(x)
    return math.degrees(rad)

def acosd(x):
    rad = math.acos(x)
    return math.degrees(rad)

def atand(x):
    rad = math.atan(x)
    return math.degrees(rad)

def km2deg(km):
    radius = 6371
    circum = 2*pi*radius
    conv = circum / 360
    deg = km / conv
    return deg

def deg2km(deg):
    radius = 6371
    circum = 2*pi*radius
    conv = circum / 360
    km = deg * conv
    return km

def rad2deg(rad):
    deg = rad*(360/(2*pi))
    return deg

def skm2sdeg(skm):
    sdeg = skm * deg2km(1)
    return sdeg

def sdeg2skm(sdeg):
    skm = sdeg / deg2km(1)
    return skm

def srad2skm(srad):
    sdeg = srad * ((2*pi)/360)
    return sdeg / deg2km(1)

def rotateSeisENZtoTRZ( E, N, Z, BAZ ):
    angle = mod(BAZ+180, 360)
    R = N*distaz.cosd(angle) + E*distaz.sind(angle)
    T = E*distaz.cosd(angle) - N*distaz.sind(angle)
    return R, T, Z

def rssq(x):
    return np.sqrt(np.sum(np.abs(x)**2))

def snr(x, y):
    spow = rssq(x)**2
    npow = rssq(y)**2
    return 10 * np.log10(spow / npow)

def latlon_from(lat1,lon1,azimuth,gcarc_dist):
    lat2 = asind ((sind (lat1) * cosd (gcarc_dist)) + (cosd (lat1) * sind (gcarc_dist) * cosd (azimuth)))
    if ( cosd (gcarc_dist) >= (cosd (90 - lat1) * cosd (90 - lat2))):
        lon2 = lon1 + asind (sind (gcarc_dist) * sind (azimuth) / cosd (lat2))
    else:
        lon2 = lon1 + asind (sind (gcarc_dist) * sind (azimuth) / cosd (lat2)) + 180
    return lat2, lon2

