import geopandas as gpd
import pandas as pd
import os
import numpy as np

missing_ids_path = os.path.join('data', 'repair_id_matching', 'weird_ids.csv')
out_path = os.path.join('data', 'repair_id_matching', 'completed_ids.csv')
df = pd.read_csv(missing_ids_path)
df_matching_ref = pd.read_csv(os.path.join('data', 'matching_bmw_to_address.csv'), sep=';')

df_out = pd.DataFrame(columns=df_matching_ref.columns)
df_out['BMW_userid'] = df.user_id
df_out['BMW_vid'] = df.vin
df_out['GWR_x'] = np.nan
df_out['GWR_y'] = np.nan

missing_ids = df['user_id']

for ix, row in df.iterrows():
    gwr_path = os.path.join('data', 'repair_id_matching', 'pv_mobility_gwr', str(row['user_id']), 'gwr.gpkg')
    gdf = gpd.read_file(gwr_path)

    if gdf.empty:
        x = np.nan
        y = np.nan
    else:
        x = gdf.geometry.x.iloc[0]
        y = gdf.geometry.y.iloc[0]

    df_out.loc[ix, 'GWR_x'] = x
    df_out.loc[ix, 'GWR_y'] = y

df_out.to_csv(index=False, path_or_buf=out_path, sep=';')

# read pv_mobility_gwr
# read weird_ids.csv

# read geopackage into geopandas
# for every weird ID, extract the coordinates
# append entries to matching_bmw_to_address.csv
    # fields: 'GWR_x', 'GWR_y', BMW_userid, BMW_vid, rest can be nan
    # coord system: 'epsg:21781'
