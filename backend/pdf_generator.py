from pathlib import Path
from datetime import datetime
import re

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader


# =========================================================
# BASIC SETTINGS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

QR_PATH = BASE_DIR / "assets" / "upi-qr.png"

FIXED = {
    "company_name": "AMAAN TOUR AND TRAVELS",

    "bank_name": "STATE BANK OF INDIA",
    "bank_account": "30938200536",
    "bank_ifsc": "SBIN0000060",
    "account_name": "Abdul Talib khan",

    "upi_id": "talibamankhan@oksbi",

    "signature": "AUTHORIZED SIGNATURE",
}


PAGE_W, PAGE_H = A4


# =========================================================
# HELPERS
# =========================================================

def money(value):
    """
    Format amount.

    Examples:
        1999       -> 1,999/-
        1999.78    -> 1,999.78/-
    """

    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0

    if amount.is_integer():
        return f"{int(amount):,}/-"

    return f"{amount:,.2f}/-"


def clean_filename(value):
    value = str(value or "bill").strip()

    value = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        value
    )

    return value[:80] or "bill"


def format_date(value):
    """
    Convert HTML date:
        2026-09-17

    Into:
        17/09/2026
    """

    if not value:
        return ""

    value = str(value).strip()

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).strftime("%d/%m/%Y")

    except ValueError:
        return value


def validate(data):

    if not data:
        raise ValueError(
            "No bill data received."
        )

    items = data.get("items") or []

    if not items:
        raise ValueError(
            "Add at least one journey/service row."
        )


def fit_font(c, text, max_width, font="Helvetica", size=10, minimum=6):

    text = str(text or "")

    current = size

    while current > minimum:

        width = c.stringWidth(
            text,
            font,
            current
        )

        if width <= max_width:
            break

        current -= 0.5

    return current


def draw_center(
    c,
    text,
    x,
    y,
    width,
    font="Helvetica",
    size=10
):

    text = str(text or "")

    actual_size = fit_font(
        c,
        text,
        width - 4 * mm,
        font,
        size
    )

    c.setFont(
        font,
        actual_size
    )

    text_width = c.stringWidth(
        text,
        font,
        actual_size
    )

    c.drawString(
        x + (width - text_width) / 2,
        y,
        text
    )


def draw_left(
    c,
    text,
    x,
    y,
    width,
    font="Helvetica",
    size=10
):

    text = str(text or "")

    actual_size = fit_font(
        c,
        text,
        width - 5 * mm,
        font,
        size
    )

    c.setFont(
        font,
        actual_size
    )

    c.drawString(
        x + 2 * mm,
        y,
        text
    )


def draw_right(
    c,
    text,
    x,
    y,
    width,
    font="Helvetica",
    size=10
):

    text = str(text or "")

    actual_size = fit_font(
        c,
        text,
        width - 5 * mm,
        font,
        size
    )

    c.setFont(
        font,
        actual_size
    )

    text_width = c.stringWidth(
        text,
        font,
        actual_size
    )

    c.drawString(
        x + width - text_width - 2 * mm,
        y,
        text
    )


# =========================================================
# PDF GENERATOR
# =========================================================

