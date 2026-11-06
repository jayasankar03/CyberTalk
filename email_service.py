import os
import smtplib
import ssl
import html
from email.message import EmailMessage
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

def build_password_reset_link(
    reset_url: str,
    reset_token: str,
    recipient_email: str,
) -> str:
    """Build a password-reset URL after strict security validation."""

    environment = (
        os.getenv("CYBERTALK_ENV") or ""
    ).strip().lower()

    if environment not in {"development", "production"}:
        raise RuntimeError(
            "Invalid or missing CyberTalk environment configuration."
        )

    if not all((reset_url, reset_token, recipient_email)):
        raise RuntimeError(
            "Invalid password-reset URL configuration."
        )

    # Reject whitespace, control characters and backslashes.
    if (
        any(ord(char) < 32 or ord(char) == 127 for char in reset_url)
        or any(char.isspace() for char in reset_url)
        or "\\" in reset_url
    ):
        raise RuntimeError("Unsafe password-reset URL.")

    try:
        parsed_url = urlsplit(reset_url)
        hostname = parsed_url.hostname
        port = parsed_url.port
    except ValueError:
        raise RuntimeError("Invalid password-reset URL.") from None

    if (
        not hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
        or parsed_url.fragment
    ):
        raise RuntimeError("Unsafe password-reset URL.")

    hostname = hostname.lower().rstrip(".")

    if environment == "development":
        # Local HTTP is permitted only on the Streamlit development port.
        if (
            parsed_url.scheme.lower() != "http"
            or hostname not in {"localhost", "127.0.0.1", "::1"}
            or port != 8501
        ):
            raise RuntimeError(
                "Untrusted development password-reset URL."
            )

    else:
        # Production must use HTTPS and an explicitly trusted hostname.
        allowed_hosts = {
            host.strip().lower().rstrip(".")
            for host in (
                os.getenv(
                    "CYBERTALK_PASSWORD_RESET_ALLOWED_HOSTS"
                ) or ""
            ).split(",")
            if host.strip()
        }

        if (
            parsed_url.scheme.lower() != "https"
            or hostname not in allowed_hosts
            or port not in (None, 443)
        ):
            raise RuntimeError(
                "Untrusted production password-reset URL."
            )

    # Preserve unrelated query parameters, but replace existing
    # token/email values to prevent duplicate parameter injection.
    query_parameters = [
        (key, value)
        for key, value in parse_qsl(
            parsed_url.query,
            keep_blank_values=True,
        )
        if key not in {"token", "email"}
    ]

    query_parameters.extend([
        ("token", reset_token),
        ("email", recipient_email),
    ])

    return urlunsplit((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        urlencode(query_parameters),
        "",
    ))

def send_password_reset_email(
    recipient_email: str,
    reset_token: str,
) -> None:
    """Send a password-reset link using the configured SMTP server."""

    smtp_host = (os.getenv("CYBERTALK_SMTP_HOST") or "").strip()

    smtp_port_value = (
        os.getenv("CYBERTALK_SMTP_PORT", "587").strip()
    )

    smtp_username = (
        os.getenv("CYBERTALK_SMTP_USERNAME") or ""
    ).strip()

    smtp_password = (
        os.getenv("CYBERTALK_SMTP_PASSWORD") or ""
    ).strip()

    sender_email = (
        os.getenv("CYBERTALK_SMTP_FROM_EMAIL") or ""
    ).strip()
    reset_url = (
    os.getenv("CYBERTALK_PASSWORD_RESET_URL") or ""
    ).strip()

    password_reset_link = build_password_reset_link(
        reset_url=reset_url,
        reset_token=reset_token,
        recipient_email=recipient_email,
    )

    required_settings = {
    "CYBERTALK_SMTP_HOST": smtp_host,
    "CYBERTALK_SMTP_USERNAME": smtp_username,
    "CYBERTALK_SMTP_PASSWORD": smtp_password,
    "CYBERTALK_SMTP_FROM_EMAIL": sender_email,
    }

    missing_settings = [
        name for name, value in required_settings.items() if not value
    ]

    if missing_settings:
        raise RuntimeError(
            "Password-reset email settings are incomplete."
        )

    try:
        smtp_port = int(smtp_port_value)
    except (TypeError, ValueError):
        raise RuntimeError(
            "Invalid SMTP port configuration."
        ) from None

    if not 1 <= smtp_port <= 65535:
        raise RuntimeError(
            "Invalid SMTP port configuration."
        )

    # Add the token and recipient to the configured reset page URL.
    parsed_url = urlsplit(reset_url)
    query_parameters = dict(parse_qsl(parsed_url.query))
    query_parameters.update({
        "token": reset_token,
        "email": recipient_email,
    })

    password_reset_link = urlunsplit((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        urlencode(query_parameters),
        parsed_url.fragment,
    ))

    message = EmailMessage()
    message["Subject"] = "Reset Your CyberTalk Password"
    message["From"] = sender_email
    message["To"] = recipient_email

    # Plain-text version for email clients without HTML support.
    plain_text = (
        "Hello,\n\n"
        "We received a request to reset your CyberTalk password.\n\n"
        "To choose a new password, open the following link:\n"
        f"{password_reset_link}\n\n"
        "This link expires in 30 minutes and can only be used once.\n\n"
        "If you did not request this password reset, you can safely "
        "ignore this email. Your password will remain unchanged.\n\n"
        "For your security, never share this link with anyone.\n\n"
        "Regards,\n"
        "CyberTalk Security Team"
    )

    message.set_content(plain_text)
    html_safe_reset_link = html.escape(
        password_reset_link,
        quote=True,
    )
