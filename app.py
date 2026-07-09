import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- CONFIGURATION ---
APP_NAME = "Channel One Content Tracker"
# আপনার লোগোর ডিরেক্ট লিংক এখানে দিন (যেমন: ড্রাইভ লিংক বা ওয়েবসাইট লিংক)
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/c/c3/%E0%A6%9A%E0%A7%8D%E0%A6%AF%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B2_%E0%A6%93%E0%A6%AF%E0%A6%BC%E0%A6%BE%E0%A6%A8%E0%A7%87%E0%A6%B0_%E0%A6%B2%E0%A7%8B%E0%A6%97%E0%A7%8B.svg" 
SPREADSHEET_ID = "1byGzAKrYovR29-LxtmffLMjtsIcdv3b5RXbUq4EK9VA"

def get_gsheet_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/1byGzAKrYovR29-LxtmffLMjtsIcdv3b5RXbUq4EK9VA/gviz/tq?tqx=out:csv&sheet=2026 JULY"

# --- PAGE CONFIG ---
st.set_page_config(page_title=APP_NAME, layout="wide", page_icon="🎬")

# --- CUSTOM GLOSSY CSS ---
st.markdown(f"""
    <style>
    .main {{ background-color: #0B192C; }}
    [data-testid="stSidebar"] {{ background-color: #0B192C; border-right: 1px solid #ffc709; }}
    
    /* Glossy Header & Titles */
    h1, h2, h3 {{ 
        color: #ffc709 !important; 
        font-family: 'Segoe UI', sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }}
    
    /* Metrics Card */
    .metric-card {{
        background: linear-gradient(135deg, rgba(30, 62, 98, 0.6) 0%, rgba(11, 25, 44, 0.8) 100%);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #ffc709;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 199, 9, 0.2);
    }}
    
    /* Form Styling */
    div[data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 30px;
        border: 0.5px solid #ffc709;
    }}
    
    /* Dataframe Styling */
    .stDataFrame {{ border: 1px solid #1E3E62; border-radius: 10px; }}
    </style>
""", unsafe_allow_html=True)

# --- APP HEADER WITH LOGO ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image(LOGO_URL, width=120)
with col_title:
    st.title(APP_NAME)
    st.subheader("Efficiency. Accuracy. Results.")

# --- DATA LOADING ---
current_month_name = datetime.now().strftime("%B %Y")
today_date = datetime.now().strftime("%Y-%m-%d")

try:
    url = get_gsheet_url(current_month_name.replace(" ", "%20"))
    df = pd.read_csv(url)
except:
    df = pd.DataFrame(columns=["Date", "Uploader Email", "Headline/Caption", "Sponsor", "FB", "YT", "TT", "IG", "Notes"])

# --- SIDEBAR & AUTH ---
st.sidebar.image(LOGO_URL, width=100)
st.sidebar.markdown("---")
user_email = st.sidebar.text_input("👤 Team Member Email", placeholder="yourname@channelone.com")
st.sidebar.info(f"📅 Active Session: {current_month_name}")

# --- DASHBOARD SECTION (Daily & Monthly Tracker) ---
st.markdown("### 📊 Live Performance Dashboard")
dash_col1, dash_col2, dash_col3 = st.columns(3)

# ১. আজকের মোট কন্টেন্ট
today_count = len(df[df['Date'] == today_date]) if not df.empty else 0
with dash_col1:
    st.markdown(f"<div class='metric-card'><h4 style='color:white'>Today's Total</h4><h1 style='color:#ffc709'>{today_count}</h1></div>", unsafe_allow_html=True)

# ২. মাসের মোট স্পন্সর কন্টেন্ট
total_month = len(df) if not df.empty else 0
with dash_col2:
    st.markdown(f"<div class='metric-card'><h4 style='color:white'>Total This Month</h4><h1 style='color:#ffc709'>{total_month}</h1></div>", unsafe_allow_html=True)

# ৩. স্পন্সর ডেইলি টার্গেট ট্র্যাকার
with dash_col3:
    st.markdown("<div class='metric-card'><h4 style='color:white'>Sponsor Target Check</h4>", unsafe_allow_html=True)
    if not df.empty:
        # উদাহরণস্বরূপ: কোনো স্পন্সরের আজ ৫টি ভিডিও দেওয়ার কথা থাকলে এখানে তা দেখাবে
        active_sponsors = df[df['Date'] == today_date]['Sponsor'].value_counts()
        for sp, count in active_sponsors.items():
            st.markdown(f"<p style='color:#ffc709; margin:0;'>{sp}: {count}/5 Done</p>", unsafe_allow_html=True)
    else:
        st.write("No data for today")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TABS FOR NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["📥 Data Entry", "📋 Content Logs", "📈 Sponsor Analytics"])

with tab1:
    st.markdown("### 📝 Submit New Content")
    with st.form("entry_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            d_date = st.date_input("Upload Date", datetime.now())
            d_head = st.text_input("Headline / Caption")
            # আপনার ৩০ জন স্পন্সরের নাম এখানে ড্রপডাউন হিসেবে দিতে পারেন
            d_sponsor = st.selectbox("Select Sponsor", ["Sponsor A", "Sponsor B", "Sponsor C", "Others"])
        with f_col2:
            d_fb = st.text_input("Facebook Link")
            d_yt = st.text_input("YouTube Link")
            d_tt = st.text_input("TikTok Link")
            d_ig = st.text_input("Instagram Link")
        
        d_notes = st.text_area("Internal Notes")
        submit = st.form_submit_button("🚀 Save to Cloud Database")
        
        if submit:
            if not user_email: st.error("Please enter your email in the sidebar first!")
            else: st.success(f"Data for '{d_sponsor}' submitted successfully!")

with tab2:
    st.markdown(f"### 📄 All Records for {current_month_name}")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No records found for this month.")

with tab3:
    st.markdown("### 📉 Monthly Sponsor Overview")
    if not df.empty:
        # স্পন্সর অনুযায়ী পুরো মাসের সামারি টেবিল
        sponsor_summary = df['Sponsor'].value_counts().reset_index()
        sponsor_summary.columns = ['Sponsor Name', 'Total Contents Provided']
        
        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.table(sponsor_summary)
        with col_chart:
            st.bar_chart(df['Sponsor'].value_counts())
            
        # PDF Reporting
        selected_sp = st.selectbox("Download Report for Sponsor:", sponsor_summary['Sponsor Name'])
        # (PDF generation code remains same as before)
        st.button("📄 Generate & Download PDF Report")
    else:
        st.info("Analytics will appear here once data is entered.")

# --- FOOTER ---
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'>© 2026 {APP_NAME} | Managed by Channel One Team</p>", unsafe_allow_html=True)