def generate_bill_pdf(data, output_dir):

    validate(data)

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    invoice_no = clean_filename(
        data.get("invoice_no")
    )

    output_path = (
        output_dir /
        f"{invoice_no}.pdf"
    )

    # =====================================================
    # CREATE A4 PDF
    # =====================================================

    c = canvas.Canvas(
        str(output_path),
        pagesize=A4
    )

    c.setTitle(
        f"Amaan Tour and Travels - {invoice_no}"
    )

    c.setAuthor(
        FIXED["company_name"]
    )

    # =====================================================
    # OUTER BORDER
    # =====================================================

    outer_x = 12 * mm
    outer_y = 15 * mm

    outer_w = PAGE_W - 24 * mm
    outer_h = PAGE_H - 30 * mm

    c.setLineWidth(1.0)

    c.rect(
        outer_x,
        outer_y,
        outer_w,
        outer_h
    )

    # =====================================================
    # INNER BILL BOX
    # =====================================================

    inner_x = 25 * mm
    inner_y = 42 * mm

    inner_w = PAGE_W - 50 * mm
    inner_h = 190 * mm

    c.setLineWidth(0.9)

    c.rect(
        inner_x,
        inner_y,
        inner_w,
        inner_h
    )

    # =====================================================
    # CAR NUMBER
    # =====================================================

    items = data.get("items") or []

    first_item = items[0] if items else {}

    car_no = (
        data.get("car_no")
        or first_item.get("vehicle_no")
        or ""
    )

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        inner_x + 5 * mm,
        inner_y + inner_h - 11 * mm,
        f"Car no-[{car_no}]"
    )

    # =====================================================
    # TABLE POSITION
    # =====================================================

    table_x = inner_x

    table_top = (
        inner_y +
        inner_h -
        18 * mm
    )

    # =====================================================
    # COLUMN WIDTHS
    # =====================================================

    date_w = 34 * mm
    service_w = 28 * mm
    description_w = 70 * mm

    amount_w = (
        inner_w -
        date_w -
        service_w -
        description_w
    )

    x1 = table_x
    x2 = x1 + date_w
    x3 = x2 + service_w
    x4 = x3 + description_w
    x5 = x4 + amount_w

    # =====================================================
    # HEADER
    # =====================================================

    header_h = 13 * mm

    header_bottom = (
        table_top -
        header_h
    )

    c.setLineWidth(0.8)

    # Header outer box
    c.rect(
        table_x,
        header_bottom,
        inner_w,
        header_h
    )

    # Vertical lines
    c.line(
        x2,
        table_top,
        x2,
        header_bottom
    )

    c.line(
        x3,
        table_top,
        x3,
        header_bottom
    )

    c.line(
        x4,
        table_top,
        x4,
        header_bottom
    )

    # Header text
    header_y = (
        header_bottom +
        4.2 * mm
    )

    draw_center(
        c,
        "Date of journey",
        x1,
        header_y,
        date_w,
        "Helvetica-Bold",
        9
    )

    draw_center(
        c,
        "Service",
        x2,
        header_y,
        service_w,
        "Helvetica-Bold",
        9
    )

    draw_center(
        c,
        "Description",
        x3,
        header_y,
        description_w,
        "Helvetica-Bold",
        9
    )

    draw_center(
        c,
        "Amount",
        x4,
        header_y,
        amount_w,
        "Helvetica-Bold",
        9
    )

    # =====================================================
    # JOURNEY ROWS
    # =====================================================

    row_h = 13 * mm

    current_y = header_bottom

    total = 0

    # Maximum rows that fit in the reference bill area.
    # Extra rows are kept from overflowing the invoice box.
    max_rows = 8

    for index, item in enumerate(items[:max_rows]):

        row_bottom = (
            current_y -
            row_h
        )

        # Horizontal row box
        c.rect(
            table_x,
            row_bottom,
            inner_w,
            row_h
        )

        # Vertical lines
        c.line(
            x2,
            current_y,
            x2,
            row_bottom
        )

        c.line(
            x3,
            current_y,
            x3,
            row_bottom
        )

        c.line(
            x4,
            current_y,
            x4,
            row_bottom
        )

        # -------------------------------------------------
        # DATE
        # -------------------------------------------------

        date_value = (
            item.get("date")
            or item.get("journey_date")
            or ""
        )

        # If HTML date input was used
        date_value = format_date(
            date_value
        )

        # -------------------------------------------------
        # SERVICE
        # -------------------------------------------------

        service_value = (
            item.get("service")
            or "Official"
        )

        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        description = (
            item.get("description")
            or item.get("route")
            or ""
        )

        # -------------------------------------------------
        # AMOUNT
        # -------------------------------------------------

        amount = item.get(
            "amount",
            0
        )

        try:
            total += float(amount or 0)
        except (TypeError, ValueError):
            pass

        amount_text = money(
            amount
        )

        text_y = (
            row_bottom +
            4.2 * mm
        )

        draw_center(
            c,
            date_value,
            x1,
            text_y,
            date_w,
            "Helvetica",
            9
        )

        draw_center(
            c,
            service_value,
            x2,
            text_y,
            service_w,
            "Helvetica",
            9
        )

        draw_left(
            c,
            description,
            x3,
            text_y,
            description_w,
            "Helvetica",
            9
        )

        draw_right(
            c,
            amount_text,
            x4,
            text_y,
            amount_w,
            "Helvetica",
            9
        )

        current_y = row_bottom

    # =====================================================
    # TOTAL
    # =====================================================

    # If frontend already calculated/sent total,
    # use it. Otherwise use journey sum.
    supplied_total = data.get("total")

    if supplied_total not in (
        None,
        "",
        0,
        "0"
    ):
        try:
            total = float(
                supplied_total
            )
        except (TypeError, ValueError):
            pass

    total_w = 72 * mm
    total_h = 13 * mm

    total_x = (
        inner_x +
        inner_w -
        total_w -
        4 * mm
    )

    total_y = (
        inner_y +
        47 * mm
    )

    c.setLineWidth(0.9)

    c.rect(
        total_x,
        total_y,
        total_w,
        total_h
    )

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        total_x + 3 * mm,
        total_y + 4.7 * mm,
        "Total Amount :-"
    )

    total_text = (
        f"RS {money(total)}"
    )

    draw_right(
        c,
        total_text,
        total_x + 35 * mm,
        total_y + 4.7 * mm,
        total_w - 37 * mm,
        "Helvetica-Bold",
        10
    )

    # =====================================================
    # QR CODE
    # =====================================================

    qr_x = (
        inner_x +
        6 * mm
    )

    qr_y = (
        inner_y +
        8 * mm
    )

    qr_size = 31 * mm

    if QR_PATH.exists():

        try:

            c.drawImage(
                ImageReader(
                    str(QR_PATH)
                ),
                qr_x,
                qr_y,
                width=qr_size,
                height=qr_size,
                preserveAspectRatio=True,
                mask="auto"
            )

        except Exception:
            pass

    # =====================================================
    # BANK DETAILS
    # =====================================================

    bank_x = (
        inner_x +
        42 * mm
    )

    bank_y = (
        inner_y +
        36 * mm
    )

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawString(
        bank_x,
        bank_y,
        f"BANK NAME:- {FIXED['bank_name']}"
    )

    c.drawString(
        bank_x,
        bank_y - 6 * mm,
        f"BANK A/C :- {FIXED['bank_account']}"
    )

    c.drawString(
        bank_x,
        bank_y - 12 * mm,
        f"BANK IFSC :- {FIXED['bank_ifsc']}"
    )

    c.drawString(
        bank_x,
        bank_y - 18 * mm,
        f"Name :- {FIXED['account_name']}"
    )

    # =====================================================
    # UPI ID
    # =====================================================

    if FIXED.get("upi_id"):

        c.setFont(
            "Helvetica",
            8
        )

        c.drawString(
            qr_x,
            qr_y - 4 * mm,
            f"UPI: {FIXED['upi_id']}"
        )

    # =====================================================
    # AUTHORIZED SIGNATURE
    # =====================================================

    signature_x = (
        inner_x +
        inner_w -
        58 * mm
    )

    signature_y = (
        inner_y +
        19 * mm
    )

    c.setFont(
        "Helvetica-Bold",
        9
    )

    c.drawCentredString(
        signature_x + 29 * mm,
        signature_y,
        FIXED["signature"]
    )

    # =====================================================
    # COMPANY NAME
    # =====================================================

    c.setFont(
        "Helvetica-Bold",
        11
    )

    c.drawCentredString(
        inner_x +
        inner_w / 2,
        inner_y + 6 * mm,
        FIXED["company_name"]
    )

    # =====================================================
    # FINISH
    # =====================================================

    c.showPage()

    c.save()

    return output_path
