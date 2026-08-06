import streamlit as st
from datetime import date
from utils import require_login, df_query, run, current_student_id

st.set_page_config(page_title="Students", page_icon="🧑‍🎓", layout="wide")
user = require_login()
st.title("🧑‍🎓 Students")

classes_df = df_query("SELECT id, name FROM classes")
class_map = dict(zip(classes_df["name"], classes_df["id"]))

if user["role"] == "student":
    sid = current_student_id(user)
    df = df_query(
        """SELECT s.name, c.name as class, s.admission_date, s.contact, s.guardian_name,
                  s.total_fee, s.fee_paid, (s.total_fee - s.fee_paid) as due
           FROM students s LEFT JOIN classes c ON s.class_id=c.id
           WHERE s.id=?""",
        (sid,),
    )
    st.subheader("My Record")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.stop()

# Admin / teacher view
tab1, tab2 = st.tabs(["📋 All Students", "➕ Add / Admit Student"])

with tab1:
    search = st.text_input("Search by name")
    q = """SELECT s.id, s.name, c.name as class, s.admission_date, s.contact, s.guardian_name,
                  s.total_fee, s.fee_paid, (s.total_fee-s.fee_paid) as due
           FROM students s LEFT JOIN classes c ON s.class_id=c.id"""
    if search:
        q += " WHERE s.name LIKE ?"
        df = df_query(q, (f"%{search}%",))
    else:
        df = df_query(q)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if user["role"] == "admin" and not df.empty:
        st.markdown("##### Delete a student")
        del_id = st.selectbox("Select student to remove", df["id"], format_func=lambda i: df[df.id == i]["name"].values[0])
        if st.button("🗑️ Delete student", type="secondary"):
            run("DELETE FROM students WHERE id=?", (del_id,))
            st.success("Deleted.")
            st.rerun()

with tab2:
    if user["role"] != "admin":
        st.info("Only admin can admit new students.")
    else:
        with st.form("add_student"):
            name = st.text_input("Full name")
            cls = st.selectbox("Class", options=list(class_map.keys()) if class_map else [])
            contact = st.text_input("Contact number")
            guardian = st.text_input("Guardian name")
            total_fee = st.number_input("Total fee (term/year)", min_value=0.0, step=1000.0)
            paid_now = st.number_input("Admission fee paid now", min_value=0.0, step=500.0)
            submitted = st.form_submit_button("Admit Student", type="primary")
            if submitted:
                if not name or not cls:
                    st.error("Name and class are required.")
                else:
                    cid = class_map[cls]
                    new_id = run(
                        """INSERT INTO students(name,class_id,admission_date,contact,guardian_name,total_fee,fee_paid)
                           VALUES (?,?,?,?,?,?,?)""",
                        (name, cid, date.today().isoformat(), contact, guardian, total_fee, paid_now),
                    )
                    if paid_now > 0:
                        run(
                            "INSERT INTO fee_payments(student_id,amount,payment_date,note) VALUES (?,?,?,?)",
                            (new_id, paid_now, date.today().isoformat(), "Admission payment"),
                        )
                    st.success(f"{name} admitted successfully!")
                    st.rerun()
