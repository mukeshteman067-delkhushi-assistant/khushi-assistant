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
    
    /* टॉप स्टेटस बार */
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

# 3. Gemini 3.6 Flash Client Setup
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान और सच्ची AI दोस्त। समय (IST): {ist_now}। बिल्कुल संक्षिप्त, सरल, सटीक और स्पष्ट हिंदी में उत्तर दो।"

# मेमोरी व स्टेट्स
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

# स्टेटस फ्लैग्स (शुरुआत में सब कुछ 100% बंद रहेगा)
if "show_cam" not in st.session_state: st.session_state.show_cam = False
if "show_set" not in st.session_state: st.session_state.show_set = False

# URL से टॉगल स्वीकार करें
qp = st.query_params.get("action", "")
if qp == "cam":
    st.session_state.show_cam = not st.session_state.show_cam
    st.session_state.show_set = False
    st.query_params.clear()
    st.rerun()
elif qp == "set":
    st.session_state.show_set = not st.session_state.show_set
    st.session_state.show_cam = False
    st.query_params.clear()
    st.rerun()

# 4. फ्रोज़न लेआउट: बायाँ 52% पोर्ट्रेट + दायाँ स्विचेस + 1:1 स्क्वायर ज़ूम
st.components.v1.html(f"""
<div id="masterBoard" style="width:100%; box-sizing:border-box; background:#0a0c16; padding:8px; border-radius:14px; border:1px solid #1e2640; position:relative; overflow:hidden;">
    
    <!-- मुख्य सामान्य ग्रिड: बायाँ पोर्ट्रेट + दायाँ स्विचेस -->
    <div id="standardGrid" style="display:flex; width:100%; gap:8px;">
        
        <!-- बायाँ 52%: पोर्ट्रेट विज़ुअल + Puss & Zoom ठीक नीचे -->
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

        <!-- दायाँ 48%: स्विचेस (कैमरा, माइक, सेटिंग) -->
        <div id="switchesPanel" style="width:48%; display:flex; flex-direction:column; justify-content:space-between; gap:8px;">
            <!-- 1. कैमरा ON - OFF स्विच -->
            <button onclick="navAction('cam')" style="width:100%; background:#221b0e; color:#facc15; border:1px solid #ca8a04; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
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
            <button onclick="navAction('set')" style="width:100%; background:#1c172d; color:#c084fc; border:1px solid #9333ea; padding:12px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
                ⚙️ सेटिंग
            </button>
        </div>
    </div>

    <!-- ज़ूम स्थिति: 100vh Cinema Mode (सारे स्विच व खाली जगह गायब) -->
    <div id="squareZoomOverlay" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:#070913; z-index:999999; flex-direction:column; align-items:center; justify-content:center; box-sizing:border-box; padding:15px;">
        
        <button onclick="exitSquareZoom()" style="position:absolute; top:15px; right:15px; background:#ff4b4b; color:#fff; border:none; padding:9px 18px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; box-shadow:0 2px 10px rgba(0,0,0,0.8);">
            ✕ सामान्य डिस्प्ले
        </button>

        <div style="width:85vw; max-width:380px; height:85vw; max-height:380px; background:#000; border:2px solid #00ff80; border-radius:14px; overflow:hidden; box-shadow:0 0 35px rgba(0,255,128,0.5); display:flex; align-items:center; justify-content:center;">
            <img src="{khushi_b64}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />
        </div>

        <div style="display:flex; gap:12px; width:85vw; max-width:380px; margin-top:20px; align-items:center; justify-content:center;">
            <button onclick="pussSpeech()" style="background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:12px 18px; border-radius:25px; font-weight:bold; font-size:13px; cursor:pointer; box-shadow:0 4px 12px rgba(0,0,0,0.6);">
                🛑 Puss
            </button>
            <button onclick="triggerMicVoice()" style="flex:1; background:linear-gradient(90deg, #10b981, #059669); color:#fff; border:none; padding:12px 16px; border-radius:25px; font-weight:bold; font-size:13.5px; cursor:pointer; box-shadow:0 4px 15px rgba(0,255,128,0.3);">
                🎙️ बोलिए (खुशी सुन रही है...)
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
        squareOverlay.style.display = 'flex';
        const pDoc = window.parent.document;
        const cInp = pDoc.querySelector('div[data-testid="stChatInput"]');
        if (cInp) cInp.style.display = 'none';
        const cCard = pDoc.getElementById('chatAnswerContainer');
        if (cCard) cCard.style.display = 'none';
    }}

    function exitSquareZoom() {{
        squareOverlay.style.display = 'none';
        const pDoc = window.parent.document;
        const cInp = pDoc.querySelector('div[data-testid="stChatInput"]');
        if (cInp) cInp.style.display = 'block';
        const cCard = pDoc.getElementById('chatAnswerContainer');
        if (cCard) cCard.style.display = 'block';
    }}

    function pussSpeech() {{
        try {{
            window.speechSynthesis.cancel();
            if (window.parent && window.parent.speechSynthesis) window.parent.speechSynthesis.cancel();
        }} catch(e) {{}}
        micStatus.innerText = 'शांत';
    }}

    function navAction(act) {{
        const url = new URL(window.parent.location.href);
        url.searchParams.set('action', act);
        window.parent.location.href = url.toString();
    }}

    // 100% एक्टिव वॉयस इंजन
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

    function triggerMicVoice() {{
        try {{
            const u = new SpeechSynthesisUtterance("");
            window.speechSynthesis.speak(u);
            if (window.parent && window.parent.speechSynthesis) window.parent.speechSynthesis.speak(u);
        }} catch(e) {{}}
        if (rec) {{
            try {{ rec.start(); }} catch(e) {{ rec.stop(); setTimeout(() => rec.start(), 200); }}
        }}
    }}

    micBtn.onclick = triggerMicVoice;
</script>
""", height=385)

