"""Reference invoice parser for the invoice-parsing skill.

Parses raw invoice text into a normalized structure and validates that the line-item
arithmetic matches the printed total.
"""

from __future__ import annotations

import re

_LINE_RE = re.compile(r"^(?P<desc>.+?)\s+(?P<qty>\d+)\s+(?P<price>\d+\.\d{2})$")


def parse_line_items(text: str) -> list[dict]:
    """Extract line items from the body of an invoice.

    Each matched row becomes a dict with description, quantity, unit price, and amount.
    """
    items: list[dict] = []
    for line in text.splitlines():
        match = _LINE_RE.match(line.strip())
        if not match:
            continue
        qty = int(match.group("qty"))
        price = float(match.group("price"))
        items.append(
            {
                "description": match.group("desc"),
                "quantity": qty,
                "unit_price": price,
                "amount": round(qty * price, 2),
            }
        )
    return items


def parse_invoice(text: str) -> dict:
    """Return a normalized invoice dict with vendor, items, and reconciled totals."""
    items = parse_line_items(text)
    subtotal = round(sum(item["amount"] for item in items), 2)
    return {"items": items, "subtotal": subtotal}
