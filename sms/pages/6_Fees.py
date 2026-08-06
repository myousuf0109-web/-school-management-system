import streamlit as st
import pandas as pd
from datetime import date
from utils import require_login, df_query, run, current_student_id

st.set_page_config(page_title="Student Fees", page_icon="💰", layout="wide")
user = require_login()
st.title("💰 Student Fees")

if user["role"] == "student":
    sid = current_student_id(user)
    df = df_query("SELECT total_fee, fee_paid, (total_fee-fee_paid) as due FROM students WHERE id=?", (sid,))
    row = df.iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Fee", f"{row['total_fee']:,.0f}")
    c2.metric("Paid", f"{row['fee_paid']:,.0f}")
    c3.metric("Due", f"{row['due']:,.0f}")
    hist = df_query("SELECT payment_date, amount, note FROM fee_payments WHERE student_id=? ORDER BY payment_date DESC", (sid,))
    st.subheader("Payment History")
    st.dataframe(hist, use_container_width=True, hide_index=True)
    st.stop()

# admin / teacher
tab1, tab2 = st.tabs(["📋 Fee Status", "💵 Record Payment"])

with tab1:
    df = df_query(
        """SELECT s.id, s.name, cl.name as class, s.total_fee, s.fee_paid, (s.total_fee-s.fee_paid) as due
           FROM students s LEFT JOIN classes cl ON s.class_id=cl.id"""
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        total_paid = df["fee_paid"].sum()
        total_due = df["due"].sum()
        chart_df = pd.DataFrame({"amount": [total_paid, total_due]}, index=["Paid", "Unpaid"])
        st.write("#### Paid vs Unpaid (school-wide)")
        st.bar_chart(chart_df)

        st.write("#### Per-student fee status")
        st.bar_chart(df.set_index("name")[["fee_paid", "due"]])

with tab2:
    if user["role"] != "admin":
        st.info("Only admin can record payments.")
    else:
        students_df = df_query("SELECT id, name FROM students")
        if not students_df.empty:
            sid = st.selectbox("Student", options=students_df["id"], format_func=lambda i: students_df[students_df.id==i]["name"].values[0])
            amount = st.number_input("Amount received", min_value=0.0, step=500.0)
            note = st.text_input("Note", value="Fee installment")
            if st.button("Record Payment", type="primary") and amount > 0:
                run("INSERT INTO fee_payments(student_id,amount,payment_date,note) VALUES (?,?,?,?)",
                    (sid, amount, date.today().isoformat(), note))
                run("UPDATE students SET fee_paid = fee_paid + ? WHERE id=?", (amount, sid))
                st.success("Payment recorded.")
                st.rerun()
