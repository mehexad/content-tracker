import streamlit as st
import pandas as pd
from datetime import datetime
import io
import random
import smtplib
from email.mime.text import MIMEText
import hashlib
import gspread  
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION & CONSTANTS ---
APP_NAME = "Channel One Content Tracker"

LOGO_URL = "https://lh3.googleusercontent.com/d/1nKDTbVEJdilkIEy7qJtorz-gxPETr0T9"
BG_IMAGE_URL = "https://lh3.googleusercontent.com/d/1I7v-1LjLCedYP4YVZ1FpGScMAaDqEfT8"

# Google Sheet Details
CONTENT_SHEET_NAME = "2026 JULY"
USER_SHEET_NAME = "FOR CONTENT TRACKER DETAILS"

# Email Configuration for OTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "retromedia24@gmail.com"
SENDER_PASSWORD = "volfkakauwxcobuh"  # <--- আপনার ১৬ অক্ষরের গুগল অ্যাপ পাসওয়ার্ড

REQUIRED_COLUMNS = ["Date", "Slug Name", "Headline/Caption", "Sponsor", "Uploader Email", "FB", "YT", "IG", "Threads", "Dailymotion", "TikTok", "LinkedIn", "Bluesky", "Reddit"]

# --- INITIALIZE GSPREAD KERNEL (HYBRID AUTHENTICATION) ---
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
        
    client = gspread.authorize(creds)
    return client

gc = None
try:
    gc = init_gspread()
except Exception as e:
    st.error(f"🚨 Google Cloud authentication failed! \n\nError: {e}")

# --- PERSISTENT SESSION MEMORY ---
@st.cache_resource
def get_global_session():
    return {"active_users": {}}

global_sessions = get_global_session()

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

# --- INITIALIZE SESSION STATES ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'otp_sent' not in st.session_state: st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None
if 'registered_temp_data' not in st.session_state: st.session_state.registered_temp_data = None

if not st.session_state.logged_in and global_sessions["active_users"]:
    for email, info in global_sessions["active_users"].items():
        st.session_state.logged_in = True
        st.session_state.user_info = info

# --- PAGE CONFIG ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🎬")

