import streamlit as st
import google.generativeai as genai
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# ==========================================
# 🔑 ส่วนตั้งค่าระบบ
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="ระบบบันทึกจับกุมอัจฉริยะ", layout="wide", page_icon="🚓")

st.title("🚓 ระบบสร้างบันทึกจับกุม (ฝ่ายสืบสวน)")
st.markdown("กรอกข้อมูลให้ครบถ้วน เลือกให้ AI ช่วยแนะนำ (ถ้าต้องการ) และนำข้อความมาใส่ในช่องกรอก ก่อนสร้างบันทึก")

# ==========================================
# 📝 ส่วนที่ 1: ข้อมูลทั่วไป และ ผู้ต้องหา
# ==========================================
with st.container(border=True):
    st.subheader("📌 1. ข้อมูลการจับกุม และ ผู้ต้องหา")
    
    col1, col2 = st.columns(2)
    with col1:
        report_loc = st.text_input("สถานที่ทำบันทึก", placeholder="เช่น กองกำกับการสืบสวน ตำรวจภูธรจังหวัดภูเก็ต")
        report_date = st.text_input("วัน/เดือน/ปี และเวลา ที่บันทึก", placeholder="เช่น วันที่ 23 กันยายน 2568 เวลาประมาณ 15.30 น.")
        arrest_date = st.text_input("วัน/เดือน/ปี และเวลา ที่จับกุม", placeholder="เช่น วันที่ 23 กันยายน 2568 เวลาประมาณ 13.20 น.")
        arrest_loc = st.text_area("สถานที่เกิดเหตุ/จับกุม", height=100)
        commanders = st.text_area("อำนวยการจับกุมโดย", placeholder="พ.ต.อ... ผกก..., พ.ต.ท... รอง ผกก...", height=100)
        officers = st.text_area("เจ้าหน้าที่ตำรวจชุดจับกุม ได้แก่", placeholder="พ.ต.ท.สมชาย ใจดี, ร.ต.อ.รักชาติ ยิ่งชีพ, ด.ต.ยอดเยี่ยม เกรียงไกร (คั่นชื่อด้วยลูกน้ำ , หรือขึ้นบรรทัดใหม่)", height=100)
    
    with col2:
        suspect_name = st.text_input("ชื่อ-นามสกุล ผู้ต้องหา")
        c2_1, c2_2, c2_3 = st.columns([2, 2, 1])
        with c2_1:
            suspect_id = st.text_input("เลขบัตรประชาชน/พาสปอร์ต")
        with c2_2:
            suspect_nationality = st.text_input("สัญชาติ")
        with c2_3:
            suspect_age = st.text_input("อายุ")
            
        suspect_address = st.text_area("ที่อยู่ผู้ต้องหา", height=68)
        
        st.markdown("**ข้อมูล พ.ร.บ.อุ้มหายฯ**")
        notify_date = st.text_input("วันที่แจ้งข้อมูล", placeholder="เช่น 23 ก.ย. 2568")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            notify_attorney = st.text_input("เวลาแจ้งอัยการ", placeholder="เช่น 14.00 น.")
        with col_n2:
            notify_district = st.text_input("เวลาแจ้งนายอำเภอ", placeholder="เช่น 14.15 น.")

# ==========================================
# ⚖️ ส่วนที่ 2: คดี ของกลาง และ พฤติการณ์ (ข้อมูลจริงที่จะนำไปสร้างเอกสาร)
# ==========================================
with st.container(border=True):
    st.subheader("⚖️ 2. ของกลาง ข้อหา และพฤติการณ์ (สำหรับสร้างเอกสาร)")
    st.warning("⚠️ ข้อมูลในช่องนี้ จะถูกนำไปสร้างเป็นบันทึกจับกุมฉบับจริง ดังนั้นต้องกรอกให้สมบูรณ์ครับ")
    
    evidence = st.text_area("ของกลางที่ตรวจยึด", placeholder="1. ... พบที่...\n2. ... พบที่...", height=100)
    charge_input = st.text_area("ข้อกล่าวหา", placeholder="กรอกข้อหาที่นี่...", height=68)
    behavior_input = st.text_area("พฤติการณ์การจับกุมฉบับสมบูรณ์", height=200, placeholder="พิมพ์พฤติการณ์ หรือ ก๊อปปี้ข้อความที่ AI แนะนำจากด้านล่างมาวางที่นี่...")
    suspect_statement = st.text_area("คำให้การของผู้ต้องหาในชั้นจับกุม", placeholder="เช่น ในชั้นจับกุม ผู้ต้องหาให้การรับสารภาพตลอดข้อกล่าวหา โดยรับว่า...", height=68)

