import streamlit as st
import google.generativeai as genai

# ==========================================
# 🔑 ส่วนตั้งค่าระบบ (พี่ต้องเอา API Key มาใส่ตรงนี้)
# ==========================================
# ลบคำว่า ใส่_API_KEY_ที่นี่ แล้วเอาคีย์ของพี่มาวางแทน (อย่าลบเครื่องหมาย " " ออกนะครับ)
API_KEY = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="ระบบบันทึกจับกุมอัจฉริยะ", layout="wide")

# ==========================================
# 🎨 ส่วนหน้าตาเว็บ (UI)
# ==========================================
st.title("🚓 ระบบสร้างบันทึกจับกุม (ฝ่ายสืบสวน)")
st.caption("กรอกข้อมูลเบื้องต้น แล้วให้ AI ช่วยร่างพฤติการณ์จับกุมที่สละสลวย")

# --- ส่วนที่ 1: ข้อมูลการจับกุม ---
st.subheader("📌 1. ข้อมูลการจับกุม")
col1, col2 = st.columns(2)
with col1:
    arrest_date = st.text_input("วันเวลาจับกุม", placeholder="เช่น 1 มี.ค. 2569 เวลา 14.00 น.")
    arrest_loc = st.text_area("สถานที่จับกุม", placeholder="เช่น ถ.ภูเก็ต ต.ตลาดใหญ่ อ.เมือง จ.ภูเก็ต")
    officers = st.text_area("ชื่อและยศ ชุดจับกุม", placeholder="พ.ต.ท. ..., ร.ต.อ. ...")

with col2:
    report_date = st.text_input("วันเวลาที่ทำบันทึก", placeholder="เช่น 1 มี.ค. 2569 เวลา 16.00 น.")
    report_loc = st.text_input("สถานที่ทำบันทึก", placeholder="เช่น กก.สส.ภ.จว.ภูเก็ต หรือ สภ.เมืองภูเก็ต")
    charge_input = st.text_input("ข้อหา", placeholder="กรอกเอง หรือเว้นไว้ให้ AI แนะนำได้")

# --- ส่วนที่ 2: ข้อมูลผู้ต้องหา ---
st.divider()
st.subheader("👤 2. ข้อมูลผู้ต้องหา")
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    suspect_name = st.text_input("ชื่อ-นามสกุล ผู้ต้องหา")
    suspect_address = st.text_area("ที่อยู่ตามบัตรประชาชน")
with c2:
    suspect_id = st.text_input("เลขบัตรประชาชน")
    suspect_phone = st.text_input("เบอร์โทรศัพท์")
with c3:
    suspect_age = st.text_input("อายุ")

# --- ส่วนที่ 3: ของกลางและพฤติการณ์ ---
st.divider()
st.subheader("📦 3. ของกลางและพฤติการณ์")
evidence = st.text_area("ของกลางที่ตรวจยึด", placeholder="1. ...\n2. ...")
st.info("💡 ทริค: ช่องพฤติการณ์ด้านล่างนี้ พี่สามารถพิมพ์เล่าเหตุการณ์เป็นภาษาพูดคร่าวๆ ได้เลย แล้วเดี๋ยวกดให้ AI ช่วยเกลาเป็นภาษากฎหมายให้ครับ หรือถ้าพี่มีรูปแบบการทำรายงานที่ถนัดอยู่แล้ว ก็พิมพ์ลงไปตรงๆ ได้เลย")
behavior_input = st.text_area("พฤติการณ์การจับกุม (ร่างคร่าวๆ)", height=150)

# ==========================================
# ⚙️ ส่วนปุ่มกดและการทำงานของ AI
# ==========================================
st.divider()
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("🤖 1. ให้ AI ช่วยเกลาพฤติการณ์และแนะนำข้อหา", use_container_width=True):
        if API_KEY == "ใส่_API_KEY_ที่นี่":
            st.error("⚠️ พี่ลืมใส่ API KEY ในโค้ดบรรทัดที่ 8 ครับ!")
        elif not behavior_input:
            st.warning("⚠️ กรุณาพิมพ์พฤติการณ์คร่าวๆ ก่อนครับ AI จะได้มีข้อมูลไปแต่งเรื่อง")
        else:
            try:
                genai.configure(api_key=API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                คุณคือตำรวจฝ่ายสืบสวนที่เชี่ยวชาญการเขียนบันทึกจับกุมและกฎหมายอาญาไทย 
                จงนำข้อมูลต่อไปนี้มาเรียบเรียงเป็น 'พฤติการณ์การจับกุม' ให้สละสลวย รัดกุม เป็นทางการ และแนะนำ 'ข้อหา' 
                
                ข้อมูล:
                - วันเวลา/สถานที่จับกุม: {arrest_date} ณ {arrest_loc}
                - ของกลาง: {evidence}
                - เหตุการณ์คร่าวๆ: {behavior_input}
                
                ตอบกลับมาโดยแบ่งเป็น 2 หัวข้อคือ:
                **ข้อหาที่แนะนำ:**
                (ระบุข้อหา)
                
                **พฤติการณ์แห่งการจับกุมที่เกลาแล้ว:**
                (ระบุพฤติการณ์)
                """
                
                with st.spinner('กำลังใช้ AI วิเคราะห์และเรียบเรียง...'):
                    response = model.generate_content(prompt)
                    st.session_state['ai_result'] = response.text
                    st.success("✅ AI เรียบเรียงเสร็จแล้ว! ดูผลลัพธ์ด้านล่างได้เลยครับ")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")

# แสดงผลที่ AI คิดให้
if 'ai_result' in st.session_state:
    st.markdown("---")
    st.markdown("### ✨ ผลลัพธ์จาก AI")
    st.info(st.session_state['ai_result'])

with col_btn2:
    if st.button("📄 2. ดูตัวอย่างร่างบันทึกจับกุมฉบับสมบูรณ์", use_container_width=True):
        st.success("🎉 คัดลอกข้อความด้านล่างนี้ไปวางใน Word ได้เลยครับ!")
        
        report_template = f"""
**บันทึกการจับกุม**

ทำที่: {report_loc}
วันเวลาที่ทำบันทึก: {report_date}

ด้วยวันนี้ เมื่อเวลาประมาณ {arrest_date} เจ้าหน้าที่ตำรวจประกอบด้วย {officers}
ได้ร่วมกันทำการจับกุมตัว {suspect_name} อายุ {suspect_age} ปี 
เลขประจำตัวประชาชน {suspect_id}
ที่อยู่: {suspect_address} 
เบอร์โทรศัพท์: {suspect_phone}

สถานที่จับกุม: {arrest_loc}
พร้อมด้วยของกลาง: {evidence}
โดยกล่าวหาว่า: {charge_input}

**พฤติการณ์แห่งการจับกุม:**
{behavior_input}
        """
        st.markdown(report_template)