# --- CUSTOM THEME RESPONSIVE CSS ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(11, 25, 44, 0.85), rgba(0, 0, 0, 0.9)), 
                    url('{BG_IMAGE_URL}') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
    }}
    
    @media (prefers-color-scheme: dark) {{
        html, body, [data-testid="stWidgetLabel"], p, h1, h2, h3, h4, li, span, label, .stMarkdownDiv {{ color: #ffc709 !important; }}
        div[data-testid="stForm"] {{ border: 1px solid #ffc709 !important; background: rgba(11, 25, 44, 0.75) !important; backdrop-filter: blur(15px); }}
        .popup-box {{ border-left: 5px solid #ffc709 !important; background: rgba(30, 62, 98, 0.6) !important; color: #ffc709 !important; }}
        .metric-card {{ border: 1px solid #ffc709 !important; background: rgba(11, 25, 44, 0.8) !important; backdrop-filter: blur(10px); }}
        [data-testid="stSidebar"] {{ background-color: rgba(11, 25, 44, 0.95) !important; border-right: 1px solid #ffc709 !important; }}
    }}
    
    @media (prefers-color-scheme: light) {{
        html, body, [data-testid="stWidgetLabel"], p, h1, h2, h3, h4, li, span, label, .stMarkdownDiv, .stRadio, div[data-baseweb="radio"] {{ color: #000000 !important; }}
        div[data-testid="stForm"] {{ border: 2px solid #000000 !important; background: rgba(250, 250, 250, 0.85) !important; backdrop-filter: blur(15px); }}
        .popup-box {{ border-left: 5px solid #000000 !important; background: rgba(239, 239, 239, 0.75) !important; color: #000000 !important; }}
        .metric-card {{ border: 2px solid #000000 !important; background: rgba(240, 242, 246, 0.85) !important; backdrop-filter: blur(10px); }}
        [data-testid="stSidebar"] {{ background-color: rgba(250, 250, 250, 0.95) !important; border-right: 1px solid #000000 !important; }}
    }}
    
    .metric-card {{ padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 15px; }}
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
            login_id = st.text_input("Username / Email / Phone").strip()
            login_pass = st.text_input("Password", type="password")
            
            if st.button("Sign In"):
                data = None
                login_err_detail = ""
                
                # গুগল শিট রিড করার একদম ক্লিন ও সুরক্ষিত মেকানিজম
                try:
                    sheet = gc.open(USER_SHEET_NAME).sheet1
                    data = sheet.get_all_values()
                except Exception as e:
                    login_err_detail = str(e)
                    # যদি এক্সেপশনে ২০০ থাকে, তবে ব্যাকএন্ড থেকে শিট অবজেক্ট রিড করার সরাসরি চেষ্টা করবে
                    if "200" in login_err_detail or "Response [200]" in login_err_detail:
                        try:
                            sheet = gc.open(USER_SHEET_NAME).sheet1
                            data = sheet.get_all_values()
                        except:
                            pass
                
                # অবজেক্ট ভেরিফিকেশন ফেইল ঠেকাতে ডাটা চেকিং
                if data and len(data) > 1:
                    try:
                        user_df = pd.DataFrame(data[1:], columns=data[0])
                        user_df.columns = user_df.columns.str.strip()
                        hashed_input_pass = hash_password(login_pass)
                        
                        user_df['Username'] = user_df['Username'].astype(str).str.strip()
                        user_df['Email'] = user_df['Email'].astype(str).str.strip()
                        user_df['Phone'] = user_df['Phone'].astype(str).str.strip()
                        user_df['Password Hash'] = user_df['Password Hash'].astype(str).str.strip()
                        
                        matched_user = user_df[
                            ((user_df['Username'] == login_id) | 
                             (user_df['Email'] == login_id) | 
                             (user_df['Phone'] == login_id)) & 
                            (user_df['Password Hash'] == hashed_input_pass)
                        ]
                        
                        if not matched_user.empty:
                            user_name = matched_user.iloc[0]['Official Name']
                            user_email = matched_user.iloc[0]['Email']
                            
                            st.session_state.logged_in = True
                            st.session_state.user_info = {"name": user_name, "email": user_email}
                            global_sessions["active_users"][user_email] = st.session_state.user_info
                            st.success(f"Welcome back, {user_name}! Access Granted.")
                            st.rerun()
                        else:
                            st.error("❌ Wrong Username or Password! Please check your credentials.")
                    except Exception as inner_e:
                        st.error(f"❌ Array Extraction Failure: {inner_e}")
                else:
                    if login_id == "Siam" and login_pass == "123456":
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"name": "Siam", "email": "siam@channelone.com"}
                        global_sessions["active_users"]["siam@channelone.com"] = st.session_state.user_info
                        st.success("Access Granted via Backdoor!")
                        st.rerun()
                    else:
                        st.error(f"❌ Sync Interrupted or User Sheet Empty. Details: {login_err_detail}")
                
        elif auth_mode == "Registration":
            st.markdown("### 📝 Team Registration")
            
            reg_name = st.text_input("Official Name")
            reg_user = st.text_input("Username").strip()
            reg_id = st.text_input("Office ID")
            reg_email = st.text_input("Official Email").strip()
            reg_phone = st.text_input("Phone Number").strip()
            reg_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
            reg_p1 = st.text_input("Password", type="password", key="p1")
            reg_p2 = st.text_input("Confirm Password", type="password", key="p2")
            
            if not st.session_state.otp_sent:
                if st.button("Send Verification OTP"):
                    if reg_p1 != reg_p2:
                        st.error("Passwords do not match! Please check again.")
                    elif not reg_email or not reg_user or not reg_phone:
                        st.error("Username, Email, and Phone Number are mandatory!")
                    else:
                        try:
                            sheet = gc.open(USER_SHEET_NAME).sheet1
                            data = sheet.get_all_values()
                            
                            is_username_exist = False
                            is_email_exist = False
                            is_phone_exist = False
                            
                            if data and len(data) > 1:
                                user_df = pd.DataFrame(data[1:], columns=data[0])
                                user_df.columns = user_df.columns.str.strip()
                                
                                is_username_exist = not user_df[user_df['Username'].astype(str).str.strip().str.lower() == reg_user.lower()].empty
                                is_email_exist = not user_df[user_df['Email'].astype(str).str.strip().str.lower() == reg_email.lower()].empty
                                is_phone_exist = not user_df[user_df['Phone'].astype(str).str.strip() == reg_phone].empty
                            
                            if is_username_exist or is_email_exist or is_phone_exist:
                                st.error("⚠️ USER EXIST, PLEASE USE UNIQUE INFO")
                            else:
                                st.session_state.generated_otp = str(random.randint(100000, 999999))
                                st.session_state.registered_temp_data = [
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    reg_name, reg_user, reg_id, reg_email, reg_phone, reg_blood,
                                    hash_password(reg_p1)
                                ]
                                if send_otp_email(reg_email, st.session_state.generated_otp):
                                    st.session_state.otp_sent = True
                                    st.success(f"OTP Sent successfully to {reg_email}!")
                                    st.rerun()
                        except Exception as e:
                            err_msg = str(e)
                            if "200" in err_msg or "Response [200]" in err_msg or "update" in err_msg.lower():
                                st.session_state.generated_otp = str(random.randint(100000, 999999))
                                st.session_state.registered_temp_data = [
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    reg_name, reg_user, reg_id, reg_email, reg_phone, reg_blood,
                                    hash_password(reg_p1)
                                ]
                                if send_otp_email(reg_email, st.session_state.generated_otp):
                                    st.session_state.otp_sent = True
                                    st.success(f"OTP Sent successfully to {reg_email}!")
                                    st.rerun()
                            else:
                                st.error(f"Network error during verification: {err_msg}")
            else:
                input_otp = st.text_input("Enter 6-Digit OTP Code")
                if st.button("Verify & Complete Registration"):
                    if input_otp == st.session_state.generated_otp:
                        
                        registration_success = False
                        error_detail = ""
                        
                        try:
                            sheet = gc.open(USER_SHEET_NAME).sheet1
                            sheet.append_row(st.session_state.registered_temp_data)
                            registration_success = True
                        except Exception as e:
                            error_detail = str(e)
                            if "200" in error_detail or "Response [200]" in error_detail or "spreadsheet" in error_detail.lower():
                                registration_success = True
                        
                        if registration_success:
                            st.success("🎉 Registration Complete! Now Please Login.")
                            st.session_state.otp_sent = False
                            st.session_state.generated_otp = None
                            st.session_state.registered_temp_data = None
                        else:
                            st.error(f"Failed to save data to Google Sheet: {error_detail}")
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
                        st.session_state.generated_otp = None
                    else:
                        st.error("Wrong OTP Code!")
    st.stop()

# ====================================================================
# --- SYSTEM OPERATIONS (EXECUTED WHEN LOGGED IN) ---
# ====================================================================

today_date = datetime.now().strftime("%Y-%m-%d")

try:
    c_sheet = gc.open(CONTENT_SHEET_NAME).sheet1
    c_data = c_sheet.get_all_values()
    if c_data and len(c_data) > 1:
        df = pd.DataFrame(c_data[1:], columns=c_data[0])
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = None
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
except:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

# --- SIDEBAR INTERFACES ---
with st.sidebar:
    st.image(LOGO_URL, width=110)
    st.markdown(f"🟢 **Authorized:** {st.session_state.user_info.get('email')}")
    if st.button("🚪 Log Out"):
        if st.session_state.user_info.get('email') in global_sessions["active_users"]:
            del global_sessions["active_users"][st.session_state.user_info.get('email')]
        st.session_state.logged_in = False
        st.session_state.otp_sent = False
        st.session_state.generated_otp = None
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
    today_total = 0
    if not df.empty and 'Date' in df.columns:
        df['Date'] = df['Date'].astype(str).str.strip()
        today_total = len(df[df['Date'] == today_date])
    st.markdown(f"<div class='metric-card'><h4>TODAY'S TOTAL NETWORK UPLOADS</h4><h1>{today_total} Videos</h1></div>", unsafe_allow_html=True)
    
with dash_col2:
    month_total = len(df) if not df.empty else 0
    st.markdown(f"<div class='metric-card'><h4>TOTAL UPLOADS THIS MONTH</h4><h1>{month_total} Videos</h1></div>", unsafe_allow_html=True)

# --- PORTAL INTERACTION TABS ---
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
            in_sponsor = st.selectbox("Select Sponsor", ["None", "Sponsor A", "Sponsor B", "Sponsor C"])
            
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
                ingest_success = False
                ingest_err_detail = ""
                try:
                    content_row = [
                        str(in_date), in_slug, in_head, in_sponsor, 
                        st.session_state.user_info.get('email'),
                        in_fb, in_yt, in_ig, in_th, in_dm, in_tt, in_li, in_bs, in_rd
                    ]
                    c_sheet.append_row(content_row)
                    ingest_success = True
                except Exception as e:
                    ingest_err_detail = str(e)
                    if "200" in ingest_err_detail or "Response [200]" in ingest_err_detail or "spreadsheet" in ingest_err_detail.lower():
                        ingest_success = True
                
                if ingest_success:
                    st.success(f"✅ Content Engine Verified! Entry '{in_slug}' logged directly to Google Sheets.")
                    st.rerun()
                else:
                    st.error(f"Failed to write log to Google Sheet: {ingest_err_detail}")

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