# HTML version for modern email clients.
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberTalk Password Reset</title>
</head>
<body style="
    margin: 0;
    padding: 30px 15px;
    background-color: #f3f4f6;
    font-family: Arial, Helvetica, sans-serif;
    color: #1f2937;
">
    <table width="100%" cellpadding="0" cellspacing="0"
           style="max-width: 600px; margin: auto;
                  background-color: #ffffff;
                  border-radius: 10px; overflow: hidden;">

        <tr>
            <td style="
                background-color: #111827;
                padding: 28px;
                text-align: center;
            ">
                <h1 style="
                    margin: 0;
                    color: #ffffff;
                    font-size: 26px;
                    letter-spacing: 1px;
                ">
                    CyberTalk
                </h1>
                <p style="
                    margin: 8px 0 0;
                    color: #cbd5e1;
                    font-size: 13px;
                ">
                    Cybersecurity Collaboration Platform
                </p>
            </td>
        </tr>

        <tr>
            <td style="padding: 35px 30px;">

                <h2 style="
                    margin-top: 0;
                    color: #111827;
                    font-size: 22px;
                ">
                    Reset Your Password
                </h2>

                <p style="font-size: 15px; line-height: 1.7;">
                    Hello,
                </p>

                <p style="font-size: 15px; line-height: 1.7;">
                    We received a request to reset your CyberTalk
                    account password. Click the button below to
                    choose a new password.
                </p>

                <table cellpadding="0" cellspacing="0"
                       style="margin: 28px auto;">
                    <tr>
                        <td style="
                            background-color: #2563eb;
                            border-radius: 6px;
                            text-align: center;
                        ">
                            <a href="{html_safe_reset_link}"
                               style="
                                   display: inline-block;
                                   padding: 14px 30px;
                                   color: #ffffff;
                                   text-decoration: none;
                                   font-size: 15px;
                                   font-weight: bold;
                               ">
                                Reset Password
                            </a>
                        </td>
                    </tr>
                </table>

                <p style="font-size: 14px; line-height: 1.7;">
                    This link expires in <strong>30 minutes</strong>
                    and can only be used once.
                </p>

                <p style="font-size: 14px; line-height: 1.7;">
                    If the button does not work, copy and paste
                    this link into your browser:
                </p>

                <p style="
                    font-size: 12px;
                    line-height: 1.6;
                    word-break: break-all;
                    color: #2563eb;
                ">
                    <a href="{html_safe_reset_link}"
                       style="color: #2563eb;">
                        {html_safe_reset_link}
                    </a>
                </p>

                <hr style="
                    border: none;
                    border-top: 1px solid #e5e7eb;
                    margin: 28px 0;
                ">

                <p style="
                    font-size: 13px;
                    line-height: 1.7;
                    color: #4b5563;
                ">
                    <strong>Security notice:</strong>
                    If you did not request this password reset,
                    you can safely ignore this email.
                    Your password will remain unchanged.
                </p>

                <p style="
                    font-size: 13px;
                    line-height: 1.7;
                    color: #4b5563;
                ">
                    For your security, never share this reset link
                    with anyone.
                </p>

                <p style="
                    margin-top: 30px;
                    font-size: 14px;
                    line-height: 1.6;
                ">
                    Regards,<br>
                    <strong>CyberTalk Security Team</strong>
                </p>

            </td>
        </tr>

        <tr>
            <td style="
                background-color: #f9fafb;
                padding: 18px;
                text-align: center;
                color: #6b7280;
                font-size: 11px;
            ">
                This is an automated security email from CyberTalk.
                Please do not reply.
            </td>
        </tr>

    </table>
</body>
</html>
"""

    message.add_alternative(html_content, subtype="html")

    tls_context = ssl.create_default_context()

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(
                smtp_host,
                smtp_port,
                context=tls_context,
                timeout=20,
            ) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(message)

        else:
            with smtplib.SMTP(
                smtp_host,
                smtp_port,
                timeout=20,
            ) as server:
                server.ehlo()
                server.starttls(context=tls_context)
                server.ehlo()
                server.login(smtp_username, smtp_password)
                server.send_message(message)

    except (
        smtplib.SMTPException,
        OSError,
        ssl.SSLError,
        TimeoutError,
    ):
        raise RuntimeError(
            "Password-reset email delivery failed."
        ) from None