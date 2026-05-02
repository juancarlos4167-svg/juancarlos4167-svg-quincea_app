"""Capa de acceso a Supabase como base de datos."""

from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from supabase import Client, create_client

from config import EMPLEADOS_INICIALES

TABLA_EMPLEADOS = "empleados"
TABLA_LIQUIDACIONES = "liquidaciones"

EMPLEADOS_COLS = [
    "id", "nombre", "sueldo_mensual", "activo", "modo_pago",
    "fecha_alta", "notas",
]
LIQUIDACIONES_COLS = [
    "id", "empleado_id", "tipo", "anio", "mes", "quincena",
    "fecha_pago", "fecha_inicio_vac", "fecha_fin_vac",
    "hs_50", "hs_100", "hs_ausencia", "dias_vacaciones",
    "hs_especiales_extra", "hs_especiales_ausencia",
    "adelantos", "total_calculado", "total_pagado",
    "estado", "observaciones", "updated_at",
]


@st.cache_resource(show_spinner=False)
def _client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)


def _seed_empleados() -> list[dict]:
    """Carga empleados iniciales desde config.py o desde st.secrets[seed]."""
    if EMPLEADOS_INICIALES:
        return EMPLEADOS_INICIALES
    try:
        seed = st.secrets.get("seed", {})
        return list(seed.get("empleados", []))
    except Exception:
        return []


def init_db() -> str:
    """Precarga empleados si la tabla esta vacia."""
    cli = _client()
    res = cli.table(TABLA_EMPLEADOS).select("id", count="exact").execute()
    if res.data and len(res.data) > 0:
        return "Base de datos ya inicializada."

    seed = _seed_empleados()
    if not seed:
        return ("Base de datos lista. Sin empleados precargados — "
                "agregalos desde la pantalla \"Empleados\".")

    hoy = datetime.now().strftime("%Y-%m-%d")
    rows = [
        {
            "nombre": e["nombre"],
            "sueldo_mensual": e.get("sueldo", e.get("sueldo_mensual", 0)),
            "activo": "SI",
            "modo_pago": e.get("modo_pago", "quincenal"),
            "fecha_alta": hoy,
            "notas": e.get("notas", ""),
        }
        for e in seed
    ]
    cli.table(TABLA_EMPLEADOS).insert(rows).execute()
    return f"{len(rows)} empleados precargados."


def init_sheets() -> str:
    return init_db()


