
import streamlit as st

st.title("👥 Eat Together")

st.subheader("Create or Join a Group")
group_name = st.text_input("Group Name")
if st.button("Create Group"):
    st.session_state["group_name"] = group_name
    st.success(f"Group '{group_name}' created!")

st.subheader("Add Guest Preferences (optional)")
guest_prefs = st.text_area("Guest Preferences (e.g., vegan, halal)")
guest_restrictions = st.text_area("Guest Restrictions (e.g., no pork, nut allergy)")

st.subheader("Group Restaurant Recommendation")
if st.button("Get Recommendation"):
    st.success("🍽 Recommended: Hanbit Restaurant (matched all preferences)")

if st.button("🎲 Random Roulette"):
    st.success("🎉 Result: Dormitory Cafeteria")
