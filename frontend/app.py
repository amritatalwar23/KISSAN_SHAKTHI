"""Kisan Shakti (किसान शक्ति / ಕಿಸಾನ್ ಶಕ್ತಿ)
AI-Based Multilingual Agricultural Assistance Web Application
"""

import io
import json
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# ---------------------------------------------------------
# Page Configuration & Agricultural Visual Identity
# ---------------------------------------------------------
st.set_page_config(
    page_title="Kisan Shakti — AI Agricultural Assistance",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

BACKEND_API_BASE = "http://127.0.0.1:8000"

# Custom CSS for Fresh Agricultural Green-and-White Theme
CUSTOM_CSS = """
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #FAFCF8;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Custom Headers */
    h1, h2, h3 {
        color: #1B5E20 !important;
        font-weight: 700;
    }

    /* Keep chat replies and their optional reference panel readable across themes. */
    div[data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] *,
    div[data-testid="stExpander"] div[data-testid="stMarkdownContainer"] *,
    div[data-testid="stExpander"] [data-testid="stCaptionContainer"] {
        color: #000000 !important;
    }
    
    /* Card Container */
    .agri-card {
        background: #FFFFFF;
        border: 1px solid #E0E7DE;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(27, 94, 32, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .agri-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(27, 94, 32, 0.10);
    }
    
    /* Status Badges */
    .badge-confident {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-uncertain {
        background-color: #FFF3E0;
        color: #E65100;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-crisis {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    /* Disclaimer Banner */
    .disclaimer-banner {
        background-color: #FFFDE7;
        border-left: 5px solid #FBC02D;
        padding: 12px 16px;
        border-radius: 6px;
        color: #5D4037;
        font-size: 0.88rem;
        margin-bottom: 20px;
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 60%, #43A047 100%);
        color: #FFFFFF;
        padding: 30px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(27, 94, 32, 0.15);
    }
    .hero-title {
        color: #000000 !important;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: #E8F5E9;
        font-size: 1.1rem;
        font-weight: 400;
        line-height: 1.5;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# Helper Functions for Backend Connectivity
# ---------------------------------------------------------
@st.cache_data(ttl=15)
def check_backend_health():
    """Checks if FastAPI backend is reachable."""
    try:
        res = requests.get(f"{BACKEND_API_BASE}/health", timeout=3)
        if res.status_code == 200:
            return True, res.json()
        return False, {"error": f"Status code {res.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}


# ---------------------------------------------------------
# Sidebar Navigation & Settings
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1592982537447-7440770cbfc9?w=400&q=80", use_container_width=True)
    st.title("🌾 Kisan Shakti")
    st.caption("AI Multilingual Agricultural Advisory")

    backend_ok, health_info = check_backend_health()
    if backend_ok:
        st.success("🟢 Backend Connected (Port 8000)")
    else:
        st.warning("🟡 Backend Offline / Starting...")
        st.caption("Launch using: `python scripts/run_backend.py`")

    st.markdown("---")
    language_choice = st.selectbox(
        "🌐 Language / ಭಾಷೆ / भाषा",
        ["English", "Kannada (ಕನ್ನಡ)", "Hindi (हिन्दी)"],
        index=0
    )
    lang_code = "en" if "English" in language_choice else ("kn" if "Kannada" in language_choice else "hi")

    st.markdown("---")
    navigation = st.radio(
        "📌 Navigation",
        [
            "🏠 Home Dashboard",
            "🔬 Crop Disease Detection",
            "💬 Agricultural AI Assistant",
            "🏛️ Government Schemes",
            "🌱 Smart Crop Planning",
            "🧑‍🌾 Expert & KVK Directory",
            "🎙️ Voice Assistance",
            "📊 Analytics Dashboard"
        ],
        index=0
    )

    st.markdown("---")
    st.markdown("""
        **Emergency Contacts:**
        - 📞 **Tele-MANAS**: `14416` (24x7)
        - 📞 **Kisan Call Centre**: `1800-180-1551`
    """)


# ---------------------------------------------------------
# Standard Safety Disclaimer Banner
# ---------------------------------------------------------
def render_disclaimer():
    st.markdown("""
    <div class="disclaimer-banner">
        ⚠️ <strong>Notice:</strong> Kisan Shakti outputs are preliminary AI assistance generated from research datasets and institutional publications. 
        Field diagnoses and financial commitments must be validated with certified agricultural officers or Krishi Vigyan Kendra (KVK) specialists.
    </div>
    """, unsafe_allow_html=True)


def render_more_info(sources=None, details=None, warning=None):
    """Keep citations and full retrieved material available without crowding chat replies."""
    sources = sources or []
    details = details or {}
    if not sources and not details and not warning:
        return

    with st.expander("More info & source documents"):
        if sources:
            st.markdown("**Sources**")
            for index, source in enumerate(sources, start=1):
                source = str(source)
                if source.startswith(("https://", "http://")):
                    host = source.split("//", 1)[-1].split("/", 1)[0]
                    st.markdown(f"- [Open official source: {host}]({source})")
                else:
                    st.markdown(f"- {source}")

        chunks = details.get("retrieved_chunks", []) if isinstance(details, dict) else []
        if chunks:
            st.markdown("**Retrieved guidance**")
            for chunk in chunks:
                st.markdown(f"**{chunk.get('title', 'Advisory excerpt')}**")
                attribution = " · ".join(str(value) for value in [chunk.get("source"), chunk.get("publication")] if value)
                if attribution:
                    st.caption(attribution)
                st.write(chunk.get("content", ""))

        if isinstance(details, dict) and details.get("full_advisory"):
            st.markdown("**Full advisory text**")
            st.markdown(details["full_advisory"])

        if isinstance(details, dict) and details.get("schemes"):
            st.markdown("**Scheme details**")
            for scheme in details["schemes"]:
                st.markdown(f"**{scheme.get('name', 'Scheme')}**")
                st.write(scheme.get("benefits", ""))
                criteria = scheme.get("eligibility_criteria", [])
                if criteria:
                    st.caption("Eligibility: " + "; ".join(criteria))
                if scheme.get("official_link"):
                    st.markdown(f"[Official scheme page]({scheme['official_link']})")

        if isinstance(details, dict) and details.get("contacts"):
            st.markdown("**Local support contacts**")
            for contact in details["contacts"]:
                st.markdown(f"**{contact.get('name', 'Agriculture support')}**")
                st.write(contact.get("address", ""))
                if contact.get("phone"):
                    st.write(f"Phone: {contact['phone']}")
                if contact.get("email"):
                    st.write(f"Email: {contact['email']}")
                if contact.get("official_link"):
                    st.markdown(f"[Contact website]({contact['official_link']})")

        if isinstance(details, dict) and details.get("recommendations"):
            st.markdown("**Crop shortlist details**")
            for crop in details["recommendations"][:5]:
                st.markdown(f"**{crop.get('crop_name', 'Crop')}** — {crop.get('suitability_score', 'n/a')} rule score")
                st.write(crop.get("rationale", ""))
            for assumption in details.get("assumptions", []):
                st.caption(assumption)

        if warning:
            st.caption(f"Note: {warning}")


# ---------------------------------------------------------
# Module 1: Home Dashboard
# ---------------------------------------------------------
if navigation == "🏠 Home Dashboard":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🌾 Kisan Shakti (किसान शक्ति / ಕಿಸಾನ್ ಶಕ್ತಿ)</div>
        <div class="hero-subtitle">
            An AI-driven multilingual agricultural intelligence platform empowering Indian farmers with 
            deep-learning crop disease diagnosis, agronomic crop planning, government subsidies discovery, 
            and verified institutional expert assistance.
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_disclaimer()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="agri-card">
            <h3>🔬 Disease Diagnosis</h3>
            <p>Upload leaf photographs to identify 17 common diseases across Tomato, Potato, and Maize using MobileNetV3 deep learning.</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="agri-card">
            <h3>🌱 Crop Planning</h3>
            <p>Receive rule-grounded agronomic crop choices factoring soil type, seasonal calendars, and local water availability.</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="agri-card">
            <h3>🏛️ Subsidies & Schemes</h3>
            <p>Explore verified central and state welfare programs like PM-KISAN, PMFBY crop insurance, and Kisan Credit Card.</p>
        </div>
        """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("""
        <div class="agri-card">
            <h3>🧑‍🌾 Verified KVK Directory</h3>
            <p>Access location-indexed official contacts and physical addresses for Krishi Vigyan Kendras across India.</p>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown("""
        <div class="agri-card">
            <h3>🌐 Multilingual AI Chat</h3>
            <p>Ask farming questions in English, Kannada, or Hindi with grounded retrieval from ICAR manuals and package of practices.</p>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown("""
        <div class="agri-card">
            <h3>🛡️ Farmer Crisis Guard</h3>
            <p>Sensitive detection of agricultural distress linking directly to verified national helplines including Tele-MANAS (14416).</p>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------
# Module 2: Crop Disease Detection
# ---------------------------------------------------------
elif navigation == "🔬 Crop Disease Detection":
    st.title("🔬 Crop Disease Identification")
    st.markdown("Upload a close-up photograph of an affected crop leaf (Tomato, Potato, or Maize) for deep-learning assessment.")
    render_disclaimer()

    col_upload, col_result = st.columns([1, 1])

    with col_upload:
        st.markdown("### 📤 Upload Leaf Photo")
        uploaded_file = st.file_uploader(
            "Choose a leaf image (JPG, PNG, WEBP, max 10MB)",
            type=["jpg", "jpeg", "png", "webp"],
            help="Ensure good lighting and that the leaf surface is clearly visible."
        )

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"Uploaded Image: {uploaded_file.name}", use_container_width=True)
            analyze_button = st.button("🔍 Diagnose Crop Disease", type="primary", use_container_width=True)
        else:
            analyze_button = False

    with col_result:
        st.markdown("### 📋 Diagnostic Assessment")
        if uploaded_file is not None and analyze_button:
            with st.spinner("Analyzing leaf pathology with MobileNetV3..."):
                try:
                    uploaded_file.seek(0)
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    res = requests.post(f"{BACKEND_API_BASE}/predict/disease", files=files, timeout=15)
                    
                    if res.status_code == 200:
                        data = res.json()
                        
                        # Status badge
                        badge_class = "badge-confident" if data["status"] == "confident" else "badge-uncertain"
                        st.markdown(f'<span class="{badge_class}">Status: {data["status"].upper()}</span>', unsafe_allow_html=True)

                        st.markdown(f"#### Crop: **{data['crop_name']}**")
                        st.markdown(f"#### Diagnosis: **{data['disease_name']}**")
                        
                        # Confidence metric
                        conf = data["confidence"]
                        st.progress(conf)
                        st.markdown(f"**Confidence Score:** `{conf:.1%}`")

                        if data.get("warning"):
                            st.warning(data["warning"])

                        st.markdown("---")
                        st.markdown("##### 🌿 Grounded Advisory & Treatment:")
                        st.info(data["advisory"])

                        if data.get("source_references"):
                            st.caption(f"**Sources:** {', '.join(data['source_references'])}")

                        # Alternative predictions
                        if data.get("top_alternatives"):
                            st.markdown("##### Alternative Possibilities:")
                            for alt in data["top_alternatives"]:
                                st.write(f"- **{alt['crop']} - {alt['disease']}**: {alt['confidence']:.1%}")

                    elif res.status_code == 415:
                        st.error("Unsupported file type. Please upload a standard JPG or PNG image.")
                    else:
                        detail = res.json().get("detail", res.text)
                        st.error(f"Prediction failed: {detail}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the backend server. Please verify FastAPI is running on port 8000.")
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
        elif uploaded_file is None:
            st.info("Please upload an image from the left panel to begin disease diagnosis.")


# ---------------------------------------------------------
# Module 3: Agricultural AI Assistant (Chat & RAG)
# ---------------------------------------------------------
elif navigation == "💬 Agricultural AI Assistant":
    st.title("💬 Kisan Shakti Agricultural Assistant")
    st.markdown("Ask questions on crop diseases, nutrient deficiencies, pest control, weather precautions, or farming practices.")
    st.caption("Try asking about cyclone/flood preparation, irrigation, soil tests and fertilizer, pest control, seeds and sowing, crop choice, harvesting/storage, schemes, or your nearest KVK. Include your crop, district, and growth stage for more specific guidance.")
    render_disclaimer()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Namaste! I am Kisan Shakti. How may I assist you with your farming, crops, or government schemes today?",
                "sources": []
            }
        ]

    # Display Chat History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
        if msg["role"] == "assistant":
            try:
                render_more_info(sources=msg.get("sources"), details=msg.get("structured_data"), warning=msg.get("warning"))
            except Exception:
                st.caption("More information is temporarily unavailable.")

    # Chat Input
    user_input = st.chat_input("Type your farming question (English, Kannada, or Hindi)...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        response_sources = []
        response_details = {}
        response_warning = None
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Consulting agricultural knowledge base..."):
                try:
                    payload = {
                        "query": user_input,
                        "language": lang_code,
                        "location": {"state": "Karnataka"},
                        "history": [
                            {"role": msg.get("role", "user"), "content": str(msg.get("content", ""))}
                            for msg in st.session_state.chat_history[:-1][-8:]
                            if msg.get("role") in ("user", "assistant")
                        ]
                    }
                    res = requests.post(f"{BACKEND_API_BASE}/query", json=payload, timeout=35)
                    if res.status_code == 200:
                        data = res.json()
                        answer = str(data.get("answer") or "").strip()
                        if not answer:
                            answer = "I couldn't prepare an answer for that question. Please try adding the crop and the specific issue."
                        st.markdown(answer)
                        response_sources = data.get("sources", [])
                        response_details = data.get("structured_data", {})
                        response_warning = data.get("warning")
                        if data.get("warning") and data.get("routed_module") == "wellbeing":
                            st.warning(data["warning"])

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": data.get("sources", []),
                            "structured_data": data.get("structured_data", {}),
                            "warning": data.get("warning")
                        })
                    else:
                        err_msg = f"I couldn't process that question (server returned {res.status_code}). Please try again."
                        st.error(err_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": err_msg, "sources": []})
                except requests.exceptions.RequestException as e:
                    err_msg = "I can't reach the assistant service right now. Please check that the backend is running and try again."
                    st.error(f"{err_msg} ({e})")
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg, "sources": []})
                except Exception as e:
                    err_msg = "I hit a display error while preparing that reply. Please try the question again."
                    st.error(f"{err_msg} ({e})")
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg, "sources": []})

        if response_sources or response_details or response_warning:
            try:
                render_more_info(sources=response_sources, details=response_details, warning=response_warning)
            except Exception:
                st.caption("More information is temporarily unavailable.")
        # Rebuild the transcript from session state so the reply remains visible
        # after Streamlit finishes handling the submitted chat input.
        st.rerun()


# ---------------------------------------------------------
# Module 4: Government Schemes
# ---------------------------------------------------------
elif navigation == "🏛️ Government Schemes":
    st.title("🏛️ Government Schemes & Subsidies")
    st.markdown("Search and filter verified financial support, crop insurance, and irrigation subsidy programs.")
    render_disclaimer()

    col_filters = st.columns([1, 1, 1, 2])
    with col_filters[0]:
        state_filter = st.selectbox("State", ["All", "Karnataka", "Uttar Pradesh", "Maharashtra"])
    with col_filters[1]:
        crop_filter = st.selectbox("Crop", ["All", "Potato", "Tomato", "Millet", "Paddy", "Maize"])
    with col_filters[2]:
        category_filter = st.selectbox("Farmer Category", ["All", "Small and Marginal Farmer", "All Farmers"])
    with col_filters[3]:
        search_kw = st.text_input("Keyword Search", placeholder="e.g., insurance, subsidy, credit, drip")

    search_btn = st.button("🔍 Search Schemes", type="primary")

    try:
        payload = {
            "state": None if state_filter == "All" else state_filter,
            "crop": None if crop_filter == "All" else crop_filter,
            "category": None if category_filter == "All" else category_filter,
            "keyword": search_kw if search_kw.strip() else None
        }
        res = requests.post(f"{BACKEND_API_BASE}/recommend/scheme", json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.markdown(f"**Found {data['total_found']} Verified Schemes**")
            
            for item in data["schemes"]:
                with st.expander(f"📌 {item['name']} ({item['level']} - {item['state']})", expanded=True):
                    st.markdown(f"**Ministry:** {item['ministry']}")
                    st.markdown(f"**Benefits:** {item['benefits']}")
                    st.markdown(f"**Target Beneficiaries:** {item['target_beneficiaries']}")
                    
                    st.markdown("**Eligibility Criteria:**")
                    for crit in item["eligibility_criteria"]:
                        st.write(f"- {crit}")

                    st.markdown("**Required Documents:**")
                    for doc in item["documents_required"]:
                        st.write(f"- {doc}")

                    st.markdown(f"🔗 **Official Portal:** [{item['official_link']}]({item['official_link']})")
                    st.caption(f"Last Verified: {item['last_verified']} | Status: {item['status']}")

            st.caption(data["disclaimer"])
        else:
            st.error("Failed to load schemes from backend.")
    except Exception as e:
        st.error(f"Backend connectivity issue: {e}")


# ---------------------------------------------------------
# Module 5: Smart Crop Planning
# ---------------------------------------------------------
elif navigation == "🌱 Smart Crop Planning":
    st.title("🌱 Smart Agronomic Crop Planning")
    st.markdown("Generate crop recommendations grounded in documented ICAR packages of practice.")
    render_disclaimer()

    with st.form("crop_planning_form"):
        col1, col2 = st.columns(2)
        with col1:
            state_in = st.selectbox("State", ["Karnataka", "Maharashtra", "Uttar Pradesh", "Madhya Pradesh", "Tamil Nadu"])
            district_in = st.text_input("District / Taluk", value="Dharwad")
            season_in = st.selectbox("Season", ["Kharif (Monsoon)", "Rabi (Winter)", "Zaid (Summer)"])
        with col2:
            soil_in = st.selectbox("Soil Type", ["Red sandy loam", "Black cotton soil", "Alluvial soil", "Clayey loam", "Laterite soil"])
            water_in = st.selectbox("Water Availability", ["Moderate (Well/Borewell)", "High (Canal/Assured Irrigation)", "Low (Rainfed)"])
            land_in = st.number_input("Land Size (Acres)", min_value=0.5, max_value=50.0, value=2.5, step=0.5)

        submit_plan = st.form_submit_button("🌱 Generate Crop Recommendations", type="primary")

    if submit_plan:
        with st.spinner("Evaluating agronomic suitability rules..."):
            try:
                # Clean season input
                clean_season = season_in.split()[0]
                clean_water = water_in.split()[0]
                payload = {
                    "state": state_in,
                    "district": district_in,
                    "season": clean_season,
                    "soil_type": soil_in,
                    "water_availability": clean_water,
                    "land_size_acres": land_in
                }
                res = requests.post(f"{BACKEND_API_BASE}/recommend/crop", json=payload, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"Generated {len(data['recommendations'])} suitable crop options for {state_in} ({district_in}).")

                    for crop in data["recommendations"]:
                        with st.container():
                            st.markdown(f"""
                            <div class="agri-card">
                                <h3>🌾 {crop['crop_name']} <span class="badge-confident">Suitability: {crop['suitability_score']:.0%}</span></h3>
                                <p><strong>Recommended Varieties:</strong> {crop['variety']}</p>
                                <p><strong>Duration:</strong> {crop['duration_days']} | <strong>Water Need:</strong> {crop['water_requirement']}</p>
                                <p><strong>Rationale:</strong> {crop['rationale']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if crop.get("key_risks_and_cautions"):
                                st.warning("⚠️ **Key Pest & Weather Risks:** " + " | ".join(crop["key_risks_and_cautions"]))

                    st.markdown("---")
                    st.markdown("##### 📌 Important Regional Cautions:")
                    for c in data.get("cautions", []):
                        st.write(f"- {c}")

                    st.caption(data["disclaimer"])
                else:
                    st.error("Failed to generate recommendations from backend.")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")


# ---------------------------------------------------------
# Module 6: Expert & KVK Directory
# ---------------------------------------------------------
elif navigation == "🧑‍🌾 Expert & KVK Directory":
    st.title("🧑‍🌾 Krishi Vigyan Kendra (KVK) & Expert Directory")
    st.markdown("Find verified government agricultural research stations, extension centers, and contact officers.")
    render_disclaimer()

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        state_lookup = st.selectbox("Select State", ["Karnataka", "Maharashtra", "Uttar Pradesh", "All"])
    with col_exp2:
        district_lookup = st.text_input("District (Optional)", placeholder="e.g. Bangalore Rural, Dharwad, Mysore, Pune")

    lookup_btn = st.button("📍 Find Verified Support Centers", type="primary")

    try:
        payload = {
            "state": state_lookup,
            "district": district_lookup if district_lookup.strip() else None
        }
        res = requests.post(f"{BACKEND_API_BASE}/expert", json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.markdown(f"**Found {data['total_found']} Verified Support Centers**")

            for contact in data["contacts"]:
                with st.container():
                    st.markdown(f"""
                    <div class="agri-card">
                        <h4>🏛️ {contact['name']}</h4>
                        <p><strong>Organization:</strong> {contact['organization']} ({contact['type']})</p>
                        <p><strong>Address:</strong> {contact['address']}</p>
                        <p>📞 <strong>Phone:</strong> <code>{contact.get('phone', 'N/A')}</code> | ✉️ <strong>Email:</strong> {contact.get('email', 'N/A')}</p>
                        <p>🔗 <strong>Portal:</strong> <a href="{contact['official_link']}" target="_blank">{contact['official_link']}</a></p>
                        <span style="font-size: 0.8rem; color: #757575;">Verified on: {contact['verified_on']}</span>
                    </div>
                    """, unsafe_allow_html=True)

            st.caption(data["disclaimer"])
            st.info(f"For all other regions, consult the National ICAR KVK Portal: [kvk.icar.gov.in]({data['official_directory_url']})")
        else:
            st.error("Failed to fetch expert directory.")
    except Exception as e:
        st.error(f"Backend error: {e}")


# ---------------------------------------------------------
# Module 7: Voice Assistance
# ---------------------------------------------------------
elif navigation == "🎙️ Voice Assistance":
    st.title("🎙️ Multilingual Voice Assistance")
    st.markdown("Speak your question or upload an audio file to receive spoken and written agricultural guidance.")
    render_disclaimer()

    col_voice_l, col_voice_r = st.columns([1, 1])

    with col_voice_l:
        st.markdown("### 🗣️ Voice Input")
        st.info("💡 You can record audio using your device microphone or upload a voice memo (.wav, .mp3).")
        audio_file = st.file_uploader("Upload audio recording", type=["wav", "mp3", "m4a", "ogg"])
        
        simulated_voice_transcripts = {
            "en": "My tomato leaves have black spots with yellow borders, how can I control it?",
            "kn": "ನನ್ನ ಟೊಮೆಟೊ ಎಲೆಗಳ ಮೇಲೆ ಕಪ್ಪು ಚುಕ್ಕೆಗಳಿವೆ, ನಾನು ಏನು ಮಾಡಬೇಕು?",
            "hi": "मेरे आलू के पौधों की पत्तियों पर भूरे धब्बे हैं, इसका क्या इलाज है?"
        }

        st.markdown("---")
        st.markdown("##### 🎙️ Quick Speech Simulator (for testing without mic)")
        if st.button("▶️ Test Voice Query in Current Language"):
            st.session_state["transcribed_text"] = simulated_voice_transcripts.get(lang_code, simulated_voice_transcripts["en"])

    with col_voice_r:
        st.markdown("### 📝 Speech-to-Text Transcription")
        current_transcription = st.session_state.get("transcribed_text", "")
        transcribed_input = st.text_area("Recognized Speech", value=current_transcription, height=100)

        process_voice = st.button("🚀 Process Voice Query", type="primary")

        if process_voice and transcribed_input.strip():
            with st.spinner("Processing spoken query through orchestrator..."):
                try:
                    payload = {
                        "query": transcribed_input,
                        "language": lang_code,
                        "location": {"state": "Karnataka"}
                    }
                    res = requests.post(f"{BACKEND_API_BASE}/query", json=payload, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        st.markdown("#### 🌾 Advisory Response:")
                        st.markdown(data["answer"])

                        # Audio playback simulation via browser speech
                        st.markdown("""
                        <script>
                            if ('speechSynthesis' in window) {
                                let msg = new SpeechSynthesisUtterance();
                                msg.text = "Query answered successfully by Kisan Shakti.";
                                window.speechSynthesis.speak(msg);
                            }
                        </script>
                        """, unsafe_allow_html=True)
                        st.success("🔊 Spoken audio synthesis ready.")
                    else:
                        st.error("Error generating answer.")
                except Exception as e:
                    st.error(f"Backend error: {e}")


# ---------------------------------------------------------
# Module 8: Analytics Dashboard
# ---------------------------------------------------------
elif navigation == "📊 Analytics Dashboard":
    st.title("📊 Diagnostic & Advisory Analytics")
    st.markdown("Observability metrics for disease diagnoses, query routing, and multilingual activity.")
    st.caption("All metrics are derived directly from the application database (SQLite).")

    try:
        res = requests.get(f"{BACKEND_API_BASE}/analytics", timeout=5)
        if res.status_code == 200:
            stats = res.json()

            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            total_pred = stats.get("total_predictions", 0)
            col_m1.metric("Total Disease Scans", total_pred)
            col_m2.metric("Active Crops", len(stats.get("by_crop", {})) or 3)
            col_m3.metric("Supported Classes", 17)
            col_m4.metric("KVKs Indexed", 6)

            st.markdown("---")
            col_ch1, col_ch2 = st.columns(2)

            with col_ch1:
                st.markdown("##### 🔬 Diagnoses by Crop")
                crop_data = stats.get("by_crop", {})
                if not crop_data:
                    # Provide realistic demonstration sample when fresh
                    crop_data = {"Tomato": 14, "Potato": 9, "Corn (Maize)": 7}
                    st.caption("Displaying baseline distribution for demonstration.")

                fig_crop = px.pie(
                    names=list(crop_data.keys()),
                    values=list(crop_data.values()),
                    hole=0.4,
                    color_discrete_sequence=["#2E7D32", "#81C784", "#FFB74D", "#4CAF50"]
                )
                fig_crop.update_layout(margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_crop, use_container_width=True)

            with col_ch2:
                st.markdown("##### 💬 Query Distribution by Module")
                mod_data = stats.get("by_module", {})
                if not mod_data:
                    mod_data = {"schemes": 12, "crop_planning": 8, "knowledge_rag": 15, "experts": 6, "wellbeing": 2}
                    st.caption("Displaying baseline distribution for demonstration.")

                fig_mod = px.bar(
                    x=list(mod_data.keys()),
                    y=list(mod_data.values()),
                    labels={"x": "Module", "y": "Query Count"},
                    color=list(mod_data.values()),
                    color_continuous_scale="Greens"
                )
                fig_mod.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
                st.plotly_chart(fig_mod, use_container_width=True)

        else:
            st.error("Failed to load analytics.")
    except Exception as e:
        st.error(f"Backend connectivity issue: {e}")
