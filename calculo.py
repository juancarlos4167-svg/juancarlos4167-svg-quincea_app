"""Logica de calculo de la liquidacion quincenal y vacaciones."""

from dataclasses import dataclass, asdict, field
from typing import Optional

from config import (
    DIVISOR_QUINCENA, DIVISOR_DIA, DIVISOR_DIA_VACACIONES, DIVISOR_HORA,
    COEF_HORA_50, COEF_HORA_100, DIAS_QUINCENA, JORNADA_HORAS,
    MESES_BONO_ESPECIAL, BONO_ESPECIAL_PORCENTAJE, BONO_ESPECIAL_DIAS_PROMEDIO,
)


@dataclass
class LiquidacionQuincena:
    nombre: str
    sueldo_mensual: float
    quincena_base: float
    valor_dia: float
    valor_hora: float
    valor_hora_50: float
    valor_hora_100: float
    dias_trabajados: int
    hs_50: float
    hs_100: float
    hs_ausencia: float
    adelantos: float
    importe_extras_50: float
    importe_extras_100: float
    importe_ausencias: float
    total_a_cobrar: float
    modo_pago: str
    bono_especial_aplica: bool = False
    bono_especial_importe: float = 0.0
    bono_especial_valor_hora: float = 0.0
    bono_especial_horas_efectivas: float = 0.0
    bono_especial_horas_base: int = 0
    hs_especiales_extra: float = 0.0
    hs_especiales_ausencia: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LiquidacionVacaciones:
    nombre: str
    sueldo_mensual: float
    valor_dia_vacaciones: float
    dias_vacaciones: int
    fecha_inicio: str
    fecha_fin: str
    total_a_cobrar: float

    def to_dict(self) -> dict:
        return asdict(self)


def valor_dia(sueldo: float) -> float:
    return sueldo / DIVISOR_DIA


def valor_dia_vacaciones(sueldo: float) -> float:
    return sueldo / DIVISOR_DIA_VACACIONES


def valor_hora(sueldo: float) -> float:
    return sueldo / DIVISOR_HORA


def valor_hora_50(sueldo: float) -> float:
    return valor_hora(sueldo) * COEF_HORA_50


def valor_hora_100(sueldo: float) -> float:
    return valor_hora(sueldo) * COEF_HORA_100


def quincena_base(sueldo: float) -> float:
    return sueldo / DIVISOR_QUINCENA


def aplica_bono_especial(mes: int, quincena: int, modo_pago: str) -> bool:
    """El bono se paga en la 2da quincena de mayo, junio, julio y agosto.
    No aplica al modo mensual (Sandra)."""
    if modo_pago == "mensual":
        return False
    return mes in MESES_BONO_ESPECIAL and quincena == 2


def calcular_bono_especial(
    sueldo_mensual: float,
    hs_especiales_extra_total_mes: float,
    hs_especiales_ausencia_total_mes: float,
    horas_base: int = BONO_ESPECIAL_DIAS_PROMEDIO,
    porcentaje: float = BONO_ESPECIAL_PORCENTAJE,
) -> tuple[float, float, float]:
    """Bono 25% en funcion de horas especiales.

    Devuelve (bono_pagado, valor_hora_especial, horas_efectivas).
    """
    bono_total = sueldo_mensual * porcentaje
    if horas_base <= 0:
        return 0.0, 0.0, 0.0
    valor_hora_especial = bono_total / horas_base
    horas_efectivas = max(
        0.0,
        horas_base + (hs_especiales_extra_total_mes or 0)
        - (hs_especiales_ausencia_total_mes or 0),
    )
    bono_pagado = valor_hora_especial * horas_efectivas
    return bono_pagado, valor_hora_especial, horas_efectivas


def calcular_quincena(
    nombre: str,
    sueldo_mensual: float,
    hs_50: float = 0,
    hs_100: float = 0,
    hs_ausencia: float = 0,
    adelantos: float = 0,
    modo_pago: str = "quincenal",
    mes: int = 0,
    quincena: int = 0,
    hs_especiales_extra: float = 0,
    hs_especiales_ausencia: float = 0,
    hs_especiales_extra_q1: float = 0,
    hs_especiales_ausencia_q1: float = 0,
) -> LiquidacionQuincena:
    base = quincena_base(sueldo_mensual)
    vh = valor_hora(sueldo_mensual)
    vh50 = vh * COEF_HORA_50
    vh100 = vh * COEF_HORA_100

    bono_aplica = False
    bono_importe = 0.0
    bono_valor_hora = 0.0
    bono_horas_efectivas = 0.0

    if modo_pago == "mensual":
        total = sueldo_mensual
        importe_50 = 0.0
        importe_100 = 0.0
        importe_aus = 0.0
        adelantos = 0.0
        hs_50 = hs_100 = hs_ausencia = 0.0
        hs_especiales_extra = hs_especiales_ausencia = 0.0
        dias_trab = 30
        base = sueldo_mensual
    else:
        importe_50 = hs_50 * vh50
        importe_100 = hs_100 * vh100
        importe_aus = hs_ausencia * vh
        total = base + importe_50 + importe_100 - importe_aus - adelantos
        dias_trab = max(0, DIAS_QUINCENA - int(round(hs_ausencia / JORNADA_HORAS)))

        if aplica_bono_especial(mes, quincena, modo_pago):
            hs_extra_total = (hs_especiales_extra_q1 or 0) + (hs_especiales_extra or 0)
            hs_aus_esp_total = (hs_especiales_ausencia_q1 or 0) + (hs_especiales_ausencia or 0)
            bono_importe, bono_valor_hora, bono_horas_efectivas = (
                calcular_bono_especial(sueldo_mensual, hs_extra_total, hs_aus_esp_total)
            )
            bono_aplica = True
            total += bono_importe

    return LiquidacionQuincena(
        nombre=nombre,
        sueldo_mensual=sueldo_mensual,
        quincena_base=base,
        valor_dia=valor_dia(sueldo_mensual),
        valor_hora=vh,
        valor_hora_50=vh50,
        valor_hora_100=vh100,
        dias_trabajados=dias_trab,
        hs_50=hs_50,
        hs_100=hs_100,
        hs_ausencia=hs_ausencia,
        adelantos=adelantos,
        importe_extras_50=importe_50,
        importe_extras_100=importe_100,
        importe_ausencias=importe_aus,
        total_a_cobrar=total,
        modo_pago=modo_pago,
        bono_especial_aplica=bono_aplica,
        bono_especial_importe=bono_importe,
        bono_especial_valor_hora=bono_valor_hora,
        bono_especial_horas_efectivas=bono_horas_efectivas,
        bono_especial_horas_base=BONO_ESPECIAL_DIAS_PROMEDIO if bono_aplica else 0,
        hs_especiales_extra=hs_especiales_extra,
        hs_especiales_ausencia=hs_especiales_ausencia,
    )


def calcular_vacaciones(
    nombre: str,
    sueldo_mensual: float,
    dias_vacaciones: int,
    fecha_inicio: str = "",
    fecha_fin: str = "",
) -> LiquidacionVacaciones:
    vd = valor_dia_vacaciones(sueldo_mensual)
    return LiquidacionVacaciones(
        nombre=nombre,
        sueldo_mensual=sueldo_mensual,
        valor_dia_vacaciones=vd,
        dias_vacaciones=dias_vacaciones,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        total_a_cobrar=vd * dias_vacaciones,
    )


def formato_pesos(valor: float) -> str:
    if valor is None:
        return "$ 0,00"
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}"
