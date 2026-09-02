import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

# 1. पेज कॉन्फ़िगरेशन (डिज़ाइन 100% सुरक्षित)
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.4rem 4rem 0.4rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
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

# मेमोरी प्रबंधन
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

# 4. शुद्ध HTML/JS द्वारा 100% एक्टिव व गतिशील बटन्स (बिना डिज़ाइन बदले)
st.components.v1.html(f"""
<div id="masterBoard" style="width:100%; box-sizing:border-box; background:#0a0c16; padding:8px; border-radius:14px; border:1px solid #1e2640; position:relative; overflow:hidden;">
    
    <!-- सामान्य दृश्य: बायाँ पोर्ट्रेट + दायाँ स्विचेस (Exact Design) -->
    <div id="standardGrid" style="display:flex; width:100%; gap:8px;">
        
        <!-- बायाँ 52%: पोर्ट्रेट विज़ुअल + Puss & Zoom नीचे -->
        <div style="width:52%; display:flex; flex-direction:column; gap:6px;">
            <div id="portraitFrame" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:all 0.35s ease;">
                <img id="avatarPic" src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 12%; animation:breathe 4s infinite ease-in-out;" />
            </div>
            
            <div style="display:flex; gap:5px; width:100%;">
                <button onclick="pussSpeech()" id="pussBtn" style="flex:1; background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                    🛑 Puss
                </button>
                <button onclick="enterSquareZoom()" style="flex:1; background:#12283d; color:#38bdf8; border:1px solid #38bdf8; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                    ⛶ Zoom
                </button>
            </div>
        </div>

        <!-- दायाँ 48%: स्विचेस (कैमरा ऑन-ऑफ, माइक-स्पीकर, सेटिंग) -->
        <div id="switchesPanel" style="width:48%; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
            <!-- 1. कैमरा ON - OFF स्विच -->
            <button onclick="toggleCamDirect()" style="width:100%; background:#221b0e; color:#facc15; border:1px solid #ca8a04; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                📷 कैमरा on — off
            </button>

            <!-- 2. mike - spiker (बोलने के लिए) -->
            <div style="display:flex; flex-direction:column; align-items:center;">
                <button id="micBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:15px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                    🎙️ mike - spiker (बोलें)
                </button>
                <span id="micStatus" style="font-size:10px; color:#9ca3af; margin-top:4px;">माइक व स्पीकर एक्टिव</span>
            </div>

            <!-- 3. सेटिंग स्विच -->
            <button onclick="toggleSettingsDirect()" style="width:100%; background:#1c172d; color:#c084fc; border:1px solid #9333ea; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                ⚙️ सेटिंग
            </button>
        </div>
    </div>

    <!-- ज़ूम स्थिति: 1:1 Square काले घेरे में विज़ुअल -->
    <div id="squareZoomOverlay" style="display:none; width:100%; height:490px; position:relative; background:#000; border-radius:14px; overflow:hidden; border:2px solid #00ff80; box-shadow:0 0 30px rgba(0,255,128,0.5);">
        
        <div style="width:100%; height:390px; display:flex; justify-content:center; align-items:center; background:#000; overflow:hidden;">
            <img src="{khushi_b64}" style="width:380px; height:380px; object-fit:cover; object-position:center 15%; border-radius:14px;" />
        </div>
        
        <button onclick="exitSquareZoom()" style="position:absolute; top:12px; right:12px; z-index:100; background:#ff4b4b; color:#fff; border:none; padding:8px 16px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,0.7);">
            ✕ सामान्य डिस्प्ले
        </button>

        <div style="position:absolute; bottom:12px; left:0; width:100%; display:flex; justify-content:center; align-items:center; gap:12px; z-index:100; padding:0 10px; box-sizing:border-box;">
            <button onclick="pussSpeech()" style="background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:12px 18px; border-radius:25px; font-weight:bold; font-size:13px; cursor:pointer; box-shadow:0 4px 12px rgba(0,0,0,0.6);">
                🛑 Puss (रोकें)
            </button>
            <button onclick="triggerMicVoice()" style="flex:1; max-width:260px; background:linear-gradient(90deg, #10b981, #059669); color:#fff; border:none; padding:12px 16px; border-radius:25px; font-weight:bold; font-size:13.5px; cursor:pointer; box-shadow:0 4px 15px rgba(0,255,128,0.3);">
                🎙️ बोलिए (माइक व स्पीकर चालू)
            </button>
        </div>
    </div>
</div>

<style>
    @keyframes breathe {{ 0%{{transform:scale(1);}} 50%{{transform:scale(1.025) translateY(-1.5px);}} 100%{{transform:scale(1);}} }}
</style>

<script>
    const standardGrid = document.getElementById('standardGrid');
    const squareOverlay = document.getElementById('squareZoomOverlay');
    const micStatus = document.getElementById('micStatus');
    const portraitFrame = document.getElementById('portraitFrame');
    const micBtn = document.getElementById('micBtn');

    // 1. Zoom In/Out (Perfect Working)
    function enterSquareZoom() {{
        standardGrid.style.display = 'none';
        squareOverlay.style.display = 'block';
        
        const chatInp = window.parent.document.querySelector('div[data-testid="stChatInput"]');
        if (chatInp) chatInp.style.display = 'none';
        
        const chatCards = window.parent.document.getElementById('chatAnswerContainer');
        if (chatCards) chatCards.style.display = 'none';

        const camBox = window.parent.document.getElementById('hiddenCameraBlock');
        if (camBox) camBox.style.display = 'none';

        const setBox = window.parent.document.getElementById('hiddenSettingsBlock');
        if (setBox) setBox.style.display = 'none';
    }}

    function exitSquareZoom() {{
        squareOverlay.style.display = 'none';
        standardGrid.style.display = 'flex';
        
        const chatInp = window.parent.document.querySelector('div[data-testid="stChatInput"]');
        if (chatInp) chatInp.style.display = 'block';
        
        const chatCards = window.parent.document.getElementById('chatAnswerContainer');
        if (chatCards) chatCards.style.display = 'block';
    }}

    // 2. Puss (बोलना तुरंत बीच में म्यूट करें)
    function pussSpeech() {{
        try {{
            window.speechSynthesis.cancel();
            if (window.parent && window.parent.speechSynthesis) {{
                window.parent.speechSynthesis.cancel();
            }}
        }} catch(e) {{}}
        portraitFrame.style.borderColor = '#ff4b4b';
        micStatus.innerText = 'शांत';
    }}

    // 3. कैमरा ऑन-ऑफ (Instant DOM Toggle)
    function toggleCamDirect() {{
        const camEl = window.parent.document.getElementById('hiddenCameraBlock');
        const setEl = window.parent.document.getElementById('hiddenSettingsBlock');
        if (setEl) setEl.style.display = 'none';
        if (camEl) {{
            const isShown = camEl.style.display === 'block';
            camEl.style.display = isShown ? 'none' : 'block';
            if (!isShown) camEl.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // 4. सेटिंग ऑन-ऑफ (Instant DOM Toggle)
    function toggleSettingsDirect() {{
        const setEl = window.parent.document.getElementById('hiddenSettingsBlock');
        const camEl = window.parent.document.getElementById('hiddenCameraBlock');
        if (camEl) camEl.style.display = 'none';
        if (setEl) {{
            const isShown = setEl.style.display === 'block';
            setEl.style.display = isShown ? 'none' : 'block';
            if (!isShown) setEl.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    // 5. माइक व स्पीकर (100% Reliable Voice Engine)
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition || (window.parent && (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition));
    let rec = null;

    if (SpeechRec) {{
        rec = new SpeechRec();
        rec.lang = 'hi-IN';
        rec.continuous = false;
        rec.interimResults = false;

        rec.onstart = () => {{
            micStatus.innerText = "सुन रही हूँ... बोलिए 🎙️";
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

        rec.onerror = (err) => {{
            micBtn.style.background = "#ff4b4b";
            micStatus.innerText = "माइक अनुमति दें";
        }};
        
        rec.onend = () => {{
            micBtn.style.background = "#ff4b4b";
        }};
    }}

    function triggerMicVoice() {{
        try {{
            const unlock = new SpeechSynthesisUtterance("");
            window.speechSynthesis.speak(unlock);
            if (window.parent && window.parent.speechSynthesis) {{
                window.parent.speechSynthesis.speak(unlock);
            }}
        }} catch(e) {{}}

        if (rec) {{
            try {{
                rec.start();
            }} catch(e) {{
                rec.stop();
                setTimeout(() => rec.start(), 200);
            }}
        }} else {{
            micStatus.innerText = "ब्राउज़र सपोर्ट नहीं है";
        }}
    }}

    micBtn.onclick = triggerMicVoice;
</script>
""", height=385)

