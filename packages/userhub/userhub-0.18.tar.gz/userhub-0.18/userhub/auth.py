"""Async helpers for authenticating against the Chill Services user platform.

All functions here talk to the centralized API at https://chill.services/api/.
They are async-only, log failures, and return fallbacks instead of raising so
callers must inspect results explicitly.
"""

import re

from libdev.cfg import cfg
from libdev.req import fetch
from libdev.log import log


LINK = "https://chill.services/api/"


def check_phone(cont):
    """Return True if the value looks like a phone number after preprocessing."""
    return 11 <= len(str(cont)) <= 18


def pre_process_phone(cont):
    """Normalize phone numbers: strip non-digits and swap a leading 8 for 7."""

    if not cont:
        return 0

    cont = str(cont)

    if cont[0] == "8":
        cont = "7" + cont[1:]

    cont = re.sub(r"[^0-9]", "", cont)

    if not cont:
        return 0

    return int(cont)


def check_mail(cont):
    """Return True if the value matches a minimal email pattern."""
    return re.match(r".+@.+\..+", cont) is not None


def detect_type(login):
    """Heuristically classify login input as phone, mail, or login."""

    if check_phone(pre_process_phone(login)):
        return "phone"

    if check_mail(login):
        return "mail"

    return "login"


async def auth(
    project: str,
    by: str,
    token: str,
    network: int = 0,
    ip: str = None,
    locale: str = cfg("locale", "en"),
    login: str = None,
    social: int = None,
    user: str = None,
    password: str = None,
    name: str = None,
    surname: str = None,
    image: str = None,
    mail: str = None,
    utm: str = None,
    online: bool = False,
    check_password: bool = False,
):
    """
    Authenticate a user against the platform and return user info plus token.

    Args:
        project: Project identifier registered on the platform.
        by: Auth path (e.g., phone/mail/login/social/password/token).
        token: Session or temporary token; may be rotated by the platform.
        network: Social network/provider id (default 0).
        ip: Client IP address.
        locale: Preferred locale; defaults to cfg("locale", "en").
        login: User login/phone/mail identifier.
        social: Social ID for social auth flows.
        user: Explicit user identifier, when applicable.
        password: Password to validate when check_password is True.
        name: Optional name to supply on first-time auth.
        surname: Optional surname to supply on first-time auth.
        image: Optional avatar URL for social/first login.
        mail: Optional email to bind.
        utm: Traffic source identifier.
        online: Mark user as online.
        check_password: Enforce password validation server-side.

    Returns:
        tuple(user_dict_or_None, issued_token, is_new_user_bool). On non-200,
        logs the error and returns (None, token, False).
    """

    req = {
        "by": by,
        "token": token,
        "network": network,
        "ip": ip,
        "locale": locale,
        "project": project,
        "login": login,
        "social": social,
        "user": user,
        "password": password,
        "name": name,
        "surname": surname,
        "image": image,
        "mail": mail,
        "utm": utm,
        "online": online,
        "check_password": check_password,
    }

    code, res = await fetch(LINK + "account/proj/", req)
    if code != 200:
        log.error(f"{code}: {res}")
        return None, token, False
    return res["user"], res["token"], res["new"]


async def token(
    project: str,
    token: str,
    network: int = 0,
    utm: str = None,
    extra: dict = None,
    ip: str = None,
    locale: str = cfg("locale", "en"),
    user_agent: str = None,
):
    """
    Persist a session token and metadata on the platform.

    Args:
        project: Project identifier registered on the platform.
        token: Token to store/refresh (may be rotated in response).
        network: Social network/provider id (default 0).
        utm: Traffic source identifier.
        extra: Arbitrary metadata dict to persist with the token.
        ip: Client IP address.
        locale: Preferred locale; defaults to cfg("locale", "en").
        user_agent: Optional client user agent string.

    Returns:
        tuple(issued_token_or_None, user_id_or_0, status_code_int). On non-200,
        logs the error and returns (None, 0, 2).
    """

    if extra is None:
        extra = {}

    req = {
        "token": token,
        "network": network,
        "utm": utm,
        "extra": extra,
        "ip": ip,
        "locale": locale,
        "user_agent": user_agent,
        "project": project,
    }

    code, res = await fetch(LINK + "account/proj_token/", req)
    if code != 200:
        log.error(f"{code}: {res}")
        return None, 0, 2
    return res["token"], res["user"], res["status"]
