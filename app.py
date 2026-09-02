import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai

# 1. पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

# 2. कॉम्पैक्ट और कीपैड-फ़्रेंडली CSS
st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.5rem 4rem 0.5rem; max-width: 100%; }
    header, footer, #MainMenu { visibility: hidden; }
    .stChatFloatingInputContainer { bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# 3. इमेज लोड
def get_khushi_img():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return ""

khushi_img = get_khushi_img()

# 4. API और पर्सोना
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान और सच्ची AI दोस्त। समय (IST): {ist_now}। शेयर बाजार, कोडिंग, विज्ञान और सामान्य बातों का संक्षिप्त व स्पष्ट हिंदी में उत्तर दो।"

# मेमोरी
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

if "cam_open" not in st.session_state: st.session_state.cam_open = False
if "settings_open" not in st.session_state: st.session_state.settings_open = False

# 5. स्केच के अनुसार टॉप लेआउट (बायाँ: वीडियो + Puss/Zoom | दायाँ: कैमरा, माइक-स्पीकर, सेटिंग)
col_left, col_right = st.columns([1, 1])

with col_left:
    # Talking Khushi Video Box
    st.components.v1.html(f"""
    <div id="vidBox" style="width:100%; height:190px; background:#0c0d18; border-radius:12px; border:2px solid #ff4b4b; overflow:hidden; position:relative; display:flex; align-items:center; justify-content:center; box-shadow:0 0 15px rgba(255,75,75,0.3); transition:0.3s;">
        <img id="avatarImg" src="{khushi_img}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%; animation:breathe 4s infinite ease-in-out;" />
        <div id="wave" style="position:absolute; bottom:0; left:0; width:100%; height:25px; background:linear-gradient(transparent, rgba(0,0,0,0.85)); display:none; align-items:flex-end; justify-content:center; gap:3px; padding-bottom:3px;">
            <div style="width:3px; height:12px; background:#00ff80;"></div>
            <div style="width:3px; height:18px; background:#00ff80;"></div>
            <div style="width:3px; height:10px; background:#00ff80;"></div>
        </div>
    </div>
    <style>
        @keyframes breathe {{ 0%{{transform:scale(1);}} 50%{{transform:scale(1.03) translateY(-1px);}} 100%{{transform:scale(1);}} }}
        .zoomed {{ position:fixed !important; top:0 !important; left:0 !important; width:100vw !important; height:90vh !important; z-index:999999 !important; border-radius:0 !important; }}
    </style>
    <script>
        window.addEventListener('message', (e) => {{
            const box = document.getElementById('vidBox');
            const wave = document.getElementById('wave');
            if (e.data.type === 'START') {{ box.style.borderColor='#00ff80'; wave.style.display='flex'; }}
            if (e.data.type === 'STOP') {{ box.style.borderColor='#ff4b4b'; wave.style.display='none'; }}
            if (e.data.type === 'ZOOM') {{ box.classList.toggle('zoomed'); }}
            if (e.data.type === 'PUSS') {{ window.speechSynthesis.cancel(); box.style.borderColor='#ff4b4b'; wave.style.display='none'; }}
        }});
    </script>
    """, height=195)

    # Puss और Zoom बटन (ठीक वीडियो के नीचे)
    c_puss, c_zoom = st.columns(2)
    with c_puss:
        if st.button("🛑 Puss (रोकें)", use_container_width=True):
            st.components.v1.html("<script>window.parent.postMessage({type:'PUSS'},'*');</script>", height=0)
    with c_zoom:
        if st.button("⛶ Zoom", use_container_width=True):
            st.components.v1.html("<script>window.parent.postMessage({type:'ZOOM'},'*');</script>", height=0)

with col_right:
    # 1. कैमरा on - off बटन
    cam_label = "📷 कैमरा (ON)" if st.session_state.cam_open else "📷 कैमरा (OFF)"
    if st.button(cam_label, use_container_width=True):
        st.session_state.cam_open = not st.session_state.cam_open
        st.rerun()

    # 2. Mike - Spiker (बोलने के लिए)
    st.components.v1.html("""
    <button id="micBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:10px 4px; border-radius:10px; font-weight:bold; font-size:13px; cursor:pointer; margin-top:2px; box-shadow:0 3px 10px rgba(255,75,75,0.3);">
        🎙️ mike - spiker (बोलें)
    </button>
    <p id="st" style="font-size:11px; color:#888; text-align:center; margin:3px 0 0 0;">टैप करके बोलें...</p>
    <script>
        const btn = document.getElementById('micBtn');
        const st = document.getElementById('st');
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SR) {
            const rec = new SR();
            rec.lang = 'hi-IN';
            btn.onclick = () => {
                if ('speechSynthesis' in window) window.speechSynthesis.speak(new SpeechSynthesisUtterance(""));
                rec.start();
                st.innerText = "सुन रही हूँ...";
                btn.style.background = "#00cc66";
            };
            rec.onresult = (e) => {
                const text = e.results[0][0].transcript;
                st.innerText = "भेजा: " + text;
                btn.style.background = "#ff4b4b";
                const inp = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (inp) {
                    const setVal = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    setVal.call(inp, text);
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(() => {
                        const send = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                        if (send) send.click();
                    }, 300);
                }
            };
            rec.onerror = () => { btn.style.background = "#ff4b4b"; st.innerText = "माइक एरर"; };
        }
    </script>
    """, height=65)

    # 3. सेटिंग बटन
    if st.button("⚙️ सेटिंग", use_container_width=True):
        st.session_state.settings_open = not st.session_state.settings_open
        st.rerun()

# ऑन-डिमांड कैमरा (केवल ऑन होने पर दिखेगा)
active_image = None
if st.session_state.cam_open:
    st.info("📷 कैमरा व इमेज स्कैनर एक्टिव:")
    c1, c2 = st.columns(2)
    with c1: cam_shot = st.camera_input("फोटो खींचें", label_visibility="collapsed")
    with c2: file_doc = st.file_uploader("चार्ट अपलोड", type=["jpg", "png"], label_visibility="collapsed")
    active_image = cam_shot if cam_shot else file_doc

# ऑन-डिमांड सेटिंग
if st.session_state.settings_open:
    if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
        st.session_state.messages = []
        save_mem()
        st.session_state.settings_open = False
        st.rerun()

# 6. मिडिल सेक्शन: (चैट बाट) और 👉 खुशी Answer
st.markdown("---")
for msg in st.session_state.messages[-2:]:
    if msg["role"] == "user":
        st.markdown(f"**🗣️ आप:** {msg['content']}")
    else:
        st.markdown(f"""
        <div style="background:#131528; border:1px solid #00ff80; border-radius:12px; padding:12px 14px; margin:6px 0; box-shadow:0 3px 12px rgba(0,255,128,0.15);">
            <strong style="color:#00ff80;">👉 खुशी Answer:</strong><br>
            <span style="color:#e2e8f0; font-size:14px; line-height:1.5;">{msg['content']}</span>
        </div>
        """, unsafe_allow_html=True)

# 7. Gemini इंजन (सटीक उत्तर व फॉलबैक)
def ask_gemini(prompt, img_file):
    models = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.0-flash']
    content = [prompt, Image.open(img_file)] if img_file else prompt
    for m in models:
        try:
            res = client.models.generate_content(model=m, contents=content)
            if res and res.text: return res.text
        except Exception: continue
    return "माफ़ कीजिए, अभी सर्वर व्यस्त है। कृपया पुनः पूछें।"

def speak_out(text):
    clean_txt = re.sub(r'[*#~`_+=|\\<>]', ' ', text).replace('"', '').replace("'", "")
    st.components.v1.html(f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance("{clean_txt}");
            u.lang = 'hi-IN';
            u.onstart = () => {{ window.parent.postMessage({{type:'START'}},'*'); }};
            u.onend = () => {{ window.parent.postMessage({{type:'STOP'}},'*'); }};
            u.onerror = () => {{ window.parent.postMessage({{type:'STOP'}},'*'); }};
            window.speechSynthesis.speak(u);
        }}
    </script>
    """, height=0)

# 8. निचला इनपुट (Key-Ped के लिए जगह)
user_q = st.chat_input("यहाँ लिखें या mike बटन दबाकर बोलें...")

if user_q or (active_image and st.button("🔍 विश्लेषण करें")):
    q = user_q if user_q else "इस तस्वीर का विश्लेषण करें।"
    st.session_state.messages.append({"role": "user", "content": q})
    
    with st.spinner("खुशी सोच रही है... ✨"):
        ans = ask_gemini(q, active_image)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        speak_out(ans)
        st.rerun()
