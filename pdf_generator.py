"""Generador de PDF de recibos.

- A4 horizontal, 4 recibos por hoja (en grilla 2x2).
- Cada recibo del ancho aprox de un billete argentino (~155 mm).
- Si no hay horas al 100% cargadas, no se incluye esa fila.
"""

from io import BytesIO
from typing import Iterable

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from calculo import LiquidacionQuincena, LiquidacionVacaciones, formato_pesos


PAGE_W, PAGE_H = landscape(A4)
COLS, ROWS = 2, 2
MARGIN_X = 8 * mm
MARGIN_Y = 8 * mm
GAP_X = 6 * mm
GAP_Y = 6 * mm

CARD_W = (PAGE_W - 2 * MARGIN_X - GAP_X) / COLS
CARD_H = (PAGE_H - 2 * MARGIN_Y - GAP_Y) / ROWS


def _card_origin(idx_in_page: int) -> tuple[float, float]:
    col = idx_in_page % COLS
    row = idx_in_page // COLS
    x = MARGIN_X + col * (CARD_W + GAP_X)
    y = PAGE_H - MARGIN_Y - (row + 1) * CARD_H - row * GAP_Y
    return x, y


def _draw_quincena_card(c: canvas.Canvas, x: float, y: float,
                        liq: LiquidacionQuincena,
                        meta: dict) -> None:
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    c.rect(x, y, CARD_W, CARD_H)

    pad = 4 * mm
    inner_x = x + pad
    inner_w = CARD_W - 2 * pad
    cur_y = y + CARD_H - pad

    c.setFillColor(colors.HexColor("#1f3b6f"))
    c.rect(x, cur_y - 9 * mm, CARD_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inner_x, cur_y - 6 * mm, "RECIBO DE QUINCENA")
    c.setFont("Helvetica", 8)
    titulo_periodo = f"{meta.get('quincena_label','')}  {meta.get('mes_label','')} {meta.get('anio','')}"
    c.drawRightString(x + CARD_W - pad, cur_y - 6 * mm, titulo_periodo)
    cur_y -= 14 * mm

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inner_x, cur_y, liq.nombre)
    c.setFont("Helvetica", 8)
    fpago = meta.get("fecha_pago", "")
    if fpago:
        c.drawRightString(x + CARD_W - pad, cur_y, f"Fecha de pago: {fpago}")
    cur_y -= 5 * mm

    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(inner_x, cur_y, inner_x + inner_w, cur_y)
    cur_y -= 4 * mm

    def linea(label: str, valor: str, bold: bool = False, big: bool = False) -> None:
        nonlocal cur_y
        font = "Helvetica-Bold" if bold else "Helvetica"
        size = 11 if big else 9
        c.setFont(font, size)
        c.drawString(inner_x, cur_y, label)
        c.drawRightString(inner_x + inner_w, cur_y, valor)
        cur_y -= (size * 0.45) * mm + 2.6 * mm

    def linea_3col(label: str, cant: str, vu: str, total: str) -> None:
        nonlocal cur_y
        c.setFont("Helvetica", 9)
        c.drawString(inner_x, cur_y, label)
        col_cant_x = inner_x + inner_w * 0.50
        col_vu_x = inner_x + inner_w * 0.72
        c.drawRightString(col_cant_x, cur_y, cant)
        c.drawRightString(col_vu_x, cur_y, vu)
        c.drawRightString(inner_x + inner_w, cur_y, total)
        cur_y -= 4.6 * mm

    if liq.modo_pago == "mensual":
        linea("Modalidad", "MES COMPLETO")
        linea("Sueldo mensual", formato_pesos(liq.sueldo_mensual))
    else:
        linea("Sueldo mensual", formato_pesos(liq.sueldo_mensual))
        linea("Quincena base (sueldo / 2)", formato_pesos(liq.quincena_base), bold=True)
        linea("Días trabajados", str(liq.dias_trabajados))

        c.setStrokeColor(colors.HexColor("#cccccc"))
        c.line(inner_x, cur_y + 1 * mm, inner_x + inner_w, cur_y + 1 * mm)

        c.setFont("Helvetica-Bold", 8)
        c.drawString(inner_x, cur_y, "Detalle")
        col_cant_x = inner_x + inner_w * 0.50
        col_vu_x = inner_x + inner_w * 0.72
        c.drawRightString(col_cant_x, cur_y, "Cant.")
        c.drawRightString(col_vu_x, cur_y, "Valor hora")
        c.drawRightString(inner_x + inner_w, cur_y, "Importe")
        cur_y -= 4 * mm

        if liq.hs_50 > 0:
            linea_3col(
                "Horas extras 50%",
                f"{liq.hs_50:g}",
                formato_pesos(liq.valor_hora_50),
                formato_pesos(liq.importe_extras_50),
            )
        if liq.hs_100 > 0:
            linea_3col(
                "Horas extras 100%",
                f"{liq.hs_100:g}",
                formato_pesos(liq.valor_hora_100),
                formato_pesos(liq.importe_extras_100),
            )
        if liq.hs_ausencia > 0:
            linea_3col(
                "Hs ausencia / retiro",
                f"{liq.hs_ausencia:g}",
                formato_pesos(liq.valor_hora),
                f"- {formato_pesos(liq.importe_ausencias)}",
            )
        if liq.adelantos > 0:
            adel_dia = meta.get("adelanto_fecha", "")
            label = f"Adelanto" + (f" ({adel_dia})" if adel_dia else "")
            linea(label, f"- {formato_pesos(liq.adelantos)}")
        if liq.bono_especial_aplica and liq.bono_especial_importe > 0:
            linea_3col(
                "Bono 25% (hs especiales)",
                f"{liq.bono_especial_horas_efectivas:g} hs",
                formato_pesos(liq.bono_especial_valor_hora),
                formato_pesos(liq.bono_especial_importe),
            )

    cur_y -= 1 * mm
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(inner_x, cur_y, inner_x + inner_w, cur_y)
    cur_y -= 6 * mm

    c.setFillColor(colors.HexColor("#1f3b6f"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inner_x, cur_y, "TOTAL A COBRAR")
    c.drawRightString(inner_x + inner_w, cur_y, formato_pesos(liq.total_a_cobrar))
    c.setFillColor(colors.black)


def _draw_vacaciones_card(c: canvas.Canvas, x: float, y: float,
                          liq: LiquidacionVacaciones,
                          meta: dict) -> None:
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    c.rect(x, y, CARD_W, CARD_H)

    pad = 4 * mm
    inner_x = x + pad
    inner_w = CARD_W - 2 * pad
    cur_y = y + CARD_H - pad

    c.setFillColor(colors.HexColor("#0e7c66"))
    c.rect(x, cur_y - 9 * mm, CARD_W, 9 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inner_x, cur_y - 6 * mm, "RECIBO DE VACACIONES")
    c.setFont("Helvetica", 8)
    if liq.fecha_inicio and liq.fecha_fin:
        rango = f"{liq.fecha_inicio} a {liq.fecha_fin}"
    else:
        rango = ""
    c.drawRightString(x + CARD_W - pad, cur_y - 6 * mm, rango)
    cur_y -= 14 * mm

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inner_x, cur_y, liq.nombre)
    c.setFont("Helvetica", 8)
    fpago = meta.get("fecha_pago", "")
    if fpago:
        c.drawRightString(x + CARD_W - pad, cur_y, f"Fecha de pago: {fpago}")
    cur_y -= 5 * mm

    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(inner_x, cur_y, inner_x + inner_w, cur_y)
    cur_y -= 4 * mm

    def linea(label, valor, bold=False):
        nonlocal cur_y
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, 9)
        c.drawString(inner_x, cur_y, label)
        c.drawRightString(inner_x + inner_w, cur_y, valor)
        cur_y -= 5 * mm

    linea("Sueldo mensual", formato_pesos(liq.sueldo_mensual))
    linea("Valor día vacaciones (sueldo / 25)", formato_pesos(liq.valor_dia_vacaciones))
    linea("Días de vacaciones", str(liq.dias_vacaciones))

    cur_y -= 2 * mm
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(inner_x, cur_y, inner_x + inner_w, cur_y)
    cur_y -= 6 * mm

    c.setFillColor(colors.HexColor("#0e7c66"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inner_x, cur_y, "TOTAL A COBRAR")
    c.drawRightString(inner_x + inner_w, cur_y, formato_pesos(liq.total_a_cobrar))
    c.setFillColor(colors.black)


def generar_pdf_quincena(items: Iterable[tuple[LiquidacionQuincena, dict]]) -> bytes:
    items = list(items)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    for i, (liq, meta) in enumerate(items):
        slot = i % (COLS * ROWS)
        if i > 0 and slot == 0:
            c.showPage()
        x, y = _card_origin(slot)
        _draw_quincena_card(c, x, y, liq, meta)
    c.save()
    return buf.getvalue()


def generar_pdf_vacaciones(items: Iterable[tuple[LiquidacionVacaciones, dict]]) -> bytes:
    items = list(items)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    for i, (liq, meta) in enumerate(items):
        slot = i % (COLS * ROWS)
        if i > 0 and slot == 0:
            c.showPage()
        x, y = _card_origin(slot)
        _draw_vacaciones_card(c, x, y, liq, meta)
    c.save()
    return buf.getvalue()
