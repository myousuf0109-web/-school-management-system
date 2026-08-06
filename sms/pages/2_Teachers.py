import streamlit as st
from datetime import date
from utils import require_login, df_query, run

st.set_page_config(page_title="Teachers", page_icon="🧑‍🏫", layout="wide")
user = require_login()
st.title("🧑‍🏫 Teachers")

tab1, tab2 = st.tabs(["📋 All Teachers", "➕ Add Teacher"])

with tab1:
    df = df_query("SELECT id, name, subject, contact, monthly_salary, joined_date FROM teachers")
    st.dataframe(df, use_container_width=True, hide_index=True)

    if user["role"] == "admin" and not df.empty:
        st.markdown("##### Remove a teacher")
        del_id = st.selectbox("Select teacher", df["id"], format_func=lambda i: df[df.id == i]["name"].values[0])
        if st.button("🗑️ Remove teacher"):
            run("DELETE FROM teachers WHERE id=?", (del_id,))
            st.success("Removed.")
            st.rerun()

with tab2:
    if user["role"] != "admin":
        st.info("Only admin can add teachers.")
    else:
        with st.form("add_teacher"):
            name = st.text_input("Full name")
            subject = st.text_input("Subject")
            contact = st.text_input("Contact")
            salary = st.number_input("Monthly salary", min_value=0.0, step=1000.0)
            submitted = st.form_submit_button("Add Teacher", type="primary")
            if submitted:
                if not name:
                    st.error("Name is required.")
                else:
                    run(
                        "INSERT INTO teachers(name,subject,contact,monthly_salary,joined_date) VALUES (?,?,?,?,?)",
                        (name, subject, contact, salary, date.today().isoformat()),
                    )
                    st.success(f"{name} added.")
                    st.rerun()
