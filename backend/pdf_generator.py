from pathlib import Path
from datetime import datetime
import re

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm


BASE_DIR = Path(__file__).resolve().parent.parent

FIXED = {
    "company_name": "AMAAN TOUR AND TRAVELS",
    "bank_name": "STATE BANK OF INDIA",
    "bank_account": "30938200536",
    "bank_ifsc": "SBIN0000060",
    "account_name": "Abdul Talib khan",
    "upi_id": "talibamankhan@oksbi",
    "signature_title": "AUTHORIZED SIGNATURE",
}

QR_PATH = BASE_DIR / "assets" / "upi-qr.png"


def money(value):
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0

    if amount.is_integer():
        return f"{int(amount)}/-"

    return f"{amount:,.2f}/-"


def clean_filename(value):
    value = str(value or "bill").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return value[:80] or "bill"


def format_date(value):
    if not value:
        return ""

    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(value)


def validate(data):
    if not str(data.get("bill_to_name", "")).strip():
        raise ValueError("Please fill: Bill-to name")

    if not data.get("items"):
        raise ValueError("Add at least one journey/service row.")


def draw_fitted(c, text, x, y, max_width, font="Helvetica", size=10,
                align="left", min_size=7):
    """Draw text without allowing it to overflow its allotted width."""
    text = str(text or "")
    current = size

    while current > min_size and c.stringWidth(text, font, current) > max_width:
        current -= 0.25

    c.setFont(font, current)
    width = c.stringWidth(text, font, current)

    if align == "center":
        c.drawString(x + (max_width - width) / 2, y, text)
    elif align == "right":
        c.drawString(x + max_width - width, y, text)
    else:
        c.drawString(x, y, text)


