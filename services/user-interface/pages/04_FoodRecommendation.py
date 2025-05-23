
import streamlit as st

st.title("🍱 Food Recommendations")

# Search bar
search_term = st.text_input("Search for a menu or restaurant")

# Filters
st.subheader("Filters")
price_range = st.slider("Price range (KRW)", 0, 20000, (3000, 10000), step=500)
distance = st.slider("Distance (meters)", 0, 2000, 1000)
rating = st.slider("Minimum Rating", 0.0, 5.0, 3.0, step=0.1)

# Sort options
sort_by = st.selectbox("Sort by", ["Matched Preferences", "Rating", "Price", "Distance"])
sort_order = st.radio("Order", ["Ascending", "Descending"])

# Simulated results
st.subheader("Recommended Menus")

sample_menus = [
    {"name": "Kimchi Stew", "restaurant": "Student Cafeteria", "price": 4500, "rating": 4.2},
    {"name": "Bibimbap", "restaurant": "Hanbit Restaurant", "price": 5000, "rating": 4.5},
    {"name": "Pork Cutlet", "restaurant": "Dormitory Cafeteria", "price": 5500, "rating": 4.0},
]

for menu in sample_menus:
    with st.container():
        st.markdown(f"**{menu['name']}** - {menu['restaurant']}")
        st.write(f"💵 {menu['price']} KRW | ⭐ {menu['rating']}")
        st.button("View Details", key=menu["name"])
