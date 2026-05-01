"""ABM de empleados."""

from datetime import date

import streamlit as st

from auth import requerir_login
from calculo import formato_pesos
from config import APP_ICON
from db import get_empleados, upsert_empleado, desactivar_empleado

st.set_page_config(page_title="Empleados", page_icon=APP_ICON, layout="wide")
requerir_login()

st.title("👥 Empleados")

tab_lista, tab_nuevo = st.tabs(["📋 Lista / Edición", "➕ Nuevo empleado"])

with tab_lista:
    df = get_empleados(solo_activos=False)
    if df.empty:
        st.info("No hay empleados cargados.")
    else:
        df_show = df.copy()
        df_show["sueldo_mensual"] = df_show["sueldo_mensual"].apply(formato_pesos)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("✏️ Editar empleado")
        opciones = {f"{r['nombre']} (id {r['id']})": int(r["id"])
                    for _, r in df.iterrows()}
        sel = st.selectbox("Seleccionar", options=list(opciones.keys()))
        emp_id = opciones[sel]
        emp = df[df["id"] == emp_id].iloc[0]

        with st.form(f"edit_{emp_id}"):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre", value=emp["nombre"])
                sueldo = st.number_input("Sueldo mensual", min_value=0.0,
                                         value=float(emp["sueldo_mensual"]), step=1000.0,
                                         format="%.2f")
                modo_pago = st.selectbox("Modo de pago",
                                         ["quincenal", "mensual"],
                                         index=0 if emp["modo_pago"] == "quincenal" else 1)
            with c2:
                activo = st.selectbox("Activo", ["SI", "NO"],
                                      index=0 if str(emp["activo"]).upper() == "SI" else 1)
                fecha_alta = st.text_input("Fecha de alta", value=str(emp.get("fecha_alta", "")))
                notas = st.text_area("Notas", value=str(emp.get("notas", "")))

            colb1, colb2 = st.columns([1, 1])
            with colb1:
                guardar = st.form_submit_button("💾 Guardar cambios", type="primary",
                                                use_container_width=True)
            with colb2:
                desactivar = st.form_submit_button("🚫 Desactivar empleado",
                                                   use_container_width=True)

            if guardar:
                upsert_empleado({
                    "id": emp_id,
                    "nombre": nombre,
                    "sueldo_mensual": sueldo,
                    "activo": activo,
                    "modo_pago": modo_pago,
                    "fecha_alta": fecha_alta,
                    "notas": notas,
                })
                st.success(f"{nombre} actualizado.")
                st.rerun()
            if desactivar:
                desactivar_empleado(emp_id)
                st.success(f"{nombre} desactivado.")
                st.rerun()

with tab_nuevo:
    with st.form("nuevo"):
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre")
            sueldo = st.number_input("Sueldo mensual", min_value=0.0, step=1000.0,
                                     format="%.2f")
            modo_pago = st.selectbox("Modo de pago", ["quincenal", "mensual"])
        with c2:
            fecha_alta = st.date_input("Fecha de alta", value=date.today()).strftime("%Y-%m-%d")
            notas = st.text_area("Notas")
        ok = st.form_submit_button("➕ Crear empleado", type="primary", use_container_width=True)
        if ok:
            if not nombre.strip():
                st.error("Falta el nombre.")
            else:
                upsert_empleado({
                    "id": None,
                    "nombre": nombre.strip(),
                    "sueldo_mensual": sueldo,
                    "activo": "SI",
                    "modo_pago": modo_pago,
                    "fecha_alta": fecha_alta,
                    "notas": notas,
                })
                st.success(f"{nombre} creado.")
                st.rerun()
