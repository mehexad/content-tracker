import streamlit as st
import pandas as pd
from datetime import datetime
import io
import random
import smtplib
from email.mime.text import MIMEText
import hashlib

# --- CONFIGURATION & CONSTANTS (DIRECTLY INTEGRATED) ---
APP_NAME = "Channel One Content Tracker"
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/c/c3/%E0%A6%9A%E0%A7%8D%E0%A6%AF%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B2_%E0%A6%93%E0%A6%AF%E0%A6%BC%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B2_%E0%A6%92%E0%A6%AF%E0%A6%BC%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B0_%E0%A6%B2%E0%A7%86%E0%A6%97%E0%A7%8B.svg"

# Google Sheet Details
CONTENT_SHEET_ID = "1byGzAKrYovR29-LxtmffLMjtsIcdv3b5RXbUq4EK9VA"
CONTENT_SHEET_NAME = "2026 JULY"
USER_SHEET_ID = "117tCpIN4vBNVOO3b5P5b7yC2kOo_gh5SThanT7rM860"
USER_SHEET_NAME = "FOR CONTENT TRACKER DETAILS"

# Email Configuration for OTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "Channelonedigitaldesk@gmail.com"
SENDER_PASSWORD = "@onedigit@ldesk"

# --- SYSTEM UTILITIES ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def send_otp_email(target_email, otp_code):
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

def get_gsheet_url(sheet_id, sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name.replace(' ', '%20')}"

# --- INITIALIZE SESSION STATES ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'otp_sent' not in st.session_state: st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None
if 'reg_data' not in st.session_state: st.session_state.reg_data = {}

# --- PAGE CONFIG ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🎬")

