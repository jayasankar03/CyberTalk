
import json
import os
from datetime import datetime, timezone, timedelta
import time

import requests
import streamlit as st
from streamlit_cookies_controller import CookieController

import re
from io import BytesIO
from xml.sax.saxutils import escape

from pathlib import Path

import base64

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)

# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="CyberTalk",
    page_icon="""
    <svg width="76" height="84" viewBox="0 0 100 110"
        xmlns="http://www.w3.org/2000/svg">
        <path d="M50 5 L91 22 L85 67 Q76 91 50 104
                Q24 91 15 67 L9 22 Z"
            fill="#102F4B"
            stroke="#19C9F4"
            stroke-width="4"/>
        <path d="M50 16 L79 29 L74 65 Q67 83 50 94
                Q33 83 26 65 L21 29 Z"
            fill="#0878D1"
            fill-opacity="0.35"/>
        <path d="M32 42 H68 M32 68 H68"
            stroke="#16D9F5" stroke-width="2"/>
        <text x="50" y="62" fill="#FFFFFF"
            font-size="25" font-weight="bold"
            text-anchor="middle">CT</text>
        </svg>
    """.strip(),
    layout="wide",
)
# -----------------------------
# Load CyberTalk global styles
# -----------------------------

CSS_FILE = Path(__file__).resolve().parent / "styles" / "cybertalk.css"

