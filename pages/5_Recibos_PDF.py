"""Generacion de recibos en PDF."""

from datetime import date

import streamlit as st

from auth import requerir_login
from calculo import calcular_quincena, calcular_vacaciones, formato_pesos
from config import APP_ICON, MESES
from db import get_empleados, get_liquidaciones
from pdf_generator import generar_pdf_quincena, generar_pdf_vacaciones

st.set_page_config(page_title="Recibos PDF", page_icon=APP_ICON, layout="wide")
requerir_login()

st.title("🖨️ Recibos en PDF")
st.caption("Generá el PDF de los recibos guardados. 4 recibos por hoja, A4 horizontal.")

df = get_liquidaciones()
emps = get_empleados(solo_activos=False)
if df.empty:
    st.warning("No hay liquidaciones guardadas todavía.")
    st.stop()

nombres = dict(zip(emps["id"], emps["nombre"]))
sueldos = dict(zip(emps["id"], emps["sueldo_mensual"]))
modo_pago = dict(zip(emps["id"], emps["modo_pago"]))

tab_q, tab_v = st.tabs(["📄 Quincena", "🏖️ Vacaciones"])

with tab_q:
    sub = df[df["tipo"] == "quincena"]
    if sub.empty:
        st.info("Sin recibos de quincena.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            anios = sorted(sub["anio"].unique(), reverse=True)
            anio = st.selectbox("Año", options=anios, key="q_anio")
        with c2:
            meses_disp = sorted(sub[sub["anio"] == anio]["mes"].unique())
            mes = st.selectbox("Mes", options=meses_disp,
                               format_func=lambda m: MESES[m], key="q_mes")
        with c3:
            quincena = st.radio("Quincena", options=[1, 2], horizontal=True, key="q_q")

        seleccion = sub[(sub["anio"] == anio) & (sub["mes"] == mes)
                        & (sub["quincena"] == quincena)].copy()
        seleccion["empleado"] = seleccion["empleado_id"].map(nombres)
        seleccion = seleccion.sort_values("empleado")

        if seleccion.empty:
            st.warning("No hay liquidaciones para ese período.")
        else:
            st.write(f"**{len(seleccion)} recibos** seleccionados:")
            st.dataframe(
                seleccion[["empleado", "fecha_pago", "hs_50", "hs_100",
                           "hs_ausencia", "adelantos", "total_calculado"]],
                use_container_width=True, hide_index=True,
            )

            items = []
            for _, row in seleccion.iterrows():
                emp_id = int(row["empleado_id"])
                sueldo = float(sueldos.get(emp_id, 0.0))
                liq = calcular_quincena(
                    nombre=nombres.get(emp_id, "?"),
                    sueldo_mensual=sueldo if modo_pago.get(emp_id) != "mensual" else float(row["total_calculado"]),
                    hs_50=float(row["hs_50"]),
                    hs_100=float(row["hs_100"]),
                    hs_ausencia=float(row["hs_ausencia"]),
                    adelantos=float(row["adelantos"]),
                    modo_pago=modo_pago.get(emp_id, "quincenal"),
                )
                meta = {
                    "anio": int(row["anio"]),
                    "mes_label": MESES[int(row["mes"])],
                    "quincena_label": "1ª QUINCENA" if int(row["quincena"]) == 1 else "2ª QUINCENA",
                    "fecha_pago": row["fecha_pago"],
                }
                items.append((liq, meta))

            pdf_bytes = generar_pdf_quincena(items)
            nombre_pdf = f"recibos_{anio}_{int(mes):02d}_q{quincena}.pdf"
            st.download_button(
                f"⬇️ Descargar PDF ({nombre_pdf})",
                data=pdf_bytes, file_name=nombre_pdf, mime="application/pdf",
                type="primary", use_container_width=True,
            )

with tab_v:
    sub = df[df["tipo"] == "vacaciones"]
    if sub.empty:
        st.info("Sin recibos de vacaciones.")
    else:
        sub2 = sub.copy()
        sub2["empleado"] = sub2["empleado_id"].map(nombres)
        sub2["periodo"] = sub2.apply(
            lambda r: f"{r['fecha_inicio_vac']} a {r['fecha_fin_vac']}", axis=1)
        st.dataframe(
            sub2[["empleado", "periodo", "dias_vacaciones",
                  "fecha_pago", "total_calculado"]],
            use_container_width=True, hide_index=True,
        )

        ids = st.multiselect("Recibos a incluir en el PDF",
                             options=sub2["id"].tolist(),
                             format_func=lambda i: f"{sub2[sub2['id']==i]['empleado'].iloc[0]} ({sub2[sub2['id']==i]['periodo'].iloc[0]})",
                             default=sub2["id"].tolist())
        seleccion = sub2[sub2["id"].isin(ids)]
        if not seleccion.empty:
            items = []
            for _, row in seleccion.iterrows():
                emp_id = int(row["empleado_id"])
                liq = calcular_vacaciones(
                    nombre=nombres.get(emp_id, "?"),
                    sueldo_mensual=float(sueldos.get(emp_id, 0.0)),
                    dias_vacaciones=int(row["dias_vacaciones"]),
                    fecha_inicio=row["fecha_inicio_vac"],
                    fecha_fin=row["fecha_fin_vac"],
                )
                meta = {"fecha_pago": row["fecha_pago"]}
                items.append((liq, meta))
            pdf_bytes = generar_pdf_vacaciones(items)
            st.download_button(
                "⬇️ Descargar PDF de vacaciones",
                data=pdf_bytes, file_name="recibos_vacaciones.pdf",
                mime="application/pdf", type="primary", use_container_width=True,
            )
