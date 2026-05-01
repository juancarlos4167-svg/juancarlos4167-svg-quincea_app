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

EMPLEADOS_INICIALES = [
    {"nombre": "SEBASTIAN",  "sueldo": 1100000.00, "modo_pago": "quincenal", "notas": "Sueldo en blanco, varía mes a mes"},
    {"nombre": "AGUSTIN",    "sueldo": 1003241.54, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "JONATHAN",   "sueldo": 1003241.54, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "FRANCO",     "sueldo": 1003241.54, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "GONZALO1",   "sueldo": 1003241.54, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "SANDRA",     "sueldo": 1250000.00, "modo_pago": "mensual",   "notas": "Cobra mes completo el día 5"},
    {"nombre": "NAHUEL",     "sueldo":  801248.00, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "EZEQUIEL",   "sueldo":  842000.00, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "JOEL",       "sueldo":  750000.00, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "CRISTIAN",   "sueldo":  750000.00, "modo_pago": "quincenal", "notas": ""},
    {"nombre": "GONZALO2",   "sueldo":  750000.00, "modo_pago": "quincenal", "notas": ""},
]

MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
