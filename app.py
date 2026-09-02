import streamlit as st
import json, os, re, base64, urllib.request
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

# 3. API सेटिंग्स
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "").strip()
ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY", "").strip()
ELEVEN_VOICE_ID = st.secrets.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip() # डिफ़ॉल्ट या आपकी कस्टम वॉयस ID

client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%I:%M %p, %d %b %Y")
PERSONA = f"तुम 'Khushi' हो - हमदर्द, बुद्धिमान, सजीव और सच्ची AI दोस्त। समय (IST): {ist_now}। बिल्कुल संक्षिप्त, सरल, सजीव और सीधे हिंदी में 2-3 पंक्तियों में तुरंत उत्तर दो।"

# 4. ElevenLabs ऑडियो जनरेटर (प्राकृतिक मानवीय आवाज़)
def get_elevenlabs_audio(text):
    if not ELEVEN_KEY:
        return ""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_KEY
        }
        data = json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
        }).encode("utf-8")
        
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as res:
            audio_bytes = res.read()
            return f"data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}"
    except Exception:
        return ""

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

if st.query_params.get("action") == "clear":
    st.session_state.messages = []
    save_mem()
    st.query_params.clear()
    st.rerun()

# अंतिम उत्तर और ऑडियो
last_audio = st.session_state.get("current_audio", "")
last_answer = ""
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_answer = st.session_state.messages[-1]["content"]
clean_speak = re.sub(r'[*#~`_+=|\\<>]', ' ', last_answer).replace('"', ' ').replace("'", " ").strip()

