#!/usr/bin/env python3
"""
extractors.py

Simple heuristics to extract candidate (email, cpf, name, password) tuples from
free-form text. These are intentionally conservative — they attempt to find
likely leak patterns such as CSV lines, `email:password` pairs, or simple
CSV-like rows.
"""
import re
import csv
from io import StringIO

RE_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
RE_CPF = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
RE_EMAIL_PASS = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+)[:;|,\t ]+([^\s,;|]+)")


def extract_from_text(text):
    """Return a list of dicts with extracted fields (email,password,cpf,name,raw)
    """
    results = []

    # Try to find email:password patterns
    for m in RE_EMAIL_PASS.finditer(text):
        email = m.group(1)
        password = m.group(2)
        results.append({"email": email, "password": password, "raw": m.group(0)})

    # Try CSV-like lines: detect lines with comma and an email present
    for line in text.splitlines():
        if "," in line and RE_EMAIL.search(line):
            # Try parse as CSV row
            try:
                rdr = csv.reader([line])
                row = next(rdr)
                # find email in row
                email = next((c for c in row if RE_EMAIL.search(c)), None)
                password = next((c for c in row if len(c) > 0 and c != email and not RE_EMAIL.search(c)), None)
                if email:
                    item = {"email": email, "password": password or "", "raw": line}
                    results.append(item)
            except Exception:
                pass

    # CPF scanning
    for m in RE_CPF.finditer(text):
        results.append({"cpf": m.group(0), "raw": m.group(0)})

    # If nothing found, try to find any emails alone
    if not results:
        for m in RE_EMAIL.finditer(text):
            results.append({"email": m.group(0), "raw": m.group(0)})

    return results
