import streamlit as st

st.set_page_config(page_title="Search Restaurant", layout="wide")
st.markdown("""
<style>
.navbar {
    background-color: #f0f2f6;
    padding: 10px;
    border-bottom: 1px solid #ddd;
    margin-bottom: 20px;
}
.navbar a {
    margin-right: 15px;
    text-decoration: none;
    font-weight: bold;
    color: #0366d6;
}
</style>
<div class="navbar">
    <a href="/FoodHome" target="_self">Food</a>
    <a href="/RecipeHome" target="_self">Recipe</a>
    <a href="/ToolsIngredients" target="_self">Tools & Ingredients</a>
    <a href="/Preferences" target="_self">Preferences</a>
    <a href="/EatTogether" target="_self">Eat Together</a>
</div>
""", unsafe_allow_html=True)
st.title("Search Restaurant")
st.write("This is the search restaurant screen.")
