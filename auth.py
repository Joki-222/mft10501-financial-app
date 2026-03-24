"""
auth.py — Simple authentication and role-based access control.

Three roles:
  - user:     can view dashboard, ask assistant, export memo
  - reviewer: can also view review flags, override recommendations
  - admin:    can also view all logs, change policy rules

For classroom use, passwords are stored in .streamlit/secrets.toml.
This is NOT production-grade auth — it is a teaching prototype.
"""

import streamlit as st

# ── Role definitions ─────────────────────────────────────────
ROLE_PERMISSIONS = {
    "user": {
        "view_dashboard": True,
        "ask_assistant": True,
        "export_memo": True,
        "view_flags": False,
        "override": False,
        "view_all_logs": False,
    },
    "reviewer": {
        "view_dashboard": True,
        "ask_assistant": True,
        "export_memo": True,
        "view_flags": True,
        "override": True,
        "view_all_logs": True,
    },
    "admin": {
        "view_dashboard": True,
        "ask_assistant": True,
        "export_memo": True,
        "view_flags": True,
        "override": True,
        "view_all_logs": True,
    },
}


def check_password() -> bool:
    """
    Simple password gate. Returns True if the user enters
    a valid password from secrets.toml.
    """
    if st.session_state.get("authenticated"):
        return True

    pwd = st.text_input("Enter password to continue", type="password")

    if not pwd:
        st.info("Enter the app password to proceed.")
        return False

    # Check against known passwords
    user_pw = st.secrets.get("APP_PASSWORD", "demo")
    reviewer_pw = st.secrets.get("REVIEWER_PASSWORD", "reviewer")

    if pwd == reviewer_pw:
        st.session_state["authenticated"] = True
        st.session_state["role"] = "reviewer"
        st.rerun()
    elif pwd == user_pw:
        st.session_state["authenticated"] = True
        st.session_state["role"] = "user"
        st.rerun()
    else:
        st.error("Incorrect password.")
        return False

    return False


def get_role() -> str:
    """Return the current user's role."""
    return st.session_state.get("role", "user")


def can(permission: str) -> bool:
    """Check if current role has a given permission."""
    role = get_role()
    return ROLE_PERMISSIONS.get(role, {}).get(permission, False)
