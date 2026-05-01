"""Logica de calculo de la liquidacion quincenal y vacaciones."""

from dataclasses import dataclass, asdict
from typing import Optional

from config import (
    DIVISOR_QUINCENA, DIVISOR_DIA, DIVISOR_DIA_VACACIONES, DIVISOR_HORA,
    COEF_HORA_50, COEF_HORA_100, DIAS_QUINCENA, JORNADA_HORAS,
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


def calcular_quincena(
    nombre: str,
    sueldo_mensual: float,
    hs_50: float = 0,
    hs_100: float = 0,
    hs_ausencia: float = 0,
    adelantos: float = 0,
    modo_pago: str = "quincenal",
) -> LiquidacionQuincena:
    base = quincena_base(sueldo_mensual)
    vh = valor_hora(sueldo_mensual)
    vh50 = vh * COEF_HORA_50
    vh100 = vh * COEF_HORA_100

    if modo_pago == "mensual":
        total = sueldo_mensual
        importe_50 = 0.0
        importe_100 = 0.0
        importe_aus = 0.0
        adelantos = 0.0
        hs_50 = hs_100 = hs_ausencia = 0.0
        dias_trab = 30
        base = sueldo_mensual
    else:
        importe_50 = hs_50 * vh50
        importe_100 = hs_100 * vh100
        importe_aus = hs_ausencia * vh
        total = base + importe_50 + importe_100 - importe_aus - adelantos
        dias_trab = max(0, DIAS_QUINCENA - int(round(hs_ausencia / JORNADA_HORAS)))

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
