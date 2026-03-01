import streamlit as st
import google.generativeai as genai
import docx
from docx.shared import Pt
import io

# ==========================================
# 🔑 ส่วนตั้งค่าระบบ (ใส่ API Key ของพี่ตรงนี้)
# ==========================================
API_KEY = st.secrets["GEMINI_API_KEY"] # ใช้แบบดึงจากตู้เซฟเหมือนเดิมครับ

st.set_page_config(page_title="ระบบบันทึกจับกุมอัจฉริยะ", layout="wide", page_icon="🚓")

st.title("🚓 ระบบสร้างบันทึกจับกุม (ฝ่ายสืบสวน)")
st.markdown("กรอกข้อมูลให้ครบถ้วน จากนั้นให้ AI ช่วยร่างพฤติการณ์ และดาวน์โหลดเป็นไฟล์ Word เพื่อนำไปใช้งาน")

# ==========================================
# 📝 ส่วนที่ 1: ข้อมูลเบื้องต้น
# ==========================================
with st.container(border=True):
    st.subheader("📌 1. ข้อมูลการจับกุม และ ผู้ต้องหา")
    
    col1, col2 = st.columns(2)
    with col1:
        arrest_date = st.text_input("วันเวลาจับกุม", placeholder="เช่น 1 มี.ค. 2569 เวลา 14.00 น.")
        arrest_loc = st.text_area("สถานที่จับกุม", placeholder="เช่น ถ.ภูเก็ต ต.ตลาดใหญ่ อ.เมือง จ.ภูเก็ต", height=100)
        officers = st.text_area("ชื่อและยศ ชุดจับกุม", placeholder="พ.ต.ท. ..., ร.ต.อ. ...", height=100)
    
    with col2:
        report_date = st.text_input("วันเวลาที่ทำบันทึก", placeholder="เช่น 1 มี.ค. 2569 เวลา 16.00 น.")
        report_loc = st.text_input("สถานที่ทำบันทึก", placeholder="เช่น กก.สส.ภ.จว.ภูเก็ต หรือ สภ.เมืองภูเก็ต")
        suspect_name = st.text_input("ชื่อ-นามสกุล ผู้ต้องหา")
        
        c2_1, c2_2, c2_3 = st.columns([2, 2, 1])
        with c2_1:
            suspect_id = st.text_input("เลขบัตรประชาชน")
        with c2_2:
            suspect_phone = st.text_input("เบอร์โทรศัพท์")
        with c2_3:
            suspect_age = st.text_input("อายุ")
            
        suspect_address = st.text_area("ที่อยู่ตามบัตรประชาชน", height=68)

# ==========================================
# ⚖️ ส่วนที่ 2: คดีและของกลาง
# ==========================================
with st.container(border=True):
    st.subheader("⚖️ 2. ข้อหา และ ของกลาง")
    charge_input = st.text_input("ข้อหา", placeholder="กรอกข้อหาให้ชัดเจน (สำคัญมาก หากต้องการให้ AI สร้างพฤติการณ์ให้)")
    evidence = st.text_area("ของกลางที่ตรวจยึด", placeholder="1. ...\n2. ...", height=100)

# ==========================================
# 🤖 ส่วนที่ 3: ผู้ช่วย AI ร่างพฤติการณ์
# ==========================================
with st.container(border=True):
    st.subheader("🤖 3. พฤติการณ์การจับกุม")
    st.info("💡 **วิธีใช้งาน:** หากพี่กรอกข้อหาด้านบนไว้แล้ว พี่สามารถปล่อยช่องนี้ทิ้งไว้ว่างๆ แล้วกดปุ่ม AI เพื่อให้มันแต่งเรื่องให้ตั้งแต่ต้นได้เลย หรือถ้าพี่มีโครงเรื่องอยู่แล้วก็พิมพ์ลงไปให้ AI ช่วยเกลาก็ได้ครับ")
    
    behavior_input = st.text_area("พฤติการณ์การจับกุม (ร่างคร่าวๆ / หรือเว้นว่างไว้)", height=150)
    
    if st.button("✨ ให้ AI ช่วยร่าง/เกลา พฤติการณ์จับกุม", type="primary"):
        if not charge_input and not behavior_input:
            st.warning("⚠️ กรุณากรอก 'ข้อหา' หรือ 'พฤติการณ์คร่าวๆ' อย่างใดอย่างหนึ่งครับ AI จะได้มีข้อมูลไปแต่งเรื่องถูกคดี")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # เงื่อนไขความฉลาด: ถ้าไม่ได้พิมพ์พฤติการณ์มา ให้แต่งให้ใหม่เลยจากข้อหา
                if not behavior_input:
                    prompt = f"""
                    คุณคือพนักงานสืบสวนมืออาชีพ จงแต่ง 'พฤติการณ์การจับกุม' ขึ้นมาใหม่ทั้งหมด ให้สอดคล้องกับข้อหาและข้อมูลดังนี้:
                    - ข้อหา: {charge_input}
                    - สถานที่จับกุม: {arrest_loc}
                    - ของกลาง: {evidence}
                    ให้เขียนเป็นภาษากฎหมายที่รัดกุม เป็นทางการ และสมจริง (ไม่ต้องใส่ชื่อผู้ต้องหาหรือชุดจับกุมซ้ำในพฤติการณ์ ให้เล่าเฉพาะเหตุการณ์ลงมือจับกุมและการตรวจค้น)
                    """
                else:
                    prompt = f"""
                    คุณคือพนักงานสืบสวนมืออาชีพ จงนำเหตุการณ์คร่าวๆ ต่อไปนี้ มาเกลาใหม่ให้เป็น 'พฤติการณ์การจับกุม' ด้วยภาษากฎหมายที่สละสลวย รัดกุม:
                    เหตุการณ์: {behavior_input}
                    ข้อหาที่เกี่ยวข้อง: {charge_input}
                    ของกลาง: {evidence}
                    """
                
                with st.spinner('กำลังใช้ AI วิเคราะห์และเรียบเรียง...'):
                    response = model.generate_content(prompt)
                    st.session_state['ai_behavior'] = response.text
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")

    # แสดงผลลัพธ์พฤติการณ์ในกล่องข้อความสวยๆ
    if 'ai_behavior' in st.session_state:
        st.success("✅ ร่างพฤติการณ์สำเร็จ! ตรวจสอบข้อความด้านล่างนี้ (แก้ไขเพิ่มเติมได้ก่อนกดโหลด Word)")
        final_behavior = st.text_area("พฤติการณ์ที่สมบูรณ์ (สามารถแก้ไขข้อความตรงนี้ได้เลย)", value=st.session_state['ai_behavior'], height=300)
    else:
        final_behavior = behavior_input

