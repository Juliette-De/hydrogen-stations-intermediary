import pandas as pd
import folium
import numpy as np
import streamlit as st
from IPython.display import display
from streamlit_folium import folium_static

#@st.cache_data
def load_and_prepare():
  df = pd.read_csv('df_clean.csv')
  region_dep = pd.read_csv("departements-region.csv", sep=';')

  df['truck_traffic'] = df['TMJA'] * df['ratioPL'] / 100
  df["depPrD"] = df["depPrD"].astype(str)
  df = df.merge(region_dep[["num_dep", "region_name"]], right_on="num_dep", left_on="depPrD", how="left")

  df_by_region_and_road = df.groupby(["route", "region_name"])["truck_traffic"].mean().reset_index()
  df = df.merge(df_by_region_and_road, how='left', on=["region_name", "route"])
  df.rename(columns = {"truck_traffic_y" : "truck_traffic_region", "truck_traffic_x" : "truck_traffic_segment"}, inplace=True)

  df['avg_traffic_bin'] = pd.cut(df['truck_traffic_segment'], 5, labels=[1, 5, 10, 15, 20])

  df['longueur'] = df['longueur'].str.replace(",", ".").astype(float)
  df_len = df.groupby('route')['longueur'].sum().reset_index()
  df = df.merge(df_len, how='left', on='route')
  df.rename(columns = {'longueur_x':'longueur', 'longueur_y':'longueur_route'}, inplace=True)
  return (df)

def color():
  # generate a random list of n hexadecimal colors
  n = 1000
  colors = ['#'+''.join([np.random.choice(list('0123456789ABCDEF')) for j in range(6)]) for i in range(n)]
  return colors

def intermediateStations_region(df):
  options = [(125, 0.2), (150, 0.25), (200, 0.3)]
  l = []
  for option in options:
    frequency = option[0]
    affluence = option[1]
    seuil_frequentation_quantile = np.quantile(df['truck_traffic_segment'], affluence)
    df_grandes_routes = df[(df['longueur_route'] >= frequency * 1000) & (df['truck_traffic_segment'] >= seuil_frequentation_quantile)].reset_index()
    df_grandes_routes['longueur_cumul'] = df_grandes_routes.groupby(['route'])['longueur'].cumsum()

    df_idx = pd.DataFrame()
    df_grandes_routes['index'] = df_grandes_routes.index
    for k in range(round(max(df_grandes_routes.longueur_cumul)/(int(frequency) * 1000))):
      milestone = k * frequency * 1000
      temp = pd.DataFrame(df_grandes_routes[df_grandes_routes['longueur_cumul'] <= milestone].groupby('route')['index'].max()).reset_index(drop=True)
      df_idx = pd.concat([df_idx, temp], axis=0).drop_duplicates()

    df_idx = df_idx.reset_index(drop=True)

    df_idx['is_stationable'] = 1

    df_grandes_routes = df_grandes_routes.merge(df_idx, how='left', on='index')

    df_grandes_routes = df_grandes_routes.groupby('region_name')['is_stationable'].sum().reset_index()

    l.append(df_grandes_routes)
  return l

def intermediateStations(df, frequency, affluence):
  seuil_frequentation_quantile = np.quantile(df['truck_traffic_segment'], affluence)
  df_grandes_routes = df[(df['longueur_route'] >= frequency * 1000) & (df['truck_traffic_segment'] >= seuil_frequentation_quantile)].reset_index()
  df_grandes_routes['longueur_cumul'] = df_grandes_routes.groupby(['route'])['longueur'].cumsum()

  df_idx = pd.DataFrame()
  df_grandes_routes['index'] = df_grandes_routes.index

  for k in range(round(max(df_grandes_routes.longueur_cumul)/(int(frequency) * 1000))):
    milestone = k * frequency * 1000
    temp = pd.DataFrame(df_grandes_routes[df_grandes_routes['longueur_cumul'] <= milestone].groupby('route')['index'].max()).reset_index(drop=True)
    df_idx = pd.concat([df_idx, temp], axis=0).drop_duplicates()

  df_idx = df_idx.reset_index(drop=True)

  df_idx['is_stationable'] = 1

  df_grandes_routes = df_grandes_routes.merge(df_idx, how='left', on='index')

  colors = color()

  map_center = [46.2276, 2.2137]
  m = folium.Map(zoom_start=5.4, location=map_center)
  j=0
  for route in list(df.route.unique()):
    for i, row in df[df['route'] == route].iterrows():
      folium.PolyLine(
          locations=[[row['latD'], row['lonD']], [row['latF'], row['lonF']]],
          color=colors[j],
          tooltip=row['route'],
          weight=row['avg_traffic_bin']
      ).add_to(m)
    j += 1

  for i, row in df_grandes_routes[df_grandes_routes['is_stationable'] == 1].iterrows():
    folium.Marker(
        location=[row['latF'], row['lonF']],
        color='red',
        radius=4   
    ).add_to(m)

  return m, df_grandes_routes

def globalTraffic(df):
  colors = color()

  # create a folium map centered on the US
  map_center = [46.2276, 2.2137]
  m = folium.Map(zoom_start=5.4, location=map_center)

  # add markers for starting and ending positions

  j=0
  for route in list(df.route.unique()):
    for i, row in df[df['route'] == route].iterrows():
      folium.PolyLine(
          locations=[[row['latD'], row['lonD']], [row['latF'], row['lonF']]],
          color=colors[j],
          tooltip=row['route'],
          weight=row['avg_traffic_bin']
      ).add_to(m)

      
    j += 1

  return m