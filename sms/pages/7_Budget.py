import streamlit as st
import pandas as pd
from datetime import date
from utils import require_login, df_query, run

st.set_page_config(page_title="School Budget", page_icon="🏦", layout="wide")
user = require_login(allowed_roles=["admin"])
st.title("🏦 School Budget")

df = df_query("SELECT category, entry_type, amount, entry_date, note FROM budget ORDER BY entry_date DESC")

income = df[df.entry_type == "income"]["amount"].sum() if not df.empty else 0
expense = df[df.entry_type == "expense"]["amount"].sum() if not df.empty else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total Income", f"{income:,.0f}")
c2.metric("Total Expense", f"{expense:,.0f}")
c3.metric("Net Balance", f"{income - expense:,.0f}")

if not df.empty:
    st.write("#### Income vs Expense")
    st.bar_chart(pd.DataFrame({"amount": [income, expense]}, index=["Income", "Expense"]))

    st.write("#### By Category")
    cat_df = df.groupby(["category", "entry_type"])["amount"].sum().reset_index()
    st.dataframe(cat_df, use_container_width=True, hide_index=True)

st.write("#### All Entries")
st.dataframe(df, use_container_width=True, hide_index=True)

with st.expander("➕ Add budget entry"):
    with st.form("add_budget"):
        category = st.text_input("Category (e.g. Tuition Fees, Utilities)")
        entry_type = st.selectbox("Type", ["income", "expense"])
        amount = st.number_input("Amount", min_value=0.0, step=500.0)
        note = st.text_input("Note")
        if st.form_submit_button("Add Entry", type="primary"):
            if category and amount > 0:
                run(
                    "INSERT INTO budget(category,entry_type,amount,entry_date,note) VALUES (?,?,?,?,?)",
                    (category, entry_type, amount, date.today().isoformat(), note),
                )
                st.success("Added.")
                st.rerun()

st.divider()
st.subheader("👩‍🏫 Teacher Salary Payments")
teachers_df = df_query("SELECT id, name, monthly_salary FROM teachers")
st.dataframe(teachers_df, use_container_width=True, hide_index=True)

with st.expander("💵 Pay a teacher"):
    if not teachers_df.empty:
        tid = st.selectbox("Teacher", options=teachers_df["id"], format_func=lambda i: teachers_df[teachers_df.id==i]["name"].values[0])
        amount = st.number_input("Amount", min_value=0.0, step=1000.0, key="salary_amount")
        if st.button("Pay Salary", type="primary") and amount > 0:
            run("INSERT INTO teacher_salary_payments(teacher_id,amount,payment_date,note) VALUES (?,?,?,?)",
                (tid, amount, date.today().isoformat(), "Salary payment"))
            run("INSERT INTO budget(category,entry_type,amount,entry_date,note) VALUES (?,?,?,?,?)",
                ("Teacher Salaries", "expense", amount, date.today().isoformat(), "Salary payment"))
            st.success("Salary payment recorded.")
            st.rerun()