if CSS_FILE.exists():
    st.markdown(
        f"<style>{CSS_FILE.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
# -----------------------------
# CyberTalk Custom UI Theme
# -----------------------------

st.markdown(
    """
    <style>

    /* Refined dark cybersecurity background */
    .stApp {
        background: linear-gradient(
            135deg,
            #050b14 0%,
            #0a1625 50%,
            #07111d 100%
        );
        color: #eaf2ff;
    }

    /* Main content area */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #0b192c,
            #10243d
        );
        border-right: 1px solid #263e5c;
    }

    /* Headings */
    h1, h2, h3 {
        color: #eaf2ff !important;
        font-weight: 700 !important;
    }

    /* Paragraphs */
    p, label, .stMarkdown {
        color: #d1deef;
    }

    /* Buttons */
    .stButton > button,
    .stFormSubmitButton > button {
        background: linear-gradient(
            90deg,
            #0878d1,
            #13a5d9
        );
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 600;
        transition: 0.2s ease;
    }

    .stButton > button:hover,
    .stFormSubmitButton > button:hover {
        background: linear-gradient(
            90deg,
            #0965ad,
            #087fc0
        );
        color: white;
        border: none;
    }

    /* Input fields */
    .stTextInput input,
    .stTextArea textarea {
        background-color: #142a43;
        color: white;
        border: 1px solid #34516f;
        border-radius: 8px;
    }

    /* Dividers */
    hr {
        border-color: #34516f;
    }

    /* Expanders */
    [data-testid="stExpander"] {
        background-color: #10243b;
        border: 1px solid #294663;
        border-radius: 10px;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #122a44;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #294663;
    }
    /* Compact three-dot conversation menu button */
    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button {
        background: transparent !important;
        background-image: none !important;
        color: #d1deef !important;

        border: none !important;
        box-shadow: none !important;
        border-radius: 6px !important;

        width: 32px !important;
        min-width: 32px !important;
        max-width: 32px !important;

        height: 32px !important;
        min-height: 32px !important;

        padding: 0 !important;

        font-size: 16px !important;
        font-weight: 500 !important;
        line-height: 1 !important;
    }

    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button * {
        font-size: 16px !important;
        line-height: 1 !important;
    }

    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button:hover {
        background: #203b58 !important;
        color: #19c9f4 !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* ChatGPT-inspired conversation history rows */
    [data-testid="stSidebar"] [class*="st-key-history_title_"] button {
        background: transparent !important;
        background-image: none !important;
        color: #d1deef !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        min-height: 38px !important;
        height: auto !important;
        padding: 7px 10px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        overflow: hidden !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
    }

    [data-testid="stSidebar"] [class*="st-key-history_title_"] button:hover {
        background: #20334a !important;
        color: #f4f7fb !important;
        border-color: transparent !important;
    }

    [data-testid="stSidebar"] [class*="st-key-history_menu_icon_wrapper_"] {
        margin-top: -1px;
    }

    /* Centered delete confirmation dialog */
    [data-testid="stDialog"] {
        background: #10243d;
        border: 1px solid #34516f;
        border-radius: 14px;
    }
    /* About page hero section */
    .about-hero {
        text-align: center;
        padding: 48px 24px;
        margin: 20px 0 32px 0;
        background: linear-gradient(
            135deg,
            #0c1b2d,
            #102943
        );
        border: 1px solid #234663;
        border-radius: 16px;
    }

    .about-eyebrow {
        color: #19c9f4;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 3px;
        margin-bottom: 16px;
    }

    .about-hero h1 {
        color: #f0f6ff;
        font-size: 38px;
        font-weight: 750;
        margin-bottom: 16px;
    }

    .about-hero p {
        color: #b8c9dc;
        font-size: 16px;
        line-height: 1.8;
        max-width: 760px;
        margin: auto;
    }

    /* About page feature cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
        margin: 20px 0 30px 0;
    }

    .feature-card {
        background: #0c1b2b;
        border: 1px solid #203d57;
        border-radius: 12px;
        padding: 22px;
    }

    .feature-card h3 {
        color: #eaf2ff;
        font-size: 18px;
        margin-bottom: 10px;
    }

    .feature-card p {
        color: #aebfd2;
        font-size: 14px;
        line-height: 1.7;
        margin-bottom: 0;
    }

    .feature-number {
        color: #19c9f4;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 12px;
    }

    /* Landing page authentication button */
    [class*="st-key-landing_sign_in_button"] button {
        min-height: 44px;
        border-radius: 9px;
        font-weight: 700;
    }

    /* Responsive feature layout */
    @media (max-width: 700px) {
        .feature-grid {
            grid-template-columns: 1fr;
        }

        .about-hero {
            padding: 32px 16px;
        }

        .about-hero h1 {
            font-size: 28px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# -----------------------------
# CyberTalk Brand Logo
# -----------------------------


def render_cybertalk_logo():
    """Render the original CyberTalk CT shield logo."""

    logo_col, title_col = st.columns(
        [0.7, 7],
        gap="small",
        vertical_alignment="center",
    )

    with logo_col:
        st.components.v1.html(
            """
            <svg width="76" height="84" viewBox="0 0 100 110"
                 xmlns="http://www.w3.org/2000/svg">
                <path d="M50 5 L91 22 L85 67 Q76 91 50 104
                         Q24 91 15 67 L9 22 Z"
                      fill="#102F4B"
                      stroke="#19C9F4"
                      stroke-width="4"/>
                <path d="M50 16 L79 29 L74 65 Q67 83 50 94
                         Q33 83 26 65 L21 29 Z"
                      fill="#0878D1"
                      fill-opacity="0.35"/>
                <path d="M32 42 H68 M32 68 H68"
                      stroke="#16D9F5" stroke-width="2"/>
                <text x="50" y="62" fill="#FFFFFF"
                      font-size="25" font-weight="bold"
                      text-anchor="middle">CT</text>
            </svg>
            """,
            height=120,
            scrolling=False,
        )

    with title_col:
        st.title("CyberTalk", anchor=False)

API_URL = os.getenv(
    "CYBERTALK_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# -----------------------------
# Authentication
# -----------------------------

AUTH_COOKIE_NAME = "cybertalk_access_token"

cookie_controller = CookieController(
    key="cybertalk_auth_cookies"
)

st.session_state.setdefault("access_token", None)


def clear_authentication():

    """Clear both Streamlit and browser authentication state."""

    st.session_state["access_token"] = None

    try:
        cookie_value = cookie_controller.get(AUTH_COOKIE_NAME)

        if cookie_value is not None:
            cookie_controller.remove(AUTH_COOKIE_NAME)

    except (TypeError, AttributeError):
        # The cookie controller may not have browser cookie data
        # available during Streamlit testing.
        pass

    st.session_state.pop("qa_result", None)
    st.session_state.pop("cybertalk_result", None)


def get_api_error(response):
    """Extract a readable error message from an API response."""
    try:
        return response.json().get("detail", response.text)
    except (ValueError, AttributeError):
        return response.text


def get_auth_headers():
    """Return the authentication header for the current user."""
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"}

def fetch_admin_audit_logs():
    """Retrieve administrator audit records."""
    return requests.get(
        f"{API_URL}/admin/audit-logs",
        headers=get_auth_headers(),
        timeout=15,
    )

def format_audit_timestamp(value):
    """Convert an API audit timestamp from UTC to Indian Standard Time."""
    if not value:
        return "N/A"

    try:
        timestamp = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        # SQLite timestamps may arrive without timezone information.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        ist = timezone(timedelta(hours=5, minutes=30))

        return timestamp.astimezone(ist).strftime(
            "%d %b %Y, %I:%M:%S %p IST"
        )

    except (ValueError, TypeError, AttributeError):
        return str(value)

def fetch_admin_users(search=""):
    """Retrieve users through the protected administrator API."""
    params = {"search": search} if search.strip() else None

    return requests.get(
        f"{API_URL}/admin/users",
        headers=get_auth_headers(),
        params=params,
        timeout=15,
    )


def fetch_admin_user_details(user_id):
    """Retrieve one user's safe account details."""
    return requests.get(
        f"{API_URL}/admin/users/{user_id}",
        headers=get_auth_headers(),
        timeout=15,
    )


def update_admin_user_role(user_id, role):
    """Update another user's role through the protected API."""
    return requests.patch(
        f"{API_URL}/admin/users/{user_id}/role",
        headers=get_auth_headers(),
        json={"role": role},
        timeout=15,
    )

def deactivate_admin_user(user_id):
    """Deactivate a user account through the admin API."""

    try:
        response = requests.patch(
            f"{API_URL}/admin/users/{user_id}/deactivate",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.status_code == 200:
            return True, response.json().get(
                "message",
                "User account deactivated successfully.",
            )

        try:
            detail = response.json().get("detail", "Unable to deactivate account.")
        except ValueError:
            detail = "Unable to deactivate account."

        return False, detail

    except requests.RequestException:
        return False, "Unable to connect to the CyberTalk API."


def reactivate_admin_user(user_id):
    """Reactivate a previously deactivated user account."""

    try:
        response = requests.patch(
            f"{API_URL}/admin/users/{user_id}/reactivate",
            headers=get_auth_headers(),
            timeout=10,
        )

        if response.status_code == 200:
            return True, response.json().get(
                "message",
                "User account reactivated successfully.",
            )

        try:
            detail = response.json().get("detail", "Unable to reactivate account.")
        except ValueError:
            detail = "Unable to reactivate account."

        return False, detail

    except requests.RequestException:
        return False, "Unable to connect to the CyberTalk API."

# -----------------------------
# Chat history helper functions
# -----------------------------

def save_chat_history(conversation_type, title, content):
    """Save a conversation for the authenticated user."""

    response = requests.post(
        f"{API_URL}/history",
        headers=get_auth_headers(),
        json={
            "conversation_type": conversation_type,
            "title": title,
            "content": json.dumps(content, ensure_ascii=False),
        },
        timeout=30,
    )

    return response


def fetch_chat_history():
    """Retrieve the authenticated user's conversations."""

    return requests.get(
        f"{API_URL}/history",
        headers=get_auth_headers(),
        timeout=15,
    )


def fetch_single_chat_history(history_id):
    """Retrieve one saved conversation."""

    return requests.get(
        f"{API_URL}/history/{history_id}",
        headers=get_auth_headers(),
        timeout=15,
    )

def build_conversation_text(title, conversation_type, content):
    """Format a saved Q&A or stakeholder dialogue as readable text."""

    lines = [
        "CYBERTALK — CONVERSATION EXPORT",
        "=" * 55,
        f"Title: {title}",
        f"Type: {'Cybersecurity Q&A' if conversation_type == 'qa' else 'Stakeholder Dialogue'}",
        "",
    ]

    if conversation_type == "qa":
        lines.extend([
            "QUESTION",
            "-" * 55,
            str(content.get("question", "Not available")),
            "",
            "ANSWER",
            "-" * 55,
            str(content.get("answer", "Not available")),
        ])

    elif conversation_type == "dialogue":
        lines.extend([
            "DISCUSSION DETAILS",
            "-" * 55,
            f"Topic: {content.get('topic', title)}",
            f"Rounds: {content.get('rounds', 'Not available')}",
        ])

        stakeholders = content.get("stakeholders", [])
        if stakeholders:
            names = [
                str(item.get("name", "Unknown stakeholder"))
                for item in stakeholders
            ]
            lines.append("Stakeholders: " + " and ".join(names))

        lines.extend([
            "",
            "STAKEHOLDER DIALOGUE",
            "-" * 55,
        ])

        dialogue = content.get("dialogue", [])

        for entry in dialogue:
            lines.extend([
                f"Turn {entry.get('turn', '?')} — "
                f"{entry.get('speaker', 'Unknown stakeholder')}",
                str(entry.get("message", "")),
                "",
            ])


        agreement = content.get("agreement", {})

        if not isinstance(agreement, dict):
            agreement = {}

        status_labels = {
            "agreement_reached": "Agreement reached",
            "partial_agreement": "Partial agreement",
            "no_agreement": "No agreement",
        }

        status = str(agreement.get("status") or "unknown")

        explanation = agreement.get("explanation")

        if not isinstance(explanation, str) or not explanation.strip():
            explanation = "Not provided"

        lines.extend([
            "FINAL AGREEMENT EVALUATION",
            "-" * 55,
            f"Status: {status_labels.get(status, status.replace('_', ' ').title())}",
            "",
            "Explanation:",
            explanation,
            "",
            "Shared decision:",
        ])

        shared_decision = agreement.get("shared_decision")

        if isinstance(shared_decision, str) and shared_decision.strip():
            lines.append(shared_decision)
        else:
            lines.append("No confirmed shared decision.")

        lines.extend([
            "",
            "Unresolved disagreements:",
        ])

        unresolved = agreement.get("unresolved_disagreements", [])

        if isinstance(unresolved, str):
            unresolved_items = [unresolved] if unresolved.strip() else []

        elif isinstance(unresolved, list):
            unresolved_items = [
                str(item).strip()
                for item in unresolved
                if item is not None and str(item).strip()
            ]

        else:
            unresolved_items = []

        if unresolved_items:
            lines.extend(f"- {item}" for item in unresolved_items)
        else:
            lines.append("None reported.")

        lines.extend([
            "",
            "Recommended next actions:",
        ])

        next_actions = agreement.get("next_actions", [])

        if isinstance(next_actions, str):
            action_items = [next_actions] if next_actions.strip() else []

        elif isinstance(next_actions, list):
            action_items = [
                str(item).strip()
                for item in next_actions
                if item is not None and str(item).strip()
            ]

        else:
            action_items = []

        if action_items:
            lines.extend(
                f"{index}. {action}"
                for index, action in enumerate(action_items, start=1)
            )
        else:
            lines.append("None specified.")


    else:
        lines.append("Conversation content is unavailable.")

    lines.extend([
        "",
        "=" * 55,
        "Generated by CyberTalk",
    ])

    return "\n".join(lines)


def build_conversation_pdf(title, conversation_type, content):
    """Create a readable PDF export of a saved conversation."""

    text_content = build_conversation_text(
        title,
        conversation_type,
        content,
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"CyberTalk - {title}",
        author="CyberTalk",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CyberTalkTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=16,
    )

    heading_style = ParagraphStyle(
        "CyberTalkHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#17365D"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "CyberTalkBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        spaceAfter=5,
        splitLongWords=True,
    )

    story = []

    for index, line in enumerate(text_content.splitlines()):
        if index == 0:
            story.append(Paragraph(escape(line), title_style))

        elif line and set(line) == {"="}:
            story.append(Spacer(1, 5))

        elif line and set(line) == {"-"}:
            story.append(Spacer(1, 3))

        elif line and line.isupper() and len(line) < 60:
            story.append(Paragraph(escape(line), heading_style))

        elif line:
            story.append(
                Paragraph(
                    escape(line).replace("\n", "<br/>"),
                    body_style,
                )
            )

        else:
            story.append(Spacer(1, 5))

    document.build(story)

    return buffer.getvalue()


def build_conversation_filename(title, extension):
    """Create a safe filename from a conversation title."""

    safe_title = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        str(title),
    ).strip("._")

    if not safe_title:
        safe_title = "conversation"

    return f"{safe_title}.{extension}"

def delete_chat_history(history_id):
    """Delete one conversation belonging to the current user."""

    return requests.delete(
        f"{API_URL}/history/{history_id}",
        headers=get_auth_headers(),
        timeout=15,
    )

def delete_all_chat_history():
    """Delete all conversations belonging to the current user."""

    return requests.delete(
        f"{API_URL}/history",
        headers=get_auth_headers(),
        timeout=30,
    )


@st.dialog("Delete all conversations?")
def show_delete_all_confirmation():
    """Confirm and delete all conversations for the current user."""

    st.warning(
        "You are about to permanently delete all your saved conversations."
    )

    st.caption(
        "This action cannot be undone. Other users' conversations "
        "will not be affected."
    )

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button(
            "Delete All",
            key="confirm_delete_all_chats",
            type="primary",
            use_container_width=True,
        ):
            try:
                response = delete_all_chat_history()

                if response.ok:
                    result = response.json()
                    deleted_count = result.get("deleted_count", 0)

                    st.session_state["delete_all_success"] = (
                        deleted_count
                    )

                    # Clear any conversation currently displayed.
                    st.session_state.pop("qa_result", None)
                    st.session_state.pop("cybertalk_result", None)

                    # Clear history-related UI state.
                    for key in list(st.session_state.keys()):
                        if (
                            key.startswith("show_history_menu_")
                        ):
                            st.session_state.pop(key, None)

                    st.rerun()

                else:
                    st.error(get_api_error(response))

            except requests.exceptions.RequestException:
                st.error("Could not connect to the API. Please try again.")

    with cancel_col:
        if st.button(
            "Cancel",
            key="cancel_delete_all_chats",
            use_container_width=True,
        ):
            st.rerun()

def rename_chat_history(history_id, new_title):
    """Rename one conversation belonging to the current user."""

    return requests.put(
        f"{API_URL}/history/{history_id}",
        headers=get_auth_headers(),
        json={"title": new_title},
        timeout=15,
    )

def create_share_link(history_id, expires_in_days=None):
    """Create a shareable link for an owned conversation."""

    payload = {}

    if expires_in_days is not None:
        payload["expires_in_days"] = expires_in_days

    return requests.post(
        f"{API_URL}/history/{history_id}/share",
        headers=get_auth_headers(),
        json=payload,
        timeout=15,
    )


def revoke_share_link(history_id, share_id):
    """Revoke a shareable link for an owned conversation."""

    return requests.delete(
        f"{API_URL}/history/{history_id}/share/{share_id}",
        headers=get_auth_headers(),
        timeout=15,
    )


# -----------------------------
# Verify current user session
# -----------------------------

current_user = None

if st.session_state.get("access_token"):

    try:
        profile_response = requests.get(
            f"{API_URL}/users/me",
            headers=get_auth_headers(),
            timeout=15,
        )

        if profile_response.status_code == 401:
            clear_authentication()

            st.session_state.pop("qa_result", None)
            st.session_state.pop("cybertalk_result", None)

            st.warning(
                "Your session has expired. Please log in again."
            )

        elif not profile_response.ok:
            st.error(
                "Could not verify your account: "
                f"{get_api_error(profile_response)}"
            )
            st.stop()

        else:
            current_user = profile_response.json()

    except requests.exceptions.RequestException:
        st.error(
            "Could not connect to the CyberTalk API. "
            f"Make sure FastAPI is running at {API_URL}."
        )
        st.stop()


# -----------------------------
# Login and registration
# -----------------------------

if not st.session_state.get("access_token"):

    # -------------------------
    # Password reset confirmation
    # -------------------------

    reset_token = st.query_params.get("token", "")

    if reset_token:

        st.title("Reset Your Password")

        st.write(
            "Enter your new password to regain access to CyberTalk."
        )

        with st.form("password_reset_confirm_form"):

            new_reset_password = st.text_input(
                "New Password",
                type="password",
                max_chars=128,
            )

            confirm_reset_password = st.text_input(
                "Confirm New Password",
                type="password",
                max_chars=128,
            )

            reset_submitted = st.form_submit_button(
                "Reset Password",
                type="primary",
                use_container_width=True,
            )

        if reset_submitted:

            if not new_reset_password or not confirm_reset_password:

                st.error("Please complete both password fields.")

            elif len(new_reset_password) < 8:

                st.error(
                    "Password must contain at least 8 characters."
                )

            elif new_reset_password != confirm_reset_password:

                st.error("Passwords do not match.")

            else:

                try:
                    with st.spinner("Updating your password..."):

                        reset_response = requests.post(
                            f"{API_URL}/password-reset/confirm",
                            json={
                                "token": reset_token,
                                "new_password": new_reset_password,
                            },
                            timeout=30,
                        )

                    if reset_response.ok:

                        st.query_params.clear()

                        st.success(
                            "Password reset successful! "
                            "You can now sign in with your new password."
                        )

                    else:

                        st.error(
                            "Password reset failed: "
                            f"{get_api_error(reset_response)}"
                        )

                except requests.exceptions.RequestException as exc:

                    st.error(
                        f"Could not connect to the API: {exc}"
                    )

        st.stop()
    # -------------------------
    # About Page and Authentication Modal
    # -------------------------

    if "show_auth_dialog" not in st.session_state:
        st.session_state["show_auth_dialog"] = False

    if "auth_modal_view" not in st.session_state:
        st.session_state["auth_modal_view"] = "signin"

    def open_auth_dialog():
        st.session_state["show_auth_dialog"] = True
        st.session_state["auth_modal_view"] = "signin"

    def close_auth_dialog():
        st.session_state["show_auth_dialog"] = False
        st.session_state["auth_modal_view"] = "signin"

    def open_forgot_password():
        st.session_state["auth_modal_view"] = "forgot"

    def open_create_account():
        st.session_state["auth_modal_view"] = "signup"

    def return_to_sign_in():
        st.session_state["auth_modal_view"] = "signin"

    # -------------------------
    # About CyberTalk Landing Page
    # -------------------------

    # Top navigation: original logo on the left, authentication on the right.
    header_column, auth_column = st.columns(
        [8, 1.5],
        vertical_alignment="center",
    )

    with header_column:
        render_cybertalk_logo()

    with auth_column:
        st.button(
            "Sign In",
            key="landing_sign_in_button",
            type="primary",
            use_container_width=True,
            on_click=open_auth_dialog,
        )

    # Hero section
    st.markdown(
        """
        <div class="about-hero">
            <div class="about-eyebrow">
                CYBERSECURITY DECISION SUPPORT
            </div>
            <h1>Two Chatbots, One Agreement</h1>
            <p>
                Explore complex cybersecurity challenges through
                AI-powered discussions between two stakeholders
                with different professional perspectives.
                Compare viewpoints, evaluate decisions, and
                discover a shared path forward.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # About section
    st.header("About CyberTalk")

    st.write(
        """
        CyberTalk is a Generative AI-powered cybersecurity
        discussion platform.

        It brings together two user-defined stakeholders with
        different professional responsibilities to examine
        cybersecurity challenges.

        Through structured AI-generated conversations, CyberTalk
        explores competing perspectives and evaluates whether
        stakeholders reach a shared decision, partially agree,
        or maintain unresolved disagreements.
        """
    )

    # Application features
    st.header("Explore CyberTalk")

    feature_cards = """
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-number">01 / DISCUSS</div>
            <h3>Stakeholder Dialogue</h3>
            <p>
                Create structured conversations between
                two stakeholders using your own professional
                roles and responsibilities.
            </p>
        </div>

        <div class ="feature-card">
            <div class="feature-number">02 / LEARN</div>
            <h3>Cybersecurity Q&amp;A</h3>
            <p>
                Ask cybersecurity-related questions and
                receive AI-generated explanations and
                practical guidance.
            </p>
        </div>

        <div class="feature-card">
            <div class="feature-number">03 / EVALUATE</div>
            <h3>Agreement Evaluation</h3>
            <p>
                Understand whether stakeholders agree,
                partially agree, or disagree, with
                explanations and recommended next actions.
            </p>
        </div>

        <div class="feature-card">
            <div class="feature-number">04 / MANAGE</div>
            <h3>Conversation History</h3>
            <p>
                Save, revisit, rename, share, and download
                your previous cybersecurity conversations.
            </p>
        </div>

        <div class="feature-card">
            <div class="feature-number">05 / CONFIGURE</div>
            <h3>Configurable Discussions</h3>
            <p>
                Select between one and five discussion
                rounds based on the complexity of your topic.
            </p>
        </div>
    </div>
    """

    st.html(feature_cards)

    # How it works
    st.header("How It Works")

    st.markdown(
        """
        1. Enter a cybersecurity discussion topic.
        2. Define two different stakeholder roles.
        3. Select the number of discussion rounds.
        4. Generate the AI-powered stakeholder conversation.
        5. Review the final agreement and recommended actions.
        """
    )

    st.divider()

    # Technology stack
    st.header("Technology Behind CyberTalk")

    st.markdown(
        """
        <div style="
            background:#0c1b2b;
            border:1px solid #203d57;
            border-radius:12px;
            padding:22px;
            text-align:center;
            color:#b8c9dc;
            line-height:2.2;
        ">
            Python &nbsp; | &nbsp;
            FastAPI &nbsp; | &nbsp;
            Streamlit &nbsp; | &nbsp;
            Ollama &nbsp; | &nbsp;
            Llama 3.2 &nbsp; | &nbsp;
            SQLAlchemy &nbsp; | &nbsp;
            SQLite &nbsp; | &nbsp;
            Pydantic
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Footer
    st.markdown(
        """
        <div style="
            text-align:center;
            padding:35px 10px 15px 10px;
            color:#8195ab;
            font-size:13px;
        ">
            CyberTalk — Two Chatbots, One Agreement
            <br>
            AI-powered cybersecurity discussions and decision support.
        </div>
        """,
        unsafe_allow_html=True,
    )


    # -------------------------
    # Centered Authentication Modal
    # -------------------------

    @st.dialog(
        "Welcome Back",
        width="small",
        on_dismiss=close_auth_dialog,
    )
    def authentication_dialog():

        modal_view = st.session_state["auth_modal_view"]

        # -------------------------
        # Sign In
        # -------------------------

        if modal_view == "signin":

            st.write("Sign in to access your CyberTalk workspace.")

            identifier = st.text_input(
                "Username or Email",
                max_chars=255,
                key="modal_login_identifier",
            )

            login_password = st.text_input(
                "Password",
                type="password",
                key="modal_login_password",
            )

            _, forgot_column = st.columns([3, 1])

            with forgot_column:
                st.button(
                    "Forgot Password?",
                    key="modal_forgot_password",
                    type="tertiary",
                    on_click=open_forgot_password,
                )

            if st.button(
                "Sign In",
                key="modal_sign_in",
                type="primary",
                use_container_width=True,
            ):

                if not identifier.strip() or not login_password:

                    st.error(
                        "Please enter your username/email and password."
                    )

                else:

                    try:
                        with st.spinner("Signing you in..."):

                            login_response = requests.post(
                                f"{API_URL}/login",
                                json={
                                    "identifier": identifier.strip(),
                                    "password": login_password,
                                },
                                timeout=30,
                            )

                        if login_response.ok:

                            login_data = login_response.json()

                            # Store the JWT in Streamlit session state.
                            access_token = login_data["access_token"]

                            st.session_state["access_token"] = access_token

                            # Persist the JWT in the browser until its actual expiration.
                            expires_in = int(login_data.get("expires_in", 1800))

                            cookie_controller.set(
                                AUTH_COOKIE_NAME,
                                access_token,
                                max_age=max(1, expires_in),
                                same_site="lax",
                                secure=(
                                    os.getenv(
                                        "CYBERTALK_COOKIE_SECURE",
                                        "false"
                                    ).lower() == "true"
                                ),
                            )

                            # Close the authentication dialog.
                            st.session_state["show_auth_dialog"] = False

                            # Restart the Streamlit script so the newly authenticated
                            # user is verified and the correct workspace is displayed.
                            st.rerun()
                        else:

                            st.error(
                                "Login failed: "
                                f"{get_api_error(login_response)}"
                            )

                    except requests.exceptions.RequestException as exc:

                        st.error(
                            f"Could not connect to the API: {exc}"
                        )

                    except (ValueError, KeyError):

                        st.error(
                            "The API returned an invalid login response."
                        )

            st.divider()

            st.caption("Don't have an account yet?")

            if st.button(
                "Sign Up",
                key="modal_open_signup",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state["auth_modal_view"] = "signup"
                st.rerun()

        # -------------------------
        # Forgot Password
        # -------------------------

        elif modal_view == "forgot":

            st.subheader("Reset Your Password")

            st.write(
                "Enter your registered email address. "
                "We'll send you a password-reset link."
            )

            with st.form("modal_password_reset_form"):

                reset_email = st.text_input(
                    "Registered Email",
                    max_chars=255,
                )

                reset_submitted = st.form_submit_button(
                    "Send Reset Link",
                    type="primary",
                    use_container_width=True,
                )

            if reset_submitted:

                if not reset_email.strip():

                    st.error(
                        "Please enter your registered email address."
                    )

                else:

                    try:
                        with st.spinner(
                            "Sending password-reset email..."
                        ):

                            reset_response = requests.post(
                                f"{API_URL}/password-reset/request",
                                json={
                                    "email": reset_email.strip()
                                },
                                timeout=30,
                            )

                        if reset_response.ok:

                            st.success(
                                reset_response.json().get(
                                    "message",
                                    "If an account exists for that email, "
                                    "a password-reset link has been sent."
                                )
                            )

                        else:

                            st.error(
                                "Could not process the request: "
                                f"{get_api_error(reset_response)}"
                            )

                    except requests.exceptions.RequestException as exc:

                        st.error(
                            f"Could not connect to the API: {exc}"
                        )

            st.button(
                "Back to Sign In",
                key="modal_back_from_forgot",
                use_container_width=True,
                on_click=return_to_sign_in,
            )

        # -------------------------
        # Create Account
        # -------------------------

        elif modal_view == "signup":

            st.subheader("Create Your Account")

            st.write(
                "Register to start exploring cybersecurity "
                "discussions with CyberTalk."
            )

            with st.form("modal_registration_form"):

                register_username = st.text_input(
                    "Username",
                    max_chars=50,
                )

                register_email = st.text_input(
                    "Email Address",
                    max_chars=255,
                )

                register_password = st.text_input(
                    "Password",
                    type="password",
                    max_chars=128,
                )

                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    max_chars=128,
                )

                register_submitted = st.form_submit_button(
                    "Create Account",
                    type="primary",
                    use_container_width=True,
                )

            if register_submitted:

                if not register_username.strip():
                    st.error("Please enter a username.")

                elif len(register_username.strip()) < 3:
                    st.error(
                        "Username must contain at least 3 characters."
                    )

                elif not register_email.strip():
                    st.error("Please enter your email address.")

                elif len(register_email.strip()) < 5:
                    st.error("Please enter a valid email address.")

                elif not register_password:
                    st.error("Please enter a password.")

                elif len(register_password) < 8:
                    st.error(
                        "Password must contain at least 8 characters."
                    )

                elif len(register_password) > 128:
                    st.error(
                        "Password cannot exceed 128 characters."
                    )

                elif register_password != confirm_password:
                    st.error("The passwords do not match.")

                else:

                    try:
                        with st.spinner("Creating your account..."):

                            register_response = requests.post(
                                f"{API_URL}/register",
                                json={
                                    "username": register_username.strip(),
                                    "email": register_email.strip().lower(),
                                    "password": register_password,
                                },
                                timeout=30,
                            )

                        if register_response.status_code == 201:

                            st.success(
                                "Account created successfully! "
                                "You can now sign in."
                            )

                            st.session_state["auth_modal_view"] = "signin"
                            st.rerun()

                        else:

                            st.error(
                                "Registration failed: "
                                f"{get_api_error(register_response)}"
                            )

                    except requests.exceptions.RequestException as exc:

                        st.error(
                            f"Could not connect to the API: {exc}"
                        )

            st.button(
                "Back to Sign In",
                key="modal_back_from_signup",
                use_container_width=True,
                on_click=return_to_sign_in,
            )

    if st.session_state["show_auth_dialog"]:
        authentication_dialog()

    st.stop()

# Ensure a valid user profile exists before showing authenticated content.
if not isinstance(current_user, dict):
    clear_authentication()
    st.stop()


# -----------------------------
# Authenticated user controls
# -----------------------------

st.sidebar.success(
    f"Signed in as {current_user.get('username', 'User')}"
)

st.sidebar.caption(
    f"Role: {current_user.get('role', 'user')}"
)


# -----------------------------
# Administrator Dashboard
# -----------------------------

st.session_state.setdefault("show_admin_dashboard", False)

is_admin = current_user.get("role") == "admin"

if is_admin:
    if st.sidebar.button(
        "Admin Dashboard",
        key="open_admin_dashboard",
        use_container_width=True,
    ):
        st.session_state["show_admin_dashboard"] = (
            not st.session_state["show_admin_dashboard"]
        )
        st.session_state["show_profile"] = False
        st.rerun()

if st.session_state["show_admin_dashboard"]:

    if not is_admin:
        st.session_state["show_admin_dashboard"] = False
        st.error("Administrator privileges are required.")
        st.stop()

    if st.button("Back to Chat", key="admin_back_to_chat"):
        st.session_state["show_admin_dashboard"] = False
        st.rerun()

    st.title("Admin Dashboard")
    st.write(
        "Review registered CyberTalk accounts and manage account roles."
    )
    st.divider()

    if st.session_state.pop("admin_role_update_success", False):
        st.success("User role updated successfully.")

    try:
        admin_search = st.text_input(
            "Search users",
            placeholder="Search by username or email",
            key="admin_user_search",
        )

        users_response = fetch_admin_users(admin_search)

        if users_response.status_code == 401:
            st.error("Your session has expired. Please sign in again.")
            clear_authentication()
            st.session_state["show_admin_dashboard"] = False
            st.stop()

        if users_response.status_code == 403:
            st.error("Administrator privileges are required.")
            st.session_state["show_admin_dashboard"] = False
            st.stop()

        if not users_response.ok:
            st.error(
                "Could not load registered users: "
                f"{get_api_error(users_response)}"
            )
            st.stop()

        admin_users = users_response.json()

        if not isinstance(admin_users, list):
            st.error("The API returned an invalid user list.")
            st.stop()

                # Keep the complete search result for account metrics.
        all_admin_users = admin_users

        total_users = len(all_admin_users)

        admin_count = sum(
            1 for user in all_admin_users
            if user.get("role") == "admin"
        )

        regular_count = sum(
            1 for user in all_admin_users
            if user.get("role") == "user"
        )

        active_users = sum(
            1 for user in all_admin_users
            if user.get("is_active", False)
        )

        inactive_users = total_users - active_users

        metric_columns = st.columns(5)

        metric_columns[0].metric("Users in Results", total_users)
        metric_columns[1].metric("Active Accounts", active_users)
        metric_columns[2].metric("Inactive Accounts", inactive_users)
        metric_columns[3].metric("Administrators", admin_count)
        metric_columns[4].metric("Regular Users", regular_count)

        st.subheader("Registered Users")

        status_filter = st.selectbox(
            "Filter by Account Status",
            options=["All Accounts", "Active", "Inactive"],
            key="admin_account_status_filter",
        )

        if status_filter == "Active":
            admin_users = [
                user for user in all_admin_users
                if user.get("is_active", False)
            ]

        elif status_filter == "Inactive":
            admin_users = [
                user for user in all_admin_users
                if not user.get("is_active", False)
            ]
        else:
            admin_users = all_admin_users

        if admin_users:

            display_users = [
                {
                    "User ID": user.get("id"),
                    "Username": user.get("username"),
                    "Email": user.get("email"),
                    "Role": str(
                        user.get("role", "user")
                    ).title(),
                    "Account Status": (
                        "Active"
                        if user.get("is_active", False)
                        else "Inactive"
                    ),
                    "Primary Admin": (
                        "Yes"
                        if user.get("is_primary_admin", False)
                        else "No"
                    ),
                    "Registered": user.get(
                        "created_at",
                        "N/A",
                    ),
                }
                for user in admin_users
            ]
            st.dataframe(
                display_users,
                use_container_width=True,
                hide_index=True,
            )

            user_options = {
                (
                    f"{user.get('username', 'Unknown')} "
                    f"({user.get('email', 'No email')}) — "
                    f"ID {user.get('id')}"
                ): user.get("id")
                for user in admin_users
            }

            st.subheader("User Details and Role Management")

            selected_label = st.selectbox(
                "Select a user",
                options=list(user_options.keys()),
                key="admin_selected_user",
            )

            selected_user_id = user_options[selected_label]

            details_response = fetch_admin_user_details(
                selected_user_id
            )

            if details_response.status_code == 401:
                st.error(
                    "Your session has expired. Please sign in again."
                )
                clear_authentication()
                st.session_state["show_admin_dashboard"] = False
                st.stop()

            elif details_response.status_code == 403:
                st.error("Administrator privileges are required.")
                st.session_state["show_admin_dashboard"] = False
                st.stop()

            elif details_response.status_code == 404:
                st.warning("This user account no longer exists.")

            elif not details_response.ok:
                st.error(
                    "Could not load user details: "
                    f"{get_api_error(details_response)}"
                )

            else:
                selected_user = details_response.json()

                detail_columns = st.columns(2)

                with detail_columns[0]:
                    st.write("**User ID**")
                    st.write(selected_user.get("id", "N/A"))

                    st.write("**Username**")
                    st.write(selected_user.get("username", "N/A"))

                with detail_columns[1]:
                    st.write("**Email**")
                    st.write(selected_user.get("email", "N/A"))

                    st.write("**Current role**")
                    st.write(
                        str(
                            selected_user.get("role", "user")
                        ).title()
                    )

                st.caption(
                    "Registration date: "
                    f"{selected_user.get('created_at', 'Not available')}"
                )

                if selected_user.get("id") == current_user.get("id"):

                    st.info(
                        "You cannot change your own administrator role."
                    )

                else:
                    current_role = selected_user.get("role", "user")

                    desired_role = st.selectbox(
                        "Change account role",
                        options=["user", "admin"],
                        index=0 if current_role == "user" else 1,
                        format_func=lambda value: value.title(),
                        key=f"admin_role_choice_{selected_user_id}",
                    )

                    if desired_role == current_role:
                        st.caption(
                            "The selected account already has this role."
                        )

                    elif st.button(
                        f"Update role to {desired_role.title()}",
                        key=f"admin_update_role_{selected_user_id}",
                        type="primary",
                    ):

                        try:
                            role_response = update_admin_user_role(
                                selected_user_id,
                                desired_role,
                            )

                            if role_response.status_code == 401:
                                st.error(
                                    "Your session has expired. "
                                    "Please sign in again."
                                )
                                clear_authentication()
                                st.session_state[
                                    "show_admin_dashboard"
                                ] = False
                                st.stop()

                            elif role_response.status_code == 403:
                                st.error(
                                    "Administrator privileges are required."
                                )

                            elif role_response.status_code == 409:
                                st.warning(
                                    get_api_error(role_response)
                                )

                            elif role_response.ok:
                                st.session_state[
                                    "admin_role_update_success"
                                ] = True
                                st.rerun()

                            else:
                                st.error(
                                    "Could not update the user role: "
                                    f"{get_api_error(role_response)}"
                                )

                        except requests.exceptions.RequestException:
                            st.error(
                                "Unable to update the user role. "
                                "Check the API connection and try again."
                            )
                st.divider()
                st.subheader("Account Lifecycle Management")

                account_is_active = selected_user.get(
                    "is_active",
                    False,
                )

                is_primary_admin = selected_user.get(
                    "is_primary_admin",
                    False,
                )

                if account_is_active:
                    st.success("Account Status: Active")

                    if is_primary_admin:
                        st.info(
                            "The primary administrator account "
                            "cannot be deactivated."
                        )

                    elif selected_user.get("id") == current_user.get("id"):
                        st.info(
                            "You cannot deactivate your own account."
                        )

                    else:
                        confirm_deactivation = st.checkbox(
                            "I confirm that I want to deactivate this account.",
                            key=f"confirm_deactivation_{selected_user_id}",
                        )

                        if st.button(
                            "Deactivate Account",
                            key=f"deactivate_user_{selected_user_id}",
                            type="primary",
                            disabled=not confirm_deactivation,
                        ):
                            try:
                                success, message = deactivate_admin_user(
                                    selected_user_id
                                )

                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)

                            except requests.exceptions.RequestException:
                                st.error(
                                    "Unable to deactivate the account. "
                                    "Please check the API connection."
                                )

                else:
                    st.warning("Account Status: Inactive")

                    if st.button(
                        "Reactivate Account",
                        key=f"reactivate_user_{selected_user_id}",
                    ):
                        try:
                            success, message = reactivate_admin_user(
                                selected_user_id
                            )

                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

                        except requests.exceptions.RequestException:
                            st.error(
                                "Unable to reactivate the account. "
                                "Please check the API connection."
                            )

                deactivated_at = selected_user.get("deactivated_at")

                if deactivated_at:
                    st.caption(
                        f"Deactivated At: {deactivated_at}"
                    )
        else:
            st.info("No registered users match your search.")

        # -----------------------------
        # Administrator Audit History
        # -----------------------------

        st.divider()
        st.subheader("Audit History")

        audit_response = fetch_admin_audit_logs()

        if audit_response.status_code == 401:
            st.error(
                "Your session has expired. Please sign in again."
            )
            clear_authentication()
            st.session_state["show_admin_dashboard"] = False
            st.stop()

        elif audit_response.status_code == 403:
            st.error("Administrator privileges are required.")
            st.session_state["show_admin_dashboard"] = False
            st.stop()

        elif not audit_response.ok:
            st.error(
                "Could not load audit history: "
                f"{get_api_error(audit_response)}"
            )

        else:
            audit_records = audit_response.json()

            if not isinstance(audit_records, list):
                st.error("The API returned an invalid audit history.")
            elif not audit_records:
                st.info("No administrator activity has been recorded yet.")
            else:
                display_audit_logs = [
                    {
                        "Administrator": record.get(
                            "actor_username", "Unknown"
                        ),
                        "Affected User": record.get(
                            "target_username", "Unknown"
                        ),
                        "Action": record.get(
                            "action", "Unknown"
                        ).replace("_", " ").title(),
                        "Role Change": (
                            f"{record.get('previous_role', 'N/A')} → "
                            f"{record.get('new_role', 'N/A')}"
                        ),
                        "Account Status": (
                            f"{record.get('previous_status') or 'N/A'} → "
                            f"{record.get('new_status') or 'N/A'}"
                        ),
                        "Timestamp": record.get(
                            "created_at", "N/A"
                        ),
                    }
                    for record in audit_records
                ]

                st.dataframe(
                    display_audit_logs,
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    f"Showing the latest {len(audit_records)} "
                    "administrator activity records."
                )

    except requests.exceptions.RequestException:
        st.error(
            "Unable to connect to the administrator API. "
            "Please check that the CyberTalk API is running."
        )

    st.stop()


# -----------------------------
# Top-right Profile Icon
# -----------------------------

st.session_state.setdefault("show_profile", False)

st.session_state.setdefault("edit_profile_open", False)

st.session_state.setdefault("change_password_open", False)

# Retrieve the saved profile picture for the home-page avatar.
profile_picture_bytes = None
profile_picture_mime = "image/jpeg"

if not st.session_state["show_profile"]:

    try:
        avatar_response = requests.get(
            f"{API_URL}/users/me/profile-picture",
            headers=get_auth_headers(),
            timeout=15,
        )

        if avatar_response.status_code == 200:
            profile_picture_bytes = avatar_response.content
            profile_picture_mime = avatar_response.headers.get(
                "content-type",
                "image/jpeg",
            ).split(";")[0]

        elif avatar_response.status_code == 401:
            clear_authentication()
            st.warning(
                "Your session has expired. Please log in again."
            )
            st.stop()

        elif avatar_response.status_code != 404:
            st.warning(
                "Could not load your profile picture."
            )

    except requests.exceptions.RequestException:
        st.warning(
            "Could not connect to load your profile picture."
        )


# Display the profile-picture navigation control only on the home page.
if not st.session_state["show_profile"]:

    top_spacer, profile_column = st.columns([12, 1])

    with profile_column:

        # Use the uploaded picture as the profile button itself.
        if profile_picture_bytes:

            encoded_picture = base64.b64encode(
                profile_picture_bytes
            ).decode("ascii")

            st.markdown(
                f"""
                <style>
                div.st-key-profile_menu_button button {{
                    width: 36px !important;
                    height: 36px !important;
                    min-width: 36px !important;
                    min-height: 36px !important;
                    max-width: 36px !important;
                    max-height: 36px !important;
                    padding: 0 !important;
                    border-radius: 50% !important;

                    background-image: url(
                        "data:{profile_picture_mime};base64,{encoded_picture}"
                    ) !important;

                    background-size: cover !important;
                    background-position: center !important;
                    background-repeat: no-repeat !important;

                    color: transparent !important;
                    box-shadow: none !important;
                }}

                /* Keep the profile button contents small */
                div.st-key-profile_menu_button button p {{
                    display: none !important;
                }}

                /* Reduce the three-dot menu icon size */
                div.st-key-profile_menu_button button svg {{
                    width: 18px !important;
                    height: 18px !important;
                }}

                /* Center the three-dot icon */
                div.st-key-profile_menu_button button {{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }}

                /* =================================
                CONVERSATION THREE-DOT MENU
                ================================= */

                /* Compact three-dot trigger */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"] {{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 34px !important;
                    min-width: 34px !important;
                    max-width: 34px !important;
                    height: 32px !important;
                    min-height: 32px !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    border: none !important;
                    border-radius: 6px !important;
                    background: transparent !important;
                    color: #ffffff !important;
                    box-shadow: none !important;
                    font-size: 23px !important;
                    line-height: 1 !important;
                    gap: 0 !important;
                }}

                /* Conversation three-dot menu trigger */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"] {{
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 34px !important;
                    min-width: 34px !important;
                    height: 32px !important;
                    min-height: 32px !important;
                    padding: 0 !important;
                    border: none !important;
                    border-radius: 6px !important;
                    background: transparent !important;
                    color: #ffffff !important;
                    box-shadow: none !important;
                    font-size: 0 !important;
                }}

                /* Hide all original button contents */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"] > * {{
                    display: none !important;
                }}

                /* Remove any automatic arrow decorations */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"]::after {{
                    display: none !important;
                    content: none !important;
                }}

                /* Display exactly one custom three-dot icon */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"]::before {{
                    content: "···" !important;
                    display: block !important;
                    visibility: visible !important;
                    color: #ffffff !important;
                    font-family: Arial, sans-serif !important;
                    font-size: 24px !important;
                    font-weight: 700 !important;
                    line-height: 1 !important;
                }}

                /* Hover */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"]:hover {{
                    background: rgba(255, 255, 255, 0.10) !important;
                }}

                /* Focus */
                div[class*="st-key-history_menu_popover_"]
                button[data-testid="stPopoverButton"]:focus {{
                    outline: none !important;
                    box-shadow: none !important;
                }}

                /* =================================
                COMPACT DROPDOWN PANEL
                ================================= */

                div[data-testid="stPopoverBody"] {{
                    width: 180px !important;
                    min-width: 180px !important;
                    max-width: 180px !important;
                    padding: 6px !important;
                    border-radius: 10px !important;
                }}

                /* Compact dropdown action buttons */
                div[class*="st-key-menu_rename_"] button,
                div[class*="st-key-menu_share_"] button,
                div[class*="st-key-menu_download_"] button,
                div[class*="st-key-menu_delete_"] button {{
                    width: 100% !important;
                    min-height: 34px !important;
                    padding: 5px 9px !important;
                    margin: 1px 0 !important;
                    border-radius: 6px !important;
                    font-size: 13px !important;
                }}

                div[class*="st-key-history_menu_popover_"]
                [data-testid="stPopoverButton"] svg {{
                    display: none !important;
                }}
                /* -----------------------------
                ChatGPT-style conversation UI
                ----------------------------- */

                /* Stakeholder conversation messages */
                [data-testid="stChatMessage"] {{
                    background: rgba(18, 38, 60, 0.72);
                    border: 1px solid #294663;
                    border-radius: 14px;
                    padding: 18px 20px;
                    margin-bottom: 14px;
                    transition: border-color 0.2s ease;
                }}

                [data-testid="stChatMessage"]:hover {{
                    border-color: #168acb;
                }}

                /* Conversation message text */
                [data-testid="stChatMessage"] p {{
                    color: #e2ebf7;
                    line-height: 1.75;
                    font-size: 15px;
                }}

                /* Stakeholder names and turn labels */
                [data-testid="stChatMessage"] strong {{
                    color: #19c9f4;
                    font-weight: 700;
                }}

                /* Input focus styling */
                .stTextInput input:focus,
                .stTextArea textarea:focus {{
                    border-color: #19a9e5 !important;
                    box-shadow: 0 0 0 1px #19a9e5 !important;
                }}

                /* Better text area readability */
                .stTextArea textarea {{
                    line-height: 1.6;
                    padding: 12px;
                }}

                /* Responsive conversation spacing */
                @media (max-width: 700px) {{
                    [data-testid="stChatMessage"] {{
                        padding: 13px;
                        border-radius: 11px;
                    }}
                }}
                /* Remove the outer box around the selected conversation action panel */
                div[class*="st-key-history_action_panel_"] {{
                    border: none !important;
                    outline: none !important;
                    box-shadow: none !important;
                    background: transparent !important;
                    padding: 0 !important;
                }}

                /* Remove borders from elements directly inside the action panel */
                div[class*="st-key-history_action_panel_"] > div {{
                    border: none !important;
                    outline: none !important;
                    box-shadow: none !important;
                    background: transparent !important;
                }}

                /* Remove backgrounds from conversation action buttons */
                div[class*="st-key-menu_rename_"] button,
                div[class*="st-key-menu_share_"] button,
                div[class*="st-key-menu_download_"] button,
                div[class*="st-key-menu_delete_"] button {{
                    background: transparent !important;
                    background-color: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    color: #e2e8f0 !important;
                    text-align: left !important;
                    justify-content: flex-start !important;
                    padding: 8px 12px !important;
                }}

                /* Subtle hover effect */
                div[class*="st-key-menu_rename_"] button:hover,
                div[class*="st-key-menu_share_"] button:hover,
                div[class*="st-key-menu_download_"] button:hover,
                div[class*="st-key-menu_delete_"] button:hover {{
                    background: rgba(255, 255, 255, 0.08) !important;
                    border: none !important;
                    box-shadow: none !important;
                }}

                </style>
                """,
                unsafe_allow_html=True,
            )

            profile_button_label = " "

        else:
            profile_button_label = "👤"

        if st.button(
            profile_button_label,
            key="profile_menu_button",
            help="My Profile",
            use_container_width=False,
        ):

            st.session_state["show_profile"] = True
            st.rerun()

# -----------------------------
# Redesigned My Profile Page
# -----------------------------

if st.session_state["show_profile"]:

    # -----------------------------
    # Profile page styling
    # -----------------------------

    st.markdown(
        """
        <style>
        .profile-page-header {
            margin: 12px 0 24px 0;
        }

        .profile-page-header h1 {
            color: #f0f6ff;
            font-size: 32px;
            margin-bottom: 5px;
        }

        .profile-page-header p {
            color: #9fb2c9;
            font-size: 14px;
        }

        .profile-avatar {
            width: 152px;
            height: 152px;
            border-radius: 50%;
            overflow: hidden;
            margin: 8px auto 14px auto;
            border: 3px solid #19c9f4;
            box-shadow: 0 0 22px rgba(25, 201, 244, 0.18);
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #0878d1, #102f4b);
            color: white;
            font-size: 42px;
            font-weight: 700;
        }

        .profile-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
        }

        .profile-avatar-caption {
            text-align: center;
            color: #a9bad0;
            font-size: 13px;
            margin-bottom: 12px;
        }

        .profile-section-heading {
            color: #19c9f4;
            font-size: 17px;
            font-weight: 700;
            margin-bottom: 12px;
        }
        /* Personal Information editor */

        .profile-editor-title {
            color: #f0f6ff;
            font-size: 19px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .profile-editor-description {
            color: #91a8c2;
            font-size: 13px;
            margin-bottom: 20px;
        }

        div.st-key-open_edit_profile button {
            background: linear-gradient(90deg, #087fa8, #19c9f4) !important;
            color: #ffffff !important;
            border: 1px solid #19c9f4 !important;
            border-radius: 9px !important;
            font-weight: 700 !important;
            min-height: 44px !important;
            transition: all 0.2s ease !important;
        }

        div.st-key-open_edit_profile button:hover {
            border-color: #65ddff !important;
            filter: brightness(1.12);
        }

        div.st-key-update_profile_form {
            padding: 8px 2px 4px 2px;
        }

        div.st-key-update_profile_form input {
            border-radius: 8px !important;
        }

        div.st-key-update_profile_form button {
            background: #087fa8 !important;
            color: #ffffff !important;
            border: 1px solid #19c9f4 !important;
            border-radius: 9px !important;
            font-weight: 700 !important;
            min-height: 42px !important;
        }

        div.st-key-update_profile_form button:hover {
            background: #09678a !important;
            border-color: #65ddff !important;
        }

        div.st-key-cancel_edit_profile button {
            border-radius: 9px !important;
            min-height: 42px !important;
            font-weight: 600 !important;
        }

        .profile-detail-label {
            color: #91a8c2;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.7px;
            margin-bottom: 4px;
        }

        .profile-detail-value {
            color: #f0f6ff;
            font-size: 15px;
            font-weight: 500;
            overflow-wrap: anywhere;
            margin-bottom: 18px;
        }

        /* Profile picture upload button */

        div[data-testid="stFileUploader"] {
            width: 100% !important;
            max-width: 260px !important;
            margin: 12px auto 20px auto !important;
        }

        div[data-testid="stFileUploader"] label {
            display: none !important;
        }

        /* Profile navigation and action buttons */
        div.st-key-open_edit_profile button,
        div.st-key-open_change_password button {
            border-radius: 9px !important;
            min-height: 42px !important;
        }

        /* Profile form inputs */
        div.st-key-update_profile_form input,
        div.st-key-change_password_form input {
            border-radius: 8px !important;
        }

        /* Responsive profile picture */
        @media (max-width: 600px) {
            .profile-avatar {
                width: 125px;
                height: 125px;
                font-size: 34px;
            }

            .profile-page-header h1 {
                font-size: 26px;
            }
        }
        /* FINAL OVERRIDE: Profile picture uploader */

        div[data-testid="stFileUploader"] {
            width: 100% !important;
            max-width: 260px !important;
            margin: 12px auto 20px auto !important;
        }

        /* Remove the grey dropzone */
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            box-shadow: none !important;
            min-height: 0 !important;
        }

        /* Hide drag-and-drop instructions */
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }

        /* Style the actual native upload button */
        div[data-testid="stFileUploader"] button,
        div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
            width: 100% !important;
            min-height: 46px !important;
            background: linear-gradient(90deg, #0878d1, #13a5d9) !important;
            background-color: #0878d1 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 9px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            box-shadow: none !important;
            justify-content: center !important;
        }

        /* Hover effect */
        div[data-testid="stFileUploader"] button:hover,
        div[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"]:hover {
            background: linear-gradient(90deg, #096bb8, #108fc4) !important;
            background-color: #096bb8 !important;
            box-shadow: 0 4px 14px rgba(25, 169, 229, 0.25) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------
    # Back navigation
    # -----------------------------

    if st.button(
        "← Back to Chat",
        key="back_to_chat",
    ):
        st.session_state["show_profile"] = False
        st.session_state["edit_profile_open"] = False
        st.session_state["change_password_open"] = False
        st.rerun()

    # -----------------------------
    # Profile page heading
    # -----------------------------

    st.title("My Profile")

    st.caption(
        "Manage your personal information and account settings."
    )

    # Display messages after successful operations.
    profile_notice = st.session_state.pop(
        "profile_notice",
        None,
    )

    if profile_notice:
        notice_type, notice_message = profile_notice

        if notice_type == "success":
            st.success(notice_message)
        elif notice_type == "info":
            st.info(notice_message)
        else:
            st.warning(notice_message)

    if st.session_state.pop(
        "profile_picture_upload_success",
        False,
    ):
        st.success("Profile picture uploaded successfully!")

    # -----------------------------
    # Retrieve profile picture
    # -----------------------------

    picture_bytes = None
    picture_mime = "image/jpeg"

    try:
        picture_response = requests.get(
            f"{API_URL}/users/me/profile-picture",
            headers=get_auth_headers(),
            timeout=15,
        )

        if picture_response.status_code == 200:
            picture_bytes = picture_response.content

            picture_mime = picture_response.headers.get(
                "content-type",
                "image/jpeg",
            ).split(";")[0]

        elif picture_response.status_code == 401:
            clear_authentication()
            st.error(
                "Your session has expired. Please log in again."
            )
            st.stop()

        elif picture_response.status_code != 404:
            st.warning(
                "Could not load your profile picture."
            )

    except requests.exceptions.RequestException:
        st.warning(
            "Could not connect to load your profile picture."
        )

    # -----------------------------
    # Profile avatar and upload
    # -----------------------------

    avatar_spacer_left, avatar_column, avatar_spacer_right = (
        st.columns([1, 2, 1])
    )

    with avatar_column:

        if picture_bytes:
            import base64

            encoded_picture = base64.b64encode(
                picture_bytes
            ).decode("utf-8")

            st.markdown(
                f"""
                <div style="
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 15px 0 25px 0;
                ">
                    <img
                        src="data:{picture_mime};base64,{encoded_picture}"
                        style="
                            width: 160px;
                            height: 160px;
                            border-radius: 50%;
                            object-fit: cover;
                            object-position: center;
                            border: 3px solid #3B82F6;
                        "
                    />
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(
                "You have not uploaded a profile picture yet."
            )

        # Single-button profile picture upload

        uploader_version = st.session_state.get(
            "profile_picture_uploader_version", 0
        )

        uploaded_picture = st.file_uploader(
            "Update Profile Picture",
            type=["png", "jpg", "jpeg"],
            key=f"profile_picture_uploader_{uploader_version}",
            help="JPEG or PNG image. Maximum size: 5 MB.",
            label_visibility="collapsed",
        )
        if uploaded_picture is not None:

            picture_data = uploaded_picture.getvalue()

            st.markdown("**Preview your new profile picture**")
            st.image(picture_data, width=160)

            if len(picture_data) > 5 * 1024 * 1024:
                st.error("The profile picture must not exceed 5 MB.")

            else:
                st.info("Confirm whether you want to save this picture.")

                confirm_col, cancel_col = st.columns(2)

                with confirm_col:
                    confirm_upload = st.button(
                        "Save Profile Picture",
                        key="confirm_profile_picture_upload",
                        type="primary",
                        use_container_width=True,
                    )

                with cancel_col:
                    cancel_upload = st.button(
                        "Cancel",
                        key="cancel_profile_picture_upload",
                        use_container_width=True,
                    )

                if cancel_upload:
                    st.session_state["profile_picture_uploader_version"] = (
                        st.session_state.get(
                            "profile_picture_uploader_version", 0
                        ) + 1
                    )
                    st.rerun()

                if confirm_upload:
                    try:
                        with st.spinner("Updating profile picture..."):
                            upload_response = requests.post(
                                f"{API_URL}/users/me/profile-picture",
                                headers=get_auth_headers(),
                                files={
                                    "file": (
                                        uploaded_picture.name,
                                        picture_data,
                                        uploaded_picture.type,
                                    )
                                },
                                timeout=30,
                            )

                        if upload_response.status_code in (200, 201):

                            st.session_state["profile_picture_uploader_version"] = (
                                st.session_state.get(
                                    "profile_picture_uploader_version", 0
                                ) + 1
                            )

                            st.session_state["profile_picture_upload_success"] = True

                            st.rerun()

                        elif upload_response.status_code == 401:
                            clear_authentication()
                            st.error("Your session has expired.")
                            st.stop()

                        else:
                            st.error(get_api_error(upload_response))

                    except requests.exceptions.RequestException:
                        st.error("Unable to upload your profile picture.")



    st.divider()


    # -----------------------------
    # Account overview
    # -----------------------------

    st.markdown(
        '<div class="profile-section-heading">'
        'Account Overview'
        '</div>',
        unsafe_allow_html=True,
    )

    account_role = str(
        current_user.get("role", "user")
    ).title()

    account_active = current_user.get("is_active", True)

    account_status = (
        "Active" if account_active else "Inactive"
    )

    with st.container(border=True):

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:

            st.markdown(
                '<div class="profile-detail-label">Username</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="profile-detail-value">'
                f'{escape(str(current_user.get("username", "N/A")))}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="profile-detail-label">Account Role</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="profile-detail-value">'
                f'{escape(account_role)}'
                f'</div>',
                unsafe_allow_html=True,
            )

        with detail_col2:

            st.markdown(
                '<div class="profile-detail-label">Email Address</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="profile-detail-value">'
                f'{escape(str(current_user.get("email", "N/A")))}'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="profile-detail-label">Account Status</div>',
                unsafe_allow_html=True,
            )

            status_color = (
                "#32d49a" if account_active else "#ff8585"
            )

            st.markdown(
                f'<div class="profile-detail-value" '
                f'style="color:{status_color};">'
                f'{escape(account_status)}'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="profile-detail-label">User ID</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="profile-detail-value">'
            f'{escape(str(current_user.get("id", "N/A")))}'
            f'</div>',
            unsafe_allow_html=True,
        )

        created_at = current_user.get(
            "created_at",
            "Not available",
        )

        st.markdown(
            '<div class="profile-detail-label">Registration Date</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="profile-detail-value">'
            f'{escape(str(created_at))}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # -----------------------------
    # Edit Profile
    # -----------------------------

    st.markdown(
        '<div class="profile-section-heading">'
        'Personal Information'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        (
            "Close Profile Editor"
            if st.session_state["edit_profile_open"]
            else "Update Profile"
        ),
        key="open_edit_profile",
        use_container_width=True,
    ):

        st.session_state["edit_profile_open"] = (
            not st.session_state["edit_profile_open"]
        )

        st.session_state["change_password_open"] = False
        st.rerun()

    if st.session_state["edit_profile_open"]:

        with st.container(border=True):

            st.subheader("Edit Profile")

            st.caption(
                "Manage your username and email address."
            )

            with st.form("update_profile_form"):

                updated_username = st.text_input(
                    "Username",
                    value=current_user.get("username", ""),
                    max_chars=50,
                )

                updated_email = st.text_input(
                    "Email Address",
                    value=current_user.get("email", ""),
                    max_chars=255,
                )

                save_profile = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True,
                )

            cancel_col, empty_col = st.columns([1, 2], gap="medium")

            with cancel_col:
                cancel_profile_edit = st.button(
                    "Cancel",
                    key="cancel_edit_profile",
                    use_container_width=True,
                )

            if cancel_profile_edit:
                st.session_state["edit_profile_open"] = False
                st.rerun()

            if save_profile:

                username = updated_username.strip()
                email = updated_email.strip().lower()

                if len(username) < 3:

                    st.error(
                        "Username must contain at least 3 characters."
                    )

                elif (
                    "@" not in email
                    or "." not in email.split("@")[-1]
                ):

                    st.error(
                        "Please provide a valid email address."
                    )

                elif (
                    username == current_user.get("username")
                    and email == current_user.get(
                        "email", ""
                    ).lower()
                ):

                    st.session_state["edit_profile_open"] = False

                    st.session_state["profile_notice"] = (
                        "info",
                        "No profile changes were made.",
                    )

                    st.rerun()

                else:

                    try:
                        with st.spinner(
                            "Updating your profile..."
                        ):

                            update_response = requests.put(
                                f"{API_URL}/users/me",
                                headers=get_auth_headers(),
                                json={
                                    "username": username,
                                    "email": email,
                                },
                                timeout=15,
                            )

                        if update_response.status_code == 200:

                            # Close the editor immediately after success.
                            st.session_state["edit_profile_open"] = False

                            st.session_state["profile_notice"] = (
                                "success",
                                "Your profile was updated successfully.",
                            )

                            st.rerun()

                        elif update_response.status_code == 401:

                            clear_authentication()

                            st.error(
                                "Your session has expired. Please log in again."
                            )

                            st.stop()

                        else:

                            # Keep the editor open so the user can correct errors.
                            st.error(
                                get_api_error(update_response)
                            )

                    except requests.exceptions.RequestException:

                        st.error(
                            "Unable to update your profile. "
                            "Please check your connection and try again."
                        )

    st.divider()

    # -----------------------------
    # Change Password
    # -----------------------------

    st.markdown(
        '<div class="profile-section-heading">'
        'Security Settings'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        (
            "Close Password Settings"
            if st.session_state["change_password_open"]
            else "Change Password"
        ),
        key="open_change_password",
        use_container_width=True,
    ):

        st.session_state["change_password_open"] = (
            not st.session_state["change_password_open"]
        )

        st.session_state["edit_profile_open"] = False
        st.rerun()

    if st.session_state["change_password_open"]:

        with st.container(border=True):

            st.subheader("Update Your Password")

            st.caption(
                "Choose a strong password to protect your account."
            )

            with st.form("change_password_form"):

                current_password = st.text_input(
                    "Current Password",
                    type="password",
                )

                new_password = st.text_input(
                    "New Password",
                    type="password",
                    help="Must contain at least 8 characters.",
                )

                confirm_new_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                )

                change_password_submitted = st.form_submit_button(
                    "Save New Password",
                    use_container_width=True,
                )

            if change_password_submitted:

                if (
                    not current_password
                    or not new_password
                    or not confirm_new_password
                ):

                    st.error(
                        "Please fill in all password fields."
                    )

                elif len(new_password) < 8:

                    st.error(
                        "New password must contain at least 8 characters."
                    )

                elif new_password != confirm_new_password:

                    st.error(
                        "New passwords do not match."
                    )

                elif new_password == current_password:

                    st.error(
                        "New password must be different from the current password."
                    )

                else:

                    try:
                        with st.spinner(
                            "Updating your password..."
                        ):

                            password_response = requests.post(
                                f"{API_URL}/change-password",
                                headers=get_auth_headers(),
                                json={
                                    "current_password": current_password,
                                    "new_password": new_password,
                                    "confirm_new_password": confirm_new_password,
                                },
                                timeout=15,
                            )

                        if password_response.status_code == 200:

                            st.session_state[
                                "change_password_open"
                            ] = False

                            st.session_state["profile_notice"] = (
                                "success",
                                "Your password was changed successfully.",
                            )

                            st.rerun()

                        elif password_response.status_code == 401:

                            clear_authentication()

                            st.error(
                                "Your session has expired. Please log in again."
                            )

                            st.stop()

                        else:

                            st.error(
                                get_api_error(password_response)
                            )

                    except requests.exceptions.RequestException:

                        st.error(
                            "Unable to connect to the CyberTalk server. "
                            "Please try again."
                        )

    st.divider()

    # -----------------------------
    # Logout
    # -----------------------------

    if st.button(
        "Log Out",
        use_container_width=True,
        key="profile_logout",
    ):

        clear_authentication()

        st.session_state["show_profile"] = False
        st.session_state["edit_profile_open"] = False
        st.session_state["change_password_open"] = False

        st.rerun()

    st.stop()

@st.dialog("Delete conversation?")
def confirm_delete_conversation(history_id):
    """Delete a conversation after explicit user confirmation."""

    try:
        response = delete_chat_history(history_id)

        if response.ok:
            st.session_state[f"delete_success_{history_id}"] = True
        else:
            st.session_state[f"delete_error_{history_id}"] = (
                get_api_error(response)
            )

    except requests.exceptions.RequestException:
        st.session_state[f"delete_error_{history_id}"] = (
            "Could not connect to the API."
        )


@st.dialog("Delete conversation?")
def show_delete_confirmation(history_id, title):
    st.write(
        f'Are you sure you want to permanently delete "{title}"?'
    )
    st.caption("This action cannot be undone.")

    success_key = f"delete_success_{history_id}"
    error_key = f"delete_error_{history_id}"

    if st.session_state.get(success_key):
        st.session_state.pop(success_key, None)
        st.rerun()

    if st.session_state.get(error_key):
        st.error(st.session_state.pop(error_key))

    confirm_col, cancel_col = st.columns(2)

    with confirm_col:
        if st.button(
            "Delete",
            key=f"confirm_delete_{history_id}",
            type="primary",
            use_container_width=True,
            on_click=confirm_delete_conversation,
            args=(history_id,),
        ):
            if st.session_state.get(success_key):
                st.session_state.pop(success_key, None)
                st.rerun()

    with cancel_col:
        if st.button(
            "Cancel",
            key=f"cancel_delete_{history_id}",
            use_container_width=True,
        ):
            st.rerun()

# -----------------------------
# Chat History Sidebar
# -----------------------------

st.sidebar.divider()
st.sidebar.subheader("My Chat History")
if "delete_all_success" in st.session_state:
    deleted_count = st.session_state.pop("delete_all_success")

    st.sidebar.success(
        f"Successfully deleted {deleted_count} conversation(s)."
    )
try:
    history_response = fetch_chat_history()

    if history_response.status_code == 401:
        st.sidebar.warning(
            "Your session has expired. Please log in again."
        )

    elif history_response.ok:
        history_records = history_response.json()

        if not isinstance(history_records, list):
            st.sidebar.warning(
                "The API returned an invalid history response."
            )

        elif not history_records:
            st.sidebar.caption(
                "No saved conversations yet."
            )

        else:
            st.sidebar.caption(
            f"{len(history_records)} saved conversation(s)"
            )

            if st.sidebar.button(
                "Delete All Chats",
                key="delete_all_chats_button",
                use_container_width=True,
            ):
                show_delete_all_confirmation()

            for record in history_records:
                history_id = record["id"]
                conversation_type = record["conversation_type"]
                title = record["title"]

                menu_key = f"show_history_menu_{history_id}"
                details_key = f"show_history_details_{history_id}"
                confirm_delete_key = (
                    f"confirm_delete_history_{history_id}"
                )

                # Conversation title and three-dot menu.
                title_col, menu_col = st.sidebar.columns(
                    [0.88, 0.12]
                )

                with title_col:
                    if st.button(
                        title,
                        key=f"history_title_{history_id}",
                        help="Open conversation",
                        use_container_width=False,
                    ):
                        # Open the saved conversation directly from its title.
                        try:
                            detail_response = fetch_single_chat_history(history_id)

                            if detail_response.ok:
                                saved_record = detail_response.json()
                                raw_content = saved_record.get("content", "{}")
                                saved_content = (
                                    json.loads(raw_content)
                                    if isinstance(raw_content, str)
                                    else raw_content
                                )
                                saved_type = saved_record.get(
                                    "conversation_type",
                                    conversation_type,
                                )

                                if saved_type == "qa":
                                    if not isinstance(saved_content, dict):
                                        raise ValueError("Invalid saved Q&A data.")
                                    st.session_state["qa_result"] = saved_content
                                    st.session_state["active_workspace"] = "qa"
                                    st.session_state.pop("cybertalk_result", None)

                                elif saved_type == "dialogue":
                                    if not isinstance(saved_content, dict):
                                        raise ValueError("Invalid saved dialogue data.")
                                    st.session_state["cybertalk_result"] = saved_content
                                    st.session_state["active_workspace"] = "discussion"
                                    st.session_state.pop("qa_result", None)

                                else:
                                    raise ValueError("Unsupported conversation type.")

                                for state_key in list(st.session_state.keys()):
                                    if state_key.startswith("show_history_menu_"):
                                        st.session_state[state_key] = False

                                st.rerun()
                            else:
                                st.sidebar.error(
                                    "Could not open this conversation: "
                                    f"{get_api_error(detail_response)}"
                                )

                        except (
                            requests.exceptions.RequestException,
                            ValueError,
                            KeyError,
                            TypeError,
                        ):
                            st.sidebar.error(
                                "Could not load the saved conversation."
                            )

                with menu_col:
                    history_menu_popover = st.popover(
                        "···",
                        key=f"history_menu_popover_{history_id}",
                        help="Conversation actions",
                        type="tertiary",
                        use_container_width=False,
                        width=190,
                    )

                    # Show only four actions in the initial floating menu.
                    with history_menu_popover:
                        if st.button(
                            "Rename",
                            icon=":material/edit:",
                            key=f"menu_rename_{history_id}",
                            use_container_width=True,
                        ):
                            st.session_state[f"history_action_{history_id}"] = "rename"
                            st.rerun()

                        if st.button(
                            "Share",
                            icon=":material/share:",
                            key=f"menu_share_{history_id}",
                            use_container_width=True,
                        ):
                            st.session_state[f"history_action_{history_id}"] = "share"
                            st.rerun()

                        if st.button(
                            "Download",
                            icon=":material/download:",
                            key=f"menu_download_{history_id}",
                            use_container_width=True,
                        ):
                            st.session_state[f"history_action_{history_id}"] = "download"
                            st.rerun()

                        if st.button(
                            "Delete",
                            icon=":material/delete:",
                            key=f"menu_delete_{history_id}",
                            use_container_width=True,
                            type="secondary",
                        ):
                            st.session_state[f"history_action_{history_id}"] = "delete"
                            st.rerun()
                # --------------------------------------------------
                # Render the selected conversation action separately
                # --------------------------------------------------

                action_key = f"history_action_{history_id}"
                selected_action = st.session_state.get(action_key)

                if selected_action:

                    with st.container(key=f"history_action_panel_{history_id}"):

                        # Close the selected action panel.
                        if st.button(
                            "Close",
                            key=f"close_history_action_{history_id}",
                            type="tertiary",
                        ):
                            st.session_state.pop(action_key, None)
                            st.rerun()

                        # -------------------------
                        # RENAME
                        # -------------------------
                        if selected_action == "rename":

                            st.markdown("**Rename conversation**")

                            with st.form(
                                key=f"rename_history_form_{history_id}",
                                border=False,
                            ):
                                new_title = st.text_input(
                                    "Conversation title",
                                    value=title,
                                    max_chars=500,
                                    key=f"rename_title_{history_id}",
                                )

                                rename_submitted = st.form_submit_button(
                                    "Save changes",
                                    use_container_width=True,
                                )

                            if rename_submitted:

                                if not new_title.strip():
                                    st.warning(
                                        "Conversation title cannot be empty."
                                    )

                                elif new_title.strip() == title:
                                    st.info(
                                        "The conversation title has not changed."
                                    )

                                else:
                                    try:
                                        rename_response = rename_chat_history(
                                            history_id,
                                            new_title.strip(),
                                        )

                                        if rename_response.ok:
                                            st.session_state.pop(action_key, None)
                                            st.rerun()

                                        else:
                                            st.error(
                                                "Could not rename conversation: "
                                                f"{get_api_error(rename_response)}"
                                            )

                                    except requests.exceptions.RequestException:
                                        st.error(
                                            "Could not connect to the API."
                                        )

                        # -------------------------
                        # SHARE
                        # -------------------------
                        elif selected_action == "share":

                            st.markdown("**Share conversation**")

                            share_state_key = f"share_link_data_{history_id}"
                            revoked_state_key = f"share_revoked_{history_id}"

                            if st.session_state.pop(revoked_state_key, False):
                                st.success("Share link revoked successfully.")

                            with st.form(
                                key=f"share_form_{history_id}",
                                border=False,
                            ):

                                expiry_label = st.selectbox(
                                    "Link expiration",
                                    options=[
                                        "Never",
                                        "1 day",
                                        "7 days",
                                        "30 days",
                                        "90 days",
                                        "365 days",
                                    ],
                                    key=f"share_expiry_{history_id}",
                                )

                                generate_share = st.form_submit_button(
                                    "Generate Shareable Link",
                                    use_container_width=True,
                                    disabled=bool(
                                        st.session_state.get(share_state_key)
                                    ),
                                )

                            if generate_share:

                                expiry_days = {
                                    "Never": None,
                                    "1 day": 1,
                                    "7 days": 7,
                                    "30 days": 30,
                                    "90 days": 90,
                                    "365 days": 365,
                                }

                                try:
                                    share_response = create_share_link(
                                        history_id,
                                        expiry_days[expiry_label],
                                    )

                                    if share_response.ok:
                                        st.session_state[share_state_key] = (
                                            share_response.json()
                                        )
                                        st.rerun()

                                    else:
                                        st.error(
                                            "Could not create share link: "
                                            f"{get_api_error(share_response)}"
                                        )

                                except requests.exceptions.RequestException:
                                    st.error(
                                        "Could not connect to the API."
                                    )

                            share_data = st.session_state.get(share_state_key)

                            if share_data:

                                st.caption("Your read-only sharing link")

                                st.code(share_data["share_url"])

                                if share_data.get("expires_at"):
                                    st.caption(
                                        f"Expires: {share_data['expires_at']}"
                                    )
                                else:
                                    st.caption("This link does not expire.")

                                if st.button(
                                    "Revoke Share Link",
                                    key=f"revoke_share_{history_id}",
                                    use_container_width=True,
                                    type="secondary",
                                ):
                                    try:
                                        revoke_response = revoke_share_link(
                                            history_id,
                                            share_data["share_id"],
                                        )

                                        if revoke_response.ok:
                                            st.session_state.pop(
                                                share_state_key,
                                                None,
                                            )
                                            st.session_state[revoked_state_key] = True
                                            st.rerun()

                                        else:
                                            st.error(
                                                "Could not revoke share link: "
                                                f"{get_api_error(revoke_response)}"
                                            )

                                    except requests.exceptions.RequestException:
                                        st.error(
                                            "Could not connect to the API."
                                        )

                        # -------------------------
                        # DOWNLOAD
                        # -------------------------
                        elif selected_action == "download":

                            st.markdown("**Download conversation**")

                            try:
                                download_response = fetch_single_chat_history(
                                    history_id
                                )

                                if download_response.ok:

                                    download_record = download_response.json()

                                    raw_content = download_record.get(
                                        "content",
                                        "{}",
                                    )

                                    if isinstance(raw_content, str):
                                        download_content = json.loads(raw_content)
                                    else:
                                        download_content = raw_content

                                    download_title = download_record.get(
                                        "title",
                                        title,
                                    )

                                    download_type = download_record.get(
                                        "conversation_type",
                                        conversation_type,
                                    )

                                    txt_data = build_conversation_text(
                                        download_title,
                                        download_type,
                                        download_content,
                                    )

                                    pdf_data = build_conversation_pdf(
                                        download_title,
                                        download_type,
                                        download_content,
                                    )

                                    st.download_button(
                                        "Download as PDF",
                                        data=pdf_data,
                                        file_name=build_conversation_filename(
                                            download_title,
                                            "pdf",
                                        ),
                                        mime="application/pdf",
                                        key=f"download_pdf_{history_id}",
                                        use_container_width=True,
                                    )

                                    st.download_button(
                                        "Download as TXT",
                                        data=txt_data,
                                        file_name=build_conversation_filename(
                                            download_title,
                                            "txt",
                                        ),
                                        mime="text/plain",
                                        key=f"download_txt_{history_id}",
                                        use_container_width=True,
                                    )

                                else:
                                    st.warning(
                                        "Could not load this conversation "
                                        "for download."
                                    )

                            except (
                                requests.exceptions.RequestException,
                                ValueError,
                            ):
                                st.warning(
                                    "Could not prepare the conversation download."
                                )

                        # -------------------------
                        # DELETE
                        # -------------------------
                        elif selected_action == "delete":

                            st.markdown("**Delete conversation**")

                            st.warning(
                                "This action will permanently delete this conversation."
                            )

                            if st.button(
                                "Continue to delete",
                                key=f"confirm_delete_action_{history_id}",
                                use_container_width=True,
                                type="secondary",
                            ):
                                st.session_state.pop(action_key, None)

                                show_delete_confirmation(
                                    history_id,
                                    title,
                                )

    else:
        st.sidebar.warning(
            "Could not load your chat history."
        )

except requests.exceptions.RequestException:
    st.sidebar.warning(
        "Chat history is currently unavailable."
    )


# -----------------------------
# Main workspace navigation
# -----------------------------

if "active_workspace" not in st.session_state:
    st.session_state["active_workspace"] = "home"

render_cybertalk_logo()


# -----------------------------
# ChatGPT-style home screen
# -----------------------------

if st.session_state["active_workspace"] == "home":

    st.title("What would you like to work on?")

    st.write(
        "Welcome to CyberTalk. Choose a workspace to get started."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("New Discussion")

        st.write(
            "Bring two cybersecurity stakeholders together, "
            "explore different perspectives, and work towards "
            "a shared decision."
        )

        if st.button(
            "Start a New Discussion",
            type="primary",
            use_container_width=True,
        ):

            st.session_state["active_workspace"] = "discussion"
            st.rerun()

    with col2:

        st.subheader("Ask CyberTalk")

        st.write(
            "Ask an individual cybersecurity question and "
            "receive a direct answer from the AI assistant."
        )

        if st.button(
            "Ask a Question",
            use_container_width=True,
        ):

            st.session_state["active_workspace"] = "qa"
            st.rerun()

    # Do not display either workspace on the home screen.
    st.stop()


# -----------------------------
# Workspace navigation
# -----------------------------

nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 1])

with nav_col1:
    if st.button(
        "New Discussion",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["active_workspace"] == "discussion"
            else "secondary"
        ),
    ):
        st.session_state["active_workspace"] = "discussion"
        st.rerun()