# ==========================================
# 📄 ส่วนที่ 4: ดาวน์โหลดเป็น Word
# ==========================================
st.divider()
st.subheader("📄 4. สร้างและดาวน์โหลดเอกสาร")

def create_word_doc():
    doc = docx.Document()
    
    # กำหนดฟอนต์เริ่มต้นเป็น TH Sarabun PSK (ถ้าในเครื่องมีฟอนต์นี้ มันจะแสดงผลสวยงาม)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'TH Sarabun PSK'
    font.size = docx.shared.Pt(16)
    
    # หัวกระดาษ
    title = doc.add_paragraph()
    title.alignment = 1 # ตรงกลาง
    run = title.add_run("บันทึกการจับกุม")
    run.bold = True
    
    # สถานที่ทำบันทึก
    p_loc = doc.add_paragraph()
    p_loc.alignment = 2 # ชิดขวา
    p_loc.add_run(f"ทำที่ {report_loc}\nวันเวลา {report_date}")
    
    # ย่อหน้าที่ 1: ข้อมูลการจับ
    p1 = doc.add_paragraph()
    p1.paragraph_format.first_line_indent = docx.shared.Inches(0.5)
    p1.add_run(f"ด้วยวันนี้ เมื่อเวลาประมาณ {arrest_date} เจ้าหน้าที่ตำรวจชุดจับกุมประกอบด้วย {officers} ")
    p1.add_run(f"ได้ร่วมกันทำการจับกุมตัว {suspect_name} อายุ {suspect_age} ปี หมายเลขประจำตัวประชาชน {suspect_id} ")
    p1.add_run(f"ที่อยู่ {suspect_address} หมายเลขโทรศัพท์ {suspect_phone}")
    
    # ย่อหน้าที่ 2: สถานที่และของกลาง
    p2 = doc.add_paragraph()
    p2.paragraph_format.first_line_indent = docx.shared.Inches(0.5)
    p2.add_run(f"สถานที่จับกุม: {arrest_loc}\n")
    p2.add_run(f"พร้อมด้วยของกลาง:\n{evidence}\n")
    p2.add_run(f"โดยกล่าวหาว่า: {charge_input}")
    
    # ย่อหน้าที่ 3: พฤติการณ์
    doc.add_paragraph().add_run("\nพฤติการณ์แห่งการจับกุม:").bold = True
    p3 = doc.add_paragraph()
    p3.paragraph_format.first_line_indent = docx.shared.Inches(0.5)
    p3.add_run(final_behavior)
    
    # ลงชื่อ
    doc.add_paragraph("\n\n")
    p_sign = doc.add_paragraph()
    p_sign.alignment = 1
    p_sign.add_run("(ลงชื่อ).......................................................ผู้จับกุม/ผู้บันทึก\n")
    p_sign.add_run("(ลงชื่อ).......................................................ผู้ต้องหา")
    
    # บันทึกไฟล์ลงหน่วยความจำ
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ปุ่มดาวน์โหลด Word
if st.button("📥 ดาวน์โหลดบันทึกจับกุม (ไฟล์ Word .docx)", use_container_width=True):
    word_file = create_word_doc()
    st.download_button(
        label="คลิกที่นี่เพื่อบันทึกไฟล์ลงเครื่อง",
        data=word_file,
        file_name=f"บันทึกจับกุม_{suspect_name}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary"
    )
