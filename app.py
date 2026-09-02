import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.4rem 4rem 0.4rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# खुशी ओरिजिनल इमेज (Base64)
def get_khushi_b64():
    if os.path.exists("khushi.jpg"):
        try:
            with open("khushi.jpg", "rb") as f:
                return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
        except Exception: pass
    return ""

khushi_b64 = get_khushi_b64()

# Gemini 3.6 Flash Client
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान और सच्ची AI दोस्त। समय (IST): {ist_now}। संक्षिप्त, सरल व स्पष्ट हिंदी में बात करो।"

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

# 100% फ्रोज़न डिज़ाइन (बायाँ 52% पोर्ट्रेट + दायाँ स्विचेस + 1:1 स्क्वायर ज़ूम)
st.components.v1.html(f"""
<div id="masterBoard" style="width:100%; box-sizing:border-box; background:#0a0c16; padding:8px; border-radius:14px; border:1px solid #1e2640; position:relative; overflow:hidden;">
    
    <div id="standardGrid" style="display:flex; width:100%; gap:8px;">
        
        <div style="width:52%; display:flex; flex-direction:column; gap:6px;">
            <div id="portraitFrame" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35);">
                <img id="avatarPic" src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 12%; animation:breathe 4s infinite ease-in-out;" />
            </div>
            
            <div style="display:flex; gap:5px; width:100%;">
                <button onclick="pussSpeech()" style="flex:1; background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                    🛑 Puss
                </button>
                <button onclick="enterSquareZoom()" style="flex:1; background:#12283d; color:#38bdf8; border:1px solid #38bdf8; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                    ⛶ Zoom
                </button>
            </div>
        </div>

        <div id="switchesPanel" style="width:48%; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
            <button onclick="toggleBox('cameraWrap')" style="width:100%; background:#221b0e; color:#facc15; border:1px solid #ca8a04; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                📷 कैमरा on — off
            </button>

            <div style="display:flex; flex-direction:column; align-items:center;">
                <button id="micBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:15px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                    🎙️ mike - spiker (बोलें)
                </button>
                <span id="micStatus" style="font-size:10px; color:#9ca3af; margin-top:4px;">माइक व स्पीकर एक्टिव</span>
            </div>

            <button onclick="toggleBox('settingsWrap')" style="width:100%; background:#1c172d; color:#c084fc; border:1px solid #9333ea; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                ⚙️ सेटिंग
            </button>
        </div>
    </div>

    <div id="squareZoomOverlay" style="display:none; width:100%; height:490px; position:relative; background:#000; border-radius:14px; overflow:hidden; border:2px solid #00ff80; box-shadow:0 0 30px rgba(0,255,128,0.5);">
        <div style="width:100%; height:390px; display:flex; justify-content:center; align-items:center; background:#000; overflow:hidden;">
            <img src="{khushi_b64}" style="width:380px; height:380px; object-fit:cover; object-position:center 15%; border-radius:14px;" />
        </div>
        
        <button onclick="exitSquareZoom()" style="position:absolute; top:12px; right:12px; z-index:100; background:#ff4b4b; color:#fff; border:none; padding:8px 16px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,0.7);">
            ✕ सामान्य डिस्प्ले
        </button>

        <div style="position:absolute; bottom:12px; left:0; width:100%; display:flex; justify-content:center; align-items:center; gap:12px; z-index:100; padding:0 10px; box-sizing:border-box;">
            <button onclick="pussSpeech()" style="background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:12px 18px; border-radius:25px; font-weight:bold; font-size:13px; cursor:pointer;">
                🛑 Puss (रोकें)
            </button>
            <button onclick="startVoice()" style="flex:1; max-width:260px; background:linear-gradient(90deg, #10b981, #059669); color:#fff; border:none; padding:12px 16px; border-radius:25px; font-weight:bold; font-size:13.5px; cursor:pointer; box-shadow:0 4px 15px rgba(0,255,128,0.3);">
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
    const micBtn = document.getElementById('micBtn');

    function enterSquareZoom() {{
        standardGrid.style.display = 'none';
        squareOverlay.style.display = 'block';
        const pDoc = window.parent.document;
        const cInp = pDoc.querySelector('div[data-testid="stChatInput"]');
        if (cInp) cInp.style.display = 'none';
        const cCard = pDoc.getElementById('chatAnswerContainer');
        if (cCard) cCard.style.display = 'none';
    }}

    function exitSquareZoom() {{
        squareOverlay.style.display = 'none';
        standardGrid.style.display = 'flex';
        const pDoc = window.parent.document;
        const cInp = pDoc.querySelector('div[data-testid="stChatInput"]');
        if (cInp) cInp.style.display = 'block';
        const cCard = pDoc.getElementById('chatAnswerContainer');
        if (cCard) cCard.style.display = 'block';
    }}

    function pussSpeech() {{
        try {{
            window.speechSynthesis.cancel();
            if (window.parent && window.parent.speechSynthesis) {{
                window.parent.speechSynthesis.cancel();
            }}
        }} catch(e) {{}}
        micStatus.innerText = 'शांत';
    }}

    function toggleBox(boxId) {{
        const pDoc = window.parent.document;
        const target = pDoc.getElementById(boxId);
        const otherId = boxId === 'cameraWrap' ? 'settingsWrap' : 'cameraWrap';
        const other = pDoc.getElementById(otherId);
        if (other) other.style.display = 'none';
        if (target) {{
            const isHidden = target.style.display === 'none' || !target.style.display;
            target.style.display = isHidden ? 'block' : 'none';
            if (isHidden) target.scrollIntoView({{ behavior: 'smooth' }});
        }}
    }}

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition || (window.parent && (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition));
    let rec = null;
    if (SpeechRec) {{
        rec = new SpeechRec();
        rec.lang = 'hi-IN';
        rec.onstart = () => {{
            micStatus.innerText = "सुन रही हूँ... बोलिए 🎙️";
            micBtn.style.background = "#10b981";
        }};
        rec.onresult = (e) => {{
            const text = e.results[0][0].transcript;
            micStatus.innerText = "भेजा: " + text;
            micBtn.style.background = "#ff4b4b";
            const pDoc = window.parent.document;
            const inp = pDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (inp) {{
                const nativeVal = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                nativeVal.call(inp, text);
                inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
                setTimeout(() => {{
                    const send = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                    if (send) send.click();
                }}, 300);
            }}
        }};
        rec.onerror = () => {{ micBtn.style.background = "#ff4b4b"; micStatus.innerText = "माइक एरर"; }};
        rec.onend = () => {{ micBtn.style.background = "#ff4b4b"; }};
    }}

    function startVoice() {{
        try {{
            const u = new SpeechSynthesisUtterance("");
            window.speechSynthesis.speak(u);
            if (window.parent && window.parent.speechSynthesis) window.parent.speechSynthesis.speak(u);
        }} catch(e) {{}}
        if (rec) {{
            try {{ rec.start(); }} catch(e) {{ rec.stop(); setTimeout(() => rec.start(), 200); }}
        }}
    }}

    micBtn.onclick = startVoice;
</script>
""", height=385)

