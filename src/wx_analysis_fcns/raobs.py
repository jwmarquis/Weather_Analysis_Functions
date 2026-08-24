#!/usr/bin/env python

import numpy as np
import requests
import gzip
import shutil
from netCDF4 import Dataset
import xarray as xr
from datetime import datetime, timedelta
import metpy.calc as mpcalc


def get_raobs(dt: datetime = datetime.utcnow().replace(microsecond=0,second=0,minute=0), pres_lev):
    del_t = datetime.now() - dt
    del_t_days = del_t.days + (del_t.seconds/60/60/24)
    #get data from MADIS
    if del_t_days>:
        base_url = 'https://madis-data.cprk.ncep.noaa.gov/madisPublic1/data/archive/'
        url = f'{base_url}{dt:%Y}/{dt:%m}/{dt:%d}/point/raob/netcdf/{dt:%Y%m%d_%H%M}.gz'
    else:
        base_url = 'https://madis-data.cprk.ncep.noaa.gov/madisPublic1/data/point/raob/netcdf/'
        url = f'{base_url}{dt:%Y%m%d_%H%M}.gz'
        
    r = requests.get(url,allow_redirects=True)
    open('temp.nc.gz','wb').write(r.content)
    with gzip.open('temp.nc.gz','rb') as f_in:
        with open('temp.nc','wb') as f_out:
            shutil.copyfileobj(f_in,f_out)
    data=Dataset('temp.nc','r')

    #read data
    lat = data['staLat'][:]
    lat = lat.filled(np.nan)
    lon = data['staLon'][:]
    lon = lon.filled(np.nan)
    to_drop = np.where((np.isnan(lat) | np.isnan(lon)))
    lat = lat[~to_drop]
    lon = lon[~to_drop]
    pres = data['prMan'][:]
    pres = pres.filled(np.nan)
    pres = pres[~to_drop]
    hght = data['htMan'][:]
    hght = hght.filled(np.nan)
    hght = hght[~to_drop]
    temp = data['tpMan'][:]
    temp = temp.filled(np.nan)
    temp[temp<100]=np.nan
    temp = (temp-273.15)
    temp = temp[~to_drop]
    dwptdp = data['tdMan'][:]
    dwptdp = dwptdp.filled(np.nan)
    dwptdp[dwptdp<100]=np.nan
    dwptdp = (dwptdp-273.15)
    dwptdp = dwptdp[~to_drop]
    wdir = data['wdMan'][:]
    wdir = wdir.filled(np.nan)
    wdir[wdir<0] = np.nan
    wdir = wdir[~to_drop]
    wspd = data['wsMan'][:]
    wspd = wspd.filled(np.nan)
    wspd[wspd>250] = np.nan
    wspd = wspd[~to_drop]

    name = data['staName'][:]
    name = name[~to_drop]
    name = [i.tostring().decode()[:4] for i in name]
    u,v = mpcalc.wind_components((wspd*units('m/s')).to('knots'),wdir*units.degree)

    #create xarray dataset
    ds = xr.Dataset(
        coords=dict(
            id=(['id'],name)
            ),
        data_vars=dict(
            lon=(['id'],lon),
            lat=(['id'],lat),
            pressure=(['id','pres'],pres),
            height=(['id','pres'],hght),
            temperature=(['id','pres'],temp),
            dwptdp=(['id','pres'],dwptdp),
            u=(['id','pres'],u),
            v=(['id','pres'],v)
            )
    )
    return(ds)