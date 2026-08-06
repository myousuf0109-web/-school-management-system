import streamlit as st
from db import init_db, get_user, check_pw

st.set_page_config(page_title="School Management System", page_icon="🎓", layout="wide")
init_db()

if "user" not in st.session_state:
    st.session_state.user = None


def login_screen():
    st.markdown("<h1 style='text-align:center'>🎓 School Management System</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True, type="primary"):
            user = get_user(username)
            if user and check_pw(password, user["password_hash"]):
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid username or password")

        with st.expander("Demo credentials"):
            st.write("**Admin:** admin / admin123")
            st.write("**Teacher:** ahsan / teacher123  (or sara, bilal)")
            st.write("**Student:** ali / student123  (or fatima, zainab, usman)")


def logout_button():
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user['username']}** ({st.session_state.user['role']})")
        if st.button("Log out"):
            st.session_state.user = None
            st.rerun()


if not st.session_state.user:
    login_screen()
else:
    logout_button()
    role = st.session_state.user["role"]
    st.sidebar.markdown("---")
    st.sidebar.caption("Use the pages menu above to navigate.")
    st.title("🎓 Dashboard")
    st.info("Use the left sidebar to open: Students, Teachers, Classes & Courses, "
            "Attendance, Grades & Rankings, Fees, Budget, Notice Board, and AI Assistant.")
    st.caption("Pages automatically show only what your role is allowed to see/edit.")
