import streamlit as st
from utils import require_login, df_query, current_student_id

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")
user = require_login()
st.title("🤖 AI Assistant")

st.caption(
    "This assistant answers questions using your live school data. "
    "You need your own free Anthropic API key from console.anthropic.com to use it."
)

api_key = st.text_input("Anthropic API key", type="password", help="Get one free at console.anthropic.com")
model_name = st.text_input("Model", value="claude-sonnet-4-5", help="Check docs.claude.com for the latest model name if this errors.")


def build_context(user):
    """Builds a compact text summary of relevant data, scoped by role."""
    parts = []
    if user["role"] == "student":
        sid = current_student_id(user)
        s = df_query("SELECT * FROM students WHERE id=?", (sid,))
        g = df_query(
            """SELECT co.name as course, g.exam_name, g.marks, g.max_marks
               FROM grades g JOIN courses co ON g.course_id=co.id WHERE g.student_id=?""", (sid,))
        a = df_query("SELECT status, COUNT(*) c FROM attendance WHERE student_id=? GROUP BY status", (sid,))
        parts.append("STUDENT RECORD:\n" + s.to_string(index=False))
        parts.append("GRADES:\n" + g.to_string(index=False))
        parts.append("ATTENDANCE SUMMARY:\n" + a.to_string(index=False))
    else:
        students = df_query("SELECT s.name, cl.name as class, s.total_fee, s.fee_paid FROM students s LEFT JOIN classes cl ON s.class_id=cl.id")
        grades = df_query("SELECT s.name, co.name as course, g.exam_name, g.marks, g.max_marks FROM grades g JOIN students s ON g.student_id=s.id JOIN courses co ON g.course_id=co.id")
        attendance = df_query("SELECT s.name, a.status, COUNT(*) c FROM attendance a JOIN students s ON a.student_id=s.id GROUP BY s.name, a.status")
        budget = df_query("SELECT category, entry_type, SUM(amount) total FROM budget GROUP BY category, entry_type")
        parts.append("STUDENTS:\n" + students.to_string(index=False))
        parts.append("GRADES:\n" + grades.to_string(index=False))
        parts.append("ATTENDANCE:\n" + attendance.to_string(index=False))
        if user["role"] == "admin":
            parts.append("BUDGET:\n" + budget.to_string(index=False))
    return "\n\n".join(parts)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

question = st.chat_input("Ask about students, grades, fees, attendance, budget...")

if question:
    if not api_key:
        st.error("Please enter your Anthropic API key above first.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            context = build_context(user)
            system_prompt = (
                "You are a helpful school data assistant. Answer ONLY using the data provided below. "
                "If the data doesn't contain the answer, say so. Be concise and use numbers/tables where useful.\n\n"
                f"{context}"
            )
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = client.messages.create(
                        model=model_name,
                        max_tokens=1000,
                        system=system_prompt,
                        messages=[{"role": "user", "content": question}],
                    )
                    answer = response.content[0].text
                    st.write(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Error calling the AI: {e}")

st.divider()
st.subheader("✨ Auto-generate a performance remark")
st.caption("Generates a short teacher-style remark for a student's report card based on their grades.")

students_df = df_query("SELECT id, name FROM students") if user["role"] != "student" else None
target_sid = current_student_id(user) if user["role"] == "student" else None

if user["role"] != "student" and not students_df.empty:
    target_sid = st.selectbox("Student", options=students_df["id"], format_func=lambda i: students_df[students_df.id == i]["name"].values[0])

if st.button("Generate Remark") and target_sid:
    if not api_key:
        st.error("Please enter your Anthropic API key above first.")
    else:
        g = df_query(
            """SELECT co.name as course, g.marks, g.max_marks FROM grades g
               JOIN courses co ON g.course_id=co.id WHERE g.student_id=?""", (target_sid,))
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name,
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"Write a short, encouraging 2-3 sentence report card remark for a student "
                               f"based on these grades:\n{g.to_string(index=False)}"
                }],
            )
            st.success(response.content[0].text)
        except Exception as e:
            st.error(f"Error calling the AI: {e}")
