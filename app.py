"""StudyMatch: find study partners in your major. Streamlit + SQLite, styled with HTML/CSS."""
import html
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = "studymatch.db"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TIMES = ["Morning", "Afternoon", "Evening"]
STYLES = ["Quiet focus", "Talk it through", "Practice problems", "Quiz each other"]
YEARS = ["Freshman", "Sophomore", "Junior", "Senior", "Grad"]
MAJORS = [
    "Biology", "Business", "Chemistry", "Computer Science", "Economics",
    "Engineering", "English", "History", "Mathematics", "Nursing",
    "Physics", "Political Science", "Psychology", "Other",
]

st.set_page_config(
    page_title="StudyMatch", page_icon="📚", layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- look and feel (HTML/CSS) ----------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Public+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #14213D; --blue: #3D5A80; --page: #F3F6FA; --card: #FFFFFF;
  --line: #D5DDE8; --hl: #FFE45C; --muted: #5B6B82;
}
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.stApp { background: var(--page); color: var(--ink); font-family: 'Public Sans', system-ui, sans-serif; }
.block-container { max-width: 820px; padding-top: 1.2rem; padding-bottom: 4rem; }
.stApp h2, .stApp h3 { font-family: 'Bricolage Grotesque', sans-serif; letter-spacing: -0.02em; color: var(--ink); }

/* top bar and hero */
.nav { display: flex; justify-content: space-between; align-items: center; padding: .4rem 0 1.4rem; }
.mark {
  font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 1.35rem;
  letter-spacing: -0.02em; padding: 0 .15em;
  background: linear-gradient(transparent 58%, var(--hl) 58%, var(--hl) 92%, transparent 92%);
}
.navnote { color: var(--muted); font-size: .9rem; }
.hero { padding: 1.2rem 0 1.8rem; border-bottom: 1px solid var(--line); margin-bottom: 1.2rem; }
.stApp .hero h1 {
  font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; color: var(--ink);
  font-size: clamp(2rem, 5.5vw, 3.1rem); line-height: 1.05; letter-spacing: -0.03em;
  margin: 0 0 .9rem; max-width: 16em; padding: 0;
}
.hero p { max-width: 34em; font-size: 1.05rem; line-height: 1.55; color: var(--blue); margin: 0 0 .6rem; }
.hero .count { font-weight: 600; color: var(--ink); }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] p { font-family: 'Bricolage Grotesque', sans-serif; font-weight: 600; font-size: 1.05rem; }
.stTabs [data-baseweb="tab-highlight"] { background: var(--ink); }

/* buttons */
.stButton button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background: var(--ink); border: 0; color: #fff; border-radius: 10px; font-weight: 600; padding: .5rem 1.2rem;
}
.stButton button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { background: var(--blue); }

/* match cards */
.match { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 1.1rem 1.25rem; margin: 0 0 .9rem; }
.match-top { display: flex; gap: .9rem; align-items: center; }
.avatar {
  flex: none; width: 2.7rem; height: 2.7rem; border-radius: 50%; background: var(--ink); color: #fff;
  display: grid; place-items: center; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700;
}
.who { flex: 1; min-width: 0; }
.stApp .match .who h3 { margin: 0; padding: 0; font-size: 1.2rem; font-weight: 700; }
.who .sub { color: var(--muted); font-size: .9rem; }
.score { text-align: right; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 1.6rem; line-height: 1; }
.score small { display: block; font-family: 'Public Sans', sans-serif; font-weight: 500; font-size: .75rem; color: var(--muted); margin-top: .25rem; }
.bar { height: 5px; background: #E3E9F1; border-radius: 3px; margin: .9rem 0 .8rem; overflow: hidden; }
.bar div { height: 100%; background: var(--blue); }
.row { display: flex; flex-wrap: wrap; gap: .4rem .5rem; align-items: center; margin: .35rem 0; font-size: .92rem; }
.row .k { color: var(--muted); margin-right: .25rem; }
.hl {
  font-weight: 600; padding: 0 .3em; border-radius: 2px;
  background: linear-gradient(transparent 30%, var(--hl) 30%, var(--hl) 92%, transparent 92%);
}
.bio { margin: .6rem 0 0; font-size: .95rem; line-height: 1.5; }
.muted { color: var(--muted); font-size: .9rem; margin: .4rem 0; }
.contact {
  display: inline-block; margin-top: .8rem; padding: .45rem .9rem; border-radius: 8px;
  background: var(--ink); color: #fff !important; font-weight: 600; font-size: .9rem; text-decoration: none;
}
.contact:hover { background: var(--blue); }
.contact:focus-visible { outline: 3px solid var(--blue); outline-offset: 2px; }
.contact-note { margin-left: .6rem; color: var(--muted); font-size: .85rem; }
</style>
"""


def esc(text):
    """Escape user-typed text before it goes into HTML."""
    return html.escape(str(text or ""))


# ---------- storage ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS students (
            email TEXT PRIMARY KEY, name TEXT, major TEXT, year TEXT,
            courses TEXT, slots TEXT, style TEXT, bio TEXT)"""
    )
    return conn


