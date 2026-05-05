import ast
import json
import os
import random
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP
from html import escape
import re
from urllib import error as urllib_error
from urllib import request as urllib_request

import streamlit as st
from dotenv import load_dotenv


load_dotenv()
load_dotenv("env")


PRODUCTS = [
    {"name": "KVH", "kind": "structural_beam"},
    {"name": "BSH", "kind": "structural_beam"},
    {"name": "KERTO", "kind": "structural_beam"},
    {"name": "Hobelware", "kind": "hobelware"},
    {
        "name": "OSB-Platte",
        "kind": "panel",
        "formats": ["250 x 62,5 cm", "250 x 67,5 cm"],
    },
    {
        "name": "Siebdruckplatte",
        "kind": "panel",
        "formats": ["125 x 250 cm"],
    },
    {
        "name": "3-Schicht-Platte",
        "kind": "panel",
        "formats": ["125 x 205 cm", "125 x 250 cm"],
    },
    {
        "name": "Dekorplatte",
        "kind": "panel",
        "formats": ["280 x 207 cm", "410 x 130 cm"],
    },
]

STRUCTURAL_WIDTHS_BY_LEVEL = {
    1: [Decimal("0.04"), Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12")],
    2: [Decimal("0.04"), Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14")],
    3: [Decimal("0.04"), Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16")],
}
STRUCTURAL_HEIGHTS_BY_LEVEL = {
    1: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.16"), Decimal("0.20")],
    2: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.20"), Decimal("0.24")],
    3: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20"), Decimal("0.24"), Decimal("0.28")],
}
STRUCTURAL_LENGTHS_BY_LEVEL = {
    1: [Decimal("5.0"), Decimal("6.0"), Decimal("7.0"), Decimal("8.0")],
    2: [Decimal("5.0"), Decimal("6.0"), Decimal("7.0"), Decimal("8.0"), Decimal("9.0"), Decimal("10.0")],
    3: [Decimal("6.0"), Decimal("7.0"), Decimal("8.0"), Decimal("9.0"), Decimal("10.0"), Decimal("11.0"), Decimal("12.0"), Decimal("13.0")],
}
HOBEL_WIDTHS_BY_LEVEL = {
    1: [Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16")],
    2: [Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18")],
    3: [Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20")],
}
HOBEL_THICKNESSES_BY_LEVEL = {
    1: [Decimal("0.019"), Decimal("0.023")],
    2: [Decimal("0.019"), Decimal("0.023")],
    3: [Decimal("0.019"), Decimal("0.023"), Decimal("0.027")],
}
HOBEL_LENGTHS_BY_LEVEL = {
    1: [Decimal("3.0"), Decimal("3.5"), Decimal("4.0"), Decimal("4.5"), Decimal("5.0"), Decimal("6.0")],
    2: [Decimal("3.0"), Decimal("3.5"), Decimal("4.0"), Decimal("4.5"), Decimal("5.0"), Decimal("5.5"), Decimal("6.0")],
    3: [Decimal("3.0"), Decimal("3.5"), Decimal("4.0"), Decimal("4.5"), Decimal("5.0"), Decimal("5.5"), Decimal("6.0")],
}
COUNTS_BY_LEVEL = {
    1: [4, 6, 8, 10, 12, 16, 20],
    2: [5, 6, 8, 10, 12, 14, 18, 24, 30],
    3: [5, 7, 9, 11, 14, 18, 22, 28, 36],
}
BOARD_COUNTS_BY_LEVEL = {
    1: [4, 6, 8, 10, 12],
    2: [6, 8, 10, 12, 14, 16],
    3: [8, 10, 12, 14, 16, 18, 20],
}
THICKNESSES_BY_LEVEL = {
    1: [Decimal("0.018"), Decimal("0.022"), Decimal("0.027"), Decimal("0.040"), Decimal("0.050")],
    2: [Decimal("0.019"), Decimal("0.022"), Decimal("0.025"), Decimal("0.027"), Decimal("0.040"), Decimal("0.050")],
    3: [Decimal("0.019"), Decimal("0.022"), Decimal("0.025"), Decimal("0.032"), Decimal("0.038"), Decimal("0.045"), Decimal("0.050")],
}
M3_PRICES_BY_LEVEL = {
    1: [Decimal("280"), Decimal("320"), Decimal("350"), Decimal("420"), Decimal("560"), Decimal("720")],
    2: [Decimal("295"), Decimal("365"), Decimal("420"), Decimal("445"), Decimal("585"), Decimal("760")],
    3: [Decimal("337"), Decimal("398"), Decimal("478"), Decimal("525"), Decimal("693"), Decimal("815")],
}
TOTAL_VOLUMES_BY_LEVEL = {
    1: [Decimal("0.72"), Decimal("0.96"), Decimal("1.20"), Decimal("1.44"), Decimal("1.80"), Decimal("2.40")],
    2: [Decimal("0.84"), Decimal("1.05"), Decimal("1.26"), Decimal("1.68"), Decimal("2.10"), Decimal("2.52")],
    3: [Decimal("0.945"), Decimal("1.155"), Decimal("1.485"), Decimal("1.890"), Decimal("2.310"), Decimal("2.625")],
}
RUNNING_METER_PRICES_BY_LEVEL = {
    1: [Decimal("4.80"), Decimal("6.20"), Decimal("7.50"), Decimal("9.60"), Decimal("12.40")],
    2: [Decimal("5.35"), Decimal("6.85"), Decimal("8.40"), Decimal("10.25"), Decimal("13.75")],
    3: [Decimal("5.95"), Decimal("7.40"), Decimal("9.35"), Decimal("11.80"), Decimal("14.60")],
}
FLOORING_PRODUCTS = [
    {
        "name": "Eiche-Massivholzdiele",
        "lengths": [Decimal("1.20"), Decimal("1.50"), Decimal("1.80"), Decimal("2.00"), Decimal("2.20")],
        "widths": [Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20"), Decimal("0.22")],
        "thicknesses": [Decimal("0.018"), Decimal("0.020"), Decimal("0.021")],
        "package_counts": [4, 5, 6, 7, 8],
    },
    {
        "name": "Parkett",
        "lengths": [Decimal("0.60"), Decimal("0.90"), Decimal("1.20"), Decimal("1.50"), Decimal("1.80")],
        "widths": [Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20")],
        "thicknesses": [Decimal("0.010"), Decimal("0.012"), Decimal("0.014")],
        "package_counts": [6, 7, 8],
    },
    {
        "name": "Vinylboden",
        "lengths": [Decimal("0.90"), Decimal("1.00"), Decimal("1.20"), Decimal("1.22"), Decimal("1.50")],
        "widths": [Decimal("0.12"), Decimal("0.15"), Decimal("0.18"), Decimal("0.20"), Decimal("0.23")],
        "thicknesses": [Decimal("0.003"), Decimal("0.004"), Decimal("0.005")],
        "package_counts": [10, 12, 16, 20],
    },
]
PANEL_M2_PRICES_BY_LEVEL = {
    1: [Decimal("8.90"), Decimal("12.50"), Decimal("18.90"), Decimal("24.90"), Decimal("32.50")],
    2: [Decimal("9.80"), Decimal("14.90"), Decimal("22.50"), Decimal("29.90"), Decimal("38.50")],
    3: [Decimal("11.40"), Decimal("17.80"), Decimal("26.90"), Decimal("34.90"), Decimal("44.50")],
}
PANEL_COUNTS_BY_LEVEL = {
    1: [6, 8, 10, 12, 15, 18, 20],
    2: [10, 12, 16, 20, 24, 30],
    3: [14, 18, 22, 28, 32, 40],
}
PRODUCT_DENSITIES = {
    "KVH": [Decimal("430"), Decimal("450"), Decimal("470")],
    "BSH": [Decimal("450"), Decimal("480"), Decimal("500")],
    "KERTO": [Decimal("500"), Decimal("510"), Decimal("530")],
    "Hobelware": [Decimal("470"), Decimal("520"), Decimal("560")],
    "OSB-Platte": [Decimal("590"), Decimal("620"), Decimal("650")],
    "Siebdruckplatte": [Decimal("650"), Decimal("700"), Decimal("750")],
    "3-Schicht-Platte": [Decimal("450"), Decimal("500"), Decimal("550")],
    "Dekorplatte": [Decimal("620"), Decimal("650"), Decimal("700")],
}
FLOORING_NEEDS_BY_LEVEL = {
    1: [Decimal("25"), Decimal("40"), Decimal("60"), Decimal("80")],
    2: [Decimal("45"), Decimal("70"), Decimal("90"), Decimal("100"), Decimal("120")],
    3: [Decimal("65"), Decimal("95"), Decimal("125"), Decimal("150"), Decimal("180")],
}
ORDER_EK_VALUES_BY_LEVEL = {
    1: [Decimal("280"), Decimal("420"), Decimal("560"), Decimal("750"), Decimal("900")],
    2: [Decimal("365"), Decimal("585"), Decimal("760"), Decimal("980"), Decimal("1250")],
    3: [Decimal("478"), Decimal("693"), Decimal("815"), Decimal("1190"), Decimal("1540")],
}

UNIT_LABELS = {
    "m3": "Kubikmeter",
    "m2": "Quadratmeter",
    "lfm": "Laufmeter",
    "EUR": "Euro",
    "kg": "Kilogramm",
    "m": "Meter",
    "cm": "Zentimeter",
    "mm": "Millimeter",
    "Faktor": "Faktor",
    "Pakete": "Pakete",
    "Prozent": "Prozent",
}

ERROR_PATTERN_GUIDE = """
1. Falsche Umrechnungslogik bei Dimensionen:
- Verwechslung zwischen Laufmeter, Quadratmeter und Kubikmeter.
- Richtungen wie m zu m2, m2 zu m3 oder der Rückweg werden falsch gedacht.

2. Maße nicht vollständig berücksichtigt:
- Breite, Höhe oder Dicke wird vergessen.
- Klassiker sind lfm zu m2 ohne Breite oder m2 zu m3 ohne Dicke.

3. Preisbasis falsch angewendet:
- Ein Preis pro Quadratmeter, Laufmeter oder Kubikmeter wird mit der falschen Mengeneinheit verknüpft.

4. Fehler bei Kommazahlen und Einheitensprüngen:
- Millimeter, Zentimeter und Meter werden falsch umgesetzt.
- Typische Muster sind Faktor 10, 100 oder 1000, zum Beispiel 0,18 statt 0,018.

5. Verhältnis falsch interpretiert:
- Es wird multipliziert, obwohl geteilt werden müsste, oder umgekehrt.

6. Vorwärts- und Rückwärtsrechnung verwechselt:
- Eine Richtung klappt, aber die Umkehrung wird falsch aufgebaut.

7. Fehlende Struktur oder falsche Reihenfolge:
- Umrechnung, Mengenrechnung und Preisrechnung werden vermischt.

8. Kein Plausibilitätscheck:
- Das Ergebnis wird nicht auf Größenordnung und fachliche Plausibilität geprüft.
"""

FORMULA_GUIDE = """
Preisumrechnung:
- Euro pro Kubikmeter zu Euro pro Quadratmeter: Preis pro Kubikmeter x Dicke
- Euro pro Kubikmeter zu Euro pro Laufmeter: Preis pro Kubikmeter x Breite x Höhe
- Euro pro Quadratmeter zu Euro pro Laufmeter: Preis pro Quadratmeter x Breite
- Euro pro Quadratmeter zu Euro pro Kubikmeter: Preis pro Quadratmeter / Dicke
- Euro pro Laufmeter zu Euro pro Quadratmeter: Preis pro Laufmeter / Breite
- Euro pro Laufmeter zu Euro pro Kubikmeter: Preis pro Laufmeter / (Breite x Höhe)

Mengen- und Volumenumrechnung:
- Kubikmeter zu Quadratmeter: Kubikmeter / Dicke
- Quadratmeter zu Kubikmeter: Quadratmeter x Dicke
- Kubikmeter zu Laufmeter: Kubikmeter / (Breite x Höhe)
- Laufmeter zu Kubikmeter: Laufmeter x Breite x Höhe
- Quadratmeter zu Laufmeter: Quadratmeter / Breite
- Laufmeter zu Quadratmeter: Laufmeter x Breite

Bodenpakete:
- Fläche pro Stück: Länge x Breite
- Paketfläche: Fläche pro Stück x Stückzahl im Paket
- Benötigte Pakete: Bedarf in Quadratmeter / Paketfläche, danach auf volle Pakete aufrunden

Dichte und Gewicht:
- Gewicht in Kilogramm: Kubikmeter x Dichte in Kilogramm pro Kubikmeter
- Dichte in Kilogramm pro Kubikmeter: Gewicht / Kubikmeter

Deckungsbeitrag:
- Absoluter DB in Euro: VK - EK
- Relativer DB in Prozent: (VK - EK) / VK x 100
- VK aus EK und DB: EK / (1 - DB-Satz)
- EK aus VK und DB: VK x (1 - DB-Satz)
"""

REQUEST_INTROS = [
    "Ein Kunde fragt folgende Ware an",
    "Eine Kundin interessiert sich für folgende Ware",
    "Es geht eine Anfrage über folgendes Material ein",
    "Für ein Angebot liegt folgende Ware vor",
    "Im Tagesgeschäft kommt folgende Anfrage rein",
]


def q(value_str):
    return Decimal(value_str)


def format_decimal(value, places):
    quant = q("1") if places == 0 else q("1." + ("0" * places))
    return str(value.quantize(quant, rounding=ROUND_HALF_UP)).replace(".", ",")


def precise_decimal_places(value, min_places=3, max_places=5):
    for places in range(min_places, max_places + 1):
        quant = q("1." + ("0" * places))
        if value == value.quantize(quant, rounding=ROUND_HALF_UP):
            return places
    return max_places


def round_up_to_whole(value):
    return value.to_integral_value(rounding=ROUND_CEILING)


def ensure_sentence(text):
    text = str(text).strip()
    if not text:
        return text
    if text[-1] in ".!?":
        return text
    return f"{text}."


def format_m(value):
    return format_decimal(value, 2).rstrip("0").rstrip(",")


def format_cm(value):
    return format_decimal(value * 100, 1).rstrip("0").rstrip(",")


def format_mm(value):
    return format_decimal(value * 1000, 0)


def unit_label(unit):
    return UNIT_LABELS.get(unit, unit)


def normalize_secret_value(value):
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"\s+", "", text)
    return text.strip()


def get_openai_api_key():
    for key in ("OPENAI_API_KEY", "openai_api_key"):
        try:
            if key in st.secrets and st.secrets[key]:
                secret_value = normalize_secret_value(st.secrets[key])
                if secret_value:
                    return secret_value
        except Exception:
            pass

        env_value = os.getenv(key)
        if env_value:
            env_value = normalize_secret_value(env_value)
            if env_value:
                return env_value

    return None


def get_optional_openai_header(name):
    try:
        if name in st.secrets and st.secrets[name]:
            value = str(st.secrets[name]).strip()
            if value:
                return value
    except Exception:
        pass

    value = os.getenv(name)
    if value:
        value = value.strip()
        if value:
            return value

    return None


def extract_responses_text(payload):
    if payload.get("output_text"):
        return str(payload["output_text"]).strip()

    collected = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if content.get("type") in ("output_text", "text") and text:
                collected.append(str(text))
            refusal_text = content.get("refusal")
            if content.get("type") == "refusal" and refusal_text:
                collected.append(str(refusal_text))

    return "\n".join(collected).strip()


def display_measure(value_m, allowed_units):
    unit = random.choice(list(allowed_units))
    if unit == "m":
        return f"{format_m(value_m)} m"
    if unit == "cm":
        return f"{format_cm(value_m)} cm"
    if unit == "mm":
        return f"{format_mm(value_m)} mm"
    return f"{format_decimal(value_m, 3)} m"


def display_measure_pair_same_unit(first_m, second_m, allowed_units):
    unit = random.choice(list(allowed_units))
    return display_measure(first_m, (unit,)), display_measure(second_m, (unit,))


def call_openai_responses_api(prompt, max_output_tokens):
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY fehlt in st.secrets und in der lokalen Umgebung.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    organization = get_optional_openai_header("OPENAI_ORGANIZATION")
    project = get_optional_openai_header("OPENAI_PROJECT")
    if organization:
        headers["OpenAI-Organization"] = organization
    if project:
        headers["OpenAI-Project"] = project

    payload = {
        "model": "gpt-4o-mini",
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    }
                ],
            }
        ],
        "max_output_tokens": max_output_tokens,
        "text": {
            "verbosity": "low",
        },
    }

    request = urllib_request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib_request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
    except urllib_error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Netzwerkfehler: {exc.reason}") from exc

    response_data = json.loads(body)
    return extract_responses_text(response_data)


def make_guided_step(
    label,
    expected,
    unit,
    display_places,
    round_for_check,
    correction,
    formula_hint=None,
    placeholder=None,
    match_mode=None,
):
    return {
        "label": label,
        "expected": expected,
        "unit": unit,
        "display_places": display_places,
        "round_for_check": round_for_check,
        "correction": correction,
        "formula_hint": formula_hint or correction,
        "placeholder": placeholder,
        "match_mode": match_mode,
    }


def format_solution_steps(*steps):
    lines = ["Rechenweg:"]
    for index, (title, formula, calculation) in enumerate(steps, start=1):
        if index > 1:
            lines.append("")
        lines.append(f"{index}. {title}")
        lines.append(f"Formel: {formula}")
        lines.append(f"Berechnung: {calculation}")
    return "\n".join(lines)


def current_level(task_number):
    if task_number >= 10:
        return 3
    if task_number >= 4:
        return 2
    return 1


def pick_level(task_number):
    base_level = current_level(task_number)
    if base_level == 1:
        return random.choices([1, 2, 3], weights=[3, 4, 3], k=1)[0]
    if base_level == 2:
        return random.choices([1, 2, 3], weights=[2, 4, 4], k=1)[0]
    return random.choices([1, 2, 3], weights=[1, 3, 6], k=1)[0]


def choice_for_level(pool_by_level, level):
    return random.choice(pool_by_level[level])


def product_name(product):
    if isinstance(product, dict):
        return product["name"]
    return str(product)


def generate_structural_dimensions(level):
    first = choice_for_level(STRUCTURAL_WIDTHS_BY_LEVEL, level)
    second = choice_for_level(STRUCTURAL_HEIGHTS_BY_LEVEL, level)
    return sorted([first, second])


def panel_thickness_for_product(product, level):
    name = product_name(product)
    pools = {
        "OSB-Platte": {
            1: [Decimal("0.012"), Decimal("0.015"), Decimal("0.018"), Decimal("0.022")],
            2: [Decimal("0.012"), Decimal("0.015"), Decimal("0.018"), Decimal("0.022"), Decimal("0.025")],
            3: [Decimal("0.012"), Decimal("0.015"), Decimal("0.018"), Decimal("0.022"), Decimal("0.025"), Decimal("0.030")],
        },
        "Siebdruckplatte": {
            1: [Decimal("0.009"), Decimal("0.012"), Decimal("0.015"), Decimal("0.018")],
            2: [Decimal("0.009"), Decimal("0.012"), Decimal("0.015"), Decimal("0.018"), Decimal("0.021")],
            3: [Decimal("0.009"), Decimal("0.012"), Decimal("0.015"), Decimal("0.018"), Decimal("0.021"), Decimal("0.030")],
        },
        "3-Schicht-Platte": {
            1: [Decimal("0.019"), Decimal("0.022"), Decimal("0.027"), Decimal("0.040")],
            2: [Decimal("0.019"), Decimal("0.022"), Decimal("0.027"), Decimal("0.032"), Decimal("0.040")],
            3: [Decimal("0.019"), Decimal("0.022"), Decimal("0.027"), Decimal("0.032"), Decimal("0.040"), Decimal("0.050")],
        },
        "Dekorplatte": {
            1: [Decimal("0.008"), Decimal("0.010"), Decimal("0.016"), Decimal("0.019")],
            2: [Decimal("0.008"), Decimal("0.010"), Decimal("0.016"), Decimal("0.019"), Decimal("0.022")],
            3: [Decimal("0.008"), Decimal("0.010"), Decimal("0.016"), Decimal("0.019"), Decimal("0.022"), Decimal("0.025")],
        },
    }
    return random.choice(pools.get(name, THICKNESSES_BY_LEVEL)[level])


def m3_price_for_product(product, level):
    name = product_name(product)
    pools = {
        "KVH": {
            1: [Decimal("350"), Decimal("390"), Decimal("420"), Decimal("460")],
            2: [Decimal("380"), Decimal("420"), Decimal("460"), Decimal("520")],
            3: [Decimal("398"), Decimal("445"), Decimal("495"), Decimal("560")],
        },
        "BSH": {
            1: [Decimal("560"), Decimal("640"), Decimal("720"), Decimal("780")],
            2: [Decimal("585"), Decimal("690"), Decimal("760"), Decimal("845")],
            3: [Decimal("640"), Decimal("760"), Decimal("890"), Decimal("980")],
        },
        "KERTO": {
            1: [Decimal("720"), Decimal("840"), Decimal("960")],
            2: [Decimal("815"), Decimal("950"), Decimal("1080")],
            3: [Decimal("890"), Decimal("1050"), Decimal("1180"), Decimal("1320")],
        },
        "Hobelware": {
            1: [Decimal("720"), Decimal("840"), Decimal("960")],
            2: [Decimal("815"), Decimal("950"), Decimal("1080")],
            3: [Decimal("890"), Decimal("1050"), Decimal("1180"), Decimal("1320")],
        },
        "OSB-Platte": {
            1: [Decimal("280"), Decimal("320"), Decimal("350")],
            2: [Decimal("295"), Decimal("337"), Decimal("365")],
            3: [Decimal("320"), Decimal("365"), Decimal("398")],
        },
        "Siebdruckplatte": {
            1: [Decimal("560"), Decimal("720"), Decimal("840")],
            2: [Decimal("585"), Decimal("760"), Decimal("890")],
            3: [Decimal("693"), Decimal("815"), Decimal("980")],
        },
        "3-Schicht-Platte": {
            1: [Decimal("720"), Decimal("840"), Decimal("960")],
            2: [Decimal("760"), Decimal("890"), Decimal("1050")],
            3: [Decimal("815"), Decimal("980"), Decimal("1180")],
        },
        "Dekorplatte": {
            1: [Decimal("560"), Decimal("720"), Decimal("840")],
            2: [Decimal("585"), Decimal("760"), Decimal("890")],
            3: [Decimal("693"), Decimal("815"), Decimal("980")],
        },
    }
    return random.choice(pools.get(name, M3_PRICES_BY_LEVEL)[level])


def panel_m2_price_for_product(product, level):
    name = product_name(product)
    pools = {
        "OSB-Platte": {
            1: [Decimal("8.90"), Decimal("11.90"), Decimal("14.90")],
            2: [Decimal("9.80"), Decimal("12.90"), Decimal("16.90")],
            3: [Decimal("11.40"), Decimal("14.90"), Decimal("18.90")],
        },
        "Siebdruckplatte": {
            1: [Decimal("24.90"), Decimal("32.50"), Decimal("38.50")],
            2: [Decimal("29.90"), Decimal("38.50"), Decimal("44.50")],
            3: [Decimal("34.90"), Decimal("44.50"), Decimal("54.90")],
        },
        "3-Schicht-Platte": {
            1: [Decimal("22.50"), Decimal("29.90"), Decimal("36.90")],
            2: [Decimal("26.90"), Decimal("34.90"), Decimal("42.50")],
            3: [Decimal("32.50"), Decimal("39.90"), Decimal("49.90")],
        },
        "Dekorplatte": {
            1: [Decimal("18.90"), Decimal("24.90"), Decimal("32.50")],
            2: [Decimal("22.50"), Decimal("29.90"), Decimal("38.50")],
            3: [Decimal("26.90"), Decimal("34.90"), Decimal("44.50")],
        },
    }
    return random.choice(pools.get(name, PANEL_M2_PRICES_BY_LEVEL)[level])


def panel_format_dimensions(format_text):
    dimensions = {
        "250 x 62,5 cm": (Decimal("2.50"), Decimal("0.625")),
        "250 x 67,5 cm": (Decimal("2.50"), Decimal("0.675")),
        "125 x 250 cm": (Decimal("1.25"), Decimal("2.50")),
        "125 x 205 cm": (Decimal("1.25"), Decimal("2.05")),
        "280 x 207 cm": (Decimal("2.80"), Decimal("2.07")),
        "410 x 130 cm": (Decimal("4.10"), Decimal("1.30")),
    }
    return dimensions.get(format_text, (Decimal("1.25"), Decimal("2.50")))


def panel_package_count(product):
    name = product_name(product)
    if name == "OSB-Platte":
        return random.choice([40, 50, 60])
    if name == "Siebdruckplatte":
        return random.choice([15, 20, 25])
    return random.choice([20, 25, 30])


def panel_count_for_level(level):
    return random.choice(PANEL_COUNTS_BY_LEVEL[level])


def board_count_for_level(level):
    return random.choice(BOARD_COUNTS_BY_LEVEL[level])


def density_for_product(product):
    return random.choice(PRODUCT_DENSITIES.get(product_name(product), [Decimal("500")]))


def generate_whole_volume_position(level):
    product = random.choice(PRODUCTS)
    kind = product["kind"]

    if kind == "structural_beam":
        length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
        width_m, height_m = generate_structural_dimensions(level)
        count = random.choice(COUNTS_BY_LEVEL[level])
        total_volume = length_m * width_m * height_m * Decimal(count)
        width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))
        context = (
            f"{count} Stück {product['name']} im Format {format_m(length_m)} m x "
            f"{width_text} x {height_text}"
        )
        return product, context, total_volume, precise_decimal_places(total_volume)

    if kind == "panel":
        panel_format = panel_format_text(product)
        length_m, width_m = panel_format_dimensions(panel_format)
        thickness_m = panel_thickness_for_product(product, level)
        panel_count = panel_count_for_level(level)
        total_volume = length_m * width_m * thickness_m * Decimal(panel_count)
        thickness_text = display_measure(thickness_m, ("mm", "cm"))
        context = (
            f"{panel_count} Platten {product['name']} im Format {panel_format} "
            f"bei {thickness_text} Dicke"
        )
        return product, context, total_volume, precise_decimal_places(total_volume)

    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    running_meters = board_length * Decimal(board_count)
    total_volume = width_m * height_m * running_meters
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))
    context = (
        f"{board_count} Bretter {hobelware_display_name(product)} mit je {format_m(board_length)} m Länge, "
        f"{width_text} Breite und {thickness_text} Stärke"
    )
    return product, context, total_volume, precise_decimal_places(total_volume)


