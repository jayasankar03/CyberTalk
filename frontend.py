
import os

import requests
import streamlit as st


# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="CyberTalk",
    page_icon="🛡️",
    layout="wide",
)

API_URL = os.getenv(
    "CYBERTALK_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


# -----------------------------
# Page heading
# -----------------------------

st.title("🛡️ CyberTalk")
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
# User input
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
# Validate and call the API
# -----------------------------

if submitted:
    errors = []

    if len(topic.strip()) < 3:
        errors.append("Enter a topic containing at least 3 characters.")

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
        errors.append("Please provide two different stakeholders.")

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
                    try:
                        detail = response.json().get(
                            "detail",
                            response.text,
                        )
                    except ValueError:
                        detail = response.text

                    st.error(
                        f"The CyberTalk API returned "
                        f"HTTP {response.status_code}: {detail}"
                    )
                    st.stop()

                result = response.json()

            # Keep the complete result available during reruns.
            st.session_state["cybertalk_result"] = result

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
            st.error("The API returned an invalid JSON response.")


# -----------------------------
# Display the generated result
# -----------------------------

result = st.session_state.get("cybertalk_result")

if result:
    st.divider()

    st.header("Discussion Results")

    st.markdown(f"**Topic:** {result.get('topic', 'Not provided')}")

    stakeholders = result.get("stakeholders", [])
    if stakeholders:
        names = [
            item.get("name", "Unknown stakeholder")
            for item in stakeholders
        ]
        st.markdown("**Stakeholders:** " + " and ".join(names))

    st.markdown(
        f"**Discussion rounds:** {result.get('rounds', 'Unknown')}"
    )

    st.caption(
        "The final two statements are closing statements, "
        "in addition to the requested discussion rounds."
    )

    # Display the alternating discussion.
    st.subheader("Stakeholder Dialogue")

    dialogue = result.get("dialogue", [])

    if not dialogue:
        st.warning("The API returned no dialogue entries.")

    for entry in dialogue:
        turn_number = entry.get("turn", "?")
        speaker = entry.get("speaker", "Unknown stakeholder")
        message = entry.get("message", "")

        with st.chat_message("assistant"):
            st.markdown(
                f"**Turn {turn_number} — {speaker}**"
            )
            st.write(message)

    # Display the agreement evaluation.
    st.divider()
    st.subheader("Final Agreement Evaluation")

    agreement = result.get("agreement", {})

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

    st.markdown(
        f"**Status:** {status_labels.get(status, status)}"
    )

    st.write(explanation)

    shared_decision = agreement.get("shared_decision")

    st.markdown("**Shared decision**")
    if shared_decision:
        st.success(shared_decision)
    else:
        st.warning(
            "The evaluator did not identify a confirmed shared decision."
        )

    unresolved = agreement.get("unresolved_disagreements", [])

    st.markdown("**Unresolved disagreements**")
    if unresolved:
        for disagreement in unresolved:
            st.write(f"- {disagreement}")
    else:
        st.write("No unresolved disagreements were reported.")

    next_actions = agreement.get("next_actions", [])

    st.markdown("**Next actions**")
    if next_actions:
        for action in next_actions:
            st.write(f"- {action}")
    else:
        st.write("No next actions were reported.")
