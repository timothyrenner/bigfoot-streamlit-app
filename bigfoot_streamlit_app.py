import streamlit as st
import pandas as pd
import altair as alt
import folium

from streamlit_folium import folium_static
from dateutil.parser import parse


# This is by far the slowest operation in the whole app. Caching it means
# that it won't re-execute. And since the data itself never really changes
# for the duration of the app, the cache will almost never become invalid
# unless you change the code of this function.
@st.cache
def load_data():
    dataset = pd.read_csv("bfro_report_locations.csv")
    dataset.loc[:, "timestamp"] = dataset.timestamp.apply(parse)
    dataset.loc[:, "year"] = dataset.timestamp.dt.year
    # yes there are sightings from the future.
    return (
        dataset.query("year<=2020")
        .query("longitude>=-180 & longitude<=180")
        .query("latitude>=-90 & latitude<=90")
    )


def select_color(classification):
    if classification == "Class A":
        return "red"
    elif classification == "Class B":
        return "orange"
    else:
        return "blue"


st.title("Bigfoot Sightings")

bigfoot_sightings = load_data()

# What I'm doing is defining all the filter controls on the sidbar first,
# filtering the data, then rendering it on the main panel.

# Each control just returns its value. No callbacks, no state.
classifications = st.sidebar.multiselect(
    "Classification",
    options=bigfoot_sightings.classification.unique().tolist(),
    default=bigfoot_sightings.classification.unique().tolist(),
)

years = st.sidebar.slider(
    "Year",
    min_value=int(bigfoot_sightings.year.min()),
    max_value=int(bigfoot_sightings.year.max()),
    value=(1956, int(bigfoot_sightings.year.max()),),
)

text = st.sidebar.text_input("Filter Report Titles").lower()

# This bit of code actually runs the filters.
filtered_sightings = (
    bigfoot_sightings.query("classification.isin(@classifications)")
    .query("year>=@years[0]")
    .query("year<=@years[1]")
)

if text:
    filtered_sightings = filtered_sightings.query("title.str.contains(@text)")


# Next up are the plots. Originally this was a pydeck chart but now there's a
# streamlit plugin for Folium, which is awful to work with but at least it's
# free.

m = folium.Map(
    location=[
        filtered_sightings.latitude.mean(),
        filtered_sightings.longitude.mean(),
    ],
    zoom_start=4,
    tiles="cartodbpositron",
)
for _, row in filtered_sightings.iterrows():
    folium.Circle(
        radius=1000,
        location=[row.latitude, row.longitude],
        tooltip=row.title,
        fill=True,
        color=select_color(row.classification),
        opacity=0.5,
    ).add_to(m)


folium_static(m)

# I had a hard time getting st.line_chart to do what I want, but Altair was
# pretty simple to learn. I really like that Altair does those simple
# transformations (in this case date manipulation and groupby) inline, rather
# than me having to create a frame just for this chart.
sightings_by_year = (
    alt.Chart(filtered_sightings)
    .mark_line()
    .encode(x="year(timestamp)", y="count(number)", color="classification")
)

st.altair_chart(sightings_by_year, use_container_width=True)

# Hopefully this is obvious.
sightings_by_classification = (
    alt.Chart(filtered_sightings)
    .mark_bar()
    .encode(x="classification", y="count(number)")
)

st.altair_chart(sightings_by_classification, use_container_width=True)

# This just displays the data as a fancypants html table.
st.write(filtered_sightings)