def _df_empleados(data: list[dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(columns=EMPLEADOS_COLS)
    df = pd.DataFrame(data)
    for col in EMPLEADOS_COLS:
        if col not in df.columns:
            df[col] = None
    df["sueldo_mensual"] = pd.to_numeric(df["sueldo_mensual"], errors="coerce").fillna(0.0)
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    df["nombre"] = df["nombre"].fillna("").astype(str)
    df["activo"] = df["activo"].fillna("SI").astype(str)
    df["modo_pago"] = df["modo_pago"].fillna("quincenal").astype(str)
    df["fecha_alta"] = df["fecha_alta"].fillna("").astype(str)
    df["notas"] = df["notas"].fillna("").astype(str)
    return df[EMPLEADOS_COLS].sort_values("id").reset_index(drop=True)


def get_empleados(solo_activos: bool = True) -> pd.DataFrame:
    cli = _client()
    q = cli.table(TABLA_EMPLEADOS).select("*")
    if solo_activos:
        q = q.eq("activo", "SI")
    res = q.execute()
    return _df_empleados(res.data or [])


def get_empleado_por_id(emp_id: int) -> Optional[dict]:
    cli = _client()
    res = cli.table(TABLA_EMPLEADOS).select("*").eq("id", int(emp_id)).execute()
    if not res.data:
        return None
    return res.data[0]


def upsert_empleado(empleado: dict) -> int:
    cli = _client()
    payload = {
        "nombre": empleado["nombre"],
        "sueldo_mensual": float(empleado["sueldo_mensual"]),
        "activo": empleado.get("activo", "SI"),
        "modo_pago": empleado.get("modo_pago", "quincenal"),
        "fecha_alta": _fecha_o_none(empleado.get("fecha_alta")) or datetime.now().strftime("%Y-%m-%d"),
        "notas": empleado.get("notas", "") or "",
    }
    if empleado.get("id"):
        emp_id = int(empleado["id"])
        cli.table(TABLA_EMPLEADOS).update(payload).eq("id", emp_id).execute()
        return emp_id
    res = cli.table(TABLA_EMPLEADOS).insert(payload).execute()
    return int(res.data[0]["id"])


def desactivar_empleado(emp_id: int) -> None:
    cli = _client()
    cli.table(TABLA_EMPLEADOS).update({"activo": "NO"}).eq("id", int(emp_id)).execute()


def _fecha_o_none(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        v = valor.strip()
        return v if v else None
    return str(valor)


def _df_liquidaciones(data: list[dict]) -> pd.DataFrame:
    if not data:
        return pd.DataFrame(columns=LIQUIDACIONES_COLS)
    df = pd.DataFrame(data)
    for col in LIQUIDACIONES_COLS:
        if col not in df.columns:
            df[col] = None
    for col in ["id", "empleado_id", "anio", "mes", "quincena", "dias_vacaciones"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["hs_50", "hs_100", "hs_ausencia",
                "hs_especiales_extra", "hs_especiales_ausencia",
                "adelantos", "total_calculado", "total_pagado"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["tipo", "fecha_pago", "fecha_inicio_vac", "fecha_fin_vac",
                "estado", "observaciones", "updated_at"]:
        df[col] = df[col].fillna("").astype(str)
    return df[LIQUIDACIONES_COLS]


def get_liquidaciones() -> pd.DataFrame:
    cli = _client()
    res = (cli.table(TABLA_LIQUIDACIONES).select("*")
           .order("anio", desc=True)
           .order("mes", desc=True)
           .order("quincena", desc=True)
           .execute())
    return _df_liquidaciones(res.data or [])


def buscar_liquidacion(empleado_id: int, tipo: str, anio: int, mes: int,
                       quincena: int = 0) -> Optional[dict]:
    cli = _client()
    q = (cli.table(TABLA_LIQUIDACIONES).select("*")
         .eq("empleado_id", int(empleado_id))
         .eq("tipo", tipo)
         .eq("anio", int(anio))
         .eq("mes", int(mes)))
    if tipo == "quincena":
        q = q.eq("quincena", int(quincena))
    res = q.order("id", desc=True).limit(1).execute()
    if not res.data:
        return None
    return res.data[0]


def upsert_liquidacion(liq: dict) -> int:
    cli = _client()
    payload = {
        "empleado_id": int(liq["empleado_id"]),
        "tipo": liq.get("tipo", "quincena"),
        "anio": int(liq["anio"]),
        "mes": int(liq["mes"]),
        "quincena": int(liq.get("quincena", 0) or 0),
        "fecha_pago": _fecha_o_none(liq.get("fecha_pago")),
        "fecha_inicio_vac": _fecha_o_none(liq.get("fecha_inicio_vac")),
        "fecha_fin_vac": _fecha_o_none(liq.get("fecha_fin_vac")),
        "hs_50": float(liq.get("hs_50", 0) or 0),
        "hs_100": float(liq.get("hs_100", 0) or 0),
        "hs_ausencia": float(liq.get("hs_ausencia", 0) or 0),
        "dias_vacaciones": int(liq.get("dias_vacaciones", 0) or 0),
        "hs_especiales_extra": float(liq.get("hs_especiales_extra", 0) or 0),
        "hs_especiales_ausencia": float(liq.get("hs_especiales_ausencia", 0) or 0),
        "adelantos": float(liq.get("adelantos", 0) or 0),
        "total_calculado": float(liq.get("total_calculado", 0) or 0),
        "total_pagado": float(liq.get("total_pagado", 0) or 0),
        "estado": liq.get("estado", "pendiente") or "pendiente",
        "observaciones": liq.get("observaciones", "") or "",
        "updated_at": datetime.now().isoformat(),
    }
    if liq.get("id"):
        liq_id = int(liq["id"])
        cli.table(TABLA_LIQUIDACIONES).update(payload).eq("id", liq_id).execute()
        return liq_id
    res = cli.table(TABLA_LIQUIDACIONES).insert(payload).execute()
    return int(res.data[0]["id"])


def borrar_liquidacion(liq_id: int) -> None:
    cli = _client()
    cli.table(TABLA_LIQUIDACIONES).delete().eq("id", int(liq_id)).execute()
