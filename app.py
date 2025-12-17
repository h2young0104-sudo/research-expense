import streamlit as st
import datetime
import smtplib
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# ==========================================
# [설정] 페이지 및 디자인
# ==========================================
st.set_page_config(page_title="연구비 증빙 제출 시스템", page_icon="🧾", layout="wide")

st.markdown("""
    <style>
    [data-testid="stFileUploader"] {
        background-color: #f8f9fa;
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 15px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        background-color: #e3e6ea;
        border-color: #4CAF50;
    }
    [data-testid="stFileUploader"] section > div {
        color: #333333;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧾 연구비 지출 증빙 제출 시스템")
st.markdown("### 🚨 안내: 작성된 내용은 안희영 선생님에게 메일로 전송됩니다.")
st.divider()

# ==========================================
# [기능 0] 상태 관리 및 초기화
# ==========================================
# 세션 상태 초기화 (폼 리셋을 위한 ID 관리)
if 'form_id' not in st.session_state:
    st.session_state.form_id = 0
if 'is_submitted' not in st.session_state:
    st.session_state.is_submitted = False

def reset_amount_check():
    # 결제 수단 변경 시 고액 여부 초기화
    key_name = f"amount_radio_key_{st.session_state.form_id}"
    if key_name in st.session_state:
        st.session_state[key_name] = "아니오 (100만 원 미만)"

# ==========================================
# [기능 1] 이메일 발송 함수
# ==========================================
def send_email_with_attachments(data_summary, files_dict):
    try:
        sender_email = st.secrets["email"]["sender_address"]
        sender_pass = st.secrets["email"]["sender_password"]
        receiver_emails = st.secrets["email"]["receiver_address"]

        msg = MIMEMultipart()
        msg['Subject'] = f"[연구비제출] {data_summary['성명']} - {data_summary['항목']} ({data_summary['날짜']})"
        msg['From'] = sender_email
        msg['To'] = receiver_emails

        body = f"""
        <h3>🧾 연구비 증빙 서류 제출 알림</h3>
        <p>연구비 지출 증빙 서류가 접수되었습니다.</p>
        <p>아래 내용을 확인하여 시스템에 등록 부탁드립니다.</p>
        <hr>
        <ul>
            <li><b>성명:</b> <span style="color:blue;">{data_summary['성명']}</span></li>
            <li><b>과제명:</b> {data_summary['과제']}</li>
            <li><b>지출항목:</b> {data_summary['항목']} ({data_summary['결제수단']})</li>
            <li><b>고액여부:</b> {data_summary['고액']}</li>
            <li><b>사유/내용:</b> {data_summary['사유']}</li>
            <li><b>제출일시:</b> {data_summary['날짜']} (KST)</li>
        </ul>
        <hr>
        <p>※ 첨부된 파일({len([f for f in files_dict.values() if f is not None])}개)을 확인해주세요.</p>
        """
        msg.attach(MIMEText(body, 'html'))

        for key, file_obj in files_dict.items():
            if file_obj is not None:
                file_obj.seek(0)
                safe_name = f"{data_summary['날짜'][:10]}_{data_summary['성명']}_{key}_{file_obj.name}"
                part = MIMEApplication(file_obj.read(), Name=safe_name)
                part.add_header('Content-Disposition', 'attachment', filename=safe_name)
                msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_pass)
            server.send_message(msg)
        
        return True
