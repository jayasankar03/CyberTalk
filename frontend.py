
import json
import os
from datetime import datetime, timezone, timedelta

import requests
import streamlit as st

import re
from io import BytesIO
from xml.sax.saxutils import escape

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
    page_icon="🛡️",
    layout="wide",
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
    /* Minimal three-dot conversation menu button */
    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button {
        background: transparent !important;
        background-image: none !important;
        color: #d1deef !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        min-height: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        font-size: 25px !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }

    [class*="st-key-history_menu_icon_wrapper_"] .stButton > button:hover {
        background: #203b58 !important;
        color: #19c9f4 !important;
        border: none !important;
        box-shadow: none !important;
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

st.session_state.setdefault("access_token", None)


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

        status_labels = {
            "agreement_reached": "Agreement reached",
            "partial_agreement": "Partial agreement",
            "no_agreement": "No agreement",
        }

        status = agreement.get("status", "unknown")

        lines.extend([
            "FINAL AGREEMENT EVALUATION",
            "-" * 55,
            f"Status: {status_labels.get(status, status)}",
            "",
            "Explanation:",
            str(agreement.get("explanation", "Not provided")),
            "",
            "Shared decision:",
            str(agreement.get("shared_decision") or "No confirmed shared decision"),
            "",
            "Unresolved disagreements:",
        ])

        unresolved = agreement.get("unresolved_disagreements", [])

        if unresolved:
            lines.extend(f"- {item}" for item in unresolved)
        else:
            lines.append("None reported.")

        lines.extend([
            "",
            "Next actions:",
        ])

        next_actions = agreement.get("next_actions", [])

        if isinstance(next_actions, list) and next_actions:
            lines.extend(f"- {item}" for item in next_actions)
        elif isinstance(next_actions, str) and next_actions.strip():
            lines.append(next_actions)
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
                            or key.startswith("show_history_details_")
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
            st.session_state["access_token"] = None

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

                            st.session_state["access_token"] = (
                                login_data["access_token"]
                            )

                            st.session_state["show_auth_dialog"] = False

                            st.success("Login successful!")
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
    st.session_state["access_token"] = None
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
            st.session_state["access_token"] = None
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
                st.session_state["access_token"] = None
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
                                st.session_state["access_token"] = None
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
            st.session_state["access_token"] = None
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

top_spacer, profile_column = st.columns([12, 1])

with profile_column:

    if st.button(
        "👤",
        key="profile_menu_button",
        help="My Profile",
        use_container_width=True,
    ):

        st.session_state["show_profile"] = (
            not st.session_state["show_profile"]
        )

        st.rerun()


# -----------------------------
# My Profile Page
# -----------------------------

if st.session_state["show_profile"]:
    if st.button(
        "← Back to Chat",
        key="back_to_chat",
    ):
        st.session_state["show_profile"] = False
        st.session_state["edit_profile_open"] = False
        st.session_state["change_password_open"] = False
        st.rerun()

    st.title("My Profile")

    st.write(
        "View your CyberTalk account information."
    )

    st.divider()

    if st.button(
        "Edit Profile",
        key="open_edit_profile",
        use_container_width=True,
    ):
        st.session_state["edit_profile_open"] = (
            not st.session_state["edit_profile_open"]
        )
        st.session_state["change_password_open"] = False
        st.rerun()

    if st.session_state["edit_profile_open"]:
        st.subheader("Edit Profile")

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

        if save_profile:
            username = updated_username.strip()
            email = updated_email.strip().lower()

            if len(username) < 3:
                st.error("Username must contain at least 3 characters.")

            elif (
                "@" not in email
                or "." not in email.split("@")[-1]
            ):
                st.error("Please provide a valid email address.")

            elif (
                username == current_user.get("username")
                and email == current_user.get("email", "").lower()
            ):
                st.info("No profile changes were made.")

            else:
                try:
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
                        st.success(
                            "Your profile was updated successfully."
                        )
                        st.rerun()

                    elif update_response.status_code == 401:
                        st.error(
                            "Your session has expired. Please log in again."
                        )
                        st.session_state["access_token"] = None
                        st.rerun()

                    else:
                        st.error(get_api_error(update_response))

                except requests.RequestException:
                    st.error(
                        "Unable to update your profile. "
                        "Please check your connection and try again."
                    )

        st.divider()

    st.divider()
    st.subheader("Account Information")

    st.write("**User ID**")
    st.write(current_user.get("id", "N/A"))
    st.divider()

    st.write("**Account Role**")
    st.write(current_user.get("role", "user").title())
    st.divider()

    st.write("**Username**")
    st.write(current_user.get("username", "N/A"))
    st.divider()

    st.write("**Email Address**")
    st.write(current_user.get("email", "N/A"))
    st.divider()

    st.subheader("Account Details")

    created_at = current_user.get(
        "created_at",
        "Not available",
    )

    st.write("**Registration Date**")
    st.write(created_at)

    st.caption(
        "Your profile information is retrieved securely "
        "from your authenticated CyberTalk account."
    )

    if st.button(
        "Change Password",
        key="open_change_password",
        use_container_width=True,
    ):
        st.session_state["change_password_open"] = (
            not st.session_state["change_password_open"]
        )
        st.session_state["edit_profile_open"] = False
        st.rerun()

    if st.session_state["change_password_open"]:
        st.subheader("Change Password")
        st.caption("Update your account password securely.")

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
                "Change Password",
                use_container_width=True,
            )

        if change_password_submitted:
            if not current_password or not new_password or not confirm_new_password:
                st.error("Please fill in all password fields.")

            elif len(new_password) < 8:
                st.error("New password must contain at least 8 characters.")

            elif new_password != confirm_new_password:
                st.error("New passwords do not match.")

            elif new_password == current_password:
                st.error("New password must be different from the current password.")

            else:
                try:
                    response = requests.post(
                        f"{API_URL}/change-password",
                        headers=get_auth_headers(),
                        json={
                            "current_password": current_password,
                            "new_password": new_password,
                            "confirm_new_password": confirm_new_password,
                        },
                        timeout=15,
                    )

                    if response.status_code == 200:
                        st.success("Password changed successfully!")

                    elif response.status_code == 401:
                        st.session_state["access_token"] = None
                        st.error(
                            "Your session has expired. Please log in again."
                        )
                        st.rerun()

                    else:
                        st.error(get_api_error(response))

                except requests.RequestException:
                    st.error(
                        "Unable to connect to the CyberTalk server. "
                        "Please try again."
                    )

    st.divider()

    if st.button(
        "Log Out",
        use_container_width=True,
        key="profile_logout",
    ):
        st.session_state["access_token"] = None
        st.session_state["show_profile"] = False

        st.session_state["edit_profile_open"] = False
        st.session_state["change_password_open"] = False

        st.session_state.pop("qa_result", None)
        st.session_state.pop("cybertalk_result", None)

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
                        use_container_width=True,
                    ):
                        st.session_state[details_key] = not (
                            st.session_state.get(details_key, False)
                        )
                        st.rerun()

                with menu_col:
                    with st.container(
                        key=f"history_menu_icon_wrapper_{history_id}"
                    ):
                        if st.button(
                            "⋮",
                            key=f"history_menu_button_{history_id}",
                            help="Conversation actions",
                            use_container_width=True,
                        ):
                            st.session_state[menu_key] = not (
                                st.session_state.get(menu_key, False)
                            )
                            st.rerun()
                # Expanded conversation details.
                if st.session_state.get(details_key, False):
                    with st.sidebar.container():
                        st.caption(
                            f"Type: {conversation_type.upper()}"
                        )
                        st.caption(
                            f"Saved: {record['created_at']}"
                        )

                        if st.button(
                            "Open Conversation",
                            key=f"open_history_{history_id}",
                            use_container_width=True,
                        ):
                            try:
                                detail_response = (
                                    fetch_single_chat_history(history_id)
                                )

                                if detail_response.ok:
                                    saved_record = detail_response.json()
                                    saved_content = json.loads(
                                        saved_record["content"]
                                    )

                                    if (
                                        saved_record["conversation_type"]
                                        == "qa"
                                    ):
                                        if not isinstance(
                                            saved_content, dict
                                        ):
                                            raise ValueError(
                                                "Invalid saved Q&A data."
                                            )

                                        st.session_state["qa_result"] = (
                                            saved_content
                                        )
                                        st.session_state.pop(
                                            "cybertalk_result",
                                            None,
                                        )

                                    elif (
                                        saved_record["conversation_type"]
                                        == "dialogue"
                                    ):
                                        if not isinstance(
                                            saved_content, dict
                                        ):
                                            raise ValueError(
                                                "Invalid saved dialogue data."
                                            )

                                        st.session_state[
                                            "cybertalk_result"
                                        ] = saved_content
                                        st.session_state.pop(
                                            "qa_result",
                                            None,
                                        )

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
                            ):
                                st.sidebar.error(
                                    "Could not load the saved conversation."
                                )

                # Three-dot menu actions.
                if st.session_state.get(menu_key, False):
                    with st.sidebar.container(border=True):
                        st.caption("Conversation actions")

                        with st.form(
                            key=f"rename_history_form_{history_id}"
                        ):
                            new_title = st.text_input(
                                "Conversation title",
                                value=title,
                                max_chars=500,
                                key=f"rename_title_{history_id}",
                            )

                            rename_submitted = st.form_submit_button(
                                "Rename",
                                use_container_width=True,
                            )

                            if rename_submitted:
                                if not new_title.strip():
                                    st.sidebar.warning(
                                        "Conversation title cannot be empty."
                                    )

                                elif new_title.strip() == title:
                                    st.sidebar.info(
                                        "The conversation title has not changed."
                                    )

                                else:
                                    try:
                                        rename_response = rename_chat_history(
                                            history_id,
                                            new_title.strip(),
                                        )

                                        if rename_response.ok:
                                            st.session_state[menu_key] = False
                                            st.rerun()

                                        else:
                                            st.sidebar.error(
                                                "Could not rename conversation: "
                                                f"{get_api_error(rename_response)}"
                                            )

                                    except requests.exceptions.RequestException:
                                        st.sidebar.error(
                                            "Could not connect to the API."
                                        )

                        st.divider()

                        st.caption("Share or export conversation")

                        share_state_key = f"share_link_data_{history_id}"
                        revoked_state_key = f"share_revoked_{history_id}"

                        if st.session_state.pop(revoked_state_key, False):
                            st.sidebar.success("Share link revoked successfully.")

                        with st.form(key=f"share_form_{history_id}"):
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
                                disabled=bool(st.session_state.get(share_state_key)),
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
                                    st.sidebar.error(
                                        "Could not create share link: "
                                        f"{get_api_error(share_response)}"
                                    )

                            except requests.exceptions.RequestException:
                                st.sidebar.error(
                                    "Could not connect to the API."
                                )

                        share_data = st.session_state.get(share_state_key)

                        if share_data:
                            st.caption("Your read-only sharing link")

                            # Streamlit code blocks provide a copy-to-clipboard control.
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
                                        st.session_state.pop(share_state_key, None)
                                        st.session_state[revoked_state_key] = True
                                        st.rerun()

                                    else:
                                        st.sidebar.error(
                                            "Could not revoke share link: "
                                            f"{get_api_error(revoke_response)}"
                                        )

                                except requests.exceptions.RequestException:
                                    st.sidebar.error(
                                        "Could not connect to the API."
                                    )

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

                        except (requests.exceptions.RequestException, ValueError):
                            st.warning(
                                "Could not prepare the conversation download."
                            )

                        if st.button(
                            "Delete",
                            key=f"delete_history_{history_id}",
                            use_container_width=True,
                            type="secondary",
                        ):
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
# Main page heading
# -----------------------------