def evaluate_expression(text):
    expression = text.strip()
    if "=" in expression:
        parts = [part.strip() for part in expression.split("=") if part.strip()]
        if parts:
            expression = parts[-1]

    cleaned = expression.replace(",", ".")
    cleaned = cleaned.replace("×", "*").replace("·", "*")
    cleaned = cleaned.replace("x", "*").replace("X", "*").replace(":", "/")
    parsed = ast.parse(cleaned, mode="eval")
    return evaluate_ast_node(parsed.body)


def evaluate_ast_node(node):
    if isinstance(node, ast.BinOp):
        left = evaluate_ast_node(node.left)
        right = evaluate_ast_node(node.right)

        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise InvalidOperation

    if isinstance(node, ast.UnaryOp):
        value = evaluate_ast_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return value
        if isinstance(node.op, ast.USub):
            return -value
        raise InvalidOperation

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return Decimal(str(node.value))

    raise InvalidOperation


def generate_structural_product():
    choices = [p for p in PRODUCTS if p["kind"] == "structural_beam"]
    return random.choice(choices)


def generate_panel_product():
    choices = [p for p in PRODUCTS if p["kind"] == "panel"]
    return random.choice(choices)


def generate_hobelware_product():
    choices = [p for p in PRODUCTS if p["kind"] == "hobelware"]
    return random.choice(choices)


def panel_format_text(product):
    formats = product.get("formats", [])
    return random.choice(formats) if formats else ""


def request_intro():
    return random.choice(REQUEST_INTROS)


def hobelware_display_name(product):
    return f"{product['name']} (Glattkantbretter)"


def structural_package_count(width_m, height_m):
    area = width_m * height_m
    if area <= Decimal("0.0048"):
        return 100
    if area <= Decimal("0.0096"):
        return 60
    if area <= Decimal("0.0160"):
        return 40
    return 20


def db_percent_for_product(product, level):
    name = product_name(product)
    pools = {
        "KVH": {
            1: [Decimal("12"), Decimal("13"), Decimal("15")],
            2: [Decimal("12"), Decimal("13"), Decimal("15"), Decimal("17")],
            3: [Decimal("13"), Decimal("15"), Decimal("17"), Decimal("19")],
        },
        "OSB-Platte": {
            1: [Decimal("12"), Decimal("13"), Decimal("15")],
            2: [Decimal("12"), Decimal("13"), Decimal("15"), Decimal("17")],
            3: [Decimal("13"), Decimal("15"), Decimal("17"), Decimal("19")],
        },
        "BSH": {
            1: [Decimal("22"), Decimal("24"), Decimal("25")],
            2: [Decimal("23"), Decimal("24"), Decimal("25"), Decimal("27")],
            3: [Decimal("24"), Decimal("25"), Decimal("27"), Decimal("29")],
        },
        "KERTO": {
            1: [Decimal("24"), Decimal("25"), Decimal("27")],
            2: [Decimal("24"), Decimal("25"), Decimal("27"), Decimal("29")],
            3: [Decimal("25"), Decimal("27"), Decimal("29"), Decimal("31")],
        },
        "Hobelware": {
            1: [Decimal("28"), Decimal("30"), Decimal("32")],
            2: [Decimal("28"), Decimal("30"), Decimal("32"), Decimal("34")],
            3: [Decimal("30"), Decimal("32"), Decimal("34"), Decimal("37")],
        },
        "Dekorplatte": {
            1: [Decimal("28"), Decimal("30"), Decimal("32")],
            2: [Decimal("28"), Decimal("30"), Decimal("32"), Decimal("34")],
            3: [Decimal("30"), Decimal("32"), Decimal("34"), Decimal("37")],
        },
        "Siebdruckplatte": {
            1: [Decimal("20"), Decimal("22"), Decimal("24")],
            2: [Decimal("22"), Decimal("24"), Decimal("25"), Decimal("27")],
            3: [Decimal("24"), Decimal("25"), Decimal("27"), Decimal("30")],
        },
        "3-Schicht-Platte": {
            1: [Decimal("24"), Decimal("25"), Decimal("28")],
            2: [Decimal("25"), Decimal("28"), Decimal("30")],
            3: [Decimal("28"), Decimal("30"), Decimal("32")],
        },
        "Eiche-Massivholzdiele": {
            1: [Decimal("34"), Decimal("36"), Decimal("38")],
            2: [Decimal("36"), Decimal("38"), Decimal("40")],
            3: [Decimal("38"), Decimal("40"), Decimal("42")],
        },
        "Parkett": {
            1: [Decimal("32"), Decimal("34"), Decimal("36")],
            2: [Decimal("34"), Decimal("36"), Decimal("38")],
            3: [Decimal("36"), Decimal("38"), Decimal("40")],
        },
        "Vinylboden": {
            1: [Decimal("30"), Decimal("32"), Decimal("34")],
            2: [Decimal("32"), Decimal("34"), Decimal("36")],
            3: [Decimal("34"), Decimal("36"), Decimal("38")],
        },
    }
    fallback = {
        1: [Decimal("23"), Decimal("25"), Decimal("30")],
        2: [Decimal("23"), Decimal("27"), Decimal("30"), Decimal("33")],
        3: [Decimal("23"), Decimal("28"), Decimal("31"), Decimal("34"), Decimal("37")],
    }
    return random.choice(pools.get(name, fallback)[level])


def db_percent_for_level(level):
    return db_percent_for_product("allgemeine Ware", level)


def task_volume_beam(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    piece_volume = length_m * width_m * height_m
    result = piece_volume * Decimal(count)
    piece_volume_places = precise_decimal_places(piece_volume)
    result_places = precise_decimal_places(result)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: {count} Stück {product['name']} mit je {format_m(length_m)} m Länge, {width_text} Breite und {height_text} Höhe. In diesem Querschnitt liegen normalerweise {package_count} Stück im Paket.\n\nWie viele Kubikmeter sind das insgesamt?",
            f"Für eine Lieferung {product['name']} liegen {count} Stück mit {format_m(length_m)} m Länge sowie {width_text} x {height_text} Querschnitt vor. Ein volles Paket würde hier {package_count} Stück enthalten.\n\nWie viele Kubikmeter ergeben sich daraus?",
            f"Eine Kundin interessiert sich für {count} Stück {product['name']} mit {format_m(length_m)} m Länge, {width_text} Breite und {height_text} Höhe. Im Paket liegen bei diesem Maß normalerweise {package_count} Stück.\n\nWie viele Kubikmeter Ware sind das?",
        ]
    )

    solution = format_solution_steps(
        (
            "Volumen pro Stück",
            "Volumen pro Stück = Länge x Breite x Höhe",
            f"{format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x "
            f"{format_decimal(height_m, 2)} Meter = {format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
        ),
        (
            "Gesamtvolumen",
            "Gesamtvolumen = Volumen pro Stück x Stückzahl",
            f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter x {count} Stück = "
            f"{format_decimal(result, result_places)} Kubikmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": result_places,
        "round_for_check": False,
        "task_type": "volume_beam",
        "correction": "Achte darauf, zuerst das Volumen pro Stück aus Länge x Breite x Höhe zu berechnen und danach mit der Stückzahl zu multiplizieren.",
        "solution": solution,
        "perfect_formula": (
            f"{format_m(length_m)} x {format_decimal(width_m, 2)} x "
            f"{format_decimal(height_m, 2)} x {count}"
        ),
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Rechne zuerst Länge x Breite x Höhe für ein einzelnes Stück.",
            ),
            make_guided_step(
                "Gesamtvolumen",
                result.normalize(),
                "m3",
                result_places,
                False,
                "Multipliziere danach das Volumen pro Stück mit der Stückzahl.",
            ),
        ],
    }


