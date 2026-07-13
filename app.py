import streamlit as st

st.set_page_config(
    page_title="DCF Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #0f1117;
    }

    section[data-testid="stSidebar"] {
        background-color: #161b27;
        border-right: 1px solid #1e2535;
    }

    section[data-testid="stSidebar"] .stMarkdown p {
        color: #8892a4;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }

    .main-header {
        font-size: 1.9rem;
        font-weight: 700;
        color: #f0f4ff;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }

    .sub-header {
        font-size: 0.9rem;
        color: #5a6478;
        margin-bottom: 2rem;
        font-weight: 400;
    }

    .step-card {
        background: #161b27;
        border: 1px solid #1e2535;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.2s;
    }

    .step-card:hover {
        border-color: #2e7df7;
    }

    .step-number {
        font-size: 0.7rem;
        font-weight: 700;
        color: #2e7df7;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.4rem;
    }

    .step-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #e8edf5;
        margin-bottom: 0.4rem;
    }

    .step-desc {
        font-size: 0.85rem;
        color: #5a6478;
        line-height: 1.6;
    }

    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }

    .badge-done {
        background: #0d2b1a;
        color: #22c55e;
        border: 1px solid #16572e;
    }

    .badge-active {
        background: #0c1f3d;
        color: #2e7df7;
        border: 1px solid #1a3a6e;
    }

    .badge-waiting {
        background: #1a1e2a;
        color: #5a6478;
        border: 1px solid #252b3a;
    }

    .metric-card {
        background: #161b27;
        border: 1px solid #1e2535;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
    }

    .metric-label {
        font-size: 0.72rem;
        color: #5a6478;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f0f4ff;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.02em;
    }

    .metric-delta {
        font-size: 0.75rem;
        margin-top: 0.2rem;
    }

    .delta-up { color: #22c55e; }
    .delta-down { color: #ef4444; }
    .delta-neutral { color: #5a6478; }

    .stButton > button {
        background: #2e7df7;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        font-size: 0.85rem;
        font-family: 'Inter', sans-serif;
        transition: background 0.2s;
        cursor: pointer;
    }

    .stButton > button:hover {
        background: #1a6ae0;
    }

    div[data-testid="stNumberInput"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stSelectbox"] label {
        color: #8892a4;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    .nav-item {
        padding: 0.5rem 0.8rem;
        border-radius: 8px;
        margin-bottom: 0.2rem;
        cursor: pointer;
        font-size: 0.88rem;
        font-weight: 500;
        color: #8892a4;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .nav-item.active {
        background: #0c1f3d;
        color: #2e7df7;
    }

    .divider {
        border: none;
        border-top: 1px solid #1e2535;
        margin: 1.5rem 0;
    }

    .info-box {
        background: #0c1f3d;
        border: 1px solid #1a3a6e;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-size: 0.84rem;
        color: #8cb4ff;
        line-height: 1.6;
    }

    .warning-box {
        background: #1f1600;
        border: 1px solid #3d2e00;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        font-size: 0.84rem;
        color: #f59e0b;
        line-height: 1.6;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th {
        background: #1e2535;
        color: #8892a4;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.6rem 0.8rem;
        text-align: left;
        font-weight: 600;
    }

    td {
        color: #c8d0e0;
        font-size: 0.86rem;
        padding: 0.6rem 0.8rem;
        border-bottom: 1px solid #1e2535;
        font-family: 'JetBrains Mono', monospace;
    }

    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #161b27; }

    .highlight-row td {
        color: #2e7df7;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #161b27;
        border-radius: 10px;
        padding: 0.3rem;
        gap: 0.2rem;
        border: 1px solid #1e2535;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #5a6478;
        border-radius: 8px;
        padding: 0.4rem 1rem;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: #0c1f3d !important;
        color: #2e7df7 !important;
    }

    footer { display: none; }
    #MainMenu { display: none; }
    header { display: none; }
</style>
""", unsafe_allow_html=True)


def main():
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 📊 DCF Analyzer")
        st.markdown("---")

        pages = {
            "🏠  Home": "home",
            "📄  Upload 10-K": "upload",
            "🔍  Data Preview": "preview",
            "📈  DCF Model": "dcf",
        }

        if "page" not in st.session_state:
            st.session_state.page = "home"

        for label, key in pages.items():
            # Determine if clickable
            disabled = False
            if key == "preview" and not st.session_state.get("financials"):
                disabled = True
            if key == "dcf" and not st.session_state.get("confirmed"):
                disabled = True

            if not disabled:
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key
                    st.rerun()
            else:
                st.button(label, key=f"nav_{key}", disabled=True, use_container_width=True)

        st.markdown("---")

        # Progress indicators
        st.markdown("**Progress**")
        steps = [
            ("API Key", bool(st.session_state.get("api_key"))),
            ("10-K Uploaded", bool(st.session_state.get("financials"))),
            ("Data Confirmed", bool(st.session_state.get("confirmed"))),
            ("DCF Ready", bool(st.session_state.get("confirmed"))),
        ]
        for step_name, done in steps:
            icon = "✅" if done else "⬜"
            st.markdown(f"{icon} {step_name}")

        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.72rem;color:#3a4055;'>Built with Claude API · Streamlit</div>",
            unsafe_allow_html=True
        )

    # Route pages
    page = st.session_state.get("page", "home")

    if page == "home":
        from pages_content import home_page
        home_page()
    elif page == "upload":
        from pages_content import upload_page
        upload_page()
    elif page == "preview":
        from pages_content import preview_page
        preview_page()
    elif page == "dcf":
        from pages_content import dcf_page
        dcf_page()


if __name__ == "__main__":
    main()
