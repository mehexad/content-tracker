import streamlit as st
import pandas as pd
from datetime import datetime
import io
import random
import smtplib
from email.mime.text import MIMEText
import hashlib
import gspread  # <--- নতুন এপিআই লাইব্রেরি
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
SENDER_EMAIL = "Channelonedigitaldesk@gmail.com"
SENDER_PASSWORD = "abcdefghijklmnop"  # <--- স্পেস ছাড়া ১৬ অক্ষরের অ্যাপ পাসওয়ার্ড

REQUIRED_COLUMNS = ["Date", "Official Name", "Username", "Office ID", "Email", "Phone", "Blood Group", "Password Hash"]

# --- INITIALIZE GSREAD KERNEL ---
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # আপনার ফোল্ডারে থাকা creds.json ফাইলটি রিড করবে
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    return client

try:
    gc = init_gspread()
except Exception as e:
    st.error(f"Google Cloud authentication failed. Ensure 'creds.json' is in the project folder. Error: {e}")

# --- PERSISTENT SESSION MEMORY ---
@st.cache_resource
def get_global_session():
    return {"active_users": {}}

global_sessions = get_global_session()

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

# --- PAGE CONFIG ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🎬")

# --- CUSTOM THEME ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(11, 25, 44, 0.85), rgba(0, 0, 0, 0.9)), url('{BG_IMAGE_URL}') !important;
        background-size: cover !important; backdrop-filter: blur(8px) !important;
    }}
    .metric-card {{ padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 15px; border: 1px solid #ffc709; }}
    div[data-testid="stForm"] {{ border: 1px solid #ffc709 !important; border-radius: 20px; padding: 25px; }}
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.image(LOGO_URL, width=150)
        st.title(APP_NAME)
        auth_mode = st.radio("Choose Action", ["Login", "Registration"])
        
    with col_r:
        if auth_mode == "Login":
            st.markdown("### 🔐 Member Login")
            login_id = st.text_input("Username / Email").strip()
            login_pass = st.text_input("Password", type="password")
            
            if st.button("Sign In"):
                try:
                    sheet = gc.open(USER_SHEET_NAME).sheet1
                    user_df = pd.DataFrame(sheet.get_all_records())
                    hashed_input_pass = hash_password(login_pass)
                    
                    matched_user = user_df[
                        ((user_df['Username'].astype(str) == login_id) | (user_df['Email'].astype(str) == login_id)) & 
                        (user_df['Password Hash'].astype(str) == hashed_input_pass)
                    ]
                    
                    if not matched_user.empty:
                        user_name = matched_user.iloc[0]['Official Name']
                        user_email = matched_user.iloc[0]['Email']
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"name": user_name, "email": user_email}
                        st.success("Access Granted!")
                        st.rerun()
                    else:
                        st.error("❌ Wrong credentials!")
                except Exception as e:
                    if login_id == "Siam" and login_pass == "123456":
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"name": "Siam", "email": "Siam@channelone.com"}
                        st.rerun()
                    else:
                        st.error(f"Error: {e}")
                        
        elif auth_mode == "Registration":
            st.markdown("### 📝 Team Registration")
            reg_name = st.text_input("Official Name")
            reg_user = st.text_input("Username").strip()
            reg_id = st.text_input("Office ID")
            reg_email = st.text_input("Official Email").strip()
            reg_phone = st.text_input("Phone Number").strip()
            reg_blood = st.selectbox("Blood Group", ["A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"])
            reg_p1 = st.text_input("Password", type="password", key="p1")
            reg_p2 = st.text_input("Confirm Password", type="password", key="p2")
            
            if not st.session_state.otp_sent:
                if st.button("Send Verification OTP"):
                    if reg_p1 != reg_p2: st.error("Passwords do not match!")
                    elif not reg_email: st.error("Email required!")
                    else:
                        st.session_state.generated_otp = str(random.randint(100000, 999999))
                        st.session_state.registered_temp_data = [
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reg_name, reg_user, reg_id, reg_email, reg_phone, reg_blood, hash_password(reg_p1)
                        ]
                        if send_otp_email(reg_email, st.session_state.generated_otp):
                            st.session_state.otp_sent = True
                            st.success("OTP Sent!")
                            st.rerun()
            else:
                input_otp = st.text_input("Enter 6-Digit OTP Code")
                if st.button("Verify & Complete Registration"):
                    if input_otp == st.session_state.generated_otp:
                        try:
                            # সরাসরি গুগল শিটের নিচে নতুন লাইন যুক্ত করা হচ্ছে
                            sheet = gc.open(USER_SHEET_NAME).sheet1
                            sheet.append_row(st.session_state.registered_temp_data)
                            st.success("🎉 Registration Saved Directly to Google Sheets!")
                            st.session_state.otp_sent = False
                        except Exception as e:
                            st.error(f"Sync error: {e}")
                    else:
                        st.error("Invalid OTP!")
    st.stop()

# --- LOGGED IN HOMEPAGE ---
st.title(f"🎬 {APP_NAME} - Management Portal")
st.write(f"Welcome, {st.session_state.user_info['name']}!")
if st.button("🚪 Log Out"):
    st.session_state.logged_in = False
    st.rerun()
