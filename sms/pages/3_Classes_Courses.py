import streamlit as st
from utils import require_login, df_query, run

st.set_page_config(page_title="Classes & Courses", page_icon="🏫", layout="wide")
user = require_login()
st.title("🏫 Classes & Courses")

teachers_df = df_query("SELECT id, name FROM teachers")
teacher_map = dict(zip(teachers_df["name"], teachers_df["id"]))

col1, col2 = st.columns(2)

with col1:
    st.subheader("Classes")
    df = df_query(
        """SELECT cl.id, cl.name, t.name as class_teacher
           FROM classes cl LEFT JOIN teachers t ON cl.teacher_id=t.id"""
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    if user["role"] == "admin":
        with st.form("add_class"):
            name = st.text_input("Class name (e.g. Class 8-A)")
            teacher = st.selectbox("Class teacher", options=["-- none --"] + list(teacher_map.keys()))
            if st.form_submit_button("Add Class", type="primary"):
                if name:
                    tid = teacher_map.get(teacher)
                    run("INSERT INTO classes(name,teacher_id) VALUES (?,?)", (name, tid))
                    st.success("Class added.")
                    st.rerun()

with col2:
    st.subheader("Courses")
    df2 = df_query(
        """SELECT co.id, co.name as course, cl.name as class, t.name as teacher
           FROM courses co
           LEFT JOIN classes cl ON co.class_id=cl.id
           LEFT JOIN teachers t ON co.teacher_id=t.id"""
    )
    st.dataframe(df2, use_container_width=True, hide_index=True)
    if user["role"] == "admin":
        classes_df = df_query("SELECT id, name FROM classes")
        class_map = dict(zip(classes_df["name"], classes_df["id"]))
        with st.form("add_course"):
            cname = st.text_input("Course name (e.g. Chemistry)")
            cls = st.selectbox("Class", options=list(class_map.keys()) if class_map else [])
            teacher = st.selectbox("Teacher", options=list(teacher_map.keys()) if teacher_map else [], key="course_teacher")
            if st.form_submit_button("Add Course", type="primary"):
                if cname and cls and teacher:
                    run(
                        "INSERT INTO courses(name,class_id,teacher_id) VALUES (?,?,?)",
                        (cname, class_map[cls], teacher_map[teacher]),
                    )
                    st.success("Course added.")
                    st.rerun()
