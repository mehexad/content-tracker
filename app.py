import streamlit as st
import pandas as pd
from datetime import datetime
import random
import smtplib
from email.mime.text import MIMEText
import hashlib
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION & CONSTANTS ---
APP_NAME = "Channel One Content Tracker"
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/c/c3/%E0%A6%9A%E0%A7%8D%E0%A6%AF%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B2_%E0%A6%93%E0%A6%AF%E0%A6%BC%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B2_%E0%A6%92%E0%A6%AF%E0%A6%BC%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B2_%E0%A6%B2%E0%A7%8B%E0%A6%97%E0%A7%8B.svg"

# Google Sheet Details
CONTENT_SHEET_ID = "1byGzAKrYovR29-LxtmffLMjtsIcdv3b5RXbUq4EK9VA"
CONTENT_SHEET_NAME = "2026 JULY"
USER_SHEET_ID = "117tCpIN4vBNVOO3b5P5b7yC2kOo_gh5SThanT7rM860"
USER_SHEET_NAME = "FOR CONTENT TRACKER DETAILS"

# Email Configuration for OTP (put the real value in st.secrets, NOT here)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = st.secrets.get("email", {}).get("sender_email", "")
SENDER_PASSWORD = st.secrets.get("email", {}).get("sender_password", "")

CONTENT_COLUMNS = ["Date", "Slug Name", "Headline/Caption", "Sponsor", "Uploader Email",
                    "FB", "YT", "IG", "Threads", "Dailymotion", "TikTok", "LinkedIn",
                    "Bluesky", "Reddit", "Notes"]

USER_COLUMNS = ["Name", "Username", "Office ID", "Email", "Phone", "Blood Group", "PasswordHash"]

# --- SYSTEM UTILITIES ---
def hash_password(password):
    return hashlib.sha256(str.encode(password.strip())).hexdigest()

def send_otp_email(target_email, otp_code):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        st.error("Email is not configured. Add [email] sender_email / sender_password to Streamlit secrets.")
        return False
    try:
        msg = MIMEText(f"Your Channel One Portal Verification Code is: {otp_code}\nValid for 5 minutes.")
        msg['Subject'] = "Channel One Security OTP Verification"
        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [target_email], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Dispatch Error: {e}")
        return False

# --- GOOGLE SHEETS CONNECTION (real read + write via service account) ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

@st.cache_resource(show_spinner=False)
def get_gspread_client():
    if "gcp_service_account" not in st.secrets:
        st.error(
            "Google service account credentials are missing. "
            "Add a [gcp_service_account] block to your Streamlit secrets "
            "(see setup instructions)."
        )
        st.stop()
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)

def get_worksheet(sheet_id, sheet_name):
    client = get_gspread_client()
    sh = client.open_by_key(sheet_id)
    try:
        return sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # Create the tab with headers if it does not exist yet
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=20)
        return ws

def ensure_headers(ws, expected_columns):
    values = ws.get_all_values()
    if not values or values[0] == [] or all(c == "" for c in values[0]):
        ws.update("A1", [expected_columns])
        return expected_columns
    return values[0]

@st.cache_data(ttl=30, show_spinner=False)
def read_sheet_as_df(sheet_id, sheet_name, _cache_key):
    ws = get_worksheet(sheet_id, sheet_name)
    records = ws.get_all_records()
    return pd.DataFrame(records)

def append_row_matching_headers(sheet_id, sheet_name, expected_columns, data_dict):
    """Writes a row to the sheet, aligning values to whatever the header row
    order actually is (falls back to expected_columns if the sheet is empty)."""
    ws = get_worksheet(sheet_id, sheet_name)
    headers = ensure_headers(ws, expected_columns)
    row = [str(data_dict.get(h, "")) for h in headers]
    ws.append_row(row, value_input_option="USER_ENTERED")

