# Amaan Tour and Travels - Bill Generator

Personal bill generator for Amaan Tour and Travels.

## Features

- GST Bill / Non-GST Bill
- GSTIN appears only on GST bills
- Same bill layout for both types
- Multiple journey/service rows
- Automatic grand-total calculation from Amount fields
- Fixed company information
- Fixed bank information
- Fixed authorized-signature section
- Permanent UPI QR image from `assets/upi-qr.png`
- One-page PDF output
- Flask + ReportLab backend
- Railway-ready

## Project structure

```text
bill-generator/
├── backend/
│   ├── app.py
│   ├── pdf_generator.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── assets/
│   └── upi-qr.png
├── .gitignore
├── Procfile
└── README.md
```

## Run locally

From the project root:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Start:

```bash
python backend/app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Railway deployment

1. Create a **private GitHub repository**.
2. Upload this project.
3. In Railway, create a new project from the GitHub repository.
4. Railway will use the `Procfile`.
5. Generate a public domain for the service.
6. Open the Railway URL and create bills.

No database is required for the first version.

## Fixed bill information

The fixed values are in:

```text
backend/pdf_generator.py
```

The current QR image is:

```text
assets/upi-qr.png
```

Replace that PNG with the final QR image you want to use. Keep the same filename.

## Important

The sample bill contains a visual total that does not match its displayed line amount. This application calculates the Grand Total from the Amount values entered in the form, so future bills will have a mathematically consistent total.
