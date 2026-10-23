import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

st.set_page_config(
    page_title="AI Water Well Predictor - MP",
    layout="wide",
    page_icon="💧",
    initial_sidebar_state="expanded"
)

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

theme = st.sidebar.radio("🎨 Theme", ["Dark", "Light"], index=0 if st.session_state.theme == "dark" else 1)
st.session_state.theme = theme.lower()

# Simple theme CSS
if st.session_state.theme == "light":
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; color: #212529; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; }
        </style>
    """, unsafe_allow_html=True)

st.title("💧 AI-Enabled Water Well Predictor")
st.caption("Madhya Pradesh Focus | Powered by CGWB Telemetry Data")

@st.cache_data
def load_data():
    return pd.read_csv("mp_station_summary.csv")

df = load_data()

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

def find_nearest(lat, lon, data):
    data = data.copy()
    data["distance_km"] = data.apply(
        lambda row: haversine(lat, lon, row["latitude"], row["longitude"]), axis=1
    )
    return data.loc[data["distance_km"].idxmin()]

def get_prediction(water_level):
    depth = abs(float(water_level))
    if depth < 5:
        return {
            "suitability": "Highly Suitable",
            "dig_depth": f"{int(depth+15)} – {int(depth+35)} m",
            "discharge": "8 – 20 L/s",
            "technique": "Dug well / Shallow Borewell (DTH)",
            "quality": "Generally Good",
            "color": "green"
        }
    elif depth < 15:
        return {
            "suitability": "Suitable",
            "dig_depth": f"{int(depth+25)} – {int(depth+60)} m",
            "discharge": "5 – 12 L/s",
            "technique": "DTH Borewell (Recommended)",
            "quality": "Good to Moderate",
            "color": "blue"
        }
    elif depth < 30:
        return {
            "suitability": "Moderately Suitable",
            "dig_depth": f"{int(depth+40)} – {int(depth+90)} m",
            "discharge": "2 – 8 L/s",
            "technique": "DTH / Rotary Combination",
            "quality": "Moderate (Check Fluoride/Nitrate)",
            "color": "orange"
        }
    else:
        return {
            "suitability": "Less Suitable / Critical",
            "dig_depth": f"{int(depth+50)} – {int(depth+120)} m",
            "discharge": "1 – 5 L/s",
            "technique": "Deep Borewell with proper casing",
            "quality": "May have quality issues – Lab test recommended",
            "color": "red"
        }

@st.cache_data(show_spinner=False)
def geocode_place(place_name):
    geolocator = Nominatim(user_agent="water_well_predictor_mp_v2")
    try:
        location = geolocator.geocode(place_name + ", Madhya Pradesh, India", timeout=10)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except:
        return None, None, None

st.sidebar.header("🔍 Search Location")

# Popular places for quick select
popular_places = {
    "SVVV University, Indore": (22.7605, 75.8945),
    "Vijay Nagar, Indore": (22.7533, 75.8937),
    "Rajwada, Indore": (22.7177, 75.8655),
    "Indore Airport": (22.7218, 75.8011),
    "IIT Indore": (22.5204, 75.9207),
    "Medi-Caps University": (22.6800, 75.8300),
    "Bhopal - New Market": (23.2599, 77.4126),
    "Ujjain - Mahakal": (23.1765, 75.7885),
}

selected_quick = st.sidebar.selectbox(
    "Quick Select (type to filter)",
    options=["-- Select --"] + list(popular_places.keys())
)

if selected_quick != "-- Select --":
    lat, lon = popular_places[selected_quick]
    st.session_state["click_lat"] = lat
    st.session_state["click_lon"] = lon
    st.session_state["search_address"] = selected_quick

# Free text search
search_query = st.sidebar.text_input("Or type any place name", placeholder="e.g. SVVV University Indore")

if st.sidebar.button("🔎 Search", type="primary"):
    if search_query.strip():
        with st.spinner("Searching location..."):
            lat, lon, address = geocode_place(search_query)
            if lat and lon:
                st.session_state["click_lat"] = lat
                st.session_state["click_lon"] = lon
                st.session_state["search_address"] = address

                # Save to history
                if "history" not in st.session_state:
                    st.session_state.history = []
                st.session_state.history.insert(0, {
                    "name": address,
                    "lat": lat,
                    "lon": lon
                })
                st.session_state.history = st.session_state.history[:8]  # keep last 8
                st.sidebar.success("Location found!")
            else:
                st.sidebar.error("Location not found. Try adding 'Indore'")

# Search History
if "history" in st.session_state and st.session_state.history:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕘 Recent Searches")
    for i, item in enumerate(st.session_state.history):
        if st.sidebar.button(f"{item['name'][:40]}...", key=f"hist_{i}"):
            st.session_state["click_lat"] = item["lat"]
            st.session_state["click_lon"] = item["lon"]
            st.session_state["search_address"] = item["name"]

with st.expander("ℹ️ About this Project"):
    st.markdown("""
    **AI-Enabled Water Well Predictor** is a college major project designed to help users decide whether a location is suitable for constructing a water well.

    **What it predicts:**
    - Suitability for well construction
    - Recommended dig depth
    - Expected discharge
    - Best drilling technique
    - Expected groundwater quality

    **Data Source:** Central Ground Water Board (CGWB) Telemetry stations of Madhya Pradesh  
    **Method:** Rule-based expert system inspired by NAQUIM hydrogeology (mainly Deccan Trap basalt)

    **Developed by:** Sarthak Jain  
    **College Major Project – 2025-26**
    """)
default_lat = st.session_state.get("click_lat", 22.7196)
default_lon = st.session_state.get("click_lon", 75.8577)

m = folium.Map(location=[default_lat, default_lon], zoom_start=11 if "click_lat" in st.session_state else 8)

for _, row in df.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=3,
        color="#1f77b4",
        fill=True,
        fill_opacity=0.5,
        popup=f"<b>{row['station']}</b><br>{row['district']}<br>Avg: {row['avg_water_level']} m"
    ).add_to(m)

if "click_lat" in st.session_state:
    folium.Marker(
        [st.session_state["click_lat"], st.session_state["click_lon"]],
        popup="Selected Location",
        icon=folium.Icon(color="red", icon="tint", prefix="fa")
    ).add_to(m)

map_data = st_folium(m, width="100%", height=480, key="main_map")

if map_data and map_data.get("last_clicked"):
    st.session_state["click_lat"] = map_data["last_clicked"]["lat"]
    st.session_state["click_lon"] = map_data["last_clicked"]["lng"]
    st.session_state.pop("search_address", None)

if "click_lat" in st.session_state:
    lat = st.session_state["click_lat"]
    lon = st.session_state["click_lon"]
    nearest = find_nearest(lat, lon, df)
    pred = get_prediction(nearest["avg_water_level"])
    address = st.session_state.get("search_address", f"{lat:.5f}, {lon:.5f}")

    st.success(f"**Selected Location:** {address}")
    st.write(f"**Nearest CGWB Station:** `{nearest['station']}` ({nearest['district']}) — **{nearest['distance_km']:.1f} km** away")

    c1, c2, c3 = st.columns(3)
    c1.metric("Average Water Level", f"{nearest['avg_water_level']} m bgl")
    c2.metric("Latest Water Level", f"{nearest['latest_water_level']} m bgl")
    c3.metric("Readings Available", int(nearest["data_points"]))

    st.markdown("---")
    st.subheader("🔮 Prediction Results")

    st.markdown(f"""
    | Parameter                    | Result                                      |
    |-----------------------------|---------------------------------------------|
    | **Suitability**             | :{pred['color']}[**{pred['suitability']}**] |
    | **Recommended Dig Depth**   | **{pred['dig_depth']}**                     |
    | **Expected Discharge**      | {pred['discharge']}                         |
    | **Best Drilling Technique** | {pred['technique']}                         |
    | **Expected Water Quality**  | {pred['quality']}                           |
    """)

st.markdown("---")
st.markdown("""
**📌 Disclaimer & Data Source**

- Water level data is taken from **Central Ground Water Board (CGWB)** telemetry stations.  
- Predictions are generated using a **rule-based expert system** based on typical hydrogeology of Madhya Pradesh (mainly Deccan Trap basalt).  
- This tool is for **educational / academic purposes only**.  
- Always consult a qualified hydrogeologist and conduct proper site investigation before drilling any well.
""")