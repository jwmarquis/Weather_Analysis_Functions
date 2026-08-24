#!/usr/bin/env python

from herbie import Herbie
from datetime import datetime, timedelta
import xarray as xr
xr.set_options(use_new_combine_kwarg_defaults=True)
import numpy as np

GFS_START = datetime(2007,1,1,0)
RAP_AWS_START = datetime(2021,2,22,0)
NAM_AWS_START = datetime(2021,9,16,0)
HRRR_AWS_START = datetime(2014,7,30,18)

GEFS_START = datetime(2007,1,1,0)


class DataAvailabilityError(RuntimeError):
    """Requested data are not available for the given date/model."""
    pass

def get_model_data(dt: datetime = datetime.utcnow().replace(microsecond=0,second=0,minute=0), model="gfs", fxx=0, bbox=[15,-170,75,-50], product=None, resolution=None):
    model = model.lower()
    #############
    #### GFS ####
    #############
    if model == "gfs":
        if dt < GFS_START:
            raise DataAvailabilityError(
                f"GFS is unavailable before {GFS_START:%Y-%m-%d}. "+
                f"Requested time: {dt:%Y-%m-%d %H:%M}."
            )
        if dt.year >= 2021:
            if product:
                pass
            elif resolution:
                product = 'pgrb2.0p25' if resolution<0.5 else 'pgrb2.0p50' if resolution<1.0 else 'pgrb2.1p00'
            else:
                product = 'pgrb2.0p25'
        else:
            if product:
                pass
            elif resolution:
                product = '0.5-degree' if resolution<1.0 else '1.0-degree'
            else:
                product = '0.5-degree'
        ds = read_gfs(dt, product, fxx, bbox)

    #############
    #### RAP ####
    #############
    if model == "rap":
        if dt < RAP_AWS_START:
            raise DataAvailabilityError(
                f"RAP is unavailable before {RAP_AWS_START:%Y-%m-%d}. "+
                f"Requested time: {dt:%Y-%m-%d %H:%M}."
            )
        if product:
            pass
        elif resolution:
            product = 'awp130pgrb' if resolution<20 else 'awp252pgrb' if resolution<40 else 'awp236pgrb'
        else:
            product = 'awp130pgrb'
        ds = read_rap(dt, product, fxx, bbox)

    #############
    #### NAM ####
    #############
    if model == "nam":
        if dt < NAM_AWS_START:
            raise DataAvailabilityError(
                f"NAM is unavailable before {NAM_AWS_START:%Y-%m-%d}. "+
                f"Requested time: {dt:%Y-%m-%d %H:%M}."
            )

        if product:
            pass
        elif resolution:
            product = 'conusnest.hiresf' if resolution<12 else 'awphys' if resolution<32 else 'awip32'
        else:
            product = 'awphys'
        ds = read_nam(dt, product, fxx, bbox)

    ##############
    #### HRRR ####
    ##############
    if model == "hrrr":
        if dt < HRRR_AWS_START:
            raise DataAvailabilityError(
                f"HRRR is unavailable before {HRRR_AWS_START:%Y-%m-%d}. "+
                f"Requested time: {dt:%Y-%m-%d %H:%M}."
            )
        if product:
            pass
        else:
            product = "prs"
        ds = read_hrrr(dt, product, fxx, bbox)

    return ds

def subset_bbox(ds, bbox):
    lat_min, lon_min, lat_max, lon_max = bbox

    lat = ds.latitude
    lon = ds.longitude

    # Detect if longitude is 0-360 and bbox has negative longitudes
    lon_min_ds, lon_max_ds = float(lon.min()), float(lon.max())
    if lon_min_ds >= 0 and lon_min < 0:
        # Convert negative bbox longitudes to 0-360
        lon_min = (lon_min + 360) % 360
        lon_max = (lon_max + 360) % 360
    
    if lat.ndim == 1 and lon.ndim == 1:
        lat_slice = slice(lat_max, lat_min) if lat[0] > lat[-1] else slice(lat_min, lat_max)
        lon_slice = slice(lon_min, lon_max)
        print(lon_slice)
        return ds.sel(latitude=lat_slice, longitude=lon_slice)

    else:
        mask = (
            (lat >= lat_min) & (lat <= lat_max) &
            (lon >= lon_min) & (lon <= lon_max)
        )

        if not mask.any():
            return ds
            
        y_index, x_index = np.where(mask)

        y_min, y_max = y_index.min(), y_index.max()
        x_min, x_max = x_index.min(), x_index.max()

        return ds.isel(y=slice(y_min, y_max + 1),x=slice(x_min, x_max + 1))


