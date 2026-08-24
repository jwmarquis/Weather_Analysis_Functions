#!/usr/bin/env python

import matplotlib.colors
import numpy as np

colors_ws = [(0.000, '#FFFFFF'),
             (0.083, '#87CEFA'),
             (0.166, '#6A5ACD'),
             (0.250, '#E696DC'),
             (0.333, '#C85ABE'),
             (0.416, '#A01496'),
             (0.500, '#C80028'),
             (0.583, '#DC283C'),
             (0.666, '#F05050'),
             (0.750, '#FAF064'),
             (0.833, '#DCBE46'),
             (0.916, '#BE8C28'),
             (1.000, '#A05A0A')]

cmap_ws = matplotlib.colors.LinearSegmentedColormap.from_list("windspeed",colors_ws,N=120)
ws_range_925 = np.arange(20,81,1)
ws_label_925 = np.arange(20,81,5)
ws_range_850 = np.arange(20,81,1)
ws_label_850 = np.arange(20,81,5)
ws_range_700 = np.arange(20,81,1)
ws_label_700 = np.arange(20,81,5)
ws_range_500 = np.arange(20,141,1)
ws_label_500 = np.arange(20,141,10)
ws_range_300 = np.arange(50,171,1)
ws_label_300 = np.arange(50,171,10)



colors_temp = [(0.000, '#B3ECE0'),
               (0.125, '#A08AC6'),
               (0.250, '#8C28AC'),
               (0.375, '#D4E2E8'),
               (0.4999,'#1450B4'),
               (0.500,'#0F505F'),
               (0.625, '#F3F2A7'),
               (0.750, '#A56847'),
               (0.875, '#690B10'),
               (1.000, '#E8DFD6')]

cmap_temp = matplotlib.colors.LinearSegmentedColormap.from_list("temps",colors_temp,N=80)
temp_range_925 = np.arange(-40,41,1)
temp_label_925 = np.arange(-40,41,5)
temp_range_850 = np.arange(-40,41,1)
temp_label_850 = np.arange(-40,41,5)
temp_range_700 = np.arange(-40,41,1)
temp_label_700 = np.arange(-40,41,5)
temp_range_500 = np.arange(-50,1,1)
temp_label_500 = np.arange(-50,1,5)



colors_vort = [(0.000, '#323232'),
               (0.256, '#ffffff'),
               (0.268, '#ffffa0'),
               (0.488, '#d92323'),
               (0.573, '#ad0097'),
               (0.756, '#090d68'),
               (1.000, '#91ffff')]
cmap_vort = matplotlib.colors.LinearSegmentedColormap.from_list("vorticity",colors_vort,N=102)
vort_range = np.arange(-20,61,2)
vort_label = np.arange(-20,61,5)


colors_theta = [(0.000, '#986d4d'),
                (0.288, '#4d4334'),
                (0.640, '#f4f2d7'),
                (0.647, '#c8eac8'),
                (0.784, '#084e08'),
                (0.791, '#61a3af'),
                (0.856, '#132c2b'),
                (0.863, '#66669a'),
                (0.928, '#2d1e64'),
                (0.935, '#724071'),
                (1.000, '#a37080')]

cmap_theta = matplotlib.colors.LinearSegmentedColormap.from_list('theta',colors_theta,N=139)
theta_range = np.arange(230,370,2)
theta_label = np.arange(230,370,10)