def find_user_row(login_id):
    ws = get_worksheet(USER_SHEET_ID, USER_SHEET_NAME)
    headers = ensure_headers(ws, USER_COLUMNS)
    records = ws.get_all_records()
    login_id_clean = login_id.strip().lower()
    for rec in records:
        candidates = [
            str(rec.get("Username", "")).strip().lower(),
            str(rec.get("Email", "")).strip().lower(),
            str(rec.get("Phone", "")).strip().lower(),
        ]
        if login_id_clean in candidates and login_id_clean != "":
            return rec
    return None

# --- INITIALIZE SESSION STATES ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'otp_sent' not in st.session_state: st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None
if 'reg_data' not in st.session_state: st.session_state.reg_data = {}
if 'fp_otp_sent' not in st.session_state: st.session_state.fp_otp_sent = False
if 'fp_generated_otp' not in st.session_state: st.session_state.fp_generated_otp = None
if 'fp_email' not in st.session_state: st.session_state.fp_email = ""

# --- PAGE CONFIG ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🎬")

# --- THEME CSS ---
st.markdown(f"""
    <style>
    @media (prefers-color-scheme: dark) {{
        .stApp {{ background-color: #0B192C !important; }}
        html, body, [data-testid="stWidgetLabel"], p, h1, h2, h3, h4, li, span, label, .stMarkdownDiv {{
            color: #ffc709 !important;
        }}
        div[data-testid="stForm"] {{
            border: 1px solid #ffc709 !important;
            background: linear-gradient(135deg, rgba(30, 62, 98, 0.4) 0%, rgba(11, 25, 44, 0.6) 100%) !important;
        }}
        .popup-box {{ border-left: 5px solid #ffc709 !important; background: rgba(30, 62, 98, 0.4) !important; color: #ffc709 !important; }}
        .metric-card {{ border: 1px solid #ffc709 !important; background: linear-gradient(135deg, rgba(30, 62, 98, 0.5) 0%, rgba(11, 25, 44, 0.7) 100%) !important; }}
        [data-testid="stSidebar"] {{ background-color: #0B192C !important; border-right: 1px solid #ffc709 !important; }}
    }}
    @media (prefers-color-scheme: light) {{
        .stApp {{ background-color: #FFFFFF !important; }}
        html, body, [data-testid="stWidgetLabel"], p, h1, h2, h3, h4, li, span, label, .stMarkdownDiv, .stRadio, div[data-baseweb="radio"] {{
            color: #000000 !important;
        }}
        div[data-testid="stForm"] {{ border: 2px solid #000000 !important; background: #FAFAFA !important; }}
        .popup-box {{ border-left: 5px solid #000000 !important; background: #EFEFEF !important; color: #000000 !important; }}
        .metric-card {{ border: 2px solid #000000 !important; background: #F0F2F6 !important; }}
        [data-testid="stSidebar"] {{ background-color: #FAFAFA !important; border-right: 1px solid #000000 !important; }}
    }}
    .metric-card {{ padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 15px; }}
    .popup-box {{ border-radius: 10px; padding: 15px; margin-bottom: 12px; font-size: 0.9rem; }}
    div[data-testid="stForm"] {{ border-radius: 20px; padding: 25px; }}
    </style>
""", unsafe_allow_html=True)

