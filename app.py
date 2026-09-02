import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai

# 1. पेज कॉन्फ़िगरेशन
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

# 2. मोबाइल पर भी साइड-बाय-साइड (Side-by-Side) लॉक रखने वाला CSS
st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.4rem 4.5rem 0.4rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
    
    /* मोबाइल पर कॉलम्स को एक-दूसरे के नीचे जाने से रोकें */
    div[data-testid="column"] {
        width: 50% !important;
        flex: 1 1 50% !important;
        min-width: 48% !important;
    }
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. खुशी ओरिजिनल इमेज
def get_khushi_b64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return ""

khushi_b64 = get_khushi_b64()

# 4. API Client सेटअप (AQ. और AIza दोनों समर्थित)
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")

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

if "cam_state" not in st.session_state: st.session_state.cam_state = False
if "settings_state" not in st.session_state: st.session_state.settings_state = False

# 5. आपके स्केच के अनुसार टॉप लेआउट (बायाँ: Talking Khushi Video + Puss/Zoom | दायाँ: कैमरा on-off, mike-spiker, सेटिंग)
st.components.v1.html(f"""
<div style="display:flex; width:100%; gap:8px; box-sizing:border-box; background:#0f111e; padding:8px; border-radius:12px; border:1px solid #2d3748;">
    
    <!-- बायाँ हिस्सा: Talking Khushi Video (MP4/विज़न) + Puss/Zoom ठीक नीचे -->
    <div style="width:50%; display:flex; flex-direction:column; gap:5px;">
        <div id="videoContainer" style="width:100%; height:160px; background:#000; border:2px solid #ff4b4b; border-radius:10px; overflow:hidden; position:relative;">
            <img id="avatarPic" src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%; animation:breathe 4s infinite ease-in-out;" />
            <div id="eqWave" style="position:absolute; bottom:0; left:0; width:100%; height:20px; background:rgba(0,0,0,0.7); display:none; align-items:flex-end; justify-content:center; gap:3px;">
                <div style="width:3px; height:8px; background:#00ff80;"></div>
                <div style="width:3px; height:15px; background:#00ff80;"></div>
                <div style="width:3px; height:10px; background:#00ff80;"></div>
            </div>
        </div>
        
        <!-- Puss और Zoom बटन ठीक वीडियो के नीचे -->
        <div style="display:flex; gap:4px; width:100%;">
            <button onclick="pussSpeech()" style="flex:1; background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:7px 2px; border-radius:6px; font-size:11px; font-weight:bold; cursor:pointer;">
                🛑 Puss
            </button>
            <button onclick="toggleZoom()" id="zoomBtn" style="flex:1; background:#12283d; color:#38bdf8; border:1px solid #38bdf8; padding:7px 2px; border-radius:6px; font-size:11px; font-weight:bold; cursor:pointer;">
                ⛶ Zoom
            </button>
        </div>
    </div>

    <!-- दायाँ हिस्सा: कैमरा on-off, mike-spiker (बोलने के लिए), सेटिंग -->
    <div style="width:50%; display:flex; flex-direction:column; justify-content:space-between; gap:5px;">
        <!-- 1. कैमरा on — off -->
        <button onclick="toggleCam()" style="width:100%; background:#262010; color:#facc15; border:1px solid #ca8a04; padding:8px 2px; border-radius:8px; font-size:11px; font-weight:bold; cursor:pointer;">
            📷 कैमरा on — off
        </button>

        <!-- 2. mike - spiker (बोलने के लिए) -->
        <div style="display:flex; flex-direction:column; align-items:center;">
            <button id="micBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:10px 2px; border-radius:8px; font-size:11px; font-weight:bold; cursor:pointer; box-shadow:0 2px 8px rgba(255,75,75,0.4);">
                🎙️ mike - spiker (बोलें)
            </button>
            <span id="micStatus" style="font-size:9px; color:#9ca3af; margin-top:2px;">टैप करके बोलें</span>
        </div>

        <!-- 3. सेटिंग -->
        <button onclick="toggleSettings()" style="width:100%; background:#201830; color:#c084fc; border:1px solid #9333ea; padding:8px 2px; border-radius:8px; font-size:11px; font-weight:bold; cursor:pointer;">
            ⚙️ सेटिंग
        </button>
    </div>
</div>

<style>
    @keyframes breathe {{ 0%{{transform:scale(1);}} 50%{{transform:scale(1.03) translateY(-1px);}} 100%{{transform:scale(1);}} }}
    .zoomed-full {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 94vh !important;
        z-index: 999999 !important;
        border-radius: 0 !important;
    }}
</style>

<script>
    const card = document.getElementById('videoContainer');
    const zoomBtn = document.getElementById('zoomBtn');
    const wave = document.getElementById('waveWave');
    const micBtn = document.getElementById('micBtn');
    const micStatus = document.getElementById('micStatus');

    let isZoomed = false;

    function toggleZoom() {{
        isZoomed = !isZoomed;
        if (isZoomed) {{
            card.classList.add('zoomed-full');
            zoomBtn.innerText = '✕ छोटा';
            zoomBtn.style.background = '#ff4b4b';
            zoomBtn.style.color = '#fff';
        }} else {{
            card.classList.remove('zoomed-full');
            zoomBtn.innerText = '⛶ Zoom';
            zoomBtn.style.background = '#12283d';
            zoomBtn.style.color = '#38bdf8';
        }}
    }}

    function pussSpeech() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
        }}
        card.style.borderColor = '#ff4b4b';
        micStatus.innerText = 'शांत';
    }}

    function toggleCam() {{
        const el = window.parent.document.getElementById('cameraBoxContainer');
        if (el) {{
            el.style.display = (el.style.display === 'none') ? 'block' : 'none';
            el.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    function toggleSettings() {{
        const el = window.parent.document.getElementById('settingsBoxContainer');
        if (el) {{
            el.style.display = (el.style.display === 'none') ? 'block' : 'none';
            el.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // Voice Input Recognition
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {{
        const rec = new SpeechRec();
        rec.lang = 'hi-IN';
        micBtn.onclick = () => {{
            if ('speechSynthesis' in window) window.speechSynthesis.speak(new SpeechSynthesisUtterance(""));
            rec.start();
            micStatus.innerText = "सुन रही हूँ...";
            micBtn.style.background = "#10b981";
        }};
        rec.onresult = (e) => {{
            const text = e.results[0][0].transcript;
            micStatus.innerText = "भेजा: " + text;
            micBtn.style.background = "#ff4b4b";
            const inp = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (inp) {{
                const nativeVal = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                nativeVal.call(inp, text);
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                setTimeout(() => {{
                    const send = window.parent.document.querySelector('button[data-testid="stChatInputSubmitButton"]');
                    if (send) send.click();
                }}, 300);
            }}
        }};
        rec.onerror = () => {{ micBtn.style.background = "#ff4b4b"; micStatus.innerText = "माइक एरर"; }};
    }}
</script>
""", height=220)