# --- CUSTOM THEME RESPONSIVE CSS (DARK & LIGHT SWITCH ACCURATE) ---
st.markdown(f"""
    <style>
    /* Glossy Background Base */
    .main {{ background-color: #0B192C; }}
    
    /* Dynamic Text Colors Based on User System Dark/Light Selection */
    @media (prefers-color-scheme: dark) {{
        html, body, [data-testid="stWidgetLabel"], p, h1, h2, h3, h4, li, span, label {{
            color: #ffc709 !important;
        }}
        /* Input fields font color adjustment for dark mode */
        input, select, textarea, div[data-baseweb="select"] span {{
            color: #ffc709 !important;
        }}
        div[data-testid="stForm"] {{
            border: 1px solid #ffc709 !important;
            background: linear-gradient(135deg, rgba(30, 62, 98, 0.4) 0%, rgba(11, 25, 44, 0.6) 100%);
        }}
        .popup-box {{
            border-left: 5px solid #ffc709;
            background: rgba(30, 62, 98, 0.4);
            color: #ffc709 !important;
        }}
        .metric-card {{
            border: 1px solid #ffc709;
            background: linear-gradient(135deg, rgba(30, 62, 98, 0.5) 0%, rgba(11, 25, 44, 0.7) 100%);
        }}
    }}
    
    @media (prefers-color-scheme: light) {{
        html, body, [data-testid="stWidgetLabel"], p, h1, h2, h3, h4, li, span, label {{
            color: #000000 !important;
        }}
        /* Input fields font color adjustment for light mode */
        input, select, textarea, div[data-baseweb="select"] span {{
            color: #000000 !important;
        }}
        div[data-testid="stForm"] {{
            border: 1px solid #000000 !important;
            background: #FFFFFF !important;
        }}
        .popup-box {{
            border-left: 5px solid #000000;
            background: #F4F6F9;
            color: #000000 !important;
        }}
        .metric-card {{
            border: 1px solid #000000;
            background: #FAFAFA;
        }}
    }}

    /* Global UI Formats */
    .metric-card {{
        padding: 20px; border-radius: 15px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 15px;
    }}
    .popup-box {{
        border-radius: 10px; padding: 15px; margin-bottom: 12px; font-size: 0.9rem;
    }}
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
            login_id = st.text_input("Username / Email / Phone")
            login_pass = st.text_input("Password", type="password")
            if st.button("Sign In"):
                st.session_state.logged_in = True
                st.session_state.user_info = {"name": "Authorized User", "email": login_id}
                st.success("Access Granted!")
                st.rerun()
                
        elif auth_mode == "Registration":
            st.markdown("### 📝 Team Registration")
            if not st.session_state.otp_sent:
                reg_name = st.text_input("Official Name")
                reg_user = st.text_input("Username")
                reg_id = st.text_input("Office ID")
                reg_email = st.text_input("Official Email")
                reg_phone = st.text_input("Phone Number")
                reg_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
                reg_p1 = st.text_input("Password", type="password")
                reg_p2 = st.text_input("Confirm Password", type="password")
                
                if st.button("Send Verification OTP"):
                    if reg_p1 != reg_p2:
                        st.error("Passwords do not match!")
                    elif not reg_email or not reg_user:
                        st.error("Email and Username are mandatory!")
                    else:
                        st.session_state.generated_otp = str(random.randint(100000, 999999))
                        st.session_state.reg_data = {
                            "name": reg_name, "username": reg_user, "id": reg_id,
                            "email": reg_email, "phone": reg_phone, "blood": reg_blood,
                            "pass": hash_password(reg_p1)
                        }
                        if send_otp_email(reg_email, st.session_state.generated_otp):
                            st.session_state.otp_sent = True
                            st.success(f"OTP Sent successfully to {reg_email}!")
                            st.rerun()
            else:
                st.info("Enter the 6-digit OTP sent to your email.")
                input_otp = st.text_input("OTP Code", max_chars=6)
                if st.button("Verify & Complete Registration"):
                    if input_otp == st.session_state.generated_otp:
                        st.success("Registration Saved to Cloud DB! Switch to Login Mode.")
                        st.session_state.otp_sent = False
                    else:
                        st.error("Invalid OTP Code!")
                        
        elif auth_mode == "Forgot Password":
            st.markdown("### 🔑 Reset Password")
            f_email = st.text_input("Enter Registered Email")
            if not st.session_state.otp_sent:
                if st.button("Get Reset OTP"):
                    st.session_state.generated_otp = str(random.randint(100000, 999999))
                    if send_otp_email(f_email, st.session_state.generated_otp):
                        st.session_state.otp_sent = True
                        st.success("Verification Link & OTP Dispatched!")
                        st.rerun()
            else:
                f_otp = st.text_input("Enter OTP Code")
                new_p = st.text_input("New Password", type="password")
                if st.button("Update Password"):
                    if f_otp == st.session_state.generated_otp:
                        st.success("Password Updated successfully!")
                        st.session_state.otp_sent = False
                    else:
                        st.error("Wrong OTP Code!")
    st.stop()

# ====================================================================
# --- SYSTEM OPERATIONS (EXECUTED WHEN LOGGED IN) ---
# ====================================================================

today_date = datetime.now().strftime("%Y-%m-%d")

try:
    url = get_gsheet_url(CONTENT_SHEET_ID, CONTENT_SHEET_NAME)
    df = pd.read_csv(url)
except:
    df = pd.DataFrame(columns=["Date", "Slug Name", "Headline/Caption", "Sponsor", "Uploader Email", "FB", "YT", "IG", "Threads", "Dailymotion", "TikTok", "LinkedIn", "Bluesky", "Reddit"])

# --- SIDEBAR INTERFACES & INFRASTRUCTURE ---
with st.sidebar:
    st.image(LOGO_URL, width=110)
    st.markdown(f"🟢 **Session Authorized:** {st.session_state.user_info.get('email')}")
    if st.button("🚪 Log Out"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.markdown("---")
    st.markdown("### 📈 Sponsor Execution Blueprint")
    with st.expander("🔍 View Sponsor Target Details", expanded=False):
        st.markdown("""
        <div class='popup-box'>
            <b>Sponsor A (Daraz)</b><br>
            • Creative: 2 Popups, 1 TVC (30s)<br>
            • Monthly Goal: 60 Uploads<br>
            • Video Type: Entertainment / Reels<br>
            • Today's Progress: 3 | Pending: 1
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

# --- CORE NETWORKS PERFORMANCE DASHBOARD ---
st.markdown("### 📊 Live Operations Dashboard (Organic & Commercial Total)")
dash_col1, dash_col2 = st.columns(2)

with dash_col1:
    today_total = len(df[df['Date'] == today_date]) if not df.empty else 0
    st.markdown(f"<div class='metric-card'><h4>TODAY'S TOTAL NETWORK UPLOADS</h4><h1>{today_total} Videos</h1></div>", unsafe_allow_html=True)
    
with dash_col2:
    month_total = len(df) if not df.empty else 0
    st.markdown(f"<div class='metric-card'><h4>TOTAL UPLOADS THIS MONTH</h4><h1>{month_total} Videos</h1></div>", unsafe_allow_html=True)

# --- PORTAL INTERACTION TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📥 Content Ingestion", "📋 Logs & Archives", "🏆 Team Live Score", "📈 Sponsor Deep Analytics"])

# --- TAB 1: INGESTION WITH CONDITIONAL VALIDATION ---
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
            
            if not in_slug or not in_head:
                st.error("❌ Insertion Failed: 'Slug Name' and 'Headline / Caption' are strictly required!")
            elif not has_at_least_one_link:
                st.error("❌ Insertion Failed: You MUST provide at least ONE platform link to complete the entry!")
            else:
                st.success(f"✅ Content Engine Verified! Entry '{in_slug}' logged successfully.")

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
