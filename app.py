import streamlit as st
from pyairtable import Api
from datetime import datetime
import resend
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import re

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Ladder Company Portal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# AIRTABLE CONNECTION
# ─────────────────────────────────────────────
@st.cache_resource
def get_airtable_api():
    return Api(st.secrets["AIRTABLE_API_KEY"])

@st.cache_resource
def get_tables():
    api = get_airtable_api()
    base = api.base(st.secrets["AIRTABLE_BASE_ID"])
    return {
        "companies": base.table(st.secrets["COMPANIES_TABLE"]),
        "projects": base.table(st.secrets["PROJECTS_TABLE"]),
        "students": base.table(st.secrets["STUDENTS_TABLE"]),
    }

# ─────────────────────────────────────────────
# MAGIC LINK AUTH
# ─────────────────────────────────────────────
def get_serializer():
    return URLSafeTimedSerializer(st.secrets["MAGIC_LINK_SECRET"])

def generate_magic_token(email):
    return get_serializer().dumps(email, salt="magic-link")

def verify_magic_token(token, max_age=3600):
    try:
        return get_serializer().loads(token, salt="magic-link", max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None

def send_magic_link(email, company_name, supervisor_name):
    resend.api_key = st.secrets["RESEND_API_KEY"]
    token = generate_magic_token(email)
    base_url = st.secrets.get("APP_URL", "http://localhost:8501")
    magic_link = f"{base_url}?token={token}"
    try:
        resend.Emails.send({
            "from": st.secrets.get("FROM_EMAIL", "Ladder Internships <onboarding@resend.dev>"),
            "to": [email],
            "subject": "Your Ladder Company Portal Login Link",
            "html": f"""
            <div style="font-family: Georgia, serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="border-bottom: 3px solid #1B2B5E; padding-bottom: 16px; margin-bottom: 24px;">
                    <h2 style="color: #1B2B5E; margin: 0; font-size: 22px; letter-spacing: 0.05em;">
                        LADDER INTERNSHIPS
                    </h2>
                    <p style="color: #4A5568; margin: 4px 0 0 0; font-size: 13px;">Company Portal</p>
                </div>
                <p style="color: #1B2B5E;">Hi {supervisor_name},</p>
                <p style="color: #1B2B5E;">
                    Click below to access your intern dashboard for <strong>{company_name}</strong>:
                </p>
                <p style="margin: 30px 0;">
                    <a href="{magic_link}"
                       style="background: #1B2B5E;
                              color: white; padding: 12px 30px; text-decoration: none;
                              border-radius: 6px; display: inline-block; font-weight: 600;
                              font-family: Arial, sans-serif;">
                        Access Portal &rarr;
                    </a>
                </p>
                <p style="color: #64748B; font-size: 13px;">
                    This link expires in 1 hour. If you didn't request this, you can safely ignore this email.
                </p>
            </div>
            """
        })
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# ─────────────────────────────────────────────
# FIELD MAPPINGS
# ─────────────────────────────────────────────
COMPANY_FIELDS = {
    "unique_id":          "Company Unique ID",
    "name":               "Company Name",
    "industry":           "Company Industry",
    "size":               "Company Size",
    "supervisor_name":    "Who would be the supervisor for the Ladder Intern?",
    "supervisor_email":   "Supervisor Email",
    "description":        "Ladder-Revised Company Description",
    "website":            "What is your company's website?",
    "supervisor_linkedin":"Supervisor LinkedIn",
    "poc_email":          "POC Email",
    "poc_title":          "POC Title",
    "address":            "Company Address",
}

PROJECT_FIELDS = {
    "unique_id":          "Unique Record ID_Company Projects",
    "name":               "Name of the Project",
    "manager":            "Manager/PTL",
    "category":           "Project Category",
    "confirmed_signups":  "# Confirmed sign ups",
    "description":        "Project Description",
    "skills":             "Skills needed for the project",
    "wde_link":           "Link to WDE",
    "max_interns":        "Max #interns possible",
    "timezones":          "Timezones of assigned students",
    "meeting_day":        "Day for Weekly meeting",
    "final_output":       "Final Output of the project",
    "cohort":             "Which cohort for this project",
    "total_meetings":     "How many meetings have you had? Rollup (from Notes/Feedback (Company, Student, LC))",
    "week_1":             "Week 1 - Meeting Occurred",
    "week_2":             "Week 2 - Meeting Occurred",
    "week_3":             "Week 3 - Meeting Occurred",
    "week_4":             "Week 4 - Meeting Occurred",
    "week_5":             "Week 5 - Meeting Occurred",
    "week_6":             "Week 6 - Meeting Occurred",
    "week_7":             "Week 7 - Meeting Occurred",
    "week_8":             "Week 8 - Meeting Occurred",
}

STUDENT_FIELDS = {
    "student_id":         "Student ID",
    "full_name":          "Student's Full Name",
    "email":              "Student's Email",
    "preferred_name":     "Student's First/Preferred Name",
    "program_type":       "Program Type",
    "project_assigned":   "Project Assigned",
    "meetings_count":     "# of meetings (from Company Update Forms)",
    "weekly_notes":       "Manager Weekly Submissions Date and Notes",
    "timezone":           "Timezone",
    "grade":              "Current Grade",
    "gpa":                "What is your GPA at school? (If a current student)",
    "interest_reason":    "Student Response: Why are you interested in this industry?",
    "candidacy_reason":   "Student Response: Why are you a good candidate for our Internship program?",
    "resume_url":         "Resume (URL) (from Submissions Table)",
}

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1B2B5E;
        margin-bottom: 0.25rem;
        letter-spacing: -0.01em;
    }
    .sub-header {
        font-size: 1rem;
        color: #4A5568;
        margin-bottom: 1.75rem;
    }
    .project-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 2px 8px rgba(27,43,94,0.08);
        border-left: 4px solid #1B2B5E;
        margin-bottom: 1.25rem;
    }
    .week-badge-done {
        display: inline-block;
        background: #EEF2FF;
        color: #1B2B5E;
        border: 1px solid #1B2B5E;
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }
    .week-badge-pending {
        display: inline-block;
        background: #F3F4F6;
        color: #9CA3AF;
        border: 1px solid #D1D5DB;
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.78rem;
        margin: 2px;
    }
    .preview-banner {
        background: #EEF2FF;
        border: 1px solid #1B2B5E;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
        color: #1B2B5E;
    }
    .info-label {
        font-size: 0.8rem;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.1rem;
    }
    /* Navy sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F1B3D;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stCaption p { color: #94A3B8 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); }
    [data-testid="stSidebar"] .stButton button {
        background-color: rgba(255,255,255,0.08);
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.25);
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: rgba(255,255,255,0.18);
        border-color: rgba(255,255,255,0.45);
    }
    [data-testid="stSidebar"] .stRadio > div { gap: 0.25rem !important; }
    [data-testid="stSidebar"] .stRadio > div > label {
        background-color: transparent !important;
        border-radius: 6px !important;
        padding: 0.6rem 1rem !important;
        margin: 0 !important;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background-color: rgba(255,255,255,0.08) !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background-color: rgba(255,255,255,0.12) !important;
        border-left: 3px solid #7B93D4 !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label > div:first-child {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for _key, _default in [
    ("authenticated",     False),
    ("company_name",      None),
    ("company_id",        None),
    ("supervisor_name",   None),
    ("supervisor_email",  None),
    ("is_preview",        False),
    ("magic_link_sent",   False),
    ("team_unlocked",     False),
    ("selected_intern_id", None),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# ─────────────────────────────────────────────
# DATA FUNCTIONS
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_company_by_email(email):
    """Find a company record by supervisor email."""
    tables = get_tables()
    try:
        safe = email.replace("'", "\\'")
        records = tables["companies"].all(
            formula=f"LOWER({{Supervisor Email}}) = LOWER('{safe}')"
        )
        if records:
            r = records[0]
            f = r["fields"]
            return {
                "id":                 r["id"],
                "name":               f.get(COMPANY_FIELDS["name"], ""),
                "unique_id":          f.get(COMPANY_FIELDS["unique_id"], ""),
                "industry":           f.get(COMPANY_FIELDS["industry"], ""),
                "size":               f.get(COMPANY_FIELDS["size"], ""),
                "supervisor_name":    f.get(COMPANY_FIELDS["supervisor_name"], ""),
                "supervisor_email":   f.get(COMPANY_FIELDS["supervisor_email"], ""),
                "description":        f.get(COMPANY_FIELDS["description"], ""),
                "website":            f.get(COMPANY_FIELDS["website"], ""),
                "supervisor_linkedin":f.get(COMPANY_FIELDS["supervisor_linkedin"], ""),
                "poc_email":          f.get(COMPANY_FIELDS["poc_email"], ""),
                "poc_title":          f.get(COMPANY_FIELDS["poc_title"], ""),
                "address":            f.get(COMPANY_FIELDS["address"], ""),
            }
    except Exception as e:
        st.error(f"Error finding company: {e}")
    return None

@st.cache_data(ttl=300)
def get_projects_for_company(company_name):
    """Get all Company Projects belonging to a given company."""
    tables = get_tables()
    try:
        safe = company_name.replace("'", "\\'")
        # cell_format="string" makes Airtable return linked record fields
        # as their display names instead of raw record IDs.
        records = tables["projects"].all(
            formula=f"FIND('{safe}', {{Unique Record ID_Company Projects}}) > 0",
            cell_format="string",
            user_locale="en-us",
            time_zone="America/New_York",
        )
        projects = []
        for r in records:
            f = r["fields"]
            # With cell_format="string", checkboxes return "true"/"false" strings
            week_data = {
                f"week_{i}": f.get(PROJECT_FIELDS[f"week_{i}"], "").lower() == "true"
                for i in range(1, 9)
            }
            # confirmed_signups comes back as a string; coerce safely
            raw_signups = f.get(PROJECT_FIELDS["confirmed_signups"], "0") or "0"
            try:
                confirmed_signups = int(float(str(raw_signups)))
            except (ValueError, TypeError):
                confirmed_signups = 0

            projects.append({
                "id":               r["id"],
                "unique_id":        f.get(PROJECT_FIELDS["unique_id"], ""),
                "name":             f.get(PROJECT_FIELDS["name"], ""),
                "manager":          f.get(PROJECT_FIELDS["manager"], ""),
                "category":         f.get(PROJECT_FIELDS["category"], ""),
                "confirmed_signups":confirmed_signups,
                "description":      f.get(PROJECT_FIELDS["description"], ""),
                "skills":           f.get(PROJECT_FIELDS["skills"], ""),
                "wde_link":         f.get(PROJECT_FIELDS["wde_link"], ""),
                "max_interns":      f.get(PROJECT_FIELDS["max_interns"], ""),
                "timezones":        f.get(PROJECT_FIELDS["timezones"], ""),
                "meeting_day":      f.get(PROJECT_FIELDS["meeting_day"], ""),
                "final_output":     f.get(PROJECT_FIELDS["final_output"], ""),
                "cohort":           f.get(PROJECT_FIELDS["cohort"], ""),
                "total_meetings":   f.get(PROJECT_FIELDS["total_meetings"], "0") or "0",
                **week_data,
            })
        return projects
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
        return []

@st.cache_data(ttl=300)
def get_students_for_company(company_name):
    """Get all Student Applications assigned to a given company."""
    tables = get_tables()
    try:
        safe = company_name.replace("'", "\\'")
        records = tables["students"].all(
            formula=f"FIND('{safe}', {{Student ID}}) > 0"
        )
        students = []
        for r in records:
            f = r["fields"]
            students.append({
                "id":               r["id"],
                "student_id":       f.get(STUDENT_FIELDS["student_id"], ""),
                "full_name":        f.get(STUDENT_FIELDS["full_name"], ""),
                "preferred_name":   f.get(STUDENT_FIELDS["preferred_name"], ""),
                "email":            f.get(STUDENT_FIELDS["email"], ""),
                "program_type":     f.get(STUDENT_FIELDS["program_type"], ""),
                "project_assigned": f.get(STUDENT_FIELDS["project_assigned"], ""),
                "meetings_count":   f.get(STUDENT_FIELDS["meetings_count"], ""),
                "weekly_notes":     f.get(STUDENT_FIELDS["weekly_notes"], ""),
                "timezone":         f.get(STUDENT_FIELDS["timezone"], ""),
                "grade":            f.get(STUDENT_FIELDS["grade"], ""),
                "gpa":              f.get(STUDENT_FIELDS["gpa"], ""),
                "interest_reason":  f.get(STUDENT_FIELDS["interest_reason"], ""),
                "candidacy_reason": f.get(STUDENT_FIELDS["candidacy_reason"], ""),
                "resume_url":       f.get(STUDENT_FIELDS["resume_url"], ""),
            })
        return students
    except Exception as e:
        st.error(f"Error fetching students: {e}")
        return []

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def parse_meetings_count(value):
    """Handle Airtable rollup formats: number, '1,1,1', or list."""
    if not value and value != 0:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
        return len(parts)
    return 0

def parse_weekly_notes(notes_text):
    """Parse the Manager Weekly Submissions rollup text into [{date, notes}]."""
    if not notes_text:
        return []
    # Split entries on newline + comma (Airtable rollup separator)
    raw_entries = re.split(r'\n\s*,\s*', notes_text.strip())
    date_pattern = re.compile(
        r'^(.*?)\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\s*$',
        re.DOTALL
    )
    result = []
    for entry in raw_entries:
        entry = entry.strip().lstrip(',').strip()
        if not entry:
            continue
        match = date_pattern.search(entry)
        if match:
            result.append({"date": match.group(2), "notes": match.group(1).strip()})
        else:
            result.append({"date": "", "notes": entry})
    result.sort(key=lambda x: x["date"] or "0000", reverse=True)
    return result

def format_date(date_str):
    """Format an ISO date string to a human-readable form."""
    if not date_str:
        return "Not set"
    if isinstance(date_str, list):
        date_str = date_str[0] if date_str else ""
    if not date_str:
        return "Not set"
    try:
        ds = date_str[:10]
        date_obj = datetime.strptime(ds, "%Y-%m-%d")
        day = date_obj.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{date_obj.strftime('%B')} {day}{suffix}, {date_obj.year}"
    except Exception:
        return date_str

def meetings_completed(project):
    """Count how many of the 8 weekly meetings have occurred."""
    return sum(1 for i in range(1, 9) if project.get(f"week_{i}"))

def render_week_tracker(project):
    """Return HTML badges for each of the 8 internship weeks."""
    badges = []
    for i in range(1, 9):
        if project.get(f"week_{i}"):
            badges.append(f'<span class="week-badge-done">W{i} ✓</span>')
        else:
            badges.append(f'<span class="week-badge-pending">W{i}</span>')
    return "".join(badges)

def safe_url(url):
    """Ensure a URL has a scheme."""
    if not url:
        return url
    if not url.startswith("http"):
        return "https://" + url
    return url

# ─────────────────────────────────────────────
# MAGIC LINK TOKEN CHECK
# ─────────────────────────────────────────────
def check_magic_link_token():
    qp = st.query_params
    if "token" in qp and not st.session_state.authenticated:
        email = verify_magic_token(qp["token"])
        if email:
            company = get_company_by_email(email)
            if company:
                st.session_state.authenticated    = True
                st.session_state.company_name     = company["name"]
                st.session_state.company_id       = company["id"]
                st.session_state.supervisor_name  = company["supervisor_name"]
                st.session_state.supervisor_email = company["supervisor_email"]
                st.session_state.is_preview       = False
                st.query_params.clear()
                st.rerun()
        else:
            st.error("This login link has expired or is invalid. Please request a new one.")
            st.query_params.clear()

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login_page():
    st.markdown("""
    <style>
        .stApp { background-color: #0F1B3D; }
        .main-header { color: #FFFFFF !important; letter-spacing: 0.03em; }
        .sub-header { color: #A0B0D0 !important; }
        .stApp h3, .stApp p, .stApp label, .stApp span { color: #FFFFFF !important; }
        .stApp input {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        .stApp .stButton > button,
        .stApp [data-testid="stFormSubmitButton"] > button {
            background-color: #1B2B5E !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        .stApp .stButton > button:hover,
        .stApp [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #2A3F80 !important;
        }
        .stApp .stButton > button p,
        .stApp [data-testid="stFormSubmitButton"] > button p { color: #FFFFFF !important; }
        .stApp details {
            background-color: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
        }
        .stApp details summary,
        .stApp details summary * { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<img src="data:image/png;base64,{}" width="320" style="filter: brightness(0) invert(1); margin-bottom: 1rem;">'.format(
            __import__('base64').b64encode(open('assets/ladder_logo.png', 'rb').read()).decode()
        ),
        unsafe_allow_html=True
    )
    st.markdown('<p class="main-header">Company Portal</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Track your interns progress through the program</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.magic_link_sent:
            st.success("Check your email! We've sent you a magic link to access the portal.")
            st.info("The link will expire in 1 hour.")
            if st.button("Send another link"):
                st.session_state.magic_link_sent = False
                st.rerun()
        else:
            st.markdown("### Supervisor Email")
            st.markdown("Sign in with the email you registered with Lumiere Ladder.")
            with st.form("login_form"):
                email = st.text_input(
                    "Email Address",
                    placeholder="your@company.com",
                    label_visibility="collapsed"
                )
                submitted = st.form_submit_button("Send Magic Link", use_container_width=True)
                if submitted and email:
                    company = get_company_by_email(email)
                    if company:
                        if send_magic_link(email, company["name"], company["supervisor_name"]):
                            st.session_state.magic_link_sent = True
                            st.rerun()
                    else:
                        st.error("Email not found. Please use the supervisor email you registered with Lumiere Ladder.")

        st.markdown("---")

        # Team preview access
        if st.session_state.team_unlocked:
            st.markdown("#### Team Preview Mode")
            st.caption("Preview any company's portal view")
            with st.form("preview_form"):
                preview_email = st.text_input(
                    "Company Supervisor Email",
                    placeholder="supervisor@company.com"
                )
                preview_submitted = st.form_submit_button("Preview as Company", use_container_width=True)
                if preview_submitted:
                    company = get_company_by_email(preview_email)
                    if company:
                        st.session_state.authenticated    = True
                        st.session_state.company_name     = company["name"]
                        st.session_state.company_id       = company["id"]
                        st.session_state.supervisor_name  = company["supervisor_name"]
                        st.session_state.supervisor_email = company["supervisor_email"]
                        st.session_state.is_preview       = True
                        st.rerun()
                    else:
                        st.error("Company not found.")
        else:
            with st.expander("Team Access"):
                with st.form("team_unlock_form"):
                    admin_key = st.text_input("Admin Key", type="password", placeholder="Enter admin key")
                    unlock_submitted = st.form_submit_button("Unlock", use_container_width=True)
                    if unlock_submitted:
                        if admin_key == st.secrets["ADMIN_KEY"]:
                            st.session_state.team_unlocked = True
                            st.rerun()
                        else:
                            st.error("Invalid admin key.")

# ─────────────────────────────────────────────
# COMPANY OVERVIEW
# ─────────────────────────────────────────────
def show_company_overview():
    company_name = st.session_state.company_name
    company  = get_company_by_email(st.session_state.supervisor_email)
    projects = get_projects_for_company(company_name)
    students = get_students_for_company(company_name)

    st.markdown('<p class="main-header">Company Overview</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="sub-header">Welcome back, {st.session_state.supervisor_name}! '
        f'Here\'s a summary of your Ladder internship program.</p>',
        unsafe_allow_html=True
    )

    # ── Summary metrics ──
    total_interns = len(students)
    meetings_total = sum(meetings_completed(p) for p in projects)
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Active Projects", len(projects))
    with col_m2:
        st.metric("Assigned Interns", total_interns)
    with col_m3:
        st.metric("Total Meetings Held", meetings_total)

    st.markdown("---")

    # ── Company profile ──
    st.markdown("### About Your Company")
    if company:
        col1, col2 = st.columns([2, 1])
        with col1:
            if company["description"]:
                st.markdown(company["description"])
            else:
                st.caption("No description on file.")
        with col2:
            if company["industry"]:
                st.markdown('<p class="info-label">Industry</p>', unsafe_allow_html=True)
                st.markdown(company["industry"])
            if company["size"]:
                st.markdown('<p class="info-label">Company Size</p>', unsafe_allow_html=True)
                st.markdown(str(company["size"]))
            if company["website"]:
                st.markdown('<p class="info-label">Website</p>', unsafe_allow_html=True)
                st.markdown(f"[{company['website']}]({safe_url(company['website'])})")
            if company["address"]:
                st.markdown('<p class="info-label">Location</p>', unsafe_allow_html=True)
                st.markdown(company["address"])

        st.markdown("---")

        # Supervisor / POC info
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Supervisor**")
            sup_name  = company["supervisor_name"] or "—"
            sup_email = company["supervisor_email"] or "—"
            sup_li    = company["supervisor_linkedin"]
            st.markdown(f"{sup_name} — {sup_email}")
            if sup_li:
                st.markdown(f"[LinkedIn →]({safe_url(sup_li)})")
        with col4:
            poc_email = company.get("poc_email", "")
            poc_title = company.get("poc_title", "")
            if poc_email and poc_email != company["supervisor_email"]:
                st.markdown("**Additional Point of Contact**")
                st.markdown(f"{poc_title or 'POC'}: {poc_email}")

    st.markdown("---")
    st.info("Use **Your Projects** in the sidebar to view your project details and meeting progress.")

def extract_cohort_from_student_id(student_id):
    """Extract cohort name from 'StudentName | CompanyName | CohortName' format."""
    if not student_id:
        return ""
    parts = student_id.split("|")
    if len(parts) >= 3:
        return parts[-1].strip().strip('"').strip("'")
    return ""

# ─────────────────────────────────────────────
# YOUR PROJECTS VIEW
# ─────────────────────────────────────────────
def show_projects():
    company_name = st.session_state.company_name
    projects     = get_projects_for_company(company_name)

    st.markdown('<p class="main-header">Your Projects</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">View project details and track weekly meeting progress.</p>',
        unsafe_allow_html=True
    )

    if not projects:
        st.info("No projects assigned yet.")
        return

    # ── Cohort filter ──
    cohorts = sorted(set(p["cohort"] for p in projects if p["cohort"]))
    if len(cohorts) > 1:
        cohort_options = ["All Cohorts"] + cohorts
        selected_cohort = st.selectbox("Filter by cohort", cohort_options, key="project_cohort_filter")
        if selected_cohort != "All Cohorts":
            projects = [p for p in projects if p["cohort"] == selected_cohort]
    elif cohorts:
        st.caption(f"Cohort: {cohorts[0]}")

    st.markdown(f"**{len(projects)}** project{'s' if len(projects) != 1 else ''}")
    st.markdown("---")

    for project in projects:
        completed = meetings_completed(project)
        week_html = render_week_tracker(project)
        category  = project["category"] or "—"
        cohort    = project["cohort"] or "—"
        n_interns = project["confirmed_signups"]

        st.markdown(
            f'<div class="project-card">'
            f'<h4 style="margin:0 0 0.4rem 0;">{project["name"]}</h4>'
            f'<p style="color:#4A5568;margin:0 0 0.75rem 0;font-size:0.88rem;">'
            f'Category: {category}&nbsp;&nbsp;|&nbsp;&nbsp;Cohort: {cohort}'
            f'&nbsp;&nbsp;|&nbsp;&nbsp;Interns: {n_interns}'
            f'</p>'
            f'<p style="margin:0 0 0.4rem 0;font-size:0.85rem;font-weight:600;color:#1B2B5E;">'
            f'Meeting Progress — {completed}/8 weeks completed</p>'
            f'{week_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        if project.get("wde_link"):
            st.markdown(f"[📄 View Work Description & Evaluation]({project['wde_link']})")

        with st.expander("View full project details"):
            c1, c2 = st.columns(2)
            with c1:
                if project["description"]:
                    st.markdown("**Project Description**")
                    st.markdown(project["description"])
            with c2:
                if project["final_output"]:
                    st.markdown("**Final Deliverable**")
                    st.markdown(project["final_output"])
            if project["skills"]:
                st.markdown("**Skills Required**")
                st.markdown(project["skills"])
            cd1, cd2 = st.columns(2)
            with cd1:
                if project["meeting_day"]:
                    st.markdown(f"**Weekly Meeting Day:** {project['meeting_day']}")
            with cd2:
                if project["timezones"]:
                    st.markdown(f"**Intern Timezones:** {project['timezones']}")
            if project["max_interns"]:
                st.markdown(f"**Max Interns:** {project['max_interns']}")

        st.markdown("---")

# ─────────────────────────────────────────────
# INTERN PROFILE TABS
# ─────────────────────────────────────────────
def show_intern_background(student):
    st.markdown("### Intern Background")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Current Grade**")
        st.markdown(student["grade"] or "Not specified")
        st.markdown("**GPA**")
        st.markdown(student["gpa"] or "Not specified")
        st.markdown("**Timezone**")
        st.markdown(student["timezone"] or "Not specified")
    with col2:
        st.markdown("**Program Type**")
        st.markdown(student["program_type"] or "Not specified")
        st.markdown("**Email**")
        st.markdown(student["email"] or "Not specified")

    st.markdown("---")
    with st.expander("💡 Why are they interested in this industry?", expanded=True):
        st.markdown(student["interest_reason"] or "Not provided.")
    with st.expander("⭐ Why are they a strong candidate?", expanded=True):
        st.markdown(student["candidacy_reason"] or "Not provided.")

def show_intern_meetings(student):
    st.markdown("### Meeting Activity")

    meetings = parse_meetings_count(student.get("meetings_count", 0))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Meetings Held", meetings)
    with col2:
        remaining = max(0, 8 - meetings)
        st.metric("Weeks Remaining", remaining)
    with col3:
        pct = int((meetings / 8) * 100) if meetings <= 8 else 100
        st.metric("Program Progress", f"{pct}%")

    if meetings > 0:
        st.progress(min(meetings / 8, 1.0))

    st.markdown("---")
    st.markdown("### Weekly Meeting Notes")
    notes = parse_weekly_notes(student.get("weekly_notes", ""))
    if not notes:
        st.info("No meeting notes recorded yet.")
    else:
        for note in notes:
            date_label = format_date(note["date"]) if note["date"] else "Undated entry"
            with st.expander(f"📅 {date_label}"):
                st.markdown(note["notes"] or "No notes recorded.")

def show_intern_resume(student):
    st.markdown("### Resume")
    resume = student.get("resume_url", "")
    if isinstance(resume, list):
        resume = ", ".join(str(u) for u in resume if u)
    if resume:
        urls = [u.strip() for u in resume.split(",") if u.strip().startswith("http")]
        if urls:
            for i, url in enumerate(urls):
                label = f"View Resume" if len(urls) == 1 else f"View Resume {i + 1}"
                st.markdown(f"[📄 {label}]({url})")
        else:
            st.markdown(resume)
    else:
        st.info("No resume submitted yet.")

# ─────────────────────────────────────────────
# YOUR INTERNS VIEW
# ─────────────────────────────────────────────
def show_interns():
    company_name = st.session_state.company_name
    students     = get_students_for_company(company_name)

    st.markdown('<p class="main-header">Your Interns</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">View profiles and track progress for each intern assigned to your company.</p>',
        unsafe_allow_html=True
    )

    if not students:
        st.info("No interns have been assigned to your company yet.")
        return

    # ── Intern profile drill-down ──
    if st.session_state.selected_intern_id:
        selected = next(
            (s for s in students if s["id"] == st.session_state.selected_intern_id),
            None
        )
        if selected:
            if st.button("← Back to Intern List"):
                st.session_state.selected_intern_id = None
                st.rerun()

            preferred = selected["preferred_name"]
            display_name = selected["full_name"]
            st.markdown(f"## {display_name}")
            if preferred and preferred != display_name:
                st.caption(f"Goes by: {preferred}")

            st.markdown("---")
            tab1, tab2, tab3 = st.tabs([
                "🎓 Background",
                "📋 Meeting Activity",
                "📄 Resume",
            ])
            with tab1:
                show_intern_background(selected)
            with tab2:
                show_intern_meetings(selected)
            with tab3:
                show_intern_resume(selected)
            return

    # ── Intern list ──
    # Attach cohort to each student from their student_id field
    for s in students:
        s["cohort"] = extract_cohort_from_student_id(s.get("student_id", ""))

    # Cohort filter
    cohorts = sorted(set(s["cohort"] for s in students if s["cohort"]))
    filtered = students
    if len(cohorts) > 1:
        col_f1, col_f2 = st.columns([2, 3])
        with col_f1:
            cohort_options = ["All Cohorts"] + cohorts
            selected_cohort = st.selectbox("Filter by cohort", cohort_options, key="intern_cohort_filter")
            if selected_cohort != "All Cohorts":
                filtered = [s for s in students if s["cohort"] == selected_cohort]
        with col_f2:
            search = st.text_input(
                "Search interns",
                placeholder="🔍 Type a name...",
                label_visibility="collapsed",
                key="intern_search"
            )
            if search:
                filtered = [s for s in filtered if search.lower() in s["full_name"].lower()]
    else:
        search = st.text_input(
            "Search interns",
            placeholder="🔍 Type a name...",
            label_visibility="collapsed"
        )
        if search:
            filtered = [s for s in students if search.lower() in s["full_name"].lower()]

    _cohort_label = ""
    if len(cohorts) > 1 and "intern_cohort_filter" in st.session_state:
        _sel = st.session_state["intern_cohort_filter"]
        if _sel and _sel != "All Cohorts":
            _cohort_label = f" in {_sel}"
    st.markdown(
        f"**{len(filtered)}** intern{'s' if len(filtered) != 1 else ''}"
        + (_cohort_label or " assigned to your company")
    )

    st.markdown("---")
    for student in filtered:
        meetings = parse_meetings_count(student.get("meetings_count", 0))
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            if st.button(student["full_name"], key=f"intern_{student['id']}", use_container_width=True):
                st.session_state.selected_intern_id = student["id"]
                st.rerun()
        with col2:
            tz = student["timezone"] or "—"
            st.caption(f"🌍 {tz}")
        with col3:
            grade = student["grade"] or "—"
            st.caption(f"Grade {grade}")
        with col4:
            st.caption(f"📅 {meetings} meeting{'s' if meetings != 1 else ''}")
        st.markdown("---")

# ─────────────────────────────────────────────
# RESOURCES VIEW
# ─────────────────────────────────────────────
def show_resources():
    st.markdown('<p class="main-header">Resources</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Helpful links and tools for hosting a Ladder intern.</p>',
        unsafe_allow_html=True
    )

    resources = [
        {
            "title":       "Ladder Supervisor Guide",
            "description": "Everything you need to know about hosting a Ladder intern — expectations, best practices, and program timelines.",
            "url":         "",
        },
        {
            "title":       "Weekly Meeting Update Form",
            "description": "Submit your notes and intern progress after each weekly meeting. This keeps the Ladder team informed.",
            "url":         "",
        },
        {
            "title":       "Ladder Program Overview",
            "description": "An overview of the 8-week internship structure, milestones, and what interns are expected to deliver.",
            "url":         "",
        },
        {
            "title":       "Contact Your Program Manager",
            "description": "Have a question or concern about your intern? Reach out to the Ladder program team.",
            "url":         "",
        },
    ]

    for resource in resources:
        if resource["url"]:
            link_html = (
                f'<a href="{resource["url"]}" target="_blank" '
                f'style="color: #1B2B5E; text-decoration: none; font-weight: 600;">Open &rarr;</a>'
            )
        else:
            link_html = '<span style="color:#999;font-size:0.85rem;">Link coming soon</span>'

        st.markdown(
            f'<div style="background: #FAFAFA; border: 1px solid #E5E7EB; '
            f'border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem;">'
            f'<h4 style="margin: 0 0 0.35rem 0;">{resource["title"]}</h4>'
            f'<p style="margin: 0 0 0.75rem 0; color: #555; font-size:0.93rem;">'
            f'{resource["description"]}</p>'
            f'{link_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────
# DASHBOARD SHELL
# ─────────────────────────────────────────────
def show_dashboard():
    with st.sidebar:
        st.markdown(
        '<img src="data:image/png;base64,{}" width="55" style="filter: brightness(0) invert(1); margin-bottom: 0.5rem;">'.format(
            __import__('base64').b64encode(open('assets/ladder_logo_symbol.png','rb').read()).decode()
        ),
        unsafe_allow_html=True
    )
        st.markdown(f"### {st.session_state.company_name}")
        st.caption(f"Supervisor: {st.session_state.supervisor_name}")

        if st.session_state.is_preview:
            st.warning("👁️ Preview Mode")

        st.markdown("---")

        view = st.radio(
            "Navigation",
            ["🏢 Company Overview", "📁 Your Projects", "👥 Your Interns", "📚 Resources"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

        if st.button("🚪 Logout"):
            st.session_state.authenticated    = False
            st.session_state.company_name     = None
            st.session_state.company_id       = None
            st.session_state.supervisor_name  = None
            st.session_state.supervisor_email = None
            st.session_state.is_preview       = False
            st.session_state.selected_intern_id = None
            st.rerun()

    if st.session_state.is_preview:
        st.markdown(
            f'<div class="preview-banner">👁️ <strong>Preview Mode:</strong> '
            f'Viewing as {st.session_state.company_name}</div>',
            unsafe_allow_html=True
        )

    if view == "🏢 Company Overview":
        show_company_overview()
    elif view == "📁 Your Projects":
        show_projects()
    elif view == "👥 Your Interns":
        show_interns()
    else:
        show_resources()

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    check_magic_link_token()
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
