"""Historico de liquidaciones."""

import pandas as pd
import streamlit as st

from auth import requerir_login
from calculo import formato_pesos
from config import APP_ICON, MESES
from db import get_empleados, get_liquidaciones, borrar_liquidacion

st.set_page_config(page_title="Histórico", page_icon=APP_ICON, layout="wide")
requerir_login()

st.title("📚 Histórico de liquidaciones")

df = get_liquidaciones()
if df.empty:
    st.info("Aún no hay liquidaciones guardadas.")
    st.stop()

emps = get_empleados(solo_activos=False)
nombres = dict(zip(emps["id"], emps["nombre"]))
df["empleado"] = df["empleado_id"].map(nombres)

c1, c2, c3, c4 = st.columns(4)
with c1:
    anios = sorted(df["anio"].unique(), reverse=True)
    anio = st.selectbox("Año", options=["Todos"] + list(anios))
with c2:
    mes = st.selectbox("Mes", options=["Todos"] + list(range(1, 13)),
                       format_func=lambda x: x if x == "Todos" else MESES[x])
with c3:
    tipo = st.selectbox("Tipo", options=["Todos", "quincena", "vacaciones"])
with c4:
    emp_filter = st.selectbox("Empleado", options=["Todos"] + sorted(df["empleado"].dropna().unique().tolist()))

f = df.copy()
if anio != "Todos":
    f = f[f["anio"] == anio]
if mes != "Todos":
    f = f[f["mes"] == mes]
if tipo != "Todos":
    f = f[f["tipo"] == tipo]
if emp_filter != "Todos":
    f = f[f["empleado"] == emp_filter]

f = f.sort_values(["anio", "mes", "quincena", "empleado"], ascending=[False, False, False, True])

show = f[[
    "id", "empleado", "tipo", "anio", "mes", "quincena", "fecha_pago",
    "hs_50", "hs_100", "hs_ausencia", "dias_vacaciones", "adelantos",
    "total_calculado", "total_pagado", "estado", "observaciones",
]].copy()
show["mes"] = show["mes"].apply(lambda m: MESES[m] if 1 <= m <= 12 else "")
show["total_calculado"] = show["total_calculado"].apply(formato_pesos)
show["total_pagado"] = show["total_pagado"].apply(formato_pesos)
show["adelantos"] = show["adelantos"].apply(formato_pesos)

st.dataframe(show, use_container_width=True, hide_index=True)

total = f["total_calculado"].sum()
st.markdown(f"### Total filtrado: **{formato_pesos(total)}**")

st.divider()
st.subheader("🗑️ Borrar liquidación")
ids = f["id"].tolist()
if ids:
    sel = st.selectbox("ID a borrar", options=ids)
    if st.button("Borrar", type="secondary"):
        borrar_liquidacion(int(sel))
        st.success(f"Liquidación {sel} borrada.")
        st.rerun()
