import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# --- DATABASE SETUP ---
conn = sqlite3.connect('content_tracker.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        member_email TEXT,
        headline TEXT,
        fb_link TEXT,
        yt_link TEXT,
        tiktok_link TEXT,
        insta_link TEXT,
        sponsor TEXT,
        notes TEXT
    )
''')
conn.commit()

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Content & Sponsor Tracker", layout="wide")

# --- CUSTOM CSS FOR THE GLOSSY DARK/LIGHT THEME ---
# Utilizing #ffc709 (Yellow) and Glossy Dark Blue (#0B192C / #1E3E62)
st.markdown("""
    <style>
    /* Global Styles */
    .main {
        padding: 2rem;
    }
    h1, h2, h3 {
        color: #ffc709 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        text-shadow: 0px 0px 10px rgba(255, 199, 9, 0.3);
    }
    
    /* Input Form Glossy Effect */
    div[data-testid="stForm"] {
        border: 1px solid rgba(255, 199, 9, 0.2);
        border-radius: 15px;
        background: linear-gradient(135deg, rgba(30, 62, 98, 0.4) 0%, rgba(11, 25, 44, 0.6) 100%);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        padding: 2rem;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(45deg, #1E3E62, #0B192C);
        color: #ffc709 !important;
        border: 2px solid #ffc709 !important;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        box-shadow: 0 0 15px rgba(255,199,9,0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: #ffc709 !important;
        color: #0B192C !important;
        box-shadow: 0 0 25px rgba(255,199,9,0.5);
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- PDF GENERATION FUNCTION ---
def generate_pdf(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#0B192C'),
        spaceAfter=20
    )
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10
    )
    
    # Header
    story.append(Paragraph("Content & Sponsor Marketing Report", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Table Data Prep
    headers = ['Date', 'Uploader', 'Headline', 'Links (FB/YT/TT/IG)', 'Sponsor', 'Notes']
    data = [headers]
    
    for idx, row in df.iterrows():
        links = f"FB: {row['fb_link']}\nYT: {row['yt_link']}\nTT: {row['tiktok_link']}\nIG: {row['insta_link']}"
        data.append([
            Paragraph(str(row['date']), cell_style),
            Paragraph(str(row['member_email']), cell_style),
            Paragraph(str(row['headline']), cell_style),
            Paragraph(links, cell_style),
            Paragraph(str(row['sponsor']), cell_style),
            Paragraph(str(row['notes']), cell_style)
        ])
    
    # ReportLab Table Styling (Using Dark Blue & Yellow accents)
    t = Table(data, colWidths=[60, 80, 100, 150, 80, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0B192C')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#ffc709')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F4F6F9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#1E3E62')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- APP UI ---
st.title("🎬 Media Team Content & Sponsor Tracker")
st.write("টিমের সদস্যরা লগইন মেইল দিয়ে নিচে কন্টেন্ট এর তথ্য আপলোড করুন।")

# Sidebar for Team Authentication Note & Theme Switch Info
st.sidebar.header("🔐 Team Access & Theme")
user_email = st.sidebar.text_input("আপনার অফিসিয়াল মেইল দিন (যেমন: member@company.com)", value="")

st.sidebar.markdown("""
---
**💡 থিম পরিবর্তন (Dark/Light Mode):**
আপনার স্ক্রিনের ডানদিকের উপরে **Settings (⚙️) -> Theme** থেকে সরাসরি Dark বা Light মোড সিলেক্ট করতে পারবেন। আমাদের কাস্টম কালার দুটি মোডেই চমৎকার কাজ করবে।
""")

# --- ENTRY FORM ---
st.header("📥 নতুন কন্টেন্ট এন্ট্রি ফর্ম")
with st.form("content_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        content_date = st.date_input("কন্টেন্ট আপলোডের তারিখ", datetime.now())
        headline = st.text_input("হেডলাইন / ক্যাপশন")
        sponsor = st.text_input("স্পন্সর কোম্পানির নাম")
        notes = st.text_area("মন্তব্য (যদি থাকে)")
        
    with col2:
        fb_link = st.text_input("ফেসবুক লিংক (FB Link)")
        yt_link = st.text_input("ইউটিউব লিংক (YT Link)")
        tiktok_link = st.text_input("টিকটক লিংক (TikTok Link)")
        insta_link = st.text_input("ইন্সটাগ্রাম লিংক (Instagram Link)")
        
    submit_button = st.form_submit_button("ডাটাবেজে সংরক্ষণ করুন")

if submit_button:
    if user_email == "":
        st.error("⚠️ ডাটা সাবমিট করার আগে অবশ্যই সাইডবারে আপনার 'মেইল এড্রেস' প্রদান করুন।")
    elif headline == "":
        st.error("⚠️ কন্টেন্টের হেডলাইন দেওয়া বাধ্যতামূলক।")
    else:
        # Save to SQLite
        c.execute('''
            INSERT INTO content (date, member_email, headline, fb_link, yt_link, tiktok_link, insta_link, sponsor, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(content_date), user_email, headline, fb_link, yt_link, tiktok_link, insta_link, sponsor, notes))
        conn.commit()
        st.success("✅ কন্টেন্ট সফলভাবে ডাটাবেজে সেভ হয়েছে!")

# --- DISPLAY & REPORT GENERATION ---
st.separator()
st.header("📊 সংরক্ষিত কন্টেন্ট তালিকা ও রিপোর্ট")

# Load Data
df = pd.read_sql_query("SELECT id, date, member_email, headline, fb_link, yt_link, tiktok_link, insta_link, sponsor, notes FROM content ORDER BY id DESC", conn)

if not df.empty:
    # Filter by Sponsor Option
    all_sponsors = ["All"] + list(df['sponsor'].unique())
    selected_sponsor = st.selectbox("স্পন্সর অনুযায়ী ফিল্টার করুন (পিডিএফ ডাউনলোডের জন্য)", all_sponsors)
    
    filtered_df = df if selected_sponsor == "All" else df[df['sponsor'] == selected_sponsor]
    
    # Display Table
    st.dataframe(filtered_df, use_container_width=True)
    
    # PDF Download Button
    pdf_data = generate_pdf(filtered_df)
    st.download_button(
        label="📥 স্পন্সরের জন্য PDF রিপোর্ট ডাউনলোড করুন",
        data=pdf_data,
        file_name=f"Sponsor_Report_{selected_sponsor}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf"
    )
else:
    st.info("এখনো কোনো কন্টেন্ট আপলোড করা হয়নি।")
