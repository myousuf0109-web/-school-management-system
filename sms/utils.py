import streamlit as st
import pandas as pd
from db import get_conn


def require_login(allowed_roles=None):
    """Guard a page. Stops execution if not logged in / not authorized."""
    if "user" not in st.session_state or not st.session_state.user:
        st.warning("Please log in from the main page first.")
        st.stop()
    user = st.session_state.user
    if allowed_roles and user["role"] not in allowed_roles:
        st.error("You don't have permission to view this page.")
        st.stop()
    with st.sidebar:
        st.write(f"👤 **{user['username']}** ({user['role']})")
        if st.button("Log out", key="logout_sidebar"):
            st.session_state.user = None
            st.rerun()
    return user


def df_query(sql, params=()):
    with get_conn() as conn:
        return pd.read_sql_query(sql, conn, params=params)


def run(sql, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def current_student_id(user):
    """If logged-in user is a student, return their students.id"""
    if user["role"] == "student":
        return user["linked_id"]
    return None


def current_teacher_id(user):
    if user["role"] == "teacher":
        return user["linked_id"]
    return None
