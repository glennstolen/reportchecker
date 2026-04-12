import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.auth import (
    SESSION_TOKEN_EXPIRE_DAYS,
    create_magic_token,
    create_session_token,
    get_current_user,
    verify_token,
)
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


class RequestLinkBody(BaseModel):
    email: str


class VerifyBody(BaseModel):
    token: str


async def _send_magic_link_email(email: str, magic_link: str) -> None:
    """Send magic link email. Prints link to console if SMTP is not configured."""
    settings = get_settings()
    if not settings.smtp_user:
        print(f"\n{'=' * 60}")
        print(f"MAGIC LINK FOR {email}:")
        print(magic_link)
        print(f"{'=' * 60}\n")
        return

    def _send() -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Logg inn på ReportChecker"
        msg["From"] = settings.smtp_from
        msg["To"] = email

        text = (
            f"Klikk her for å logge inn på ReportChecker:\n\n{magic_link}\n\n"
            f"Lenken er gyldig i 15 minutter."
        )
        html = f"""<html><body>
<p>Klikk på knappen nedenfor for å logge inn på ReportChecker:</p>
<p>
  <a href="{magic_link}"
     style="background:#2563eb;color:white;padding:12px 24px;
            text-decoration:none;border-radius:6px;display:inline-block;">
    Logg inn
  </a>
</p>
<p style="color:#6b7280;font-size:14px;">
  Lenken er gyldig i 15 minutter.
  Hvis du ikke ba om dette kan du ignorere denne e-posten.
</p>
</body></html>"""
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, email, msg.as_string())

    await asyncio.to_thread(_send)


@router.post("/request-link")
async def request_magic_link(body: RequestLinkBody, db: Session = Depends(get_db)):
    """Request a magic link. Always returns the same message to prevent email enumeration."""
    settings = get_settings()
    user = (
        db.query(User)
        .filter(User.email == body.email, User.is_active == True)
        .first()
    )
    if user:
        token = create_magic_token(body.email)
        magic_link = f"{settings.app_url}/auth/verify?token={token}"
        try:
            await _send_magic_link_email(body.email, magic_link)
        except Exception as e:
            print(f"E-postsending feilet: {e}")

    return {"message": "Hvis e-posten er registrert, har du mottatt en innloggingslenke."}


@router.post("/verify")
def verify_magic_link(body: VerifyBody, response: Response, db: Session = Depends(get_db)):
    """Verify magic link token and issue a session cookie."""
    email = verify_token(body.token, "magic")
    if not email:
        raise HTTPException(status_code=400, detail="Ugyldig eller utløpt lenke")

    user = (
        db.query(User)
        .filter(User.email == email, User.is_active == True)
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Bruker ikke funnet")

    session_token = create_session_token(email)
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )
    return {"message": "Innlogget", "email": email}


@router.post("/logout")
def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(key="session", path="/")
    return {"message": "Logget ut"}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current user's email."""
    return {"email": current_user.email}