def task_unit_conversion(level):
    conversion = random.choice(
        [
            {
                "product": "KVH",
                "value": Decimal(random.choice(["5", "6", "8", "10", "12"])),
                "from_unit": "m",
                "to_unit": "mm",
                "factor": Decimal("1000"),
                "dimension": "Länge",
                "question": "Wie viele Millimeter sind das?",
                "operation": "x",
            },
            {
                "product": "Hobelware",
                "value": Decimal(random.choice(["300", "400", "500", "600"])),
                "from_unit": "cm",
                "to_unit": "m",
                "factor": Decimal("100"),
                "dimension": "Länge",
                "question": "Wie viele Meter sind das?",
                "operation": "/",
            },
            {
                "product": "Platte",
                "value": Decimal(random.choice(["18", "22", "25", "40", "50"])),
                "from_unit": "mm",
                "to_unit": "cm",
                "factor": Decimal("10"),
                "dimension": "Dicke",
                "question": "Wie viele Zentimeter sind das?",
                "operation": "/",
            },
            {
                "product": "Platte",
                "value": Decimal(random.choice(["18", "22", "25", "40", "50"])),
                "from_unit": "mm",
                "to_unit": "m",
                "factor": Decimal("1000"),
                "dimension": "Dicke",
                "question": "Wie viele Meter sind das?",
                "operation": "/",
            },
            {
                "product": "Hobelware",
                "value": Decimal(random.choice(["10", "12", "16", "20"])),
                "from_unit": "cm",
                "to_unit": "mm",
                "factor": Decimal("10"),
                "dimension": "Breite",
                "question": "Wie viele Millimeter sind das?",
                "operation": "x",
            },
        ]
    )

    if conversion["operation"] == "x":
        result = conversion["value"] * conversion["factor"]
        formula = f"{format_decimal(conversion['value'], 0)} x {format_decimal(conversion['factor'], 0)}"
        formula_text = f"{unit_label(conversion['from_unit'])} zu {unit_label(conversion['to_unit'])}: mal {format_decimal(conversion['factor'], 0)}"
    else:
        result = conversion["value"] / conversion["factor"]
        formula = f"{format_decimal(conversion['value'], 0)} / {format_decimal(conversion['factor'], 0)}"
        formula_text = f"{unit_label(conversion['from_unit'])} zu {unit_label(conversion['to_unit'])}: geteilt durch {format_decimal(conversion['factor'], 0)}"

    display_places = 3 if conversion["to_unit"] == "m" and result != result.quantize(q("1"), rounding=ROUND_HALF_UP) else 0
    if conversion["to_unit"] == "cm" and result != result.quantize(q("1"), rounding=ROUND_HALF_UP):
        display_places = 1

    prompt = random.choice(
        [
            f"Bei {conversion['product']} geht es um eine {conversion['dimension']} von {format_decimal(conversion['value'], 0)} {unit_label(conversion['from_unit'])}.\n\n{conversion['question']}",
            f"Für eine kurze Maßkontrolle liegt folgende Angabe vor: {format_decimal(conversion['value'], 0)} {unit_label(conversion['from_unit'])} {conversion['dimension'].lower()} bei {conversion['product']}.\n\n{conversion['question']}",
        ]
    )

    solution = format_solution_steps(
        (
            "Einheiten umrechnen",
            formula_text,
            f"{formula} = {format_decimal(result, display_places)} {unit_label(conversion['to_unit'])}",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": conversion["to_unit"],
        "display_places": display_places,
        "round_for_check": False,
        "task_type": "unit_conversion",
        "correction": "Achte auf den Sprung zwischen Millimeter, Zentimeter und Meter. Je größer die Einheit wird, desto kleiner wird die Zahl.",
        "solution": solution,
        "perfect_formula": formula,
        "guided_steps": [
            make_guided_step(
                "Einheiten umrechnen",
                result.normalize(),
                conversion["to_unit"],
                display_places,
                False,
                f"Rechne {formula_text.lower()}.",
                formula_text,
                placeholder=formula,
            ),
        ],
    }


def task_price_per_running_meter(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    m3_price = m3_price_for_product(product, level)
    cross_section = width_m * height_m
    result = width_m * height_m * m3_price
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Die Ware kostet {format_decimal(m3_price, 0)} Euro pro Kubikmeter, ist {width_text} breit, {thickness_text} stark und die Bretter sind {format_m(board_length)} m lang.\n\nWie teuer ist 1 Laufmeter?",
            f"Für ein Angebot liegt {display_name} vor. Der Preis beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter. Ein Brett ist {format_m(board_length)} m lang und hat {width_text} x {thickness_text} Querschnitt.\n\nWie teuer ist 1 Laufmeter?",
        ]
    )

    solution = format_solution_steps(
        (
            "Querschnitt",
            "Querschnitt = Breite x Höhe",
            f"{format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 3)} Meter = "
            f"{format_decimal(cross_section, 5)} Quadratmeter",
        ),
        (
            "Preis je Laufmeter",
            "Euro pro Laufmeter = Euro pro Kubikmeter x Querschnitt",
            f"{format_decimal(m3_price, 0)} Euro pro Kubikmeter x {format_decimal(cross_section, 5)} Quadratmeter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "price_per_running_meter",
        "correction": "Prüfe, ob du zuerst Breite x Höhe in Meter angesetzt und daraus das Volumen von 1 Laufmeter bestimmt hast.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(m3_price, 0)} x {format_decimal(width_m, 2)} x "
            f"{format_decimal(height_m, 3)}"
        ),
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                cross_section.normalize(),
                "m2",
                5,
                False,
                "Rechne zuerst Breite x Höhe mit Meterwerten.",
            ),
            make_guided_step(
                "Preis je Laufmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere danach den Querschnitt mit dem Preis pro Kubikmeter.",
                placeholder="Zum Beispiel 0,00304 * 350",
            ),
        ],
    }


def task_price_per_square_meter(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    thickness_m = panel_thickness_for_product(product, level)
    m3_price = m3_price_for_product(product, level)
    result = thickness_m * m3_price
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Eine {product['name']} im Format {panel_format} ist {thickness_text} dick. Ein Kubikmeter kostet {format_decimal(m3_price, 0)} Euro.\n\nWie teuer ist 1 Quadratmeter dieser Platte?",
            f"Für eine {product['name']} im Format {panel_format} liegt ein Preis von {format_decimal(m3_price, 0)} Euro pro Kubikmeter vor. Die Platte ist {thickness_text} dick.\n\nWie teuer ist 1 Quadratmeter?",
        ]
    )

    solution = format_solution_steps(
        (
            "Preis je Quadratmeter",
            "Euro pro Quadratmeter = Euro pro Kubikmeter x Dicke",
            f"{format_decimal(m3_price, 0)} Euro pro Kubikmeter x {format_decimal(thickness_m, 3)} Meter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "price_per_square_meter",
        "correction": "Hier brauchst du nur die Dicke der Platte. Ein Quadratmeter mal Dicke ergibt das Volumen, und dieses Volumen wird mit dem Kubikmeterpreis multipliziert.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Preis pro Quadratmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Rechne hier direkt Dicke in Meter x Preis pro Kubikmeter.",
                "Formel: Dicke in Meter x Preis pro Kubikmeter",
            ),
        ],
    }


def task_square_meters_from_volume(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    thickness_m = panel_thickness_for_product(product, level)
    panel_count = panel_count_for_level(level)
    sheet_area = length_m * width_m
    square_meters = sheet_area * Decimal(panel_count)
    total_volume = square_meters * thickness_m
    result = square_meters
    square_meters_places = precise_decimal_places(square_meters, 2, 4)
    total_volume_places = precise_decimal_places(total_volume)
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Es liegt eine Ware von {format_decimal(total_volume, total_volume_places)} Kubikmeter {product['name']} im Format {panel_format} vor. Die Platte ist {thickness_text} dick.\n\nWie viele Quadratmeter sind das?",
            f"Ein Kunde fragt nach der Fläche einer {product['name']} im Format {panel_format}. Verfügbar sind {format_decimal(total_volume, total_volume_places)} Kubikmeter bei {thickness_text} Dicke.\n\nWie viele Quadratmeter ergeben sich?",
        ]
    )

    solution = format_solution_steps(
        (
            "Quadratmeter",
            "Quadratmeter = Kubikmeter / Dicke",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter / {format_decimal(thickness_m, 3)} Meter = "
            f"{format_decimal(result, square_meters_places)} Quadratmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m2",
        "display_places": square_meters_places,
        "round_for_check": False,
        "task_type": "square_meters_from_volume",
        "correction": "Denk an die Grundformel Quadratmeter = Kubikmeter / Dicke.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Dicke in Meter",
                thickness_m.normalize(),
                "m",
                3,
                False,
                "Wandle die Dicke gedanklich sauber in Meter um.",
            ),
            make_guided_step(
                "Quadratmeter",
                result.normalize(),
                "m2",
                square_meters_places,
                False,
                "Teile das Volumen durch die Dicke.",
            ),
        ],
    }


def task_volume_from_square_meters(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    thickness_m = panel_thickness_for_product(product, level)
    panel_count = panel_count_for_level(level)
    sheet_area = length_m * width_m
    square_meters = sheet_area * Decimal(panel_count)
    result = square_meters * thickness_m
    square_meters_places = precise_decimal_places(square_meters, 2, 4)
    result_places = precise_decimal_places(result)
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Für eine {product['name']} im Format {panel_format} liegen {format_decimal(square_meters, square_meters_places)} Quadratmeter vor. Die Platte ist {thickness_text} dick.\n\nWie viele Kubikmeter sind das?",
            f"Ein Kunde fragt nach dem Volumen einer {product['name']} im Format {panel_format}. Verfügbar sind {format_decimal(square_meters, square_meters_places)} Quadratmeter bei {thickness_text} Dicke.\n\nWie viele Kubikmeter ergeben sich?",
        ]
    )

    solution = format_solution_steps(
        (
            "Kubikmeter",
            "Kubikmeter = Quadratmeter x Dicke",
            f"{format_decimal(square_meters, square_meters_places)} Quadratmeter x {format_decimal(thickness_m, 3)} Meter = "
            f"{format_decimal(result, result_places)} Kubikmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": result_places,
        "round_for_check": False,
        "task_type": "volume_from_square_meters",
        "correction": "Multipliziere die Quadratmeter mit der Dicke in Meter, um auf das Volumen zu kommen.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Kubikmeter",
                result.normalize(),
                "m3",
                result_places,
                False,
                "Rechne hier direkt Quadratmeter x Dicke in Meter.",
                "Formel: Quadratmeter x Dicke",
            ),
        ],
    }


def task_total_price_from_volume(level):
    product, context, total_volume, total_volume_places = generate_whole_volume_position(level)
    m3_price = m3_price_for_product(product, level)
    result = total_volume * m3_price

    prompt = random.choice(
        [
            f"Eine Position umfasst {context}. Das Volumen liegt bei {format_decimal(total_volume, total_volume_places)} Kubikmeter. Der Preis beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Gesamtpreis?",
            f"Für {context} liegt ein Volumen von {format_decimal(total_volume, total_volume_places)} Kubikmeter vor. Das Angebot steht bei {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Gesamtpreis?",
        ]
    )

    solution = format_solution_steps(
        (
            "Gesamtpreis",
            "Gesamtpreis = Volumen x Preis pro Kubikmeter",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(m3_price, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "total_price_from_volume",
        "correction": "Für den Gesamtpreis reicht Volumen x Preis pro Kubikmeter.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Gesamtpreis",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Für den Gesamtpreis brauchst du nur Volumen x Preis pro Kubikmeter.",
                "Volumen x Preis pro Kubikmeter",
            ),
        ],
    }


def task_square_meters_from_running_meters(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    thickness_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    running_meters = board_length * Decimal(board_count)
    result = running_meters * width_m
    running_meters_places = precise_decimal_places(running_meters, 0, 1)
    result_places = precise_decimal_places(result)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name}. Ein Brett ist {format_m(board_length)} m lang, die Ware ist {width_text} breit und {thickness_text} stark.\n\nWie viele Quadratmeter sind das?",
            f"Ein Kunde möchte wissen, wie viele Quadratmeter {display_name} aus {format_decimal(running_meters, running_meters_places)} Laufmetern ergeben. Die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWie viele Quadratmeter sind das?",
        ]
    )

    solution = format_solution_steps(
        (
            "Quadratmeter",
            "Quadratmeter = Laufmeter x Breite",
            f"{format_decimal(running_meters, running_meters_places)} Laufmeter x {format_decimal(width_m, 2)} Meter = "
            f"{format_decimal(result, result_places)} Quadratmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m2",
        "display_places": result_places,
        "round_for_check": False,
        "task_type": "square_meters_from_running_meters",
        "correction": "Für Hobelware rechnest du die Laufmeter mit der Breite in Meter zu Quadratmetern um.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Quadratmeter",
                result.normalize(),
                "m2",
                result_places,
                False,
                "Rechne hier direkt Laufmeter x Breite in Meter.",
                "Formel: Laufmeter x Breite",
            ),
        ],
    }


def task_running_meters_from_volume(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    running_meters = board_length * Decimal(board_count)
    total_volume = width_m * height_m * running_meters
    total_volume_places = precise_decimal_places(total_volume)
    running_meters_places = precise_decimal_places(running_meters, 0, 1)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Insgesamt liegen {format_decimal(total_volume, total_volume_places)} Kubikmeter vor. Die Bretter sind {format_m(board_length)} m lang und haben {width_text} Breite bei {thickness_text} Stärke.\n\nWie viele Laufmeter sind das?",
            f"Ein Kunde möchte wissen, wie viele Laufmeter {display_name} in {format_decimal(total_volume, total_volume_places)} Kubikmeter enthalten sind. Ein Brett ist {format_m(board_length)} m lang, die Ware hat {width_text} Breite und {thickness_text} Stärke.\n\nWie viele Laufmeter sind das?",
        ]
    )

    cross_section = width_m * height_m
    solution = format_solution_steps(
        (
            "Laufmeter",
            "Laufmeter = Kubikmeter / (Breite x Höhe)",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter / "
            f"({format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 3)} Meter) = "
            f"{format_decimal(running_meters, running_meters_places)} Laufmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": running_meters.normalize(),
        "unit": "lfm",
        "display_places": running_meters_places,
        "round_for_check": False,
        "task_type": "running_meters_from_volume",
        "correction": "Setze Breite und Stärke in Meter direkt in die Klammer und teile das Gesamtvolumen durch diese Klammer.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(total_volume, total_volume_places)} / "
            f"({format_decimal(width_m, 2)} x {format_decimal(height_m, 3)})"
        ),
        "guided_steps": [
            make_guided_step(
                "Laufmeter",
                running_meters.normalize(),
                "lfm",
                running_meters_places,
                False,
                "Teile das Gesamtvolumen direkt durch Breite x Stärke in Meter.",
                "Formel: Laufmeter = Kubikmeter / (Breite x Höhe)",
            ),
        ],
    }


def task_running_meters_from_square_meters(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    thickness_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    result = board_length * Decimal(board_count)
    square_meters = result * width_m
    square_meters_places = precise_decimal_places(square_meters)
    result_places = precise_decimal_places(result, 0, 1)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Verfügbar sind {format_decimal(square_meters, square_meters_places)} Quadratmeter. Die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWie viele Laufmeter sind das?",
            f"Ein Kunde fragt nach den Laufmetern einer {display_name}. Verfügbar sind {format_decimal(square_meters, square_meters_places)} Quadratmeter. Die Ware ist {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWie viele Laufmeter ergeben sich?",
        ]
    )

    solution = format_solution_steps(
        (
            "Laufmeter",
            "Laufmeter = Quadratmeter / Breite",
            f"{format_decimal(square_meters, square_meters_places)} Quadratmeter / {format_decimal(width_m, 2)} Meter = "
            f"{format_decimal(result, result_places)} Laufmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "lfm",
        "display_places": result_places,
        "round_for_check": False,
        "task_type": "running_meters_from_square_meters",
        "correction": "Für Hobelware teilst du die Quadratmeter durch die Breite in Meter, um die Laufmeter zu erhalten.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Laufmeter",
                result.normalize(),
                "lfm",
                result_places,
                False,
                "Rechne hier direkt Quadratmeter / Breite in Meter.",
                "Formel: Quadratmeter / Breite",
            ),
        ],
    }


def task_db_sale_price(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)

    piece_volume = length_m * width_m * height_m
    total_volume = piece_volume * Decimal(count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    result = total_ek / divisor
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. Ein Kubikmeter kostet im EK {format_decimal(ek_price_m3, 0)} Euro, bei diesem Querschnitt liegen {package_count} Stück im Paket. Es soll ein DB von {format_decimal(db_percent, 0)} % erzielt werden.\n\nWie hoch ist der gesamte VK für diese Position?",
            f"Für eine Anfrage liegen {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} vor. Der EK liegt bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter, der Ziel-DB bei {format_decimal(db_percent, 0)} %. Ein Paket in diesem Maß enthält {package_count} Stück.\n\nWie hoch ist der gesamte VK?",
        ]
    )

    solution = format_solution_steps(
        (
            "Volumen pro Stück",
            "Volumen pro Stück = Länge x Breite x Höhe",
            f"{format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x "
            f"{format_decimal(height_m, 2)} Meter = {format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
        ),
        (
            "Gesamtvolumen",
            "Gesamtvolumen = Volumen pro Stück x Stückzahl",
            f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter x {count} Stück = "
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
        ),
        (
            "Gesamter EK",
            "Gesamter EK = Gesamtvolumen x EK pro Kubikmeter",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(total_ek, 2)} Euro",
        ),
        (
            "Gesamter VK",
            "Gesamter VK = gesamter EK / (1 - DB-Satz)",
            f"{format_decimal(total_ek, 2)} Euro / {format_decimal(divisor, 2)} = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "db_sale_price",
        "correction": "Rechne zuerst das Volumen eines einzelnen Stücks, daraus das Gesamtvolumen und danach den gesamten EK. Für den VK mit DB teilst du den EK durch 1 minus DB-Satz, also zum Beispiel durch 0,70 bei 30 % DB.",
        "solution": solution,
        "perfect_formula": (
            f"{format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x "
            f"{count} x {format_decimal(ek_price_m3, 0)} / {format_decimal(divisor, 2)}"
        ),
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Rechne zuerst Länge x Breite x Höhe für ein einzelnes Stück.",
                "Länge x Breite x Höhe",
                placeholder="Zum Beispiel 9 * 0,12 * 0,10",
            ),
            make_guided_step(
                "Gesamtvolumen",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Multipliziere danach das Volumen pro Stück mit der Stückzahl.",
                "Volumen pro Stück x Stückzahl",
                placeholder="Zum Beispiel 0,108 * 8",
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere das Gesamtvolumen mit dem EK pro Kubikmeter.",
                "Formel: Gesamtvolumen x EK pro Kubikmeter",
            ),
            make_guided_step(
                "Gesamter VK",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch 1 minus DB-Satz.",
                "Formel: EK / (1 - DB-Satz)",
            ),
        ],
    }


