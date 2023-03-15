import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import sys

#sys.path.append("/Users/antoinerazeghi/Documents/Projects/AirLiquide/airliquide/")


#from ... import hub_clustering
import hub_clustering.params as p
import hub_clustering.utils as f

# st.header("Locating charging stations according to hubs")

dataset = f.load_data()


final_df = pd.DataFrame([])
centroids = dict()
datasets_for_map = dict()
i = 0
for scenario in p.HUB_SIZE_THRESHOLDS.keys():
    df = f.filter_dataset(dataset, scenario=scenario)
    final_dataset, centroids_df = f.run_kmeans(df)
    df = f.count_centroid_by_region(centroids_df)
    df.rename(columns={"count": f"count_{scenario}"}, inplace=True)
    centroids[f"{scenario}"] = centroids_df
    datasets_for_map[f"{scenario}"] = final_dataset
    if i == 0:
        final_df = pd.concat([final_df, df], axis=1)
    else:
        final_df = pd.concat([final_df, df.iloc[:, -1]], axis=1)
    i += 1

st.subheader("Charging stations per region per scenario")
options = st.multiselect(
    "What scenario would you like to stimulate?",
    p.HUB_SIZE_THRESHOLDS.keys(),
    p.HUB_SIZE_THRESHOLDS.keys(),
)
regions = final_df["Libellé des régions"]
fig3 = go.Figure()
if "optimistic" in options:
    fig3.add_trace(
        go.Bar(
            x=regions,
            y=final_df["count_optimistic"],
            name="Optimistic",
            marker_color=px.colors.qualitative.Plotly[0],
        )
    )
if "moderate" in options:
    fig3.add_trace(
        go.Bar(
            x=regions,
            y=final_df["count_moderate"],
            name="Moderate",
            marker_color=px.colors.qualitative.Plotly[1],
        )
    )
if "conservative" in options:
    fig3.add_trace(
        go.Bar(
            x=regions,
            y=final_df["count_conservative"],
            name="Conservative",
            marker_color=px.colors.qualitative.Plotly[3],
        )
    )
fig3.update_layout(barmode="group", xaxis_tickangle=-45)
st.plotly_chart(fig3)


st.subheader("Map")

map_scenario = st.selectbox(
    "Select a scenario to get a map showing the locations of the stations",
    p.HUB_SIZE_THRESHOLDS.keys(),
)

fig2 = f.visualize_on_map(datasets_for_map[map_scenario], centroids[map_scenario])
st.plotly_chart(fig2)