# ==========================================
# 🤖 ส่วนที่ 3: พื้นที่ทำงานของ AI (แยก 3 บล็อค)
# ==========================================
with st.container(border=True):
    st.subheader("🤖 3. ผู้ช่วย AI (กดเพื่อขอคำแนะนำ)")
    st.info("💡 เมื่อ AI แนะนำข้อความให้แล้ว ให้ท่าน 'ก๊อปปี้' ข้อความไปวางในกล่องด้านบน (ส่วนที่ 2) ด้วยตนเอง")

    # บล็อคที่ 1: ร่างพฤติการณ์ใหม่
    st.markdown("#### 🔹 3.1 ให้ AI ร่างพฤติการณ์ใหม่ (กรณีไม่ได้พิมพ์พฤติการณ์)")
    if st.button("📝 ร่างพฤติการณ์จากข้อมูลทั้งหมด"):
        if not charge_input or not evidence or not arrest_loc or not suspect_name:
            st.error("กรุณากรอก 'ผู้ต้องหา', 'สถานที่เกิดเหตุ', 'ของกลาง' และ 'ข้อกล่าวหา' ให้ครบก่อนครับ")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""
                คุณคือพนักงานสืบสวนมืออาชีพของสำนักงานตำรวจแห่งชาติไทย จงร่าง 'พฤติการณ์การจับกุม' ฉบับสมบูรณ์ที่พร้อมใช้งานทันที 
                โดยห้ามเว้นช่องว่าง (เช่น [ชื่อ] หรือ [เวลา]) ให้ใช้ข้อมูลด้านล่างนี้ผูกเป็นเรื่องราวให้ครบถ้วนตามหลักนิยมการเขียนบันทึกจับกุม:
                
                - วันเวลาจับกุม: {arrest_date}
                - สถานที่จับกุม: {arrest_loc}
                - ชุดจับกุม: {officers}
                - ผู้ต้องหา: {suspect_name}
                - ของกลาง: {evidence}
                - ข้อกล่าวหา: {charge_input}
                - คำให้การ: {suspect_statement}
                
                ให้เขียนบรรยายตั้งแต่ชุดจับกุมได้รับแจ้ง/ออกตรวจ จนพบตัวผู้ต้องหา การแสดงตัวตรวจค้น การพบของกลาง การแจ้งข้อหาและสิทธิ และจบที่การนำตัวส่งพนักงานสอบสวน 
                ให้เขียนด้วยภาษากฎหมายที่รัดกุม เป็นทางการ และต้องไม่มีช่องว่างให้เติมเองเด็ดขาด
                """
                with st.spinner('กำลังร่างพฤติการณ์ฉบับสมบูรณ์...'):
                    st.session_state['ai_result_1'] = model.generate_content(prompt).text
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
    
    if 'ai_result_1' in st.session_state:
        st.success("✨ คำแนะนำจาก AI (ก๊อปปี้ไปวางด้านบนได้เลย):")
        st.write(st.session_state['ai_result_1'])

    st.divider()

    # บล็อคที่ 2: แนะนำข้อหา
    st.markdown("#### 🔹 3.2 ให้ AI วิเคราะห์และแนะนำข้อหา (จากพฤติการณ์)")
    if st.button("⚖️ วิเคราะห์ข้อหา"):
        if not behavior_input:
            st.error("กรุณาพิมพ์เรื่องราวในช่อง 'พฤติการณ์การจับกุม' ด้านบนก่อนครับ")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"จากพฤติการณ์นี้: '{behavior_input}' และของกลาง: '{evidence}' จงระบุ 'ฐานความผิด/ข้อกล่าวหา' ตามกฎหมายไทย ตอบมาเฉพาะชื่อข้อหาที่ครบถ้วน"
                with st.spinner('กำลังวิเคราะห์ข้อหา...'):
                    st.session_state['ai_result_2'] = model.generate_content(prompt).text
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
                
    if 'ai_result_2' in st.session_state:
        st.success("✨ ข้อหาที่ AI แนะนำ (ก๊อปปี้ไปวางด้านบนได้เลย):")
        st.write(st.session_state['ai_result_2'])

    st.divider()

    # บล็อคที่ 3: เกลาพฤติการณ์
    st.markdown("#### 🔹 3.3 ให้ AI เกลาและเติมเต็มพฤติการณ์ให้สมบูรณ์")
    if st.button("✨ เกลาพฤติการณ์ให้สมบูรณ์พร้อมใช้"):
        if not behavior_input:
            st.error("กรุณาพิมพ์เรื่องราวคร่าวๆ ในช่อง 'พฤติการณ์การจับกุม' ด้านบนก่อนครับ")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"""
                คุณคือพนักงานสืบสวนมืออาชีพ จงนำเหตุการณ์คร่าวๆ นี้ มาเกลาและขยายความให้เป็น '