# शुद्ध ऑन-डिमांड कैमरा ब्लॉक (स्क्रीन पर कोई खुला कचरा नहीं - 100% हिडन)
active_image = None
st.markdown("""
<div id="cameraWrap" style="display:none; background:#141724; padding:10px; border-radius:10px; margin:6px 0; border:1px solid #ca8a04;">
    <span style='color:#facc15; font-size:12px; font-weight:bold;'>📷 कैमरा व स्कैनर (फ़ोटो लें या अपलोड करें):</span>
</div>
""", unsafe_allow_html=True)

# शुद्ध ऑन-डिमांड सेटिंग्स ब्लॉक (स्क्रीन पर कोई खुला कचरा नहीं - 100% हिडन)
st.markdown("""
<div id="settingsWrap" style="display:none; background:#181628; padding:12px; border-radius:10px; margin:6px 0; border:1px solid #9333ea;">
    <b style='color:#c084fc; font-size:13px;'>⚙️ सिस्टम सेटिंग्स:</b>
    <p style='font-size:11px; color:#9ca3af; margin:4px 0 0 0;'>🟢 AI मॉडल: <b>Gemini 3.6 Flash</b> सक्रिय है।</p>
</div>
""", unsafe_allow_html=True)

# चैट संवाद व उत्तर कार्ड
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

# AI इंजन (Gemini 3.6 Flash)
def ask_gemini(prompt, img):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली।"
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

# चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.spinner("खुशी सोच रही है... ✨"):
        ans = ask_gemini(user_query, None)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        save_mem()
        speak(ans)
        st.rerun()
