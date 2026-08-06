# School Management System (Python-only, Streamlit)

A full-stack school management system written entirely in Python (Streamlit for
frontend + backend, SQLite for the database). No HTML/CSS/JS needed.

## What's included
- **Multi-role login**: Admin, Teacher, Student (each sees different pages/permissions)
- **Students**: admission, records, search, delete
- **Teachers**: records, subjects, salaries
- **Classes & Courses**: setup and assignment
- **Attendance**: mark daily attendance, per-student % chart
- **Grades & Rankings**: enter marks, auto-ranked leaderboards, performance charts
- **Fees**: paid/unpaid tracking per student, payment history, paid-vs-unpaid charts
- **Budget**: school income/expenses, teacher salary payments, net balance
- **Notice Board**: post/view announcements
- **AI Assistant**: chat with your live school data (needs a free Anthropic API key),
  plus one-click AI-generated report card remarks

## 1. Run it locally
```bash
pip install streamlit pandas plotly bcrypt anthropic
streamlit run app.py
```
Open the URL it prints (usually http://localhost:8501).

The database (`sms.db`) is created automatically on first run, pre-loaded with
demo data so you can log in immediately:

| Role    | Username | Password    |
|---------|----------|-------------|
| Admin   | admin    | admin123    |
| Teacher | ahsan    | teacher123  |
| Student | ali      | student123  |

(Other demo accounts: teachers `sara`/`bilal`, students `fatima`/`zainab`/`usman` —
all use the same passwords as above for their role.)

## 2. Use the AI Assistant
Get a free API key at **console.anthropic.com**, paste it into the AI Assistant
page's password field (it's never saved to disk). If the model name field errors,
check **docs.claude.com** for the current model name and update the field.

## 3. Deploy it for free (so it's a real website, not just local)
1. Push this folder to a GitHub repo (public or private).
2. Go to **share.streamlit.io** (Streamlit Community Cloud) → sign in with GitHub.
3. Click "New app", pick your repo, set the main file to `app.py`, deploy.
4. You'll get a free permanent URL like `yourapp.streamlit.app`.

**Important:** change the demo passwords (edit `db.py`'s `seed()` function, or add
a "change password" feature) before sharing the link publicly, and don't commit a
real Anthropic API key into the repo — always paste it into the app at runtime.

## Project structure
```
app.py                     # login + landing page
db.py                      # schema, seeding, password hashing
utils.py                   # shared auth guard + query helpers
pages/
  1_Students.py
  2_Teachers.py
  3_Classes_Courses.py
  4_Attendance.py
  5_Grades_Rankings.py
  6_Fees.py
  7_Budget.py
  8_Notice_Board.py
  9_AI_Assistant.py
```

## Notes / what's simplified for v1
- Attendance marking is per-class, one date at a time.
- Fee payments are cumulative on the student record (a full ledger is in `fee_payments` too).
- The AI assistant sends a summary of your data to Anthropic's API when you ask a
  question — don't use it with a real, private production key that has broader
  access than you intend, and be aware student data leaves your machine when you
  use this feature.
- This is a strong working foundation, not a finished, audited production system —
  test it with your real data before relying on it, and tell me what to fix or add
  next (e.g. edit/delete for grades and attendance, CSV export, password reset,
  parent portal, timetable, exams calendar, printable report cards) and I'll build
  it in the same style.
