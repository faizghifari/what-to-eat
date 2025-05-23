import streamlit as st

st.title("🏠 Home")
st.write(f"Welcome, {st.session_state.get('username', 'Guest')}!")