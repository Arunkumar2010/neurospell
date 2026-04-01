import streamlit as st
import re
from spell_corrector import SpellCorrector
from context_model import ContextCorrector
import language_tool_python
import os

# ── CONFIGURATION ────────────────────
# Replace with your actual direct download URL for deployment
CORPUS_URL = "https://drive.google.com/uc?id=1wNfc6hBOxYBcXDBbvadkhpA9i2o1bGo7"
LOCAL_CORPUS = "data/corpus.txt"

# Must be FIRST before anything else (Streamlit requirement)
if "total_words" not in st.session_state:
    st.session_state.total_words = 0
if "errors_found" not in st.session_state:
    st.session_state.errors_found = 0
if "corrections_made" not in st.session_state:
    st.session_state.corrections_made = 0
if "accuracy" not in st.session_state:
    st.session_state.accuracy = 0.0
if "input_text" not in st.session_state:
    st.session_state.input_text = ""
if "history" not in st.session_state:
    # Ensure history keys are always correct
    st.session_state.history = []

st.set_page_config(
    page_title="NEURO·SPELL",
    page_icon="⬡",
    layout="wide"
)

# ── CSS & JS ANIMATED BACKGROUND ─────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Share+Tech+Mono&family=Rajdhani:wght@400;600&display=swap');

html, body, [class*="css"] {
    background: #050a14 !important;
    color: #c8d8f0 !important;
    font-family: 'Rajdhani', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background: #050a14 !important;
}

[data-testid="stHeader"] {
    background: rgba(5,10,20,0.8) !important;
    backdrop-filter: blur(10px);
}

/* Custom Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #050a14; }
::-webkit-scrollbar-thumb { background: #0d2844; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00c8ff; }

/* Cyberpunk Glows */
.stButton>button {
    background: transparent !important;
    color: #00c8ff !important;
    border: 1px solid #00c8ff !important;
    font-family: 'Orbitron', sans-serif !important;
    letter-spacing: 2px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
}

.stButton>button:hover {
    background: rgba(0,200,255,0.1) !important;
    box-shadow: 0 0 15px rgba(0,200,255,0.4);
    border-color: #00ff88 !important;
    color: #00ff88 !important;
}

.stTextArea textarea {
    background: #0a1628 !important;
    color: #c8d8f0 !important;
    border: 1px solid #0d2844 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 15px !important;
}

.flicker {
    animation: flicker 2s infinite;
}

@keyframes flicker {
    0% { opacity: 0.8; }
    50% { opacity: 1; }
    100% { opacity: 0.9; }
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}
.blink { animation: blink 1s infinite; }

/* ═══ ANIMATED BACKGROUND EL ═══ */
#particle-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
}

.scan-line {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #00c8ff40, #00c8ff, #00c8ff40, transparent);
    animation: scanMove 4s linear infinite;
    z-index: 1;
    pointer-events: none;
}

@keyframes scanMove {
    0%   { top: 0%; opacity: 1; }
    100% { top: 100%; opacity: 0.3; }
}

.cyber-grid {
    position: fixed;
    inset: 0;
    background-image: 
        linear-gradient(rgba(0,200,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,200,255,0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: 0;
    pointer-events: none;
}
</style>

<!-- Particle Canvas Layer -->
<canvas id="particle-canvas"></canvas>
<div class="scan-line"></div>
<div class="cyber-grid"></div>

<script>
const canvas = document.getElementById('particle-canvas');
if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    class Particle {
        constructor() {
            this.init();
        }
        init() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 1.5 + 0.5;
            this.speedX = Math.random() * 0.5 - 0.25;
            this.speedY = Math.random() * 0.5 - 0.25;
            this.color = Math.random() > 0.5 ? '#00c8ff' : '#00ff88';
            this.opacity = Math.random() * 0.5 + 0.1;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }
        draw() {
            ctx.globalAlpha = this.opacity;
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    for (let i = 0; i < 100; i++) particles.push(new Particle());

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            p.update();
            p.draw();
        });
        requestAnimationFrame(animate);
    }
    animate();
}
</script>
""", unsafe_allow_html=True)

# ── MODEL LOADING ────────────────────
@st.cache_resource
def load_all_models():
    # Detect corpus source (Local priority, URL fallback for deployment)
    corpus_source = LOCAL_CORPUS if os.path.exists(LOCAL_CORPUS) else CORPUS_URL
    
    # Primary engines
    corrector = SpellCorrector(corpus_source)
    analyzer = ContextCorrector()
    # Grammar engine
    try:
        grammar_tool = language_tool_python.LanguageTool('en-US')
    except Exception:
        grammar_tool = None
    return corrector, analyzer, grammar_tool

corrector, analyzer, grammar_tool = load_all_models()

# ── SIDEBAR METRICS ──────────────────
with st.sidebar:
    st.markdown("""
    <p style='font-family:Share Tech Mono,monospace;
    font-size:11px;color:#00c8ff;letter-spacing:3px;
    margin-bottom:20px;'>◈ CORRECTION STATS</p>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    col1.metric("WORDS", int(st.session_state.total_words))
    col2.metric("ERRORS", int(st.session_state.errors_found))
    col1.metric("FIXED", int(st.session_state.corrections_made))
    col2.metric("ACCURACY", f"{st.session_state.accuracy}%")
    
    st.markdown("<hr style='border: 0.1px solid #0d2844;'>", unsafe_allow_html=True)
    st.markdown("""
    <p style='font-family:Share Tech Mono,monospace;
    font-size:9px;color:#4a7a9b;letter-spacing:1px;'>
    ◈ ENGINE: DISTILBERT-BASE-UNCASED<br>
    ◈ CORPUS: 14M WORDS<br>
    ◈ MODES: STATISTICAL + NEURAL + GRAMMATICAL</p>
    """, unsafe_allow_html=True)