with nav_col2:
    if st.button(
        "Ask CyberTalk",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["active_workspace"] == "qa"
            else "secondary"
        ),
    ):
        st.session_state["active_workspace"] = "qa"
        st.rerun()

with nav_col3:
    if st.button(
        "Home",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state["active_workspace"] == "home"
            else "secondary"
        ),
    ):
        st.session_state["active_workspace"] = "home"
        st.rerun()



# -----------------------------
# Selected workspace heading
# -----------------------------

if st.session_state["active_workspace"] == "discussion":

    st.subheader("New Discussion")

    st.caption(
        "Start a cybersecurity discussion between two stakeholders."
    )

elif st.session_state["active_workspace"] == "qa":

    st.subheader("Ask CyberTalk")

    st.caption(
        "Ask a cybersecurity question and receive a direct answer."
    )
if st.session_state["active_workspace"] == "qa":
    # -----------------------------
    # Cybersecurity Q&A
    # -----------------------------

    st.divider()

    st.header("💬 Ask a Cybersecurity Question")

    st.write(
        "Ask a cybersecurity-related question and get a direct answer "
        "from the AI assistant. This mode does not generate a stakeholder "
        "dialogue."
    )

    with st.form("qa_form"):

        question = st.text_input(
            "Your question",
            placeholder=(
                "Example: How can I protect my organization from phishing?"
            ),
            max_chars=2000,
        )

        qa_submitted = st.form_submit_button(
            "Ask CyberTalk",
            use_container_width=True,
        )


    if qa_submitted:

        if not question.strip():

            st.error("Please enter a question.")

        else:

            try:

                with st.spinner(
                    "Checking your question and generating an answer..."
                ):

                    qa_response = requests.post(
                        f"{API_URL}/ask",
                        headers=get_auth_headers(),
                        json={
                            "question": question.strip()
                        },
                        timeout=360,
                    )

                if not qa_response.ok:

                    st.error(
                        f"The CyberTalk API returned "
                        f"HTTP {qa_response.status_code}: "
                        f"{get_api_error(qa_response)}"
                    )

                else:

                    qa_result = qa_response.json()

                    st.session_state["qa_result"] = qa_result
                    st.session_state["qa_question"] = question.strip()

                    # Automatically save Q&A history.
                    try:

                        history_response = save_chat_history(
                            conversation_type="qa",
                            title=question.strip()[:500],
                            content={
                                "question": question.strip(),
                                "answer": qa_result.get("answer", ""),
                            },
                        )

                        if history_response.status_code == 201:

                            st.session_state["qa_history_saved_success"] = True

                            st.rerun()

                        else:

                            st.warning(
                                "Your answer was generated, but could not "
                                "be saved to chat history."
                            )

                    except requests.exceptions.RequestException:

                        st.warning(
                            "Your answer was generated, but chat history "
                            "could not be reached."
                        )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. Please try again."
                )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to the CyberTalk API. "
                    f"Make sure FastAPI is running at {API_URL}."
                )

            except requests.exceptions.RequestException as exc:

                st.error(f"Request failed: {exc}")

            except ValueError:

                st.error(
                    "The API returned an invalid JSON response."
                )


    # -----------------------------
    # Display Q&A conversation
    # -----------------------------
    if st.session_state.pop(
        "qa_history_saved_success",
        False,
    ):
        st.success(
            "Your conversation was saved to chat history."
        )

    qa_result = st.session_state.get("qa_result")

    if qa_result:

        displayed_question = qa_result.get(
            "question",
            st.session_state.get("qa_question", ""),
        )

        if displayed_question:

            with st.chat_message("user"):

                st.markdown(displayed_question)

        with st.chat_message("assistant"):

            st.markdown("**CyberTalk**")

            st.markdown(
                qa_result.get(
                    "answer",
                    "No answer was returned.",
                )
            )

