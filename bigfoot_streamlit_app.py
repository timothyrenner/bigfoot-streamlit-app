import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import os

from dateutil.parser import parse

try:
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())
except ImportError:
    print("python-dotenv is not installed.")
    print("I'll still look for the mapbox token in the environment.")


MAPBOX_KEY = os.environ.get("MAPBOX_KEY", "")


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
    return dataset.query("year<=2020")


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


# Next up are the plots. If there's no mapbox key we can skip this one but
# you really want it cause it's an awesome map.
# This is not clear in streamlit's docs: they make it seem like the key is
# optional, but it isn't. It straight up won't work without it.
# Or if it is optional I couldn't figure it out.
if MAPBOX_KEY:
    # I used the "lower level" pydeck to build this even though it's not
    # a complicated map because I could not get streamlit.map( ... ) to work at
    # all. It just showed blank tiles.
    deck = pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=39.5, longitude=-97.35, zoom=3
        ),
        map_style="mapbox://styles/mapbox/outdoors-v11",
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=filtered_sightings[["longitude", "latitude"]],
                get_position=["longitude", "latitude"],
                elevation_range=[0, 1000],
                coverage=1,
                radius=25000,
                pickable=True,
                opacity=0.5,
            )
        ],
    )

    st.pydeck_chart(deck)
else:
    st.write(
        "Unable to find a Mapbox key. Deck.gl chart won't work without it."
    )

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