def task_volume_from_running_meters(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    running_meters = board_length * Decimal(board_count)
    result = width_m * height_m * running_meters
    result_places = precise_decimal_places(result)
    running_meters_places = precise_decimal_places(running_meters, 0, 1)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Ein Kunde plant {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name}. Die Bretter sind {format_m(board_length)} m lang und haben einen Querschnitt von {width_text} x {thickness_text}.\n\nWie viele Kubikmeter sind das?",
            f"Für eine Position {display_name} liegen {format_decimal(running_meters, running_meters_places)} Laufmeter bei {width_text} x {thickness_text} Querschnitt vor. Ein Brett ist {format_m(board_length)} m lang.\n\nWie viele Kubikmeter ergeben sich daraus?",
        ]
    )

    solution = format_solution_steps(
        (
            "Gesamtvolumen",
            "Kubikmeter = Laufmeter x Breite x Höhe",
            f"{format_decimal(running_meters, running_meters_places)} Laufmeter x {format_decimal(width_m, 2)} Meter x "
            f"{format_decimal(height_m, 3)} Meter = {format_decimal(result, result_places)} Kubikmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": result_places,
        "round_for_check": False,
        "task_type": "volume_from_running_meters",
        "correction": "Rechne die Laufmeter direkt mit Breite und Höhe in Meter zu Kubikmeter um.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Gesamtvolumen",
                result.normalize(),
                "m3",
                result_places,
                False,
                "Rechne hier direkt Laufmeter x Breite x Höhe.",
                "Formel: Laufmeter x Breite x Höhe",
            ),
        ],
    }


def task_volume_from_total_price(level):
    product, context, total_volume, total_volume_places = generate_whole_volume_position(level)
    m3_price = m3_price_for_product(product, level)
    total_price = total_volume * m3_price

    prompt = random.choice(
        [
            f"Für {context} liegt ein Gesamtpreis von {format_decimal(total_price, 2)} Euro vor. Der Preis beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie viele Kubikmeter sind angeboten?",
            f"Ein Angebot über {context} endet bei {format_decimal(total_price, 2)} Euro. Berechnet wird mit {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie viele Kubikmeter Ware stecken dahinter?",
        ]
    )

    solution = format_solution_steps(
        (
            "Kubikmeter",
            "Volumen = Gesamtpreis / Preis pro Kubikmeter",
            f"{format_decimal(total_price, 2)} Euro / {format_decimal(m3_price, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": total_volume.normalize(),
        "unit": "m3",
        "display_places": total_volume_places,
        "round_for_check": False,
        "task_type": "volume_from_total_price",
        "correction": "Teile den Gesamtpreis durch den Preis pro Kubikmeter.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Kubikmeter",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Teile den Gesamtpreis durch den Preis pro Kubikmeter.",
                "Gesamtpreis / Preis pro Kubikmeter",
            ),
        ],
    }


def task_weight_from_volume(level):
    product, context, total_volume, total_volume_places = generate_whole_volume_position(level)
    density = density_for_product(product)
    result = total_volume * density

    prompt = random.choice(
        [
            f"Für {context} liegt ein Volumen von {format_decimal(total_volume, total_volume_places)} Kubikmeter vor. Die Dichte wird mit {format_decimal(density, 0)} Kilogramm pro Kubikmeter angesetzt.\n\nWie schwer ist die Position ungefähr?",
            f"Eine Lieferung umfasst {context}. Das Volumen beträgt {format_decimal(total_volume, total_volume_places)} Kubikmeter, die Dichte liegt bei {format_decimal(density, 0)} Kilogramm pro Kubikmeter.\n\nWelches Gewicht ergibt sich?",
        ]
    )

    solution = format_solution_steps(
        (
            "Gewicht",
            "Gewicht = Volumen x Dichte",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x "
            f"{format_decimal(density, 0)} Kilogramm pro Kubikmeter = {format_decimal(result, 2)} Kilogramm",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "kg",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "weight_from_volume",
        "correction": "Beim Gewicht ist die Dichte nur der Faktor pro Kubikmeter. Du rechnest also das Volumen mit Kilogramm pro Kubikmeter weiter.",
        "solution": solution,
        "perfect_formula": f"{format_decimal(total_volume, total_volume_places)} x {format_decimal(density, 0)}",
        "guided_steps": [
            make_guided_step(
                "Gewicht",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "kg",
                2,
                True,
                "Multipliziere das Volumen mit der Dichte.",
                "Volumen x Dichte",
                placeholder="Zum Beispiel 1,250 * 620",
            ),
        ],
    }


def task_m3_price_from_running_meter(level):
    product = generate_hobelware_product()
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    price_per_lfm = choice_for_level(RUNNING_METER_PRICES_BY_LEVEL, level)
    cross_section = width_m * height_m
    result = price_per_lfm / cross_section
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Ein Laufmeter {product['name']} kostet {format_decimal(price_per_lfm, 2)} Euro. Der Querschnitt beträgt {width_text} x {thickness_text}.\n\nWie hoch ist der Preis pro Kubikmeter?",
            f"Für {product['name']} liegt ein Laufmeterpreis von {format_decimal(price_per_lfm, 2)} Euro vor. Der Querschnitt beträgt {width_text} x {thickness_text}.\n\nWie hoch ist der Preis pro Kubikmeter?",
        ]
    )

    solution = format_solution_steps(
        (
            "Breite x Höhe",
            "Querschnitt = Breite x Höhe",
            f"{format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 3)} Meter = "
            f"{format_decimal(cross_section, 5)} Quadratmeter",
        ),
        (
            "Preis pro Kubikmeter",
            "Euro pro Kubikmeter = Euro pro Laufmeter / Querschnitt",
            f"{format_decimal(price_per_lfm, 2)} Euro pro Laufmeter / {format_decimal(cross_section, 5)} Quadratmeter = "
            f"{format_decimal(result, 2)} Euro pro Kubikmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "m3_price_from_running_meter",
        "correction": "Teile den Laufmeterpreis durch Breite x Höhe in Meter, um auf den Kubikmeterpreis zu kommen.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(price_per_lfm, 2)} / "
            f"({format_decimal(width_m, 2)} x {format_decimal(height_m, 3)})"
        ),
        "guided_steps": [
            make_guided_step(
                "Breite x Höhe",
                cross_section.normalize(),
                "m2",
                5,
                False,
                "Rechne zuerst Breite x Höhe mit Meterwerten.",
                "Formel: Breite x Höhe",
                placeholder="Zum Beispiel 0,16 * 0,019",
            ),
            make_guided_step(
                "Preis pro Kubikmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den Laufmeterpreis durch den Querschnitt.",
                "Formel: Laufmeterpreis / (Breite x Höhe)",
            ),
        ],
    }


def task_ek_from_vk_db(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    db_percent = db_percent_for_product(product, level)
    ek_price_m3 = m3_price_for_product(product, level)

    total_volume = length_m * width_m * height_m * Decimal(count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_vk = total_ek / divisor
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. Der VK liegt bei {format_decimal(total_vk, 2)} Euro, kalkuliert wurde mit {format_decimal(db_percent, 0)} % DB. Ein Paket in diesem Maß enthält {package_count} Stück.\n\nWie hoch ist der gesamte EK?",
            f"Ein Angebot über {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} endet bei {format_decimal(total_vk, 2)} Euro VK. Der DB beträgt {format_decimal(db_percent, 0)} %. Bei diesem Querschnitt liegen {package_count} Stück im Paket.\n\nWie hoch ist der gesamte EK?",
        ]
    )

    solution = format_solution_steps(
        (
            "DB-Faktor",
            "DB-Faktor = 1 - DB-Satz",
            f"1 - {format_decimal(db_percent, 0)} % = {format_decimal(divisor, 2)}",
        ),
        (
            "Gesamter EK",
            "EK = VK x DB-Faktor",
            f"{format_decimal(total_vk, 2)} Euro x {format_decimal(divisor, 2)} = {format_decimal(total_ek, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "ek_from_vk_db",
        "correction": "Wenn der VK und der DB bekannt sind, rechnest du den EK mit VK x (1 - DB-Satz).",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "DB-Faktor",
                divisor.normalize(),
                "Faktor",
                2,
                False,
                "Ziehe den DB-Satz von 1 ab, also zum Beispiel 0,70 bei 30 % DB.",
                "Formel: 1 - DB-Satz",
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den VK mit dem DB-Faktor.",
                "Formel: VK x DB-Faktor",
            ),
        ],
    }


def task_package_price(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level)
    package_count = structural_package_count(width_m, height_m)
    m3_price = m3_price_for_product(product, level)
    piece_volume = length_m * width_m * height_m
    total_volume = piece_volume * Decimal(package_count)
    result = total_volume * m3_price
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: ein volles Paket {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. In diesem Querschnitt liegen {package_count} Stück im Paket. Der EK liegt bei {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Paketpreis im EK?",
            f"Für ein Angebot liegt ein volles Paket {product['name']} vor. Das Maß beträgt {format_m(length_m)} m x {width_text} x {height_text}, im Paket liegen {package_count} Stück und der EK beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Paketpreis?",
        ]
    )

    solution = format_solution_steps(
        (
            "Volumen pro Stück",
            "Volumen pro Stück = Länge x Breite x Höhe",
            f"{format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x "
            f"{format_decimal(height_m, 2)} Meter = {format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
        ),
        (
            "Paketvolumen",
            "Paketvolumen = Volumen pro Stück x Stückzahl im Paket",
            f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter x {package_count} Stück = "
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
        ),
        (
            "Paketpreis",
            "Paketpreis = Paketvolumen x Preis pro Kubikmeter",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(m3_price, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "package_price",
        "correction": "Starte mit dem Volumen eines einzelnen Stücks. Danach baust du daraus das Paketvolumen auf und erst anschließend den Preis.",
        "solution": solution,
        "perfect_formula": (
            f"{format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x "
            f"{package_count} x {format_decimal(m3_price, 0)}"
        ),
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Beginne mit dem Volumen eines einzelnen Stücks.",
                "Länge, Breite und Höhe als Meterwerte einsetzen",
            ),
            make_guided_step(
                "Paketvolumen",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Nutze das Volumen pro Stück und die Stückzahl im Paket.",
                "Volumen pro Stück mit der Paketstückzahl weiterrechnen",
            ),
            make_guided_step(
                "Paketpreis",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere das Paketvolumen mit dem Preis pro Kubikmeter.",
                "Paketvolumen mit dem Kubikmeterpreis weiterrechnen",
            ),
        ],
    }


def task_panel_package_price(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    package_count = panel_package_count(product)
    m2_price = panel_m2_price_for_product(product, level)

    sheet_area = length_m * width_m
    package_area = sheet_area * Decimal(package_count)
    result = package_area * m2_price
    sheet_area_places = precise_decimal_places(sheet_area)
    package_area_places = precise_decimal_places(package_area)

    prompt = random.choice(
        [
            f"Für ein Angebot liegt ein Plattenpaket {product['name']} im Format {panel_format} vor. Im Paket liegen {package_count} Platten, der Preis beträgt {format_decimal(m2_price, 2)} Euro pro Quadratmeter.\n\nWie hoch ist der Paketpreis?",
            f"Ein Kunde fragt ein ganzes Paket {product['name']} an. Eine Platte hat das Format {panel_format}, im Paket sind {package_count} Stück enthalten und kalkuliert wird mit {format_decimal(m2_price, 2)} Euro pro Quadratmeter.\n\nWie hoch ist der Preis für das Paket?",
        ]
    )

    solution = format_solution_steps(
        (
            "Fläche pro Platte",
            "Fläche pro Platte = Länge x Breite",
            f"{format_decimal(length_m, 2)} Meter x {format_decimal(width_m, 3)} Meter = "
            f"{format_decimal(sheet_area, sheet_area_places)} Quadratmeter",
        ),
        (
            "Paketfläche",
            "Paketfläche = Fläche pro Platte x Plattenanzahl",
            f"{format_decimal(sheet_area, sheet_area_places)} Quadratmeter x {package_count} Stück = "
            f"{format_decimal(package_area, package_area_places)} Quadratmeter",
        ),
        (
            "Paketpreis",
            "Paketpreis = Paketfläche x Preis pro Quadratmeter",
            f"{format_decimal(package_area, package_area_places)} Quadratmeter x {format_decimal(m2_price, 2)} Euro pro Quadratmeter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "panel_package_price",
        "correction": "Rechne zuerst die Fläche pro Platte, dann die Paketfläche und danach den Paketpreis über den Quadratmeterpreis.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(length_m, 2)} x {format_decimal(width_m, 3)} x "
            f"{package_count} x {format_decimal(m2_price, 2)}"
        ),
        "guided_steps": [
            make_guided_step(
                "Fläche pro Platte",
                sheet_area.normalize(),
                "m2",
                sheet_area_places,
                False,
                "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                "Länge x Breite",
                placeholder="Zum Beispiel 2,50 * 0,625",
            ),
            make_guided_step(
                "Paketfläche",
                package_area.normalize(),
                "m2",
                package_area_places,
                False,
                "Multipliziere die Plattenfläche mit der Anzahl der Platten im Paket.",
                "Fläche pro Platte x Plattenanzahl",
                placeholder="Zum Beispiel 1,5625 * 40",
            ),
            make_guided_step(
                "Paketpreis",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere die Paketfläche mit dem Quadratmeterpreis.",
                "Paketfläche x Preis pro Quadratmeter",
                placeholder="Zum Beispiel 62,50 * 12,90",
            ),
        ],
    }


def task_package_db_sale_price(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level)
    package_count = structural_package_count(width_m, height_m)
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)

    piece_volume = length_m * width_m * height_m
    total_volume = piece_volume * Decimal(package_count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    result = total_ek / divisor
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: ein volles Paket {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. Im Paket liegen {package_count} Stück, der EK liegt bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter und es soll ein DB von {format_decimal(db_percent, 0)} % erzielt werden.\n\nWie hoch ist der Paket-VK?",
            f"Für ein Angebot soll ein komplettes Paket {product['name']} kalkuliert werden. Das Maß beträgt {format_m(length_m)} m x {width_text} x {height_text}, im Paket liegen {package_count} Stück. Der EK beträgt {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter, Ziel-DB {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der Verkaufspreis für das Paket?",
        ]
    )

    solution = format_solution_steps(
        (
            "Volumen pro Stück",
            "Volumen pro Stück = Länge x Breite x Höhe",
            f"{format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x "
            f"{format_decimal(height_m, 2)} Meter = {format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
        ),
        (
            "Paketvolumen",
            "Paketvolumen = Volumen pro Stück x Stückzahl im Paket",
            f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter x {package_count} Stück = "
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
        ),
        (
            "Paket-EK",
            "Paket-EK = Paketvolumen x EK pro Kubikmeter",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(total_ek, 2)} Euro",
        ),
        (
            "Paket-VK",
            "Paket-VK = Paket-EK / (1 - DB-Satz)",
            f"{format_decimal(total_ek, 2)} Euro / {format_decimal(divisor, 2)} = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "package_db_sale_price",
        "correction": "Arbeite dich schrittweise vor: erst Einzelvolumen, dann Paketvolumen, danach Paket-EK und erst zuletzt den DB berücksichtigen.",
        "solution": solution,
        "perfect_formula": (
            f"{format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x "
            f"{package_count} x {format_decimal(ek_price_m3, 0)} / {format_decimal(divisor, 2)}"
        ),
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Beginne mit dem Volumen eines einzelnen Stücks.",
                "Länge, Breite und Höhe als Meterwerte einsetzen",
            ),
            make_guided_step(
                "Paketvolumen",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Nutze das Volumen pro Stück und die Stückzahl im Paket.",
                "Volumen pro Stück mit der Paketstückzahl weiterrechnen",
            ),
            make_guided_step(
                "Paket-EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Rechne das Paketvolumen mit dem EK pro Kubikmeter weiter.",
                "Paketvolumen mit dem Kubikmeter-EK weiterrechnen",
            ),
            make_guided_step(
                "Paket-VK",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Berücksichtige zum Schluss den gewünschten DB.",
                "Paket-EK durch den verbleibenden Kostenanteil teilen",
            ),
        ],
    }


def task_flooring_packages(level):
    product = random.choice(FLOORING_PRODUCTS)
    length_m = random.choice(product["lengths"])
    width_m = random.choice(product["widths"])
    thickness_m = random.choice(product["thicknesses"])
    package_count = random.choice(product["package_counts"])
    needed_area = choice_for_level(FLOORING_NEEDS_BY_LEVEL, level)

    piece_area = length_m * width_m
    package_area = piece_area * Decimal(package_count)
    raw_packages = needed_area / package_area
    result = round_up_to_whole(raw_packages)
    piece_area_places = precise_decimal_places(piece_area)
    package_area_places = precise_decimal_places(package_area)
    raw_package_places = precise_decimal_places(raw_packages, 3, 4)

    width_text = display_measure(width_m, ("cm", "m"))
    if product["name"] == "Vinylboden":
        thickness_text = display_measure(thickness_m, ("mm",))
    else:
        thickness_text = display_measure(thickness_m, ("cm", "mm"))

    prompt = random.choice(
        [
            f"Eine Kundin benötigt {format_decimal(needed_area, 0)} Quadratmeter {product['name']}. Eine Diele ist {format_m(length_m)} m lang, {width_text} breit und {thickness_text} stark. In einem Paket liegen {package_count} Stück.\n\nWie viele volle Pakete werden benötigt?",
            f"Für ein Bodenangebot liegen {format_decimal(needed_area, 0)} Quadratmeter Bedarf vor. Die Ware ist {product['name']} mit {format_m(length_m)} m Länge, {width_text} Breite und {thickness_text} Stärke. Pro Paket sind {package_count} Stück enthalten.\n\nWie viele Pakete müssen bestellt werden?",
            f"Im Auftrag stehen {format_decimal(needed_area, 0)} Quadratmeter {product['name']}. Ein Stück misst {format_m(length_m)} m x {width_text}, die Stärke beträgt {thickness_text}, im Paket liegen {package_count} Stück.\n\nWie viele Pakete sind nötig?",
        ]
    )

    solution = format_solution_steps(
        (
            "Fläche pro Stück",
            "Fläche pro Stück = Länge x Breite",
            f"{format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter = "
            f"{format_decimal(piece_area, piece_area_places)} Quadratmeter",
        ),
        (
            "Paketfläche",
            "Paketfläche = Fläche pro Stück x Stückzahl im Paket",
            f"{format_decimal(piece_area, piece_area_places)} Quadratmeter x {package_count} Stück = "
            f"{format_decimal(package_area, package_area_places)} Quadratmeter",
        ),
        (
            "Benötigte Pakete",
            "Pakete = Bedarf / Paketfläche, danach auf volle Pakete aufrunden",
            f"{format_decimal(needed_area, 0)} Quadratmeter / {format_decimal(package_area, package_area_places)} Quadratmeter = "
            f"{format_decimal(raw_packages, raw_package_places)} Pakete, aufgerundet = {format_decimal(result, 0)} Pakete",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result,
        "unit": "Pakete",
        "display_places": 0,
        "round_for_check": False,
        "match_mode": "ceil_integer",
        "task_type": "flooring_packages",
        "correction": "Berechne zuerst die Fläche eines Stücks, dann die Paketfläche und runde die benötigte Paketanzahl am Ende auf ein volles Paket auf.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(needed_area, 0)} / "
            f"({format_m(length_m)} x {format_decimal(width_m, 2)} x {package_count}) = "
            f"{format_decimal(raw_packages, raw_package_places)}, aufgerundet {format_decimal(result, 0)}"
        ),
        "guided_steps": [
            make_guided_step(
                "Fläche pro Stück",
                piece_area.normalize(),
                "m2",
                piece_area_places,
                False,
                "Rechne zuerst Länge x Breite für ein einzelnes Bodenelement.",
                "Länge x Breite",
                placeholder="Zum Beispiel 2 * 0,20",
            ),
            make_guided_step(
                "Paketfläche",
                package_area.normalize(),
                "m2",
                package_area_places,
                False,
                "Multipliziere die Fläche pro Stück mit der Stückzahl im Paket.",
                "Fläche pro Stück x Stückzahl im Paket",
                placeholder="Zum Beispiel 0,40 * 7",
            ),
            make_guided_step(
                "Benötigte Pakete",
                result,
                "Pakete",
                0,
                False,
                "Teile den Bedarf durch die Paketfläche und runde anschließend auf volle Pakete auf.",
                "Bedarf / Paketfläche, dann auf volle Pakete aufrunden",
                placeholder="Zum Beispiel 100 / 2,80",
                match_mode="ceil_integer",
            ),
        ],
    }