# 5. ऑन-डिमांड कैमरा ब्लॉक (शुरुआत में 100% छुपा हुआ - कोई खाली पट्टी नहीं)
active_image = None
st.markdown('<div id="hiddenCameraBlock" style="display:none; background:#141724; padding:10px; border-radius:10px; margin:6px 0; border:1px solid #ca8a04;">', unsafe_allow_html=True)
st.markdown("<span style='color:#facc15; font-size:12px; font-weight:bold;'>📷 कैमरा व इमेज स्कैनर (फ़ोटो लें या बंद करने के लिए दोबारा स्विच दबाएँ):</span>", unsafe_allow_html=True)
col_c1, col_c2 = st.columns(2)
with col_c1: cam_shot = st.camera_input("कैमरा", label_visibility="collapsed")
with col_c2: file_doc = st.file_uploader("गैलरी", type=["jpg", "png"], label_visibility="collapsed")
active_image = cam_shot if cam_shot else file_doc
st.markdown('</div>', unsafe_allow_html=True)

# 6. ऑन-डिमांड सेटिंग्स ब्लॉक (शुरुआत में 100% छुपा हुआ)
st.markdown('<div id="hiddenSettingsBlock" style="display:none; background:#181628; padding:12px; border-radius:10px; margin:6px 0; border:1px solid #9333ea;">', unsafe_allow_html=True)
st.markdown("<b style='color:#c084fc; font-size:13px;'>⚙️ सिस्टम सेटिंग्स व टूल्स:</b>", unsafe_allow_html=True)
col_s1, col_s2 = st.columns(2)
with col_s1:
    if st.button("🗑️ चैट हिस्ट्री / मेमोरी साफ़ करें", use_container_width=True):
        st.session_state.messages = []
        save_mem()
        st.rerun()
with col_s2:
    if st.button("🔄 सिस्टम रीलोड / रिफ्रेश", use_container_width=True):
        st.rerun()
st.caption("🟢 एक्टिव AI मॉडल: **Gemini 3.6 Flash**")
st.markdown('</div>', unsafe_allow_html=True)

# 7. चैट संवाद व उत्तर कार्ड
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

# 8. आधिकारिक Gemini 3.6 Flash इंजन
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

# 9. निचला इनपुट
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
        
