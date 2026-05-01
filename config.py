"""Configuracion global del programa de liquidacion quincenal."""

APP_NAME = "Liquidación Quincenal"
APP_ICON = "💵"

DIVISOR_QUINCENA = 2
DIVISOR_DIA = 30
DIVISOR_DIA_VACACIONES = 25
DIVISOR_HORA = 200
COEF_HORA_50 = 1.5
COEF_HORA_100 = 2.0
DIAS_QUINCENA = 13
JORNADA_HORAS = 8

DIA_PAGO_PRIMERA = 20
DIA_PAGO_SEGUNDA = 5

SHEET_EMPLEADOS = "EMPLEADOS"
SHEET_LIQUIDACIONES = "LIQUIDACIONES"

# Lista de empleados iniciales (vacia por defecto en el repo publico).
# Los empleados ya estan cargados en Supabase. Si necesitas re-seedear
# en una base nueva, agregalos desde la pantalla "Empleados" o configurá
# [seed] en .streamlit/secrets.toml (ver secrets.toml.example).
EMPLEADOS_INICIALES: list[dict] = []

MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