# ── MAIN TERMINAL ────────────────────
tab1, tab2 = st.tabs(["⬡  SPELL CORRECTOR", "◈  PROJECT ANALYSIS"])

# ════════════════════════════════════
# TAB 1 — ENGINE
# ════════════════════════════════════
with tab1:
    # Header UI
    st.markdown("""
    <div style='display:flex;align-items:center;gap:12px;
    padding:12px 0 20px 0;border-bottom:1px solid #0d2844;
    margin-bottom:24px;'>
      <div style='width:42px;height:42px;border:1.5px solid #00c8ff;
      border-radius:8px;display:flex;align-items:center;
      justify-content:center;font-size:20px;'>⬡</div>
      <div>
        <div style='font-family:Orbitron,monospace;font-size:18px;
        color:#00c8ff;letter-spacing:3px;'>NEURO·SPELL <span class="blink">_</span></div>
        <div style='font-family:Share Tech Mono,monospace;font-size:9px;
        color:#4a7a9b;letter-spacing:2px;'>
        CONTEXT-BASED CORRECTION SYSTEM v2.0</div>
      </div>
      <div class="flicker" style='margin-left:auto;font-family:Share Tech Mono,monospace;
      font-size:9px;color:#00ff88;border:1px solid #00ff8830;
      background:#00ff8808;padding:4px 10px;border-radius:3px;'>
      ● DISTILBERT ONLINE</div>
    </div>
    """, unsafe_allow_html=True)

    # File input
    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;letter-spacing:2px;margin-bottom:8px;'>◈ UPLOAD TERMINAL</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["txt"], key="file_upl", label_visibility="collapsed")

    if uploaded_file:
        content = uploaded_file.read().decode("utf-8").strip()
        if content and content != st.session_state.input_text:
            st.session_state.input_text = content
            st.rerun()

    # Main Input
    st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;letter-spacing:2px;margin:16px 0 8px;'>◈ INPUT MATRIX</p>", unsafe_allow_html=True)
    user_input = st.text_area(
        "",
        value=st.session_state.input_text,
        height=200,
        placeholder="Input text for neural diagnostic analysis...",
        label_visibility="collapsed"
    )
    
    # Live Sync
    if user_input != st.session_state.input_text:
        st.session_state.input_text = user_input

    # Toolbar
    col_check, col_clear = st.columns([4,1])
    with col_check:
        check = st.button("◈ CHECK & CORRECT MATRIX", use_container_width=True)
    with col_clear:
        if st.button("✕ CLEAR", use_container_width=True):
            st.session_state.input_text = ""
            st.rerun()

    # Live Stats Bar
    st.markdown(f"""
    <div style='display:flex;gap:20px;padding:10px 0;border-top:1px solid #0d2844;margin-top:10px;'>
      <span style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;'>◈ WORDS: <span style='color:#00c8ff;'>{len(user_input.split()) if user_input.strip() else 0}</span></span>
      <span style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;'>◈ CHARS: <span style='color:#00c8ff;'>{len(user_input)}</span></span>
    </div>
    """, unsafe_allow_html=True)

    # Correction Pipeline
    if check:
        if not user_input.strip():
            st.warning("⚠ ERROR: INPUT MATRIX EMPTY")
        else:
            with st.spinner("◈ ANALYZING SEMANTIC VECTORS..."):
                # Use regex split to preserve whitespace and punctuation for exact reconstructed output
                tokens = re.split(r'(\s+)', user_input)
                corrections = []
                # corrected_tokens will contain the final word or spacing
                corrected_tokens = []
                
                # Words list for context awareness (strip spacing)
                words = [t for t in tokens if t and not t.isspace()]
                word_indices = [i for i, t in enumerate(tokens) if t and not t.isspace()]
                
                for i, token in enumerate(tokens):
                    if not token or token.isspace():
                        corrected_tokens.append((token, token, False, "SPACE"))
                        continue
                        
                    # Extract alphanumeric core for checking
                    clean = re.sub(r'[^\w\s]', '', token)
                    p_start = re.search(r'^[^\w]+', token)
                    p_end = re.search(r'[^\w]+$', token)
                    ps = p_start.group() if p_start else ""
                    pe = p_end.group() if p_end else ""
                    
                    if not clean:
                        corrected_tokens.append((token, token, False, "PUNCT"))
                        continue

                    # 1. Statistical Layer (Non-word)
                    result = corrector.get_correction(clean)

                    if result is None:
                        corrected_tokens.append((f"{ps}{clean}{pe}", f"{ps}{clean}{pe}", False, "UNKNOWN"))
                        continue

                    stat_corr, stat_conf, is_non_word = result
                    
                    final_corr = clean
                    error_type = None
                    conf = 100
                    expl = ""

                    if is_non_word:
                        final_corr = stat_corr
                        error_type = "NON-WORD"
                        conf = int(stat_conf * 100)
                        expl = f"'{clean}' unknown. Matrix suggests '{stat_corr}'."
                    else:
                        # 2. Neural Layer (Contextual)
                        # We need the relative index in the 'words' list
                        w_idx = word_indices.index(i)
                        neural_pred, neural_conf, is_real_error = analyzer.check_context(words, w_idx)
                        if is_real_error:
                            final_corr = neural_pred
                            error_type = "REAL-WORD"
                            conf = int(neural_conf * 100)
                            expl = f"Context mismatch. Neural engine suggests '{neural_pred}'."

                    changed = (error_type is not None)
                    corrected_tokens.append((f"{ps}{clean}{pe}", f"{ps}{final_corr}{pe}", changed, error_type))
                    
                    if changed:
                        corrections.append({
                            "original": clean,
                            "corrected": final_corr,
                            "type": error_type,
                            "confidence": conf,
                            "explanation": expl
                        })

                # Layer 3: Grammar Rule Analysis
                grammar_matches = grammar_tool.check(user_input) if grammar_tool else []
                
                # Global Stats
                total_w = len(words)
                fixed_e = len(corrections)
                st.session_state.total_words = total_w
                st.session_state.errors_found = fixed_e
                st.session_state.corrections_made = fixed_e
                st.session_state.accuracy = round(((total_w - fixed_e)/total_w)*100, 1) if total_w > 0 else 0.0

            # ── RESULT UI ──
            st.markdown("<hr style='border:0.5px solid #00c8ff20;margin:30px 0;'>", unsafe_allow_html=True)
            l_col, r_col = st.columns(2)
            
            with l_col:
                st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;letter-spacing:2px;margin-bottom:8px;'>◈ ORIGINAL MATRIX</p>", unsafe_allow_html=True)
                orig_html = "<div style='background:#0a1628;border:1px solid #0d2844;border-radius:8px;padding:16px;max-height:300px;overflow-y:auto;font-size:14px;white-space:pre-wrap;'>"
                for o, c, ch, etype in corrected_tokens:
                    if ch:
                        color = "#ff4444" if etype == "NON-WORD" else "#7b2fff"
                        orig_html += f"<span style='color:{color};text-decoration:underline wavy {color};'>{o}</span>"
                    else:
                        orig_html += f"<span>{o}</span>"
                orig_html += "</div>"
                st.markdown(orig_html, unsafe_allow_html=True)

            with r_col:
                st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:10px;color:#00ff88;letter-spacing:2px;margin-bottom:8px;'>◈ NEURAL RECONSTRUCTION</p>", unsafe_allow_html=True)
                corr_html = "<div style='background:#0a1628;border:1px solid #00ff8820;border-radius:8px;padding:16px;max-height:300px;overflow-y:auto;font-size:14px;white-space:pre-wrap;'>"
                for o, c, ch, etype in corrected_tokens:
                    if ch:
                        corr_html += f"<span style='color:#00ff88;font-weight:600;'>{c}</span>"
                    else:
                        corr_html += f"<span>{c}</span>"
                corr_html += "</div>"
                st.markdown(corr_html, unsafe_allow_html=True)

            # Accept / Copy
            final_text = "".join([c for o, c, ch, et in corrected_tokens])
            col_acc, col_cp = st.columns(2)
            with col_acc:
                if st.button("◈ ACCEPT MATRIX CORRECTIONS", use_container_width=True):
                    st.session_state.input_text = final_text
                    st.rerun()
            with col_cp:
                st.markdown(f"""
                <button onclick="navigator.clipboard.writeText(`{final_text}`)" style='width:100%;background:transparent;border:1px solid #00c8ff;color:#00c8ff;font-family:Orbitron,monospace;font-size:10px;padding:8.5px;border-radius:4px;cursor:pointer;'>◈ COPY TO CLIPBOARD</button>
                """, unsafe_allow_html=True)

            # Diagnostic Cards
            st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;letter-spacing:2px;margin:24px 0 12px;'>◈ DIAGNOSTIC REPORTS</p>", unsafe_allow_html=True)
            
            for c in corrections:
                color = "#ff4444" if c["type"] == "NON-WORD" else "#7b2fff"
                st.markdown(f"""
                <div style='background:#0a1628;border:1px solid #0d2844;border-left:3px solid {color};border-radius:8px;padding:16px;margin-bottom:10px;'>
                  <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div><span style='color:#ff4444;text-decoration:line-through;'>{c["original"]}</span> → <span style='color:#00ff88;font-weight:600;'>{c["corrected"]}</span></div>
                    <span style='font-size:9px;background:{color}20;color:{color};padding:2px 8px;border-radius:3px;font-family:Share Tech Mono,monospace;'>{c["type"]}</span>
                  </div>
                  <div style='font-size:11px;color:#4a7a9b;margin-top:6px;'>{c["explanation"]} | {c["confidence"]}% CONF</div>
                </div>
                """, unsafe_allow_html=True)

            for g in grammar_matches:
                st.markdown(f"""
                <div style='background:#0a1628;border:1px solid #0d2844;border-left:3px solid #f0a500;border-radius:8px;padding:16px;margin-bottom:10px;'>
                  <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div style='color:#f0a500;font-size:11px;font-family:Share Tech Mono,monospace;'>◈ GRAMMAR: {g.message}</div>
                    <span style='font-size:9px;background:#f0a50020;color:#f0a500;padding:2px 8px;border-radius:3px;font-family:Share Tech Mono,monospace;'>SYNTAX</span>
                  </div>
                  <div style='font-size:11px;color:#4a7a9b;margin-top:6px;'>Suggestion: <span style='color:#f0a500;'>{", ".join(g.replacements[:2])}</span></div>
                </div>
                """, unsafe_allow_html=True)

            if not corrections and not grammar_matches:
                st.success("✓ TERMINAL CLEAR: NO ANOMALIES DETECTED")

            # History update (Safe dictionary keys)
            st.session_state.history.insert(0, {"orig": user_input[:40], "corr": final_text[:40], "err": fixed_e})
            st.session_state.history = st.session_state.history[:5]

    # Persistent History Display (Resilient Keys)
    if st.session_state.history:
        st.markdown("<hr style='border:0.1px solid #0d2844;margin:20px 0;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-family:Share Tech Mono,monospace;font-size:10px;color:#4a7a9b;letter-spacing:2px;margin-bottom:8px;'>◈ LOG HISTORY</p>", unsafe_allow_html=True)
        for i, h in enumerate(st.session_state.history):
            h_err = h.get('err', 0)
            h_orig = h.get('orig', '---')
            h_corr = h.get('corr', '---')
            with st.expander(f"Session {i+1} — {h_err} issues resolved"):
                st.markdown(f"<div style='font-family:Share Tech Mono,monospace;font-size:11px;'>INPUT: {h_orig}...<br>OUTPUT: {h_corr}...</div>", unsafe_allow_html=True)

