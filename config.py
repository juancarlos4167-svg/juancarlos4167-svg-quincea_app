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

# Bono especial: durante mayo, junio, julio y agosto los empleados de
# lunes a viernes trabajan una hora mas por dia. Por ese esfuerzo cobran
# un 25% del sueldo mensual, prorrateado por dias trabajados, en la 2da
# quincena de cada uno de esos meses.
MESES_BONO_ESPECIAL = [5, 6, 7, 8]
BONO_ESPECIAL_PORCENTAJE = 0.25
BONO_ESPECIAL_DIAS_PROMEDIO = 22

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
