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
        officers = st.text_area("เจ้าหน้าที่ตำรวจชุดจับกุม ได้แก่", placeholder="พิมพ์ชื่อคั่นด้วยลูกน้ำ เช่น: พ.ต.ท.สมชาย ใจดี, ร.ต.อ.รักชาติ ยิ่งชีพ, ด.ต.ยอดเยี่ยม เกรียงไกร", height=100)
    
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

    # บล็อคที่ 1: ร่างพฤติการณ์ใหม่ (แก้บั๊ก f-string และเพิ่มความฉลาดแล้ว)
    st.markdown("#### 🔹 3.1 ให้ AI ร่างพฤติการณ์ใหม่ (กรณีไม่ได้พิมพ์พฤติการณ์เลย)")
    if st.button("📝 ร่างพฤติการณ์จากข้อมูลทั้งหมด"):
        if not charge_input or not evidence or not arrest_loc or not suspect_name:
            st.error("กรุณากรอก 'ผู้ต้องหา', 'สถานที่เกิดเหตุ', 'ของกลาง' และ 'ข้อกล่าวหา' ให้ครบก่อนครับ")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # เขียน prompt แบบใหม่ ป้องกัน GitHub ตัดบรรทัดพัง
                prompt = (
                    f"ในฐานะตำรวจฝ่ายสืบสวน จงเขียน 'พฤติการณ์การจับกุม' ฉบับสมบูรณ์ พร้อมนำไปใช้งานทันที "
                    f"คำสั่งบังคับเด็ดขาด: ห้ามเว้นช่องว่าง [ ] ให้เติมเองเด็ดขาด ให้นำข้อมูลทั้งหมดนี้ร้อยเรียงเป็นเรื่องราวเดียวกันให้ครบถ้วน: \n"
                    f"วันเวลาจับกุม: {arrest_date}\n"
                    f"สถานที่: {arrest_loc}\n"
                    f"ชุดจับกุม: {officers}\n"
                    f"ผู้ต้องหา: {suspect_name}\n"
                    f"ของกลาง: {evidence}\n"
                    f"ข้อหา: {charge_input}\n"
                    f"คำให้การ: {suspect_statement}\n"
                    f"ให้บรรยายเริ่มตั้งแต่ชุดจับกุมออกตรวจหรือได้รับแจ้งเหตุ ไปจนถึงการพบผู้ต้องหา การแสดงตัวเข้าตรวจค้น "
                    f"การพบของกลาง การแจ้งข้อกล่าวหาและสิทธิตามกฎหมาย และการนำตัวส่งพนักงานสอบสวน ดำเนินคดีตามกฎหมาย"
                )
                
                with st.spinner('กำลังร่างพฤติการณ์ฉบับสมบูรณ์ (รอสักครู่)...'):
                    st.session_state['ai_result_1'] = model.generate_content(prompt).text
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
    
    if 'ai_result_1' in st.session_state:
        st.success("✨ คำแนะนำจาก AI (ก๊อปปี้ไปวางในช่องพฤติการณ์ด้านบนได้เลย):")
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
                prompt = (
                    f"จากพฤติการณ์นี้: '{behavior_input}' และของกลาง: '{evidence}' "
                    f"จงระบุ 'ฐานความผิด/ข้อกล่าวหา' ตามกฎหมายไทย ตอบมาเฉพาะชื่อข้อหาที่ครบถ้วน"
                )
                with st.spinner('กำลังวิเคราะห์ข้อหา...'):
                    st.session_state['ai_result_2'] = model.generate_content(prompt).text
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
                
    if 'ai_result_2' in st.session_state:
        st.success("✨ ข้อหาที่ AI แนะนำ (ก๊อปปี้ไปวางในช่องข้อหาด้านบนได้เลย):")
        st.write(st.session_state['ai_result_2'])

    st.divider()

    # บล็อคที่ 3: เกลาพฤติการณ์ (เพิ่มความฉลาดให้ดึงข้อมูลมาเติมเต็ม)
    st.markdown("#### 🔹 3.3 ให้ AI เกลาและเติมเต็มพฤติการณ์ให้สมบูรณ์")
    if st.button("✨ เกลาพฤติการณ์ให้สมบูรณ์พร้อมใช้"):
        if not behavior_input:
            st.error("กรุณาพิมพ์เรื่องราวคร่าวๆ ในช่อง 'พฤติการณ์การจับกุม' ด้านบนก่อนครับ")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = (
                    f"ในฐานะตำรวจฝ่ายสืบสวน จงนำเหตุการณ์ย่อต่อไปนี้:\n'{behavior_input}'\n\n"
                    f"มาเขียนขยายความและเกลาเป็น 'พฤติการณ์การจับกุม' ฉบับสมบูรณ์ โดยบังคับให้นำข้อมูลต่อไปนี้แทรกเข้าไปในเนื้อเรื่องให้ครบถ้วนและแนบเนียน "
                    f"คำสั่งบังคับเด็ดขาด: ห้ามเว้นช่องว่าง [ ] ให้เติมเองเด็ดขาด:\n"
                    f"วันเวลา: {arrest_date}\n"
                    f"สถานที่: {arrest_loc}\n"
                    f"ชุดจับกุม: {officers}\n"
                    f"ผู้ต้องหา: {suspect_name}\n"
                    f"ของกลาง: {evidence}\n"
                    f"ข้อหา: {charge_input}\n"
                    f"คำให้การ: {suspect_statement}\n"
                    f"ปรับสำนวนให้เป็นภาษากฎหมายที่รัดกุม สละสลวย ตามฟอร์มบันทึกจับกุมมาตรฐาน เล่าตั้งแต่การเข้าจับกุมจนถึงการนำส่งพนักงานสอบสวน"
                )
                
                with st.spinner('กำลังเกลาและเติมเต็มเนื้อหา (รอสักครู่)...'):
                    st.session_state['ai_result_3'] = model.generate_content(prompt).text
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
                
    if 'ai_result_3' in st.session_state:
        st.success("✨ พฤติการณ์ที่สมบูรณ์พร้อมใช้ (ก๊อปปี้ไปวางทับในช่องพฤติการณ์ด้านบนได้เลย):")
        st.write(st.session_state['ai_result_3'])

