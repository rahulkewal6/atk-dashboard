import streamlit as st


def _get_users() -> dict:
    """Load user credentials from st.secrets."""
    try:
        return dict(st.secrets.get("users", {}))
    except Exception:
        return {}


def _show_login():
    """Render the branded login screen."""
    from utils.branding import inject_css
    inject_css()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='text-align:center; margin-bottom:24px;'>
                <span style='color:#FF6600; font-size:2rem; font-weight:800;'>ATK</span>
                <span style='color:#FFFFFF; font-size:2rem; font-weight:400;'> Exhibitions</span><br>
                <span style='color:#888888; font-size:0.95rem;'>Sales Dashboard — Sign In</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. rahul")
            password = st.text_input("Password", type="password", placeholder="Your password")
            submit = st.form_submit_button("Sign In", use_container_width=True)

            if submit:
                users = _get_users()
                uname = username.strip().lower()
                if uname in users:
                    user = users[uname]
                    if password == user.get("password", ""):
                        st.session_state.authenticated = True
                        st.session_state.username = uname
                        st.session_state.role = user.get("role", "editor")
                        st.session_state.display_name = user.get("display", username)
                        st.rerun()
                    else:
                        st.error("Incorrect password. Try again.")
                else:
                    st.error("Username not recognised.")


def require_login():
    """
    Call at the top of every page.
    Blocks the page and shows login form until authenticated.
    """
    if not st.session_state.get("authenticated", False):
        _show_login()
        st.stop()


def is_admin() -> bool:
    return st.session_state.get("role", "editor") == "admin"


def get_display_name() -> str:
    return st.session_state.get("display_name", "")


def can_modify(owner: str) -> bool:
    """
    True if the current user may edit/delete an item.
    Admins can modify everything; editors can modify only what they created.
    """
    if is_admin():
        return True
    return str(owner or "").strip().lower() == get_display_name().strip().lower()


def show_user_bar():
    """
    Show logged-in user info + logout button in the sidebar.
    Call this after require_login() on every page.
    """
    name = get_display_name()
    role = "Admin" if is_admin() else "Editor"
    st.sidebar.markdown(
        f"<div style='color:#AAAAAA; font-size:0.8rem; padding:4px 0;'>"
        f"Logged in as <span style='color:#FF6600; font-weight:700;'>{name}</span> "
        f"<span style='color:#555;'>({role})</span></div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Sign Out", use_container_width=True):
        for key in ["authenticated", "username", "role", "display_name"]:
            st.session_state.pop(key, None)
        st.rerun()
