#!/usr/bin/env python3
"""Fetch only the latest drawn period from the public MOF prize page."""
import datetime as dt
import json
import pathlib
import re
import urllib.request
from html.parser import HTMLParser

class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        value = " ".join(data.split())
        if value:
            self.parts.append(value)

now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
if now.month % 2 != 1 or now.day < 26:
    raise SystemExit("Not a post-draw day; refusing update")
year = now.year - 1911
end = now.month - 1
if end == 0:
    year -= 1
    end = 12
start = end - 1
term = f"{year:03d}{start:02d}"
url = f"https://www.etax.nat.gov.tw/etw-main/ETW183W2_{term}/"
req = urllib.request.Request(url, headers={"User-Agent": "InvoiceChecker-AI-Test/1.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    html = resp.read().decode("utf-8")
parser = Text()
parser.feed(html)
text = " ".join(parser.parts)
def extract(label, next_label):
    pattern = re.escape(label) + r"(?:(?!" + re.escape(next_label) + r").){0,450}"
    m = re.search(pattern, text, re.S)
    if not m:
        raise ValueError(f"Missing {label}")
    numbers = re.findall(r"(?<!\\d)\\d{8}(?!\\d)", m.group())
    if not numbers:
        raise ValueError(f"No eight-digit prize after {label}")
    return numbers
special = extract("特別獎", "特獎")[0]
grand = extract("特獎", "頭獎")[0]
first = extract("頭獎", "增開六獎")
if len(first) < 3:
    raise ValueError("Too few first prizes; source layout may have changed")
datafile = pathlib.Path("prizes.json")
existing = json.loads(datafile.read_text(encoding="utf-8")) if datafile.exists() else {}
existing[term] = {"special": special, "grand": grand, "first": first[:3]}
ordered = dict(sorted(existing.items(), reverse=True)[:4])
datafile.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Updated {term} from {url}")