# नंबर 4: सर्चिंग/थिंकिंग स्टेटस ऊपर ही रहेगा
thinking_box = st.empty()

# नंबर 1: कैमरा ऑन-ऑफ (जब तक बटन नहीं दबेगा, कोड 0% रेंडर होगा - शून्य खाली पट्टी)
active_image = None
if st.session_state.show_cam:
    st.markdown('<div style="background:#141724; padding:10px; border-radius:10px; margin:6px 0; border:1px solid #ca8a04;">', unsafe_allow_html=True)
    st.markdown("<span style='color:#facc15; font-size:12px; font-weight:bold;'>📷 कैमरा व स्कैनर एक्टिव है (बंद करने के लिए पुनः स्विच दबाएँ):</span>", unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1: cam_shot = st.camera_input("कैमरा स्कैन", label_visibility="collapsed")
    with col_c2: file_doc = st.file_uploader("चार्ट अपलोड", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    active_image = cam_shot if cam_shot else file_doc
    st.markdown('</div>', unsafe_allow_html=True)

# नंबर 2: सेटिंग्स (जब तक बटन नहीं दबेगा, कोड 0% रेंडर होगा)
if st.session_state.show_set:
    st.markdown('<div style="background:#181628; padding:12px; border-radius:10px; margin:6px 0; border:1px solid #9333ea;">', unsafe_allow_html=True)
    st.markdown("<b style='color:#c084fc; font-size:13px;'>⚙️ सिस्टम सेटिंग्स व टूल्स:</b>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🗑️ चैट मेमोरी साफ़ करें", use_container_width=True):
            st.session_state.messages = []
            save_mem()
            st.success("मेमोरी साफ़ हो गई!")
            st.rerun()
    with col_s2:
        if st.button("✕ सेटिंग्स बंद करें", use_container_width=True):
            st.session_state.show_set = False
            st.rerun()
    st.caption("🟢 एक्टिव AI मॉडल: **Gemini 3.6 Flash** (सुपर-फ़ास्ट टर्बो)")
    st.markdown('</div>', unsafe_allow_html=True)

# 5. चैट संवाद व उत्तर कार्ड
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

# 6. सुपर-फ़ास्ट AI इंजन
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
            
    return "माफ़ कीजिए, सर्वर व्यस्त है। कृपया पुनः पूछें।"

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

# 7. चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query or (active_image and st.button("🔍 इस फ़ोटो का विश्लेषण करें")):
    q = user_query if user_query else "कृपया इस तस्वीर का विश्लेषण करें।"
    st.session_state.messages.append({"role": "user", "content": q})
    
    # नंबर 4: सर्चिंग स्टेटस सीधे ऊपर दिखेगा
    thinking_box.markdown('<div class="thinking-badge">✨ खुशी सोच रही है... उत्तर आ रहा है ⚡</div>', unsafe_allow_html=True)
    
    ans = ask_gemini(q, active_image)
    st.session_state.messages.append({"role": "assistant", "content": ans})
    save_mem()
    
    thinking_box.empty()
    speak(ans)
    st.rerun()
