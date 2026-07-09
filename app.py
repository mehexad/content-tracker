import streamlit as st
import pandas as pd
from datetime import datetime
import io
import random
import smtplib
from email.mime.text import MIMEText
import hashlib

# --- CONFIGURATION & CONSTANTS ---
APP_NAME = "Channel One Content Tracker"

# Convert Google Drive Links to Direct Images
LOGO_URL = "https://lh3.googleusercontent.com/d/1nKDTbVEJdilkIEy7qJtorz-gxPETr0T9"
BG_IMAGE_URL = "https://lh3.googleusercontent.com/d/1I7v-1LjLCedYP4YVZ1FpGScMAaDqEfT8"

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

# --- DEFAULT COLUMNS ARCHITECTURE ---
REQUIRED_COLUMNS = ["Date", "Slug Name", "Headline/Caption", "Sponsor", "Uploader Email", "FB", "YT", "IG", "Threads", "Dailymotion", "TikTok", "LinkedIn", "Bluesky", "Reddit"]

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

def get_gsheet_url(sheet_id, sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name.replace(' ', '%20')}"

# --- INITIALIZE SESSION STATES ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}
if 'otp_sent' not in st.session_state: st.session_state.otp_sent = False
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None

# Persistent Cookie Simulation
if not st.session_state.logged_in and global_sessions["active_users"]:
    for email, info in global_sessions["active_users"].items():
        st.session_state.logged_in = True
        st.session_state.user_info = info

# --- PAGE CONFIG ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🎬")

# --- CUSTOM THEME RESPONSIVE CSS (DARKER & BLURRED BACKGROUND) ---
st.markdown(f"""
    <style>
    /* Global Background Image with Dark Overlay & Blur Effect */
    .stApp {{
        background: linear-gradient(rgba(11, 25, 44, 0.85), rgba(0, 0, 0, 0.9)), 
                    url('{BG_IMAGE_URL}') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat
