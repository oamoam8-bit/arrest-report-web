import streamlit as st
import google.generativeai as genai
import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

# ==========================================
# 🔑 ส่วนตั้งค่าระบบ (ใส่ API Key ของพี่ตรงนี้)
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="ระบบบันทึกจับกุมอัจฉริยะ", layout="wide", page_icon="🚓")

st.title("🚓 ระบบสร้างบันทึกจับกุม (ฝ่ายสืบสวน)")
st.markdown("กรอกข้อมูลให้ครบถ้วน เลือกใช้งาน AI ตามความต้องการ และดาวน์โหลดเป็นไฟล์ Word ตามฟอร์มมาตรฐาน")

# ==========================================
# 📝 ส่วนที่ 1: ข้อมูลทั่วไป และ ผู้ต้องหา
# ==========================================
with st.container(border=True):
    st.subheader("📌 1. ข้อมูลการจับกุม และ ผู้ต้องหา")
    
    col1, col2 = st.columns(2)
    with col1:
        report_loc = st.text_input("สถานที่ทำบันทึก", placeholder="เช่น กก.สส.ภ.จว.ภูเก็ต")
        report_date = st.text_input("วัน/เดือน/ปี และเวลา ที่บันทึก", placeholder="เช่น 23 กันยายน 2568 เวลา 15.30 น.")
        arrest_date = st.text_input("วัน/เดือน/ปี และเวลา ที่จับกุม", placeholder="เช่น 23 กันยายน 2568 เวลา 13.20 น.")
        arrest_loc = st.text_area("สถานที่เกิดเหตุ/จับกุม", height=100)
        commanders = st.text_area("อำนวยการจับกุมโดย", placeholder="พ.ต.อ... ผกก..., พ.ต.ท... รอง ผกก...", height=100)
        officers = st.text_area("เจ้าหน้าที่ชุดจับกุม", placeholder="พ.ต.ท..., ร.ต.อ..., ด.ต...", height=100)
    
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
        
        st.markdown("**ข้อมูล พ.ร.บ.อุ้มหายฯ (เวลาที่แจ้ง)**")
        notify_attorney = st.text_input("เวลาที่แจ้ง อัยการ", placeholder="เช่น 14.00 น.")
        notify_district = st.text_input("เวลาที่แจ้ง นายอำเภอ", placeholder="เช่น 14.15 น.")

# ==========================================
# ⚖️ ส่วนที่ 2: คดีและของกลาง
# ==========================================
with st.container(border=True):
    st.subheader("⚖️ 2. ของกลาง และ ข้อหา")
    
    evidence = st.text_area("ของกลางที่ตรวจยึด และ ตำแหน่งที่พบ", placeholder="1. ... พบที่...\n2. ... พบที่...", height=100)
    
    # ใช้ session_state เพื่อให้ AI สามารถมาเติมข้อหาให้ได้
    if 'ai_charge' not in st.session_state:
        st.session_state['ai_charge'] = ""
        
    charge_input = st.text_area("ข้อกล่าวหา", value=st.session_state['ai_charge'], placeholder="พิมพ์ข้อหาเอง หรือเว้นไว้ให้ AI แนะนำจากพฤติการณ์ด้านล่าง", height=68)

# ==========================================
# 🤖 ส่วนที่ 3: พื้นที่ทำงานของ AI (แยก 3 ฟังก์ชัน)
# ==========================================
with st.container(border=True):
    st.subheader("🤖 3. พฤติการณ์การจับกุม (AI Assistant)")
    
    if 'ai_behavior' not in st.session_state:
        st.session_state['ai_behavior'] = ""
        
    behavior_input = st.text_area("พฤติการณ์การจับกุม", value=st.session_state['ai_behavior'], height=200, placeholder="พิมพ์เรื่องราวคร่าวๆ แล้วให้ AI เกลา หรือเว้นว่างไว้ให้ AI ร่างขึ้นมาใหม่จากข้อหาก็ได้")
    
    st.markdown("##### 🎛️ เลือกคำสั่งให้ AI ช่วยเหลือ:")
    btn1, btn2, btn3 = st.columns(3)
    
    # --- ฟังก์ชัน 1: สร้างพฤติการณ์ใหม่จากความว่างเปล่า ---
    with btn1:
        if st.button("📝 1. AI ร่างพฤติการณ์ (กรณีไม่ได้พิมพ์)", use_container_width=True):
            if not charge_input or not evidence or not arrest_loc:
                st.warning("⚠️ กรุณากรอก 'สถานที่จับกุม', 'ของกลาง' และ 'ข้อกล่าวหา' ให้ครบก่อน เพื่อให้ AI มีข้อมูลไปแต่งเรื่องครับ")
            else:
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = f"""คุณคือพนักงานสืบสวนมืออาชีพ จงแต่ง 'พฤติการณ์การจับกุม' ขึ้นมาใหม่ให้สมจริง สอดคล้องกับข้อมูล:
                    - ข้อหา: {charge_input}
                    - สถานที่เกิดเหตุ: {arrest_loc}
                    - ของกลาง: {evidence}
                    เขียนเป็นภาษากฎหมายที่รัดกุม เป็นทางการ เริ่มต้นด้วย 'ก่อนทำการจับกุม...' และจบด้วยการจับกุมนำส่งพนักงานสอบสวน"""
                    with st.spinner('กำลังร่างพฤติการณ์ใหม่...'):
                        st.session_state['ai_behavior'] = model.generate_content(prompt).text
                        st.rerun()
                except Exception as e:
                    st.error(e)

    # --- ฟังก์ชัน 2: แนะนำข้อหาจากพฤติการณ์ ---
    with btn2:
        if st.button("⚖️ 2. AI วิเคราะห์และแนะนำข้อหา", use_container_width=True):
            if not behavior_input:
                st.warning("⚠️ กรุณาพิมพ์ 'พฤติการณ์' คร่าวๆ ก่อนครับ AI จะได้วิเคราะห์ข้อหาให้ได้")
            else:
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = f"""จากพฤติการณ์การจับกุมต่อไปนี้: '{behavior_input}'
                    ของกลาง: '{evidence}'
                    จงระบุ 'ฐานความผิด/ข้อกล่าวหา' ตามกฎหมายไทยที่ถูกต้องและครบถ้วนที่สุด ตอบมาเฉพาะชื่อข้อหาเท่านั้น ไม่ต้องอธิบายเพิ่ม"""
                    with st.spinner('กำลังวิเคราะห์ข้อกฎหมาย...'):
                        st.session_state['ai_charge'] = model.generate_content(prompt).text
                        st.rerun()
                except Exception as e:
                    st.error(e)

    # --- ฟังก์ชัน 3: เกลาพฤติการณ์ที่พิมพ์มาคร่าวๆ ---
    with btn3:
        if st.button("✨ 3. AI เกลาพฤติการณ์ให้สละสลวย", use_container_width=True):
            if not behavior_input:
                st.warning("⚠️ กรุณาพิมพ์พฤติการณ์คร่าวๆ ลงในกล่องข้อความก่อนครับ")
            else:
                try:
                    genai.configure(api_key=API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = f"""คุณคือพนักงานสืบสวนมืออาชีพ จงนำข้อความนี้มาเรียบเรียงใหม่ให้เป็น 'พฤติการณ์การจับกุม' ในรูปแบบภาษากฎหมายที่สละสลวย รัดกุม เหมาะสำหรับใช้ในศาล: 
                    ข้อความเดิม: {behavior_input}
                    (ปรับแก้เฉพาะภาษาให้ดูเป็นทางการขึ้น ห้ามแต่งเติมข้อเท็จจริงใหม่ลงไป)"""
                    with st.spinner('กำลังเกลาสำนวน...'):
                        st.session_state['ai_behavior'] = model.generate_content(prompt).text
                        st.rerun()
                except Exception as e:
                    st.error(e)

# ==========================================
# 📄 ส่วนที่ 4: สร้างเอกสาร Word ตามฟอร์มมาตรฐาน
# ==========================================
st.divider()
st.subheader("📄 4. สร้างบันทึกจับกุมฉบับสมบูรณ์ (Export to Word)")

def create_word_doc():
    doc = docx.Document()
    
    # ตั้งค่าฟอนต์มาตรฐาน
    style = doc.styles['Normal']
    font = style.font
    font.name = 'TH Sarabun PSK'
    font.size = Pt(16)
    
    # หัวเรื่อง
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("บันทึกการจับกุม")
    run.bold = True
    
    # ส่วนหัวตามฟอร์มที่ให้มา
    doc.add_paragraph(f"สถานที่ทำบันทึก\t\t{report_loc}")
    doc.add_paragraph(f"วัน/เดือน/ปี ที่บันทึก\t{report_date}")
    doc.add_paragraph(f"วัน/เดือน/ปี ที่จับกุม\t{arrest_date}")
    doc.add_paragraph(f"สถานที่เกิดเหตุ/จับกุม\t{arrest_loc}\n")
    
    # ชุดจับกุม
    p_cmd = doc.add_paragraph()
    p_cmd.add_run("นามเจ้าพนักงานผู้จับภายใต้การอำนวยการของ ").bold = True
    p_cmd.add_run(f"{commanders}\n")
    p_cmd.add_run("เจ้าหน้าที่ตำรวจชุดจับกุม ได้แก่ ").bold = True
    p_cmd.add_run(f"{officers}\n")
    
    # ผู้ต้องหา
    p_sus = doc.add_paragraph()
    p_sus.add_run("ได้ร่วมกันจับกุมตัวผู้ต้องหา คือ ").bold = True
    p_sus.add_run(f"{suspect_name} อายุ {suspect_age} ปี สัญชาติ {suspect_nationality} เลขประจำตัว {suspect_id} ที่อยู่ {suspect_address}\n")
    
    # ของกลางและข้อหา
    doc.add_paragraph().add_run("พร้อมด้วยของกลาง").bold = True
    doc.add_paragraph(f"{evidence}\n")
    
    p_charge = doc.add_paragraph()
    p_charge.add_run("โดยกล่าวหาว่า ").bold = True
    p_charge.add_run(f"“{st.session_state['ai_charge']}”\n")
    
    # แจ้งสิทธิ (ตามฟอร์มเป๊ะๆ)
    doc.add_paragraph().add_run("พร้อมได้แจ้งสิทธิของผู้ถูกจับให้ทราบถึงสิทธิตามกฎหมายตั้งแต่โอกาสแรกที่ถูกจับกุมแล้ว ดังนี้").bold = True
    doc.add_paragraph("1. มีสิทธิที่จะให้การหรือไม่ให้การก็ได้ และถ้อยคำของผู้ถูกจับอาจใช้เป็นพยานหลักฐานในการพิจารณาคดีได้")
    doc.add_paragraph("2. มีสิทธิที่จะพบและปรึกษาทนายความเป็นการเฉพาะตัว")
    doc.add_paragraph("3. มีสิทธิแจ้งให้ญาติหรือผู้ซึ่งตนไว้วางใจทราบถึงการจับกุม\nผู้ถูกจับได้รับทราบและเข้าใจถึงวัตถุประสงค์และเงื่อนไขของกฎหมายข้างต้นดีแล้ว\n")
    
    # พฤติการณ์
    p_beh = doc.add_paragraph()
    p_beh.add_run("พฤติการณ์ในการจับกุม กล่าวคือ ").bold = True
    p_beh.add_run(f"{st.session_state['ai_behavior']}\n")
    
    # ข้อความบังคับ พ.ร.บ.อุ้มหาย และการปฏิบัติตามกม. (จากฟอร์มต้นฉบับ)
    doc.add_paragraph("ในการจับครั้งนี้ เจ้าพนักงานผู้จับทุกนายได้ปฏิบัติตามอำนาจหน้าที่ตามกฎหมาย มิได้บังคับ ขู่เข็ญ หลอกลวง ทำร้ายร่างกาย หรือทำอันตรายแก่กาย หรือจิตใจผู้ใด...")
    doc.add_paragraph("ในการควบคุมตัวผู้ถูกจับ เจ้าหน้าที่ผู้จับกุมได้ทำการบันทึกภาพและเสียงอย่างต่อเนื่องในขณะจับและควบคุมตัวผู้ถูกจับ...")
    doc.add_paragraph("ผู้จับกุมไม่ได้กระทำการใดๆ อันเป็นการทรมาน การทำที่โหดร้าย ไร้มนุษยธรรม หรือย่ำยีศักดิ์ศรีความเป็นมนุษย์...")
    doc.add_paragraph(f"เจ้าหน้าที่ผู้จับกุม ได้แจ้งข้อมูลเกี่ยวกับผู้ถูกควบคุมตัว ไปยัง ศูนย์ป้องกันปราบปรามทรมานและการทำให้บุคคลสูญหายประจำสำนักงานอัยการ เวลา {notify_attorney}")
    doc.add_paragraph(f"เจ้าหน้าที่ผู้จับกุม ได้แจ้งข้อมูลเกี่ยวกับผู้ถูกควบคุมตัว ไปยังนายอำเภอ เวลา {notify_district}\n")
    
    # ลงท้ายและลายเซ็น
    doc.add_paragraph("รับรองว่าข้อความตามบันทึกการจับกุมนี้ถูกต้องตามความเป็นจริงทุกประการ จึงให้ลงลายมือชื่อไว้เป็นหลักฐาน\n\n")
    
    p_sign1 = doc.add_paragraph()
    p_sign1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sign1.add_run(f"(ลงชื่อ)........................................................................ ผู้ถูกจับ/รับสำเนาบันทึกการจับ\n({suspect_name})\n\n")
    
    p_sign2 = doc.add_paragraph()
    p_sign2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sign2.add_run("(ลงชื่อ)........................................................................ หัวหน้าชุดจับกุม\n\n")
    p_sign2.add_run("(ลงชื่อ)........................................................................ ผู้บันทึก/อ่าน\n")
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

if st.button("📥 4. สร้างและดาวน์โหลดบันทึกจับกุมฉบับสมบูรณ์ (Word)", type="primary", use_container_width=True):
    word_file = create_word_doc()
    st.download_button(
        label="คลิกที่นี่เพื่อบันทึกไฟล์ลงเครื่อง",
        data=word_file,
        file_name=f"บันทึกจับกุม_{suspect_name}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary"
    )
