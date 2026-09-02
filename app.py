import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.4rem 4.5rem 0.4rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
    
    /* कस्टम बटन स्टाइलिंग जो आपकी वर्तमान पसंदीदा थीम से 100% मेल खाती है */
    div.stButton > button {
        width: 100% !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 12px !important;
        padding: 12px 2px !important;
        border: 1px solid transparent !important;
    }
    
    /* मोबाइल 2-कॉलम लॉक */
    div[data-testid="column"] {
        min-width: 47% !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. खुशी ओरिजिनल इमेज (Base64)
def get_khushi_b64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return ""

khushi_b64 = get_khushi_b64()

# 3. Gemini 3.6 Flash Client
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान और सच्ची AI दोस्त। समय (IST): {ist_now}। शेयर बाजार, कोडिंग, विज्ञान और सामान्य प्रश्नों के सरल, संक्षिप्त व स्पष्ट हिंदी में उत्तर दो।"

# सेशन स्टेट प्रबंधन
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

if "show_cam" not in st.session_state:
    st.session_state.show_cam = False
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

# 4. मुख्य हेडर लेआउट (पसंदीदा डिज़ाइन: बायाँ 52% पोर्ट्रेट + दायाँ 48% कंट्रोल्स)
col_left, col_right = st.columns([52, 48])

with col_left:
    # पोर्ट्रेट डिस्प्ले + स्क्वायर ज़ूम + Puss / Zoom बटन्स
    st.components.v1.html(f"""
    <div id="portraitWrap" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35);">
        <img id="avatarImg" src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 12%; animation:breathe 4s infinite ease-in-out;" />
    </div>

    <!-- Puss और Zoom बटन -->
    <div style="display:flex; gap:6px; margin-top:6px;">
        <button onclick="doPuss()" style="flex:1; background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:10px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
            🛑 Puss
        </button>
        <button onclick="doZoom()" id="zoomBtn" style="flex:1; background:#12283d; color:#38bdf8; border:1px solid #38bdf8; padding:10px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
            ⛶ Zoom
        </button>
    </div>

    <!-- 1:1 स्क्वायर ज़ूम सिनेमाई डिस्प्ले -->
    <div id="squareZoomModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:#000; z-index:999999; flex-direction:column; align-items:center; justify-content:center;">
        <button onclick="doZoom()" style="position:absolute; top:15px; right:15px; background:#ff4b4b; color:#fff; border:none; padding:10px 18px; border-radius:25px; font-size:13px; font-weight:bold; cursor:pointer;">
            ✕ सामान्य डिस्प्ले
        </button>
        <div style="width:90vw; max-width:390px; height:90vw; max-height:390px; border:2px solid #00ff80; border-radius:14px; overflow:hidden; box-shadow:0 0 30px rgba(0,255,128,0.5);">
            <img src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />
        </div>
        <div style="margin-top:20px; display:flex; gap:12px; width:90vw; max-width:390px; justify-content:center;">
            <button onclick="doPuss()" style="background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:12px 18px; border-radius:25px; font-weight:bold; font-size:13px; cursor:pointer;">
                🛑 Puss
            </button>
            <button onclick="triggerParentMic()" style="flex:1; background:linear-gradient(90deg, #10b981, #059669); color:#fff; border:none; padding:12px 16px; border-radius:25px; font-weight:bold; font-size:13.5px; cursor:pointer;">
                🎙️ बोलिए (माइक व स्पीकर चालू)
            </button>
        </div>
    </div>

    <style>
        @keyframes breathe {{ 0%{{transform:scale(1);}} 50%{{transform:scale(1.025) translateY(-1.5px);}} 100%{{transform:scale(1);}} }}
    </style>
    <script>
        let isZoom = false;
        function doZoom() {{
            isZoom = !isZoom;
            document.getElementById('squareZoomModal').style.display = isZoom ? 'flex' : 'none';
        }}
        function doPuss() {{
            try {{
                window.speechSynthesis.cancel();
                if (window.parent && window.parent.speechSynthesis) {{
                    window.parent.speechSynthesis.cancel();
                }}
            }} catch(e) {{}}
        }}
        function triggerParentMic() {{
            const micBtn = window.parent.document.getElementById('nativeMicBtn');
            if (micBtn) micBtn.click();
        }}
    </script>
    """, height=365)

with col_right:
    # 1. कैमरा ON - OFF बटन (100% वर्किंग)
    cam_color = "#facc15" if not st.session_state.show_cam else "#ef4444"
    cam_text = "📷 कैमरा on — off" if not st.session_state.show_cam else "📷 कैमरा बंद करें"
    if st.button(cam_text, key="btn_cam_toggle"):
        st.session_state.show_cam = not st.session_state.show_cam
        st.session_state.show_settings = False
        st.rerun()

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # 2. mike - spiker (बोलने के लिए) (100% वर्किंग)
    st.components.v1.html("""
    <div style="text-align:center; padding: 2px;">
        <button id="nativeMicBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:15px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45); transition:0.2s;">
            🎙️ mike - spiker (बोलें)
        </button>
        <span id="stMsg" style="font-size:10px; color:#9ca3af; display:block; margin-top:4px;">माइक व स्पीकर एक्टिव</span>
    </div>
    <script>
        const btn = document.getElementById('nativeMicBtn');
        const stMsg = document.getElementById('stMsg');
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition || (window.parent && (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition));
        
        if (SR) {
            const rec = new SR();
            rec.lang = 'hi-IN';
            rec.continuous = false;
            rec.interimResults = false;

            btn.onclick = () => {
                try {
                    const u = new SpeechSynthesisUtterance("");
                    window.speechSynthesis.speak(u);
                    if (window.parent && window.parent.speechSynthesis) window.parent.speechSynthesis.speak(u);
                } catch(e) {}
                
                try {
                    rec.start();
                    stMsg.innerText = "सुन रही हूँ... बोलिए 🎙️";
                    btn.style.background = "#10b981";
                } catch(e) {
                    rec.stop();
                    setTimeout(() => rec.start(), 200);
                }
            };

            rec.onresult = (e) => {
                const text = e.results[0][0].transcript;
                stMsg.innerText = "भेजा: " + text;
                btn.style.background = "#ff4b4b";

                const inp = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (inp) {
                    const setNative = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    setNative.call(inp, text);
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(() => {
                        const send = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                        if (send) send.click();
                    }, 300);
                }
            };

            rec.onerror = () => {
                btn.style.background = "#ff4b4b";
                stMsg.innerText = "माइक एरर या परमिशन दें";
            };

            rec.onend = () => {
                btn.style.background = "#ff4b4b";
            };
        } else {
            stMsg.innerText = "ब्राउज़र में वॉयस सपोर्ट नहीं है";
        }
    </script>
    """, height=75)

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # 3. सेटिंग बटन (100% वर्किंग)
    if st.button("⚙️ सेटिंग", key="btn_settings_toggle"):
        st.session_state.show_settings = not st.session_state.show_settings
        st.session_state.show_cam = False
        st.rerun()

# 5. शुद्ध ऑन-डिमांड कैमरा (जब तक 'कैमरा on - off' न दबाएँ, तब तक 0% लोड रहेगा)
active_image = None
if st.session_state.show_cam:
    st.markdown('<div style="background:#141724; padding:10px; border-radius:10px; margin:6px 0; border:1px solid #ca8a04;">', unsafe_allow_html=True)
    st.markdown("<span style='color:#facc15; font-size:12px; font-weight:bold;'>📷 कैमरा व स्कैनर एक्टिव है:</span>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1: cam_shot = st.camera_input("फोटो खींचें", label_visibility="collapsed")
    with col_c2: file_doc = st.file_uploader("चार्ट अपलोड", type=["jpg", "png"], label_visibility="collapsed")
    active_image = cam_shot if cam_shot else file_doc
    st.markdown('</div>', unsafe_allow_html=True)

# 6. शुद्ध ऑन-डिमांड सेटिंग्स (जब तक '⚙️ सेटिंग' न दबाएँ, तब तक 0% लोड रहेगा)
if st.session_state.show_settings:
    st.markdown('<div style="background:#181628; padding:12px; border-radius:10px; margin:6px 0; border:1px solid #9333ea;">', unsafe_allow_html=True)
    st.markdown("<b style='color:#c084fc; font-size:13px;'>⚙️ सिस्टम सेटिंग्स व टूल्स:</b>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🗑️ चैट हिस्ट्री साफ़ करें", key="clr_btn"):
            st.session_state.messages = []
            save_mem()
            st.session_state.show_settings = False
            st.success("मेमोरी रीसेट हो गई!")
            st.rerun()
    with col_s2:
        if st.button("✕ सेटिंग्स बंद करें", key="close_set_btn"):
            st.session_state.show_settings = False
            st.rerun()
    st.caption("🟢 एक्टिव AI मॉडल: **Gemini 3.6 Flash**")
    st.markdown('</div>', unsafe_allow_html=True)

# 7. चैट संवाद व उत्तर कार्ड
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

# 8. Gemini 3.6 Flash इंजन
def ask_gemini(prompt, img):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    
    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash']
    contents_payload = [prompt, Image.open(img)] if img else prompt
    
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents_payload,
                config=types.GenerateContentConfig(system_instruction=PERSONA)
            )
            if res and res.text:
                return res.text
        except Exception:
            continue
            
    return "माफ़ कीजिए, सर्वर व्यस्त है। कृपया पुनः प्रयास करें।"

def speak(text):
    clean = re.sub(r'[*#~`_+=|\\<>]', ' ', text).replace('"', '').replace("'", "")
    st.components.v1.html(f"""
    <script>
        try {{
            const win = window.parent || window;
            if ('speechSynthesis' in win) {{
                win.speechSynthesis.cancel();
                const u = new win.SpeechSynthesisUtterance("{clean}");
                u.lang = 'hi-IN';
                u.rate = 0.95;
                win.speechSynthesis.speak(u);
            }}
        }} catch(e) {{}}
    </script>
    """, height=0)

# 9. निचला इनपुट (कीपैड बार)
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query or (active_image and st.button("🔍 इस फ़ोटो का विश्लेषण करें")):
    q = user_query if user_query else "कृपया इस तस्वीर का विश्लेषण करें।"
    st.session_state.messages.append({"role": "user", "content": q})
    
    with st.spinner("खुशी सोच रही है... ✨"):
        ans = ask_gemini(q, active_image)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        speak(ans)
        st.rerun()
        
