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

    "address_line1": "Pali road,Dehri-on-Sone",
    "address_line2": "Rohtas, Bihar, 821307",
    "email": "Talibamankhan@gmail.com",
    "phone": "9931421738,7761948730",

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


def draw_right_at(c, text, right_x, y, font="Helvetica", size=10):
    """Draw text right-aligned so it ends exactly at right_x."""

    text = str(text or "")
    c.setFont(font, size)
    text_width = c.stringWidth(text, font, size)
    c.drawString(right_x - text_width, y, text)


# =========================================================
# PDF GENERATOR
# =========================================================

def generate_bill_pdf(data, output_dir):

    validate(data)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    invoice_no = clean_filename(data.get("invoice_no"))
    output_path = output_dir / f"{invoice_no}.pdf"

    items = data.get("items") or []
    first_item = items[0] if items else {}

    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle(f"Amaan Tour and Travels - {invoice_no}")
    c.setAuthor(FIXED["company_name"])

    # =====================================================
    # OUTER BORDER (whole bill lives inside this single box)
    # =====================================================

    box_x = 12 * mm
    box_y = 15 * mm
    box_w = PAGE_W - 24 * mm
    box_h = PAGE_H - 30 * mm

    c.setLineWidth(1.1)
    c.rect(box_x, box_y, box_w, box_h)

    left_x = box_x + 5 * mm
    right_x = box_x + box_w - 5 * mm

    # =====================================================
    # TITLE
    # =====================================================

    cursor_y = box_y + box_h - 16 * mm

    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(box_x + box_w / 2, cursor_y, FIXED["company_name"])

    # =====================================================
    # COMPANY ADDRESS BLOCK (right aligned, under the title)
    # =====================================================

    cursor_y -= 10 * mm

    address_lines = [
        FIXED["address_line1"],
        FIXED["address_line2"],
        f"E-mail:-{FIXED['email']}",
        f"Contact no:- {FIXED['phone']}",
    ]

    for line in address_lines:
        draw_right_at(c, line, right_x, cursor_y, "Helvetica", 10)
        cursor_y -= 5 * mm

    # Separator under the header block
    cursor_y -= 3 * mm
    c.setLineWidth(0.8)
    c.line(box_x, cursor_y, box_x + box_w, cursor_y)

    # =====================================================
    # INVOICE INFO (left)  /  BILL TO (right)
    # =====================================================

    cursor_y -= 8 * mm

    invoice_no_display = data.get("invoice_no") or ""
    issue_date_display = format_date(data.get("issue_date"))

    bill_to_name = data.get("bill_to_name") or ""
    bill_to_address = data.get("bill_to_address") or ""
    address_parts = [ln.strip() for ln in str(bill_to_address).splitlines() if ln.strip()]

    c.setFont("Helvetica", 10)
    c.drawString(left_x, cursor_y, f"Invoice no:-{invoice_no_display}")
    draw_right_at(c, "Bill to", right_x, cursor_y, "Helvetica", 10)

    cursor_y -= 6 * mm
    c.drawString(left_x, cursor_y, f"Issue date:- {issue_date_display}")
    draw_right_at(c, bill_to_name, right_x, cursor_y, "Helvetica", 10)

    for part in address_parts:
        cursor_y -= 5.5 * mm
        draw_right_at(c, part, right_x, cursor_y, "Helvetica", 10)

    # Space to match the reference layout, then a route line
    cursor_y -= 26 * mm
    c.setLineWidth(0.8)
    c.line(box_x, cursor_y + 5 * mm, box_x + box_w, cursor_y + 5 * mm)

    route = first_item.get("route") or first_item.get("description") or ""
    c.setFont("Helvetica", 11)
    c.drawString(left_x, cursor_y, f"From-{route}")

    cursor_y -= 3 * mm
    c.setLineWidth(0.8)
    c.line(box_x, cursor_y, box_x + box_w, cursor_y)

    # =====================================================
    # TABLE
    # =====================================================

    table_x = box_x
    table_top = cursor_y
    inner_w = box_w

    date_w = 32 * mm
    service_w = 34 * mm
    km_w = 32 * mm
    rate_w = 34 * mm
    amount_w = inner_w - date_w - service_w - km_w - rate_w

    x1 = table_x
    x2 = x1 + date_w
    x3 = x2 + service_w
    x4 = x3 + km_w
    x5 = x4 + rate_w

    header_h = 12 * mm
    header_bottom = table_top - header_h

    c.setLineWidth(0.8)
    c.rect(table_x, header_bottom, inner_w, header_h)

    for x in (x2, x3, x4, x5):
        c.line(x, table_top, x, header_bottom)

    header_y = header_bottom + 4.2 * mm

    draw_center(c, "Date of journey", x1, header_y, date_w, "Helvetica-Bold", 9)
    draw_center(c, "Service", x2, header_y, service_w, "Helvetica-Bold", 9)
    draw_center(c, "KMs Run", x3, header_y, km_w, "Helvetica-Bold", 9)
    draw_center(c, "Rate", x4, header_y, rate_w, "Helvetica-Bold", 9)
    draw_center(c, "Amount", x5, header_y, amount_w, "Helvetica-Bold", 9)

    row_h = 16 * mm
    current_y = header_bottom
    total = 0
    max_rows = 6

    for item in items[:max_rows]:

        row_bottom = current_y - row_h

        c.rect(table_x, row_bottom, inner_w, row_h)
        for x in (x2, x3, x4, x5):
            c.line(x, current_y, x, row_bottom)

        date_value = format_date(item.get("date") or item.get("journey_date") or "")
        service_value = item.get("service") or "Official"
        vehicle_no = item.get("vehicle_no") or ""
        km_value = item.get("km") or ""
        rate_value = item.get("rate")
        amount = item.get("amount", 0)

        try:
            total += float(amount or 0)
        except (TypeError, ValueError):
            pass

        rate_text = money(rate_value) if rate_value not in (None, "", 0, "0") else ""
        amount_text = money(amount)

        mid_y = row_bottom + row_h / 2

        draw_center(c, date_value, x1, mid_y - 1.5 * mm, date_w, "Helvetica", 9)

        # Service name, with vehicle number in brackets below it
        draw_center(c, service_value, x2, mid_y + 2.5 * mm, service_w, "Helvetica", 9)
        if vehicle_no:
            draw_center(c, f"[{vehicle_no}]", x2, mid_y - 4 * mm, service_w, "Helvetica", 8)

        draw_center(c, km_value, x3, mid_y - 1.5 * mm, km_w, "Helvetica", 9)
        draw_right(c, rate_text, x4, mid_y - 1.5 * mm, rate_w, "Helvetica", 9)
        draw_right(c, amount_text, x5, mid_y - 1.5 * mm, amount_w, "Helvetica", 9)

        current_y = row_bottom

    table_bottom = current_y

    # =====================================================
    # GRAND TOTAL
    # =====================================================

    supplied_total = data.get("total")
    if supplied_total not in (None, "", 0, "0"):
        try:
            total = float(supplied_total)
        except (TypeError, ValueError):
            pass

    total_w = 74 * mm
    total_h = 12 * mm
    total_x = box_x + box_w - total_w
    total_y = table_bottom - 6 * mm - total_h

    c.setLineWidth(0.9)
    c.rect(total_x, total_y, total_w, total_h)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(total_x + 3 * mm, total_y + 4.4 * mm, "GRAND TOTAL :-")

    total_text = f"RS {money(total)}"
    draw_right(c, total_text, total_x + 30 * mm, total_y + 4.4 * mm, total_w - 30 * mm, "Helvetica-Bold", 11)

    # =====================================================
    # QR CODE + UPI ID
    # =====================================================

    qr_x = box_x + 6 * mm
    qr_size = 30 * mm
    qr_y = total_y - 14 * mm - qr_size

    if QR_PATH.exists():
        try:
            c.drawImage(
                ImageReader(str(QR_PATH)),
                qr_x,
                qr_y,
                width=qr_size,
                height=qr_size,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            pass

    if FIXED.get("upi_id"):
        c.setFont("Helvetica", 8)
        c.drawCentredString(qr_x + qr_size / 2, qr_y - 5 * mm, f"UPI ID: {FIXED['upi_id']}")

    # =====================================================
    # BANK DETAILS (below the QR code)
    # =====================================================

    bank_x = qr_x
    bank_y = qr_y - 13 * mm

    c.setFont("Helvetica", 9)
    c.drawString(bank_x, bank_y, f"BANK NAME:- {FIXED['bank_name']}")
    c.drawString(bank_x, bank_y - 5 * mm, f"BANK A/C :- {FIXED['bank_account']}")
    c.drawString(bank_x, bank_y - 10 * mm, f"BANK IFSC :- {FIXED['bank_ifsc']}")
    c.drawString(bank_x, bank_y - 15 * mm, f"Name :- {FIXED['account_name']}")

    # =====================================================
    # AUTHORIZED SIGNATURE (bottom right)
    # =====================================================

    sig_right_x = box_x + box_w - 6 * mm
    sig_y = box_y + 12 * mm

    c.setFont("Helvetica-Oblique", 9)
    text = FIXED["signature"]
    w = c.stringWidth(text, "Helvetica-Oblique", 9)
    c.drawString(sig_right_x - w, sig_y, text)
    c.line(sig_right_x - w, sig_y - 1, sig_right_x, sig_y - 1)

    sig_y -= 4.5 * mm
    text2 = FIXED["company_name"]
    w2 = c.stringWidth(text2, "Helvetica-Oblique", 9)
    c.drawString(sig_right_x - w2, sig_y, text2)
    c.line(sig_right_x - w2, sig_y - 1, sig_right_x, sig_y - 1)

    # =====================================================
    # FINISH
    # =====================================================

    c.showPage()
    c.save()

    return output_path