# TAB 2 — PROJECT INFO
with tab2:
    st.markdown("""
    <div style='padding:20px 0'>
      <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;'>
        <div style='background:#0a1628;border:1px solid #00c8ff20;padding:20px;border-radius:12px;'>
          <p style='color:#00c8ff;font-family:Orbitron;font-size:12px;'>LAYER 1: STATISTICAL</p>
          <p style='font-size:11px;color:#4a7a9b;'>Non-word detection using N-gram probabilities and a 14M word reference corpus.</p>
        </div>
        <div style='background:#0a1628;border:1px solid #7b2fff20;padding:20px;border-radius:12px;'>
          <p style='color:#7b2fff;font-family:Orbitron;font-size:12px;'>LAYER 2: NEURAL</p>
          <p style='font-size:11px;color:#4a7a9b;'>BERT Transformers analyze semantic vectors to detect real-word contextual errors.</p>
        </div>
        <div style='background:#0a1628;border:1px solid #f0a50020;padding:20px;border-radius:12px;'>
          <p style='color:#f0a500;font-family:Orbitron;font-size:12px;'>LAYER 3: SYNTACTIC</p>
          <p style='font-size:11px;color:#4a7a9b;'>LanguageTool rule-engine integration for grammar and punctuation diagnostics.</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