#Coordinates:
#time:            time (datetime64[ns])
#forecast hour:   step (timedelta64[ns])
#latitude:        latitude (S -> N in degrees [float64])
#longitude:       longitude (degrees East [float64])
#pressure levels: isobaricInhPa (Surface -> Top of Atmos [hPa])
#valid time:      valid_time (datetime61[ns])

#variable names:
#U wind:            u(isobaricInhPa,latitude,longitude)[m/s]
#V wind:            v(isobaricInhPa,latitude,longitude)[m/s]
#Temp:              t(isobaricInhPa,latitude,longitude)[K]
#Geopot Height:     gh(isobaricInhPa,latitude,longitude)[gpm]
#Relative Humid:    rh(isobaricInhPa,latitude,longitude)[%]
#10m U wind:        u10(latitude,longitude)[m/s]
#10m V wind:        v10(latitude,longitude)[m/s]
#2m Temp:           t2(latitude,longitude)[K]
#2m Relative Humid: rh2(latitude,longitude)[%]
#Pressure @ MSL:    pmsl(latitude,longitude)[Pa]
#Surface Pressure:  ps(latitude,longitude)[Pa]
#Surface Altitude:  orog(latitude,longitude)[gpm]

#################################################################
############################## GFS ##############################
#################################################################
def read_gfs(dt, product, fxx, bbox):  
    dt_str = dt.strftime('%Y-%m-%d %H:%M')
    H = Herbie(
        dt_str,
        model='gfs',
        product=product, #0.25 deg res common fields
        bbox=bbox,
        fxx=fxx,
    )
    
    regex_sfc = r":(?:PRES|PRMSL|HGT|RH|TMP|UGRD|VGRD):(?:mean sea level|2 m above ground|10 m above ground|surface):"
    regex_pl = r":(?:PRES|HGT|RH|TMP|UGRD|VGRD):\d+ mb:"

    ds_sfc_list = H.xarray(regex_sfc)
    ds_sfc = xr.merge(ds_sfc_list,compat="override")
    ds_sfc = ds_sfc.rename({
        "t": "ts",
        "sp": "ps",
        "r2": "rh2",
        "prmsl": "pmsl",
    })

    ds_pl_list = H.xarray(regex_pl)
    if isinstance(ds_pl_list,list):
        ds_pl = xr.merge(ds_pl_list,compat="override")
    else:
        ds_pl = ds_pl_list
    
    ds_pl = ds_pl.rename({
        "r": "rh",    
    })

    ds = xr.merge([ds_sfc,ds_pl],compat='override')

    #subset first
    ds = subset_bbox(ds,bbox)

    #now make lat/lon 2d:
    lat2d, lon2d = xr.broadcast(ds.latitude,ds.longitude)
    ds = ds.assign_coords(latitude=lat2d, longitude=lon2d)
    
    return ds


