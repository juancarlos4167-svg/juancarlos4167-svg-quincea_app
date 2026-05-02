"""Pantalla de carga de liquidacion quincenal."""

from datetime import date

import pandas as pd
import streamlit as st

from auth import requerir_login
from calculo import calcular_quincena, formato_pesos, aplica_bono_especial
from config import (APP_ICON, MESES, DIA_PAGO_PRIMERA, DIA_PAGO_SEGUNDA,
                    MESES_BONO_ESPECIAL)
from db import get_empleados, buscar_liquidacion, upsert_liquidacion

st.set_page_config(page_title="Liquidación", page_icon=APP_ICON, layout="wide")
requerir_login()

st.title("💼 Liquidación quincenal")

empleados = get_empleados(solo_activos=True)
if empleados.empty:
    st.warning("No hay empleados cargados. Inicializá la base de datos desde el menú principal.")
    st.stop()

hoy = date.today()
col1, col2, col3 = st.columns(3)
with col1:
    anio = st.number_input("Año", min_value=2024, max_value=2099, value=hoy.year, step=1)
with col2:
    mes = st.selectbox("Mes", options=list(range(1, 13)),
                       format_func=lambda m: MESES[m], index=hoy.month - 1)
with col3:
    quincena = st.radio("Quincena", options=[1, 2], horizontal=True,
                        format_func=lambda q: f"{q}ra quincena" if q == 1 else f"{q}da quincena")

es_mes_especial_bono = mes in MESES_BONO_ESPECIAL
if es_mes_especial_bono and quincena == 2:
    st.success(
        f"🌟 **{MESES[mes]} es un mes con bono especial 25%**: en esta 2ª quincena se "
        "paga el plus por la hora extra diaria de lun-vie. La app suma sola las "
        "ausencias de ambas quincenas para el cálculo del prorrateo."
    )
elif es_mes_especial_bono and quincena == 1:
    st.info(
        f"ℹ️ {MESES[mes]} es un mes con bono especial 25%. El bono se paga en la "
        "**2ª quincena**, no en esta."
    )

dia_pago = DIA_PAGO_PRIMERA if quincena == 1 else DIA_PAGO_SEGUNDA
mes_pago = mes if quincena == 1 else (mes + 1 if mes < 12 else 1)
anio_pago = anio if (quincena == 1 or mes < 12) else anio + 1
try:
    fecha_pago_default = date(anio_pago, mes_pago, dia_pago).strftime("%Y-%m-%d")
except ValueError:
    fecha_pago_default = ""
fecha_pago = st.date_input("Fecha de pago", value=date.fromisoformat(fecha_pago_default)
                           if fecha_pago_default else hoy).strftime("%Y-%m-%d")

st.divider()

empleados_filtrados = empleados.copy()
if quincena == 1:
    empleados_filtrados = empleados_filtrados[empleados_filtrados["modo_pago"] != "mensual"]

st.markdown(f"### Empleados a liquidar ({len(empleados_filtrados)})")
st.caption("Sandra (modo mensual) solo aparece en la 2ª quincena.")

resultados = []

