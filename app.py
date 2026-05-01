"""Punto de entrada de la app de liquidacion quincenal."""

from datetime import date, timedelta

import streamlit as st

from auth import requerir_login
from config import APP_NAME, APP_ICON, DIA_PAGO_PRIMERA, DIA_PAGO_SEGUNDA, MESES
from db import init_db, get_empleados, get_liquidaciones

st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")

st.markdown("""
<style>
    .big-num {font-size: 2.4rem; font-weight: 700; color: #1f3b6f;}
    .label-soft {color: #666; font-size: 0.85rem; text-transform: uppercase;
                 letter-spacing: 0.04em;}
    .card {background: #f7f8fb; padding: 1rem 1.2rem; border-radius: 12px;
           border: 1px solid #e6e8ef;}
    div[data-testid="stMetricValue"] {color: #1f3b6f;}
</style>
""", unsafe_allow_html=True)

requerir_login()

st.title(f"{APP_ICON} {APP_NAME}")

with st.sidebar:
    st.header("⚙️ Configuración")
    if st.button("🔄 Inicializar base de datos", use_container_width=True):
        with st.spinner("Conectando con Supabase..."):
            msg = init_db()
        st.success(msg)


def _proxima_fecha_pago() -> tuple[str, int]:
    hoy = date.today()
    candidatos = []
    for i in range(0, 3):
        m = hoy.month + i
        a = hoy.year
        while m > 12:
            m -= 12
            a += 1
        for d in (DIA_PAGO_PRIMERA, DIA_PAGO_SEGUNDA):
            try:
                f = date(a, m, d)
            except ValueError:
                continue
            if f >= hoy:
                candidatos.append(f)
    candidatos.sort()
    if not candidatos:
        return ("-", 0)
    proxima = candidatos[0]
    return (proxima.strftime("%d/%m/%Y"), (proxima - hoy).days)


col_a, col_b, col_c = st.columns(3)
with col_a:
    try:
        emps = get_empleados(solo_activos=True)
        st.metric("Empleados activos", len(emps))
    except Exception as e:
        st.metric("Empleados activos", "—")
        st.caption(f"⚠️ {e}")

with col_b:
    fecha_str, dias = _proxima_fecha_pago()
    st.metric("Próxima fecha de pago", fecha_str, f"en {dias} días" if dias > 0 else "hoy")

with col_c:
    try:
        liqs = get_liquidaciones()
        hoy = date.today()
        del_mes = liqs[(liqs["anio"] == hoy.year) & (liqs["mes"] == hoy.month)]
        total = del_mes["total_calculado"].sum()
        st.metric(f"Total liquidado {MESES[hoy.month]}", f"$ {total:,.0f}".replace(",", "."))
    except Exception:
        st.metric("Total liquidado del mes", "—")

st.divider()
st.subheader("¿Por dónde empezar?")
st.markdown("""
1. **Empleados** → revisá que estén todos cargados con el sueldo correcto.
2. **Liquidación** → cargá horas extras / ausencias / adelantos de la quincena en curso.
3. **Vacaciones** → liquidá vacaciones cuando un empleado las tome.
4. **Histórico** → consultá liquidaciones de quincenas anteriores.
5. **Recibos PDF** → descargá los recibos para imprimir o mandar.
""")

st.info("👈 Usá el menú lateral para navegar.")
