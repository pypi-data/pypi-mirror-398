import phonenumbers
from phonenumbers import (
    geocoder, carrier, timezone, PhoneNumberFormat, PhoneNumberMatcher
)
import logging
import re
from datetime import datetime
import json

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("tracer.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("PhoneTracer")

def ascii_logo():
    print(r"""
         __        __        ___ ___  __        __   ___  __  
        |__) |__| /  \ |\ | |__   |  |__)  /\  /  ` |__  |__) 
        |    |  | \__/ | \| |___  |  |  \ /~~\ \__, |___ |  \ 
    """)

def spam_heuristic(number: str) -> int:
    score = 0
    if re.search(r"(\d)\1{4,}", number):
        score += 2
    if number.count("0") > 6:
        score += 1
    return score

def analyze_number(raw_number: str):
    try:
        p = phonenumbers.parse(raw_number, None)
        return {
            "raw_input": raw_number,
            "valid": phonenumbers.is_valid_number(p),
            "possible": phonenumbers.is_possible_number(p),
            "international": phonenumbers.format_number(
                p, PhoneNumberFormat.INTERNATIONAL
            ),
            "e164": phonenumbers.format_number(
                p, PhoneNumberFormat.E164
            ),
            "country": geocoder.description_for_number(p, "en") or "N/A",
            "carrier": carrier.name_for_number(p, "en") or "Unknown",
            "timezones": list(timezone.time_zones_for_number(p)),
            "spam_score": spam_heuristic(raw_number)
        }
    except phonenumbers.NumberParseException:
        return None

def scan_text(text, region="US"):
    results = []
    for m in PhoneNumberMatcher(text, region):
        r = analyze_number(m.raw_string)
        if r:
            results.append(r)
    return results

def export_json(results, hint="output"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/{ts}_{hint}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    logger.info(f"Saved results to {filename}")
    return filename

def save_results_always(results, hint="run"):
    """
    Always saves results to a timestamped JSON file.
    Called by ALL interfaces.
    """
    if not results:
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/{ts}_{hint}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    logger.info(f"Results saved to {filename}")
    return filename



def format_output(data: dict) -> str:
    status = []
    if data["valid"]:
        status.append("Valid")
    if data["possible"]:
        status.append("Possible")

    spam_level = (
        "Low" if data["spam_score"] == 0 else
        "Medium" if data["spam_score"] == 1 else
        "High"
    )

    output = f"""
            ✔ Number Status      : {' & '.join(status) if status else 'Invalid'}
            🌍 Country / Region  : {data['country']}
            📞 Carrier           : {data['carrier']}
            🕒 Time Zone(s)      : {', '.join(data['timezones'])}
            📐 Number Formats
               • International  : {data['international']}
               • E.164          : {data['e164']}
            ⚠ Spam Indicator     : {spam_level}
            """

    return output.strip()