# ऑन-डिमांड कैमरा बॉक्स (टॉगल होने पर ही दिखेगा)
active_image = None
st.markdown('<div id="cameraBoxContainer" style="display:none; background:#181824; padding:8px; border-radius:10px; margin:4px 0; border:1px solid #ca8a04;">', unsafe_allow_html=True)
st.markdown("<span style='color:#facc15; font-size:12px; font-weight:bold;'>📷 कैमरा या चार्ट चुनें:</span>", unsafe_allow_html=True)
col_cam1, col_cam2 = st.columns(2)
with col_cam1: cam_shot = st.camera_input("कैमरा", label_visibility="collapsed")
with col_cam2: file_doc = st.file_uploader("चार्ट", type=["jpg", "png"], label_visibility="collapsed")
active_image = cam_shot if cam_shot else file_doc
st.markdown('</div>', unsafe_allow_html=True)

# ऑन-डिमांड सेटिंग बॉक्स (टॉगल होने पर ही दिखेगा)
st.markdown('<div id="settingsBoxContainer" style="display:none; background:#181824; padding:8px; border-radius:10px; margin:4px 0; border:1px solid #9333ea;">', unsafe_allow_html=True)
st.markdown("<span style='color:#c084fc; font-size:12px; font-weight:bold;'>⚙️ मेमोरी व सेटिंग्स:</span>", unsafe_allow_html=True)
if st.button("🗑️ चैट हिस्ट्री साफ़ करें"):
    st.session_state.messages = []
    save_mem()
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 6. स्केच अनुसार: (चैट बाट) + 👉 खुशी Answer
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

# 7. Gemini कॉल (AQ. Key के साथ डायरेक्ट एरर हैंडलिंग)
def ask_gemini(prompt, img):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली।"
    
    # सबसे स्थिर और हाई-कोटा मॉडल
    models_to_try = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    contents_payload = [prompt, Image.open(img)] if img else prompt
    
    error_log = []
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents_payload
            )
            if res and res.text:
                return res.text
        except Exception as ex:
            error_log.append(f"{m}: {str(ex)}")
            continue
            
    return f"सर्वर एरर: {error_log[0] if error_log else 'अज्ञात'}"

def speak(text):
    clean = re.sub(r'[*#~`_+=|\\<>]', ' ', text).replace('"', '').replace("'", "")
    st.components.v1.html(f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance("{clean}");
            u.lang = 'hi-IN';
            window.speechSynthesis.speak(u);
        }}
    </script>
    """, height=0)

# 8. निचला हिस्सा (Key-Ped के लिए जगह)
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query or (active_image and st.button("🔍 विश्लेषण करें")):
    q = user_query if user_query else "कृपया इस तस्वीर का विश्लेषण करें।"
    st.session_state.messages.append({"role": "user", "content": q})
    
    with st.spinner("खुशी सोच रही है... ✨"):
        ans = ask_gemini(q, active_image)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        speak(ans)
        st.rerun()
    