# ==========================================
# 📄 ส่วนที่ 4: ดูตัวอย่าง และ ดาวน์โหลด (ดึงข้อมูลจากช่องกรอกเท่านั้น)
# ==========================================
st.divider()
st.subheader("📄 4. ภาพรวมเอกสาร และ ดาวน์โหลด")

col_preview, col_export = st.columns(2)

with col_preview:
    if st.button("👁️ แสดงตัวอย่างบันทึกจับกุม", use_container_width=True):
        st.session_state['show_preview'] = True

with col_export:
    def create_word_doc():
        doc = docx.Document()
        style = doc.styles['Normal']
        font = style.font
        font.name = 'TH Sarabun PSK'
        font.size = Pt(16)
        
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.add_run("บันทึกการจับกุม").bold = True
        
        doc.add_paragraph(f"สถานที่ทำบันทึก\t\t{report_loc}")
        doc.add_paragraph(f"วัน/เดือน/ปี ที่บันทึก\t{report_date}")
        doc.add_paragraph(f"วัน/เดือน/ปี ที่จับกุม\t{arrest_date}")
        doc.add_paragraph(f"สถานที่เกิดเหตุ/จับกุม\t{arrest_loc}\n")
        
        p_cmd = doc.add_paragraph()
        p_cmd.add_run("นามเจ้าพนักงานผู้จับภายใต้การอำนวยการของ ").bold = True
        p_cmd.add_run(f"{commanders}\n")
        p_cmd.add_run("เจ้าหน้าที่ตำรวจชุดจับกุม ได้แก่ ").bold = True
        p_cmd.add_run(f"{officers}\n")
        
        p_sus = doc.add_paragraph()
        p_sus.add_run("ได้ร่วมกันจับกุมตัวผู้ต้องหา คือ ").bold = True
        p_sus.add_run(f"{suspect_name} อายุ {suspect_age} ปี สัญชาติ {suspect_nationality} เลขประจำตัว {suspect_id} ที่อยู่ {suspect_address}\n")
        
        doc.add_paragraph().add_run("พร้อมด้วยของกลาง").bold = True
        doc.add_paragraph(f"{evidence}\n")
        
        p_charge = doc.add_paragraph()
        p_charge.add_run("โดยกล่าวหาว่า ").bold = True
        p_charge.add_run(f"“{charge_input}”\n")
        
        doc.add_paragraph().add_run("พร้อมได้แจ้งสิทธิของผู้ถูกจับให้ทราบถึงสิทธิตามกฎหมายตั้งแต่โอกาสแรกที่ถูกจับกุมแล้ว ดังนี้").bold = True
        doc.add_paragraph("1. มีสิทธิที่จะให้การหรือไม่ให้การก็ได้ และถ้อยคำของผู้ถูกจับอาจใช้เป็นพยานหลักฐานในการพิจารณาคดีได้")
        doc.add_paragraph("2. มีสิทธิที่จะพบและปรึกษาทนายความเป็นการเฉพาะตัว")
        doc.add_paragraph("3. มีสิทธิแจ้งให้ญาติหรือผู้ซึ่งตนไว้วางใจทราบถึงการจับกุม (ถ้าไม่เป็นอุปสรรคต่อการจับกุม หรือควบคุม และ/หรือปัญหาด้านความปลอดภัย)\n"
                          "ผู้ถูกจับได้รับทราบและเข้าใจถึงวัตถุประสงค์และเงื่อนไขของกฎหมายข้างต้นดีแล้ว\n")
        
        p_beh = doc.add_paragraph()
        p_beh.add_run("พฤติการณ์ในการจับกุม กล่าวคือ ").bold = True
        p_beh.add_run(f"{behavior_input}\n")
        
        p_state = doc.add_paragraph()
        p_state.add_run("ในชั้นจับกุม ").bold = True
        p_state.add_run(f"{suspect_statement}\n")
        
        doc.add_paragraph("ในการจับครั้งนี้ เจ้าพนักงานผู้จับทุกนายได้ปฏิบัติตามอำนาจหน้าที่ตามกฎหมาย มิได้บังคับ ขู่เข็ญ หลอกลวง ทำร้ายร่างกาย "
                          "หรือทำอันตรายแก่กาย หรือจิตใจผู้ใด หรือให้สัญญาอื่นใดที่กระทำโดยมิชอบกับผู้ต้องหาแต่อย่างใด "
                          "และมิได้ทำให้ทรัพย์สินของผู้ใด สูญหาย เสียหาย หรือไร้ประโยชน์แต่อย่างใด")
        
        doc.add_paragraph("ในการควบคุมตัวผู้ถูกจับ เจ้าหน้าที่ผู้จับกุมได้ทำการบันทึกภาพและเสียงอย่างต่อเนื่องในขณะจับและควบคุมตัวผู้ถูกจับ"
                          "ในชั้นจับกุมจนกระทั่งส่งตัวให้พนักงานสอบสวน ตามมาตรา ๒๒ วรรคหนึ่ง แห่ง พ.ร.บ.ป้องกันและปราบปรามการทรมาน"
                          "และการกระทำให้สูญหาย พ.ศ.๒๕๖๕")
        
        doc.add_paragraph("ผู้จับกุมไม่ได้กระทำการใดๆ อันเป็นการทรมาน การทำที่โหดร้าย ไร้มนุษยธรรม หรือย่ำยีศักดิ์ศรีความเป็นมนุษย์"
                          "หรือกระทำให้บุคคลสูญหายแต่อย่างใด")
        
        doc.add_paragraph(f"เจ้าหน้าที่ผู้จับกุม ได้แจ้งข้อมูลเกี่ยวกับผู้ถูกควบคุมตัว ตามมาตรา ๒๒ วรรคสอง แห่ง พ.ร.บ.ป้องกันและปราบปราม"
                          f"การทรมานและการกระทำให้สูญหาย พ.ศ.๒๕๖๕ ไปยัง ศูนย์ป้องกันปราบปรามทรมานและการทำให้บุคคลสูญหาย"
                          f"ประจำสำนักงานอัยการจังหวัดภูเก็ต เมื่อวันที่ {notify_date} เวลา {notify_attorney} น. เรียบร้อยแล้ว")
        
        doc.add_paragraph(f"เจ้าหน้าที่ผู้จับกุม ได้แจ้งข้อมูลเกี่ยวกับผู้ถูกควบคุมตัว ตามมาตรา ๒๒ วรรคสอง แห่ง พ.ร.บ.ป้องกันและปราบปราม"
                          f"การทรมานและการกระทำให้สูญหาย พ.ศ.๒๕๖๕ ไปยังนายอำเภอเมือง จังหวัดภูเก็ตเป็นผู้รับแจ้งการควบคุมตัว "
                          f"เมื่อวันที่ {notify_date} เวลา {notify_district} น. เรียบร้อยแล้ว\n")
        
        doc.add_paragraph("รับรองว่าข้อความตามบันทึกการจับกุมนี้ถูกต้องตามความเป็นจริงทุกประการ จึงให้ลงลายมือชื่อไว้เป็นหลักฐาน "
                          "นำตัวพร้อมบันทึกจับกุม ส่งพนักงานสอบสวน เพื่อดำเนินการตามกฎหมายต่อไป\n\n")
        
        # ---------------------------------------------------------
        # ส่วนสร้างช่องลายเซ็นอัตโนมัติ (ดึงจากกล่องเจ้าหน้าที่)
        # ---------------------------------------------------------
        p_sign1 = doc.add_paragraph()
        p_sign1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sign1.add_run(f"(ลงชื่อ)........................................................................ ผู้ถูกจับ/รับสำเนาบันทึกการจับ\n({suspect_name})\n\n")
        
        # แยกรายชื่อชุดจับกุมด้วยลูกน้ำ (,) หรือการขึ้นบรรทัดใหม่ (\n)
        raw_officers = officers.replace('\n', ',').replace('และ', ',').split(',')
        officer_list = [o.strip() for o in raw_officers if o.strip()]
        
        if len(officer_list) > 0:
            # คนแรกให้เป็นหัวหน้าชุด
            p_head = doc.add_paragraph()
            p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_head.add_run(f"(ลงชื่อ)........................................................................ หัวหน้าชุดจับกุม\n({officer_list[0]})\n\n")
            
            # คนต่อๆ ไป ให้เป็นร่วมจับกุม
            for off in officer_list[1:]:
                p_co = doc.add_paragraph()
                p_co.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_co.add_run(f"(ลงชื่อ)........................................................................ ร่วมจับกุม\n({off})\n\n")
        else:
            # กรณีไม่ได้กรอกชื่อมาเลย ให้สร้างบรรทัดเปล่าเผื่อไว้
            p_blank = doc.add_paragraph()
            p_blank.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_blank.add_run("(ลงชื่อ)........................................................................ หัวหน้าชุดจับกุม\n\n")
            p_blank.add_run("(ลงชื่อ)........................................................................ ร่วมจับกุม\n\n")
        
        # บรรทัดผู้บันทึก
        p_reader = doc.add_paragraph()
        p_reader.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_reader.add_run("(ลงชื่อ)........................................................................ ผู้บันทึก/อ่าน\n")
        
        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()

    word_file = create_word_doc()
    st.download_button(
        label="📥 ดาวน์โหลดไฟล์ Word",
        data=word_file,
        file_name=f"บันทึกจับกุม_{suspect_name}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

# กล่องแสดงตัวอย่าง (Preview)
if st.session_state.get('show_preview'):
    evidence_html = evidence.replace('\n', '<br>')
    behavior_html = behavior_input.replace('\n', '<br>')
    
    st.markdown("---")
    st.markdown("### 📋 ตัวอย่างบันทึกจับกุม (อ้างอิงจากข้อมูลที่ท่านกรอก)")
    preview_text = f"""
<div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px; color: black; font-size: 16px;">
    <h3 style="text-align: center;">บันทึกการจับกุม</h3>
    <p><b>สถานที่ทำบันทึก:</b> {report_loc}</p>
    <p><b>วัน/เดือน/ปี ที่บันทึก:</b> {report_date}</p>
    <p><b>วัน/เดือน/ปี ที่จับกุม:</b> {arrest_date}</p>
    <p><b>สถานที่เกิดเหตุ/จับกุม:</b> {arrest_loc}</p>
    <br>
    <p><b>นามเจ้าพนักงานผู้จับภายใต้การอำนวยการของ</b> {commanders}</p>
    <p><b>เจ้าหน้าที่ตำรวจชุดจับกุม ได้แก่</b> {officers}</p>
    <br>
    <p><b>ได้ร่วมกันจับกุมตัวผู้ต้องหา คือ</b> {suspect_name} อายุ {suspect_age} ปี สัญชาติ {suspect_nationality} เลขประจำตัว {suspect_id} ที่อยู่ {suspect_address}</p>
    <p><b>พร้อมด้วยของกลาง:</b><br>{evidence_html}</p>
    <p><b>โดยกล่าวหาว่า:</b> “{charge_input}”</p>
    <br>
    <p><b>พฤติการณ์ในการจับกุม กล่าวคือ</b> {behavior_html}</p>
    <p><b>ในชั้นจับกุม</b> {suspect_statement}</p>
</div>
    """
    st.markdown(preview_text, unsafe_allow_html=True)
