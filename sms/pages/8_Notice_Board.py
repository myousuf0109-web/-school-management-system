import streamlit as st
from datetime import date
from utils import require_login, df_query, run

st.set_page_config(page_title="Notice Board", page_icon="📢", layout="wide")
user = require_login()
st.title("📢 Notice Board")

if user["role"] in ("admin", "teacher"):
    with st.expander("➕ Post a new notice"):
        with st.form("add_notice"):
            title = st.text_input("Title")
            content = st.text_area("Content")
            if st.form_submit_button("Post Notice", type="primary"):
                if title and content:
                    run(
                        "INSERT INTO notices(title,content,posted_by,posted_date) VALUES (?,?,?,?)",
                        (title, content, user["username"], date.today().isoformat()),
                    )
                    st.success("Notice posted.")
                    st.rerun()

notices = df_query("SELECT title, content, posted_by, posted_date FROM notices ORDER BY posted_date DESC")
for _, n in notices.iterrows():
    with st.container(border=True):
        st.markdown(f"**{n['title']}**  \n{n['content']}")
        st.caption(f"Posted by {n['posted_by']} on {n['posted_date']}")