# --- USER AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.image(LOGO_URL, width=150)
        st.title(APP_NAME)
        st.subheader("Secure Access Gateway")
        auth_mode = st.radio("Choose Action", ["Login", "Registration", "Forgot Password"])

    with col_r:
        if auth_mode == "Login":
            st.markdown("### 🔐 Member Login")
            with st.form("login_form"):
                login_id = st.text_input("Username / Email / Phone")
                login_pass = st.text_input("Password", type="password")
                submit_login = st.form_submit_button("Sign In")

            if submit_login:
                if not login_id.strip() or not login_pass.strip():
                    st.error("Please enter both your ID and password.")
                else:
                    user_rec = find_user_row(login_id)
                    if user_rec is None:
                        st.error("No account found with that Username / Email / Phone.")
                    elif user_rec.get("PasswordHash", "") != hash_password(login_pass):
                        st.error("Incorrect password.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_info = {
                            "name": user_rec.get("Name", ""),
                            "email": user_rec.get("Email", ""),
                            "username": user_rec.get("Username", ""),
                        }
                        st.success("Access Granted!")
                        st.rerun()

        elif auth_mode == "Registration":
            st.markdown("### 📝 Team Registration")
            if not st.session_state.otp_sent:
                with st.form("registration_form"):
                    reg_name = st.text_input("Official Name")
                    reg_user = st.text_input("Username")
                    reg_id = st.text_input("Office ID")
                    reg_email = st.text_input("Official Email")
                    reg_phone = st.text_input("Phone Number")
                    reg_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
                    reg_p1 = st.text_input("Password", type="password")
                    reg_p2 = st.text_input("Confirm Password", type="password")
                    submit_reg = st.form_submit_button("Send Verification OTP")

                if submit_reg:
                    # .strip() fixes the false "passwords do not match" caused by
                    # stray leading/trailing whitespace from autofill/copy-paste
                    p1, p2 = reg_p1.strip(), reg_p2.strip()
                    if not reg_email.strip() or not reg_user.strip():
                        st.error("Email and Username are mandatory!")
                    elif not p1 or not p2:
                        st.error("Please enter and confirm a password.")
                    elif p1 != p2:
                        st.error("Passwords do not match!")
                    else:
                        existing = find_user_row(reg_user) or find_user_row(reg_email)
                        if existing:
                            st.error("An account with this Username or Email already exists.")
                        else:
                            st.session_state.generated_otp = str(random.randint(100000, 999999))
                            st.session_state.reg_data = {
                                "Name": reg_name.strip(), "Username": reg_user.strip(),
                                "Office ID": reg_id.strip(), "Email": reg_email.strip(),
                                "Phone": reg_phone.strip(), "Blood Group": reg_blood,
                                "PasswordHash": hash_password(p1),
                            }
                            if send_otp_email(reg_email.strip(), st.session_state.generated_otp):
                                st.session_state.otp_sent = True
                                st.success(f"OTP Sent successfully to {reg_email}!")
                                st.rerun()
            else:
                st.info("Enter the 6-digit OTP sent to your email.")
                input_otp = st.text_input("OTP Code", max_chars=6)
                if st.button("Verify & Complete Registration"):
                    if input_otp.strip() == st.session_state.generated_otp:
                        try:
                            append_row_matching_headers(
                                USER_SHEET_ID, USER_SHEET_NAME, USER_COLUMNS, st.session_state.reg_data
                            )
                            read_sheet_as_df.clear()
                            st.success("Registration saved to Google Sheet! Switch to Login Mode.")
                            st.session_state.otp_sent = False
                            st.session_state.reg_data = {}
                        except Exception as e:
                            st.error(f"Could not save registration to Google Sheets: {e}")
                    else:
                        st.error("Invalid OTP Code!")

        elif auth_mode == "Forgot Password":
            st.markdown("### 🔑 Reset Password")
            f_email = st.text_input("Enter Registered Email")
            if not st.session_state.fp_otp_sent:
                if st.button("Get Reset OTP"):
                    if not find_user_row(f_email):
                        st.error("No account found with that email.")
                    else:
                        st.session_state.fp_generated_otp = str(random.randint(100000, 999999))
                        st.session_state.fp_email = f_email.strip()
                        if send_otp_email(f_email.strip(), st.session_state.fp_generated_otp):
                            st.session_state.fp_otp_sent = True
                            st.success("Verification OTP Dispatched!")
                            st.rerun()
            else:
                f_otp = st.text_input("Enter OTP Code")
                new_p = st.text_input("New Password", type="password")
                if st.button("Update Password"):
                    if f_otp.strip() != st.session_state.fp_generated_otp:
                        st.error("Wrong OTP Code!")
                    elif not new_p.strip():
                        st.error("Please enter a new password.")
                    else:
                        try:
                            ws = get_worksheet(USER_SHEET_ID, USER_SHEET_NAME)
                            headers = ensure_headers(ws, USER_COLUMNS)
                            cell = ws.find(st.session_state.fp_email)
                            if cell:
                                pass_col = headers.index("PasswordHash") + 1
                                ws.update_cell(cell.row, pass_col, hash_password(new_p))
                                read_sheet_as_df.clear()
                                st.success("Password updated successfully!")
                                st.session_state.fp_otp_sent = False
                            else:
                                st.error("Could not locate that account row in the sheet.")
                        except Exception as e:
                            st.error(f"Could not update password: {e}")
    st.stop()

