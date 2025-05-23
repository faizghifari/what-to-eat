
import streamlit as st

st.title("👤 User Preferences & Restrictions")

st.subheader("Available Tools")
tools = st.text_area("List your cooking tools (e.g., microwave, pan, oven)", height=100)
if st.button("Save Tools"):
    st.session_state["tools"] = tools.splitlines()
    st.success("Tools saved!")

st.subheader("Available Ingredients")
ingredients = st.text_area("List your ingredients (e.g., eggs, rice, garlic)", height=100)
if st.button("Save Ingredients"):
    st.session_state["ingredients"] = ingredients.splitlines()
    st.success("Ingredients saved!")

st.subheader("Dietary Preferences")
prefs = st.multiselect(
    "Select your food preferences",
    ["Spicy", "Sweet", "Vegan", "Korean", "Japanese", "Western"]
)
st.session_state["prefs"] = prefs

st.subheader("Dietary Restrictions")
restrictions = st.multiselect(
    "Select any dietary restrictions",
    ["Pork-free", "Gluten-free", "Nut allergy", "Halal", "Vegetarian"]
)
st.session_state["restrictions"] = restrictions

if st.button("Save All"):
    st.success("All preferences saved!")