def generate_bill_pdf(data, output_dir):
    """
    Generates ONE A4 portrait page.

    The PDF intentionally reproduces only the second-page bill design
    from the supplied reference. The old running-report page is not used.
    """

    validate(data)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{clean_filename(data.get('invoice_no'))}.pdf"

    page_w, page_h = A4
    c = canvas.Canvas(str(output_path), pagesize=A4)

    # =========================================================
    # REFERENCE PAGE 2 GEOMETRY
    # =========================================================

    # Outer border: approximately 8.5 mm from left/right/top,
    # with the same large blank area below as the reference.
    outer_x = 8.5 * mm
    outer_y = 99.5 * mm
    outer_w = 195.0 * mm
    outer_h = page_h - outer_y - 8.5 * mm

    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.7)
    c.rect(outer_x, outer_y, outer_w, outer_h)

    # Main bill box from the reference.
    inner_x = 15 * mm
    inner_y = 209 * mm
    inner_w = 183.7 * mm
    inner_h = 61 * mm
    inner_top = inner_y + inner_h

    c.setLineWidth(0.7)
    c.rect(inner_x, inner_y, inner_w, inner_h)

    # =========================================================
    # CAR NUMBER
    # =========================================================

    items = data.get("items") or []

    car_no = str(data.get("car_no", "")).strip()

    if not car_no and items:
        car_no = str(items[0].get("vehicle_no", "")).strip()

    c.setFont("Helvetica", 14)
    c.drawString(
        inner_x + 3 * mm,
        inner_top - 12 * mm,
        f"Car no-[{car_no}]"
    )

    # Horizontal separator below car number.
    separator_y = inner_top - 16 * mm
    c.setLineWidth(0.6)
    c.line(inner_x, separator_y, inner_x + inner_w, separator_y)

    # =========================================================
    # FOUR-COLUMN BILL CONTENT
    # =========================================================

    # These are intentionally text columns rather than a heavy grid,
    # matching the supplied reference page.
    date_x = inner_x + 3 * mm
    service_x = inner_x + 48 * mm
    description_x = inner_x + 85 * mm
    amount_x = inner_x + 153 * mm

    date_w = 48 * mm
    service_w = 43 * mm
    description_w = 43 * mm
    amount_w = inner_w - 156 * mm

    header_y = separator_y - 3 * mm
    value_start_y = separator_y - 10 * mm

    c.setFont("Helvetica-Bold", 11.5)

    draw_fitted(
        c, "Date of journey",
        date_x, header_y, date_w,
        "Helvetica-Bold", 11.5, "left", 8
    )

    draw_fitted(
        c, "Service",
        service_x, header_y, service_w,
        "Helvetica-Bold", 11.5, "left", 8
    )

    draw_fitted(
        c, "Description",
        description_x, header_y, description_w,
        "Helvetica-Bold", 11.5, "center", 8
    )

    draw_fitted(
        c, "Amount",
        amount_x, header_y, amount_w,
        "Helvetica-Bold", 11.5, "right", 8
    )

    # ---------------------------------------------------------
    # JOURNEY ROWS
    # ---------------------------------------------------------
    #
    # Page 2 has only four visible columns. Existing Journey rows
    # are therefore mapped as:
    #
    # date -> Date of journey
    # service -> Service
    # route -> Description
    # amount -> Amount
    #
    # Vehicle number is used for the main Car no. above.
    # KM and Rate remain input fields but are not printed because
    # they are not part of the reference Page 2 design.
    # ---------------------------------------------------------

    if not items:
        items = [{}]

    total = 0.0

    # The reference has one row. Additional Journey rows are placed
    # underneath it while staying inside the same bill rectangle.
    row_y = value_start_y
    row_gap = 7.5 * mm

    max_rows = 5

    for index, item in enumerate(items[:max_rows]):
        try:
            amount_value = float(item.get("amount") or 0)
        except (TypeError, ValueError):
            amount_value = 0

        total += amount_value

        date_text = format_date(item.get("date", ""))
        service_text = item.get("service", "")
        description_text = item.get("route", "")

        # If the route is empty, use a useful description if supplied.
        if not str(description_text).strip():
            description_text = item.get("description", "")

        amount_text = money(amount_value)

        draw_fitted(
            c, date_text,
            date_x, row_y, date_w,
            "Helvetica-Bold", 11.5, "left", 7
        )

        draw_fitted(
            c, service_text,
            service_x, row_y, service_w,
            "Helvetica-Bold", 11.5, "left", 7
        )

        draw_fitted(
            c, description_text,
            description_x, row_y, description_w,
            "Helvetica-Bold", 11.5, "center", 7
        )

        draw_fitted(
            c, amount_text,
            amount_x, row_y, amount_w,
            "Helvetica-Bold", 11.5, "right", 7
        )

        row_y -= row_gap

    # =========================================================
    # TOTAL BOX
    # =========================================================

    # The reference total box touches the bottom-right corner
    # of the inner bill rectangle.
    total_w = 65.5 * mm
    total_h = 8.3 * mm
    total_x = inner_x + inner_w - total_w
    total_y = inner_y

    c.setLineWidth(0.6)
    c.rect(total_x, total_y, total_w, total_h)

    draw_fitted(
        c,
        "Total Amount :-",
        total_x + 2.5 * mm,
        total_y + 2.6 * mm,
        37 * mm,
        "Helvetica-Bold",
        9.5,
        "left",
        7
    )

    draw_fitted(
        c,
        f"RS {money(total)}",
        total_x + 38 * mm,
        total_y + 2.6 * mm,
        total_w - 40 * mm,
        "Helvetica-Bold",
        10,
        "right",
        7
    )

    # =========================================================
    # QR CODE
    # =========================================================

    qr_x = 25 * mm
    qr_y = 155 * mm
    qr_size = 51 * mm

    if QR_PATH.exists():
        c.drawImage(
            str(QR_PATH),
            qr_x,
            qr_y,
            width=qr_size,
            height=qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )

    # =========================================================
    # BANK DETAILS
    # =========================================================

    bank_x = 25 * mm
    bank_y = 146.5 * mm

    c.setFont("Helvetica", 10.2)

    c.drawString(
        bank_x,
        bank_y,
        f"BANK NAME:-   {FIXED['bank_name']}"
    )

    c.drawString(
        bank_x,
        bank_y - 6 * mm,
        f"BANK A/C   :-   {FIXED['bank_account']}"
    )

    c.drawString(
        bank_x,
        bank_y - 12 * mm,
        f"BANK IFSC  :-   {FIXED['bank_ifsc']}"
    )

    c.drawString(
        bank_x,
        bank_y - 18 * mm,
        f"Name       :-   {FIXED['account_name']}"
    )

    # =========================================================
    # SIGNATURE
    # =========================================================

    signature_x = 135 * mm
    signature_y = 117.5 * mm

    c.setFont("Helvetica-BoldOblique", 10.5)

    c.drawCentredString(
        signature_x + 28 * mm,
        signature_y,
        FIXED["signature_title"]
    )

    c.line(
        signature_x + 8 * mm,
        signature_y - 0.8 * mm,
        signature_x + 48 * mm,
        signature_y - 0.8 * mm
    )

    c.drawCentredString(
        signature_x + 28 * mm,
        signature_y - 6 * mm,
        "AMAAN TOUR AND"
    )

    # The supplied reference visually places "TRAVELS" at the
    # lower-left of the outer bordered area.
    c.drawString(
        25 * mm,
        64.5 * mm,
        "TRAVELS"
    )

    # ONE PAGE ONLY.
    c.showPage()
    c.save()

    return output_path