# -----------------------------
# Stakeholder dialogue workspace
# -----------------------------
if st.session_state["active_workspace"] == "discussion":
    # -----------------------------
    # Stakeholder dialogue input
    # -----------------------------

    with st.container(border=True):

        st.markdown("### Define the discussion")

        st.caption(
            "Choose a cybersecurity topic, identify two stakeholders, "
            "and set how many rounds they should discuss."
        )

        with st.form("dialogue_form"):

            topic = st.text_area(
                "Cybersecurity topic",
                placeholder=(
                    "Example: Should our organization require "
                    "multi-factor authentication for all employees?"
                ),
                max_chars=500,
                height=120,
                help="Enter a topic containing at least 3 characters.",
            )

            st.markdown("**Discussion participants**")

            col1, col2 = st.columns(2)

            with col1:

                stakeholder_1 = st.text_input(
                    "Stakeholder 1",
                    placeholder="Example: Chief Information Security Officer",
                    max_chars=100,
                )

            with col2:

                stakeholder_2 = st.text_input(
                    "Stakeholder 2",
                    placeholder="Example: IT Operations Manager",
                    max_chars=100,
                )

            st.markdown("**Discussion settings**")

            rounds = st.number_input(
                "Number of discussion rounds",
                min_value=1,
                max_value=5,
                value=2,
                step=1,
                help=(
                    "Each round includes one response from each stakeholder. "
                    "Two additional closing statements are generated afterward."
                ),
            )

            submitted = st.form_submit_button(
                "Generate CyberTalk Dialogue",
                type="primary",
                use_container_width=True,
            )



    # -----------------------------
    # Validate and call dialogue API
    # -----------------------------

    if submitted:

        errors = []

        if len(topic.strip()) < 3:

            errors.append(
                "Enter a topic containing at least 3 characters."
            )

        if len(stakeholder_1.strip()) < 2:

            errors.append(
                "Stakeholder 1 must contain at least 2 characters."
            )

        if len(stakeholder_2.strip()) < 2:

            errors.append(
                "Stakeholder 2 must contain at least 2 characters."
            )

        if (
            stakeholder_1.strip().casefold()
            == stakeholder_2.strip().casefold()
        ):

            errors.append(
                "Please provide two different stakeholders."
            )

        if errors:

            for error in errors:
                st.error(error)

        else:

            payload = {
                "topic": topic.strip(),
                "stakeholder_1": stakeholder_1.strip(),
                "stakeholder_2": stakeholder_2.strip(),
                "rounds": int(rounds),
            }

            try:

                with st.spinner(
                    "Generating the discussion and evaluating agreement. "
                    "This may take several minutes..."
                ):

                    response = requests.post(
                        f"{API_URL}/dialogue",
                        headers=get_auth_headers(),
                        json=payload,
                        timeout=900,
                    )

                if not response.ok:

                    st.error(
                        f"The CyberTalk API returned "
                        f"HTTP {response.status_code}: "
                        f"{get_api_error(response)}"
                    )

                else:

                    result = response.json()

                    # Keep the complete result available during reruns.
                    st.session_state["cybertalk_result"] = result

                    # Automatically save dialogue history.
                    try:

                        history_response = save_chat_history(
                            conversation_type="dialogue",
                            title=result.get(
                                "topic",
                                "CyberTalk Discussion",
                            )[:500],
                            content=result,
                        )

                        if history_response.status_code == 201:

                            st.success(
                                "Your dialogue was saved to chat history."
                            )

                            st.rerun()

                        else:

                            st.warning(
                                "The dialogue was generated, but could not "
                                "be saved to chat history."
                            )

                    except requests.exceptions.RequestException:

                        st.warning(
                            "The dialogue was generated, but chat history "
                            "could not be reached."
                        )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. The local AI model may need "
                    "more time. Please try again."
                )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to the CyberTalk API. Make sure "
                    "FastAPI is running at "
                    f"{API_URL}."
                )

            except requests.exceptions.RequestException as exc:

                st.error(f"Request failed: {exc}")

            except ValueError:

                st.error(
                    "The API returned an invalid JSON response."
                )



    # -----------------------------
    # Display stakeholder dialogue
    # -----------------------------

    result = st.session_state.get("cybertalk_result")

    if result:

        st.divider()
        st.header("Discussion Results")

        st.markdown(
            f"**Topic:** {result.get('topic', 'Not provided')}"
        )

        stakeholders = result.get("stakeholders", [])

        stakeholder_names = [
            item.get("name", "Unknown stakeholder")
            for item in stakeholders
        ]

        if stakeholder_names:

            st.markdown(
                "**Stakeholders:** "
                + " and ".join(stakeholder_names)
            )

        st.markdown(
            f"**Discussion rounds:** "
            f"{result.get('rounds', 'Unknown')}"
        )

        # -----------------------------
        # AI performance metrics
        # -----------------------------

        performance = result.get("performance", {})

        if isinstance(performance, dict) and performance:

            st.divider()
            st.subheader("AI Performance")

            perf_col1, perf_col2, perf_col3 = st.columns(3)

            perf_col1.metric(
                "Dialogue generation",
                f"{performance.get('generation_seconds', 0):.2f} s",
            )

            perf_col2.metric(
                "Agreement evaluation",
                f"{performance.get('evaluation_seconds', 0):.2f} s",
            )

            perf_col3.metric(
                "Total processing time",
                f"{performance.get('total_seconds', 0):.2f} s",
            )

            st.caption(
                "Dialogue entries generated: "
                f"{performance.get('dialogue_entries', 0)}"
            )

        st.caption(
            "The final two statements are closing statements, "
            "in addition to the requested discussion rounds."
        )

        # -----------------------------
        # Stakeholder discussion
        # -----------------------------

        st.divider()
        st.subheader("Stakeholder Dialogue")

        st.caption(
            "Follow the discussion between the two stakeholders."
        )

        # Assign distinct chat styles dynamically.
        speaker_roles = {}

        if len(stakeholder_names) >= 2:

            speaker_roles = {
                stakeholder_names[0].strip().casefold(): "user",
                stakeholder_names[1].strip().casefold(): "assistant",
            }

        dialogue = result.get("dialogue", [])

        if not dialogue:

            st.warning(
                "The API returned no dialogue entries."
            )

        for entry in dialogue:

            turn_number = entry.get("turn", "?")

            speaker = entry.get(
                "speaker",
                "Unknown stakeholder",
            )

            message = entry.get("message", "")

            speaker_role = speaker_roles.get(
                speaker.strip().casefold(),
                "assistant",
            )

            with st.chat_message(speaker_role):

                st.markdown(
                    f"**Turn {turn_number} — {speaker}**"
                )

                st.write(message)


        # -----------------------------
        # Final agreement evaluation
        # -----------------------------

        st.divider()
        st.subheader("Final Agreement Evaluation")

        agreement = result.get("agreement", {})

        if not isinstance(agreement, dict):
            agreement = {}

        status = str(agreement.get("status") or "unknown")

        explanation = agreement.get(
            "explanation",
            "No explanation was provided.",
        )

        if not isinstance(explanation, str) or not explanation.strip():
            explanation = "No explanation was provided."

        status_labels = {
            "agreement_reached": "Agreement reached",
            "partial_agreement": "Partial agreement",
            "no_agreement": "No agreement",
        }

        status_label = status_labels.get(
            status,
            status.replace("_", " ").title(),
        )

        st.markdown(f"**Agreement status: {status_label}**")

        # Present the overall outcome.
        if status == "agreement_reached":
            st.success(explanation)

        elif status == "partial_agreement":
            st.warning(explanation)

        elif status == "no_agreement":
            st.error(explanation)

        else:
            st.info(explanation)

        # -----------------------------
        # Shared decision
        # -----------------------------

        st.markdown("**Shared decision**")

        shared_decision = agreement.get("shared_decision")

        if isinstance(shared_decision, str) and shared_decision.strip():

            if status == "agreement_reached":
                st.success(shared_decision)

            elif status == "no_agreement":
                st.warning(
                    "A proposed decision was provided, "
                    "but no agreement was reached."
                )
                st.write(shared_decision)

            else:
                st.info(shared_decision)

        else:
            st.info(
                "No confirmed shared decision was identified."
            )

        # -----------------------------
        # Unresolved disagreements
        # -----------------------------

        st.markdown("**Unresolved disagreements**")

        unresolved = agreement.get(
            "unresolved_disagreements",
            [],
        )

        if isinstance(unresolved, str):
            unresolved_items = [unresolved] if unresolved.strip() else []

        elif isinstance(unresolved, list):
            unresolved_items = [
                str(item).strip()
                for item in unresolved
                if item is not None and str(item).strip()
            ]

        else:
            unresolved_items = []

        if unresolved_items:

            for disagreement in unresolved_items:
                st.warning(disagreement)

        else:
            st.write(
                "No unresolved disagreements were reported."
            )

        # -----------------------------
        # Recommended next actions
        # -----------------------------

        st.markdown("**Recommended next actions**")

        next_actions = agreement.get("next_actions", [])

        if isinstance(next_actions, str):
            action_items = [next_actions] if next_actions.strip() else []

        elif isinstance(next_actions, list):
            action_items = [
                str(action).strip()
                for action in next_actions
                if action is not None and str(action).strip()
            ]

        else:
            action_items = []

        if action_items:

            for index, action in enumerate(action_items, start=1):
                st.markdown(f"{index}. {action}")

        else:
            st.write(
                "No next actions were reported."
            )
