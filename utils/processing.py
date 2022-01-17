import streamlit as st
from datetime import date, timedelta, datetime
from scipy.io import loadmat
import pandas as pd
import geopandas as gpd
import numpy as np


def read_data(fn, upload_mask, n=100):

    fn = sorted(fn)
    mat = loadmat(fn[0])  # TS data
    mat1 = loadmat(fn[1])  # Non-TS data

    lonlat = np.hsplit(mat['lonlat'], 2)
    df = pd.DataFrame(mat['ph_mm'], columns=mat['day'].flatten())
    df['lon'] = lonlat[0]
    df['lat'] = lonlat[1]
    df['ave'] = mat1['ph_disp'].flatten()
    df['ave'] = df['ave'].apply(lambda x: round(x, 2))

    # If max n exceeds len df, cap max n to len df
    if n > len(df):
        n = len(df)
        st.warning(f'Maximum value exceeds dataset size! Maximum value adjusted to {n}')
    df = df.reset_index().sample(n)

    df = pd.melt(df, id_vars=['lon', 'lat', 'ave', 'index'], var_name='Date')
    df['Date'] = [date(1, 1, 1) + timedelta(i) - timedelta(367) for i in df.Date]
    df = df.rename(columns={'index': 'ps', 'value': 'Displacement'})
    df['Displacement'] = df['Displacement'].apply(lambda x: round(x, 2))

    slave_days = mat['day'].flatten()
    master_day = mat['master_day'].flatten()
    days = np.sort(np.append(slave_days, master_day))
    bperp = mat['bperp'].flatten()
    bperp_df = pd.DataFrame({'Date': days, 'Bperp': bperp})
    bperp_df['Day'] = bperp_df['Date'].apply(lambda x: 'Slave' if x != int(master_day[0]) else 'Master')
    bperp_df['Temporal'] = bperp_df['Date'].apply(lambda x: x - int(master_day[0]))
    bperp_df.Date = [date(1, 1, 1) + timedelta(i) - timedelta(367) for i in bperp_df.Date]

    # Convert to GeoDataFrame
    df['geometry'] = gpd.points_from_xy(df['lon'], df['lat'], crs='EPSG:4326')
    df = gpd.GeoDataFrame(df, crs='EPSG:4326')

    if upload_mask is not None:
        df_mask = gpd.GeoDataFrame.from_file(upload_mask)
        df = gpd.clip(df, mask=df_mask)

    return df, bperp_df, slave_days, master_day, n
