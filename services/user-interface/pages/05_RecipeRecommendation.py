
import streamlit as st

st.title("🍳 Recipe Recommendations")

st.subheader("Search for Recipes")
query = st.text_input("Enter ingredients or keywords")

if st.button("Search"):
    st.session_state["recipe_query"] = query
    st.session_state["searching"] = True

if st.session_state.get("searching"):
    st.info("🔄 Searching for recipes... (simulated)")
    # Simulated result
    recipes = [
        {"name": "Fried Rice", "price": 4500, "rating": 4.5},
        {"name": "Kimchi Pancake", "price": 3000, "rating": 4.2},
    ]
    for recipe in recipes:
        with st.container():
            st.markdown(f"**{recipe['name']}**")
            st.write(f"💵 {recipe['price']} KRW | ⭐ {recipe['rating']}")
            st.button("View Recipe", key=recipe["name"])
else:
    st.info("🔍 Enter ingredients to search for recipes.")