def save_profile(p):
    with db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO students
               VALUES (:email, :name, :major, :year, :courses, :slots, :style, :bio)""",
            p,
        )


def get_profile(email):
    with db() as conn:
        row = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def all_others(email):
    with db() as conn:
        rows = conn.execute("SELECT * FROM students WHERE email != ?", (email,)).fetchall()
    return [dict(r) for r in rows]


def student_count():
    with db() as conn:
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]


# ---------- matching ----------
def split(text):
    return {x.strip().upper() for x in (text or "").split(",") if x.strip()}


def score(me, other):
    """0-100: same major counts most, then shared courses, free time, and style."""
    pts = 40 if me["major"] == other["major"] else 0
    shared_courses = split(me["courses"]) & split(other["courses"])
    shared_slots = split(me["slots"]) & split(other["slots"])
    pts += min(len(shared_courses) * 15, 30)
    pts += min(len(shared_slots) * 4, 20)
    pts += 10 if me["style"] == other["style"] else 0
    return pts, sorted(shared_courses), sorted(shared_slots)


# ---------- page pieces ----------
def header():
    n = student_count()
    if n:
        joined = f"{n} student{'s' if n != 1 else ''} already on StudyMatch."
    else:
        joined = "No one has joined yet. Be the first from your major."
    st.html(f"""
<div class="nav">
  <span class="mark">StudyMatch</span>
  <span class="navnote">Study partners for college students</span>
</div>
<div class="hero">
  <h1>Study with someone in your major who's taking your classes.</h1>
  <p>Add your courses and free hours. We rank classmates by what you actually share,
     so you spend less time finding a group and more time studying.</p>
  <p class="count">{joined}</p>
</div>
""")


def match_card(pts, o, courses, slots):
    initials = "".join(w[0] for w in o["name"].split()[:2]).upper() or "?"
    first = (o["name"].split() or ["them"])[0]

    shared = ""
    if courses:
        chips = "".join(f'<span class="hl">{esc(c)}</span>' for c in courses)
        shared += f'<div class="row"><span class="k">Shared courses</span>{chips}</div>'
    if slots:
        chips = "".join(
            f'<span class="hl">{esc(s.title().replace("-", " "))}</span>' for s in slots
        )
        shared += f'<div class="row"><span class="k">Both free</span>{chips}</div>'
    if not shared:
        shared = '<p class="muted">No shared courses or free times yet.</p>'

    bio = f'<p class="bio">{esc(o["bio"])}</p>' if o["bio"] else ""

    st.html(f"""
<div class="match">
  <div class="match-top">
    <div class="avatar">{esc(initials)}</div>
    <div class="who">
      <h3>{esc(o["name"])}</h3>
      <div class="sub">{esc(o["major"])}, {esc(o["year"])}. Prefers: {esc(o["style"].lower())}</div>
    </div>
    <div class="score">{pts}%<small>match</small></div>
  </div>
  <div class="bar"><div style="width:{pts}%"></div></div>
  {shared}
  {bio}
  <a class="contact" href="mailto:{esc(o["email"])}?subject=Study%20together%3F">Email {esc(first)}</a>
  <span class="contact-note">{esc(o["email"])}</span>
</div>
""")


# ---------- tabs ----------
def profile_page():
    me = get_profile(st.session_state.get("email", "")) or {}

    name = st.text_input("Name", me.get("name", ""))
    email = st.text_input(
        "School email", me.get("email", ""),
        help="Shown on your card so classmates can contact you. Use an address you're fine sharing.",
    )
    c1, c2 = st.columns(2)
    major = c1.selectbox("Major", MAJORS, index=MAJORS.index(me["major"]) if me else 0)
    year = c2.selectbox("Year", YEARS, index=YEARS.index(me["year"]) if me else 0)
    courses = st.text_input(
        "Courses you want to study for", me.get("courses", ""),
        placeholder="CS101, MATH201, PHYS150",
        help="Separate with commas. Matching ignores capitalization.",
    )

    st.write("When are you free? Tick every slot that works.")
    saved = split(me.get("slots", ""))
    grid = pd.DataFrame(
        [[f"{d}-{t}".upper() in saved for d in DAYS] for t in TIMES],
        index=TIMES, columns=DAYS,
    )
    grid = st.data_editor(grid, width="stretch")

    style = st.radio(
        "How do you like to study?", STYLES, horizontal=True,
        index=STYLES.index(me["style"]) if me else 0,
    )
    bio = st.text_area("Anything else?", me.get("bio", ""), max_chars=200)

    if st.button("Save profile", type="primary"):
        if not name.strip() or "@" not in email:
            st.error("Add your name and a valid email to save.")
            return
        slots = ",".join(f"{d}-{t}" for t in TIMES for d in DAYS if grid.loc[t, d])
        save_profile(dict(
            email=email.strip().lower(), name=name.strip(), major=major, year=year,
            courses=courses, slots=slots, style=style, bio=bio,
        ))
        st.session_state["email"] = email.strip().lower()
        st.success("Profile saved. Open the Find partners tab to see your matches.")


def matches_page():
    me = get_profile(st.session_state.get("email", ""))
    if not me:
        st.write("Already have a profile? Enter your email to see your matches. New here? Fill in the Your profile tab first.")
        lookup = st.text_input("Your school email", key="lookup").strip().lower()
        if lookup:
            if get_profile(lookup):
                st.session_state["email"] = lookup
                st.rerun()
            else:
                st.warning("No profile found for that email. Create one in the Your profile tab.")
        return

    st.subheader(f"Matches for {me['name'].split()[0]}")
    other_majors = st.toggle("Include students from other majors", value=False)

    results = []
    for o in all_others(me["email"]):
        if o["major"] != me["major"] and not other_majors:
            continue
        pts, courses, slots = score(me, o)
        results.append((pts, o, courses, slots))
    results.sort(key=lambda r: r[0], reverse=True)

    if not results:
        st.info(f"No other {me['major']} students have joined yet. Share the link with your classmates.")
        return
    for pts, o, courses, slots in results:
        match_card(pts, o, courses, slots)


# ---------- page ----------
st.markdown(CSS, unsafe_allow_html=True)
header()
tab_profile, tab_find = st.tabs(["Your profile", "Find partners"])
with tab_profile:
    profile_page()
with tab_find:
    matches_page()