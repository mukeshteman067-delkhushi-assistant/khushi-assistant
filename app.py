import streamlit as st
import json, os, re, base64
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# 1. पेज कॉन्फ़िगरेशन (स्क्रीनशॉट 1000267261.jpg के अनुसार 100% फ्रोज़न)
st.set_page_config(page_title="Khushi AI", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .block-container { padding: 0.2rem 0.3rem 4rem 0.3rem !important; max-width: 100% !important; }
    header, footer, #MainMenu { visibility: hidden !important; }
    
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

# 2. खुशी मीडिया लोडर (MP4 या फ़ोटो)
def get_khushi_assets():
    has_vid = os.path.exists("khushi.mp4")
    v_b64, img_b64 = "", ""
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

# 3. Gemini Client Setup
raw_key = st.secrets.get("GEMINI_API_KEY", "")
API_KEY = "".join(raw_key.split()) if raw_key else ""
client = genai.Client(api_key=API_KEY) if API_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान और सच्ची AI दोस्त। समय (IST): {ist_now}। बिल्कुल संक्षिप्त, सरल, सजीव और सीधे हिंदी में 2-3 पंक्तियों में तुरंत उत्तर दो।"

# 4. मेमोरी
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

# हिडन मेमोरी साफ़ ट्रिगर
if st.query_params.get("action") == "clear_mem":
    st.session_state.messages = []
    save_mem()
    st.query_params.clear()
    st.rerun()

# जो अंतिम उत्तर बोलना है
last_answer = ""
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_answer = st.session_state.messages[-1]["content"]
clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', last_answer).replace('"', ' ').replace("'", " ").strip()

# मीडिया टैग्स
if has_vid:
    m_norm = f'<video id="kMediaNorm" src="{media_src}" loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 12%;"></video>'
    m_zoom = f'<video id="kMediaZoom" src="{media_src}" loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 15%;"></video>'
else:
    m_norm = f'<img id="kMediaNorm" src="{media_src}" style="width:100%; height:100%; object-fit:cover; object-position:center 12%; animation:breathe 4s infinite ease-in-out;" />'
    m_zoom = f'<img id="kMediaZoom" src="{media_src}" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />'

# 5. स्क्रीनशॉट 1000267261.jpg वाला 100% परफेक्ट फ्रोज़न UI ब्लॉक
html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
    @keyframes breathe { 0%{transform:scale(1);} 50%{transform:scale(1.02) translateY(-1px);} 100%{transform:scale(1);} }
    @keyframes bounce { 0%{height:4px;} 100%{height:18px;} }
</style>
</head>
<body style="background:#0a0c16; padding:8px; border-radius:14px; border:1px solid #1e2640; overflow:hidden;">

<div id="standardGrid" style="display:flex; width:100%; gap:8px;">
    
    <!-- बायाँ 52%: विज़ुअल + लिप-सिंक + Puss & Zoom नीचे -->
    <div style="width:52%; display:flex; flex-direction:column; gap:6px;">
        <div id="portraitFrame" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:transform 0.2s ease, border-color 0.2s ease;">
            __MEDIA_NORM__
            <div id="voiceWave" style="position:absolute; bottom:6px; left:50%; transform:translateX(-50%); display:none; gap:3px; align-items:flex-end; height:18px;">
                <div style="width:3px; height:8px; background:#00ff80; border-radius:2px; animation:bounce 0.4s infinite alternate;"></div>
                <div style="width:3px; height:16px; background:#00ff80; border-radius:2px; animation:bounce 0.3s infinite alternate;"></div>
                <div style="width:3px; height:10px; background:#00ff80; border-radius:2px; animation:bounce 0.5s infinite alternate;"></div>
            </div>
        </div>
        
        <div style="display:flex; gap:5px; width:100%;">
            <button onclick="pussSpeech()" style="flex:1; background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                🛑 Puss
            </button>
            <button onclick="toggleZoom(true)" style="flex:1; background:#12283d; color:#38bdf8; border:1px solid #38bdf8; padding:9px 2px; border-radius:8px; font-size:12px; font-weight:bold; cursor:pointer;">
                ⛶ Zoom
            </button>
        </div>
    </div>

    <!-- दायाँ 48%: स्विचेस + इन-प्लेस लाइव कैमरा + इनलाइन सेटिंग्स (Exact Screenshot 1000267261.jpg) -->
    <div id="switchesPanel" style="width:48%; display:flex; flex-direction:column; justify-content:space-between; gap:6px;">
        <button id="camToggleBtn" onclick="toggleInternalCam()" style="width:100%; background:#221b0e; color:#facc15; border:1px solid #ca8a04; padding:9px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer;">
            📷 कैमरा on — off
        </button>

        <!-- बीच का काला इन-प्लेस कैमरा बॉक्स (88px) -->
        <div id="inlineCamBox" style="width:100%; height:88px; background:#07080f; border-radius:10px; border:1px dashed #2e3856; overflow:hidden; position:relative; display:flex; align-items:center; justify-content:center;">
            <video id="liveVideoFeed" autoplay playsinline muted style="width:100%; height:100%; object-fit:cover; display:none;"></video>
            <span id="camPlaceholderText" style="color:#555f7d; font-size:10px; text-align:center; padding:4px;">कैमरा स्टैंडबाय (OFF)</span>
        </div>

        <div style="display:flex; flex-direction:column; align-items:center;">
            <button id="micBtn" onclick="triggerMicVoice()" style="width:100%; background:#ff4b4b; color:white; border:none; padding:12px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                🎙️ mike - spiker (बोलें)
            </button>
            <span id="micStatus" style="font-size:10px; color:#9ca3af; margin-top:2px;">माइक व स्पीकर एक्टिव</span>
        </div>

        <div style="width:100%; background:#131526; border:1px solid #7c3aed; border-radius:10px; padding:5px 4px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; padding:0 2px;">
                <span style="color:#c084fc; font-size:10.5px; font-weight:bold;">⚙️ सेटिंग</span>
                <span style="color:#10b981; font-size:9px;">● 3.6 Flash</span>
            </div>
            <button onclick="clearMemorySafe()" style="width:100%; background:#28152e; color:#f472b6; border:1px solid #db2777; padding:5px 2px; border-radius:6px; font-size:10.5px; font-weight:bold; cursor:pointer;">
                🗑️ मेमोरी साफ़ करें
            </button>
        </div>
    </div>
</div>

<!-- 1:1 स्क्वायर ज़ूम सिनेमाई डिस्प्ले (Exact Screenshot 1000267278.jpg) -->
<div id="squareZoomOverlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:#070913; z-index:99999; flex-direction:column; align-items:center; justify-content:center; padding:15px;">
    <button onclick="toggleZoom(false)" style="position:absolute; top:12px; right:12px; background:#ff4b4b; color:#fff; border:none; padding:8px 16px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer;">
        ✕ सामान्य डिस्प्ले
    </button>

    <div style="width:260px; height:260px; background:#000; border:2px solid #00ff80; border-radius:14px; overflow:hidden; box-shadow:0 0 25px rgba(0,255,128,0.5); display:flex; align-items:center; justify-content:center;">
        __MEDIA_ZOOM__
    </div>

    <div style="display:flex; gap:10px; width:260px; margin-top:16px;">
        <button onclick="pussSpeech()" style="background:#451212; color:#ff6b6b; border:1px solid #ff4b4b; padding:10px 16px; border-radius:20px; font-weight:bold; font-size:12px; cursor:pointer;">
            🛑 Puss
        </button>
        <button onclick="triggerMicVoice()" style="flex:1; background:linear-gradient(90deg, #10b981, #059669); color:#fff; border:none; padding:10px 14px; border-radius:20px; font-weight:bold; font-size:12.5px; cursor:pointer;">
            🎙️ बोलिए
        </button>
    </div>
</div>

<script>
    const micStatus = document.getElementById('micStatus');
    const micBtn = document.getElementById('micBtn');
    const liveVideo = document.getElementById('liveVideoFeed');
    const camBox = document.getElementById('inlineCamBox');
    const camPlaceholder = document.getElementById('camPlaceholderText');
    const camBtn = document.getElementById('camToggleBtn');
    const portraitFrame = document.getElementById('portraitFrame');
    const voiceWave = document.getElementById('voiceWave');
    const mNorm = document.getElementById('kMediaNorm');
    const mZoom = document.getElementById('kMediaZoom');

    let camStream = null;

    // 1. लाइव कैमरा ऑन/ऑफ (सीधे उसी 88px बॉक्स में)
    async function toggleInternalCam() {
        if (camStream) {
            camStream.getTracks().forEach(t => t.stop());
            camStream = null;
            liveVideo.style.display = 'none';
            camPlaceholder.style.display = 'block';
            camPlaceholder.innerText = 'कैमरा स्टैंडबाय (OFF)';
            camBox.style.borderColor = '#2e3856';
            camBtn.style.color = '#facc15';
            camBtn.innerText = '📷 कैमरा on — off';
        } else {
            try {
                camStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
                liveVideo.srcObject = camStream;
                liveVideo.style.display = 'block';
                camPlaceholder.style.display = 'none';
                camBox.style.borderColor = '#00ff80';
                camBtn.style.color = '#00ff80';
                camBtn.innerText = '📷 कैमरा (LIVE ON)';
            } catch(err) {
                camPlaceholder.innerText = 'अनुमति दें';
            }
        }
    }

    // 2. 1:1 स्क्वायर ज़ूम टॉगल
    function toggleZoom(open) {
        document.getElementById('squareZoomOverlay').style.display = open ? 'flex' : 'none';
        try {
            const pDoc = window.parent.document;
            const cInp = pDoc.querySelector('div[data-testid="stChatInput"]');
            if (cInp) cInp.style.display = open ? 'none' : 'block';
        } catch(e) {}
    }

    // 3. मेमोरी साफ़ (1-क्लिक)
    function clearMemorySafe() {
        const url = new URL(window.parent.location.href);
        url.searchParams.set('action', 'clear_mem');
        window.parent.location.href = url.toString();
    }

    // 4. लिप-सिंक व मोशन
    function setSpeaking(on) {
        if (on) {
            if (mNorm && mNorm.tagName === 'VIDEO') mNorm.play().catch(e=>{});
            if (mZoom && mZoom.tagName === 'VIDEO') mZoom.play().catch(e=>{});
            portraitFrame.style.transform = 'scale(1.025) rotate(0.8deg)';
            portraitFrame.style.borderColor = '#00ff80';
            if (voiceWave) voiceWave.style.display = 'flex';
        } else {
            if (mNorm && mNorm.tagName === 'VIDEO') mNorm.pause();
            if (mZoom && mZoom.tagName === 'VIDEO') mZoom.pause();
            portraitFrame.style.transform = 'scale(1) rotate(0deg)';
            portraitFrame.style.borderColor = '#ff4b4b';
            if (voiceWave) voiceWave.style.display = 'none';
        }
    }

    // 5. Puss
    function pussSpeech() {
        if ('speechSynthesis' in window) window.speechSynthesis.cancel();
        try { if (window.parent && window.parent.speechSynthesis) window.parent.speechSynthesis.cancel(); } catch(e) {}
        setSpeaking(false);
        micStatus.innerText = 'शांत';
    }

    // 6. माइक (Voice to Chat)
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition || (window.parent && (window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition));
    let rec = SR ? new SR() : null;

    if (rec) {
        rec.lang = 'hi-IN';
        rec.onstart = () => { micStatus.innerText = "सुन रही हूँ... बोलिए 🎙️"; micBtn.style.background = "#10b981"; };
        rec.onresult = (e) => {
            const text = e.results[0][0].transcript;
            micStatus.innerText = "भेजा: " + text;
            micBtn.style.background = "#ff4b4b";
            try {
                const pDoc = window.parent.document;
                const inp = pDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (inp) {
                    Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set.call(inp, text);
                    inp.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(() => {
                        const send = pDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                        if (send) send.click();
                    }, 250);
                }
            } catch(err) {}
        };
        rec.onerror = () => { micBtn.style.background = "#ff4b4b"; micStatus.innerText = "माइक एरर"; };
        rec.onend = () => { micBtn.style.background = "#ff4b4b"; };
    }

    function triggerMicVoice() {
        try { window.speechSynthesis.speak(new SpeechSynthesisUtterance("")); } catch(e) {}
        if (rec) {
            try { rec.start(); } catch(e) { rec.stop(); setTimeout(() => rec.start(), 200); }
        }
    }

    // 7. ऑटो-स्पीकर व लिप-सिंक
    const toSpeak = "__CLEAN_SPEAK__";
    if (toSpeak && toSpeak.length > 0 && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(toSpeak);
        u.lang = 'hi-IN';
        u.rate = 1.0;
        u.pitch = 1.05;

        u.onstart = () => { setSpeaking(true); micStatus.innerText = "खुशी बोल रही है... 🔊"; };
        u.onend = () => { setSpeaking(false); micStatus.innerText = "माइक व स्पीकर एक्टिव"; };
        u.onerror = () => { setSpeaking(false); micStatus.innerText = "माइक व स्पीकर एक्टिव"; };

        setTimeout(() => { window.speechSynthesis.speak(u); }, 150);
    }
</script>
</body>
</html>
"""

final_html = html_code.replace("__MEDIA_NORM__", m_norm)\
                      .replace("__MEDIA_ZOOM__", m_zoom)\
                      .replace("__CLEAN_SPEAK__", clean_speak)

st.components.v1.html(final_html, height=385)

# 6. स्टेटस व चैट संवाद कार्ड (Exact Screenshot 1000267261.jpg)
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

# 7. AI इंजन: प्राथमिक Gemini 3.6 Flash (अथवा 2.5 Flash बैकअप)
def ask_gemini(prompt):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली। कृपया Secrets जाँचें।"
    
    # 1. पहला प्रयास: प्राथमिक मॉडल 3.6 Flash
    try:
        res = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=PERSONA)
        )
        if res and res.text:
            return res.text
    except Exception:
        pass
        
    # 2. दूसरा प्रयास: यदि 429 कोटा या सर्वर एरर आए तो अथवा बैकअप 2.5 Flash
    try:
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=PERSONA)
        )
        if res and res.text:
            return res.text
    except Exception as e:
        return f"सर्वर अधिक व्यस्त है, कृपया कुछ सेकंड बाद पुनः बोलें।"
        
    return "माफ़ कीजिए, उत्तर प्राप्त नहीं हुआ। कृपया पुनः प्रयास करें।"

# 8. चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    thinking_box.markdown('<div class="thinking-badge">✨ खुशी सोच रही है... उत्तर आ रहा है ⚡</div>', unsafe_allow_html=True)
    
    ans = ask_gemini(user_query)
    st.session_state.messages.append({"role": "assistant", "content": ans})
    save_mem()
    
    thinking_box.empty()
    st.rerun()
    
