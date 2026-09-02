import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. पेज कॉन्फ़िगरेशन (डिज़ाइन 100% फ्रोज़न)
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.4rem 4rem 0.4rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
    
    /* 52% - 48% ग्रिड और बटनों की सटीक स्टाइलिंग */
    div[data-testid="column"] {
        padding: 2px !important;
    }
    
    div.stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        padding: 8px 2px !important;
        font-size: 12px !important;
        border: 1px solid transparent !important;
        transition: all 0.2s ease !important;
    }
    
    .thinking-badge {
        background: linear-gradient(90deg, rgba(0,255,128,0.2), rgba(56,189,248,0.2));
        border: 1px solid #00ff80;
        border-radius: 20px;
        padding: 6px 14px;
        color: #00ff80;
        font-size: 12px;
        font-weight: bold;
        text-align: center;
        margin: 6px 0;
        animation: pulseBadge 1.2s infinite alternate ease-in-out;
    }
    @keyframes pulseBadge {
        0% { opacity: 0.6; }
        100% { opacity: 1; box-shadow: 0 0 14px rgba(0,255,128,0.7); }
    }
    @keyframes breathe { 0%{transform:scale(1);} 50%{transform:scale(1.02) translateY(-1px);} 100%{transform:scale(1);} }
</style>
""", unsafe_allow_html=True)

# 2. खुशी मीडिया (MP4 या फ़ोटो)
def get_khushi_assets():
    has_vid = os.path.exists("khushi.mp4")
    v_b64 = ""
    img_b64 = ""
    if has_vid:
        try:
            with open("khushi.mp4", "rb") as f:
                v_b64 = f"data:video/mp4;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                img_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return has_vid, v_b64, img_b64

has_vid, khushi_video, khushi_img = get_khushi_assets()
media_src = khushi_video if has_vid else khushi_img

# 3. Gemini 3.6 Flash Client
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो विनम्र, हमदर्द, बुद्धिमान, कोडिंग एक्सपर्ट, ईमानदार और सच्ची AI दोस्त। समय (IST): {ist_now}। बिल्कुल संक्षिप्त, सरल और सजीव हिंदी में 2 पंक्तियों में तुरंत उत्तर दो।"

# 4. स्टेट मैनेजमेंट
if "messages" not in st.session_state:
    if os.path.exists("khushi_memory.json"):
        try:
            with open("khushi_memory.json", "r", encoding="utf-8") as f:
                st.session_state.messages = json.load(f)
        except Exception: st.session_state.messages = []
    else: st.session_state.messages = []

def save_mem():
    try:
        with open("khushi_memory.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False)
    except Exception: pass

if "cam_on" not in st.session_state: st.session_state.cam_on = False
if "is_zoom" not in st.session_state: st.session_state.is_zoom = False
if "voice_active" not in st.session_state: st.session_state.voice_active = False

# अंतिम उत्तर जो बोलना है
last_answer = ""
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_answer = st.session_state.messages[-1]["content"]
clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', last_answer).replace('"', ' ').replace("'", " ").strip()

# 5. मुख्य फ्रोज़न लेआउट (52% बायाँ और 48% दायाँ)
if st.session_state.is_zoom:
    # 1:1 स्क्वायर ज़ूम सिनेमाई डिस्प्ले
    st.markdown(f"""
    <div style="width:100%; min-height:85vh; background:#070913; border-radius:8px; border:2px solid #00ff80; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:15px; box-sizing:border-box;">
        <div style="width:280px; height:370px; border-radius:8px; overflow:hidden; border:2px solid #00ff80; box-shadow:0 0 15px rgba(0,255,128,0.4); margin-bottom:10px;">
            {'<video src="' + media_src + '" autoplay loop muted playsinline style="width:100%; height:100%; object-fit:cover;"></video>' if has_vid else '<img src="' + media_src + '" style="width:100%; height:100%; object-fit:cover;" />'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_z1, col_z2 = st.columns(2)
    with col_z1:
        if st.button("✕ सामान्य डिस्प्ले", key="btn_exit_zoom"):
            st.session_state.is_zoom = False
            st.rerun()
    with col_z2:
        if st.button("🛑 Puss (रोकें)", key="btn_puss_zoom"):
            clean_speak = ""
            st.rerun()

else:
    # सामान्य 52% - 48% स्प्लिट-स्क्रीन
    master_col_left, master_col_right = st.columns([52, 48])
    
    with master_col_left:
        # बायाँ 52% फ्रेम (खुशी की इमेज/वीडियो)
        st.markdown(f"""
        <div style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35);">
            {'<video src="' + media_src + '" autoplay loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 12%;"></video>' if has_vid else '<img src="' + media_src + '" style="width:100%; height:100%; object-fit:cover; object-position:center 12%; animation:breathe 4s infinite ease-in-out;" />'}
        </div>
        """, unsafe_allow_html=True)
        
        # संशोधन 1: Puss और Zoom दोनों इमेज के ठीक नीचे एक साथ पास-पास
        col_bl, col_br = st.columns(2)
        with col_bl:
            if st.button("🛑 Puss", key="btn_puss"):
                clean_speak = ""
                st.rerun()
        with col_br:
            if st.button("⛶ Zoom", key="btn_zoom"):
                st.session_state.is_zoom = True
                st.rerun()

    with master_col_right:
        # संशोधन 2: माइक-स्पीकर वाली red बटन को कैमरा के ऊपर (शीर्ष पर, Zoom और Puss के पास) ले आया गया
        st.components.v1.html("""
        <div style="text-align:center;">
            <button id="nativeMic" style="width:100%; background:#ff4b4b; color:white; border:none; padding:12px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                🎙️ mike - spiker (बोलें)
            </button>
            <span id="mStatus" style="font-size:10px; color:#9ca3af; display:block; margin-top:3px;">माइक व स्पीकर एक्टिव</span>
        </div>
        <script>
            const btn = document.getElementById('nativeMic');
            const stTxt = document.getElementById('mStatus');
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition || (window.parent && (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition));
            let rec = SR ? new SR() : null;
            if (rec) {
                rec.lang = 'hi-IN';
                btn.onclick = () => {
                    try { rec.start(); stTxt.innerText = "सुन रही हूँ... बोलिए 🎙️"; btn.style.background = "#10b981"; }
                    catch(e) { rec.stop(); setTimeout(() => rec.start(), 150); }
                };
                rec.onresult = (e) => {
                    const text = e.results[0][0].transcript;
                    stTxt.innerText = "भेजा: " + text;
                    btn.style.background = "#ff4b4b";
                    const pDoc = window.parent.document;
                    const inp = pDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (inp) {
                        const nativeVal = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                        nativeVal.call(inp, text);
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        setTimeout(() => {
                            const send = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                            if (send) send.click();
                        }, 200);
                    }
                };
                rec.onerror = () => { btn.style.background = "#ff4b4b"; stTxt.innerText = "माइक एरर"; };
                rec.onend = () => { btn.style.background = "#ff4b4b"; };
            } else {
                stTxt.innerText = "नीचे टाइप बार प्रयोग करें";
            }
        </script>
        """, height=65)

        # 2. कैमरा ऑन-ऑफ बटन (माइक के नीचे)
        cam_text = "📷 कैमरा on — off" if not st.session_state.cam_on else "📷 कैमरा (LIVE ON)"
        if st.button(cam_text, key="btn_cam_toggle"):
            st.session_state.cam_on = not st.session_state.cam_on
            st.rerun()
            
        # 3. बीच का बॉक्स: इन-प्लेस कैमरा
        if st.session_state.cam_on:
            st.camera_input("लाइव कैमरा", label_visibility="collapsed", key="in_cam")
        else:
            st.markdown("""
            <div style="width:100%; height:88px; background:#07080f; border-radius:10px; border:1px dashed #2e3856; display:flex; align-items:center; justify-content:center;">
                <span style="color:#555f7d; font-size:11px;">कैमरा स्टैंडबाय (OFF)</span>
            </div>
            """, unsafe_allow_html=True)
        
        # 4. इनलाइन कॉम्पैक्ट सेटिंग्स
        st.markdown("""
        <div style="width:100%; background:#131526; border:1px solid #7c3aed; border-radius:10px; padding:4px; margin-top:2px;">
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0 2px;">
                <span style="color:#c084fc; font-size:10.5px; font-weight:bold;">⚙️ सेटिंग</span>
                <span style="color:#10b981; font-size:9px;">● 3.6 Flash</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🗑️ मेमोरी साफ़ करें", key="btn_clear_mem"):
            st.session_state.messages = []
            save_mem()
            st.success("मेमोरी रीसेट हो गई!")
            st.rerun()

# 6. ऑटो-स्पीच (खुशी की आवाज़ बिना रोक-टोक)
if clean_speak:
    st.components.v1.html(f"""
    <script>
        try {{
            const win = window.parent || window;
            if ('speechSynthesis' in win) {{
                win.speechSynthesis.cancel();
                const u = new win.SpeechSynthesisUtterance("{clean_speak}");
                u.lang = 'hi-IN';
                u.rate = 1.0;
                win.speechSynthesis.speak(u);
            }}
        }} catch(e) {{}}
    </script>
    """, height=0)

# 7. स्टेटस व चैट संवाद
thinking_box = st.empty()

st.markdown('<div id="chatAnswerContainer">', unsafe_allow_html=True)
for msg in st.session_state.messages[-2:]:
    if msg["role"] == "user":
        st.markdown(f"🗣️ **आप (Q):** {msg['content']}")
    else:
        st.markdown(f"""
        <div style="background:#09101d; border:1.5px solid #00ff80; border-radius:10px; padding:10px 12px; margin:4px 0; box-shadow:0 2px 10px rgba(0,255,128,0.12);">
            <b style="color:#00ff80; font-size:14px;">👉 खुशी Answer:</b><br>
            <span style="color:#f8fafc; font-size:13px; line-height:1.4;">{msg['content']}</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 8. Gemini 3.6 Flash इंजन
def ask_gemini(prompt):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    try:
        res = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=PERSONA)
        )
        if res and res.text:
            return res.text
    except Exception as e:
        return f"सर्वर व्यस्त है: {str(e)[:40]}"
    return "माफ़ कीजिए, उत्तर नहीं मिला।"

# 9. चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    thinking_box.markdown('<div class="thinking-badge">✨ खुशी सोच रही है... उत्तर आ रहा है ⚡</div>', unsafe_allow_html=True)
    
    ans = ask_gemini(user_query)
    st.session_state.messages.append({"role": "assistant", "content": ans})
    save_mem()
    
    thinking_box.empty()
    st.rerun()
