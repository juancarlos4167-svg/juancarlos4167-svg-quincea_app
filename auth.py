"""Login simple por contrasena (Streamlit session)."""

import streamlit as st


def _get_password_real() -> str:
    try:
        return str(st.secrets["auth"]["password"])
    except Exception:
        return ""


def requerir_login() -> None:
    if st.session_state.get("autenticado"):
        with st.sidebar:
            if st.button("Cerrar sesión", use_container_width=True):
                st.session_state["autenticado"] = False
                st.rerun()
        return

    st.title("🔒 Acceso restringido")
    st.markdown("Ingresá la contraseña para usar la app.")
    with st.form("login_form", clear_on_submit=True):
        pw = st.text_input("Contraseña", type="password")
        ok = st.form_submit_button("Entrar", type="primary",
                                   use_container_width=True)
    if ok:
        pw_real = _get_password_real()
        if not pw_real:
            st.error("No hay contraseña configurada en secrets.toml.")
            st.stop()
        if pw and pw == pw_real:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()
