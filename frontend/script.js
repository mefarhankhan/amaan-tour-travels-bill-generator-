const form = document.getElementById("billForm");
const rowsContainer = document.getElementById("rows");
const template = document.getElementById("rowTemplate");
const addRowBtn = document.getElementById("addRow");
const resetBtn = document.getElementById("resetBtn");
const previewBtn = document.getElementById("previewBtn");
const previewModal = document.getElementById("previewModal");
const pdfPreview = document.getElementById("pdfPreview");
const closePreviewBtn = document.getElementById("closePreview");
const totalEl = document.getElementById("grandTotal");
const statusEl = document.getElementById("status");

function today() {
  return new Date().toISOString().slice(0, 10);
}

function addRow(values = {}) {
  const fragment = template.content.cloneNode(true);
  const row = fragment.querySelector(".journey-row");

  row.querySelector(".item-date").value = values.date || document.querySelector("[name='issue_date']").value || today();
  row.querySelector(".item-route").value = values.route || "";
  row.querySelector(".item-service").value = values.service || "";
  row.querySelector(".item-vehicle").value = values.vehicle_no || "";
  row.querySelector(".item-km").value = values.km || "";
  row.querySelector(".item-rate").value = values.rate || "";
  row.querySelector(".item-amount").value = values.amount || "";

  row.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", calculateTotal);
  });

  row.querySelector(".remove-row").addEventListener("click", () => {
    row.remove();
    calculateTotal();
  });

  rowsContainer.appendChild(row);
  calculateTotal();
}

function calculateTotal() {
  let total = 0;
  document.querySelectorAll(".item-amount").forEach(input => {
    total += Number(input.value) || 0;
  });
  totalEl.textContent = `₹${total.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function collectData() {
  const fd = new FormData(form);
  const items = [];

  document.querySelectorAll(".journey-row").forEach(row => {
    items.push({
      date: row.querySelector(".item-date").value,
      route: row.querySelector(".item-route").value,
      service: row.querySelector(".item-service").value,
      vehicle_no: row.querySelector(".item-vehicle").value,
      km: row.querySelector(".item-km").value,
      rate: row.querySelector(".item-rate").value,
      amount: row.querySelector(".item-amount").value
    });
  });

  return {
    bill_type: fd.get("bill_type"),
    invoice_no: fd.get("invoice_no"),
    issue_date: fd.get("issue_date"),
    gstin: fd.get("gstin"),
    bill_to_name: fd.get("bill_to_name"),
    bill_to_address: fd.get("bill_to_address"),
    items
  };
}

function toggleGstinField() {
  const billType = document.getElementById("bill_type").value;
  const gstinField = document.getElementById("gstinField");
  const gstinInput = document.getElementById("gstin");

  const isGst = billType === "gst";
  gstinField.style.display = isGst ? "" : "none";
  gstinInput.required = isGst;

  if (!isGst) {
    gstinInput.value = "";
  }
}

document.getElementById("bill_type").addEventListener("change", toggleGstinField);
toggleGstinField();

function isMobileDevice() {
  const ua = navigator.userAgent || "";
  const touchMac = navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1; // iPadOS
  return /Android|iPhone|iPad|iPod|Mobile|Windows Phone/i.test(ua) || touchMac;
}

async function previewBill() {
  if (!form.reportValidity()) {
    return;
  }

  statusEl.textContent = "Creating exact PDF preview...";
  previewBtn.disabled = true;

  const mobile = isMobileDevice();

  // On mobile, open the tab right now (still inside this click handler)
  // so the browser doesn't treat it as a blocked popup once the fetch
  // below finishes asynchronously.
  let newTab = null;
  if (mobile) {
    newTab = window.open("", "_blank");
  }

  try {
    const response = await fetch("/api/preview-bill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectData())
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || "Unable to create PDF preview.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);

    if (mobile) {
      // Most mobile browsers (iOS Safari especially) can't render a PDF
      // inside an iframe, so hand it off to the device's own PDF viewer.
      if (newTab) {
        newTab.location.href = url;
      } else {
        window.location.href = url;
      }
      statusEl.textContent = "Preview opened in a new tab.";
    } else {
      if (pdfPreview.src) {
        URL.revokeObjectURL(pdfPreview.src);
      }

      pdfPreview.src = url;
      previewModal.style.display = "flex";
      previewModal.setAttribute("aria-hidden", "false");
      statusEl.textContent = "Preview ready. This is the actual PDF.";
    }
  } catch (error) {
    if (newTab) {
      newTab.close();
    }
    statusEl.textContent = error.message;
  } finally {
    previewBtn.disabled = false;
  }
}

function closePreview() {
  previewModal.style.display = "none";
  previewModal.setAttribute("aria-hidden", "true");

  if (pdfPreview.src) {
    URL.revokeObjectURL(pdfPreview.src);
    pdfPreview.removeAttribute("src");
  }
}

previewBtn.addEventListener("click", previewBill);
closePreviewBtn.addEventListener("click", closePreview);

previewModal.addEventListener("click", (event) => {
  if (event.target === previewModal) {
    closePreview();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && previewModal.style.display === "flex") {
    closePreview();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusEl.textContent = "Generating PDF...";

  try {
    const response = await fetch("/api/generate-bill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectData())
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error || "Unable to generate bill.");
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${collectData().invoice_no || "bill"}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    statusEl.textContent = "Bill generated successfully.";
  } catch (error) {
    statusEl.textContent = error.message;
  }
});

addRowBtn.addEventListener("click", () => addRow());

resetBtn.addEventListener("click", () => {
  form.reset();
  document.querySelector("[name='issue_date']").value = today();
  rowsContainer.innerHTML = "";
  addRow();
  statusEl.textContent = "";
  calculateTotal();
});

document.querySelector("[name='issue_date']").value = today();
addRow({
  date: today()
});
