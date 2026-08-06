import streamlit as st
import pandas as pd
from datetime import date
from utils import require_login, df_query, run, current_student_id

st.set_page_config(page_title="Attendance", page_icon="🗓️", layout="wide")
user = require_login()
st.title("🗓️ Attendance")

if user["role"] == "student":
    sid = current_student_id(user)
    df = df_query("SELECT att_date, status FROM attendance WHERE student_id=? ORDER BY att_date DESC", (sid,))
    if not df.empty:
        present_pct = round((df["status"] == "present").mean() * 100, 1)
        st.metric("My Attendance %", f"{present_pct}%")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.stop()

# admin / teacher
classes_df = df_query("SELECT id, name FROM classes")
class_map = dict(zip(classes_df["name"], classes_df["id"]))

tab1, tab2 = st.tabs(["✅ Mark Attendance", "📊 Attendance Overview"])

with tab1:
    cls = st.selectbox("Class", options=list(class_map.keys()) if class_map else [])
    att_date = st.date_input("Date", value=date.today())
    if cls:
        students_df = df_query("SELECT id, name FROM students WHERE class_id=?", (class_map[cls],))
        if students_df.empty:
            st.info("No students in this class yet.")
        else:
            statuses = {}
            for _, row in students_df.iterrows():
                statuses[row["id"]] = st.radio(
                    row["name"], ["present", "absent", "leave"], horizontal=True, key=f"att_{row['id']}"
                )
            if st.button("Save Attendance", type="primary"):
                for sid, status in statuses.items():
                    run(
                        """INSERT INTO attendance(student_id,att_date,status) VALUES (?,?,?)
                           ON CONFLICT(student_id, att_date) DO UPDATE SET status=excluded.status""",
                        (sid, att_date.isoformat(), status),
                    )
                st.success("Attendance saved.")

with tab2:
    df = df_query(
        """SELECT s.name, s.id,
                  SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as present_days,
                  COUNT(a.id) as total_days
           FROM students s LEFT JOIN attendance a ON s.id=a.student_id
           GROUP BY s.id"""
    )
    if not df.empty:
        df["attendance_%"] = (df["present_days"] / df["total_days"].replace(0, pd.NA) * 100).round(1)
        st.dataframe(df[["name", "present_days", "total_days", "attendance_%"]], use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index("name")["attendance_%"])
