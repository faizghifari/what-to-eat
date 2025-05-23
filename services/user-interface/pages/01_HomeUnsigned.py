
import streamlit as st

st.title("🍽 What To Eat")

st.info("You are not logged in. Please log in or sign up to continue.")

if st.button("Log In"):
    st.switch_page("pages/01_LoginSignup.py")

if st.button("Sign Up"):
    st.session_state.auth_mode = 'signup'
    st.switch_page("pages/01_LoginSignup.py")