# ====================================================================
# --- SYSTEM OPERATIONS (EXECUTED WHEN LOGGED IN) ---
# ====================================================================

today_date = datetime.now().strftime("%Y-%m-%d")

try:
    df = read_sheet_as_df(CONTENT_SHEET_ID, CONTENT_SHEET_NAME, "content")
    if df.empty:
        df = pd.DataFrame(columns=CONTENT_COLUMNS)
    load_error = None
except Exception as e:
    df = pd.DataFrame(columns=CONTENT_COLUMNS)
    load_error = str(e)

# --- SIDEBAR ---
with st.sidebar:
    st.image(LOGO_URL, width=110)
    st.markdown(f"🟢 **Session Authorized:** {st.session_state.user_info.get('email')}")
    if st.button("🚪 Log Out"):
        st.session_state.logged_in = False
        st.rerun()
    if st.button("🔄 Refresh Data"):
        read_sheet_as_df.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### 📈 Sponsor Execution Blueprint")
    with st.expander("🔍 View Sponsor Target Details", expanded=False):
        st.markdown("""
        <div class='popup-box'>
            <b>Sponsor A (Daraz)</b><br>
            • Creative: 2 Popups, 1 TVC (30s)<br>
            • Monthly Goal: 60 Uploads<br>
            • Video Type: Entertainment / Reels
        </div>
        <div class='popup-box'>
            <b>Sponsor B (bKash)</b><br>
            • Creative: 1 Doggy Alert, 2 TVCs<br>
            • Monthly Goal: 45 Uploads<br>
            • Video Type: Tech News / Features
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📅 Live Duty Roster")
    with st.expander("⏰ View Shift Timings", expanded=False):
        st.markdown("""
        <div class='popup-box'>
            <b>Morning Shift (08 AM - 04 PM)</b><br>
            • Siam (In-Charge Ops)<br>
            • Rahman (Uploader Desk)
        </div>
        <div class='popup-box'>
            <b>Evening Shift (04 PM - 12 AM)</b><br>
            • Karim (Digital Lead)<br>
            • Akram (Motion Editor)
        </div>
        """, unsafe_allow_html=True)

if load_error:
    st.warning(f"⚠️ Could not load the Content sheet (showing empty table). Details: {load_error}")

# --- DASHBOARD ---
st.markdown("### 📊 Live Operations Dashboard (Organic & Commercial Total)")
dash_col1, dash_col2 = st.columns(2)

with dash_col1:
    today_total = len(df[df['Date'].astype(str) == today_date]) if not df.empty and 'Date' in df.columns else 0
    st.markdown(f"<div class='metric-card'><h4>TODAY'S TOTAL NETWORK UPLOADS</h4><h1>{today_total} Videos</h1></div>", unsafe_allow_html=True)

with dash_col2:
    month_total = len(df) if not df.empty else 0
    st.markdown(f"<div class='metric-card'><h4>TOTAL UPLOADS THIS MONTH</h4><h1>{month_total} Videos</h1></div>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📥 Content Ingestion", "📋 Logs & Archives", "🏆 Team Live Score", "📈 Sponsor Deep Analytics"])

# --- TAB 1: INGESTION ---
with tab1:
    st.markdown("### 📝 Smart Content Ingestion Form")
    with st.form("strict_entry_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            in_date = st.date_input("Upload Date", datetime.now())
            in_slug = st.text_input("Slug Name *", placeholder="e.g., world-cup-news-02")
            in_head = st.text_input("Headline / Caption *")
            in_sponsor = st.selectbox("Select Sponsor (Choose 'None' for Organic)", ["None", "Sponsor A", "Sponsor B", "Sponsor C"])

        with col_f2:
            in_fb = st.text_input("Facebook Link")
            in_yt = st.text_input("YouTube Link")
            in_ig = st.text_input("Instagram Link")
            in_th = st.text_input("Threads Link")
            in_dm = st.text_input("Daily Motion Link")
            in_tt = st.text_input("TikTok Link")
            in_li = st.text_input("LinkedIn Link")
            in_bs = st.text_input("Bluesky Link")
            in_rd = st.text_input("Reddit Link")

        in_notes = st.text_area("Production Notes")
        submit_content = st.form_submit_button("🚀 Broadcast & Log Content")

        if submit_content:
            all_links = [in_fb, in_yt, in_ig, in_th, in_dm, in_tt, in_li, in_bs, in_rd]
            has_at_least_one_link = any(link.strip() != "" for link in all_links)

            if not in_slug.strip() or not in_head.strip():
                st.error("❌ Insertion Failed: 'Slug Name' and 'Headline / Caption' are strictly required!")
            elif not has_at_least_one_link:
                st.error("❌ Insertion Failed: You MUST provide at least ONE platform link to complete the entry!")
            else:
                row_data = {
                    "Date": in_date.strftime("%Y-%m-%d"),
                    "Slug Name": in_slug.strip(),
                    "Headline/Caption": in_head.strip(),
                    "Sponsor": in_sponsor,
                    "Uploader Email": st.session_state.user_info.get("email", ""),
                    "FB": in_fb.strip(), "YT": in_yt.strip(), "IG": in_ig.strip(),
                    "Threads": in_th.strip(), "Dailymotion": in_dm.strip(), "TikTok": in_tt.strip(),
                    "LinkedIn": in_li.strip(), "Bluesky": in_bs.strip(), "Reddit": in_rd.strip(),
                    "Notes": in_notes.strip(),
                }
                try:
                    append_row_matching_headers(CONTENT_SHEET_ID, CONTENT_SHEET_NAME, CONTENT_COLUMNS, row_data)
                    read_sheet_as_df.clear()
                    st.success(f"✅ Content Engine Verified! Entry '{in_slug}' logged successfully to Google Sheets.")
                except Exception as e:
                    st.error(f"❌ Could not save to Google Sheets: {e}")

# --- TAB 2: AUDIT LOGS ---
with tab2:
    st.markdown(f"### 📄 Comprehensive Log Audit - {CONTENT_SHEET_NAME}")
    st.dataframe(df, use_container_width=True)

# --- TAB 3: LIVE SCOREBOARD ---
with tab3:
    st.markdown("### 🏆 Top 10 Live Score Leaderboard")
    if not df.empty and 'Uploader Email' in df.columns:
        leaderboard = df['Uploader Email'].value_counts().reset_index()
        leaderboard.columns = ['Team Member', 'Total Videos Uploaded']
        st.table(leaderboard.head(10))
    else:
        st.info("Leaderboard will automatically populate as active user sessions log entries.")

# --- TAB 4: SPONSOR ACCOUNTING ---
with tab4:
    st.markdown("### 📈 Dedicated Sponsor Operations View")
    st.info("Sponsor execution metrics and accounting sub-systems are currently logging in synchronization with cloud clusters.")
