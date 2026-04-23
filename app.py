import streamlit as st
import streamlit.components.v1 as components

# 1. ตั้งค่าพื้นฐาน: ชื่อเว็บบน Browser Tab และขยายจอให้กว้างที่สุด
st.set_page_config(
    page_title="FTF CRA - Clinical Simulation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS Hack: สั่งซ่อนทุกอย่างที่เป็นของ Streamlit (Header, Footer, Padding)
# เพื่อให้หน้าจอ Lovable แสดงผลได้เต็มพื้นที่ 100% ไม่กวนสายตา
st.markdown("""
    <style>
    /* ซ่อน Header และ Footer */
    header, footer {visibility: hidden !important;}
    
    /* ลบช่องว่างรอบๆ ตัวเว็บ */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    
    /* แก้ไขปัญหาระยะห่างของ Element ภายใน */
    #root > div:nth-child(1) > div > div > div > div > section > div {
        padding-top: 0rem !important;
    }

    /* ปรับแต่งให้ iframe แสดงผลเต็มความกว้าง */
    iframe {
        width: 100%;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. ดึงหน้าเว็บ Lovable มาแสดง
# ใช้ความสูงแบบ 100vh (เต็มความสูงหน้าจอของคนดู)
components.iframe("https://ftf-cra.lovable.app/", height=1000, scrolling=True)