for _, emp in empleados_filtrados.iterrows():
    emp_id = int(emp["id"])
    nombre = emp["nombre"]
    sueldo = float(emp["sueldo_mensual"])
    modo = emp["modo_pago"]

    existente = buscar_liquidacion(emp_id, "quincena", anio, mes, quincena)

    hs_ausencia_q1 = 0.0
    if quincena == 2 and modo != "mensual":
        liq_q1 = buscar_liquidacion(emp_id, "quincena", anio, mes, 1)
        if liq_q1:
            hs_ausencia_q1 = float(liq_q1.get("hs_ausencia", 0) or 0)

    with st.expander(f"👤 {nombre}  —  Sueldo: {formato_pesos(sueldo)}  ({modo})",
                     expanded=False):
        if modo == "mensual":
            st.info("Modo MES COMPLETO: se paga el sueldo mensual sin descuentos ni horas extras.")
            sueldo_editable = st.number_input(
                "Sueldo a liquidar este mes", min_value=0.0, value=sueldo, step=1000.0,
                key=f"sueldo_{emp_id}", format="%.2f",
                help="Si querés cambiarlo solo para esta liquidación, edítalo acá.",
            )
            liq = calcular_quincena(nombre, sueldo_editable, modo_pago="mensual",
                                    mes=int(mes), quincena=int(quincena))
            st.markdown(f"### Total a cobrar: **{formato_pesos(liq.total_a_cobrar)}**")
            adelantos_input = 0.0
            hs50 = hs100 = hsaus = 0.0
        else:
            sueldo_editable = sueldo
            if nombre.upper() == "SEBASTIAN":
                sueldo_editable = st.number_input(
                    "Sueldo de este mes (Sebastián varía)",
                    min_value=0.0,
                    value=float(existente.get("total_calculado", 0)) * 2 if existente else sueldo,
                    step=1000.0, key=f"sueldo_seb_{emp_id}", format="%.2f",
                )
            cA, cB, cC, cD = st.columns(4)
            with cA:
                hs50 = st.number_input("Hs extras 50%", min_value=0.0, step=0.5,
                                       value=float(existente["hs_50"]) if existente else 0.0,
                                       key=f"h50_{emp_id}")
            with cB:
                hs100 = st.number_input("Hs extras 100%", min_value=0.0, step=0.5,
                                        value=float(existente["hs_100"]) if existente else 0.0,
                                        key=f"h100_{emp_id}")
            with cC:
                hsaus = st.number_input("Hs ausencia / retiro", min_value=0.0, step=0.5,
                                        value=float(existente["hs_ausencia"]) if existente else 0.0,
                                        key=f"haus_{emp_id}")
            with cD:
                adelantos_input = st.number_input("Adelantos $", min_value=0.0, step=1000.0,
                                                  value=float(existente["adelantos"]) if existente else 0.0,
                                                  key=f"adel_{emp_id}", format="%.2f")
            liq = calcular_quincena(
                nombre, sueldo_editable, hs_50=hs50, hs_100=hs100,
                hs_ausencia=hsaus, adelantos=adelantos_input, modo_pago="quincenal",
                mes=int(mes), quincena=int(quincena), hs_ausencia_q1=hs_ausencia_q1,
            )

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Quincena base", formato_pesos(liq.quincena_base))
            mc2.metric("Extras 50%", formato_pesos(liq.importe_extras_50))
            mc3.metric("Ausencias", f"- {formato_pesos(liq.importe_ausencias)}")
            mc4.metric("Adelantos", f"- {formato_pesos(adelantos_input)}")

            if liq.bono_especial_aplica:
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("🌟 Bono 25%",
                           formato_pesos(liq.bono_especial_importe))
                bc2.metric("Días efectivos",
                           f"{liq.bono_especial_dias_efectivos:g} / "
                           f"{liq.bono_especial_dias_promedio}")
                bc3.metric("Valor por día especial",
                           formato_pesos(liq.bono_especial_valor_dia))
                if hs_ausencia_q1 > 0:
                    st.caption(
                        f"💡 Se descontaron {hs_ausencia_q1:g} hs de ausencia de la "
                        f"1ª quincena del mismo mes."
                    )

            st.markdown(f"### Total a cobrar: **{formato_pesos(liq.total_a_cobrar)}**")

        observaciones = st.text_input("Observaciones", value=existente.get("observaciones", "")
                                      if existente else "", key=f"obs_{emp_id}")
        guardar = st.button("💾 Guardar liquidación", key=f"save_{emp_id}", type="primary")
        if guardar:
            obs_final = observaciones
            if liq.bono_especial_aplica and liq.bono_especial_importe > 0:
                bono_nota = (f"Bono 25% {MESES[mes]}: {formato_pesos(liq.bono_especial_importe)} "
                             f"({liq.bono_especial_dias_efectivos:g} días efectivos)")
                obs_final = f"{observaciones} | {bono_nota}".strip(" |") if observaciones else bono_nota
            payload = {
                "id": existente["id"] if existente else None,
                "empleado_id": emp_id,
                "tipo": "quincena",
                "anio": int(anio),
                "mes": int(mes),
                "quincena": int(quincena),
                "fecha_pago": fecha_pago,
                "fecha_inicio_vac": "",
                "fecha_fin_vac": "",
                "hs_50": float(hs50),
                "hs_100": float(hs100),
                "hs_ausencia": float(hsaus),
                "dias_vacaciones": 0,
                "adelantos": float(adelantos_input),
                "total_calculado": round(liq.total_a_cobrar, 2),
                "total_pagado": round(liq.total_a_cobrar, 2),
                "estado": "pendiente",
                "observaciones": obs_final,
            }
            upsert_liquidacion(payload)
            st.success(f"Liquidación de {nombre} guardada.")

        resultados.append({
            "Empleado": nombre,
            "Sueldo": liq.sueldo_mensual,
            "Quincena base": liq.quincena_base,
            "Extras 50%": liq.importe_extras_50,
            "Extras 100%": liq.importe_extras_100,
            "Ausencias": -liq.importe_ausencias,
            "Adelantos": -liq.adelantos,
            "Bono 25%": liq.bono_especial_importe,
            "Total a cobrar": liq.total_a_cobrar,
        })

st.divider()
st.markdown("### 📊 Resumen de la quincena")
df_res = pd.DataFrame(resultados)
if not df_res.empty:
    if df_res["Bono 25%"].sum() == 0:
        df_res = df_res.drop(columns=["Bono 25%"])
    formato = {c: "$ {:,.2f}".format for c in df_res.columns if c != "Empleado"}
    st.dataframe(df_res.style.format(formato), use_container_width=True, hide_index=True)
    st.markdown(
        f"#### Total a pagar de la quincena: **{formato_pesos(df_res['Total a cobrar'].sum())}**"
    )
