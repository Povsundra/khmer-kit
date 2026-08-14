"""Dark chat theme — CSS injection for Streamlit."""

from __future__ import annotations

import streamlit as st

BG = "#161B22"
SURFACE = "#21262D"
SIDEBAR = "#0D1117"
PRIMARY = "#E05263"
PRIMARY_DIM = "#3D2228"
SECONDARY = "#3FB950"
TEXT = "#F0F6FC"
MUTED = "#8B949E"
BORDER = "#30363D"

CATEGORY_LABELS = {
    "samlor": "Samlor",
    "cha": "Cha",
    "dessert": "Dessert",
    "other": "Other",
}

CATEGORY_ICONS = {
    "samlor": "🍲",
    "cha": "🥘",
    "dessert": "🍮",
    "other": "🥗",
}


def inject_theme() -> None:
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Khmer:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
        :root {{
            --bg: {BG};
            --surface: {SURFACE};
            --sidebar: {SIDEBAR};
            --primary: {PRIMARY};
            --primary-dim: {PRIMARY_DIM};
            --secondary: {SECONDARY};
            --text: {TEXT};
            --muted: {MUTED};
            --border: {BORDER};
        }}
        .stApp {{
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Inter', system-ui, sans-serif;
        }}
        .khmer {{
            font-family: 'Noto Sans Khmer', 'Inter', sans-serif;
        }}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{
            background: var(--bg);
        }}
        /* View switcher (Chat / Browse / Recipe) must scroll with page content */
        .stApp .main div[data-testid="stRadio"] {{
            position: static !important;
            top: auto !important;
            bottom: auto !important;
        }}
        div[data-testid="stSidebar"] {{
            background-color: var(--sidebar);
            border-right: 1px solid var(--border);
        }}
        div[data-testid="stSidebar"] * {{
            color: var(--text);
        }}
        .sidebar-brand {{
            padding: 0.5rem 0 1.25rem 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1rem;
        }}
        .sidebar-brand h2 {{
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
            color: var(--text);
        }}
        .sidebar-brand p {{
            font-size: 0.78rem;
            color: var(--muted);
            margin: 0.25rem 0 0 0;
        }}
        .sidebar-section {{
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            margin: 1rem 0 0.5rem 0;
        }}
        .llm-status {{
            font-size: 0.8rem;
            color: var(--muted);
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }}
        .llm-status.connected {{ color: var(--secondary); }}
        .main-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.25rem;
        }}
        .main-header h3 {{
            margin: 0;
            font-size: 1.25rem;
            font-weight: 600;
        }}
        .main-header .sub {{
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 0.15rem;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        }}
        .card-preview {{
            background: #1A2028;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem 1.25rem;
            margin-top: 0.75rem;
        }}
        .card-preview-label {{
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 0.5rem;
        }}
        .tag {{
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 500;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            margin-right: 0.35rem;
            margin-top: 0.5rem;
        }}
        .tag-source {{
            background: rgba(63, 185, 80, 0.15);
            color: var(--secondary);
            border: 1px solid rgba(63, 185, 80, 0.3);
        }}
        .tag-intent {{
            background: rgba(224, 82, 99, 0.12);
            color: var(--primary);
            border: 1px solid rgba(224, 82, 99, 0.25);
        }}
        .tag-dish {{
            background: rgba(139, 148, 158, 0.15);
            color: var(--muted);
            border: 1px solid var(--border);
        }}
        .recipe-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
        }}
        .recipe-title-kh {{
            font-size: 0.95rem;
            color: var(--muted);
            margin-bottom: 0.5rem;
        }}
        .recipe-col h4 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted);
        }}
        .recipe-col ul, .recipe-col ol {{
            color: var(--text);
            font-size: 0.9rem;
            line-height: 1.55;
        }}
        .safety-banner {{
            background: rgba(224, 180, 0, 0.1);
            border: 1px solid rgba(224, 180, 0, 0.3);
            border-radius: 8px;
            padding: 0.6rem 0.9rem;
            font-size: 0.85rem;
            color: #E3B341;
            margin-bottom: 1rem;
        }}
        .source-footer {{
            font-size: 0.78rem;
            color: var(--muted);
            margin-top: 1rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border);
        }}
        .browse-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            cursor: pointer;
            transition: border-color 0.15s;
        }}
        .browse-card:hover {{
            border-color: var(--primary);
        }}
        .welcome-box {{
            background: var(--surface);
            border: 1px dashed var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            color: var(--muted);
            text-align: center;
        }}
        div[data-testid="stChatMessage"] {{
            background: transparent;
        }}
        div[data-testid="stChatMessageContent"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text);
        }}
        .stChatInput textarea {{
            background-color: var(--surface) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
        }}
        .stButton > button[kind="primary"] {{
            background-color: var(--primary);
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }}
        .stButton > button[kind="primary"]:hover {{
            background-color: #C94455;
        }}
        div[data-testid="stRadio"] label {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.35rem 0.75rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="sidebar-brand">
            <h2><span class="khmer">ម្ហូបខ្មែរ AI</span></h2>
            <p>Khmer Kitchen Companion</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