# 5. मुख्य फ्रोज़न डिस्प्ले + Web Audio API रियल लिप-सिंक इंजन
st.components.v1.html(f"""
<div id="masterBoard" style="width:100%; box-sizing:border-box; background:#0a0c16; padding:8px; border-radius:14px; border:1px solid #1e2640; position:relative; overflow:hidden;">
    
    <div id="standardGrid" style="display:flex; width:100%; gap:8px;">
        
        <!-- बायाँ 52%: विज़ुअल + वोकल लिप-सिंक -->
        <div style="width:52%; display:flex; flex-direction:column; gap:6px;">
            <div id="portraitFrame" style="width:100%; height:310px; background:#000; border:2px solid #ff4b4b; border-radius:12px; overflow:hidden; position:relative; box-shadow:0 0 18px rgba(255,75,75,0.35); transition:transform 0.15s ease, border-color 0.2s ease;">
                {'<video id="khushiMediaNormal" src="' + khushi_video + '" loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 12%;"></video>' if has_vid else '<img id="khushiMediaNormal" src="' + khushi_img + '" style="width:100%; height:100%; object-fit:cover; object-position:center 12%;" />'}
                
                <!-- वोकल ऑडियो वेव इंडिकेटर -->
                <div id="voiceWave" style="position:absolute; bottom:6px; left:50%; transform:translateX(-50%); display:none; gap:3px; align-items:flex-end; height:18px;">
                    <div class="bar" style="width:3px; height:8px; background:#00ff80; border-radius:2px;"></div>
                    <div class="bar" style="width:3px; height:16px; background:#00ff80; border-radius:2px;"></div>
                    <div class="bar" style="width:3px; height:10px; background:#00ff80; border-radius:2px;"></div>
                </div>
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

        <!-- दायाँ 48%: स्विचेस + लाइव कैमरा + इनलाइन सेटिंग्स -->
        <div id="switchesPanel" style="width:48%; display:flex; flex-direction:column; justify-content:space-between; gap:6px;">
            <button id="camToggleBtn" onclick="toggleInternalCam()" style="width:100%; background:#221b0e; color:#facc15; border:1px solid #ca8a04; padding:9px 2px; border-radius:10px; font-size:12px; font-weight:bold; cursor:pointer; transition:0.2s;">
                📷 कैमरा on — off
            </button>

            <div id="inlineCamBox" style="width:100%; height:88px; background:#07080f; border-radius:10px; border:1px dashed #2e3856; overflow:hidden; position:relative; display:flex; align-items:center; justify-content:center;">
                <video id="liveVideoFeed" autoplay playsinline muted style="width:100%; height:100%; object-fit:cover; display:none;"></video>
                <span id="camPlaceholderText" style="color:#555f7d; font-size:10px; text-align:center; padding:4px;">कैमरा स्टैंडबाय (OFF)</span>
            </div>

            <div style="display:flex; flex-direction:column; align-items:center;">
                <button id="micBtn" style="width:100%; background:#ff4b4b; color:white; border:none; padding:12px 2px; border-radius:10px; font-size:13px; font-weight:bold; cursor:pointer; box-shadow:0 3px 12px rgba(255,75,75,0.45);">
                    🎙️ mike - spiker (बोलें)
                </button>
                <span id="micStatus" style="font-size:10px; color:#9ca3af; margin-top:2px;">माइक व स्पीकर एक्टिव</span>
            </div>

            <div style="width:100%; background:#131526; border:1px solid #7c3aed; border-radius:10px; padding:5px 4px; box-sizing:border-box;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; padding:0 2px;">
                    <span style="color:#c084fc; font-size:10.5px; font-weight:bold;">⚙️ सेटिंग</span>
                    <span style="color:#10b981; font-size:9px;">● 3.6 Flash</span>
                </div>
                <button onclick="clearMemoryDirect()" style="width:100%; background:#28152e; color:#f472b6; border:1px solid #db2777; padding:5px 2px; border-radius:6px; font-size:10.5px; font-weight:bold; cursor:pointer;">
                    🗑️ मेमोरी साफ़ करें
                </button>
            </div>
        </div>
    </div>

    <!-- ज़ूम स्थिति: 100vh Cinema Mode -->
    <div id="squareZoomOverlay" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:#070913; z-index:999999; flex-direction:column; align-items:center; justify-content:center; box-sizing:border-box; padding:15px;">
        <button onclick="exitSquareZoom()" style="position:absolute; top:15px; right:15px; background:#ff4b4b; color:#fff; border:none; padding:9px 18px; border-radius:20px; font-size:12px; font-weight:bold; cursor:pointer; box-shadow:0 2px 10px rgba(0,0,0,0.8);">
            ✕ सामान्य डिस्प्ले
        </button>

        <div style="width:85vw; max-width:380px; height:85vw; max-height:380px; background:#000; border:2px solid #00ff80; border-radius:14px; overflow:hidden; box-shadow:0 0 35px rgba(0,255,128,0.5); display:flex; align-items:center; justify-content:center;">
            {'<video id="khushiMediaZoom" src="' + khushi_video + '" loop muted playsinline style="width:100%; height:100%; object-fit:cover; object-position:center 15%;"></video>' if has_vid else '<img id="khushiMediaZoom" src="' + khushi_img + '" style="width:100%; height:100%; object-fit:cover; object-position:center 15%;" />'}
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

<audio id="elevenAudioPlayer" src="{last_audio}" preload="auto"></audio>

<script>
    const standardGrid = document.getElementById('standardGrid');
    const squareOverlay = document.getElementById('squareZoomOverlay');
    const micStatus = document.getElementById('micStatus');
    const micBtn = document.getElementById('micBtn');
    const liveVideo = document.getElementById('liveVideoFeed');
    const camBox = document.getElementById('inlineCamBox');
    const camPlaceholder = document.getElementById('camPlaceholderText');
    const camBtn = document.getElementById('camToggleBtn');
    const portraitFrame = document.getElementById('portraitFrame');
    const voiceWave = document.getElementById('voiceWave');
    const audioPlayer = document.getElementById('elevenAudioPlayer');
    
    const mNorm = document.getElementById('khushiMediaNormal');
    const mZoom = document.getElementById('khushiMediaZoom');

    let camStream = null;
    let audioCtx = null;
    let analyser = null;
    let animFrame = null;

    // Web Audio API द्वारा वास्तविक लिप-सिंक (वॉल्यूम व पिच के अनुसार चेहरे का हिलना)
    function setupAudioVisualSync(sourceNode) {{
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        sourceNode.connect(analyser);
        analyser.connect(audioCtx.destination);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function updateLipMotion() {{
            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for(let i=0; i<dataArray.length; i++) sum += dataArray[i];
            let avg = sum / dataArray.length;

            if (avg > 15) {{
                // आवाज़ के वॉल्यूम के अनुसार लाइव स्केल और टिल्ट (सच्चा लिप-मोशन)
                let scaleVal = 1 + (avg / 700);
                let rotateVal = (avg % 3 === 0) ? 0.7 : -0.7;
                portraitFrame.style.transform = `scale(${{scaleVal}}) rotate(${{rotateVal}}deg)`;
                portraitFrame.style.borderColor = '#00ff80';
                if (voiceWave) voiceWave.style.display = 'flex';
                if (mNorm && mNorm.tagName === 'VIDEO' && mNorm.paused) mNorm.play().catch(e=>{{}});
                if (mZoom && mZoom.tagName === 'VIDEO' && mZoom.paused) mZoom.play().catch(e=>{{}});
            }} else {{
                portraitFrame.style.transform = 'scale(1) rotate(0deg)';
                portraitFrame.style.borderColor = '#ff4b4b';
                if (voiceWave) voiceWave.style.display = 'none';
            }}

            animFrame = requestAnimationFrame(updateLipMotion);
        }}
        updateLipMotion();
    }}

    function stopLipMotion() {{
        if (animFrame) cancelAnimationFrame(animFrame);
        portraitFrame.style.transform = 'scale(1) rotate(0deg)';
        portraitFrame.style.borderColor = '#ff4b4b';
        if (voiceWave) voiceWave.style.display = 'none';
        if (mNorm && mNorm.tagName === 'VIDEO') mNorm.pause();
        if (mZoom && mZoom.tagName === 'VIDEO') mZoom.pause();
    }}

    // ऑटो-प्ले: या तो ElevenLabs AI आवाज़ या फिर फ़ॉलबैक न्यूरल आवाज़
    const elevenAudio = "{last_audio}";
    const fallbackText = "{clean_speak}";

    window.addEventListener('load', () => {{
        if (elevenAudio && elevenAudio.length > 50) {{
            // ElevenLabs AI Audio Play
            micStatus.innerText = "खुशी बोल रही है... (AI Voice) 🔊";
            audioPlayer.play().then(() => {{
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioCtx.createMediaElementSource(audioPlayer);
                setupAudioVisualSync(source);
            }}).catch(e => {{ playWebSpeechFallback(); }});

            audioPlayer.onended = () => {{
                stopLipMotion();
                micStatus.innerText = "माइक व स्पीकर एक्टिव";
            }};
        }} else if (fallbackText && fallbackText.length > 0) {{
            playWebSpeechFallback();
        }}
    }});

    function playWebSpeechFallback() {{
        const win = window.parent || window;
        if ('speechSynthesis' in win) {{
            win.speechSynthesis.cancel();
            const u = new win.SpeechSynthesisUtterance(fallbackText);
            u.lang = 'hi-IN';
            u.rate = 1.0;
            u.onstart = () => {{
                micStatus.innerText = "खुशी बोल रही है... 🔊";
                if (mNorm && mNorm.tagName === 'VIDEO') mNorm.play().catch(e=>{{}});
                if (mZoom && mZoom.tagName === 'VIDEO') mZoom.play().catch(e=>{{}});
                portraitFrame.style.borderColor = '#00ff80';
            }};
            u.onend = () => {{
                stopLipMotion();
                micStatus.innerText = "माइक व स्पीकर एक्टिव";
            }};
            win.speechSynthesis.speak(u);
        }}
    }}

    // 1. लाइव कैमरा
    async function toggleInternalCam() {{
        if (camStream) {{
            camStream.getTracks().forEach(track => track.stop());
            camStream = null;
            liveVideo.style.display = 'none';
            camPlaceholder.style.display = 'block';
            camPlaceholder.innerText = 'कैमरा स्टैंडबाय (OFF)';
            camBox.style.borderColor = '#2e3856';
            camBtn.style.background = '#221b0e';
            camBtn.style.color = '#facc15';
            camBtn.innerText = '📷 कैमरा on — off';
        }} else {{
            try {{
                camStream = await navigator.mediaDevices.getUserMedia({{
                    video: {{ facingMode: "user", width: {{ ideal: 320 }}, height: {{ ideal: 240 }} }},
                    audio: false
                }});
                liveVideo.srcObject = camStream;
                liveVideo.style.display = 'block';
                camPlaceholder.style.display = 'none';
                camBox.style.borderColor = '#00ff80';
                camBtn.style.background = '#0d2818';
                camBtn.style.color = '#00ff80';
                camBtn.innerText = '📷 कैमरा (LIVE ON)';
            }} catch(err) {{
                camPlaceholder.innerText = 'कैमरा अनुमति दें';
            }}
        }}
    }}

    // 2. मेमोरी साफ़
    function clearMemoryDirect() {{
        const url = new URL(window.parent.location.href);
        url.searchParams.set('action', 'clear');
        window.parent.location.href = url.toString();
    }}

    // 3. Zoom
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
        standardGrid.style.display = 'flex';
        const pDoc = window.parent.document;
        const cInp = pDoc.querySelector('div[data-testid="stChatInput"]');
        if (cInp) cInp.style.display = 'block';
        const cCard = pDoc.getElementById('chatAnswerContainer');
        if (cCard) cCard.style.display = 'block';
    }}

    // 4. Puss (तुरंत म्यूट)
    function pussSpeech() {{
        try {{
            if (audioPlayer) {{ audioPlayer.pause(); audioPlayer.currentTime = 0; }}
            const win = window.parent || window;
            if (win.speechSynthesis) win.speechSynthesis.cancel();
        }} catch(e) {{}}
        stopLipMotion();
        micStatus.innerText = 'शांत';
    }}

    // 5. वॉयस इंजन
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
                }}, 250);
            }}
        }};
        rec.onerror = () => {{ micBtn.style.background = "#ff4b4b"; micStatus.innerText = "माइक एरर"; }};
        rec.onend = () => {{ micBtn.style.background = "#ff4b4b"; }};
    }}

    function triggerMicVoice() {{
        // ऑडियो कॉन्टेक्स्ट को एक्टिव रखें (ब्राउज़र स्लीप न हो)
        try {{
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
        }} catch(e) {{}}

        if (rec) {{
            try {{ rec.start(); }} catch(e) {{ rec.stop(); setTimeout(() => rec.start(), 200); }}
        }}
    }}

    micBtn.onclick = triggerMicVoice;
</script>
""", height=385)

thinking_box = st.empty()

# 6. चैट संवाद व उत्तर कार्ड
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

# 7. सुपर-फास्ट Gemini 3.6 Flash इंजन
def ask_gemini(prompt):
    if not client:
        return "त्रुटि: GEMINI_API_KEY नहीं मिली।"
    
    models_to_try = ['gemini-3.6-flash', 'gemini-3.5-flash-lite']
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=PERSONA)
            )
            if res and res.text:
                return res.text
        except Exception:
            continue
            
    return "माफ़ कीजिए, सर्वर व्यस्त है। कृपया पुनः पूछें।"

# 8. चैट इनपुट
user_query = st.chat_input("यहाँ लिखें या ऊपर mike बटन दबाकर बोलें...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    thinking_box.markdown('<div class="thinking-badge">✨ खुशी सोच रही है... उत्तर आ रहा है ⚡</div>', unsafe_allow_html=True)
    
    ans = ask_gemini(user_query)
    st.session_state.messages.append({"role": "assistant", "content": ans})
    save_mem()
    
    # ElevenLabs ऑडियो फेच (यदि उपलब्ध हो)
    st.session_state.current_audio = get_elevenlabs_audio(ans)
    
    thinking_box.empty()
    st.rerun()
