import streamlit as st
import pandas as pd
from datetime import date
from utils import require_login, df_query, run, current_student_id

st.set_page_config(page_title="Grades & Rankings", page_icon="📈", layout="wide")
user = require_login()
st.title("📈 Grades & Rankings")

if user["role"] == "student":
    sid = current_student_id(user)
    df = df_query(
        """SELECT co.name as course, g.exam_name, g.marks, g.max_marks,
                  ROUND(g.marks*100.0/g.max_marks,1) as pct
           FROM grades g JOIN courses co ON g.course_id=co.id
           WHERE g.student_id=?""",
        (sid,),
    )
    st.subheader("My Grades")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.bar_chart(df.set_index("course")["pct"])

    st.subheader("My Class Rank")
    rank_df = df_query(
        """SELECT s.id, s.name, s.class_id, AVG(g.marks*100.0/g.max_marks) as avg_pct
           FROM students s JOIN grades g ON s.id=g.student_id
           GROUP BY s.id"""
    )
    my_class = df_query("SELECT class_id FROM students WHERE id=?", (sid,))
    if not rank_df.empty and not my_class.empty:
        cid = my_class.iloc[0]["class_id"]
        class_rank = rank_df[rank_df["class_id"] == cid].sort_values("avg_pct", ascending=False).reset_index(drop=True)
        class_rank["rank"] = class_rank.index + 1
        st.dataframe(class_rank[["rank", "name", "avg_pct"]], use_container_width=True, hide_index=True)
    st.stop()

# admin / teacher
tab1, tab2, tab3 = st.tabs(["✏️ Enter Grades", "🏆 Rankings", "📊 Performance Charts"])

with tab1:
    courses_df = df_query("SELECT co.id, co.name, cl.name as class FROM courses co JOIN classes cl ON co.class_id=cl.id")
    if courses_df.empty:
        st.info("Add a course first (Classes & Courses page).")
    else:
        course_label = st.selectbox(
            "Course", options=courses_df["id"],
            format_func=lambda i: f"{courses_df[courses_df.id==i]['name'].values[0]} ({courses_df[courses_df.id==i]['class'].values[0]})",
        )
        class_id_df = df_query("SELECT class_id FROM courses WHERE id=?", (course_label,))
        students_df = df_query("SELECT id, name FROM students WHERE class_id=?", (class_id_df.iloc[0]["class_id"],))
        exam_name = st.text_input("Exam name", value="Midterm")
        max_marks = st.number_input("Max marks", min_value=1.0, value=100.0)
        if not students_df.empty:
            marks = {}
            for _, row in students_df.iterrows():
                marks[row["id"]] = st.number_input(row["name"], min_value=0.0, max_value=max_marks, key=f"grade_{row['id']}")
            if st.button("Save Grades", type="primary"):
                for sid, m in marks.items():
                    run(
                        "INSERT INTO grades(student_id,course_id,exam_name,marks,max_marks,exam_date) VALUES (?,?,?,?,?,?)",
                        (sid, course_label, exam_name, m, max_marks, date.today().isoformat()),
                    )
                st.success("Grades saved.")

with tab2:
    rank_df = df_query(
        """SELECT s.name, cl.name as class, AVG(g.marks*100.0/g.max_marks) as avg_pct
           FROM students s
           JOIN grades g ON s.id=g.student_id
           LEFT JOIN classes cl ON s.class_id=cl.id
           GROUP BY s.id ORDER BY avg_pct DESC"""
    )
    if rank_df.empty:
        st.info("No grades entered yet.")
    else:
        rank_df["avg_pct"] = rank_df["avg_pct"].round(1)
        rank_df.insert(0, "rank", range(1, len(rank_df) + 1))
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

with tab3:
    perf_df = df_query(
        """SELECT s.name, AVG(g.marks*100.0/g.max_marks) as avg_pct
           FROM students s JOIN grades g ON s.id=g.student_id GROUP BY s.id"""
    )
    if not perf_df.empty:
        st.bar_chart(perf_df.set_index("name")["avg_pct"])
    course_perf = df_query(
        """SELECT co.name as course, AVG(g.marks*100.0/g.max_marks) as avg_pct
           FROM grades g JOIN courses co ON g.course_id=co.id GROUP BY co.id"""
    )
    if not course_perf.empty:
        st.write("Average performance by course")
        st.bar_chart(course_perf.set_index("course")["avg_pct"])
