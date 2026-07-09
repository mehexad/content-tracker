import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import gspread  
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
APP_NAME = "Channel One Content Tracker"
CONTENT_SHEET_NAME = "2026 JULY"
USER_SHEET_NAME = "FOR CONTENT TRACKER DETAILS"

# --- GSPREAD INIT ---
@st.cache_resource
def init_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # নিশ্চিত করুন আপনার ফোল্ডারে creds.json ফাইলটি আছে
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    return gspread.authorize(creds)

gc = init_gspread()

# --- UTILS ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}

# --- APP LAYOUT ---
st.set_page_config(page_title=APP_NAME, layout="wide")

if not st.session_state.logged_in:
    st.title(f"🎬 {APP_NAME}")
    auth_mode = st.radio("Choose Action", ["Login", "Registration"])
    
    if auth_mode == "Login":
        st.subheader("🔐 Member Login")
        login_id = st.text_input("Username or Email").strip()
        login_pass = st.text_input("Password", type="password")
        
        if st.button("Sign In"):
            try:
                sheet = gc.open(USER_SHEET_NAME).sheet1
                data = sheet.get_all_values()
                
                if not data or len(data) < 2:
                    st.error("শিটটি খালি অথবা হেডার রো নেই। অনুগ্রহ করে গুগল শিট চেক করুন।")
                else:
                    # নতুন ভার্সন: কলামের নাম যাই হোক, ইনডেক্স দিয়ে ধরবে
                    df = pd.DataFrame(data[1:], columns=data[0])
                    # কলামগুলোর নাম পরিষ্কার করা
                    df.columns = df.columns.str.strip()
                    
                    hashed_input = hash_password(login_pass)
                    
                    # ফিল্টারিং
                    user = df[((df['Username'].astype(str).str.strip() == login_id) | 
                              (df['Email'].astype(str).str.strip() == login_id)) & 
                              (df['Password Hash'].astype(str).str.strip() == hashed_input)]
                    
                    if not user.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_info = {"name": user.iloc[0]['Official Name'], "email": user.iloc[0]['Email']}
                        st.rerun()
                    else:
                        st.error("ইউজারনেম অথবা পাসওয়ার্ড ভুল!")
            except Exception as e:
                st.error(f"ডাটাবেজ রিডিং এরর: {e}")

    elif auth_mode == "Registration":
        st.subheader("📝 Team Registration")
        reg_name = st.text_input("Official Name")
        reg_user = st.text_input("Username")
        reg_id = st.text_input("Office ID")
        reg_email = st.text_input("Email")
        reg_phone = st.text_input("Phone")
        reg_blood = st.selectbox("Blood Group", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        reg_pass = st.text_input("Password", type="password")
        
        if st.button("Complete Registration"):
            try:
                sheet = gc.open(USER_SHEET_NAME).sheet1
                # শিটের কলাম অনুযায়ী সিরিয়ালে ডেটা ইনপুট
                sheet.append_row([datetime.now().strftime("%Y-%m-%d"), reg_name, reg_user, reg_id, reg_email, reg_phone, reg_blood, hash_password(reg_pass)])
                st.success("Registration Complete! Now Please Login.")
            except Exception as e:
                st.error(f"রেজিস্ট্রেশন এরর: {e}")
    st.stop()

# --- LOGGED IN DASHBOARD ---
st.sidebar.button("🚪 Log Out", on_click=lambda: st.session_state.update(logged_in=False))
st.write(f"Welcome, **{st.session_state.user_info.get('name')}**")