#################################################################
############################## NAM ##############################
#################################################################
def read_nam(dt, product, fxx, bbox):  
    dt_str = dt.strftime('%Y-%m-%d %H:%M')
    H = Herbie(
        dt_str,
        model='nam',
        product=product,
        bbox=bbox,
        fxx=0,
    )
    
    regex_sfc = r":(?:PRES|PRMSL|HGT|RH|TMP|UGRD|VGRD):(?:mean sea level|2 m above ground|10 m above ground|surface):"
    regex_pl = r":(?:PRES|HGT|RH|TMP|UGRD|VGRD):\d+ mb:"
    
    ds_sfc_list = H.xarray(regex_sfc)
    ds_sfc = xr.merge(ds_sfc_list,compat="override")
    ds_sfc = ds_sfc.rename({
        "t": "ts",
        "t2m": "t2",
        "sp": "ps",
        "r2": "rh2",
        "prmsl": "pmsl",
    })
    
    ds_pl_list = H.xarray(regex_pl)
    if isinstance(ds_pl_list,list):
        ds_pl = xr.merge(ds_pl_list,compat="override")
    else:
        ds_pl = ds_pl_list
    
    ds_pl = ds_pl.rename({
        "r": "rh",    
    })
    
    ds = xr.merge([ds_sfc,ds_pl],compat='override')
    ds = subset_bbox(ds,bbox)

    return ds


#################################################################
############################## RAP ##############################
#################################################################
def read_rap(dt, product, fxx, bbox):  
    dt_str = dt.strftime('%Y-%m-%d %H:%M')
    H = Herbie(
        dt_str,
        model='rap',
        product=product,
        bbox=bbox,
        fxx=fxx,
    )
    
    regex_sfc = r":(?:PRES|MSLMA|MSLET|HGT|RH|TMP|UGRD|VGRD):(?:mean sea level|2 m above ground|10 m above ground|surface):"
    regex_pl = r":(?:PRES|HGT|RH|TMP|UGRD|VGRD):\d+ mb:"

    ds_sfc_list = H.xarray(regex_sfc)
    ds_sfc = xr.merge(ds_sfc_list,compat="override")
    #print(H.inventory(r":mean sea level:"))
    if "mslma" in ds_sfc:
        ds_sfc = ds_sfc.rename({
            "t": "ts",
            "t2m": "t2",
            "sp": "ps",
            "r2": "rh2",
            "mslma": "pmsl",
        })
    elif "mslet" in ds_sfc:
        ds_sfc = ds_sfc.rename({
            "t": "ts",
            "t2m": "t2",
            "sp": "ps",
            "r2": "rh2",
            "mslet": "pmsl",
        })

    ds_pl_list = H.xarray(regex_pl)
    if isinstance(ds_pl_list,list):
        ds_pl = xr.merge(ds_pl_list,compat="override")
    else:
        ds_pl = ds_pl_list

    ds_pl = ds_pl.rename({
        "r": "rh",    
    })

    ds = xr.merge([ds_sfc,ds_pl],compat='override')

    ds = subset_bbox(ds,bbox)

    return ds


#################################################################
############################## HRRR ##############################
#################################################################
def read_hrrr(dt, product, fxx, bbox):  
    dt_str = dt.strftime('%Y-%m-%d %H:%M')
    H = Herbie(
        dt_str,
        model='hrrr',
        product=product,
        bbox=bbox,
        fxx=fxx,
    )
    
    regex_sfc = r":(?:PRES|MSLMA|MSLET|HGT|RH|TMP|UGRD|VGRD):(?:mean sea level|2 m above ground|10 m above ground|surface):"
    regex_pl = r":(?:PRES|HGT|RH|TMP|UGRD|VGRD):\d+ mb:"

    ds_sfc_list = H.xarray(regex_sfc)
    ds_sfc = xr.merge(ds_sfc_list,compat="override")
    #print(H.inventory(r":mean sea level:"))
    if "mslma" in ds_sfc:
        ds_sfc = ds_sfc.rename({
            "t": "ts",
            "t2m": "t2",
            "sp": "ps",
            "r2": "rh2",
            "mslma": "pmsl",
        })
    elif "mslet" in ds_sfc:
        ds_sfc = ds_sfc.rename({
            "t": "ts",
            "t2m": "t2",
            "sp": "ps",
            "r2": "rh2",
            "mslet": "pmsl",
        })

    ds_pl_list = H.xarray(regex_pl)
    if isinstance(ds_pl_list,list):
        ds_pl = xr.merge(ds_pl_list,compat="override")
    else:
        ds_pl = ds_pl_list

    ds_pl = ds_pl.rename({
        "r": "rh",    
    })

    ds = xr.merge([ds_sfc,ds_pl],compat='override')

    ds = subset_bbox(ds,bbox)

    return ds