render_cybertalk_logo()
st.subheader("Two Chatbots, One Agreement")

st.write(
    "Bring two cybersecurity stakeholders together to discuss a topic, "
    "explore different perspectives, and identify a shared decision."
)

st.info(
    "Enter your own stakeholder roles. CyberTalk does not restrict "
    "you to predefined personas."
)


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

                        st.success(
                            "Your conversation was saved to chat history."
                        )

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
# Display Q&A result
# -----------------------------

qa_result = st.session_state.get("qa_result")

if qa_result:

    st.subheader("Answer")

    st.write(
        qa_result.get(
            "answer",
            "No answer was returned.",
        )
    )


# -----------------------------
# Stakeholder dialogue input
# -----------------------------

with st.form("dialogue_form"):

    topic = st.text_area(
        "Cybersecurity topic",
        placeholder=(
            "Example: Should our organization require "
            "multi-factor authentication for all employees?"
        ),
        max_chars=500,
        help="Enter a topic containing at least 3 characters.",
    )

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

    status = agreement.get("status", "unknown")

    explanation = agreement.get(
        "explanation",
        "No explanation was provided.",
    )

    status_labels = {
        "agreement_reached": "Agreement reached",
        "partial_agreement": "Partial agreement",
        "no_agreement": "No agreement",
    }

    status_label = status_labels.get(
        status,
        status.replace("_", " ").title(),
    )

    st.markdown(f"**Status:** {status_label}")

    # Give each agreement outcome a distinct visual treatment.
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

    if shared_decision:

        st.success(shared_decision)

    else:

        st.warning(
            "The evaluator did not identify a confirmed shared decision."
        )

    # -----------------------------
    # Unresolved disagreements
    # -----------------------------

    st.markdown("**Unresolved disagreements**")

    unresolved = agreement.get(
        "unresolved_disagreements",
        [],
    )

    if unresolved:

        for disagreement in unresolved:

            st.warning(disagreement)

    else:

        st.write(
            "No unresolved disagreements were reported."
        )

    # -----------------------------
    # Recommended next actions
    # -----------------------------

    st.markdown("**Next actions**")

    next_actions = agreement.get("next_actions", [])

    if next_actions:

        for index, action in enumerate(next_actions, start=1):

            st.write(f"{index}. {action}")

    else:

        st.write(
            "No next actions were reported."
        )
