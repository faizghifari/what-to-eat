import streamlit as st

# Dummy user store
if 'users' not in st.session_state:
    st.session_state.users = {}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'

def login_ui():
    st.subheader("🔐 Log In")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        if email in st.session_state.users and st.session_state.users[email] == password:
            st.success("Login successful!")
            st.session_state.logged_in = True
        else:
            st.error("Invalid email or password.")

    if st.button("Don't have an account? Sign Up"):
        st.session_state.auth_mode = 'signup'

def signup_ui():
    st.subheader("📝 Sign Up")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_pw")
    confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

    if st.button("Sign Up"):
        if email in st.session_state.users:
            st.warning("Email already exists.")
        elif password != confirm:
            st.warning("Passwords do not match.")
        else:
            st.session_state.users[email] = password
            st.success("Account created! Please log in.")
            st.session_state.auth_mode = 'login'

    if st.button("Already have an account? Log In"):
        st.session_state.auth_mode = 'login'

if st.session_state.auth_mode == 'login':
    login_ui()
else:
    signup_ui()

if st.session_state.get('logged_in'):
    st.success("Redirecting to homepage...")
    st.switch_page("pages/02_Home.py")
