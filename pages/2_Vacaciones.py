"""Liquidacion de vacaciones (recibo aparte de la quincena)."""

from datetime import date, timedelta

import streamlit as st

from auth import requerir_login
from calculo import calcular_vacaciones, formato_pesos
from config import APP_ICON
from db import get_empleados, upsert_liquidacion

st.set_page_config(page_title="Vacaciones", page_icon=APP_ICON, layout="wide")
requerir_login()

st.title("🏖️ Liquidación de vacaciones")
st.caption("Las vacaciones se pagan en un recibo aparte. Valor día = sueldo / 25.")

empleados = get_empleados(solo_activos=True)
if empleados.empty:
    st.warning("No hay empleados cargados.")
    st.stop()

empleados = empleados[empleados["modo_pago"] != "mensual"]

opciones = {f"{r['nombre']}  —  {formato_pesos(r['sueldo_mensual'])}": int(r["id"])
            for _, r in empleados.iterrows()}
sel = st.selectbox("Empleado", options=list(opciones.keys()))
emp_id = opciones[sel]
emp = empleados[empleados["id"] == emp_id].iloc[0]
sueldo = float(emp["sueldo_mensual"])

col1, col2, col3 = st.columns(3)
with col1:
    fecha_inicio = st.date_input("Inicio de vacaciones", value=date.today())
with col2:
    dias = st.number_input("Cantidad de días", min_value=1, max_value=60, value=14, step=1)
with col3:
    fecha_fin_default = fecha_inicio + timedelta(days=int(dias) - 1)
    fecha_fin = st.date_input("Fin de vacaciones", value=fecha_fin_default)

with col1:
    fecha_pago = st.date_input("Fecha de pago", value=fecha_inicio)

liq = calcular_vacaciones(
    nombre=emp["nombre"], sueldo_mensual=sueldo, dias_vacaciones=int(dias),
    fecha_inicio=fecha_inicio.strftime("%Y-%m-%d"),
    fecha_fin=fecha_fin.strftime("%Y-%m-%d"),
)

st.divider()
mc1, mc2, mc3 = st.columns(3)
mc1.metric("Sueldo mensual", formato_pesos(sueldo))
mc2.metric("Valor día vacaciones", formato_pesos(liq.valor_dia_vacaciones))
mc3.metric("Total a cobrar", formato_pesos(liq.total_a_cobrar))

observaciones = st.text_input("Observaciones", value="")

if st.button("💾 Guardar recibo de vacaciones", type="primary"):
    payload = {
        "empleado_id": emp_id,
        "tipo": "vacaciones",
        "anio": fecha_pago.year,
        "mes": fecha_pago.month,
        "quincena": 0,
        "fecha_pago": fecha_pago.strftime("%Y-%m-%d"),
        "fecha_inicio_vac": liq.fecha_inicio,
        "fecha_fin_vac": liq.fecha_fin,
        "hs_50": 0,
        "hs_100": 0,
        "hs_ausencia": 0,
        "dias_vacaciones": int(dias),
        "adelantos": 0,
        "total_calculado": round(liq.total_a_cobrar, 2),
        "total_pagado": round(liq.total_a_cobrar, 2),
        "estado": "pendiente",
        "observaciones": observaciones,
    }
    upsert_liquidacion(payload)
    st.success(f"Recibo de vacaciones de {emp['nombre']} guardado.")
