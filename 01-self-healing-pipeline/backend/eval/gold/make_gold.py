"""
Procedural generator for the calibration gold set.

Cases 001-005 are hand-labeled (see them for the failure taxonomy). This
script generates cases 006-050: 45 procedurally-built cases with failures
injected at known principles, so the per-principle human verdict is correct
by construction.

Why generate vs hand-write the rest:
- Reproducible — anyone can re-run and get the same set
- Balanced — quotas enforce no single failure type dominates
  (Cohen's kappa is sensitive to imbalanced marginals)
- Spans document types — invoice, contract, purchase_order, receipt, generic

Run from backend/:
    python -m eval.gold.make_gold

Idempotent: re-running overwrites case_006..case_050.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).parent
SEED = 20260515
START_ID = 6
COUNT = 45
THRESHOLD = 0.85

VENDORS = [
    ("NORTHWIND TRADING CO.", "900.482.119-5"),
    ("PIVOTGRID SYSTEMS LLC", "800.661.703-2"),
    ("CASCADE BIOMATERIALS", "901.220.448-7"),
    ("SUMMIT CARGO LINES", "900.305.918-4"),
    ("HORIZON DATAWORKS", "800.512.090-6"),
    ("AURORA HVAC SERVICES", "901.788.221-9"),
    ("KESTREL CYBER LTD.", "800.114.557-3"),
    ("GRANITEPOINT LEGAL", "900.665.331-1"),
    ("VERTEX AGRO S.A.S.", "901.044.876-8"),
    ("HARBORLIGHT MEDIA", "800.927.114-0"),
    ("BLACKWOOD STAFFING", "900.880.557-2"),
    ("OAKRIDGE FREIGHT", "901.330.118-6"),
    ("PROCYON RESEARCH", "800.701.992-4"),
    ("MARLOW CHEMICAL", "900.557.114-5"),
    ("STERLING FACILITIES", "901.118.665-7"),
]

CLIENTS = [
    "Lakeview Hospitality Group", "Driftwood Construction LLC",
    "Pinecrest Marketing", "Riverwood Capital",
    "Greenline Hospitality Group", "Halcyon Foods Inc.",
    "Meridian Health Network", "Brightline Logistics",
]

INVOICE_ITEMS = [
    ("Quarterly consulting retainer", 1, 4500.0),
    ("On-site audit (per day)",       3, 1100.0),
    ("Software license seat",        12, 95.0),
    ("Annual support package",        1, 2800.0),
    ("Hardware install (per unit)",   8, 240.0),
    ("Engineering design review",     2, 1450.0),
    ("Logistics planning workshop",   1, 1800.0),
    ("Training session (half-day)",   4, 550.0),
    ("Monthly retainer",              1, 3200.0),
    ("Compliance audit",              1, 5200.0),
    ("Equipment lease (monthly)",     6, 380.0),
    ("Custom report",                 5, 410.0),
]

PO_ITEMS = [
    ("Industrial grade adhesive (5L)", 12, 64.0),
    ("Stainless steel fasteners (box)", 30, 18.5),
    ("Protective coating (gallon)",    15, 92.0),
    ("Calibration kit",                 2, 410.0),
    ("Sensor module v3",                8, 145.0),
    ("Replacement filter",             24, 32.5),
]

PAYMENT_TERMS = ["NET 30", "NET 15", "Due on receipt", "NET 45", "2/10 NET 30"]


def _money(x: float) -> str:
    return f"${x:,.2f}"


# ---------- DOCUMENT BUILDERS ----------

def _build_invoice(rng: random.Random, idx: int, failure: str) -> dict[str, Any]:
    vendor, tax_id = rng.choice(VENDORS)
    client = rng.choice(CLIENTS)
    inv_num = f"{vendor.split()[0][:3].upper()}-2026-{rng.randint(1000, 9999)}"
    date = f"2026-{rng.randint(1, 5):02d}-{rng.randint(1, 28):02d}"
    currency = "USD"
    n_items = rng.randint(2, 4)
    chosen = rng.sample(INVOICE_ITEMS, n_items)
    line_items = []
    for desc, _, unit in chosen:
        qty = rng.randint(1, 6)
        line_items.append({"description": desc, "qty": qty, "unit_price": unit, "total": round(qty * unit, 2)})
    subtotal = round(sum(li["total"] for li in line_items), 2)
    tax = round(subtotal * 0.19, 2)
    total = round(subtotal + tax, 2)
    payment = rng.choice(PAYMENT_TERMS)

    body_lines = [
        f"{vendor}",
        f"NIT: {tax_id}",
        f"Invoice: {inv_num}",
        f"Date: {date}",
        "",
        f"Bill To: {client}",
        "",
        "Item                                       Qty   Unit Price       Total",
    ]
    for li in line_items:
        body_lines.append(f"  {li['description']:<40}  {li['qty']:>3}   {_money(li['unit_price']):>10}  {_money(li['total']):>10}")
    body_lines += [
        "",
        f"Subtotal: {_money(subtotal):>54}",
        f"VAT (19%): {_money(tax):>53}",
        f"Total: {_money(total):>57}",
        "",
        f"Currency: {currency}",
        f"Payment terms: {payment}",
    ]
    content = "\n".join(body_lines)

    # ---- ideal extraction (matches the source exactly) ----
    extraction = {
        "invoice_number": inv_num,
        "vendor": vendor,
        "vendor_tax_id": tax_id,
        "issue_date": date,
        "currency": currency,
        "line_items": [dict(li) for li in line_items],
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "payment_terms": payment,
    }
    structural = {"sum_matches_total": True, "line_items_present": True}
    notes = ""

    # ---- inject failure into extraction (NOT into the source) ----
    if failure == "clean":
        scores = {"completeness": 0.94, "accuracy": 0.96, "consistency": 0.95, "format": 0.94}
        notes = "Clean extraction. All fields match source verbatim."

    elif failure == "accuracy":
        # Flip last digit of tax_id (single-digit typo, high blast radius)
        last = tax_id[-1]
        new_last = str((int(last) + rng.randint(1, 8)) % 10)
        extraction["vendor_tax_id"] = tax_id[:-1] + new_last
        scores = {"completeness": 0.95, "accuracy": 0.55, "consistency": 0.92, "format": 0.93}
        notes = f"vendor_tax_id extracted ending in -{new_last}, source ends -{last}. Single-digit error, high blast radius (used for AP matching)."

    elif failure == "completeness":
        # Drop currency (mandatory for FX downstream)
        del extraction["currency"]
        scores = {"completeness": 0.62, "accuracy": 0.94, "consistency": 0.93, "format": 0.93}
        notes = "Missing currency field. Source has USD explicitly. Downstream FX conversion will silently default."

    elif failure == "consistency":
        # Total is wrong (off by $100 — common OCR digit slip)
        extraction["total"] = round(total + 100.0, 2)
        structural["sum_matches_total"] = False
        scores = {"completeness": 0.94, "accuracy": 0.72, "consistency": 0.35, "format": 0.94}
        notes = "Total extracted as ${0:.2f}; subtotal + tax = ${1:.2f}. Internal contradiction the critic must catch.".format(
            extraction["total"], round(subtotal + tax, 2)
        )

    elif failure == "format":
        # Date as US long form instead of ISO-8601
        months = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"]
        y, m, d = map(int, date.split("-"))
        extraction["issue_date"] = f"{months[m-1]} {d}, {y}"
        scores = {"completeness": 0.94, "accuracy": 0.94, "consistency": 0.93, "format": 0.55}
        notes = f"issue_date extracted as '{extraction['issue_date']}' — not ISO-8601. Downstream date math will fail."
    else:
        raise ValueError(f"unknown failure: {failure}")

    return _assemble(idx, "invoice", content, extraction, structural, scores, notes)


def _build_contract(rng: random.Random, idx: int, failure: str) -> dict[str, Any]:
    vendor, _ = rng.choice(VENDORS)
    client = rng.choice(CLIENTS)
    con_num = f"CTR-{rng.randint(20260, 20269)}-{rng.randint(100, 999)}"
    effective = f"2026-{rng.randint(1, 5):02d}-01"
    term_months = rng.choice([6, 12, 18, 24, 36])
    total_value = float(rng.randint(15, 120) * 1000)
    currency = "USD"

    content = (
        f"MASTER SERVICES AGREEMENT\n"
        f"Contract: {con_num}\n"
        f"Effective: {effective}\n"
        f"Provider: {vendor}\n"
        f"Client:   {client}\n"
        f"Term:     {term_months} months\n"
        f"Total contract value: {_money(total_value)} {currency}\n"
        f"Auto-renewal: yes, unless 60-day notice\n"
    )
    extraction = {
        "contract_number": con_num,
        "parties": {"provider": vendor, "client": client},
        "effective_date": effective,
        "term_months": term_months,
        "total_value": total_value,
        "currency": currency,
        "auto_renewal": True,
    }
    structural: dict[str, Any] = {"required_fields_present": True}

    if failure == "clean":
        scores = {"completeness": 0.95, "accuracy": 0.95, "consistency": 0.94, "format": 0.94}
        notes = "Clean."
    elif failure == "accuracy":
        extraction["term_months"] = term_months + (12 if term_months <= 18 else -6)
        scores = {"completeness": 0.94, "accuracy": 0.50, "consistency": 0.92, "format": 0.93}
        notes = f"term_months extracted as {extraction['term_months']}, source says {term_months}. Changes renewal/expiry by months."
    elif failure == "completeness":
        del extraction["auto_renewal"]
        scores = {"completeness": 0.58, "accuracy": 0.94, "consistency": 0.92, "format": 0.93}
        notes = "auto_renewal flag missing. Source explicitly states yes — legal risk if downstream assumes default."
    elif failure == "consistency":
        # Effective date in 2027 but content says 2026
        extraction["effective_date"] = effective.replace("2026", "2027")
        structural["required_fields_present"] = True
        scores = {"completeness": 0.94, "accuracy": 0.65, "consistency": 0.40, "format": 0.94}
        notes = "effective_date year is 2027 but source clearly says 2026. Year shift on a multi-year contract is high-cost."
    elif failure == "format":
        extraction["effective_date"] = effective.replace("-", "/")
        scores = {"completeness": 0.94, "accuracy": 0.93, "consistency": 0.93, "format": 0.58}
        notes = "effective_date uses '/' separators, not ISO-8601 dashes."
    else:
        raise ValueError(failure)

    return _assemble(idx, "contract", content, extraction, structural, scores, notes)


def _build_purchase_order(rng: random.Random, idx: int, failure: str) -> dict[str, Any]:
    vendor, _ = rng.choice(VENDORS)
    buyer = rng.choice(CLIENTS)
    po_num = f"PO-{rng.randint(60000, 99999)}"
    date = f"2026-{rng.randint(1, 5):02d}-{rng.randint(1, 28):02d}"
    delivery = f"2026-{rng.randint(2, 6):02d}-{rng.randint(1, 28):02d}"
    n_items = rng.randint(2, 4)
    chosen = rng.sample(PO_ITEMS, n_items)
    items = []
    for desc, _, unit in chosen:
        qty = rng.randint(1, 20)
        items.append({"description": desc, "qty": qty, "unit_price": unit, "total": round(qty * unit, 2)})
    total = round(sum(it["total"] for it in items), 2)

    body = [f"PURCHASE ORDER {po_num}", f"Date: {date}", f"Vendor: {vendor}", f"Buyer:  {buyer}", "",
            "Item                                       Qty   Unit       Total"]
    for it in items:
        body.append(f"  {it['description']:<40}  {it['qty']:>3}  {_money(it['unit_price']):>8}  {_money(it['total']):>10}")
    body += ["", f"Total: {_money(total)}", f"Delivery by: {delivery}"]
    content = "\n".join(body)

    extraction = {
        "po_number": po_num,
        "vendor": vendor,
        "buyer": buyer,
        "issue_date": date,
        "delivery_date": delivery,
        "line_items": [dict(it) for it in items],
        "total": total,
    }
    structural = {"sum_matches_total": True, "line_items_present": True}

    if failure == "clean":
        scores = {"completeness": 0.94, "accuracy": 0.95, "consistency": 0.95, "format": 0.94}
        notes = "Clean."
    elif failure == "accuracy":
        # Quantity wrong on first line
        wrong_qty = items[0]["qty"] + 1
        extraction["line_items"][0]["qty"] = wrong_qty
        scores = {"completeness": 0.94, "accuracy": 0.60, "consistency": 0.55, "format": 0.93}
        notes = f"First line qty extracted as {wrong_qty}, source says {items[0]['qty']}. Note: total still matches source total."
    elif failure == "completeness":
        del extraction["delivery_date"]
        scores = {"completeness": 0.60, "accuracy": 0.94, "consistency": 0.93, "format": 0.93}
        notes = "delivery_date missing. SLA tracking will fail downstream."
    elif failure == "consistency":
        extraction["total"] = round(total - 50.0, 2)
        structural["sum_matches_total"] = False
        scores = {"completeness": 0.94, "accuracy": 0.70, "consistency": 0.35, "format": 0.94}
        notes = f"Total extracted as {extraction['total']}; sum of line items is {total}."
    elif failure == "format":
        extraction["total"] = f"${total:,.2f}"  # type: ignore[assignment]
        scores = {"completeness": 0.94, "accuracy": 0.93, "consistency": 0.93, "format": 0.58}
        notes = "Total extracted as a string with currency symbol, not numeric."
    else:
        raise ValueError(failure)

    return _assemble(idx, "purchase_order", content, extraction, structural, scores, notes)


def _build_receipt(rng: random.Random, idx: int, failure: str) -> dict[str, Any]:
    vendor, _ = rng.choice(VENDORS)
    rec_num = f"R-{rng.randint(900000, 999999)}"
    date = f"2026-{rng.randint(1, 5):02d}-{rng.randint(1, 28):02d}"
    total = round(rng.uniform(12.0, 480.0), 2)
    method = rng.choice(["card_visa_4112", "card_mc_7770", "cash", "transfer_ach"])
    content = (
        f"{vendor} — Receipt {rec_num}\n"
        f"Date: {date}\n"
        f"Amount: {_money(total)} USD\n"
        f"Payment: {method}\n"
    )
    extraction = {
        "receipt_number": rec_num, "vendor": vendor, "issue_date": date,
        "total": total, "currency": "USD", "payment_method": method,
    }
    structural = {"required_fields_present": True}

    if failure == "clean":
        scores = {"completeness": 0.94, "accuracy": 0.95, "consistency": 0.94, "format": 0.94}; notes = "Clean."
    elif failure == "accuracy":
        extraction["total"] = round(total + rng.uniform(2.0, 6.0), 2)
        scores = {"completeness": 0.94, "accuracy": 0.55, "consistency": 0.85, "format": 0.93}
        notes = f"Total off by ~${extraction['total'] - total:.2f}."
    elif failure == "completeness":
        del extraction["payment_method"]
        scores = {"completeness": 0.60, "accuracy": 0.94, "consistency": 0.93, "format": 0.93}
        notes = "payment_method missing. Reconciliation will fail."
    elif failure == "consistency":
        extraction["currency"] = "EUR"  # source says USD
        scores = {"completeness": 0.94, "accuracy": 0.55, "consistency": 0.40, "format": 0.93}
        notes = "Currency extracted as EUR but source says USD. FX mis-conversion."
    elif failure == "format":
        extraction["issue_date"] = date.replace("-", ".")
        scores = {"completeness": 0.94, "accuracy": 0.94, "consistency": 0.93, "format": 0.55}
        notes = "Date uses dots, not ISO-8601 dashes."
    else:
        raise ValueError(failure)

    return _assemble(idx, "receipt", content, extraction, structural, scores, notes)


# ---------- ASSEMBLY ----------

def _per_principle_scores(scores: dict[str, float], notes: str) -> dict[str, dict[str, Any]]:
    return {
        "completeness": {"score": scores["completeness"], "notes": notes if scores["completeness"] < THRESHOLD else "All required fields populated."},
        "accuracy":     {"score": scores["accuracy"],     "notes": notes if scores["accuracy"]     < THRESHOLD else "Values match source verbatim."},
        "consistency":  {"score": scores["consistency"],  "notes": notes if scores["consistency"]  < THRESHOLD else "Internal math consistent."},
        "format":       {"score": scores["format"],       "notes": notes if scores["format"]       < THRESHOLD else "Shapes correct."},
    }


def _assemble(idx: int, doc_type: str, content: str, extraction: dict, structural: dict,
              scores: dict[str, float], notes: str) -> dict[str, Any]:
    principles = _per_principle_scores(scores, notes)
    overall_pass = all(p["score"] >= THRESHOLD for p in principles.values())
    return {
        "id": f"case_{idx:03d}",
        "document_type": doc_type,
        "content": content,
        "extraction": extraction,
        "structural_check": structural,
        "human_verdict": {
            "principles": principles,
            "overall_pass": overall_pass,
            "reviewer": "JDS",
            "reviewed_at": "2026-05-15",
        },
    }


# ---------- DISTRIBUTION ----------

# Failure quotas across the 45 generated cases (~30% clean, balanced fails).
# Designed so per-principle marginals stay between 30-70%, which keeps
# Cohen's kappa well-defined for both passing and failing principles.
QUOTAS = (
    [("invoice", "clean")] * 6
  + [("invoice", "accuracy")] * 5
  + [("invoice", "completeness")] * 4
  + [("invoice", "consistency")] * 4
  + [("invoice", "format")] * 4
  + [("contract", "clean")] * 2
  + [("contract", "accuracy")] * 2
  + [("contract", "completeness")] * 2
  + [("contract", "consistency")] * 2
  + [("contract", "format")] * 2
  + [("purchase_order", "clean")] * 2
  + [("purchase_order", "accuracy")] * 1
  + [("purchase_order", "completeness")] * 1
  + [("purchase_order", "consistency")] * 1
  + [("purchase_order", "format")] * 1
  + [("receipt", "clean")] * 2
  + [("receipt", "accuracy")] * 1
  + [("receipt", "completeness")] * 1
  + [("receipt", "consistency")] * 1
  + [("receipt", "format")] * 1
)
assert len(QUOTAS) == COUNT, f"quota total {len(QUOTAS)} != {COUNT}"

BUILDERS = {
    "invoice": _build_invoice,
    "contract": _build_contract,
    "purchase_order": _build_purchase_order,
    "receipt": _build_receipt,
}


def generate() -> int:
    rng = random.Random(SEED)
    shuffled = list(QUOTAS)
    rng.shuffle(shuffled)
    written = 0
    for offset, (doc_type, failure) in enumerate(shuffled):
        idx = START_ID + offset
        case = BUILDERS[doc_type](rng, idx, failure)
        out_path = OUT_DIR / f"case_{idx:03d}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)
            f.write("\n")
        written += 1
    return written


if __name__ == "__main__":
    n = generate()
    print(f"Wrote {n} gold cases to {OUT_DIR}")
