import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium
from remaining_budget_helper import filter, rb, get_trans_details

st.title("Apartment Recommendation System")
st.sidebar.header("Filters")
min_budget = st.sidebar.number_input("Minimum Budget ($)", min_value=0, value=1000, step=100)
max_budget = st.sidebar.number_input("Maximum Budget ($)", min_value=min_budget, value=5000, step=100)
beds = st.sidebar.slider("Number of Beds", min_value=0, max_value=5, value=1, step=1)
safety_score = st.sidebar.slider("Minimum Safety Score", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
st.sidebar.subheader("Nearby Amenities")
park = st.sidebar.checkbox("Park")
supermarket = st.sidebar.checkbox("Supermarket")

st.sidebar.subheader("Locations")
loc1_type = st.sidebar.radio("Location 1 (Work)", options=["Amazon", "Custom"])
if loc1_type == "Amazon":
    loc1_lat, loc1_lon = 47.623531, -122.336712
else:
    loc1_lat = st.sidebar.number_input("Custom Location 1 Latitude", value=47.0)
    loc1_lon = st.sidebar.number_input("Custom Location 1 Longitude", value=-122.0)

loc2_type = st.sidebar.radio("Location 2 (University)", options=["University of Washington", "Custom"])
if loc2_type == "University of Washington":
    loc2_lat, loc2_lon = 47.66171994213688, -122.31619957341718
else:
    loc2_lat = st.sidebar.number_input("Custom Location 2 Latitude", value=47.0)
    loc2_lon = st.sidebar.number_input("Custom Location 2 Longitude", value=-122.0)

commute_type = st.sidebar.radio("Commute Type", options=["Car", "Public Transport"])
mode = "driving" if commute_type == "Car" else "transit"

income = st.sidebar.number_input("Annual Income ($ in thousands)", min_value=0, value=50, step=5) * 1000

@st.cache_data
def load_data():
    return pd.read_csv("/Users/akshankrithick/final_df.csv")

df = load_data()


filtered_df = filter(
    df=df,
    park=int(park),
    supermarket=int(supermarket),
    min_safety_pr=safety_score
)

api_key = "AIzaSyBNRW3LnHcoCCnXrnRzTCmB73tyYEYw5lM"
loc1 = f"{loc1_lat},{loc1_lon}"
loc2 = f"{loc2_lat},{loc2_lon}"
filtered_df = get_trans_details(filtered_df, commute_type=mode, loc_type="office", destination=loc1, api_key=api_key)
filtered_df = get_trans_details(filtered_df, commute_type=mode, loc_type="school", destination=loc2, api_key=api_key)

car = commute_type == "Car"
recommended_df = rb(
    df=filtered_df,
    car=car,
    income=income,
    budget=max_budget,
    park=int(park),
    supermarket=int(supermarket),
    loc1=1,
    loc2=1
)

st.header("Recommended Apartments")
if recommended_df.empty:
    st.write("No apartments match your criteria.")
else:
    m = folium.Map(location=[47.623531, -122.336712], zoom_start=12)
    for _, row in recommended_df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=(
                f"Price: ${row['price']}<br>"
                f"Beds: {row['beds']}<br>"
                f"Safety Score: {row['safety_pr']:.2f}<br>"
                f"Remaining Budget: ${row['rb']:.2f}"
            ),
            tooltip=row["name"] if "name" in row else "Apartment"
        ).add_to(m)
    st_folium(m, width=800, height=500)
