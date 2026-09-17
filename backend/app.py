from pathlib import Path
import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pdf_generator import generate_bill_pdf

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=None)
CORS(app)

@app.get("/")
def home():
    return (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

@app.get("/<path:path>")
def frontend_files(path):
    file_path = FRONTEND_DIR / path
    if file_path.is_file():
        return send_file(file_path)
    return jsonify({"error": "Not found"}), 404


@app.post("/api/preview-bill")
def preview_bill():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    try:
        pdf_path = generate_bill_pdf(data, GENERATED_DIR)
        response = send_file(
            pdf_path,
            as_attachment=False,
            download_name=pdf_path.name,
            mimetype="application/pdf",
        )
        response.headers["Content-Disposition"] = (
            f'inline; filename="{pdf_path.name}"'
        )
        return response
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Bill preview failed")
        return jsonify({"error": f"Bill preview failed: {exc}"}), 500

@app.post("/api/generate-bill")
def generate_bill():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    try:
        pdf_path = generate_bill_pdf(data, GENERATED_DIR)
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_path.name,
            mimetype="application/pdf",
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        app.logger.exception("Bill generation failed")

        @app.post("/api/preview-bill")
def preview_bill():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid or missing JSON data"
        }), 400

    try:
        pdf_path = generate_bill_pdf(
            data,
            GENERATED_DIR
        )

        return send_file(
            pdf_path,
            as_attachment=False,
            download_name=pdf_path.name,
            mimetype="application/pdf",
        )

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400

    except Exception as exc:
        app.logger.exception(
            "Bill preview failed"
        )

        return jsonify({
            "error": f"Bill preview failed: {exc}"
        }), 500
        return jsonify({"error": f"Bill generation failed: {exc}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