def get_gefs_data(dt: datetime = datetime.utcnow().replace(microsecond=0,second=0,minute=0), model="gefs", fxx=0, bbox=[15,-170,75,-50]):
    model = model.lower()
    #############
    #### GEFS ####
    #############
    if dt < GEFS_START:
        raise DataAvailabilityError(
            f"GEFS is unavailable before {GFS_START:%Y-%m-%d}. "+
            f"Requested time: {dt:%Y-%m-%d %H:%M}."
        )
        
    members = 30
    ds_list = []
    for i in range(members+1):
        print(f"  loading member {i:02d} of {members}")
        ds_mbr = read_gefs(dt, "atmos.5", fxx, bbox, member=i)
        ds_list.append(ds_mbr)
        
    ds_ens = xr.concat(ds_list, dim="member", compat="override")  
    return(ds_ens)

def read_gefs(dt, product, fxx, bbox, member):  
    dt_str = dt.strftime('%Y-%m-%d %H:%M')
    H = Herbie(
        dt_str,
        model='gefs',
        product=product, #0.25 deg res common fields
        bbox=bbox,
        fxx=fxx,
        member=member,
    )
    
    regex_sfc = r":(?:PRES|PRMSL|HGT|RH|TMP|UGRD|VGRD):(?:mean sea level|2 m above ground|10 m above ground|surface):"
    regex_pl = r":(?:PRES|HGT|RH|TMP|UGRD|VGRD):\d+ mb:"

    ds_sfc_list = H.xarray(regex_sfc)
    ds_sfc = xr.merge(ds_sfc_list,compat="override")
    ds_sfc = ds_sfc.rename({
        "sp": "ps",
        "r2": "rh2",
        "prmsl": "pmsl",
    })

    ds_pl_list = H.xarray(regex_pl)
    if isinstance(ds_pl_list,list):
        ds_pl = xr.merge(ds_pl_list,compat="override",join="outer")
    else:
        ds_pl = ds_pl_list
    
    ds_pl = ds_pl.rename({
        "r": "rh",    
    })

    ds = xr.merge([ds_sfc,ds_pl],compat='override')


    #subset first
    ds = subset_bbox(ds,bbox)

    #now make lat/lon 2d:
    lat2d, lon2d = xr.broadcast(ds.latitude,ds.longitude)
    ds = ds.assign_coords(latitude=lat2d, longitude=lon2d)

    ds = ds.expand_dims(member=[member])
    
    return ds

    
def estimate_grid_spacing_km(ds):
    lat = ds.latitude.values
    lon = ds.longitude.values

    # Works for both 1D and 2D lat/lon
    if lat.ndim == 1:
        dlat = abs(lat[1] - lat[0])
        dlon = abs(lon[1] - lon[0])
    else:
        dlat = abs(lat[1,0] - lat[0,0])
        dlon = abs(lon[0,1] - lon[0,0])

    # Rough conversion
    km_per_deg = 111.0
    return km_per_deg * max(dlat, dlon)

def compute_wind_skip(ds, bbox, fig, target_barbs=30):
    """
    Automatically compute wind barb skip based on
    grid spacing, plot size, and bbox extent.
    """
    lat_min, lon_min, lat_max, lon_max = bbox

    # Domain size (km)
    lat_extent_km = (lat_max - lat_min) * 111.0
    lon_extent_km = (lon_max - lon_min) * 111.0 * np.cos(np.deg2rad((lat_min + lat_max)/2))

    domain_km = min(lat_extent_km, lon_extent_km)

    # Grid spacing
    dx_km = estimate_grid_spacing_km(ds)

    # Desired spacing between barbs
    barb_spacing_km = domain_km / target_barbs

    skip = max(1, int(round(barb_spacing_km / dx_km)))

    return skip