def task_absolute_db_from_ek_vk(level):
    product = random.choice(PRODUCTS + FLOORING_PRODUCTS)
    total_ek = choice_for_level(ORDER_EK_VALUES_BY_LEVEL, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_vk = (total_ek / divisor).quantize(q("1.00"), rounding=ROUND_HALF_UP)
    absolute_db = total_vk - total_ek
    name = product_name(product)

    prompt = random.choice(
        [
            f"Ein Auftrag über {name} hat einen EK von {format_decimal(total_ek, 2)} Euro und einen VK von {format_decimal(total_vk, 2)} Euro.\n\nWie hoch ist der absolute DB in Euro?",
            f"Für {name} liegt ein abgeschlossener Auftrag vor: EK {format_decimal(total_ek, 2)} Euro, VK {format_decimal(total_vk, 2)} Euro.\n\nWie viel Euro Deckungsbeitrag bleiben absolut übrig?",
        ]
    )

    solution = format_solution_steps(
        (
            "Absoluter DB",
            "Absoluter DB = VK - EK",
            f"{format_decimal(total_vk, 2)} Euro - {format_decimal(total_ek, 2)} Euro = "
            f"{format_decimal(absolute_db, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": absolute_db.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "absolute_db_from_ek_vk",
        "correction": "Der absolute DB ist der Eurobetrag zwischen VK und EK.",
        "solution": solution,
        "perfect_formula": f"{format_decimal(total_vk, 2)} - {format_decimal(total_ek, 2)}",
        "guided_steps": [
            make_guided_step(
                "Absoluter DB",
                absolute_db.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Ziehe den EK vom VK ab.",
                "VK - EK",
                placeholder="Zum Beispiel 142,86 - 100",
            ),
        ],
    }


def task_relative_db_from_ek_vk(level):
    product = random.choice(PRODUCTS + FLOORING_PRODUCTS)
    total_ek = choice_for_level(ORDER_EK_VALUES_BY_LEVEL, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_vk = (total_ek / divisor).quantize(q("1.00"), rounding=ROUND_HALF_UP)
    absolute_db = total_vk - total_ek
    relative_db = ((absolute_db / total_vk) * Decimal("100")).quantize(q("1.00"), rounding=ROUND_HALF_UP)
    name = product_name(product)

    prompt = random.choice(
        [
            f"Ein Auftrag über {name} wurde mit {format_decimal(total_vk, 2)} Euro VK verkauft. Der EK liegt bei {format_decimal(total_ek, 2)} Euro.\n\nWie hoch ist der DB in Prozent?",
            f"Für {name} sind VK {format_decimal(total_vk, 2)} Euro und EK {format_decimal(total_ek, 2)} Euro bekannt.\n\nWelcher relative DB-Satz ergibt sich daraus?",
        ]
    )

    solution = format_solution_steps(
        (
            "Absoluter DB",
            "Absoluter DB = VK - EK",
            f"{format_decimal(total_vk, 2)} Euro - {format_decimal(total_ek, 2)} Euro = "
            f"{format_decimal(absolute_db, 2)} Euro",
        ),
        (
            "DB-Satz",
            "DB-Satz = absoluter DB / VK x 100",
            f"{format_decimal(absolute_db, 2)} Euro / {format_decimal(total_vk, 2)} Euro x 100 = "
            f"{format_decimal(relative_db, 2)} Prozent",
        ),
    )

    return {
        "prompt": prompt,
        "expected": relative_db,
        "unit": "Prozent",
        "display_places": 2,
        "round_for_check": True,
        "match_mode": "percent_or_factor",
        "task_type": "relative_db_from_ek_vk",
        "correction": "Berechne zuerst den absoluten DB in Euro und setze ihn danach ins Verhältnis zum VK.",
        "solution": solution,
        "perfect_formula": (
            f"({format_decimal(total_vk, 2)} - {format_decimal(total_ek, 2)}) / "
            f"{format_decimal(total_vk, 2)} * 100"
        ),
        "guided_steps": [
            make_guided_step(
                "Absoluter DB",
                absolute_db.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Ziehe zuerst den EK vom VK ab.",
                "VK - EK",
                placeholder="Zum Beispiel 142,86 - 100",
            ),
            make_guided_step(
                "DB-Satz",
                relative_db,
                "Prozent",
                2,
                True,
                "Teile den absoluten DB durch den VK und multipliziere mit 100.",
                "Absoluter DB / VK x 100",
                placeholder="Zum Beispiel 42,86 / 142,86 * 100",
                match_mode="percent_or_factor",
            ),
        ],
    }


TASK_GENERATORS = [
    task_unit_conversion,
    task_flooring_packages,
    task_volume_beam,
    task_volume_from_running_meters,
    task_volume_from_square_meters,
    task_volume_from_total_price,
    task_weight_from_volume,
    task_running_meters_from_volume,
    task_running_meters_from_square_meters,
    task_price_per_running_meter,
    task_m3_price_from_running_meter,
    task_price_per_square_meter,
    task_square_meters_from_volume,
    task_square_meters_from_running_meters,
    task_total_price_from_volume,
    task_db_sale_price,
    task_ek_from_vk_db,
    task_absolute_db_from_ek_vk,
    task_relative_db_from_ek_vk,
    task_package_price,
    task_panel_package_price,
    task_package_db_sale_price,
]

TASK_TYPE_TO_GENERATOR = {
    task_func.__name__.replace("task_", ""): task_func
    for task_func in TASK_GENERATORS
}

TASKS_BY_LEVEL = {
    1: [
        task_unit_conversion,
        task_flooring_packages,
        task_volume_beam,
        task_volume_from_running_meters,
        task_square_meters_from_running_meters,
        task_running_meters_from_volume,
        task_total_price_from_volume,
        task_volume_from_square_meters,
        task_volume_from_total_price,
        task_price_per_running_meter,
        task_price_per_square_meter,
        task_db_sale_price,
        task_absolute_db_from_ek_vk,
        task_relative_db_from_ek_vk,
        task_package_price,
        task_panel_package_price,
        task_package_db_sale_price,
    ],
    2: [
        task_unit_conversion,
        task_flooring_packages,
        task_volume_beam,
        task_volume_from_running_meters,
        task_volume_from_square_meters,
        task_volume_from_total_price,
        task_weight_from_volume,
        task_total_price_from_volume,
        task_price_per_square_meter,
        task_square_meters_from_volume,
        task_square_meters_from_running_meters,
        task_running_meters_from_volume,
        task_running_meters_from_square_meters,
        task_price_per_running_meter,
        task_db_sale_price,
        task_ek_from_vk_db,
        task_absolute_db_from_ek_vk,
        task_relative_db_from_ek_vk,
        task_package_price,
        task_panel_package_price,
        task_package_db_sale_price,
    ],
    3: TASK_GENERATORS,
}


def values_match(user_value, expected_value, round_for_check, match_mode=None):
    if match_mode == "ceil_integer":
        return round_up_to_whole(user_value) == expected_value

    if match_mode == "percent_or_factor":
        if user_value.quantize(q("1.00"), rounding=ROUND_HALF_UP) == expected_value:
            return True
        expected_factor = (expected_value / Decimal("100")).quantize(q("1.0000"), rounding=ROUND_HALF_UP)
        user_factor = user_value.quantize(q("1.0000"), rounding=ROUND_HALF_UP)
        return user_factor == expected_factor

    if round_for_check:
        return user_value.quantize(q("1.00"), rounding=ROUND_HALF_UP) == expected_value
    return user_value == expected_value


def guided_values_match(user_value, expected_value, round_for_check, current_index, unit, match_mode=None):
    if values_match(user_value, expected_value, round_for_check, match_mode):
        return True

    if unit == "EUR" and round_for_check:
        rounded_user_value = user_value.quantize(q("1.00"), rounding=ROUND_HALF_UP)
        return abs(rounded_user_value - expected_value) <= Decimal("0.01")

    if current_index == 0:
        return False

    if expected_value == 0:
        return False

    tolerance = abs(expected_value) * Decimal("0.005")
    return abs(user_value - expected_value) <= tolerance


def format_expected(task):
    return format_decimal(task["expected"], task["display_places"])


def format_value_for_task(value, task):
    return format_decimal(value, task["display_places"])


def format_user_result(value, task):
    if task.get("match_mode") == "ceil_integer":
        rounded = round_up_to_whole(value)
        if value != rounded:
            return f"{format_decimal(value, 3).rstrip('0').rstrip(',')} -> {format_decimal(rounded, 0)}"
        return format_decimal(rounded, 0)

    if task.get("match_mode") == "percent_or_factor" and abs(value) <= Decimal("1"):
        return f"{format_decimal(value, 4).rstrip('0').rstrip(',')} -> {format_decimal(value * 100, 2)}"

    if task["unit"] in {"EUR", "kg"}:
        return format_decimal(value, 2)

    if value == value.quantize(q("1"), rounding=ROUND_HALF_UP):
        return format_decimal(value, 0)

    return format_decimal(value, 4).rstrip("0").rstrip(",")


def format_value_for_step(value, step):
    if step.get("match_mode") == "ceil_integer":
        rounded = round_up_to_whole(value)
        if value != rounded:
            return f"{format_decimal(value, 3).rstrip('0').rstrip(',')} -> {format_decimal(rounded, 0)}"
        return format_decimal(rounded, 0)

    if step.get("match_mode") == "percent_or_factor" and abs(value) <= Decimal("1"):
        return f"{format_decimal(value, 4).rstrip('0').rstrip(',')} -> {format_decimal(value * 100, 2)}"

    return format_decimal(value, step["display_places"])


def is_direct_result_input(text):
    cleaned = text.strip().replace(" ", "")
    return bool(re.fullmatch(r"[+-]?\d+(?:[,.]\d+)?", cleaned))


def default_step_placeholder(step):
    label = step["label"].lower()
    unit = step["unit"]

    if "db-faktor" in label:
        return "Zum Beispiel 1 - 0,23"
    if "querschnitt" in label or "breite x höhe" in label:
        return "Zum Beispiel 0,16 * 0,019"
    if "preis je laufmeter" in label:
        return "Zum Beispiel 0,00304 * 350"
    if "preis pro quadratmeter" in label or "preis je quadratmeter" in label:
        return "Zum Beispiel 560 * 0,05"
    if "preis pro kubikmeter" in label:
        return "Zum Beispiel 6,20 / 0,00304"
    if "fläche pro stück" in label:
        return "Zum Beispiel 2 * 0,20"
    if "paketfläche" in label:
        return "Zum Beispiel 0,40 * 7"
    if "pakete" in label:
        return "Zum Beispiel 100 / 2,80"
    if "gewicht" in label:
        return "Zum Beispiel 1,250 * 620"
    if "absoluter db" in label:
        return "Zum Beispiel 142,86 - 100"
    if "db-satz" in label or "relativer db" in label:
        return "Zum Beispiel 42,86 / 142,86 * 100"
    if "volumen pro" in label:
        return "Zum Beispiel 5 * 0,12 * 0,12"
    if "paketvolumen" in label:
        return "Zum Beispiel 0,072 * 40"
    if "gesamtvolumen" in label:
        return "Zum Beispiel 0,072 * 8"
    if "paket-vk" in label or "vk" in label:
        return "Zum Beispiel 1008 / 0,77"
    if "paket-ek" in label or "paketpreis" in label or "gesamtpreis" in label:
        return "Zum Beispiel 2,88 * 350"
    if "laufmeter" in label:
        return "Zum Beispiel 0,36 / 0,012"
    if "quadratmeter" in label:
        return "Zum Beispiel 1,35 / 0,025"
    if unit == "EUR":
        return "Zum Beispiel 0,00304 * 350"
    if unit == "m3":
        return "Zum Beispiel 6 * 0,08 * 0,12"
    if unit == "m2":
        return "Zum Beispiel 1,35 / 0,025"
    if unit == "lfm":
        return "Zum Beispiel 0,36 / 0,012"
    return "Zum Beispiel 0,96 * 350"


def step_placeholder(step):
    return step.get("placeholder") or default_step_placeholder(step)


def clean_formula_expression(expression):
    expression = re.sub(r"^Berechnung:\s*", "", expression)
    cleaned = re.sub(
        r"\b(Meter|Kubikmeter|Quadratmeter|Laufmeter|Euro|Stück|Pakete|Prozent|pro|DB|bei)\b",
        "",
        expression,
    )
    cleaned = cleaned.replace("%", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\(\s+", "(", cleaned)
    cleaned = re.sub(r"\s+\)", ")", cleaned)
    return cleaned.strip()


def perfect_input_formula(task):
    if task.get("perfect_formula"):
        return task["perfect_formula"]

    for line in reversed(solution_lines(task)):
        if " = " not in line or "Formel:" in line:
            continue
        parts = line.split(" = ")
        if len(parts) >= 3:
            return clean_formula_expression(parts[-2])
        if len(parts) == 2:
            return clean_formula_expression(parts[0])

    return ""


def render_musterloesung(task):
    st.subheader("Musterlösung")
    formula = perfect_input_formula(task)
    if formula:
        st.write("Das kannst du in den Taschenrechner eingeben, um direkt zum richtigen Ergebnis zu kommen:")
        st.code(formula)
    st.write("Rechenweg mit Einheiten:")
    st.code(task["solution"])


def render_theory_section():
    st.markdown("#### Einheiten")
    st.write(
        "Einheiten sind die Grundlage für jede saubere Rechnung. Besonders bei Zentimeter, Millimeter und Meter "
        "entstehen schnell Faktor-10-, Faktor-100- oder Faktor-1000-Fehler."
    )
    st.markdown(
        """
| Richtung | Regel | Beispiel |
| --- | --- | --- |
| Meter zu Zentimeter | mal 100 | 5 Meter = 500 Zentimeter |
| Meter zu Millimeter | mal 1000 | 5 Meter = 5000 Millimeter |
| Zentimeter zu Meter | geteilt durch 100 | 500 Zentimeter = 5 Meter |
| Zentimeter zu Millimeter | mal 10 | 12 Zentimeter = 120 Millimeter |
| Millimeter zu Zentimeter | geteilt durch 10 | 40 Millimeter = 4 Zentimeter |
| Millimeter zu Meter | geteilt durch 1000 | 40 Millimeter = 0,04 Meter |
"""
    )
    st.write("Merksatz: Wenn die Einheit größer wird, wird die Zahl kleiner. Wenn die Einheit kleiner wird, wird die Zahl größer.")

    st.markdown("#### Volumen und Mengen")
    st.write(
        "Volumen und Mengen brauchst du, um Ware fachlich vergleichbar zu machen. Je nach Produkt wird in Laufmetern, "
        "Quadratmetern, Kubikmetern, Stück oder ganzen Paketen gedacht."
    )
    st.markdown(
        """
| Von | Nach | Rechenweg |
| --- | --- | --- |
| Laufmeter | Quadratmeter | Laufmeter x Breite |
| Quadratmeter | Laufmeter | Quadratmeter / Breite |
| Quadratmeter | Kubikmeter | Quadratmeter x Dicke |
| Kubikmeter | Quadratmeter | Kubikmeter / Dicke |
| Laufmeter | Kubikmeter | Laufmeter x Breite x Höhe |
| Kubikmeter | Laufmeter | Kubikmeter / (Breite x Höhe) |
| Bodenstück | Quadratmeter pro Stück | Länge x Breite |
| Bodenpaket | Quadratmeter pro Paket | Quadratmeter pro Stück x Stückzahl im Paket |
| Bedarf | Pakete | Bedarf / Paketfläche, danach auf volle Pakete aufrunden |
"""
    )

    st.markdown("#### Dichte und Gewicht")
    st.write(
        "Die Dichte brauchst du, wenn aus einem Volumen ein Gewicht werden soll, zum Beispiel für Transport, Handling "
        "oder eine Plausibilitätskontrolle. Gerechnet wird ähnlich wie beim Preis pro Kubikmeter: Statt Euro pro Kubikmeter "
        "verwendest du Kilogramm pro Kubikmeter."
    )
    st.markdown(
        """
| Gesucht | Rechenweg | Beispiel |
| --- | --- | --- |
| Gewicht | Kubikmeter x Dichte | 1,250 Kubikmeter x 620 Kilogramm pro Kubikmeter |
| Dichte | Gewicht / Kubikmeter | 775 Kilogramm / 1,250 Kubikmeter |
"""
    )

    st.markdown("#### Preise")
    st.write(
        "Preise hängen immer an einer Einheit. Darum ist entscheidend, ob ein Preis pro Laufmeter, Quadratmeter "
        "oder Kubikmeter gemeint ist, bevor du multiplizierst oder teilst."
    )
    st.markdown(
        """
| Von | Nach | Rechenweg |
| --- | --- | --- |
| Euro pro Laufmeter | Euro pro Quadratmeter | Euro pro Laufmeter / Breite |
| Euro pro Quadratmeter | Euro pro Laufmeter | Euro pro Quadratmeter x Breite |
| Euro pro Quadratmeter | Euro pro Kubikmeter | Euro pro Quadratmeter / Dicke |
| Euro pro Kubikmeter | Euro pro Quadratmeter | Euro pro Kubikmeter x Dicke |
| Euro pro Laufmeter | Euro pro Kubikmeter | Euro pro Laufmeter / (Breite x Höhe) |
| Euro pro Kubikmeter | Euro pro Laufmeter | Euro pro Kubikmeter x Breite x Höhe |
"""
    )

    st.markdown("#### Deckungsbeitrag")
    st.write(
        "Der Deckungsbeitrag zeigt, was vom Verkaufspreis nach Abzug des Einkaufspreises übrig bleibt. "
        "Absolut ist das ein Eurobetrag, relativ ein Prozentwert bezogen auf den Verkaufspreis. "
        "Der Gesamt-DB ist die Summe dieser Eurobeträge über mehrere Positionen oder einen Auftrag hinweg; im Handel wird das oft als Rohertrag betrachtet."
    )
    st.write(
        "Ein durchschnittlicher Holzhandel braucht grob etwa 24 Prozent Deckungsbeitrag, damit aus dem Rohertrag die laufenden Kosten bezahlt werden können. "
        "Der Wareneinsatz ist im EK schon enthalten; vom DB müssen dann zum Beispiel Personal, Lager, Miete, Energie, Fuhrpark, Sprit, Verwaltung, IT, Finanzierung, Schwund und Risiko getragen werden."
    )
    st.markdown(
        """
| Gesucht | Rechenweg | Beispiel |
| --- | --- | --- |
| absoluter DB | DB in Euro = VK - EK | 142,86 Euro - 100 Euro |
| relativer DB | DB in Prozent = DB in Euro / VK x 100 | 42,86 Euro / 142,86 Euro x 100 |
| VK aus EK und DB | VK = EK / (1 - DB-Satz) | 100 Euro / 0,70 bei 30 Prozent DB |
| EK aus VK und DB | EK = VK x (1 - DB-Satz) | 142,86 Euro x 0,70 bei 30 Prozent DB |
"""
    )
    st.write("Bei 30 Prozent DB bleiben 70 Prozent als Kostenanteil übrig. Darum wird beim VK durch 0,70 geteilt.")


def guided_completed_entry(text, kind="success"):
    return {
        "text": text,
        "kind": kind,
    }


def render_guided_resolved_entry(entry):
    next_step = entry.get("next_step_label", "")
    next_text = f"<div class='resolved-next'>Als Nächstes: {escape(next_step)}.</div>" if next_step else ""
    message = entry.get("message", "").strip()
    message_html = f"<div class='resolved-message'>{escape(message)}</div>" if message else ""
    result_label = "Weiterrechnen kannst du mit" if next_step else "Das Ergebnis ist"
    formula = entry.get("formula", "").strip()
    calculation = entry.get("calculation", "").strip()
    formula_html = ""
    if formula or calculation:
        formula_lines = ["<div class='resolved-formula'>"]
        formula_lines.append("<div class='resolved-formula-title'>So entsteht der grüne Wert:</div>")
        if formula:
            formula_lines.append(f"<div>Formel: <span class='resolved-formula-text'>{escape(formula)}</span></div>")
        if calculation:
            formula_lines.append(f"<div>Berechnung: <span class='resolved-good'>{escape(calculation)}</span></div>")
        formula_lines.append("</div>")
        formula_html = "\n".join(formula_lines)

    st.markdown(
        f"""
<div class="resolved-step-box">
    <div class="resolved-title">{escape(entry.get("label", "Zwischenschritt"))} wurde aufgelöst</div>
    <div>Deine Eingabe <span class="resolved-bad">{escape(entry.get("raw_value", ""))}</span> ergab <span class="resolved-bad">{escape(entry.get("user_result", ""))}</span>.</div>
    {formula_html}
    {message_html}
    <div>{result_label} <span class="resolved-good">{escape(entry.get("correct_result", ""))}</span>.</div>
    {next_text}
</div>
""",
        unsafe_allow_html=True,
    )


def render_guided_completed_entry(entry):
    if isinstance(entry, dict):
        text = entry.get("text", "")
        kind = entry.get("kind", "success")
    else:
        text = str(entry)
        kind = "success"

    if kind == "resolved":
        render_guided_resolved_entry(entry)
        return
    if kind == "warning":
        st.warning(text)
    else:
        st.success(text)


def render_guided_summary():
    text = st.session_state.get("guided_summary", "")
    if not text:
        return

    kind = st.session_state.get("guided_summary_kind", "warning")
    if kind == "success":
        st.success(text)
    elif kind == "error":
        st.error(text)
    else:
        st.warning(text)


def guided_has_warning():
    for entry in st.session_state.get("guided_completed", []):
        if isinstance(entry, dict) and entry.get("kind") in {"warning", "resolved"}:
            return True
    return False


def is_close_factor(value, target):
    tolerance = abs(target) * Decimal("0.03")
    return abs(value - target) <= tolerance


def diagnose_common_mistake(task, answer_value, expected_value):
    if expected_value == 0:
        return ""

    try:
        ratio = (answer_value / expected_value).copy_abs()
    except (InvalidOperation, ZeroDivisionError):
        return ""

    if task["task_type"] == "price_per_square_meter":
        if is_close_factor(ratio, Decimal("10")):
            return (
                "Dein Ergebnis ist ungefähr zehnmal so hoch wie die richtige Lösung. "
                "Das sieht stark danach aus, dass die Dicke in Zentimetern nicht sauber in Meter umgerechnet wurde, "
                "zum Beispiel 5 cm als 0,5 m statt 0,05 m."
            )
        if is_close_factor(ratio, Decimal("100")):
            return (
                "Dein Ergebnis ist ungefähr hundertmal so hoch wie die richtige Lösung. "
                "Prüfe die Umrechnung der Dicke sehr genau. Hier liegt sehr wahrscheinlich ein Fehler beim Sprung von Zentimeter oder Millimeter auf Meter vor."
            )

    if task["task_type"] == "unit_conversion":
        if is_close_factor(ratio, Decimal("10")) or is_close_factor(ratio, Decimal("100")) or is_close_factor(ratio, Decimal("1000")):
            return (
                "Dein Ergebnis liegt um einen typischen Einheitenfaktor daneben. "
                "Prüfe, ob du zwischen Millimeter, Zentimeter und Meter multiplizieren oder teilen musst."
            )

    if task["task_type"] in {
        "square_meters_from_volume",
        "volume_from_square_meters",
        "volume_from_running_meters",
        "running_meters_from_volume",
        "square_meters_from_running_meters",
        "running_meters_from_square_meters",
        "volume_beam",
    }:
        if is_close_factor(ratio, Decimal("10")) or is_close_factor(ratio, Decimal("100")) or is_close_factor(ratio, Decimal("1000")):
            return (
                "Dein Ergebnis weicht ungefähr um den Faktor 10, 100 oder 1000 ab. "
                "Das spricht oft für einen Fehler bei der Umrechnung von Millimeter, Zentimeter und Meter."
            )

    if task["task_type"] in {"price_per_running_meter", "m3_price_from_running_meter", "total_price_from_volume", "volume_from_total_price"}:
        if is_close_factor(ratio, Decimal("10")) or is_close_factor(ratio, Decimal("100")):
            return (
                "Dein Ergebnis liegt grob um einen glatten Faktor daneben. "
                "Prüfe deshalb zuerst die Einheit der Eingangsgröße und danach, ob du multiplizieren oder teilen musst."
            )

    if task["task_type"] == "flooring_packages":
        if answer_value < expected_value:
            return (
                "Bei Bodenpaketen darfst du nicht abrunden. "
                "Wenn eine Kommazahl an Paketen herauskommt, muss auf das nächste volle Paket aufgerundet werden."
            )

    if task["task_type"] in {"absolute_db_from_ek_vk", "relative_db_from_ek_vk"}:
        return (
            "Beim DB gehst du zuerst vom Unterschied zwischen VK und EK aus. "
            "Für den Prozentwert wird dieser Unterschied anschließend durch den VK geteilt."
        )

    if task["task_type"] == "weight_from_volume":
        return (
            "Beim Gewicht wird nicht mit einem Preis gerechnet, sondern mit der Dichte. "
            "Prüfe, ob du das Volumen in Kubikmeter mit Kilogramm pro Kubikmeter weitergerechnet hast."
        )

    return ""


def diagnose_step_mistake(task, step, answer_value):
    message = diagnose_common_mistake(task, answer_value, step["expected"])
    if message:
        return message

    try:
        ratio = (answer_value / step["expected"]).copy_abs()
    except (InvalidOperation, ZeroDivisionError):
        return ""

    if step["unit"] == "m3" and (is_close_factor(ratio, Decimal("10")) or is_close_factor(ratio, Decimal("100"))):
        return (
            "Dein Ergebnis liegt ungefähr um einen typischen Umrechnungsfaktor daneben. "
            "Prüfe noch einmal, ob Breite, Höhe oder Dicke wirklich in Meter eingesetzt wurden."
        )
    return ""


def likely_error_focus(task):
    focus = {
        "volume_beam": "Achte besonders auf vollständige Maße, auf die Stückzahl und auf die Volumenlogik.",
        "unit_conversion": "Achte besonders auf den Einheitenfaktor zwischen Millimeter, Zentimeter und Meter.",
        "price_per_running_meter": "Achte besonders auf Querschnitt, Volumen von 1 Laufmeter und die richtige Preisbasis.",
        "price_per_square_meter": "Achte besonders auf die Dicke der Platte und auf die Preisbasis pro Kubikmeter.",
        "square_meters_from_volume": "Achte besonders auf die Richtung der Umrechnung zwischen Kubikmeter und Quadratmeter.",
        "volume_from_square_meters": "Achte besonders auf die Richtung der Umrechnung von Quadratmeter zu Kubikmeter über die Dicke.",
        "total_price_from_volume": "Achte besonders darauf, ob Volumen und Preisbasis wirklich zur Zielgröße Gesamtpreis passen.",
        "running_meters_from_volume": "Achte besonders auf die Richtung Kubikmeter zu Laufmeter sowie auf Breite und Stärke in Meter.",
        "square_meters_from_running_meters": "Achte besonders auf die Richtung Laufmeter zu Quadratmeter über die Breite der Hobelware.",
        "running_meters_from_square_meters": "Achte besonders auf die Richtung Quadratmeter zu Laufmeter über die Breite der Hobelware.",
        "db_sale_price": "Achte besonders auf die Reihenfolge Einzelvolumen, Gesamtvolumen, EK und danach VK mit DB.",
        "package_db_sale_price": "Achte besonders auf die Reihenfolge Einzelvolumen, Paketvolumen, Paket-EK und VK mit DB.",
        "volume_from_running_meters": "Achte besonders auf Querschnitt mal Laufmeter und auf vollständige Maße.",
        "volume_from_total_price": "Achte besonders auf die richtige Richtung Preis zu Volumen, also teilen statt multiplizieren.",
        "weight_from_volume": "Achte besonders darauf, dass die Dichte ein Faktor pro Kubikmeter ist.",
        "m3_price_from_running_meter": "Achte besonders auf die richtige Preisbasis, auf Breite x Stärke in Meter und auf Teilen statt Multiplizieren.",
        "ek_from_vk_db": "Achte besonders auf die Rückwärtsrechnung vom VK über den DB-Faktor zum EK.",
        "package_price": "Achte besonders auf die Reihenfolge Einzelvolumen, Paketvolumen und Paketpreis.",
        "panel_package_price": "Achte besonders auf Fläche pro Platte, Paketfläche und Paketpreis über den Quadratmeterpreis.",
        "flooring_packages": "Achte besonders auf Fläche pro Stück, Paketfläche und das Aufrunden auf volle Pakete.",
        "absolute_db_from_ek_vk": "Achte besonders darauf, dass der absolute DB einfach die Differenz zwischen VK und EK ist.",
        "relative_db_from_ek_vk": "Achte besonders darauf, den absoluten DB ins Verhältnis zum VK zu setzen.",
    }
    return focus.get(task["task_type"], "Achte besonders auf die passende Einheit, die Rechenrichtung und die Preisbasis.")


def progressive_main_hint(task, answer_value, attempt):
    if attempt <= 1:
        return generate_hint(task, answer_value, False, attempt)
    if attempt == 2:
        first_step = task.get("guided_steps", [{}])[0]
        return f"{generate_hint(task, answer_value, False, attempt)} {first_step.get('formula_hint', '')}".strip()
    return "Wenn du magst, geh die Aufgabe jetzt Schritt für Schritt durch. So lässt sich der Rechenweg sauber aufbauen."


def progressive_step_hint(task, step, answer_value, step_attempt):
    diagnostic = diagnose_step_mistake(task, step, answer_value)
    if diagnostic:
        if step_attempt <= 1:
            return diagnostic
        return f"{diagnostic} {step['formula_hint']}"
    if step_attempt <= 1:
        return step["correction"]
    if step_attempt == 2:
        return f"{step['correction']} {step['formula_hint']}"
    return (
        f"{step['formula_hint']}. "
        f"Achte danach noch einmal genau auf die Richtung der Rechnung und auf die richtige Einheit."
    )


def fallback_guided_error_hint(task, step, raw_value, answer_value, step_attempt):
    diagnostic = diagnose_step_mistake(task, step, answer_value)
    user_result = f"{format_value_for_step(answer_value, step)} {unit_label(step['unit'])}"
    correct_result = f"{format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}"
    base = f"Deine Eingabe {raw_value} ergibt {user_result}. "

    if step_attempt <= 1:
        if diagnostic:
            return f"{base}{diagnostic} Bleib bei diesem Zwischenschritt und prüfe erst die Einheit, bevor du weiterrechnest."
        return f"{base}{step['correction']} Versuche den Schritt noch einmal isoliert, ohne schon den nächsten Schritt mitzunehmen."

    base = f"{base}Für {step['label']} sollte hier {correct_result} herauskommen."

    if diagnostic:
        return f"{base} {diagnostic} Bleib bei diesem Zwischenschritt und prüfe erst die Einheit, bevor du weiterrechnest."
    return f"{base} {step['formula_hint']} Setze nur die Werte ein, die zu diesem Zwischenschritt gehören."


def generate_guided_error_hint(task, step, raw_value, answer_value, step_attempt):
    local_step_diagnostic = diagnose_step_mistake(task, step, answer_value) or step["correction"]
    correct_value_context = (
        f"Richtiger Wert für diesen Schritt: {format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}. "
        if step_attempt >= 2
        else "Richtiger Wert für diesen Schritt: nicht in diesem Tipp nennen und keine konkrete Zielzahl ausgeben. "
    )
    prompt = (
        "Du bist ein Lernassistent für den Holzhandel. "
        "Ein einzelner Zwischenschritt wurde falsch gelöst. "
        "Antworte auf Deutsch, kurz und konkret, in maximal 5 Sätzen. "
        "Nutze die Angaben zur Diagnose, aber verrate im Tipp nicht den konkreten richtigen Zielwert. "
        "Nenne keine richtige Zahl, keine fertige Teilrechnung und kein Ergebnis, solange der Zwischenschritt noch nicht automatisch aufgelöst wurde. "
        "Erkläre den wahrscheinlichsten Fehler mit etwas Kontext und nenne nur den nächsten kleinen Korrekturgedanken. "
        "Beim ersten falschen Versuch bleibst du eher allgemein und gibst nur eine Orientierung. "
        "Beim zweiten falschen Versuch wird der Zwischenschritt automatisch aufgelöst; dafür brauchst du hier keine Musterlösung zu schreiben. "
        "Denke aktiv darüber nach, ob eine Maßeinheit fehlt, ein unnötiger Faktor verwendet wurde, ein nötiger Faktor fehlt, oder ob Multiplikation und Division verwechselt wurden. "
        "Übernimm die lokale Vorprüfung nicht blind, sondern bewerte Aufgabe, Zwischenschritt, Eingabe und richtigen Wert zusammen. "
        "Verrate nicht den vollständigen restlichen Lösungsweg. "
        "Keine lange Musterlösung, kein Bezug auf vorherige Hinweise. "
        f"Aufgabe: {task['prompt']} "
        f"Zwischenschritt: {step['label']}. "
        f"Eingabe des Nutzers: {raw_value}. "
        f"Berechneter Wert der Eingabe: {format_value_for_step(answer_value, step)} {unit_label(step['unit'])}. "
        f"{correct_value_context}"
        f"Versuch im Zwischenschritt: {step_attempt} von 2. "
        f"Mögliche Fehlerursache aus lokaler Vorprüfung: {local_step_diagnostic} "
        f"Fachlicher Hinweis: {step['formula_hint']}"
    )

    try:
        if not get_openai_api_key():
            return fallback_guided_error_hint(task, step, raw_value, answer_value, step_attempt)

        text = call_openai_responses_api(prompt, 200)
        if text:
            return text
    except Exception:
        pass

    return fallback_guided_error_hint(task, step, raw_value, answer_value, step_attempt)


def auto_resolve_guided_step(task, step, raw_value, answer_value, message="", next_step=None):
    solution_block = solution_block_for_label(task, step["label"])
    return {
        "kind": "resolved",
        "label": step["label"],
        "raw_value": raw_value,
        "user_result": f"{format_value_for_step(answer_value, step)} {unit_label(step['unit'])}",
        "correct_result": f"{format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}",
        "formula": solution_block.get("formula", step.get("formula_hint", "")),
        "calculation": solution_block.get("calculation", ""),
        "message": message,
        "next_step_label": next_step["label"] if next_step else "",
    }


def resolved_step_message(step, next_step=None):
    if next_step:
        return (
            "Ich habe diesen Zwischenschritt jetzt für dich gelöst. "
            "Schau dir vor allem die Berechnung zum grünen Wert an: Dort siehst du, welche Maße und Faktoren in genau diesem Schritt gebraucht werden. "
            f"Diesen grünen Wert nutzt du anschließend für {next_step['label']}."
        )
    return (
        "Ich habe diesen letzten Zwischenschritt jetzt für dich gelöst. "
        "Schau dir vor allem die Berechnung zum grünen Wert an und prüfe, welche Einheit oder Rechenrichtung dich aus dem Tritt gebracht hat. "
        "Danach kannst du den vollständigen Rechenweg in Ruhe ansehen."
    )


def fallback_hint(task, is_correct):
    if is_correct:
        return "Ergebnis ist korrekt. Du kannst dir bei Bedarf noch die Musterlösung ansehen oder direkt zur nächsten Aufgabe weitergehen."
    diagnostic = st.session_state.get("last_diagnostic_hint", "")
    base = f"{diagnostic} {task['correction']}".strip()
    return f"{base} Prüfe danach noch einmal, ob die gegebene Einheit wirklich zur gesuchten Einheit passt.".strip()


def generate_hint(task, answer_value, is_correct, attempt=None):
    local_diagnostic = diagnose_common_mistake(task, answer_value, task["expected"])
    attempt_text = f"{attempt} von 2" if attempt else "nicht angegeben"
    correct_solution_context = (
        f"Korrekte Lösung: {format_expected(task)} {unit_label(task['unit'])}. "
        if is_correct
        else "Korrekte Lösung: im Tipp nicht nennen und keine konkrete Zielzahl ausgeben. "
    )
    error_context = (
        "Keine Fehleranalyse nötig; die Antwort passt."
        if is_correct
        else local_diagnostic or likely_error_focus(task)
    )
    prompt = (
        "Du bist ein Lernassistent für den Holzhandel. "
        "Antworte auf Deutsch kurz und konkret in maximal 5 Sätzen. "
        "Wenn die Antwort richtig ist, schreibe sinngemäß 'Ergebnis ist korrekt' und gib einen kurzen nächsten Orientierungssatz. "
        "Wenn die Antwort falsch ist, nenne den wahrscheinlichsten Fehler etwas spezifischer und genau den nächsten Rechenschritt. "
        "Passe die Hilfe an den Versuch an: Beim ersten falschen Versuch nur leicht anstoßen; beim zweiten falschen Versuch wird in die Zwischenschritte gewechselt. "
        "Nenne keine vollständige Musterlösung und rechne die Lösung nicht aus. "
        "Wenn die Antwort falsch ist, verrate nicht die korrekte Zielzahl. "
        "Denke aktiv darüber nach, ob eine Maßeinheit fehlt, ein unnötiger Faktor verwendet wurde, ein nötiger Faktor fehlt, oder ob Multiplikation und Division verwechselt wurden. "
        "Übernimm die lokale Vorprüfung nicht blind, sondern bewerte Aufgabe, Nutzereingabe und korrekte Lösung zusammen. "
        "Schreibe nicht 'fachlich korrekt'. "
        "Keine Floskeln, keine lange Musterlösung. "
        f"Aufgabe: {task['prompt']} "
        f"Versuch in der Aufgabe: {attempt_text}. "
        f"Antwort des Nutzers: {format_user_result(answer_value, task)} {unit_label(task['unit'])}. "
        f"{correct_solution_context}"
        f"Mögliche Fehlerursache aus lokaler Vorprüfung: {error_context} "
        f"Zusatzhinweis: {task['correction']}"
    )

    try:
        if not get_openai_api_key():
            st.session_state.hint_backend = "fallback_no_key"
            st.session_state.hint_backend_error = ""
            return fallback_hint(task, is_correct)

        text = call_openai_responses_api(prompt, 190)
        if text:
            st.session_state.hint_backend = "api_rest"
            st.session_state.hint_backend_error = ""
            return text
        st.session_state.hint_backend = "fallback_empty_response"
        st.session_state.hint_backend_error = ""
        return fallback_hint(task, is_correct)
    except Exception:
        st.session_state.hint_backend = "fallback_exception"
        st.session_state.hint_backend_error = ""
        return fallback_hint(task, is_correct)


def fallback_guided_transition(completed_step, completed_value, next_step):
    return (
        f"Als Nächstes: {next_step['label']}. "
        f"Nutze {completed_step['label']} = {format_value_for_step(completed_value, completed_step)} "
        f"{unit_label(completed_step['unit'])}. "
        f"{ensure_sentence(next_step['formula_hint'])} So bleibt der Rechenweg sauber Schritt für Schritt aufgebaut."
    )


def generate_guided_transition_hint(task, completed_step, completed_value, next_step):
    prompt = (
        "Du bist ein Lernassistent für den Holzhandel. "
        "Ein Zwischenschritt wurde richtig gelöst. "
        "Antworte auf Deutsch in maximal 3 kurzen Sätzen. "
        f"Beginne mit dem nächsten Schritt, also: 'Als Nächstes: {next_step['label']}.' "
        "Nenne danach das Zwischenergebnis mit Einheit und erkläre konkret, wie damit im nächsten Schritt weitergerechnet wird. "
        "Gib einen kurzen Kontext, warum genau dieser nächste Schritt folgt. "
        "Wenn im Muster-Rechenweg eine konkrete Zahl für den nächsten Faktor vorkommt, nenne sie. "
        f"Aufgabe: {task['prompt']} "
        f"Richtiger Zwischenschritt: {completed_step['label']} = "
        f"{format_value_for_step(completed_value, completed_step)} {unit_label(completed_step['unit'])}. "
        f"Nächster Schritt: {next_step['label']}. "
        f"Nächste Formel: {next_step['formula_hint']} "
        f"Muster-Rechenweg: {' '.join(solution_lines(task))}"
    )

    try:
        if not get_openai_api_key():
            return fallback_guided_transition(completed_step, completed_value, next_step)

        text = call_openai_responses_api(prompt, 130)
        if text:
            return ensure_sentence(text)
    except Exception:
        pass

    return fallback_guided_transition(completed_step, completed_value, next_step)


def solution_lines(task):
    return [line for line in task["solution"].splitlines() if line and line != "Rechenweg:"]


def solution_block_for_label(task, label):
    lines = solution_lines(task)
    for index, line in enumerate(lines):
        match = re.match(r"^\d+\.\s+(.+)$", line)
        if not match or match.group(1).strip() != label:
            continue

        block_lines = []
        for block_line in lines[index + 1:]:
            if re.match(r"^\d+\.\s+.+$", block_line):
                break
            block_lines.append(block_line)

        formula = ""
        calculation = ""
        for block_line in block_lines:
            if block_line.startswith("Formel:"):
                formula = block_line.replace("Formel:", "", 1).strip()
            elif block_line.startswith("Berechnung:"):
                calculation = block_line.replace("Berechnung:", "", 1).strip()

        return {"formula": formula, "calculation": calculation}

    return {}


def normalize_explanation_question(text):
    stripped = text.strip()
    if not stripped:
        raise ValueError

    if re.fullmatch(r"[\d,\s;]+", stripped):
        numbers = []
        for part in stripped.replace(";", ",").split(","):
            piece = part.strip()
            if not piece:
                continue
            if piece.isdigit():
                numbers.append(piece)
        if numbers:
            if len(numbers) == 1:
                return f"Bitte erkläre mir Schritt {numbers[0]} genauer."
            return f"Bitte erkläre mir die Schritte {', '.join(numbers)} genauer."

    return stripped


def fallback_step_explanation(task, question_text):
    lines = solution_lines(task)
    joined = " ".join(lines)
    lower_question = question_text.lower()

    if ("db" in lower_question or "0,75" in lower_question or "25" in lower_question) and "VK bei" in joined:
        match = re.search(r"(\d+(?:,\d+)?) % DB = (\d+(?:,\d+)?) Euro / (\d+(?:,\d+)?)", joined)
        if match:
            db_percent, ek_value, factor_value = match.groups()
            rest_percent = format_decimal(Decimal("100") - Decimal(db_percent.replace(",", ".")), 0)
            return (
                f"Hier wird zuerst aus dem DB-Satz der passende Faktor gemacht. "
                f"Du nimmst 100 Prozent und ziehst {db_percent} Prozent DB ab. "
                f"Dann bleiben {rest_percent} Prozent übrig, also als Dezimalzahl {factor_value}. "
                f"Mit genau diesem Faktor rechnest du weiter: {ek_value} Euro geteilt durch {factor_value} ergibt {format_expected(task)} {unit_label(task['unit'])}."
            )

    if task["task_type"] == "flooring_packages":
        return (
            "Bei Bodenpaketen zählt zuerst die Fläche eines einzelnen Stücks: Länge mal Breite. "
            "Diese Fläche wird mit der Stückzahl im Paket multipliziert, dadurch erhältst du die Quadratmeter pro Paket. "
            "Am Ende teilst du den Bedarf durch die Paketfläche und rundest auf, weil man keine halben Pakete verkaufen kann."
        )

    if task["task_type"] == "relative_db_from_ek_vk":
        return (
            "Für den relativen DB brauchst du zuerst den absoluten DB: VK minus EK. "
            "Dieser Eurobetrag wird dann durch den VK geteilt, weil der DB-Satz immer im Verhältnis zum Verkaufspreis betrachtet wird. "
            "Mit mal 100 machst du daraus den Prozentwert."
        )

    if task["task_type"] == "absolute_db_from_ek_vk":
        return (
            "Der absolute DB ist der Betrag, der zwischen Verkaufspreis und Einkaufspreis liegt. "
            "Du ziehst also einfach den EK vom VK ab. "
            "Das Ergebnis bleibt ein Eurobetrag, noch kein Prozentwert."
        )

    if task["task_type"] == "weight_from_volume":
        return (
            "Bei der Gewichtsrechnung wird das Volumen mit der Dichte verknüpft. "
            "Die Dichte sagt, wie viele Kilogramm ein Kubikmeter ungefähr wiegt. "
            "Darum wird das Volumen in Kubikmeter mit Kilogramm pro Kubikmeter multipliziert."
        )

    if "Kubikmeter = Quadratmeter x Dicke" in joined and (
        "geteilt" in lower_question
        or "durch" in lower_question
        or "/" in lower_question
        or ":" in lower_question
    ):
        match = re.search(
            r"Berechnung: (\d+(?:,\d+)?) Quadratmeter x (\d+(?:,\d+)?) Meter = (\d+(?:,\d+)?) Kubikmeter",
            joined,
        )
        if match:
            area_value, thickness_value, volume_value = match.groups()
            return (
                f"Hier wird nicht durch {thickness_value} Meter geteilt, weil du von einer Fläche zu einem Volumen gehst. "
                f"Die {area_value} Quadratmeter sind nur die Fläche; mit der Dicke {thickness_value} Meter gibst du dieser Fläche die dritte Dimension. "
                f"Darum rechnest du {area_value} Quadratmeter x {thickness_value} Meter und kommst auf {volume_value} Kubikmeter. "
                "Teilen durch die Dicke wäre die Gegenrichtung: Dann hättest du Kubikmeter gegeben und würdest daraus Quadratmeter zurückrechnen."
            )
        return (
            "Hier wird nicht durch die Dicke geteilt, weil du von Quadratmetern zu Kubikmetern gehst. "
            "Quadratmeter beschreiben nur die Fläche; die Dicke kommt als dritte Dimension dazu. "
            "Darum wird Fläche mal Dicke gerechnet. "
            "Geteilt durch die Dicke würdest du nur rechnen, wenn Kubikmeter gegeben wären und Quadratmeter gesucht sind."
        )

    if ("dicke" in lower_question or "quadratmeter" in lower_question or "0,018" in lower_question or "0,022" in lower_question or "0,023" in lower_question or "0,025" in lower_question) and "Euro pro Quadratmeter = Euro pro Kubikmeter x Dicke" in joined:
        return (
            "Stell dir einen Kubikmeter Plattenware vor. Ein Quadratmeter dieser Platte hat nur die Dicke als dritte Dimension. "
            "Deshalb brauchst du genau die Dicke in Meter, um vom Preis pro Kubikmeter auf den Preis pro Quadratmeter zu kommen. "
            "Du nimmst also den Preis pro Kubikmeter und multiplizierst ihn mit der Dicke der Platte."
        )

    if ("laufmeter" in lower_question or "breite" in lower_question or "höhe" in lower_question) and "Laufmeter = Kubikmeter / (Breite x Höhe)" in joined:
        return (
            "Hier suchst du die Länge, die in einem gegebenen Volumen steckt. "
            "Breite mal Höhe beschreibt den Querschnitt der Ware. Wenn du das Volumen durch diesen Querschnitt teilst, "
            "bleibt als Ergebnis die Länge in Laufmetern übrig."
        )

    if ("kubikmeter" in lower_question or "laufmeter" in lower_question) and "Kubikmeter = Laufmeter x Breite x Höhe" in joined:
        return (
            "Hier wird aus einer Länge wieder ein Volumen aufgebaut. "
            "Du hast die Laufmeter als Länge und multiplizierst sie mit Breite und Höhe in Meter. "
            "So entsteht direkt das Volumen in Kubikmetern."
        )

    if ("preis" in lower_question or "kubikmeter" in lower_question or "laufmeter" in lower_question) and "Euro pro Kubikmeter = Euro pro Laufmeter / (Breite x Höhe)" in joined:
        return (
            "Hier gehst du vom Preis pro Laufmeter zurück auf den Preis pro Kubikmeter. "
            "Breite mal Höhe beschreibt, wie viel Kubikmeter in einem Laufmeter stecken. "
            "Deshalb wird der Laufmeterpreis durch Breite mal Höhe geteilt."
        )

    return (
        f"Schau dir diesen Rechenweg noch einmal in Ruhe an: {joined} "
        f"Wichtig ist hier zuerst die Formel und danach die Frage, welche Einheit in den Zahlen steckt. "
        f"So wird die gegebene Größe sauber in {unit_label(task['unit'])} weitergeführt."
    )


def generate_step_explanation(task, question_text):
    lines = solution_lines(task)
    joined_lines = "\n".join(lines)
    prompt = (
        "Du bist ein Lernassistent für die Holzbranche. "
        "Erkläre auf Deutsch eine freie Rückfrage zu einem Muster-Rechenweg. "
        "Sprich ruhig, konkret und fachlich. "
        "Beantworte zuerst direkt die gestellte Frage, bevor du den Rechenweg allgemein erklärst. "
        "Wenn die Frage eine Alternative nennt, etwa 'Warum nicht geteilt?', vergleiche diese Alternative ausdrücklich mit der richtigen Rechenrichtung. "
        "Erkläre dann, in welchem umgekehrten Fall die Alternative richtig wäre. "
        "Wenn es eine Umrechnungsaufgabe ist, nenne zuerst die zugrunde liegende Formelrichtung und erst danach die eingesetzten Zahlen. "
        "Gehe ausdrücklich auf die konkreten Zahlen aus dem Rechenweg ein, nenne die Einheit mit und erkläre genau, warum hier multipliziert oder geteilt wird. "
        "Erkläre bildhaft und anschaulich, zum Beispiel so, dass man sich die Ware oder Platte vor dem inneren Auge vorstellen kann. "
        "Vermeide Formulierungen wie 'gemeint sind hier die Schritte'. "
        "Wenn ein Prozentwert oder ein DB-Faktor vorkommt, erkläre ihn ganz konkret, zum Beispiel 100 minus 25 gleich 75 Prozent und damit 0,75 als Faktor. "
        "Verwende keine allgemeinen Floskeln wie 'die passende Formelrichtung' ohne sie direkt mit der konkreten Formel und den Zahlen zu verbinden. "
        "Antworte so, als würde dir jemand die Frage direkt im Gespräch stellen, in maximal 5 Sätzen. "
        f"Fachliche Formellogik: {FORMULA_GUIDE} "
        f"Aufgabentext: {task['prompt']} "
        f"Aufgabentyp: {task['task_type']}. "
        f"Zielgröße: {unit_label(task['unit'])}. "
        f"Rechenweg:\n{joined_lines}\n"
        f"Frage: {question_text}"
    )

    try:
        if not get_openai_api_key():
            st.session_state.explanation_backend = "fallback_no_key"
            st.session_state.explanation_backend_error = ""
            return fallback_step_explanation(task, question_text)

        text = call_openai_responses_api(prompt, 220)
        if text:
            st.session_state.explanation_backend = "api_rest"
            st.session_state.explanation_backend_error = ""
            return text
        st.session_state.explanation_backend = "fallback_empty_response"
        st.session_state.explanation_backend_error = ""
        return fallback_step_explanation(task, question_text)
    except Exception:
        st.session_state.explanation_backend = "fallback_exception"
        st.session_state.explanation_backend_error = ""
        return fallback_step_explanation(task, question_text)


def choose_task(level, recent_task_types, task_number, forced_task_type=None):
    if forced_task_type in TASK_TYPE_TO_GENERATOR:
        return TASK_TYPE_TO_GENERATOR[forced_task_type]

    candidates = TASKS_BY_LEVEL[level]
    if 2 <= task_number <= 4 and not any("db" in task_type for task_type in recent_task_types):
        db_candidates = [task_func for task_func in candidates if "db" in task_func.__name__]
        if db_candidates:
            return random.choice(db_candidates)

    if not recent_task_types:
        return random.choice(candidates)

    filtered = []
    for task_func in candidates:
        task_name = task_func.__name__.replace("task_", "")
        if task_name not in recent_task_types:
            filtered.append(task_func)

    if filtered:
        return random.choice(filtered)
    return random.choice(candidates)


def create_next_task():
    task_number = st.session_state.task_number
    level = pick_level(task_number)
    forced_task_type = st.session_state.get("next_task_type_override")
    task = choose_task(level, st.session_state.recent_task_types, task_number, forced_task_type)(level)
    st.session_state.task = task
    st.session_state.level = level
    st.session_state.attempt = 1
    st.session_state.feedback_kind = None
    st.session_state.feedback_text = ""
    st.session_state.result_text = ""
    st.session_state.last_answer_display = ""
    st.session_state.solution_visible = False
    st.session_state.show_success_solution = False
    st.session_state.show_optional_solution = False
    st.session_state.task_finished = False
    st.session_state.main_input_locked = False
    st.session_state.answer_input = ""
    st.session_state.hint_text = ""
    st.session_state.last_diagnostic_hint = ""
    st.session_state.hint_backend = ""
    st.session_state.hint_backend_error = ""
    st.session_state.guided_visible = False
    st.session_state.guided_summary = ""
    st.session_state.guided_summary_kind = "warning"
    st.session_state.guided_step_feedback = []
    st.session_state.guided_step_index = 0
    st.session_state.guided_step_attempts = {}
    st.session_state.guided_completed = []
    st.session_state.explanation_request = ""
    st.session_state.explanation_text = ""
    st.session_state.explanation_error = ""
    st.session_state.explanation_backend = ""
    st.session_state.explanation_backend_error = ""
    st.session_state.pending_next_task = False
    st.session_state.next_task_type_override = None
    st.session_state.recent_task_types.append(task["task_type"])
    st.session_state.recent_task_types = st.session_state.recent_task_types[-3:]
    for index, _step in enumerate(task.get("guided_steps", []), start=1):
        st.session_state[f"guided_input_{index}"] = ""


def init_state():
    if "task_number" not in st.session_state:
        st.session_state.task_number = 1
        st.session_state.recent_task_types = []
        st.session_state.pending_next_task = False
        st.session_state.show_theory = False
        create_next_task()
        return

    if "show_theory" not in st.session_state:
        st.session_state.show_theory = False

    if "main_input_locked" not in st.session_state:
        st.session_state.main_input_locked = False

    if st.session_state.get("pending_next_task"):
        create_next_task()


def handle_submission():
    answer_text = st.session_state.answer_input.strip()
    if not answer_text:
        st.session_state.feedback_kind = "warning"
        st.session_state.feedback_text = "Bitte gib einen Rechenweg oder ein Ergebnis ein."
        return

    try:
        answer_value = evaluate_expression(answer_text)
    except (InvalidOperation, SyntaxError, ZeroDivisionError):
        st.session_state.feedback_kind = "error"
        st.session_state.feedback_text = "Die Eingabe konnte nicht als Rechenweg erkannt werden. Erlaubt sind Zahlen, Klammern, +, -, *, /, x, :, × und optional ein Gleichheitszeichen mit Ergebnis."
        return

    task = st.session_state.task
    st.session_state.last_answer_display = format_user_result(answer_value, task)
    st.session_state.result_text = f"Dein Ergebnis: {format_user_result(answer_value, task)} {unit_label(task['unit'])}"
    st.session_state.last_diagnostic_hint = diagnose_common_mistake(task, answer_value, task["expected"])

    if values_match(answer_value, task["expected"], task["round_for_check"], task.get("match_mode")):
        st.session_state.feedback_kind = "success"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = generate_hint(task, answer_value, True, st.session_state.attempt)
        st.session_state.solution_visible = False
        st.session_state.show_success_solution = is_direct_result_input(answer_text)
        st.session_state.show_optional_solution = False
        st.session_state.task_finished = True
        st.session_state.guided_visible = False
        st.session_state.guided_summary = ""
        st.session_state.guided_summary_kind = "warning"
        st.session_state.guided_step_feedback = []
        st.session_state.explanation_text = ""
        return

    if st.session_state.attempt < 2:
        st.session_state.feedback_kind = "warning"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = progressive_main_hint(task, answer_value, st.session_state.attempt)
        st.session_state.guided_visible = False
        st.session_state.guided_summary = ""
        st.session_state.guided_summary_kind = "warning"
        st.session_state.guided_step_feedback = []
        st.session_state.attempt += 1
        return

    st.session_state.feedback_kind = "warning"
    st.session_state.feedback_text = ""
    st.session_state.hint_text = ""
    guided_steps = task.get("guided_steps", [])
    if len(guided_steps) <= 1:
        st.session_state.solution_visible = True
        st.session_state.task_finished = True
        st.session_state.guided_visible = False
        st.session_state.main_input_locked = False
        return

    st.session_state.solution_visible = False
    st.session_state.task_finished = False
    st.session_state.guided_visible = True
    st.session_state.main_input_locked = True
    st.session_state.guided_summary = "Wir gehen jetzt direkt über die Zwischenschritte weiter. Starte unten mit dem ersten Schritt."
    st.session_state.guided_summary_kind = "warning"
    st.session_state.guided_step_feedback = []


def handle_guided_submission():
    task = st.session_state.task
    guided_steps = task.get("guided_steps", [])
    if not guided_steps:
        return

    current_index = st.session_state.guided_step_index
    step = guided_steps[current_index]
    raw_value = st.session_state.get(f"guided_input_{current_index + 1}", "").strip()

    if not raw_value:
        st.session_state.feedback_kind = "warning"
        st.session_state.feedback_text = ""
        st.session_state.guided_summary = f"{step['label']}: Bitte gib hier einen Rechenweg oder ein Ergebnis ein."
        st.session_state.guided_summary_kind = "warning"
        st.session_state.guided_step_feedback = []
        st.rerun()
        return

    try:
        answer_value = evaluate_expression(raw_value)
    except (InvalidOperation, SyntaxError, ZeroDivisionError):
        st.session_state.feedback_kind = "error"
        st.session_state.feedback_text = ""
        st.session_state.guided_summary = f"{step['label']}: Die Eingabe konnte nicht gelesen werden. Erlaubt sind Zahlen, Klammern, +, -, *, /, x, :, × und optional ein Gleichheitszeichen mit Ergebnis."
        st.session_state.guided_summary_kind = "error"
        st.session_state.guided_step_feedback = []
        st.rerun()
        return

    exact_step_match = values_match(answer_value, step["expected"], step["round_for_check"], step.get("match_mode"))
    if guided_values_match(
        answer_value,
        step["expected"],
        step["round_for_check"],
        current_index,
        step["unit"],
        step.get("match_mode"),
    ):
        if exact_step_match:
            success_text = (
                f"{step['label']}: {raw_value} = "
                f"{format_value_for_step(answer_value, step)} {unit_label(step['unit'])}. Passt."
            )
        else:
            success_text = (
                f"{step['label']}: {raw_value} = "
                f"{format_value_for_step(answer_value, step)} {unit_label(step['unit'])}. "
                f"Passt als Rundung; der genaue Schritt liegt bei "
                f"{format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}."
            )
        completed = st.session_state.guided_completed
        completed.append(guided_completed_entry(success_text))
        st.session_state.guided_completed = completed
        st.session_state.guided_step_feedback = []

        if current_index == len(guided_steps) - 1:
            st.session_state.feedback_kind = "success"
            st.session_state.feedback_text = ""
            st.session_state.hint_text = ""
            st.session_state.guided_summary = "Alle Zwischenschritte passen. Schau dir den Rechenweg gerne noch einmal in Ruhe an."
            st.session_state.guided_summary_kind = "warning" if guided_has_warning() else "success"
            st.session_state.guided_visible = True
            st.session_state.solution_visible = False
            st.session_state.task_finished = True
            st.session_state.explanation_text = ""
            st.rerun()

        next_step = guided_steps[current_index + 1]
        st.session_state.guided_step_index = current_index + 1
        st.session_state.feedback_kind = "success"
        st.session_state.feedback_text = ""
        st.session_state.guided_summary = generate_guided_transition_hint(task, step, answer_value, next_step)
        st.session_state.guided_summary_kind = "warning" if guided_has_warning() else "success"
        st.rerun()

    attempts = st.session_state.guided_step_attempts
    step_attempt = attempts.get(current_index, 0) + 1
    attempts[current_index] = step_attempt
    st.session_state.guided_step_attempts = attempts
    st.session_state.feedback_kind = "warning"
    st.session_state.feedback_text = ""

    if step_attempt >= 2:
        if current_index == len(guided_steps) - 1:
            completed = st.session_state.guided_completed
            completed.append(
                auto_resolve_guided_step(
                    task,
                    step,
                    raw_value,
                    answer_value,
                    resolved_step_message(step),
                )
            )
            st.session_state.guided_completed = completed
            st.session_state.guided_step_feedback = []
            st.session_state.guided_summary = ""
            st.session_state.guided_summary_kind = "warning"
            st.session_state.guided_visible = True
            st.session_state.solution_visible = False
            st.session_state.task_finished = True
            st.session_state.explanation_text = ""
            st.rerun()

        next_step = guided_steps[current_index + 1]
        completed = st.session_state.guided_completed
        completed.append(
            auto_resolve_guided_step(
                task,
                step,
                raw_value,
                answer_value,
                resolved_step_message(step, next_step),
                next_step,
            )
        )
        st.session_state.guided_completed = completed
        st.session_state.guided_step_feedback = []
        st.session_state.guided_step_index = current_index + 1
        st.session_state.guided_summary = ""
        st.session_state.guided_summary_kind = "warning"
        st.rerun()

    error_hint = generate_guided_error_hint(task, step, raw_value, answer_value, step_attempt)
    st.session_state.guided_summary = error_hint
    st.session_state.guided_summary_kind = "warning"
    st.session_state.guided_step_feedback = []
    st.rerun()


def handle_explanation_request():
    request_text = st.session_state.explanation_request.strip()
    try:
        normalized_question = normalize_explanation_question(request_text)
    except ValueError:
        st.session_state.explanation_error = "Bitte stell hier eine kurze Frage zum Rechenweg."
        st.session_state.explanation_text = ""
        return

    st.session_state.explanation_error = ""
    st.session_state.explanation_text = generate_step_explanation(st.session_state.task, normalized_question)


def render_solution_explanation_form():
    with st.form("solution_explanation_form", clear_on_submit=False):
        st.text_input(
            "Was möchtest du zum Rechenweg wissen?",
            key="explanation_request",
            placeholder="Zum Beispiel: Warum muss ich hier durch 0,75 teilen?",
        )
        explanation_submitted = st.form_submit_button("Schritte erklären", type="primary")

    if explanation_submitted:
        handle_explanation_request()

    if st.session_state.explanation_error:
        st.warning(st.session_state.explanation_error)

    if st.session_state.explanation_text:
        st.info(f"Erklärung: {st.session_state.explanation_text}")


st.set_page_config(page_title="Holzrechner", page_icon="🪵", layout="centered")
init_state()

st.markdown(
    """
    <style>
        [data-testid="InputInstructions"] {
            display: none;
        }

        .stTextInput input {
            border: 1px solid #22c55e;
        }

        .stTextInput input:focus {
            border: 1px solid #16a34a;
            box-shadow: 0 0 0 1px #16a34a;
        }

        div.stButton > button,
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #16a34a;
            border-color: #16a34a;
            color: white;
        }

        div.stButton > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #15803d;
            border-color: #15803d;
            color: white;
        }

        .st-key-repeat_task_type_button button {
            background-color: #dc2626 !important;
            border-color: #dc2626 !important;
            color: white !important;
        }

        .st-key-repeat_task_type_button button:hover {
            background-color: #b91c1c !important;
            border-color: #b91c1c !important;
            color: white !important;
        }

        .resolved-step-box {
            border: 1px solid rgba(234, 179, 8, 0.35);
            background: rgba(113, 63, 18, 0.34);
            border-radius: 8px;
            padding: 1rem 1.15rem;
            margin: 0.8rem 0;
            line-height: 1.55;
        }

        .resolved-title {
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .resolved-message {
            margin-top: 0.45rem;
            margin-bottom: 0.45rem;
        }

        .resolved-formula {
            margin-top: 0.65rem;
            margin-bottom: 0.65rem;
            padding: 0.7rem 0.8rem;
            border-radius: 6px;
            background: rgba(21, 128, 61, 0.16);
        }

        .resolved-formula-title {
            color: #bbf7d0;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .resolved-formula-text {
            color: #d9f99d;
            font-weight: 700;
        }

        .resolved-bad {
            color: #f87171;
            font-weight: 700;
        }

        .resolved-good {
            color: #4ade80;
            font-weight: 700;
        }

        .resolved-next {
            color: #86efac;
            font-weight: 700;
            margin-top: 0.35rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Holzrechner")
st.write(
    "Im Holzhandel ist sauberes Umrechnen jeden Tag entscheidend: Volumen, Fläche, Laufmeter, Preise und DB "
    "müssen sicher sitzen, damit Angebote, Kalkulationen und Kundengespräche fachlich stimmen."
)
st.write(
    "Du kannst den Rechenweg als Formel, nur das Endergebnis oder Formel mit Gleichheitszeichen und Ergebnis eintragen. "
    "Für mal kannst du x, × oder * verwenden; zum Teilen gehen / oder :. Leerzeichen sind egal."
)
st.markdown(
    """
Beispiele, die funktionieren:
- `0,4536 / 0,0054`
- `0,4536 : 0,0054 = 84`
- `6 x 0,08 x 0,12`
- `6*0,08*0,12=0,0576`
"""
)

st.subheader("Theorie auffrischen")
st.write("Möchtest du noch deine theoretischen Grundlagen auffrischen? Dann klick hier.")
if st.button(
    "Theorie ausblenden" if st.session_state.show_theory else "Theorie anzeigen",
    key="theory_toggle_button",
):
    st.session_state.show_theory = not st.session_state.show_theory
    st.rerun()

if st.session_state.show_theory:
    render_theory_section()

st.subheader(f"Aufgabe {st.session_state.task_number}")
st.write(st.session_state.task["prompt"])
st.caption("Du kannst deinen Rechenweg als Formel, direkt das Ergebnis oder beides mit Gleichheitszeichen eintragen.")

with st.form("answer_form", clear_on_submit=False):
    st.text_input(
        "Deine Eingabe",
        key="answer_input",
        placeholder="",
        disabled=st.session_state.task_finished or st.session_state.get("main_input_locked", False),
    )
    submitted = st.form_submit_button(
        "Bestätigen",
        disabled=st.session_state.task_finished or st.session_state.get("main_input_locked", False),
        type="primary",
    )

if submitted:
    handle_submission()

if st.session_state.feedback_text:
    if st.session_state.feedback_kind == "success":
        st.success(st.session_state.feedback_text)
    elif st.session_state.feedback_kind == "warning":
        st.warning(st.session_state.feedback_text)
    else:
        st.error(st.session_state.feedback_text)

if st.session_state.result_text and not st.session_state.solution_visible:
    st.write(st.session_state.result_text)

if st.session_state.hint_text and not st.session_state.solution_visible:
    if st.session_state.feedback_kind == "success":
        st.success(f"Hinweis: {st.session_state.hint_text}")
    else:
        st.warning(f"Hinweis: {st.session_state.hint_text}")

if st.session_state.guided_visible and not st.session_state.task_finished and not st.session_state.solution_visible:
    st.info("Jetzt mit Zwischenergebnissen weiterrechnen: Unten kannst du die Aufgabe Schritt für Schritt aufbauen.")

if st.session_state.guided_visible:
    st.subheader("Geführte Zwischenschritte")
    st.write("Rechne immer nur den aktuellen Zwischenschritt aus. Sobald er passt, erscheint der nächste Schritt mit dem passenden Hinweis.")

    for completed_entry in st.session_state.guided_completed:
        render_guided_completed_entry(completed_entry)

    render_guided_summary()

    guided_steps = st.session_state.task.get("guided_steps", [])
    current_index = st.session_state.guided_step_index

    if not st.session_state.task_finished and current_index < len(guided_steps):
        current_step = guided_steps[current_index]

        with st.form("guided_steps_form", clear_on_submit=False):
            st.text_input(
                current_step["label"],
                key=f"guided_input_{current_index + 1}",
                placeholder=step_placeholder(current_step),
            )
            guided_submitted = st.form_submit_button("Schritt prüfen", type="primary")

        if guided_submitted:
            handle_guided_submission()

if st.session_state.solution_visible:
    st.warning(
        "Nicht ganz. "
        f"Dein Ergebnis: {st.session_state.last_answer_display} {unit_label(st.session_state.task['unit'])}. "
        f"Richtig wäre: {format_expected(st.session_state.task)} {unit_label(st.session_state.task['unit'])}. "
        f"{st.session_state.hint_text}"
    )
    render_musterloesung(st.session_state.task)
    render_solution_explanation_form()

if st.session_state.task_finished and not st.session_state.solution_visible:
    if st.session_state.get("show_optional_solution"):
        render_musterloesung(st.session_state.task)
        render_solution_explanation_form()
    elif st.button("Musterlösung anzeigen"):
        st.session_state.show_optional_solution = True
        st.rerun()

if st.session_state.task_finished:
    left_col, right_col = st.columns(2)
    with left_col:
        repeat_task_type = st.button("Weiter mit gleichem Aufgabentyp", key="repeat_task_type_button")
    with right_col:
        different_task_type = st.button("Weiter mit anderem Aufgabentyp", type="primary")

    if repeat_task_type or different_task_type:
        st.session_state.task_number += 1
        if repeat_task_type:
            st.session_state.next_task_type_override = st.session_state.task["task_type"]
        else:
            st.session_state.next_task_type_override = None
        st.session_state.pending_next_task = True
        st.rerun()
