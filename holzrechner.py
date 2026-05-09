import ast
import json
import os
import random
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_DOWN, ROUND_HALF_UP
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
    1: [Decimal("0.04"), Decimal("0.06"), Decimal("0.08"), Decimal("0.12"), Decimal("0.14")],
    2: [Decimal("0.04"), Decimal("0.06"), Decimal("0.08"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16")],
    3: [Decimal("0.04"), Decimal("0.06"), Decimal("0.08"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18")],
}
STRUCTURAL_HEIGHTS_BY_LEVEL = {
    1: [Decimal("0.06"), Decimal("0.08"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.20")],
    2: [Decimal("0.06"), Decimal("0.08"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20"), Decimal("0.24")],
    3: [Decimal("0.06"), Decimal("0.08"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20"), Decimal("0.24"), Decimal("0.28")],
}
STRUCTURAL_LENGTHS_BY_LEVEL = {
    1: [Decimal("5.0"), Decimal("6.0"), Decimal("7.0"), Decimal("8.0")],
    2: [Decimal("5.0"), Decimal("6.0"), Decimal("7.0"), Decimal("8.0"), Decimal("9.0"), Decimal("10.0")],
    3: [Decimal("6.0"), Decimal("7.0"), Decimal("8.0"), Decimal("9.0"), Decimal("10.0"), Decimal("11.0"), Decimal("12.0"), Decimal("13.0")],
}
HOBEL_WIDTHS_BY_LEVEL = {
    1: [Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18")],
    2: [Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20")],
    3: [Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20"), Decimal("0.22")],
}
HOBEL_THICKNESSES_BY_LEVEL = {
    1: [Decimal("0.019"), Decimal("0.023")],
    2: [Decimal("0.019"), Decimal("0.023")],
    3: [Decimal("0.019"), Decimal("0.023"), Decimal("0.027")],
}
HOBEL_LENGTHS_BY_LEVEL = {
    1: [Decimal("2.70"), Decimal("3.00"), Decimal("3.30"), Decimal("3.60"), Decimal("3.90"), Decimal("4.20"), Decimal("4.50"), Decimal("4.80"), Decimal("5.10"), Decimal("5.40")],
    2: [Decimal("2.70"), Decimal("3.00"), Decimal("3.30"), Decimal("3.60"), Decimal("3.90"), Decimal("4.20"), Decimal("4.50"), Decimal("4.80"), Decimal("5.10"), Decimal("5.40")],
    3: [Decimal("2.70"), Decimal("3.00"), Decimal("3.30"), Decimal("3.60"), Decimal("3.90"), Decimal("4.20"), Decimal("4.50"), Decimal("4.80"), Decimal("5.10"), Decimal("5.40")],
}
HOBEL_BUNDLE_COUNTS = [4, 5, 6, 7, 8]
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
INSULATION_VOLUMES = [
    Decimal("5"),
    Decimal("7"),
    Decimal("9"),
    Decimal("11"),
    Decimal("13"),
    Decimal("15"),
    Decimal("17"),
    Decimal("19"),
    Decimal("21"),
    Decimal("23"),
    Decimal("25"),
]
WOOD_FIBER_INSULATION_DENSITY = Decimal("40")
FLOORING_NEEDS_BY_LEVEL = {
    1: [Decimal("25"), Decimal("40"), Decimal("60"), Decimal("80")],
    2: [Decimal("45"), Decimal("70"), Decimal("90"), Decimal("100"), Decimal("120")],
    3: [Decimal("65"), Decimal("95"), Decimal("125"), Decimal("150"), Decimal("180")],
}
RUNNING_METER_NEEDS_BY_LEVEL = {
    1: [Decimal("30"), Decimal("45"), Decimal("60"), Decimal("75")],
    2: [Decimal("80"), Decimal("100"), Decimal("120"), Decimal("150")],
    3: [Decimal("125"), Decimal("150"), Decimal("180"), Decimal("220"), Decimal("260")],
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
    "Stück": "Stück",
    "Bund": "Bund",
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

AI_ERROR_EVALUATION_GUIDE = """
Typische Fehlerquellen, die du bei falschen Eingaben zusätzlich prüfen sollst:
Prüfe zuerst konkrete Faktoren: fehlt etwas, ist etwas zu viel enthalten, liegt ein 10/100/1000- oder Kommafehler vor, oder wurde multiplizieren und dividieren vertauscht?
Wenn eine lokale Python-Diagnose mitgegeben wird, behandle sie als starken Hinweis, aber prüfe sie anhand von Aufgabe, Eingabe und Zielgröße noch einmal selbst.
Wenn die lokale Diagnose sagt, dass ein Faktor fehlt, formuliere das nicht als offene Frage, ob dieser Faktor benötigt wird. Sage dann klar, dass dieser Faktor wahrscheinlich fehlt oder noch einbezogen werden muss.
Sprich nur dann von falscher Reihenfolge oder fehlender Struktur, wenn kein plausibler Faktor-, Einheiten- oder Richtungsfehler erkennbar ist.
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

Laufende Ware:
- Benötigte Stückzahl oder Bundzahl: Bedarf in Laufmeter / Länge pro Stück, danach auf volle Stück und bei Glattkantbrettern auf volle Bund aufrunden

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


def truncate_decimal(value, places):
    quant = q("1") if places == 0 else q("1." + ("0" * places))
    return value.quantize(quant, rounding=ROUND_DOWN)


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


def clean_ai_output(text):
    text = str(text)
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("{,}", ",")
    text = re.sub(r"\\text\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", text)
    text = text.replace("\\times", " x ")
    text = text.replace("\\cdot", " x ")
    text = text.replace("\\,", " ")
    text = text.replace("\\(", "(").replace("\\)", ")")
    text = text.replace("\\[", "").replace("\\]", "")
    text = text.replace("$", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
        "model": "gpt-5.4-nano",
        "reasoning": {
            "effort": "low",
        },
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
            "verbosity": "medium",
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


def structural_cm_number(value_m):
    return format_cm(value_m)


def generate_structural_dimensions(level, length_m=None):
    forbidden_numbers = {format_m(length_m)} if length_m is not None else set()
    valid_pairs = []

    for first in STRUCTURAL_WIDTHS_BY_LEVEL[level]:
        first_number = structural_cm_number(first)
        if first_number in forbidden_numbers:
            continue
        for second in STRUCTURAL_HEIGHTS_BY_LEVEL[level]:
            second_number = structural_cm_number(second)
            if second_number in forbidden_numbers or second_number == first_number:
                continue
            valid_pairs.append(tuple(sorted([first, second])))

    if valid_pairs:
        return list(random.choice(valid_pairs))

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


def generate_whole_volume_position_details(level):
    product = random.choice(PRODUCTS)
    kind = product["kind"]

    if kind == "structural_beam":
        length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
        width_m, height_m = generate_structural_dimensions(level, length_m)
        count = random.choice(COUNTS_BY_LEVEL[level])
        piece_volume = length_m * width_m * height_m
        total_volume = piece_volume * Decimal(count)
        piece_volume_places = precise_decimal_places(piece_volume)
        total_volume_places = precise_decimal_places(total_volume)
        width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))
        context = (
            f"{count} Stück {product['name']} im Format {format_m(length_m)} m x "
            f"{width_text} x {height_text}"
        )
        return {
            "product": product,
            "context": context,
            "total_volume": total_volume,
            "total_volume_places": total_volume_places,
            "perfect_volume_formula": (
                f"{format_m(length_m)} x {format_decimal(width_m, 2)} x "
                f"{format_decimal(height_m, 2)} x {count}"
            ),
            "volume_solution_steps": [
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
            ],
            "volume_guided_steps": [
                make_guided_step(
                    "Volumen pro Stück",
                    piece_volume.normalize(),
                    "m3",
                    piece_volume_places,
                    False,
                    "Rechne zuerst Länge x Breite x Höhe für ein einzelnes Stück.",
                    "Länge x Breite x Höhe",
                ),
                make_guided_step(
                    "Gesamtvolumen",
                    total_volume.normalize(),
                    "m3",
                    total_volume_places,
                    False,
                    "Multipliziere danach das Volumen pro Stück mit der Stückzahl.",
                    "Volumen pro Stück x Stückzahl",
                ),
            ],
            "volume_factor_checks": [
                factor_check(f"Länge {format_m(length_m)} Meter", length_m),
                factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
                factor_check(f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", height_m),
                factor_check(f"Stückzahl {count}", Decimal(count)),
            ],
        }

    if kind == "panel":
        panel_format = panel_format_text(product)
        length_m, width_m = panel_format_dimensions(panel_format)
        thickness_m = panel_thickness_for_product(product, level)
        panel_count = panel_count_for_level(level)
        sheet_area = length_m * width_m
        total_area = sheet_area * Decimal(panel_count)
        total_volume = total_area * thickness_m
        sheet_area_places = precise_decimal_places(sheet_area)
        total_area_places = precise_decimal_places(total_area)
        total_volume_places = precise_decimal_places(total_volume)
        thickness_text = display_measure(thickness_m, ("mm", "cm"))
        context = (
            f"{panel_count} Platten {product['name']} im Format {panel_format} "
            f"bei {thickness_text} Dicke"
        )
        return {
            "product": product,
            "context": context,
            "total_volume": total_volume,
            "total_volume_places": total_volume_places,
            "perfect_volume_formula": (
                f"{format_decimal(length_m, 2)} x {format_decimal(width_m, 3)} x "
                f"{panel_count} x {format_decimal(thickness_m, 3)}"
            ),
            "volume_solution_steps": [
                (
                    "Fläche pro Platte",
                    "Fläche pro Platte = Länge x Breite",
                    f"{format_decimal(length_m, 2)} Meter x {format_decimal(width_m, 3)} Meter = "
                    f"{format_decimal(sheet_area, sheet_area_places)} Quadratmeter",
                ),
                (
                    "Gesamtfläche",
                    "Gesamtfläche = Fläche pro Platte x Plattenanzahl",
                    f"{format_decimal(sheet_area, sheet_area_places)} Quadratmeter x {panel_count} Stück = "
                    f"{format_decimal(total_area, total_area_places)} Quadratmeter",
                ),
                (
                    "Gesamtvolumen",
                    "Gesamtvolumen = Gesamtfläche x Dicke",
                    f"{format_decimal(total_area, total_area_places)} Quadratmeter x "
                    f"{format_decimal(thickness_m, 3)} Meter = {format_decimal(total_volume, total_volume_places)} Kubikmeter",
                ),
            ],
            "volume_guided_steps": [
                make_guided_step(
                    "Fläche pro Platte",
                    sheet_area.normalize(),
                    "m2",
                    sheet_area_places,
                    False,
                    "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                    "Länge x Breite",
                ),
                make_guided_step(
                    "Gesamtfläche",
                    total_area.normalize(),
                    "m2",
                    total_area_places,
                    False,
                    "Multipliziere die Fläche pro Platte mit der Plattenanzahl.",
                    "Fläche pro Platte x Plattenanzahl",
                ),
                make_guided_step(
                    "Gesamtvolumen",
                    total_volume.normalize(),
                    "m3",
                    total_volume_places,
                    False,
                    "Multipliziere die Gesamtfläche mit der Dicke in Meter.",
                    "Gesamtfläche x Dicke",
                ),
            ],
            "volume_factor_checks": [
                factor_check(f"Länge {format_decimal(length_m, 2)} Meter", length_m),
                factor_check(f"Breite {format_decimal(width_m, 3)} Meter", width_m),
                factor_check(f"Plattenanzahl {panel_count}", Decimal(panel_count)),
                factor_check(f"Dicke {thickness_text} ({format_decimal(thickness_m, 3)} Meter)", thickness_m),
            ],
        }

    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    piece_volume = board_length * width_m * height_m
    running_meters = board_length * Decimal(board_count)
    total_volume = piece_volume * Decimal(board_count)
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))
    context = (
        f"{board_count} Bretter {hobelware_display_name(product)} mit je {format_m(board_length)} m Länge, "
        f"{width_text} Breite und {thickness_text} Stärke"
    )
    return {
        "product": product,
        "context": context,
        "total_volume": total_volume,
        "total_volume_places": total_volume_places,
        "perfect_volume_formula": (
            f"{format_m(board_length)} x {format_decimal(width_m, 2)} x "
            f"{format_decimal(height_m, 3)} x {board_count}"
        ),
        "volume_solution_steps": [
            (
                "Volumen pro Brett",
                "Volumen pro Brett = Länge x Breite x Stärke",
                f"{format_m(board_length)} Meter x {format_decimal(width_m, 2)} Meter x "
                f"{format_decimal(height_m, 3)} Meter = {format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
            ),
            (
                "Gesamtvolumen",
                "Gesamtvolumen = Volumen pro Brett x Brettanzahl",
                f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter x {board_count} Stück = "
                f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
            ),
        ],
        "volume_guided_steps": [
            make_guided_step(
                "Volumen pro Brett",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Rechne zuerst Länge x Breite x Stärke für ein einzelnes Brett.",
                "Länge x Breite x Stärke",
            ),
            make_guided_step(
                "Gesamtvolumen",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Multipliziere danach das Volumen pro Brett mit der Brettanzahl.",
                "Volumen pro Brett x Brettanzahl",
            ),
        ],
        "volume_factor_checks": [
            factor_check(f"Länge {format_m(board_length)} Meter", board_length),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Stärke {thickness_text} ({format_decimal(height_m, 3)} Meter)", height_m),
            factor_check(f"Brettanzahl {board_count}", Decimal(board_count)),
        ],
    }


def generate_whole_volume_position(level):
    details = generate_whole_volume_position_details(level)
    return (
        details["product"],
        details["context"],
        details["total_volume"],
        details["total_volume_places"],
    )


def evaluate_expression(text):
    expression = text.strip()
    if "=" in expression:
        parts = [part.strip() for part in expression.split("=") if part.strip()]
        if parts:
            expression = parts[-1]

    cleaned = normalize_number_input(expression)
    cleaned = cleaned.replace("×", "*").replace("·", "*")
    cleaned = cleaned.replace("x", "*").replace("X", "*").replace(":", "/")
    parsed = ast.parse(cleaned, mode="eval")
    return evaluate_ast_node(parsed.body)


def normalize_number_input(expression):
    cleaned = expression.strip()
    cleaned = re.sub(r"(?<=\d)[\s'_´`’](?=\d{3}(?:\D|$))", "", cleaned)

    def remove_dot_groups(match):
        number = match.group(0)
        if number.startswith("0."):
            return number
        return number.replace(".", "")

    cleaned = re.sub(r"(?<!\d)\d{1,3}(?:\.\d{3})+(?!\d)", remove_dot_groups, cleaned)
    return cleaned.replace(",", ".")


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


def db_factor_check(db_percent, divisor):
    divisor_text = format_decimal(divisor, 2)
    percent_text = format_decimal(db_percent, 0)
    return {
        "label": f"DB-Faktor {divisor_text} bei {percent_text} % DB",
        "value": divisor,
        "missing_when_ratio_is_value": True,
        "missing_message": (
            f"Die Abweichung passt auffällig dazu, dass der DB-Schritt fehlt. "
            f"Bei {percent_text} % DB bleibt der Faktor {divisor_text}; "
            f"für den VK wird der EK durch {divisor_text} geteilt."
        ),
    }


def factor_check(label, value, missing_when_ratio_is_value=False):
    return {
        "label": label,
        "value": value,
        "missing_when_ratio_is_value": missing_when_ratio_is_value,
    }


def base_factor_check(label, value):
    return {
        "label": label,
        "value": value,
    }


def db_wrong_factor_checks(base_value, db_percent, correct_factor, mode):
    checks = []
    percent_text = format_decimal(db_percent, 0)
    correct_text = format_decimal(correct_factor, 2)
    wrong_factors = []

    for offset in (Decimal("0.10"), Decimal("0.20"), Decimal("0.30")):
        candidate = correct_factor + offset
        if candidate < Decimal("1") and candidate != correct_factor:
            wrong_factors.append(candidate)

    for wrong_factor in dict.fromkeys(wrong_factors):
        wrong_text = format_decimal(wrong_factor, 2)
        if mode == "sale_price":
            value = base_value / wrong_factor
            message = (
                f"Deine Eingabe wirkt so, als wäre der DB-Faktor im Kopf falsch gebildet worden: "
                f"Bei {percent_text} % DB brauchst du {correct_text}, nicht {wrong_text}. "
                "Prüfe beim Ziel-VK immer zuerst: 100 Prozent minus DB-Satz ergibt den Kostenanteil."
            )
        else:
            value = base_value * wrong_factor
            message = (
                f"Deine Eingabe wirkt so, als wäre der DB-Faktor im Kopf falsch gebildet worden: "
                f"Bei {percent_text} % DB brauchst du {correct_text}, nicht {wrong_text}. "
                "Bei der Rückwärtsrechnung vom VK zum EK wird der VK mit dem richtigen Kostenanteil multipliziert."
            )

        checks.append(wrong_value_check(value, message, "EUR", round_for_check=True))

    return checks


def wrong_value_check(value, message, unit=None, round_for_check=None, match_mode=None):
    return {
        "value": value,
        "message": message,
        "unit": unit,
        "round_for_check": round_for_check,
        "match_mode": match_mode,
    }


def ignored_board_length_checks(correct_value, board_length, unit, target_label):
    length_text = format_m(board_length)
    message = (
        f"Die Abweichung passt auffällig dazu, dass die Brettlänge von {length_text} Meter in die Rechnung einbezogen wurde. "
        f"Bei {target_label} ist die Laufmeterangabe bereits die relevante Länge; die einzelne Brettlänge ist hier nur Zusatzinformation."
    )
    return [
        wrong_value_check(correct_value * board_length, message, unit),
        wrong_value_check(correct_value / board_length, message, unit),
    ]


def task_volume_beam(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
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
        "factor_checks": [
            {"label": f"Länge {format_m(length_m)} Meter", "value": length_m},
            {"label": f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", "value": width_m},
            {"label": f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", "value": height_m},
            {"label": f"Stückzahl {count}", "value": Decimal(count)},
        ],
        "wrong_value_checks": [
            wrong_value_check(
                piece_volume * Decimal(package_count),
                (
                    f"Deine Eingabe passt eher zu einem vollen Paket mit {package_count} Stück. "
                    f"Gefragt sind hier aber die tatsächlich genannten {count} Stück."
                ),
                "m3",
            ),
        ],
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
            "Preis je Laufmeter",
            "Euro pro Laufmeter = Euro pro Kubikmeter x Breite x Stärke",
            f"{format_decimal(m3_price, 0)} Euro pro Kubikmeter x {format_decimal(width_m, 2)} Meter x "
            f"{format_decimal(height_m, 3)} Meter = "
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
        "correction": "Rechne den Preis pro Kubikmeter direkt mit Breite und Stärke in Meter auf den Laufmeterpreis um.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(m3_price, 0)} x {format_decimal(width_m, 2)} x "
            f"{format_decimal(height_m, 3)}"
        ),
        "factor_checks": [
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Stärke {thickness_text} ({format_decimal(height_m, 3)} Meter)", height_m),
            factor_check(f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro", m3_price),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                m3_price / cross_section,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Kubikmeterpreis offenbar durch den Querschnitt geteilt. "
                    "Für Euro pro Laufmeter wird aus dem Kubikmeterpreis aber der Preis des Volumens von einem Laufmeter gebildet."
                ),
                "EUR",
            ),
            *ignored_board_length_checks(
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                board_length,
                "EUR",
                "dem Preis je Laufmeter",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Preis je Laufmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den Kubikmeterpreis direkt mit Breite und Stärke in Meter.",
                "Kubikmeterpreis x Breite x Stärke",
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
        "factor_checks": [
            factor_check(f"Dicke {thickness_text} ({format_decimal(thickness_m, 3)} Meter)", thickness_m),
            factor_check(f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro", m3_price),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                m3_price / thickness_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Kubikmeterpreis offenbar durch die Dicke geteilt. "
                    "Bei Euro pro Quadratmeter wird aus einem Quadratmeter Platte erst das kleine Volumen über die Dicke gebildet."
                ),
                "EUR",
            ),
        ],
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


def task_m3_price_from_square_meter(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    thickness_m = panel_thickness_for_product(product, level)
    m2_price = panel_m2_price_for_product(product, level)
    result = m2_price / thickness_m
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Eine {product['name']} im Format {panel_format} ist {thickness_text} dick und kostet {format_decimal(m2_price, 2)} Euro pro Quadratmeter.\n\nWie hoch ist der Preis pro Kubikmeter?",
            f"Für eine {product['name']} im Format {panel_format} liegt ein Quadratmeterpreis von {format_decimal(m2_price, 2)} Euro vor. Die Platte ist {thickness_text} stark.\n\nWie hoch ist der entsprechende Kubikmeterpreis?",
        ]
    )

    solution = format_solution_steps(
        (
            "Preis je Kubikmeter",
            "Euro pro Kubikmeter = Euro pro Quadratmeter / Dicke",
            f"{format_decimal(m2_price, 2)} Euro pro Quadratmeter / {format_decimal(thickness_m, 3)} Meter = "
            f"{format_decimal(result, 2)} Euro pro Kubikmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "m3_price_from_square_meter",
        "correction": "Gehe rückwärts vom Quadratmeterpreis zum Kubikmeterpreis. Ein Kubikmeter enthält bei dünnen Platten viele Quadratmeter, deshalb wird durch die Dicke in Metern geteilt.",
        "solution": solution,
        "perfect_formula": f"{format_decimal(m2_price, 2)} / {format_decimal(thickness_m, 3)}",
        "factor_checks": [
            factor_check(f"Quadratmeterpreis {format_decimal(m2_price, 2)} Euro", m2_price),
            factor_check(
                f"Dicke {thickness_text} ({format_decimal(thickness_m, 3)} Meter)",
                thickness_m,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                m2_price * thickness_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Quadratmeterpreis offenbar mit der Dicke multipliziert. "
                    "Für Euro pro Kubikmeter muss der Quadratmeterpreis auf einen ganzen Kubikmeter hochgerechnet werden."
                ),
                "EUR",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Preis pro Kubikmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den Quadratmeterpreis durch die Dicke in Metern.",
                "Quadratmeterpreis / Dicke in Meter",
                placeholder=f"Zum Beispiel {format_decimal(m2_price, 2)} / {format_decimal(thickness_m, 3)}",
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
        "factor_checks": [
            factor_check(
                f"Dicke {thickness_text} ({format_decimal(thickness_m, 3)} Meter)",
                thickness_m,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_volume * thickness_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast das Volumen offenbar mit der Dicke multipliziert. "
                    "Wenn Kubikmeter in Quadratmeter zurückgeführt werden, muss die Dicke herausgerechnet werden."
                ),
                "m2",
                round_for_check=False,
            ),
        ],
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
        "factor_checks": [
            factor_check(f"Dicke {thickness_text} ({format_decimal(thickness_m, 3)} Meter)", thickness_m),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                square_meters / thickness_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast die Quadratmeter offenbar durch die Dicke geteilt. "
                    "Für Kubikmeter muss die Fläche mit der Dicke in Meter weitergerechnet werden."
                ),
                "m3",
                round_for_check=False,
            ),
        ],
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
        "factor_checks": [
            factor_check(f"Volumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            factor_check(f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro", m3_price),
        ],
        "base_factor_checks": [
            base_factor_check(f"Volumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            base_factor_check(f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro", m3_price),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_volume / m3_price,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast das Volumen offenbar durch den Preis geteilt. "
                    "Für den Gesamtpreis wird das vorhandene Volumen mit dem Preis pro Kubikmeter bewertet."
                ),
                "EUR",
            ),
        ],
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
        "factor_checks": [
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Laufmeter {format_decimal(running_meters, running_meters_places)}", running_meters),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                running_meters / width_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast die Laufmeter offenbar durch die Breite geteilt. "
                    "Wenn aus Laufmetern Quadratmeter werden sollen, wird die Breite als Flächenfaktor genutzt."
                ),
                "m2",
                round_for_check=False,
            ),
            *ignored_board_length_checks(result.normalize(), board_length, "m2", "Quadratmetern aus Laufmetern"),
        ],
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
        "factor_checks": [
            factor_check(
                f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)",
                width_m,
                missing_when_ratio_is_value=True,
            ),
            factor_check(
                f"Stärke {thickness_text} ({format_decimal(height_m, 3)} Meter)",
                height_m,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_volume * cross_section,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast das Volumen offenbar mit dem Querschnitt multipliziert. "
                    "Wenn Kubikmeter in Laufmeter zurückgeführt werden, muss der Querschnitt herausgeteilt werden."
                ),
                "lfm",
                round_for_check=False,
            ),
            *ignored_board_length_checks(running_meters.normalize(), board_length, "lfm", "Laufmetern aus Kubikmetern"),
        ],
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
        "factor_checks": [
            factor_check(
                f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)",
                width_m,
                missing_when_ratio_is_value=True,
            ),
            factor_check(f"Quadratmeter {format_decimal(square_meters, square_meters_places)}", square_meters),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                square_meters * width_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast die Quadratmeter offenbar mit der Breite multipliziert. "
                    "Wenn Quadratmeter in Laufmeter zurückgeführt werden, muss die Breite herausgeteilt werden."
                ),
                "lfm",
                round_for_check=False,
            ),
            *ignored_board_length_checks(result.normalize(), board_length, "lfm", "Laufmetern aus Quadratmetern"),
        ],
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
    width_m, height_m = generate_structural_dimensions(level, length_m)
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
            f"Ein Lieferant bietet uns {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} zu {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter im EK an. Bei diesem Querschnitt liegen {package_count} Stück im Paket, intern soll mindestens {format_decimal(db_percent, 0)} % DB erreicht werden.\n\nZu welchem Mindestpreis können wir die gesamte Position dem Kunden anbieten?",
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
        "factor_checks": [
            factor_check(f"Länge {format_m(length_m)} Meter", length_m),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", height_m),
            factor_check(f"Stückzahl {count}", Decimal(count)),
            factor_check(f"Kubikmeterpreis {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"Gesamtvolumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            base_factor_check(f"Kubikmeterpreis {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_ek * divisor,
                (
                    f"Deine Eingabe wirkt so, als hättest du den EK mit dem DB-Faktor {format_decimal(divisor, 2)} multipliziert. "
                    "Bei der VK-Kalkulation mit Ziel-DB wird der EK aber auf den VK hochgerechnet."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_ek * (Decimal("1") + db_percent / Decimal("100")),
                (
                    f"Deine Eingabe wirkt wie ein Aufschlag von {format_decimal(db_percent, 0)} % auf den EK. "
                    "Ein Ziel-DB ist aber keine einfache Aufschlagsrechnung auf den EK, sondern wird vom Verkaufspreis aus betrachtet."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_ek / db_percent,
                (
                    f"Deine Eingabe wirkt so, als wäre mit {format_decimal(db_percent, 0)} statt mit dem DB-Faktor {format_decimal(divisor, 2)} gerechnet worden. "
                    "Prozentwerte müssen zuerst als Faktor verstanden werden."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_ek * db_percent,
                (
                    f"Deine Eingabe wirkt so, als wäre der Prozentwert {format_decimal(db_percent, 0)} direkt als Faktor verwendet worden. "
                    "Für den Ziel-DB brauchst du den Kostenanteil 1 minus DB-Satz."
                ),
                "EUR",
            ),
            wrong_value_check(
                piece_volume * Decimal(package_count) * ek_price_m3 / divisor,
                (
                    f"Deine Eingabe passt eher zu einem vollen Paket mit {package_count} Stück. "
                    f"Gefragt sind hier aber die tatsächlich genannten {count} Stück."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_ek, db_percent, divisor, "sale_price"),
        ],
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


def task_lfm_db_sale_price(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    running_meters = board_length * Decimal(board_count)
    ek_price_lfm = choice_for_level(RUNNING_METER_PRICES_BY_LEVEL, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_ek = running_meters * ek_price_lfm
    result = total_ek / divisor
    running_meters_places = precise_decimal_places(running_meters, 0, 1)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name}. Die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark. Der EK liegt bei {format_decimal(ek_price_lfm, 2)} Euro pro Laufmeter, Ziel-DB {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der gesamte VK?",
            f"Eine Kundin interessiert sich für {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name}. Ein Brett hat {format_m(board_length)} m Länge, {width_text} Breite und {thickness_text} Stärke. Kalkuliert wird mit {format_decimal(ek_price_lfm, 2)} Euro EK pro Laufmeter und {format_decimal(db_percent, 0)} % DB.\n\nWie hoch ist der Verkaufspreis für die Position?",
            f"Der Lieferant bietet {display_name} zu {format_decimal(ek_price_lfm, 2)} Euro pro Laufmeter im EK an. Angefragt sind {format_decimal(running_meters, running_meters_places)} Laufmeter; ein Brett ist {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark. Wir möchten mindestens {format_decimal(db_percent, 0)} % DB erreichen.\n\nWelchen Mindest-VK braucht die Position?",
        ]
    )

    solution = format_solution_steps(
        (
            "Gesamter EK",
            "Gesamter EK = Laufmeter x EK pro Laufmeter",
            f"{format_decimal(running_meters, running_meters_places)} Laufmeter x {format_decimal(ek_price_lfm, 2)} Euro pro Laufmeter = "
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
        "task_type": "lfm_db_sale_price",
        "correction": "Rechne zuerst die Laufmeter mit dem EK pro Laufmeter zum gesamten EK hoch. Danach wird der Ziel-DB über den verbleibenden Kostenanteil berücksichtigt.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(running_meters, running_meters_places)} x {format_decimal(ek_price_lfm, 2)} / "
            f"{format_decimal(divisor, 2)}"
        ),
        "factor_checks": [
            factor_check(f"Laufmeter {format_decimal(running_meters, running_meters_places)}", running_meters),
            factor_check(f"EK pro Laufmeter {format_decimal(ek_price_lfm, 2)} Euro", ek_price_lfm),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"Laufmeter {format_decimal(running_meters, running_meters_places)}", running_meters),
            base_factor_check(f"EK pro Laufmeter {format_decimal(ek_price_lfm, 2)} Euro", ek_price_lfm),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_ek,
                "Deine Eingabe entspricht auffällig dem gesamten EK. Für den VK muss danach noch der Ziel-DB berücksichtigt werden.",
                "EUR",
            ),
            wrong_value_check(
                total_ek * (Decimal("1") + db_percent / Decimal("100")),
                (
                    f"Deine Eingabe wirkt wie ein Aufschlag von {format_decimal(db_percent, 0)} % auf den EK. "
                    "Ein Ziel-DB wird aber vom Verkaufspreis aus betrachtet."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_ek, db_percent, divisor, "sale_price"),
        ],
        "guided_steps": [
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere die Laufmeter mit dem EK pro Laufmeter.",
                "Laufmeter x EK pro Laufmeter",
                placeholder=f"Zum Beispiel {format_decimal(running_meters, running_meters_places)} * {format_decimal(ek_price_lfm, 2)}",
            ),
            make_guided_step(
                "Gesamter VK",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch den Kostenanteil nach DB.",
                "Gesamter EK / (1 - DB-Satz)",
                placeholder=f"Zum Beispiel {format_decimal(total_ek, 2)} / {format_decimal(divisor, 2)}",
            ),
        ],
    }


def task_m2_db_sale_price(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    panel_count = panel_count_for_level(level)
    ek_price_m2 = panel_m2_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")

    sheet_area = length_m * width_m
    total_area = sheet_area * Decimal(panel_count)
    total_ek = total_area * ek_price_m2
    result = total_ek / divisor
    sheet_area_places = precise_decimal_places(sheet_area)
    total_area_places = precise_decimal_places(total_area)

    prompt = random.choice(
        [
            f"Für ein Angebot liegen {panel_count} Platten {product['name']} im Format {panel_format} vor. Der EK beträgt {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter, Ziel-DB {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der gesamte VK?",
            f"{request_intro()}: {panel_count} Stück {product['name']} im Format {panel_format}. Kalkuliert wird mit {format_decimal(ek_price_m2, 2)} Euro EK pro Quadratmeter und {format_decimal(db_percent, 0)} % DB.\n\nWie hoch ist der Verkaufspreis für diese Position?",
            f"Ein Lieferant bietet {panel_count} Platten {product['name']} im Format {panel_format} zu {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter im EK an. Für das Kundenangebot sollen mindestens {format_decimal(db_percent, 0)} % DB stehen bleiben.\n\nWelchen Mindestpreis müssen wir für diese Position anbieten?",
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
            "Gesamtfläche",
            "Gesamtfläche = Fläche pro Platte x Plattenanzahl",
            f"{format_decimal(sheet_area, sheet_area_places)} Quadratmeter x {panel_count} Stück = "
            f"{format_decimal(total_area, total_area_places)} Quadratmeter",
        ),
        (
            "Gesamter EK",
            "Gesamter EK = Gesamtfläche x EK pro Quadratmeter",
            f"{format_decimal(total_area, total_area_places)} Quadratmeter x {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter = "
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
        "task_type": "m2_db_sale_price",
        "correction": "Rechne zuerst die Fläche pro Platte und die Gesamtfläche. Danach bestimmst du den gesamten EK und kalkulierst den VK mit dem Ziel-DB.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(length_m, 2)} x {format_decimal(width_m, 3)} x {panel_count} x "
            f"{format_decimal(ek_price_m2, 2)} / {format_decimal(divisor, 2)}"
        ),
        "factor_checks": [
            factor_check(f"Länge {format_decimal(length_m, 2)} Meter", length_m),
            factor_check(f"Breite {format_decimal(width_m, 3)} Meter", width_m),
            factor_check(f"Plattenanzahl {panel_count}", Decimal(panel_count)),
            factor_check(f"EK pro Quadratmeter {format_decimal(ek_price_m2, 2)} Euro", ek_price_m2),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"Gesamtfläche {format_decimal(total_area, total_area_places)} Quadratmeter", total_area),
            base_factor_check(f"EK pro Quadratmeter {format_decimal(ek_price_m2, 2)} Euro", ek_price_m2),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_ek,
                "Deine Eingabe entspricht auffällig dem gesamten EK. Für den VK muss danach noch der Ziel-DB berücksichtigt werden.",
                "EUR",
            ),
            wrong_value_check(
                total_ek * (Decimal("1") + db_percent / Decimal("100")),
                (
                    f"Deine Eingabe wirkt wie ein Aufschlag von {format_decimal(db_percent, 0)} % auf den EK. "
                    "Ein Ziel-DB wird aber vom Verkaufspreis aus betrachtet."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_ek, db_percent, divisor, "sale_price"),
        ],
        "guided_steps": [
            make_guided_step(
                "Fläche pro Platte",
                sheet_area.normalize(),
                "m2",
                sheet_area_places,
                False,
                "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                "Länge x Breite",
                placeholder=f"Zum Beispiel {format_decimal(length_m, 2)} * {format_decimal(width_m, 3)}",
            ),
            make_guided_step(
                "Gesamtfläche",
                total_area.normalize(),
                "m2",
                total_area_places,
                False,
                "Multipliziere die Fläche pro Platte mit der Plattenanzahl.",
                "Fläche pro Platte x Plattenanzahl",
                placeholder=f"Zum Beispiel {format_decimal(sheet_area, sheet_area_places)} * {panel_count}",
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere die Gesamtfläche mit dem EK pro Quadratmeter.",
                "Gesamtfläche x EK pro Quadratmeter",
                placeholder=f"Zum Beispiel {format_decimal(total_area, total_area_places)} * {format_decimal(ek_price_m2, 2)}",
            ),
            make_guided_step(
                "Gesamter VK",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch den Kostenanteil nach DB.",
                "Gesamter EK / (1 - DB-Satz)",
                placeholder=f"Zum Beispiel {format_decimal(total_ek, 2)} / {format_decimal(divisor, 2)}",
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
        "factor_checks": [
            factor_check(f"Laufmeter {format_decimal(running_meters, running_meters_places)}", running_meters),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Stärke {thickness_text} ({format_decimal(height_m, 3)} Meter)", height_m),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                running_meters / (width_m * height_m),
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast die Laufmeter offenbar durch den Querschnitt geteilt. "
                    "Für Kubikmeter werden Laufmeter, Breite und Stärke gemeinsam multipliziert."
                ),
                "m3",
                round_for_check=False,
            ),
            *ignored_board_length_checks(result.normalize(), board_length, "m3", "Kubikmetern aus Laufmetern"),
        ],
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
        "factor_checks": [
            factor_check(f"Gesamtpreis {format_decimal(total_price, 2)} Euro", total_price),
            factor_check(
                f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro",
                m3_price,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_price * m3_price,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Gesamtpreis offenbar mit dem Kubikmeterpreis multipliziert. "
                    "Wenn aus einem Preis ein Volumen werden soll, muss die Preisbasis herausgeteilt werden."
                ),
                "m3",
                round_for_check=False,
            ),
        ],
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
        "factor_checks": [
            factor_check(f"Volumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            factor_check(f"Dichte {format_decimal(density, 0)} Kilogramm pro Kubikmeter", density),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_volume / density,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast das Volumen offenbar durch die Dichte geteilt. "
                    "Für das Gewicht wird das Volumen mit Kilogramm pro Kubikmeter multipliziert."
                ),
                "kg",
            ),
        ],
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


def task_weight_from_dimensions(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    density = density_for_product(product)
    piece_volume = length_m * width_m * height_m
    total_volume = piece_volume * Decimal(count)
    result = total_volume * density
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"Für eine Lieferung liegen {count} Stück {product['name']} mit je {format_m(length_m)} m Länge sowie {width_text} x {height_text} Querschnitt vor. Die Dichte wird mit {format_decimal(density, 0)} Kilogramm pro Kubikmeter angesetzt. Ein volles Paket hätte {package_count} Stück.\n\nWie schwer ist die Lieferung ungefähr?",
            f"{request_intro()}: {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. Als Dichte werden {format_decimal(density, 0)} Kilogramm pro Kubikmeter angenommen, bei diesem Maß liegen {package_count} Stück im Paket.\n\nWelches Gewicht ergibt sich?",
        ]
    )

    solution = format_solution_steps(
        (
            "Volumen pro Stück",
            "Volumen pro Stück = Länge x Breite x Höhe",
            f"{format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter = "
            f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
        ),
        (
            "Gesamtvolumen",
            "Gesamtvolumen = Volumen pro Stück x Stückzahl",
            f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter x {count} Stück = "
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
        ),
        (
            "Gewicht",
            "Gewicht = Gesamtvolumen x Dichte",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(density, 0)} Kilogramm pro Kubikmeter = "
            f"{format_decimal(result, 2)} Kilogramm",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "kg",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "weight_from_dimensions",
        "correction": "Bestimme zuerst das Volumen aus den konkreten Maßen und der Stückzahl. Danach wird das Gesamtvolumen mit der Dichte weitergerechnet.",
        "solution": solution,
        "perfect_formula": (
            f"{format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x "
            f"{count} x {format_decimal(density, 0)}"
        ),
        "factor_checks": [
            factor_check(f"Länge {format_m(length_m)} Meter", length_m),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", height_m),
            factor_check(f"Stückzahl {count}", Decimal(count)),
            factor_check(f"Dichte {format_decimal(density, 0)} Kilogramm pro Kubikmeter", density),
        ],
        "base_factor_checks": [
            base_factor_check(f"Gesamtvolumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            base_factor_check(f"Dichte {format_decimal(density, 0)} Kilogramm pro Kubikmeter", density),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_volume,
                "Deine Eingabe entspricht auffällig dem Gesamtvolumen. Für das Gewicht fehlt danach noch die Dichte.",
                "kg",
            ),
            wrong_value_check(
                total_volume / density,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast das Volumen offenbar durch die Dichte geteilt. "
                    "Für das Gewicht wird das Volumen mit Kilogramm pro Kubikmeter multipliziert."
                ),
                "kg",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Beginne mit dem Volumen eines einzelnen Stücks.",
                "Länge x Breite x Höhe",
                placeholder=f"Zum Beispiel {format_m(length_m)} * {format_decimal(width_m, 2)} * {format_decimal(height_m, 2)}",
            ),
            make_guided_step(
                "Gesamtvolumen",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Multipliziere das Volumen pro Stück mit der Stückzahl.",
                "Volumen pro Stück x Stückzahl",
                placeholder=f"Zum Beispiel {format_decimal(piece_volume, piece_volume_places)} * {count}",
            ),
            make_guided_step(
                "Gewicht",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "kg",
                2,
                True,
                "Multipliziere das Gesamtvolumen mit der Dichte.",
                "Gesamtvolumen x Dichte",
                placeholder=f"Zum Beispiel {format_decimal(total_volume, total_volume_places)} * {format_decimal(density, 0)}",
            ),
        ],
    }


def task_wood_fiber_insulation_weight(level):
    volume = random.choice(INSULATION_VOLUMES)
    density = WOOD_FIBER_INSULATION_DENSITY
    result = volume * density

    prompt = random.choice(
        [
            (
                f"Ein Dachstuhl soll mit Holzfaser-Einblasdämmung gedämmt werden. "
                f"Der zu füllende Hohlraum hat ein Volumen von {format_decimal(volume, 0)} Kubikmeter. "
                f"Damit die Dämmung setzungssicher eingebaut werden kann, ist eine Rohdichte von "
                f"{format_decimal(density, 0)} Kilogramm pro Kubikmeter erforderlich.\n\n"
                "Wie viele Kilogramm Einblasdämmung werden benötigt?"
            ),
            (
                f"Für eine Holzfaser-Einblasdämmung müssen {format_decimal(volume, 0)} Kubikmeter Hohlraum "
                f"gefüllt werden. Vorgegeben ist eine setzungssichere Rohdichte von "
                f"{format_decimal(density, 0)} Kilogramm pro Kubikmeter.\n\n"
                "Welche Dämmstoffmenge in Kilogramm wird gebraucht?"
            ),
            (
                f"Bei einer Baustelle sind {format_decimal(volume, 0)} Kubikmeter Gefach mit "
                f"Holzfaser-Einblasdämmung zu füllen. Die Rohdichte bleibt bei "
                f"{format_decimal(density, 0)} Kilogramm pro Kubikmeter.\n\n"
                "Wie viel Kilogramm Material müssen eingeplant werden?"
            ),
        ]
    )

    solution = format_solution_steps(
        (
            "Benötigte Dämmstoffmenge",
            "Kilogramm = Kubikmeter x Rohdichte",
            f"{format_decimal(volume, 0)} Kubikmeter x "
            f"{format_decimal(density, 0)} Kilogramm pro Kubikmeter = {format_decimal(result, 0)} Kilogramm",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result,
        "unit": "kg",
        "display_places": 0,
        "round_for_check": True,
        "task_type": "wood_fiber_insulation_weight",
        "correction": (
            "Bei Einblasdämmung ist die Rohdichte der feste Faktor pro Kubikmeter. "
            "Du rechnest das zu füllende Volumen mit 40 Kilogramm pro Kubikmeter weiter."
        ),
        "solution": solution,
        "perfect_formula": f"{format_decimal(volume, 0)} x {format_decimal(density, 0)}",
        "factor_checks": [
            factor_check(f"Volumen {format_decimal(volume, 0)} Kubikmeter", volume),
            factor_check(f"Rohdichte {format_decimal(density, 0)} Kilogramm pro Kubikmeter", density),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                volume / density,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast das Volumen offenbar durch die Rohdichte geteilt. "
                    "Für die benötigte Dämmstoffmenge wird das Volumen mit 40 Kilogramm pro Kubikmeter multipliziert."
                ),
                "kg",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Benötigte Dämmstoffmenge",
                result,
                "kg",
                0,
                True,
                "Multipliziere das Volumen des Hohlraums mit der Rohdichte.",
                "Kubikmeter x Rohdichte",
                placeholder="Zum Beispiel 18 * 40",
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
        "factor_checks": [
            factor_check(f"Laufmeterpreis {format_decimal(price_per_lfm, 2)} Euro", price_per_lfm),
            factor_check(
                f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)",
                width_m,
                missing_when_ratio_is_value=True,
            ),
            factor_check(
                f"Stärke {thickness_text} ({format_decimal(height_m, 3)} Meter)",
                height_m,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                price_per_lfm * cross_section,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Laufmeterpreis offenbar mit dem Querschnitt multipliziert. "
                    "Für Euro pro Kubikmeter muss der Laufmeterpreis auf einen ganzen Kubikmeter hochgerechnet werden."
                ),
                "EUR",
            ),
        ],
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


def task_running_meter_price_from_square_meter(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    m2_price = choice_for_level(PANEL_M2_PRICES_BY_LEVEL, level)
    result = m2_price * width_m
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Der Preis liegt bei {format_decimal(m2_price, 2)} Euro pro Quadratmeter, die Ware ist {width_text} breit, {thickness_text} stark und ein Brett ist {format_m(board_length)} m lang.\n\nWie teuer ist 1 Laufmeter?",
            f"Für {display_name} soll ein Quadratmeterpreis von {format_decimal(m2_price, 2)} Euro auf Laufmeter umgerechnet werden. Die Bretter sind {width_text} breit, {thickness_text} stark und je {format_m(board_length)} m lang.\n\nWie hoch ist der Laufmeterpreis?",
        ]
    )

    solution = format_solution_steps(
        (
            "Preis je Laufmeter",
            "Euro pro Laufmeter = Euro pro Quadratmeter x Breite",
            f"{format_decimal(m2_price, 2)} Euro pro Quadratmeter x {format_decimal(width_m, 2)} Meter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "running_meter_price_from_square_meter",
        "correction": "Für den Laufmeterpreis aus dem Quadratmeterpreis brauchst du nur die Breite. Die Brettlänge und die Stärke sind hier Zusatzinformationen.",
        "solution": solution,
        "perfect_formula": f"{format_decimal(m2_price, 2)} x {format_decimal(width_m, 2)}",
        "factor_checks": [
            factor_check(f"Quadratmeterpreis {format_decimal(m2_price, 2)} Euro", m2_price),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                m2_price / width_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Quadratmeterpreis offenbar durch die Breite geteilt. "
                    "Bei Euro pro Laufmeter wird aus einem Streifen von einem Meter Länge die Fläche über die Breite gebildet."
                ),
                "EUR",
            ),
            *ignored_board_length_checks(
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                board_length,
                "EUR",
                "dem Preis je Laufmeter",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Preis je Laufmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den Quadratmeterpreis mit der Breite in Metern.",
                "Quadratmeterpreis x Breite",
                placeholder=f"Zum Beispiel {format_decimal(m2_price, 2)} * {format_decimal(width_m, 2)}",
            ),
        ],
    }


def task_square_meter_price_from_running_meter(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    price_per_lfm = choice_for_level(RUNNING_METER_PRICES_BY_LEVEL, level)
    result = price_per_lfm / width_m
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Ein Laufmeter {display_name} kostet {format_decimal(price_per_lfm, 2)} Euro. Die Ware ist {width_text} breit, {thickness_text} stark und ein Brett ist {format_m(board_length)} m lang.\n\nWie hoch ist der Preis pro Quadratmeter?",
            f"Für {display_name} liegt ein Laufmeterpreis von {format_decimal(price_per_lfm, 2)} Euro vor. Die Bretter sind {width_text} breit, {thickness_text} stark und je {format_m(board_length)} m lang.\n\nWie teuer ist 1 Quadratmeter?",
        ]
    )

    solution = format_solution_steps(
        (
            "Preis je Quadratmeter",
            "Euro pro Quadratmeter = Euro pro Laufmeter / Breite",
            f"{format_decimal(price_per_lfm, 2)} Euro pro Laufmeter / {format_decimal(width_m, 2)} Meter = "
            f"{format_decimal(result, 2)} Euro pro Quadratmeter",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "square_meter_price_from_running_meter",
        "correction": "Rechne vom Laufmeterpreis auf den Quadratmeterpreis zurück. Dafür teilst du durch die Breite in Metern; Länge und Stärke sind hier nicht die Preisbasis.",
        "solution": solution,
        "perfect_formula": f"{format_decimal(price_per_lfm, 2)} / {format_decimal(width_m, 2)}",
        "factor_checks": [
            factor_check(f"Laufmeterpreis {format_decimal(price_per_lfm, 2)} Euro", price_per_lfm),
            factor_check(
                f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)",
                width_m,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                price_per_lfm * width_m,
                (
                    "Deine Eingabe wirkt wie die Gegenrichtung: Du hast den Laufmeterpreis offenbar mit der Breite multipliziert. "
                    "Für Euro pro Quadratmeter muss der Laufmeterpreis auf einen ganzen Quadratmeter hochgerechnet werden."
                ),
                "EUR",
            ),
            *ignored_board_length_checks(
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                board_length,
                "EUR",
                "dem Preis je Quadratmeter",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Preis je Quadratmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den Laufmeterpreis durch die Breite in Metern.",
                "Laufmeterpreis / Breite",
                placeholder=f"Zum Beispiel {format_decimal(price_per_lfm, 2)} / {format_decimal(width_m, 2)}",
            ),
        ],
    }


def task_lfm_price_from_m3_with_db(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    cross_section = width_m * height_m
    ek_lfm = cross_section * ek_price_m3
    result = ek_lfm / divisor
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Der EK beträgt {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter. Die Ware ist {width_text} breit, {thickness_text} stark und {format_m(board_length)} m lang. Der Ziel-DB liegt bei {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der VK pro Laufmeter?",
            f"Für {display_name} soll aus einem EK von {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter ein Laufmeter-VK kalkuliert werden. Querschnitt: {width_text} x {thickness_text}, Brettlänge {format_m(board_length)} m, Ziel-DB {format_decimal(db_percent, 0)} %.\n\nWie teuer ist 1 Laufmeter im VK?",
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
            "EK je Laufmeter",
            "EK je Laufmeter = Querschnitt x EK pro Kubikmeter",
            f"{format_decimal(cross_section, 5)} Quadratmeter x {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(ek_lfm, 2)} Euro",
        ),
        (
            "VK je Laufmeter",
            "VK je Laufmeter = EK je Laufmeter / (1 - DB-Satz)",
            f"{format_decimal(ek_lfm, 2)} Euro / {format_decimal(divisor, 2)} = {format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "lfm_price_from_m3_with_db",
        "correction": "Baue zuerst den EK je Laufmeter aus Querschnitt und Kubikmeterpreis auf. Erst danach wird der Ziel-DB auf den Laufmeterpreis gerechnet.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(width_m, 2)} x {format_decimal(height_m, 3)} x "
            f"{format_decimal(ek_price_m3, 0)} / {format_decimal(divisor, 2)}"
        ),
        "factor_checks": [
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Stärke {thickness_text} ({format_decimal(height_m, 3)} Meter)", height_m),
            factor_check(f"Kubikmeterpreis {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"EK je Laufmeter {format_decimal(ek_lfm, 2)} Euro", ek_lfm),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                ek_lfm,
                "Deine Eingabe entspricht dem EK je Laufmeter. Für den VK fehlt danach noch der Ziel-DB.",
                "EUR",
            ),
            wrong_value_check(
                ek_lfm * (Decimal("1") + db_percent / Decimal("100")),
                "Deine Eingabe wirkt wie ein einfacher Aufschlag auf den EK. Ein Ziel-DB wird aber vom Verkaufspreis aus betrachtet.",
                "EUR",
            ),
            *db_wrong_factor_checks(ek_lfm, db_percent, divisor, "sale_price"),
            *ignored_board_length_checks(
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                board_length,
                "EUR",
                "dem VK pro Laufmeter",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                cross_section.normalize(),
                "m2",
                5,
                False,
                "Rechne zuerst Breite x Stärke mit Meterwerten.",
                "Breite x Stärke",
                placeholder=f"Zum Beispiel {format_decimal(width_m, 2)} * {format_decimal(height_m, 3)}",
            ),
            make_guided_step(
                "EK je Laufmeter",
                ek_lfm.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den Querschnitt mit dem EK pro Kubikmeter.",
                "Querschnitt x EK pro Kubikmeter",
                placeholder=f"Zum Beispiel {format_decimal(cross_section, 5)} * {format_decimal(ek_price_m3, 0)}",
            ),
            make_guided_step(
                "VK je Laufmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den EK je Laufmeter durch den Kostenanteil nach DB.",
                "EK je Laufmeter / (1 - DB-Satz)",
                placeholder=f"Zum Beispiel {format_decimal(ek_lfm, 2)} / {format_decimal(divisor, 2)}",
            ),
        ],
    }


def task_m2_price_from_m3_with_db(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    thickness_m = panel_thickness_for_product(product, level)
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    ek_m2 = thickness_m * ek_price_m3
    result = ek_m2 / divisor
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Eine {product['name']} im Format {panel_format} ist {thickness_text} dick. Der EK beträgt {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter, Ziel-DB {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der VK pro Quadratmeter?",
            f"Für eine {product['name']} im Format {panel_format} soll aus {format_decimal(ek_price_m3, 0)} Euro EK pro Kubikmeter ein Quadratmeter-VK mit {format_decimal(db_percent, 0)} % DB kalkuliert werden. Die Platte ist {thickness_text} dick.\n\nWie teuer ist 1 Quadratmeter im VK?",
        ]
    )

    solution = format_solution_steps(
        (
            "EK je Quadratmeter",
            "EK je Quadratmeter = EK pro Kubikmeter x Dicke",
            f"{format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter x {format_decimal(thickness_m, 3)} Meter = "
            f"{format_decimal(ek_m2, 2)} Euro",
        ),
        (
            "VK je Quadratmeter",
            "VK je Quadratmeter = EK je Quadratmeter / (1 - DB-Satz)",
            f"{format_decimal(ek_m2, 2)} Euro / {format_decimal(divisor, 2)} = {format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "m2_price_from_m3_with_db",
        "correction": "Rechne zuerst den EK pro Quadratmeter über die Dicke aus dem Kubikmeterpreis. Danach kalkulierst du den VK mit dem Ziel-DB.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(ek_price_m3, 0)} x {format_decimal(thickness_m, 3)} / {format_decimal(divisor, 2)}"
        ),
        "factor_checks": [
            factor_check(f"Dicke {thickness_text} ({format_decimal(thickness_m, 3)} Meter)", thickness_m),
            factor_check(f"Kubikmeterpreis {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"EK je Quadratmeter {format_decimal(ek_m2, 2)} Euro", ek_m2),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                ek_m2,
                "Deine Eingabe entspricht dem EK je Quadratmeter. Für den VK fehlt danach noch der Ziel-DB.",
                "EUR",
            ),
            wrong_value_check(
                ek_m2 * (Decimal("1") + db_percent / Decimal("100")),
                "Deine Eingabe wirkt wie ein einfacher Aufschlag auf den EK. Ein Ziel-DB wird aber vom Verkaufspreis aus betrachtet.",
                "EUR",
            ),
            *db_wrong_factor_checks(ek_m2, db_percent, divisor, "sale_price"),
        ],
        "guided_steps": [
            make_guided_step(
                "EK je Quadratmeter",
                ek_m2.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den Kubikmeterpreis mit der Dicke in Metern.",
                "EK pro Kubikmeter x Dicke",
                placeholder=f"Zum Beispiel {format_decimal(ek_price_m3, 0)} * {format_decimal(thickness_m, 3)}",
            ),
            make_guided_step(
                "VK je Quadratmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den EK je Quadratmeter durch den Kostenanteil nach DB.",
                "EK je Quadratmeter / (1 - DB-Satz)",
                placeholder=f"Zum Beispiel {format_decimal(ek_m2, 2)} / {format_decimal(divisor, 2)}",
            ),
        ],
    }


def task_ek_from_vk_db(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
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
            f"Für {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} wurde dem Kunden ein Gesamt-VK von {format_decimal(total_vk, 2)} Euro angeboten. Im Ergebnis sollen {format_decimal(db_percent, 0)} % DB enthalten sein; ein Paket in diesem Maß enthält {package_count} Stück.\n\nWelcher gesamte Lieferanten-EK steckt in dieser Position?",
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
        "factor_checks": [
            factor_check(f"DB-Faktor {format_decimal(divisor, 2)} bei {format_decimal(db_percent, 0)} % DB", divisor),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_vk,
                "Deine Eingabe entspricht auffällig dem VK. Gefragt ist aber der EK, also der Anteil, der nach Abzug des DB-Anteils als Kostenanteil übrig bleibt.",
                "EUR",
            ),
            wrong_value_check(
                total_vk / divisor,
                (
                    f"Deine Eingabe wirkt so, als hättest du den VK durch den DB-Faktor {format_decimal(divisor, 2)} geteilt. "
                    "Bei der Rückwärtsrechnung vom VK zum EK wird der VK mit diesem Faktor multipliziert."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_vk * db_percent,
                (
                    f"Deine Eingabe wirkt so, als wäre der Prozentwert {format_decimal(db_percent, 0)} direkt als Faktor verwendet worden. "
                    f"Für die Rückwärtsrechnung brauchst du den DB-Faktor {format_decimal(divisor, 2)}."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_vk, db_percent, divisor, "ek_from_vk"),
        ],
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


def task_m3_ek_from_vk_db(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    db_percent = db_percent_for_product(product, level)
    ek_price_m3 = m3_price_for_product(product, level)

    piece_volume = length_m * width_m * height_m
    total_volume = piece_volume * Decimal(count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_vk = total_ek / divisor
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"Für {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} wurde ein Gesamt-VK von {format_decimal(total_vk, 2)} Euro angeboten. Der DB beträgt {format_decimal(db_percent, 0)} %. Bei diesem Querschnitt liegen {package_count} Stück im Paket.\n\nWie viel Euro pro Kubikmeter hat der Lieferant rechnerisch im EK berechnet?",
            f"Ein Kundenauftrag über {count} Stück {product['name']} im Maß {format_m(length_m)} m x {width_text} x {height_text} endet bei {format_decimal(total_vk, 2)} Euro Gesamt-VK. Aus der Kalkulation sollen {format_decimal(db_percent, 0)} % DB übrig bleiben.\n\nWelcher EK pro Kubikmeter steckt dahinter?",
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
            "Gesamter EK = VK x (1 - DB-Satz)",
            f"{format_decimal(total_vk, 2)} Euro x {format_decimal(divisor, 2)} = {format_decimal(total_ek, 2)} Euro",
        ),
        (
            "EK pro Kubikmeter",
            "EK pro Kubikmeter = gesamter EK / Gesamtvolumen",
            f"{format_decimal(total_ek, 2)} Euro / {format_decimal(total_volume, total_volume_places)} Kubikmeter = "
            f"{format_decimal(ek_price_m3, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": ek_price_m3.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "m3_ek_from_vk_db",
        "correction": "Rechne zuerst das Gesamtvolumen aus. Dann führst du den VK über den DB-Faktor auf den gesamten EK zurück und teilst diesen EK durch die Kubikmeter.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(total_vk, 2)} x {format_decimal(divisor, 2)} / "
            f"({format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x {count})"
        ),
        "factor_checks": [
            factor_check(f"Länge {format_m(length_m)} Meter", length_m),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", height_m),
            factor_check(f"Stückzahl {count}", Decimal(count)),
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            db_factor_check(db_percent, divisor),
            factor_check(
                f"Gesamtvolumen {format_decimal(total_volume, total_volume_places)} Kubikmeter",
                total_volume,
                missing_when_ratio_is_value=True,
            ),
        ],
        "base_factor_checks": [
            base_factor_check(f"Gesamter EK {format_decimal(total_ek, 2)} Euro", total_ek),
            base_factor_check(f"Gesamtvolumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_vk / total_volume,
                "Deine Eingabe wirkt wie der VK pro Kubikmeter. Für den EK pro Kubikmeter muss zuerst der DB aus dem VK herausgerechnet werden.",
                "EUR",
            ),
            wrong_value_check(
                total_vk / divisor / total_volume,
                (
                    f"Deine Eingabe wirkt so, als hättest du den VK durch den DB-Faktor {format_decimal(divisor, 2)} geteilt. "
                    "Bei der Rückwärtsrechnung vom VK zum EK wird mit diesem Faktor multipliziert."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_vk / total_volume, db_percent, divisor, "ek_from_vk"),
        ],
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                piece_volume.normalize(),
                "m3",
                piece_volume_places,
                False,
                "Rechne zuerst Länge x Breite x Höhe für ein einzelnes Stück.",
                "Länge x Breite x Höhe",
                placeholder=f"Zum Beispiel {format_m(length_m)} * {format_decimal(width_m, 2)} * {format_decimal(height_m, 2)}",
            ),
            make_guided_step(
                "Gesamtvolumen",
                total_volume.normalize(),
                "m3",
                total_volume_places,
                False,
                "Multipliziere danach das Volumen pro Stück mit der Stückzahl.",
                "Volumen pro Stück x Stückzahl",
                placeholder=f"Zum Beispiel {format_decimal(piece_volume, piece_volume_places)} * {count}",
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den VK mit dem DB-Faktor.",
                "VK x DB-Faktor",
                placeholder=f"Zum Beispiel {format_decimal(total_vk, 2)} * {format_decimal(divisor, 2)}",
            ),
            make_guided_step(
                "EK pro Kubikmeter",
                ek_price_m3.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch das Gesamtvolumen.",
                "Gesamter EK / Gesamtvolumen",
                placeholder=f"Zum Beispiel {format_decimal(total_ek, 2)} / {format_decimal(total_volume, total_volume_places)}",
            ),
        ],
    }


def task_lfm_ek_from_vk_db(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = board_count_for_level(level)
    running_meters = board_length * Decimal(board_count)
    ek_price_lfm = choice_for_level(RUNNING_METER_PRICES_BY_LEVEL, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_ek = running_meters * ek_price_lfm
    total_vk = total_ek / divisor
    running_meters_places = precise_decimal_places(running_meters, 0, 1)
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Ein Angebot über {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name} endet bei {format_decimal(total_vk, 2)} Euro VK. Die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark. Kalkuliert wurde mit {format_decimal(db_percent, 0)} % DB.\n\nWie hoch ist der EK pro Laufmeter?",
            f"{request_intro()}: {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name}. Der gesamte VK beträgt {format_decimal(total_vk, 2)} Euro, der DB liegt bei {format_decimal(db_percent, 0)} %. Ein Brett ist {format_m(board_length)} m lang.\n\nWelcher EK pro Laufmeter steckt dahinter?",
            f"Für {format_decimal(running_meters, running_meters_places)} Laufmeter {display_name} wurde dem Kunden ein Gesamt-VK von {format_decimal(total_vk, 2)} Euro genannt. In der Kalkulation sind {format_decimal(db_percent, 0)} % DB vorgesehen; die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWelchen Laufmeter-EK hat der Lieferant rechnerisch berechnet?",
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
            "Gesamter EK = VK x DB-Faktor",
            f"{format_decimal(total_vk, 2)} Euro x {format_decimal(divisor, 2)} = "
            f"{format_decimal(total_ek, 2)} Euro",
        ),
        (
            "EK pro Laufmeter",
            "EK pro Laufmeter = gesamter EK / Laufmeter",
            f"{format_decimal(total_ek, 2)} Euro / {format_decimal(running_meters, running_meters_places)} Laufmeter = "
            f"{format_decimal(ek_price_lfm, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": ek_price_lfm.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "lfm_ek_from_vk_db",
        "correction": "Rechne zuerst vom VK mit dem DB-Faktor auf den gesamten EK zurück. Danach teilst du den gesamten EK durch die Laufmeter.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(total_vk, 2)} x {format_decimal(divisor, 2)} / "
            f"{format_decimal(running_meters, running_meters_places)}"
        ),
        "factor_checks": [
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            db_factor_check(db_percent, divisor),
            factor_check(
                f"Laufmeter {format_decimal(running_meters, running_meters_places)}",
                running_meters,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_vk / running_meters,
                "Deine Eingabe wirkt wie der VK pro Laufmeter. Gefragt ist aber der EK pro Laufmeter nach Rückrechnung über den DB.",
                "EUR",
            ),
            wrong_value_check(
                total_vk / divisor / running_meters,
                (
                    f"Deine Eingabe wirkt so, als hättest du den VK durch den DB-Faktor {format_decimal(divisor, 2)} geteilt. "
                    "Bei der Rückwärtsrechnung vom VK zum EK wird mit diesem Faktor multipliziert."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_vk / running_meters, db_percent, divisor, "ek_from_vk"),
        ],
        "guided_steps": [
            make_guided_step(
                "DB-Faktor",
                divisor.normalize(),
                "Faktor",
                2,
                False,
                "Ziehe den DB-Satz von 1 ab.",
                "1 - DB-Satz",
                placeholder=f"Zum Beispiel 1 - 0,{format_decimal(db_percent, 0)}",
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den VK mit dem DB-Faktor.",
                "VK x DB-Faktor",
                placeholder=f"Zum Beispiel {format_decimal(total_vk, 2)} * {format_decimal(divisor, 2)}",
            ),
            make_guided_step(
                "EK pro Laufmeter",
                ek_price_lfm.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch die Laufmeter.",
                "Gesamter EK / Laufmeter",
                placeholder=f"Zum Beispiel {format_decimal(total_ek, 2)} / {format_decimal(running_meters, running_meters_places)}",
            ),
        ],
    }


def task_m2_ek_from_vk_db(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    panel_count = panel_count_for_level(level)
    ek_price_m2 = panel_m2_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")

    sheet_area = length_m * width_m
    total_area = sheet_area * Decimal(panel_count)
    total_ek = total_area * ek_price_m2
    total_vk = total_ek / divisor
    sheet_area_places = precise_decimal_places(sheet_area)
    total_area_places = precise_decimal_places(total_area)

    prompt = random.choice(
        [
            f"Ein Angebot über {panel_count} Platten {product['name']} im Format {panel_format} endet bei {format_decimal(total_vk, 2)} Euro VK. Kalkuliert wurde mit {format_decimal(db_percent, 0)} % DB.\n\nWie hoch ist der EK pro Quadratmeter?",
            f"Für {product['name']} liegen {panel_count} Stück im Format {panel_format} vor. Der Gesamt-VK beträgt {format_decimal(total_vk, 2)} Euro, der DB liegt bei {format_decimal(db_percent, 0)} %.\n\nWelcher EK pro Quadratmeter steckt dahinter?",
            f"Ein Kundenangebot über {panel_count} Platten {product['name']} im Format {panel_format} hat einen Gesamt-VK von {format_decimal(total_vk, 2)} Euro. Intern soll dabei ein DB von {format_decimal(db_percent, 0)} % erreicht werden.\n\nWelchen Quadratmeter-EK hat der Lieferant rechnerisch angesetzt?",
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
            "Gesamtfläche",
            "Gesamtfläche = Fläche pro Platte x Plattenanzahl",
            f"{format_decimal(sheet_area, sheet_area_places)} Quadratmeter x {panel_count} Stück = "
            f"{format_decimal(total_area, total_area_places)} Quadratmeter",
        ),
        (
            "DB-Faktor",
            "DB-Faktor = 1 - DB-Satz",
            f"1 - {format_decimal(db_percent, 0)} % = {format_decimal(divisor, 2)}",
        ),
        (
            "Gesamter EK",
            "Gesamter EK = VK x DB-Faktor",
            f"{format_decimal(total_vk, 2)} Euro x {format_decimal(divisor, 2)} = "
            f"{format_decimal(total_ek, 2)} Euro",
        ),
        (
            "EK pro Quadratmeter",
            "EK pro Quadratmeter = gesamter EK / Gesamtfläche",
            f"{format_decimal(total_ek, 2)} Euro / {format_decimal(total_area, total_area_places)} Quadratmeter = "
            f"{format_decimal(ek_price_m2, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": ek_price_m2.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "m2_ek_from_vk_db",
        "correction": "Rechne zuerst die Gesamtfläche aus. Danach gehst du vom VK über den DB-Faktor auf den gesamten EK zurück und teilst durch die Quadratmeter.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(total_vk, 2)} x {format_decimal(divisor, 2)} / "
            f"({format_decimal(length_m, 2)} x {format_decimal(width_m, 3)} x {panel_count})"
        ),
        "factor_checks": [
            factor_check(f"Länge {format_decimal(length_m, 2)} Meter", length_m),
            factor_check(f"Breite {format_decimal(width_m, 3)} Meter", width_m),
            factor_check(f"Plattenanzahl {panel_count}", Decimal(panel_count)),
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            db_factor_check(db_percent, divisor),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_vk / total_area,
                "Deine Eingabe wirkt wie der VK pro Quadratmeter. Gefragt ist aber der EK pro Quadratmeter nach Rückrechnung über den DB.",
                "EUR",
            ),
            wrong_value_check(
                total_vk / divisor / total_area,
                (
                    f"Deine Eingabe wirkt so, als hättest du den VK durch den DB-Faktor {format_decimal(divisor, 2)} geteilt. "
                    "Bei der Rückwärtsrechnung vom VK zum EK wird mit diesem Faktor multipliziert."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_vk / total_area, db_percent, divisor, "ek_from_vk"),
        ],
        "guided_steps": [
            make_guided_step(
                "Fläche pro Platte",
                sheet_area.normalize(),
                "m2",
                sheet_area_places,
                False,
                "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                "Länge x Breite",
                placeholder=f"Zum Beispiel {format_decimal(length_m, 2)} * {format_decimal(width_m, 3)}",
            ),
            make_guided_step(
                "Gesamtfläche",
                total_area.normalize(),
                "m2",
                total_area_places,
                False,
                "Multipliziere die Fläche pro Platte mit der Plattenanzahl.",
                "Fläche pro Platte x Plattenanzahl",
                placeholder=f"Zum Beispiel {format_decimal(sheet_area, sheet_area_places)} * {panel_count}",
            ),
            make_guided_step(
                "DB-Faktor",
                divisor.normalize(),
                "Faktor",
                2,
                False,
                "Ziehe den DB-Satz von 1 ab.",
                "1 - DB-Satz",
                placeholder=f"Zum Beispiel 1 - 0,{format_decimal(db_percent, 0)}",
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den VK mit dem DB-Faktor.",
                "VK x DB-Faktor",
                placeholder=f"Zum Beispiel {format_decimal(total_vk, 2)} * {format_decimal(divisor, 2)}",
            ),
            make_guided_step(
                "EK pro Quadratmeter",
                ek_price_m2.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch die Gesamtfläche.",
                "Gesamter EK / Gesamtfläche",
                placeholder=f"Zum Beispiel {format_decimal(total_ek, 2)} / {format_decimal(total_area, total_area_places)}",
            ),
        ],
    }


def task_package_price(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
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
        "factor_checks": [
            factor_check(f"Länge {format_m(length_m)} Meter", length_m),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", height_m),
            factor_check(f"Paketstückzahl {package_count}", Decimal(package_count)),
            factor_check(f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro", m3_price),
        ],
        "base_factor_checks": [
            base_factor_check(f"Paketvolumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            base_factor_check(f"Kubikmeterpreis {format_decimal(m3_price, 0)} Euro", m3_price),
        ],
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
        "factor_checks": [
            factor_check(f"Länge {format_decimal(length_m, 2)} Meter", length_m),
            factor_check(f"Breite {format_decimal(width_m, 3)} Meter", width_m),
            factor_check(f"Plattenanzahl {package_count}", Decimal(package_count)),
            factor_check(f"Quadratmeterpreis {format_decimal(m2_price, 2)} Euro", m2_price),
        ],
        "base_factor_checks": [
            base_factor_check(f"Paketfläche {format_decimal(package_area, package_area_places)} Quadratmeter", package_area),
            base_factor_check(f"Quadratmeterpreis {format_decimal(m2_price, 2)} Euro", m2_price),
        ],
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


def task_panel_package_db_sale_price(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    package_count = panel_package_count(product)
    ek_price_m2 = panel_m2_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")

    sheet_area = length_m * width_m
    package_area = sheet_area * Decimal(package_count)
    package_ek = package_area * ek_price_m2
    result = package_ek / divisor
    sheet_area_places = precise_decimal_places(sheet_area)
    package_area_places = precise_decimal_places(package_area)

    prompt = random.choice(
        [
            f"Für ein Angebot soll ein Plattenpaket {product['name']} kalkuliert werden. Eine Platte hat das Format {panel_format}, im Paket liegen {package_count} Platten. Der EK beträgt {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter, Ziel-DB {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der Paket-VK?",
            f"Eine Kundin interessiert sich für ein komplettes Paket {product['name']} im Format {panel_format}. Enthalten sind {package_count} Platten, der EK liegt bei {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter und es soll ein DB von {format_decimal(db_percent, 0)} % erzielt werden.\n\nWie hoch ist der Verkaufspreis für das Paket?",
            f"Der Lieferant bietet ein Paket {product['name']} im Format {panel_format} zu {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter EK an. Im Paket liegen {package_count} Platten, im Kundenangebot sollen mindestens {format_decimal(db_percent, 0)} % DB erreicht werden.\n\nZu welchem Mindestpreis können wir das Paket verkaufen?",
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
            "Paket-EK",
            "Paket-EK = Paketfläche x EK pro Quadratmeter",
            f"{format_decimal(package_area, package_area_places)} Quadratmeter x {format_decimal(ek_price_m2, 2)} Euro pro Quadratmeter = "
            f"{format_decimal(package_ek, 2)} Euro",
        ),
        (
            "Paket-VK",
            "Paket-VK = Paket-EK / (1 - DB-Satz)",
            f"{format_decimal(package_ek, 2)} Euro / {format_decimal(divisor, 2)} = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "panel_package_db_sale_price",
        "correction": "Rechne zuerst die Fläche pro Platte, dann die Paketfläche und den Paket-EK. Erst danach wird der Ziel-DB auf den Paket-VK umgerechnet.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(length_m, 2)} x {format_decimal(width_m, 3)} x {package_count} x "
            f"{format_decimal(ek_price_m2, 2)} / {format_decimal(divisor, 2)}"
        ),
        "factor_checks": [
            factor_check(f"Länge {format_decimal(length_m, 2)} Meter", length_m),
            factor_check(f"Breite {format_decimal(width_m, 3)} Meter", width_m),
            factor_check(f"Plattenanzahl {package_count}", Decimal(package_count)),
            factor_check(f"EK pro Quadratmeter {format_decimal(ek_price_m2, 2)} Euro", ek_price_m2),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"Paketfläche {format_decimal(package_area, package_area_places)} Quadratmeter", package_area),
            base_factor_check(f"EK pro Quadratmeter {format_decimal(ek_price_m2, 2)} Euro", ek_price_m2),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                package_ek,
                "Deine Eingabe entspricht auffällig dem Paket-EK. Für den Paket-VK fehlt danach noch der Ziel-DB.",
                "EUR",
            ),
            wrong_value_check(
                package_ek * (Decimal("1") + db_percent / Decimal("100")),
                "Deine Eingabe wirkt wie ein einfacher Aufschlag auf den EK. Ein Ziel-DB wird aber vom Verkaufspreis aus betrachtet.",
                "EUR",
            ),
            *db_wrong_factor_checks(package_ek, db_percent, divisor, "sale_price"),
        ],
        "guided_steps": [
            make_guided_step(
                "Fläche pro Platte",
                sheet_area.normalize(),
                "m2",
                sheet_area_places,
                False,
                "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                "Länge x Breite",
                placeholder=f"Zum Beispiel {format_decimal(length_m, 2)} * {format_decimal(width_m, 3)}",
            ),
            make_guided_step(
                "Paketfläche",
                package_area.normalize(),
                "m2",
                package_area_places,
                False,
                "Multipliziere die Fläche pro Platte mit der Plattenanzahl im Paket.",
                "Fläche pro Platte x Plattenanzahl",
                placeholder=f"Zum Beispiel {format_decimal(sheet_area, sheet_area_places)} * {package_count}",
            ),
            make_guided_step(
                "Paket-EK",
                package_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere die Paketfläche mit dem EK pro Quadratmeter.",
                "Paketfläche x EK pro Quadratmeter",
                placeholder=f"Zum Beispiel {format_decimal(package_area, package_area_places)} * {format_decimal(ek_price_m2, 2)}",
            ),
            make_guided_step(
                "Paket-VK",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den Paket-EK durch den Kostenanteil nach DB.",
                "Paket-EK / (1 - DB-Satz)",
                placeholder=f"Zum Beispiel {format_decimal(package_ek, 2)} / {format_decimal(divisor, 2)}",
            ),
        ],
    }


def task_panel_package_ek_from_vk_db(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    package_count = panel_package_count(product)
    ek_price_m2 = panel_m2_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")

    sheet_area = length_m * width_m
    package_area = sheet_area * Decimal(package_count)
    package_ek = package_area * ek_price_m2
    package_vk = package_ek / divisor
    result = ek_price_m2
    sheet_area_places = precise_decimal_places(sheet_area)
    package_area_places = precise_decimal_places(package_area)

    prompt = random.choice(
        [
            f"Ein Plattenpaket {product['name']} im Format {panel_format} wurde für {format_decimal(package_vk, 2)} Euro verkauft. Im Paket liegen {package_count} Platten und der DB beträgt {format_decimal(db_percent, 0)} %.\n\nWie hoch war der EK pro Quadratmeter?",
            f"Für ein Paket {product['name']} mit {package_count} Platten im Format {panel_format} liegt ein VK von {format_decimal(package_vk, 2)} Euro vor. Kalkuliert wurde mit {format_decimal(db_percent, 0)} % DB.\n\nWelcher EK pro Quadratmeter steckt dahinter?",
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
            "Paket-EK",
            "Paket-EK = Paket-VK x (1 - DB-Satz)",
            f"{format_decimal(package_vk, 2)} Euro x {format_decimal(divisor, 2)} = {format_decimal(package_ek, 2)} Euro",
        ),
        (
            "EK pro Quadratmeter",
            "EK pro Quadratmeter = Paket-EK / Paketfläche",
            f"{format_decimal(package_ek, 2)} Euro / {format_decimal(package_area, package_area_places)} Quadratmeter = "
            f"{format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "panel_package_ek_from_vk_db",
        "correction": "Rechne zuerst den VK über den DB-Faktor auf den Paket-EK zurück. Danach verteilst du den Paket-EK auf die Paketfläche.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(package_vk, 2)} x {format_decimal(divisor, 2)} / "
            f"({format_decimal(length_m, 2)} x {format_decimal(width_m, 3)} x {package_count})"
        ),
        "factor_checks": [
            factor_check(f"Paket-VK {format_decimal(package_vk, 2)} Euro", package_vk),
            db_factor_check(db_percent, divisor),
            factor_check(
                f"Paketfläche {format_decimal(package_area, package_area_places)} Quadratmeter",
                package_area,
                missing_when_ratio_is_value=True,
            ),
        ],
        "base_factor_checks": [
            base_factor_check(f"Paket-VK {format_decimal(package_vk, 2)} Euro", package_vk),
            base_factor_check(f"DB-Faktor {format_decimal(divisor, 2)}", divisor),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                package_vk / package_area,
                "Deine Eingabe wirkt so, als hättest du den VK direkt auf die Paketfläche verteilt. Für den EK muss zuerst der DB herausgerechnet werden.",
                "EUR",
            ),
            wrong_value_check(
                package_vk / divisor / package_area,
                "Deine Eingabe wirkt wie die Gegenrichtung beim DB: Du hast den VK offenbar noch weiter hochgerechnet statt auf den EK zurückzurechnen.",
                "EUR",
            ),
            *db_wrong_factor_checks(package_vk / package_area, db_percent, divisor, "ek_from_vk"),
        ],
        "guided_steps": [
            make_guided_step(
                "Fläche pro Platte",
                sheet_area.normalize(),
                "m2",
                sheet_area_places,
                False,
                "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                "Länge x Breite",
                placeholder=f"Zum Beispiel {format_decimal(length_m, 2)} * {format_decimal(width_m, 3)}",
            ),
            make_guided_step(
                "Paketfläche",
                package_area.normalize(),
                "m2",
                package_area_places,
                False,
                "Multipliziere die Fläche pro Platte mit der Plattenanzahl im Paket.",
                "Fläche pro Platte x Plattenanzahl",
                placeholder=f"Zum Beispiel {format_decimal(sheet_area, sheet_area_places)} * {package_count}",
            ),
            make_guided_step(
                "Paket-EK",
                package_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Rechne den Paket-VK mit dem DB-Faktor auf den Paket-EK zurück.",
                "Paket-VK x (1 - DB-Satz)",
                placeholder=f"Zum Beispiel {format_decimal(package_vk, 2)} * {format_decimal(divisor, 2)}",
            ),
            make_guided_step(
                "EK pro Quadratmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den Paket-EK durch die Paketfläche.",
                "Paket-EK / Paketfläche",
                placeholder=f"Zum Beispiel {format_decimal(package_ek, 2)} / {format_decimal(package_area, package_area_places)}",
            ),
        ],
    }


def task_package_db_sale_price(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
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
            f"Ein Lieferant bietet ein volles Paket {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} zu {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter im EK an. Das Paket enthält {package_count} Stück, unser Mindest-DB soll {format_decimal(db_percent, 0)} % betragen.\n\nWelchen Paketpreis müssen wir dem Kunden mindestens anbieten?",
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
        "factor_checks": [
            factor_check(f"Länge {format_m(length_m)} Meter", length_m),
            factor_check(f"Breite {width_text} ({format_decimal(width_m, 2)} Meter)", width_m),
            factor_check(f"Höhe {height_text} ({format_decimal(height_m, 2)} Meter)", height_m),
            factor_check(f"Paketstückzahl {package_count}", Decimal(package_count)),
            factor_check(f"Kubikmeterpreis {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
            db_factor_check(db_percent, divisor),
        ],
        "base_factor_checks": [
            base_factor_check(f"Paketvolumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            base_factor_check(f"Kubikmeterpreis {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_ek * divisor,
                (
                    f"Deine Eingabe wirkt so, als hättest du den Paket-EK mit dem DB-Faktor {format_decimal(divisor, 2)} multipliziert. "
                    "Bei der VK-Kalkulation mit Ziel-DB wird der EK aber auf den Verkaufspreis hochgerechnet."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_ek * (Decimal("1") + db_percent / Decimal("100")),
                (
                    f"Deine Eingabe wirkt wie ein Aufschlag von {format_decimal(db_percent, 0)} % auf den Paket-EK. "
                    "Ein Ziel-DB ist aber keine einfache Aufschlagsrechnung auf den EK, sondern wird vom Verkaufspreis aus betrachtet."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_ek / db_percent,
                (
                    f"Deine Eingabe wirkt so, als wäre mit {format_decimal(db_percent, 0)} statt mit dem DB-Faktor {format_decimal(divisor, 2)} gerechnet worden. "
                    "Prozentwerte müssen zuerst als Faktor verstanden werden."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_ek * db_percent,
                (
                    f"Deine Eingabe wirkt so, als wäre der Prozentwert {format_decimal(db_percent, 0)} direkt als Faktor verwendet worden. "
                    "Für den Ziel-DB brauchst du den Kostenanteil 1 minus DB-Satz."
                ),
                "EUR",
            ),
            *db_wrong_factor_checks(total_ek, db_percent, divisor, "sale_price"),
        ],
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


def task_package_ek_from_vk_db(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m, height_m = generate_structural_dimensions(level, length_m)
    package_count = structural_package_count(width_m, height_m)
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)

    piece_volume = length_m * width_m * height_m
    total_volume = piece_volume * Decimal(package_count)
    package_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    package_vk = package_ek / divisor
    piece_volume_places = precise_decimal_places(piece_volume)
    total_volume_places = precise_decimal_places(total_volume)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"Ein komplettes Paket {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} wurde für {format_decimal(package_vk, 2)} Euro verkauft. Im Paket liegen {package_count} Stück, kalkuliert wurde mit {format_decimal(db_percent, 0)} % DB.\n\nWie hoch war der Paket-EK?",
            f"Für ein Paket {product['name']} mit {package_count} Stück im Maß {format_m(length_m)} m x {width_text} x {height_text} liegt ein Paket-VK von {format_decimal(package_vk, 2)} Euro vor. Der DB beträgt {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der gesamte EK dieses Pakets?",
        ]
    )

    solution = format_solution_steps(
        (
            "DB-Faktor",
            "DB-Faktor = 1 - DB-Satz",
            f"1 - {format_decimal(db_percent, 0)} % = {format_decimal(divisor, 2)}",
        ),
        (
            "Paket-EK",
            "Paket-EK = Paket-VK x DB-Faktor",
            f"{format_decimal(package_vk, 2)} Euro x {format_decimal(divisor, 2)} = {format_decimal(package_ek, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": package_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "package_ek_from_vk_db",
        "correction": "Wenn Paket-VK und DB bekannt sind, rechnest du mit dem DB-Faktor zurück auf den Paket-EK. Die Maße beschreiben hier das Paket, sind für diese Rückwärtsrechnung aber nicht der entscheidende Rechenschritt.",
        "solution": solution,
        "perfect_formula": f"{format_decimal(package_vk, 2)} x {format_decimal(divisor, 2)}",
        "factor_checks": [
            factor_check(f"Paket-VK {format_decimal(package_vk, 2)} Euro", package_vk),
            db_factor_check(db_percent, divisor),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                package_vk / divisor,
                (
                    f"Deine Eingabe wirkt so, als hättest du den VK durch den DB-Faktor {format_decimal(divisor, 2)} geteilt. "
                    "Bei der Rückwärtsrechnung zum EK wird der VK mit diesem Faktor multipliziert."
                ),
                "EUR",
            ),
            wrong_value_check(
                total_volume * ek_price_m3,
                "Deine Eingabe entspricht dem rechnerischen Paket-EK aus Volumen und Kubikmeterpreis. Hier sollst du aber aus dem gegebenen VK und DB zurückrechnen.",
                "EUR",
            ),
            *db_wrong_factor_checks(package_vk, db_percent, divisor, "ek_from_vk"),
        ],
        "guided_steps": [
            make_guided_step(
                "DB-Faktor",
                divisor.normalize(),
                "Faktor",
                2,
                False,
                "Ziehe den DB-Satz von 1 ab.",
                "1 - DB-Satz",
                placeholder=f"Zum Beispiel 1 - 0,{format_decimal(db_percent, 0)}",
            ),
            make_guided_step(
                "Paket-EK",
                package_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den Paket-VK mit dem DB-Faktor.",
                "Paket-VK x DB-Faktor",
                placeholder=f"Zum Beispiel {format_decimal(package_vk, 2)} * {format_decimal(divisor, 2)}",
            ),
        ],
        "reference_values": {
            "piece_volume": f"{format_decimal(piece_volume, piece_volume_places)} Kubikmeter",
            "package_volume": f"{format_decimal(total_volume, total_volume_places)} Kubikmeter",
        },
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


def task_panel_count_from_area(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    length_m, width_m = panel_format_dimensions(panel_format)
    thickness_m = panel_thickness_for_product(product, level)
    panel_count = panel_count_for_level(level)
    sheet_area = length_m * width_m
    total_area = sheet_area * Decimal(panel_count)
    sheet_area_places = precise_decimal_places(sheet_area)
    total_area_places = precise_decimal_places(total_area)
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Für eine Anfrage werden {format_decimal(total_area, total_area_places)} Quadratmeter {product['name']} benötigt. Eine Platte hat das Format {panel_format} und ist {thickness_text} dick.\n\nWie viele Platten sind das?",
            f"Ein Angebot umfasst {format_decimal(total_area, total_area_places)} Quadratmeter {product['name']} im Format {panel_format}. Die Dicke beträgt {thickness_text}.\n\nWie viele einzelne Platten werden benötigt?",
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
            "Plattenanzahl",
            "Plattenanzahl = Gesamtfläche / Fläche pro Platte",
            f"{format_decimal(total_area, total_area_places)} Quadratmeter / {format_decimal(sheet_area, sheet_area_places)} Quadratmeter = "
            f"{panel_count} Stück",
        ),
    )

    return {
        "prompt": prompt,
        "expected": Decimal(panel_count),
        "unit": "Stück",
        "display_places": 0,
        "round_for_check": False,
        "task_type": "panel_count_from_area",
        "correction": "Rechne zuerst die Fläche einer einzelnen Platte aus und teile danach die Gesamtfläche durch diese Plattenfläche.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(total_area, total_area_places)} / "
            f"({format_decimal(length_m, 2)} x {format_decimal(width_m, 3)})"
        ),
        "factor_checks": [
            factor_check(f"Gesamtfläche {format_decimal(total_area, total_area_places)} Quadratmeter", total_area),
            factor_check(
                f"Fläche pro Platte {format_decimal(sheet_area, sheet_area_places)} Quadratmeter",
                sheet_area,
                missing_when_ratio_is_value=True,
            ),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_area * sheet_area,
                "Deine Eingabe wirkt wie die Gegenrichtung: Du hast die Gesamtfläche offenbar mit der Plattenfläche multipliziert. Für die Stückzahl wird geteilt.",
                "Stück",
            ),
            wrong_value_check(
                total_area / thickness_m,
                "Deine Eingabe wirkt so, als wäre die Dicke verwendet worden. Für die Anzahl der Platten brauchst du hier aber die Fläche pro Platte.",
                "Stück",
            ),
        ],
        "guided_steps": [
            make_guided_step(
                "Fläche pro Platte",
                sheet_area.normalize(),
                "m2",
                sheet_area_places,
                False,
                "Rechne zuerst Länge x Breite für eine einzelne Platte.",
                "Länge x Breite",
                placeholder=f"Zum Beispiel {format_decimal(length_m, 2)} * {format_decimal(width_m, 3)}",
            ),
            make_guided_step(
                "Plattenanzahl",
                Decimal(panel_count),
                "Stück",
                0,
                False,
                "Teile die Gesamtfläche durch die Fläche einer Platte.",
                "Gesamtfläche / Fläche pro Platte",
                placeholder=f"Zum Beispiel {format_decimal(total_area, total_area_places)} / {format_decimal(sheet_area, sheet_area_places)}",
            ),
        ],
    }


def task_running_meter_piece_count(level):
    needed_lfm = choice_for_level(RUNNING_METER_NEEDS_BY_LEVEL, level)

    is_hobelware = random.random() < 0.70
    if is_hobelware:
        product = generate_hobelware_product()
        display_name = "Glattkantbretter"
        length_m = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
        bundle_count = random.choice(HOBEL_BUNDLE_COUNTS)
        width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
        height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
        width_text = display_measure(width_m, ("cm", "m"))
        height_text = display_measure(height_m, ("mm", "cm"))
        extra_context = (
            f"Die Bretter sind {width_text} breit und {height_text} stark. "
            f"Ein Bund enthält {bundle_count} Bretter."
        )
    else:
        product = {"name": "KVH", "kind": "structural_beam"}
        display_name = product["name"]
        length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
        width_m, height_m = generate_structural_dimensions(level, length_m)
        width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))
        extra_context = f"Der Querschnitt beträgt {width_text} x {height_text}."

    raw_pieces = needed_lfm / length_m
    raw_places = precise_decimal_places(raw_pieces, 3, 4)

    if is_hobelware:
        needed_pieces = round_up_to_whole(raw_pieces)
        raw_bundles = Decimal(needed_pieces) / Decimal(bundle_count)
        result = round_up_to_whole(raw_bundles)
        raw_bundle_places = precise_decimal_places(raw_bundles, 3, 4)
        prompt = random.choice(
            [
                f"Ein Kunde benötigt {format_decimal(needed_lfm, 0)} Laufmeter {display_name}. Ein Brett ist {format_m(length_m)} m lang. {extra_context}\n\nWie viele Bund müssen mindestens bestellt werden?",
                f"Für eine Anfrage sollen {format_decimal(needed_lfm, 0)} Laufmeter {display_name} geliefert werden. Die Ware kommt in {format_m(length_m)} m Länge. {extra_context}\n\nWie viele volle Bund werden benötigt?",
                f"Eine Kundin möchte {format_decimal(needed_lfm, 0)} Laufmeter {display_name}. Die einzelnen Bretter sind jeweils {format_m(length_m)} m lang. {extra_context}\n\nWie viele Bund braucht sie mindestens?",
            ]
        )
        solution = format_solution_steps(
            (
                "Rechnerische Brettanzahl",
                "Rechnerische Brettanzahl = benötigte Laufmeter / Länge pro Brett",
                f"{format_decimal(needed_lfm, 0)} Laufmeter / {format_m(length_m)} Meter = "
                f"{format_decimal(raw_pieces, raw_places)} Bretter",
            ),
            (
                "Benötigte Bretter",
                "Benötigte Bretter = rechnerische Brettanzahl, danach auf volle Bretter aufrunden",
                f"{format_decimal(raw_pieces, raw_places)} Bretter, aufgerundet = "
                f"{format_decimal(needed_pieces, 0)} Bretter",
            ),
            (
                "Benötigte Bund",
                "Bund = benötigte Bretter / Bretter je Bund, danach auf volle Bund aufrunden",
                f"{format_decimal(needed_pieces, 0)} Bretter / {bundle_count} Bretter je Bund = "
                f"{format_decimal(raw_bundles, raw_bundle_places)} Bund, aufgerundet = {format_decimal(result, 0)} Bund",
            ),
        )
        guided_steps = [
            make_guided_step(
                "Rechnerische Brettanzahl",
                raw_pieces.normalize(),
                "Stück",
                raw_places,
                False,
                "Teile den Laufmeterbedarf durch die Länge eines Bretts.",
                "Benötigte Laufmeter / Länge pro Brett",
                placeholder="Zum Beispiel 150 / 3,30",
            ),
            make_guided_step(
                "Benötigte Bretter",
                needed_pieces,
                "Stück",
                0,
                False,
                "Runde die rechnerische Brettanzahl auf volle Bretter auf.",
                "Rechnerische Brettanzahl auf volle Bretter aufrunden",
                placeholder="Zum Beispiel 45,455",
                match_mode="ceil_integer",
            ),
            make_guided_step(
                "Benötigte Bund",
                result,
                "Bund",
                0,
                False,
                "Teile die benötigten Bretter durch die Bretter je Bund und runde auf volle Bund auf.",
                "Benötigte Bretter / Bretter je Bund, dann auf volle Bund aufrunden",
                placeholder="Zum Beispiel 46 / 6",
                match_mode="ceil_integer",
            ),
        ]
        correction = (
            "Teile den Laufmeterbedarf durch die Länge eines Bretts, runde auf volle Bretter auf "
            "und rechne danach auf volle Bund weiter."
        )
        perfect_formula = (
            f"{format_decimal(needed_lfm, 0)} / {format_m(length_m)} = "
            f"{format_decimal(raw_pieces, raw_places)}, aufgerundet {format_decimal(needed_pieces, 0)} Bretter; "
            f"{format_decimal(needed_pieces, 0)} / {bundle_count} = "
            f"{format_decimal(raw_bundles, raw_bundle_places)}, aufgerundet {format_decimal(result, 0)} Bund"
        )
        unit = "Bund"
    else:
        result = round_up_to_whole(raw_pieces)
        prompt = random.choice(
            [
                f"Ein Kunde benötigt {format_decimal(needed_lfm, 0)} Laufmeter {display_name}. Ein Stück ist {format_m(length_m)} m lang. {extra_context}\n\nWie viele Stück müssen mindestens bestellt werden?",
                f"Für eine Anfrage sollen {format_decimal(needed_lfm, 0)} Laufmeter {display_name} geliefert werden. Die Ware kommt in {format_m(length_m)} m Länge. {extra_context}\n\nWie viele volle Stück werden benötigt?",
                f"Eine Kundin möchte {format_decimal(needed_lfm, 0)} Laufmeter {display_name}. Die einzelnen Stücke sind jeweils {format_m(length_m)} m lang. {extra_context}\n\nWie viele Stück braucht sie mindestens?",
            ]
        )
        needs_rounding = raw_pieces != raw_pieces.to_integral_value()
        if needs_rounding:
            solution = format_solution_steps(
                (
                    "Rechnerische Stückzahl",
                    "Rechnerische Stückzahl = benötigte Laufmeter / Länge pro Stück",
                    f"{format_decimal(needed_lfm, 0)} Laufmeter / {format_m(length_m)} Meter = "
                    f"{format_decimal(raw_pieces, raw_places)} Stück",
                ),
                (
                    "Benötigte Stück",
                    "Stückzahl = rechnerische Stückzahl, danach auf volle Stück aufrunden",
                    f"{format_decimal(raw_pieces, raw_places)} Stück, aufgerundet = {format_decimal(result, 0)} Stück",
                ),
            )
            guided_steps = [
                make_guided_step(
                    "Rechnerische Stückzahl",
                    raw_pieces.normalize(),
                    "Stück",
                    raw_places,
                    False,
                    "Teile den Laufmeterbedarf durch die Länge eines Stücks.",
                    "Benötigte Laufmeter / Länge pro Stück",
                ),
                make_guided_step(
                    "Benötigte Stück",
                    result,
                    "Stück",
                    0,
                    False,
                    "Runde die rechnerische Stückzahl auf volle Stück auf.",
                    "Rechnerische Stückzahl auf volle Stück aufrunden",
                    match_mode="ceil_integer",
                ),
            ]
        else:
            solution = format_solution_steps(
                (
                    "Benötigte Stück",
                    "Benötigte Stück = benötigte Laufmeter / Länge pro Stück",
                    f"{format_decimal(needed_lfm, 0)} Laufmeter / {format_m(length_m)} Meter = "
                    f"{format_decimal(result, 0)} Stück",
                ),
            )
            guided_steps = [
                make_guided_step(
                    "Benötigte Stück",
                    result,
                    "Stück",
                    0,
                    False,
                    "Teile den Laufmeterbedarf durch die Länge eines Stücks.",
                    "Benötigte Laufmeter / Länge pro Stück",
                    match_mode="ceil_integer",
                ),
            ]

        correction = (
            "Teile den Laufmeterbedarf durch die Länge eines Stücks und runde anschließend auf volle Stück auf."
            if needs_rounding
            else "Teile den Laufmeterbedarf durch die Länge eines Stücks."
        )
        perfect_formula = (
            f"{format_decimal(needed_lfm, 0)} / {format_m(length_m)} = "
            f"{format_decimal(raw_pieces, raw_places)}, aufgerundet {format_decimal(result, 0)}"
            if needs_rounding
            else f"{format_decimal(needed_lfm, 0)} / {format_m(length_m)}"
        )
        unit = "Stück"

    return {
        "prompt": prompt,
        "expected": result,
        "unit": unit,
        "display_places": 0,
        "round_for_check": False,
        "match_mode": "ceil_integer",
        "task_type": "running_meter_piece_count",
        "correction": correction,
        "solution": solution,
        "perfect_formula": perfect_formula,
        "guided_steps": guided_steps,
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
        "factor_checks": [
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            factor_check(f"EK {format_decimal(total_ek, 2)} Euro", total_ek),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_ek - total_vk,
                "Deine Eingabe wirkt so, als hättest du EK minus VK gerechnet. Beim absoluten DB ist die Richtung andersherum: VK minus EK.",
                "EUR",
            ),
            wrong_value_check(
                total_vk + total_ek,
                "Deine Eingabe wirkt so, als hättest du VK und EK addiert. Beim absoluten DB geht es aber um den Betrag, der zwischen VK und EK übrig bleibt.",
                "EUR",
            ),
        ],
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
        "factor_checks": [
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            factor_check(f"EK {format_decimal(total_ek, 2)} Euro", total_ek),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                (absolute_db / total_ek * Decimal("100")).quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "Deine Eingabe wirkt so, als hättest du den absoluten DB ins Verhältnis zum EK gesetzt. Der relative DB wird hier aber auf den VK bezogen.",
                "Prozent",
                round_for_check=True,
                match_mode="percent_or_factor",
            ),
            wrong_value_check(
                total_vk - total_ek,
                "Deine Eingabe entspricht auffällig dem absoluten DB in Euro. Gefragt ist aber der relative DB-Satz in Prozent.",
                "EUR",
            ),
        ],
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


def task_absolute_db_from_position(level):
    details = generate_whole_volume_position_details(level)
    product = details["product"]
    context = details["context"]
    total_volume = details["total_volume"]
    total_volume_places = details["total_volume_places"]
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_ek = total_volume * ek_price_m3
    total_vk = total_ek / divisor
    result = total_vk - total_ek

    prompt = random.choice(
        [
            f"Für {context} liegt ein EK von {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter vor. Der gesamte VK der Position beträgt {format_decimal(total_vk, 2)} Euro.\n\nWie hoch ist der absolute DB in Euro?",
            f"Eine Position umfasst {context}. Das Volumen beträgt {format_decimal(total_volume, total_volume_places)} Kubikmeter, der EK liegt bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter und der gesamte VK dieser Position beträgt {format_decimal(total_vk, 2)} Euro.\n\nWie hoch ist der Rohertrag beziehungsweise absolute DB?",
        ]
    )

    solution = format_solution_steps(
        *details["volume_solution_steps"],
        (
            "Gesamter EK",
            "Gesamter EK = Volumen x EK pro Kubikmeter",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(total_ek, 2)} Euro",
        ),
        (
            "Absoluter DB",
            "Absoluter DB = VK - EK",
            f"{format_decimal(total_vk, 2)} Euro - {format_decimal(total_ek, 2)} Euro = {format_decimal(result, 2)} Euro",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "absolute_db_from_position",
        "correction": "Baue zuerst das Gesamtvolumen aus den Maßen auf, berechne daraus den gesamten EK und ziehe diesen EK anschließend vom VK ab.",
        "solution": solution,
        "perfect_formula": (
            f"{format_decimal(total_vk, 2)} - "
            f"(({details['perfect_volume_formula']}) x {format_decimal(ek_price_m3, 0)})"
        ),
        "factor_checks": [
            *details["volume_factor_checks"],
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            factor_check(f"Volumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            factor_check(f"EK pro Kubikmeter {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
        ],
        "base_factor_checks": [
            base_factor_check(f"Gesamter EK {format_decimal(total_ek, 2)} Euro", total_ek),
            base_factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                total_ek - total_vk,
                "Deine Eingabe wirkt wie EK minus VK. Beim absoluten DB geht es um VK minus EK.",
                "EUR",
            ),
            wrong_value_check(
                total_vk,
                "Deine Eingabe entspricht dem VK. Gefragt ist aber nur der Betrag, der nach Abzug des EK als DB bleibt.",
                "EUR",
            ),
        ],
        "guided_steps": [
            *details["volume_guided_steps"],
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere das Volumen mit dem EK pro Kubikmeter.",
                "Volumen x EK pro Kubikmeter",
                placeholder=f"Zum Beispiel {format_decimal(total_volume, total_volume_places)} * {format_decimal(ek_price_m3, 0)}",
            ),
            make_guided_step(
                "Absoluter DB",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Ziehe den EK vom VK ab.",
                "VK - EK",
                placeholder=f"Zum Beispiel {format_decimal(total_vk, 2)} - {format_decimal(total_ek, 2)}",
            ),
        ],
    }


def task_relative_db_from_position(level):
    details = generate_whole_volume_position_details(level)
    product = details["product"]
    context = details["context"]
    total_volume = details["total_volume"]
    total_volume_places = details["total_volume_places"]
    ek_price_m3 = m3_price_for_product(product, level)
    db_percent = db_percent_for_product(product, level)
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_ek = total_volume * ek_price_m3
    total_vk = total_ek / divisor
    absolute_db = total_vk - total_ek
    result = (absolute_db / total_vk) * Decimal("100")

    prompt = random.choice(
        [
            f"Für {context} liegt der EK bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter. Der gesamte VK der Position beträgt {format_decimal(total_vk, 2)} Euro.\n\nWie hoch ist der relative DB in Prozent?",
            f"Eine Anfrage umfasst {context}. Das Volumen beträgt {format_decimal(total_volume, total_volume_places)} Kubikmeter, der EK liegt bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter und der gesamte VK der Position bei {format_decimal(total_vk, 2)} Euro.\n\nWie viel Prozent DB wurden erzielt?",
        ]
    )

    solution = format_solution_steps(
        *details["volume_solution_steps"],
        (
            "Gesamter EK",
            "Gesamter EK = Volumen x EK pro Kubikmeter",
            f"{format_decimal(total_volume, total_volume_places)} Kubikmeter x {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter = "
            f"{format_decimal(total_ek, 2)} Euro",
        ),
        (
            "Absoluter DB",
            "Absoluter DB = VK - EK",
            f"{format_decimal(total_vk, 2)} Euro - {format_decimal(total_ek, 2)} Euro = {format_decimal(absolute_db, 2)} Euro",
        ),
        (
            "DB-Satz",
            "DB-Satz = absoluter DB / VK x 100",
            f"{format_decimal(absolute_db, 2)} Euro / {format_decimal(total_vk, 2)} Euro x 100 = {format_decimal(result, 2)} %",
        ),
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "Prozent",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "relative_db_from_position",
        "correction": "Baue zuerst das Gesamtvolumen aus den Maßen auf, berechne daraus den gesamten EK und danach den absoluten DB. Für den relativen DB setzt du diesen Rohertrag ins Verhältnis zum VK.",
        "solution": solution,
        "perfect_formula": (
            f"({format_decimal(total_vk, 2)} - "
            f"(({details['perfect_volume_formula']}) x {format_decimal(ek_price_m3, 0)})) / "
            f"{format_decimal(total_vk, 2)} x 100"
        ),
        "factor_checks": [
            *details["volume_factor_checks"],
            factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
            factor_check(f"Volumen {format_decimal(total_volume, total_volume_places)} Kubikmeter", total_volume),
            factor_check(f"EK pro Kubikmeter {format_decimal(ek_price_m3, 0)} Euro", ek_price_m3),
        ],
        "base_factor_checks": [
            base_factor_check(f"Gesamter EK {format_decimal(total_ek, 2)} Euro", total_ek),
            base_factor_check(f"Absoluter DB {format_decimal(absolute_db, 2)} Euro", absolute_db),
            base_factor_check(f"VK {format_decimal(total_vk, 2)} Euro", total_vk),
        ],
        "wrong_value_checks": [
            wrong_value_check(
                (absolute_db / total_ek) * Decimal("100"),
                "Deine Eingabe wirkt so, als hättest du den DB auf den EK bezogen. Der relative DB wird im Holzhandel auf den VK bezogen.",
                "Prozent",
                match_mode="percent_or_factor",
            ),
            wrong_value_check(
                absolute_db,
                "Deine Eingabe entspricht dem absoluten DB in Euro. Gefragt ist hier aber der relative DB in Prozent.",
                "Prozent",
            ),
        ],
        "guided_steps": [
            *details["volume_guided_steps"],
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere das Volumen mit dem EK pro Kubikmeter.",
                "Volumen x EK pro Kubikmeter",
                placeholder=f"Zum Beispiel {format_decimal(total_volume, total_volume_places)} * {format_decimal(ek_price_m3, 0)}",
            ),
            make_guided_step(
                "Absoluter DB",
                absolute_db.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Ziehe den EK vom VK ab.",
                "VK - EK",
                placeholder=f"Zum Beispiel {format_decimal(total_vk, 2)} - {format_decimal(total_ek, 2)}",
            ),
            make_guided_step(
                "DB-Satz",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "Prozent",
                2,
                True,
                "Teile den absoluten DB durch den VK und multipliziere mit 100.",
                "Absoluter DB / VK x 100",
                placeholder=f"Zum Beispiel {format_decimal(absolute_db, 2)} / {format_decimal(total_vk, 2)} * 100",
                match_mode="percent_or_factor",
            ),
        ],
    }


TASK_GENERATORS = [
    task_unit_conversion,
    task_flooring_packages,
    task_panel_count_from_area,
    task_running_meter_piece_count,
    task_volume_beam,
    task_volume_from_running_meters,
    task_volume_from_square_meters,
    task_volume_from_total_price,
    task_weight_from_volume,
    task_weight_from_dimensions,
    task_wood_fiber_insulation_weight,
    task_running_meters_from_volume,
    task_running_meters_from_square_meters,
    task_price_per_running_meter,
    task_m3_price_from_running_meter,
    task_m3_price_from_square_meter,
    task_price_per_square_meter,
    task_running_meter_price_from_square_meter,
    task_square_meter_price_from_running_meter,
    task_lfm_price_from_m3_with_db,
    task_m2_price_from_m3_with_db,
    task_square_meters_from_volume,
    task_square_meters_from_running_meters,
    task_total_price_from_volume,
    task_db_sale_price,
    task_lfm_db_sale_price,
    task_m2_db_sale_price,
    task_ek_from_vk_db,
    task_m3_ek_from_vk_db,
    task_lfm_ek_from_vk_db,
    task_m2_ek_from_vk_db,
    task_absolute_db_from_ek_vk,
    task_relative_db_from_ek_vk,
    task_absolute_db_from_position,
    task_relative_db_from_position,
    task_package_price,
    task_panel_package_price,
    task_panel_package_db_sale_price,
    task_panel_package_ek_from_vk_db,
    task_package_db_sale_price,
    task_package_ek_from_vk_db,
]

TASK_TYPE_TO_GENERATOR = {
    task_func.__name__.replace("task_", ""): task_func
    for task_func in TASK_GENERATORS
}

TASKS_BY_LEVEL = {
    1: [
        task_unit_conversion,
        task_flooring_packages,
        task_panel_count_from_area,
        task_running_meter_piece_count,
        task_volume_beam,
        task_volume_from_running_meters,
        task_square_meters_from_running_meters,
        task_running_meters_from_volume,
        task_wood_fiber_insulation_weight,
        task_weight_from_dimensions,
        task_total_price_from_volume,
        task_volume_from_square_meters,
        task_volume_from_total_price,
        task_price_per_running_meter,
        task_price_per_square_meter,
        task_m3_price_from_square_meter,
        task_running_meter_price_from_square_meter,
        task_square_meter_price_from_running_meter,
        task_lfm_price_from_m3_with_db,
        task_m2_price_from_m3_with_db,
        task_db_sale_price,
        task_lfm_db_sale_price,
        task_m2_db_sale_price,
        task_m3_ek_from_vk_db,
        task_lfm_ek_from_vk_db,
        task_m2_ek_from_vk_db,
        task_absolute_db_from_ek_vk,
        task_relative_db_from_ek_vk,
        task_absolute_db_from_position,
        task_relative_db_from_position,
        task_package_price,
        task_panel_package_price,
        task_panel_package_db_sale_price,
        task_panel_package_ek_from_vk_db,
        task_package_db_sale_price,
        task_package_ek_from_vk_db,
    ],
    2: [
        task_unit_conversion,
        task_flooring_packages,
        task_panel_count_from_area,
        task_running_meter_piece_count,
        task_volume_beam,
        task_volume_from_running_meters,
        task_volume_from_square_meters,
        task_volume_from_total_price,
        task_weight_from_volume,
        task_weight_from_dimensions,
        task_wood_fiber_insulation_weight,
        task_total_price_from_volume,
        task_price_per_square_meter,
        task_m3_price_from_square_meter,
        task_running_meter_price_from_square_meter,
        task_square_meter_price_from_running_meter,
        task_lfm_price_from_m3_with_db,
        task_m2_price_from_m3_with_db,
        task_square_meters_from_volume,
        task_square_meters_from_running_meters,
        task_running_meters_from_volume,
        task_running_meters_from_square_meters,
        task_price_per_running_meter,
        task_m3_price_from_running_meter,
        task_db_sale_price,
        task_lfm_db_sale_price,
        task_m2_db_sale_price,
        task_ek_from_vk_db,
        task_m3_ek_from_vk_db,
        task_lfm_ek_from_vk_db,
        task_m2_ek_from_vk_db,
        task_absolute_db_from_ek_vk,
        task_relative_db_from_ek_vk,
        task_absolute_db_from_position,
        task_relative_db_from_position,
        task_package_price,
        task_panel_package_price,
        task_panel_package_db_sale_price,
        task_panel_package_ek_from_vk_db,
        task_package_db_sale_price,
        task_package_ek_from_vk_db,
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
    return truncate_decimal(user_value, 3) == truncate_decimal(expected_value, 3)


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
    cleaned = normalize_number_input(text).replace(" ", "")
    return bool(re.fullmatch(r"[+-]?\d+(?:\.\d+)?", cleaned))


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
    if "rechnerische brettanzahl" in label:
        return "Zum Beispiel 150 / 3,30"
    if "benötigte bretter" in label:
        return "Zum Beispiel 45,455"
    if "bund" in label:
        return "Zum Beispiel 46 / 6"
    if "stückzahl" in label or "benötigte stück" in label:
        return "Zum Beispiel 150 / 3,45"
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
    return default_step_placeholder(step)


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
    st.markdown("#### Maßeinheiten")
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

    st.markdown("#### Volumen/Menge")
    st.write(
        "Volumen und Mengen brauchst du, um Ware fachlich vergleichbar zu machen. Je nach Produkt wird in Laufmetern, "
        "Quadratmetern, Kubikmetern, Stück oder ganzen Paketen gedacht."
    )
    st.markdown(
        """
| Von | Nach | Rechenweg | Beispiel |
| --- | --- | --- | --- |
| Laufmeter | Quadratmeter | Laufmeter x Breite | 24 Laufmeter x 0,16 Meter = 3,84 Quadratmeter |
| Quadratmeter | Laufmeter | Quadratmeter / Breite | 3,84 Quadratmeter / 0,16 Meter = 24 Laufmeter |
| Quadratmeter | Kubikmeter | Quadratmeter x Dicke | 51,25 Quadratmeter x 0,04 Meter = 2,05 Kubikmeter |
| Kubikmeter | Quadratmeter | Kubikmeter / Dicke | 2,05 Kubikmeter / 0,04 Meter = 51,25 Quadratmeter |
| Laufmeter | Kubikmeter | Laufmeter x Breite x Höhe | 30 Laufmeter x 0,08 Meter x 0,10 Meter = 0,240 Kubikmeter |
| Kubikmeter | Laufmeter | Kubikmeter / (Breite x Höhe) | 0,240 Kubikmeter / (0,08 Meter x 0,10 Meter) = 30 Laufmeter |
"""
    )

    st.markdown("#### Preise")
    st.write(
        "Preise hängen immer an einer Einheit. Darum ist entscheidend, ob ein Preis pro Laufmeter, Quadratmeter "
        "oder Kubikmeter gemeint ist, bevor du multiplizierst oder teilst."
    )
    st.markdown(
        """
| Von | Nach | Rechenweg | Beispiel |
| --- | --- | --- | --- |
| Euro pro Laufmeter | Euro pro Quadratmeter | Euro pro Laufmeter / Breite | 4,80 Euro pro Laufmeter / 0,16 Meter = 30,00 Euro pro Quadratmeter |
| Euro pro Quadratmeter | Euro pro Laufmeter | Euro pro Quadratmeter x Breite | 30,00 Euro pro Quadratmeter x 0,16 Meter = 4,80 Euro pro Laufmeter |
| Euro pro Quadratmeter | Euro pro Kubikmeter | Euro pro Quadratmeter / Dicke | 12,00 Euro pro Quadratmeter / 0,04 Meter = 300,00 Euro pro Kubikmeter |
| Euro pro Kubikmeter | Euro pro Quadratmeter | Euro pro Kubikmeter x Dicke | 300,00 Euro pro Kubikmeter x 0,04 Meter = 12,00 Euro pro Quadratmeter |
| Euro pro Laufmeter | Euro pro Kubikmeter | Euro pro Laufmeter / (Breite x Höhe) | 4,80 Euro pro Laufmeter / (0,08 Meter x 0,10 Meter) = 600,00 Euro pro Kubikmeter |
| Euro pro Kubikmeter | Euro pro Laufmeter | Euro pro Kubikmeter x Breite x Höhe | 600,00 Euro pro Kubikmeter x 0,08 Meter x 0,10 Meter = 4,80 Euro pro Laufmeter |
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

    st.markdown("#### Kombinierte Aufgaben")
    st.write(
        "In echten Angeboten kommen diese Formeln oft zusammen vor: Erst werden Maßeinheiten sauber umgerechnet, "
        "dann wird daraus eine Menge oder ein Volumen gebildet, anschließend ein EK oder VK berechnet und zum Schluss "
        "kann noch der gewünschte DB berücksichtigt werden."
    )
    st.markdown(
        """
**Musteraufgabe:** Für 8 Stück KVH mit 6 Meter Länge, 8 Zentimeter Breite und 12 Zentimeter Höhe liegt der EK bei 420 Euro pro Kubikmeter. Es soll ein DB von 25 Prozent erzielt werden.

**Rechenweg:**
1. Maße umrechnen: 8 Zentimeter = 0,08 Meter und 12 Zentimeter = 0,12 Meter.
2. Volumen bilden: 6 Meter x 0,08 Meter x 0,12 Meter x 8 Stück = 0,4608 Kubikmeter.
3. EK berechnen: 0,4608 Kubikmeter x 420 Euro pro Kubikmeter = 193,54 Euro.
4. DB berücksichtigen: Bei 25 Prozent DB bleibt der Kostenanteil 0,75. VK = 193,54 Euro / 0,75 = 258,05 Euro.
"""
    )


def guided_completed_entry(text, kind="success"):
    return {
        "text": text,
        "kind": kind,
    }


def render_guided_resolved_entry(entry):
    next_step = entry.get("next_step_label", "")
    next_text = f"<div class='resolved-next'>Als Nächstes: {escape(next_step)}.</div>" if next_step else ""
    message = clean_ai_output(entry.get("message", "")).strip()
    message_html = f"<div class='resolved-message'>{escape(message)}</div>" if message else ""
    result_label = "Weiterrechnen kannst du mit" if next_step else "Das Ergebnis ist"
    formula = entry.get("formula", "").strip()
    calculation = entry.get("calculation", "").strip()
    formula_html = ""
    if formula or calculation:
        formula_lines = ["<div class='resolved-formula'>"]
        formula_lines.append("<div class='resolved-formula-title'>So entsteht der korrekte Wert:</div>")
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
        st.warning(clean_ai_output(text))
    else:
        st.success(clean_ai_output(text))


def render_guided_summary():
    text = st.session_state.get("guided_summary", "")
    if not text:
        return
    text = clean_ai_output(text)

    kind = st.session_state.get("guided_summary_kind", "warning")
    if kind == "success":
        st.success(text)
    elif kind == "error":
        st.error(text)
    else:
        st.warning(f"KI-Hinweis: {text}")


def guided_has_warning():
    for entry in st.session_state.get("guided_completed", []):
        if isinstance(entry, dict) and entry.get("kind") in {"warning", "resolved"}:
            return True
    return False


def is_close_factor(value, target):
    tolerance = abs(target) * Decimal("0.03")
    return abs(value - target) <= tolerance


def diagnostic_values_match(user_value, expected_value, round_for_check=False, match_mode=None):
    if expected_value is None:
        return False

    if values_match(user_value, expected_value, round_for_check, match_mode):
        return True

    if round_for_check:
        return user_value.quantize(q("1.00"), rounding=ROUND_HALF_UP) == expected_value.quantize(
            q("1.00"), rounding=ROUND_HALF_UP
        )

    if expected_value == 0:
        return user_value == 0

    tolerance = abs(expected_value) * Decimal("0.003")
    return abs(user_value - expected_value) <= tolerance


def diagnose_factor_check(answer_value, expected_value, factor_checks):
    if expected_value == 0:
        return ""

    try:
        ratio = answer_value / expected_value
    except (InvalidOperation, ZeroDivisionError):
        return ""

    abs_ratio = ratio.copy_abs()
    normalized_factors = []
    for factor in factor_checks or []:
        label = factor.get("label", "ein Faktor")
        value = factor.get("value")
        if not value:
            continue
        value = Decimal(value)
        if value == 0:
            continue
        normalized_factors.append((factor, label, value))

    for factor, label, value in normalized_factors:
        if factor.get("missing_when_ratio_is_value") and is_close_factor(abs_ratio, value):
            return factor.get(
                "missing_message",
                (
                    f"Die Abweichung passt auffällig dazu, dass der Faktor {label} fehlt. "
                    "Prüfe, ob dieser Schritt in deinem Rechenweg wirklich vorkommt."
                ),
            )
        if is_close_factor(abs_ratio, Decimal("1") / value):
            return (
                f"Die Abweichung passt auffällig dazu, dass der Faktor {label} fehlen könnte. "
                "Prüfe, ob dieser Wert in deinem Rechenweg wirklich vorkommt."
            )

    for _factor, label, value in normalized_factors:
        if is_close_factor(abs_ratio, value):
            return (
                f"Die Abweichung passt auffällig dazu, dass der Faktor {label} zu viel verwendet wurde. "
                "Prüfe, ob dieser Wert für die gesuchte Zielgröße wirklich gebraucht wird."
            )

    for index, (_first_factor, first_label, first_value) in enumerate(normalized_factors):
        for _second_factor, second_label, second_value in normalized_factors[index + 1 :]:
            product = first_value * second_value
            if product and product != 1 and is_close_factor(abs_ratio, Decimal("1") / product):
                return (
                    "Die Abweichung passt auffällig zu zwei gleichzeitig fehlenden Faktoren: "
                    f"{first_label} und {second_label}. Prüfe, ob beide Werte im Rechenweg wirklich vorkommen."
                )
            if product != 1 and is_close_factor(abs_ratio, product):
                return (
                    "Die Abweichung passt auffällig dazu, dass zwei Faktoren zu viel verwendet wurden: "
                    f"{first_label} und {second_label}. Prüfe, ob beide Werte für die gesuchte Zielgröße wirklich gebraucht werden."
                )

            first_over_second = first_value / second_value
            if first_over_second != 1 and is_close_factor(abs_ratio, first_over_second):
                return (
                    "Die Abweichung passt auffällig zu einer Kombination aus zwei Faktorfehlern: "
                    f"{first_label} wurde eher zu viel verwendet, während {second_label} fehlen könnte."
                )

            second_over_first = second_value / first_value
            if second_over_first != 1 and is_close_factor(abs_ratio, second_over_first):
                return (
                    "Die Abweichung passt auffällig zu einer Kombination aus zwei Faktorfehlern: "
                    f"{second_label} wurde eher zu viel verwendet, während {first_label} fehlen könnte."
                )

    return ""


def diagnose_missing_base_factors(answer_value, expected_value, base_factor_checks):
    if expected_value == 0 or not base_factor_checks:
        return ""

    try:
        ratio = (answer_value / expected_value).copy_abs()
    except (InvalidOperation, ZeroDivisionError):
        return ""

    product = Decimal("1")
    labels = []
    for factor in base_factor_checks:
        label = factor.get("label", "Basiswert")
        value = factor.get("value")
        if not value:
            continue
        value = Decimal(value)
        if value == 0:
            continue
        product *= value
        labels.append(label)

    if not labels or product == 0:
        return ""

    if is_close_factor(ratio, Decimal("1") / product):
        joined_labels = " und ".join(labels)
        return (
            f"Die Abweichung passt auffällig dazu, dass die eigentliche Basis der Rechnung fehlt: {joined_labels}. "
            "Deine Eingabe wirkt so, als wären nur Umrechnungs- oder DB-Faktoren stehen geblieben. "
            "Prüfe zuerst, welche Menge bewertet wird und welche Preisbasis dazu gehört."
        )

    return ""


def diagnose_wrong_value_check(task, answer_value):
    for check in task.get("wrong_value_checks", []):
        value = check.get("value")
        if value is None:
            continue
        value = Decimal(value)
        round_for_check = check.get("round_for_check")
        if round_for_check is None:
            round_for_check = check.get("unit") in {"EUR", "kg"}
        if diagnostic_values_match(answer_value, value, round_for_check, check.get("match_mode")):
            return check.get("message", "")
    return ""


def diagnose_intermediate_value(task, answer_value, expected_value):
    guided_steps = task.get("guided_steps", [])
    if len(guided_steps) <= 1:
        return ""

    if values_match(answer_value, expected_value, task.get("round_for_check", False), task.get("match_mode")):
        return ""

    final_label = guided_steps[-1].get("label", "Endergebnis")
    for step in guided_steps[:-1]:
        if diagnostic_values_match(
            answer_value,
            step["expected"],
            step["round_for_check"],
            step.get("match_mode"),
        ):
            step_value = f"{format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}"
            return (
                f"Deine Eingabe passt auffällig zum Zwischenschritt {step['label']} ({step_value}), "
                f"aber gefragt ist {final_label} als {unit_label(task['unit'])}. "
                "Wahrscheinlich hast du einen späteren Faktor oder den nächsten Rechenschritt noch nicht berücksichtigt."
            )
    return ""


def diagnose_common_mistake(task, answer_value, expected_value, include_task_wrong_values=True, include_intermediates=True):
    if expected_value == 0:
        return ""

    if values_match(answer_value, expected_value, task.get("round_for_check", False), task.get("match_mode")):
        return ""

    if include_task_wrong_values:
        wrong_value_diagnostic = diagnose_wrong_value_check(task, answer_value)
        if wrong_value_diagnostic:
            return wrong_value_diagnostic

    base_factor_diagnostic = diagnose_missing_base_factors(
        answer_value,
        expected_value,
        task.get("base_factor_checks", []),
    )
    if base_factor_diagnostic:
        return base_factor_diagnostic

    factor_diagnostic = diagnose_factor_check(answer_value, expected_value, task.get("factor_checks", []))
    if factor_diagnostic:
        return factor_diagnostic

    if include_intermediates:
        intermediate_diagnostic = diagnose_intermediate_value(task, answer_value, expected_value)
        if intermediate_diagnostic:
            return intermediate_diagnostic

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

    if task["task_type"] in {
        "price_per_running_meter",
        "m3_price_from_running_meter",
        "m3_price_from_square_meter",
        "running_meter_price_from_square_meter",
        "square_meter_price_from_running_meter",
        "lfm_price_from_m3_with_db",
        "m2_price_from_m3_with_db",
        "total_price_from_volume",
        "volume_from_total_price",
    }:
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

    if task["task_type"] in {
        "absolute_db_from_ek_vk",
        "relative_db_from_ek_vk",
        "absolute_db_from_position",
        "relative_db_from_position",
        "m3_ek_from_vk_db",
    }:
        return (
            "Beim DB gehst du zuerst vom Unterschied zwischen VK und EK aus. "
            "Für den Prozentwert wird dieser Unterschied anschließend durch den VK geteilt."
        )

    if task["task_type"] in {"weight_from_volume", "weight_from_dimensions", "wood_fiber_insulation_weight"}:
        return (
            "Beim Gewicht wird nicht mit einem Preis gerechnet, sondern mit der Dichte. "
            "Prüfe, ob du das Volumen in Kubikmeter mit Kilogramm pro Kubikmeter weitergerechnet hast."
        )

    return ""


def diagnose_step_mistake(task, step, answer_value):
    message = diagnose_common_mistake(
        task,
        answer_value,
        step["expected"],
        include_task_wrong_values=False,
        include_intermediates=False,
    )
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
        "m3_price_from_square_meter": "Achte besonders auf die Rückrichtung vom Quadratmeterpreis zum Kubikmeterpreis über die Dicke.",
        "running_meter_price_from_square_meter": "Achte besonders auf die Breite als Verbindung zwischen Quadratmeterpreis und Laufmeterpreis.",
        "square_meter_price_from_running_meter": "Achte besonders darauf, den Laufmeterpreis durch die Breite zu teilen.",
        "lfm_price_from_m3_with_db": "Achte besonders auf Querschnitt, Kubikmeterpreis und danach den Ziel-DB.",
        "m2_price_from_m3_with_db": "Achte besonders auf Dicke, Kubikmeterpreis und danach den Ziel-DB.",
        "square_meters_from_volume": "Achte besonders auf die Richtung der Umrechnung zwischen Kubikmeter und Quadratmeter.",
        "volume_from_square_meters": "Achte besonders auf die Richtung der Umrechnung von Quadratmeter zu Kubikmeter über die Dicke.",
        "total_price_from_volume": "Achte besonders darauf, ob Volumen und Preisbasis wirklich zur Zielgröße Gesamtpreis passen.",
        "running_meters_from_volume": "Achte besonders auf die Richtung Kubikmeter zu Laufmeter sowie auf Breite und Stärke in Meter.",
        "square_meters_from_running_meters": "Achte besonders auf die Richtung Laufmeter zu Quadratmeter über die Breite der Hobelware.",
        "running_meters_from_square_meters": "Achte besonders auf die Richtung Quadratmeter zu Laufmeter über die Breite der Hobelware.",
        "db_sale_price": "Achte besonders darauf, ob nach dem gesamten EK noch der Ziel-DB berücksichtigt wurde; häufig fehlt die Division durch den DB-Faktor.",
        "lfm_db_sale_price": "Achte besonders darauf, ob zuerst der gesamte EK aus Laufmetern und EK pro Laufmeter gebildet und danach der Ziel-DB berücksichtigt wurde.",
        "m2_db_sale_price": "Achte besonders auf die Gesamtfläche, den EK pro Quadratmeter und den Ziel-DB.",
        "package_db_sale_price": "Achte besonders darauf, ob nach dem Paket-EK noch der Ziel-DB berücksichtigt wurde; häufig fehlt die Division durch den DB-Faktor.",
        "volume_from_running_meters": "Achte besonders auf Querschnitt mal Laufmeter und auf vollständige Maße.",
        "volume_from_total_price": "Achte besonders auf die richtige Richtung Preis zu Volumen, also teilen statt multiplizieren.",
        "weight_from_volume": "Achte besonders darauf, dass die Dichte ein Faktor pro Kubikmeter ist.",
        "weight_from_dimensions": "Achte besonders darauf, erst das Gesamtvolumen aus den Maßen aufzubauen und dann mit der Dichte weiterzurechnen.",
        "wood_fiber_insulation_weight": "Achte besonders darauf, dass die Rohdichte fest 40 Kilogramm pro Kubikmeter beträgt.",
        "m3_price_from_running_meter": "Achte besonders auf die richtige Preisbasis, auf Breite x Stärke in Meter und auf Teilen statt Multiplizieren.",
        "ek_from_vk_db": "Achte besonders auf die Rückwärtsrechnung vom VK über den DB-Faktor zum EK.",
        "m3_ek_from_vk_db": "Achte besonders darauf, den VK über den DB-Faktor auf den EK zurückzurechnen und danach durch das Gesamtvolumen zu teilen.",
        "lfm_ek_from_vk_db": "Achte besonders darauf, den VK über den DB-Faktor auf den gesamten EK zurückzurechnen und danach durch die Laufmeter zu teilen.",
        "m2_ek_from_vk_db": "Achte besonders darauf, zuerst die Gesamtfläche zu bilden und den VK über den DB-Faktor auf den EK pro Quadratmeter zurückzuführen.",
        "panel_package_db_sale_price": "Achte besonders auf Paketfläche, Paket-EK und danach den Ziel-DB.",
        "panel_package_ek_from_vk_db": "Achte besonders darauf, den Paket-VK über den DB-Faktor auf den Paket-EK und dann auf den Quadratmeter-EK zurückzurechnen.",
        "package_ek_from_vk_db": "Achte besonders auf die Rückwärtsrechnung vom Paket-VK über den DB-Faktor zum Paket-EK.",
        "package_price": "Achte besonders auf die Reihenfolge Einzelvolumen, Paketvolumen und Paketpreis.",
        "panel_package_price": "Achte besonders auf Fläche pro Platte, Paketfläche und Paketpreis über den Quadratmeterpreis.",
        "panel_count_from_area": "Achte besonders darauf, zuerst die Fläche pro Platte zu bilden und die Gesamtfläche dadurch zu teilen.",
        "flooring_packages": "Achte besonders auf Fläche pro Stück, Paketfläche und das Aufrunden auf volle Pakete.",
        "running_meter_piece_count": "Achte besonders darauf, den Laufmeterbedarf durch die Stücklänge zu teilen und anschließend auf volle Stück oder volle Bund aufzurunden.",
        "absolute_db_from_ek_vk": "Achte besonders darauf, dass der absolute DB einfach die Differenz zwischen VK und EK ist.",
        "relative_db_from_ek_vk": "Achte besonders darauf, den absoluten DB ins Verhältnis zum VK zu setzen.",
        "absolute_db_from_position": "Achte besonders darauf, erst den EK aus Menge und Preisbasis aufzubauen und danach VK minus EK zu rechnen.",
        "relative_db_from_position": "Achte besonders darauf, den DB aus der konkreten Menge erst in Euro und dann als Prozent vom VK zu berechnen.",
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
        "Antworte auf Deutsch, konkret und lernorientiert, in maximal 4 Sätzen. "
        "Drei bis vier Sätze sind erwünscht, wenn sie wirklich helfen. "
        "Nutze die Angaben zur Diagnose, aber verrate im Tipp nicht den konkreten richtigen Zielwert. "
        "Nenne keine richtige Zahl, keine fertige Teilrechnung und kein Ergebnis, solange der Zwischenschritt noch nicht automatisch aufgelöst wurde. "
        "Erkläre den wahrscheinlichsten Fehler mit etwas Kontext und nenne nur den nächsten kleinen Korrekturgedanken. "
        "Beim ersten falschen Versuch bleibst du eher allgemein und gibst nur eine Orientierung. "
        "Beim zweiten falschen Versuch wird der Zwischenschritt automatisch aufgelöst; dafür brauchst du hier keine Musterlösung zu schreiben. "
        "Denke aktiv darüber nach, ob eine Maßeinheit fehlt, ein unnötiger Faktor verwendet wurde, ein nötiger Faktor fehlt, oder ob Multiplikation und Division verwechselt wurden. "
        "Übernimm die lokale Vorprüfung nicht blind, sondern bewerte Aufgabe, Zwischenschritt, Eingabe und richtigen Wert zusammen. "
        "Verrate nicht den vollständigen restlichen Lösungsweg. "
        "Keine lange Musterlösung, kein Bezug auf vorherige Hinweise. "
        "Verwende keinen Markdown-Fettdruck, keine Sternchen und keine LaTeX-Schreibweise. "
        "Schreibe Maße und Rechnungen normal im Fließtext, zum Beispiel 6 m x 0,08 m x 0,12 m. "
        f"Zusätzliche Prüfperspektive: {AI_ERROR_EVALUATION_GUIDE} "
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
            "Schau dir vor allem die Berechnung zum korrekten Wert an: Dort siehst du, welche Maße und Faktoren in genau diesem Schritt gebraucht werden. "
            f"Diesen korrekten Wert nutzt du anschließend für {next_step['label']}."
        )
    return (
        "Ich habe diesen letzten Zwischenschritt jetzt für dich gelöst. "
        "Schau dir vor allem die Berechnung zum korrekten Wert an und prüfe, welche Einheit oder Rechenrichtung dich aus dem Tritt gebracht hat. "
        "Danach kannst du den vollständigen Rechenweg in Ruhe ansehen."
    )


def generate_resolved_step_message(task, step, raw_value, answer_value, next_step=None):
    solution_block = solution_block_for_label(task, step["label"])
    formula = solution_block.get("formula", step.get("formula_hint", ""))
    calculation = solution_block.get("calculation", "")
    next_context = (
        f"Nächster Schritt: {next_step['label']}. Nächster fachlicher Hinweis: {next_step['formula_hint']}"
        if next_step
        else "Das war der letzte Zwischenschritt; danach folgt kein weiterer Rechenschritt."
    )
    prompt = (
        "Du bist ein Lernassistent für Auszubildende im Holzhandel. "
        "Ein Zwischenschritt wurde zweimal falsch eingegeben und wird jetzt automatisch aufgelöst. "
        "Antworte auf Deutsch in 3 bis maximal 4 Sätzen. "
        "Erkläre konkret, warum die Nutzereingabe nicht zum Schritt passt und wie der korrekte Wert fachlich zustande kommt. "
        "Beziehe dich auf Aufgabe, Eingabe, berechneten Eingabewert, korrekten Wert und den aktuellen Zwischenschritt. "
        "Nutze die Begriffe 'korrekter Wert' und 'deine Eingabe', nicht 'grüner Wert' oder 'roter Wert'. "
        "Wenn es einen nächsten Schritt gibt, erkläre kurz, wie mit dem korrekten Wert dort weitergearbeitet wird. "
        "Wenn es keinen nächsten Schritt gibt, sage klar, dass dieser korrekte Wert das Ergebnis dieses letzten Schritts ist. "
        "Keine lange Musterlösung, keine Aufzählung. "
        "Verwende keinen Markdown-Fettdruck, keine Sternchen und keine LaTeX-Schreibweise. "
        "Schreibe Maße und Rechnungen normal im Fließtext, zum Beispiel 6 m x 0,08 m x 0,12 m. "
        f"Zusätzliche Prüfperspektive: {AI_ERROR_EVALUATION_GUIDE} "
        f"Aufgabe: {task['prompt']} "
        f"Zwischenschritt: {step['label']}. "
        f"Eingabe des Nutzers: {raw_value}. "
        f"Berechneter Wert der Eingabe: {format_value_for_step(answer_value, step)} {unit_label(step['unit'])}. "
        f"Korrekter Wert: {format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}. "
        f"Formel dieses Schritts: {formula}. "
        f"Berechnung dieses Schritts: {calculation}. "
        f"{next_context}"
    )

    try:
        if not get_openai_api_key():
            return resolved_step_message(step, next_step)

        text = call_openai_responses_api(prompt, 260)
        if text:
            return text
    except Exception:
        pass

    return resolved_step_message(step, next_step)


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
        "Antworte auf Deutsch konkret und hilfreich in maximal 4 Sätzen. "
        "Drei bis vier Sätze sind erwünscht, wenn die Antwort falsch ist. "
        "Wenn die Antwort richtig ist, schreibe sinngemäß 'Ergebnis ist korrekt' und gib einen kurzen nächsten Orientierungssatz. "
        "Wenn die Antwort falsch ist, nenne den wahrscheinlichsten Fehler etwas spezifischer und genau den nächsten Rechenschritt. "
        "Passe die Hilfe an den Versuch an: Beim ersten falschen Versuch nur leicht anstoßen; beim zweiten falschen Versuch wird in die Zwischenschritte gewechselt. "
        "Beim ersten falschen Versuch verzichtest du ausdrücklich auf konkrete Multiplikationen, Divisionen, fertige Formeln und konkrete Rechenergebnisse. "
        "Schreibe beim ersten falschen Versuch also nicht 'multipliziere A mit B', 'teile durch C' oder eine ausformulierte Formel mit konkreten Größen. "
        "Wenn der Zusatzhinweis eine Formel oder konkrete Rechenrichtung enthält, abstrahiere ihn beim ersten falschen Versuch zu einem allgemeinen Denkhinweis. "
        "Nenne keine vollständige Musterlösung und rechne die Lösung nicht aus. "
        "Wenn die Antwort falsch ist, verrate nicht die korrekte Zielzahl. "
        "Prüfe bei falschen Antworten zuerst die Faktoren der Nutzereingabe: Sind alle notwendigen Faktoren enthalten, ist ein Faktor zu viel drin, liegt ein 10/100/1000- oder Kommafehler vor, oder wurde multiplizieren und dividieren vertauscht? "
        "Wenn die lokale Vorprüfung einen fehlenden Faktor nennt, formuliere nicht als Frage, ob dieser Faktor wirklich benötigt wird; sage stattdessen, dass dieser Faktor wahrscheinlich fehlt oder noch einbezogen werden muss. "
        "Sprich nur dann von falscher Reihenfolge, wenn diese Faktor- und Richtungsprüfung keinen plausibleren Grund liefert. "
        "Bei reinen Multiplikationsketten ist die Reihenfolge normalerweise nicht der Grund für ein falsches Endergebnis. "
        "Denke aktiv darüber nach, ob eine Maßeinheit fehlt, ein unnötiger Faktor verwendet wurde, ein nötiger Faktor fehlt, oder ob Multiplikation und Division verwechselt wurden. "
        "Übernimm die lokale Vorprüfung nicht blind, sondern bewerte Aufgabe, Nutzereingabe und korrekte Lösung zusammen. "
        "Schreibe nicht 'fachlich korrekt'. "
        "Keine Floskeln, keine lange Musterlösung. "
        "Verwende keinen Markdown-Fettdruck, keine Sternchen und keine LaTeX-Schreibweise. "
        "Schreibe Maße und Rechnungen normal im Fließtext, zum Beispiel 6 m x 0,08 m x 0,12 m. "
        f"Zusätzliche Prüfperspektive: {AI_ERROR_EVALUATION_GUIDE} "
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


def fallback_main_guided_start_hint(task, answer_value):
    diagnostic = diagnose_common_mistake(task, answer_value, task["expected"])
    first_step = task.get("guided_steps", [{}])[0]
    base = (
        f"Nicht ganz. Deine Eingabe ergibt {format_user_result(answer_value, task)} {unit_label(task['unit'])}. "
    )
    if diagnostic:
        base += f"{diagnostic} "
    base += (
        "Wir gehen deshalb jetzt über die Zwischenschritte, damit der Rechenweg sauber aufgebaut wird. "
        f"Starte mit {first_step.get('label', 'dem ersten Zwischenschritt')} und rechne wirklich nur diesen einen Schritt."
    )
    return base


def generate_main_guided_start_hint(task, answer_value):
    first_step = task.get("guided_steps", [{}])[0]
    local_diagnostic = diagnose_common_mistake(task, answer_value, task["expected"]) or likely_error_focus(task)
    prompt = (
        "Du bist ein Lernassistent für Auszubildende im Holzhandel. "
        "Die Haupteingabe zur Aufgabe war zum zweiten Mal falsch; jetzt soll der Lernende über geführte Zwischenschritte weiterarbeiten. "
        "Antworte auf Deutsch in 3 bis maximal 4 Sätzen. "
        "Nenne, dass die Eingabe noch nicht passt, und beziehe dich auf den berechneten Eingabewert sowie die gesuchte Zielgröße. "
        "Nenne dabei ausdrücklich nicht die richtige Endlösung, keine konkrete Zielzahl und keine vollständige Musterrechnung. "
        "Erkläre den wahrscheinlichsten Fehler mit Bezug auf die Aufgabe und leite freundlich zum kommenden Rechenweg über. "
        "Beschreibe, dass der Rechenweg jetzt in einzelne Zwischenschritte zerlegt wird, damit zuerst nur der nächste kleine Schritt geprüft wird. "
        "Verrate nicht den vollständigen Rechenweg und nicht unnötig alle späteren Schritte. "
        "Verwende keinen Markdown-Fettdruck, keine Sternchen und keine LaTeX-Schreibweise. "
        "Schreibe Maße und Rechnungen normal im Fließtext, zum Beispiel 6 m x 0,08 m x 0,12 m. "
        f"Zusätzliche Prüfperspektive: {AI_ERROR_EVALUATION_GUIDE} "
        f"Aufgabe: {task['prompt']} "
        f"Gesuchte Zielgröße: {unit_label(task['unit'])}. "
        f"Eingabe des Nutzers ergibt: {format_user_result(answer_value, task)} {unit_label(task['unit'])}. "
        f"Wahrscheinliche Fehlerursache aus lokaler Vorprüfung: {local_diagnostic} "
        f"Erster Zwischenschritt: {first_step.get('label', 'erster Zwischenschritt')}. "
        f"Hinweis zum ersten Zwischenschritt: {first_step.get('formula_hint', first_step.get('correction', ''))}"
    )

    try:
        if not get_openai_api_key():
            return fallback_main_guided_start_hint(task, answer_value)

        text = call_openai_responses_api(prompt, 260)
        if text:
            return text
    except Exception:
        pass

    return fallback_main_guided_start_hint(task, answer_value)


def fallback_solution_reveal_feedback(task, answer_value):
    diagnostic = diagnose_common_mistake(task, answer_value, task["expected"]) or task["correction"]
    return (
        f"Nicht ganz. Deine Eingabe ergibt {format_user_result(answer_value, task)} {unit_label(task['unit'])}, "
        f"richtig wäre {format_expected(task)} {unit_label(task['unit'])}. "
        f"{diagnostic} Schau dir jetzt die Musterlösung an und achte besonders auf die Einheit und die Rechenrichtung."
    )


def generate_solution_reveal_feedback(task, answer_value):
    local_diagnostic = diagnose_common_mistake(task, answer_value, task["expected"]) or likely_error_focus(task)
    prompt = (
        "Du bist ein Lernassistent für Auszubildende im Holzhandel. "
        "Eine Aufgabe ohne sinnvolle geführte Zwischenschritte wurde falsch beantwortet; jetzt wird die Musterlösung eingeblendet. "
        "Antworte auf Deutsch in 3 bis maximal 4 Sätzen. "
        "Vergleiche die Nutzereingabe mit der richtigen Lösung, erkläre den wahrscheinlichsten Denkfehler und bereite kurz auf die Musterlösung vor. "
        "Du darfst den richtigen Endwert nennen, weil die Musterlösung direkt angezeigt wird. "
        "Keine lange Musterlösung, keine Aufzählung. "
        f"Zusätzliche Prüfperspektive: {AI_ERROR_EVALUATION_GUIDE} "
        f"Aufgabe: {task['prompt']} "
        f"Eingabe des Nutzers ergibt: {format_user_result(answer_value, task)} {unit_label(task['unit'])}. "
        f"Richtige Lösung: {format_expected(task)} {unit_label(task['unit'])}. "
        f"Wahrscheinliche Fehlerursache aus lokaler Vorprüfung: {local_diagnostic} "
        f"Fachlicher Zusatzhinweis: {task['correction']}"
    )

    try:
        if not get_openai_api_key():
            return fallback_solution_reveal_feedback(task, answer_value)

        text = call_openai_responses_api(prompt, 260)
        if text:
            return text
    except Exception:
        pass

    return fallback_solution_reveal_feedback(task, answer_value)


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
        "Antworte auf Deutsch in maximal 5 Sätzen. "
        "Drei bis fünf Sätze sind erwünscht, wenn dadurch klarer wird, warum der nächste Schritt folgt. "
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

        text = call_openai_responses_api(prompt, 220)
        if text:
            return ensure_sentence(text)
    except Exception:
        pass

    return fallback_guided_transition(completed_step, completed_value, next_step)


def solution_lines(task):
    return [line for line in task["solution"].splitlines() if line and line != "Rechenweg:"]


def solution_blocks(task):
    blocks = []
    current = None
    for line in solution_lines(task):
        match = re.match(r"^(\d+)\.\s+(.+)$", line)
        if match:
            if current:
                blocks.append(current)
            current = {
                "number": int(match.group(1)),
                "title": match.group(2).strip(),
                "formula": "",
                "calculation": "",
                "lines": [],
            }
            continue

        if not current:
            continue

        current["lines"].append(line)
        if line.startswith("Formel:"):
            current["formula"] = line.replace("Formel:", "", 1).strip()
        elif line.startswith("Berechnung:"):
            current["calculation"] = line.replace("Berechnung:", "", 1).strip()

    if current:
        blocks.append(current)
    return blocks


def format_solution_block(block):
    lines = [f"{block['number']}. {block['title']}"]
    if block.get("formula"):
        lines.append(f"Formel: {block['formula']}")
    if block.get("calculation"):
        lines.append(f"Berechnung: {block['calculation']}")
    return " ".join(lines)


def solution_block_for_label(task, label):
    for block in solution_blocks(task):
        if block["title"] == label:
            return {"formula": block["formula"], "calculation": block["calculation"]}

    return {}


def focused_solution_blocks(task, question_text):
    lower_question = question_text.lower()
    blocks = solution_blocks(task)
    focused_numbers = set()

    for match in re.finditer(r"(?:^|\b)(?:schritt\s*)?(\d+)(?:\.|\b)", lower_question):
        number = int(match.group(1))
        if 1 <= number <= len(blocks):
            focused_numbers.add(number)

    ordinal_map = {
        "erster": 1,
        "erste": 1,
        "zweiter": 2,
        "zweite": 2,
        "dritter": 3,
        "dritte": 3,
        "vierter": 4,
        "vierte": 4,
        "fünfter": 5,
        "fünfte": 5,
    }
    for word, number in ordinal_map.items():
        if word in lower_question and 1 <= number <= len(blocks):
            focused_numbers.add(number)

    if focused_numbers:
        return [block for block in blocks if block["number"] in focused_numbers]

    focused = []
    for block in blocks:
        title = block["title"].lower()
        if title in lower_question:
            focused.append(block)

    return focused


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


def fallback_focused_block_explanation(task, block, question_text):
    title = block.get("title", "dieser Schritt")
    calculation = block.get("calculation", "")
    lower_title = title.lower()
    left_side, separator, result_value = calculation.partition(" = ")

    if "paketfläche" in lower_title:
        match = re.search(
            r"(\d+(?:,\d+)?) Quadratmeter x (\d+) Stück = (\d+(?:,\d+)?) Quadratmeter",
            calculation,
        )
        if match:
            area_per_piece, piece_count, package_area = match.groups()
            return (
                f"In Schritt {block['number']} geht es nur um die Paketfläche, also um die Fläche aller Platten zusammen. "
                f"Die {area_per_piece} Quadratmeter kommen aus dem vorherigen Schritt und gelten für eine einzelne Platte. "
                f"Da im Paket {piece_count} Stück liegen, wird aus der Einzelfläche die gesamte verkaufbare Paketfläche von {package_area} Quadratmetern. "
                "Aus Handelssicht ist das wichtig, weil der spätere Preis nicht für eine Platte, sondern für das komplette Paket bewertet wird."
            )

    if "paketpreis" in lower_title or "gesamtpreis" in lower_title:
        if separator:
            return (
                f"In Schritt {block['number']} wird die bereits ermittelte Menge in einen Warenwert übersetzt. "
                f"Du hast also nicht mehr die Maße im Blick, sondern fragst: Was kostet diese Menge bei der angegebenen Preisbasis? "
                f"Mit {left_side} wird die Menge mit dem passenden Preis je Einheit bewertet, daraus ergeben sich {result_value}. "
                "Geschäftlich ist das der Moment, in dem aus Fläche oder Volumen ein Angebots- oder Paketwert wird."
            )
        return (
            f"In Schritt {block['number']} wird die vorher ermittelte Menge in einen Preis übersetzt. "
            "Erst hier kommt also die Preisbasis dazu; vorher wurden nur Mengen, Flächen oder Volumen aufgebaut."
        )

    if "fläche pro platte" in lower_title:
        return (
            f"In Schritt {block['number']} wird zuerst nur eine einzelne Platte betrachtet. "
            "Das trennt die Stücklogik sauber von der Paketlogik: Erst weißt du, wie viel Fläche ein Teil hat, danach kannst du daraus das Paket oder den Auftrag hochrechnen. "
            f"Der Wert {result_value if separator else 'aus diesem Schritt'} ist also die Flächenbasis pro Platte, noch nicht der komplette Verkaufsposten."
        )

    if "volumen pro stück" in lower_title:
        return (
            f"In Schritt {block['number']} wird bewusst nur ein einzelnes Stück betrachtet. "
            "So verhinderst du, dass Stückzahl, Länge, Breite und Höhe durcheinandergeraten. "
            f"Das Ergebnis {result_value if separator else 'aus diesem Schritt'} beschreibt den Rauminhalt eines Stücks; erst danach wird daraus die Gesamtmenge der Position."
        )

    if "db-faktor" in lower_title:
        return (
            f"In Schritt {block['number']} wird aus dem DB-Satz der Rechenfaktor gebildet. "
            "Aus Geschäftssicht geht es darum, welcher Anteil vom Verkaufspreis nach Abzug des gewünschten Deckungsbeitrags noch für den EK übrig bleibt. "
            f"Der Faktor {result_value if separator else 'aus diesem Schritt'} zeigt diesen EK-Anteil. "
            "Damit kann man anschließend sauber zwischen EK und VK umrechnen."
        )

    if "gesamtvolumen" in lower_title or "paketvolumen" in lower_title:
        return (
            f"In Schritt {block['number']} wird aus dem Einzelmaß die tatsächliche Gesamtmenge der Position. "
            "Im Holzhandel ist das die Mengenbasis, auf der später der Preis berechnet wird. "
            f"Wenn mehrere Stück oder ein ganzes Paket vorliegen, wird das einzelne Volumen auf diese Menge hochgezogen; hier ergibt sich {result_value if separator else 'das benötigte Gesamtvolumen'}. "
            "Erst danach ist klar, welche Kubikmeter überhaupt bewertet werden."
        )

    if "gesamter ek" in lower_title or "paket-ek" in lower_title:
        return (
            f"In Schritt {block['number']} wird aus der Holzmenge der Einkaufspreis der Position. "
            "Bis hier steht fest, wie viel Volumen im Auftrag oder Paket steckt; jetzt wird diese Menge mit dem EK pro Kubikmeter bewertet. "
            f"So entsteht der Wareneinsatz von {result_value if separator else 'dieser Position'}. "
            "Das ist geschäftlich die Grundlage, bevor ein Verkaufspreis oder ein Deckungsbeitrag kalkuliert wird."
        )

    if "gesamter vk" in lower_title or "paket-vk" in lower_title or lower_title.startswith("vk"):
        return (
            f"In Schritt {block['number']} wird aus dem EK ein Verkaufspreis. "
            "Der Verkaufspreis muss höher liegen als der Einkauf, weil daraus der gewünschte Deckungsbeitrag finanziert werden soll. "
            f"Der Wert {result_value if separator else 'aus diesem Schritt'} ist deshalb nicht nur ein rechnerischer Preis, sondern der kalkulierte Ziel-VK für die Position. "
            "Hier steckt also die kaufmännische Marge im Rechenweg."
        )

    if "preis je" in lower_title or "preis pro" in lower_title:
        return (
            f"In Schritt {block['number']} wird die Preisbasis gewechselt. "
            "Das ist im Holzhandel wichtig, weil Ware manchmal pro Kubikmeter eingekauft, aber pro Laufmeter oder Quadratmeter angeboten wird. "
            f"Der Wert {result_value if separator else 'aus diesem Schritt'} sagt dann, was genau eine gesuchte Verkaufseinheit kostet. "
            "Damit wird der Preis für den Kunden greifbarer."
        )

    if "absoluter db" in lower_title:
        return (
            f"In Schritt {block['number']} wird der Deckungsbeitrag als Eurobetrag betrachtet. "
            "Geschäftlich ist das der Rohertrag der Position: also das, was zwischen Verkaufspreis und Einkaufspreis übrig bleibt. "
            f"Hier bleiben {result_value if separator else 'Euro'} als absoluter DB stehen. "
            "Dieser Betrag muss später helfen, Personal, Lager, Fuhrpark und weitere Kosten zu tragen."
        )

    if "db-satz" in lower_title or "relativer db" in lower_title:
        return (
            f"In Schritt {block['number']} wird der Deckungsbeitrag ins Verhältnis zum Verkaufspreis gesetzt. "
            "Dadurch siehst du nicht nur den Eurobetrag, sondern wie stark die Position prozentual kalkuliert ist. "
            f"Der Wert {result_value if separator else 'aus diesem Schritt'} zeigt also die Marge in Prozent. "
            "Das macht unterschiedliche Aufträge vergleichbar."
        )

    return (
        f"Du fragst nach Schritt {block['number']}: {title}. "
        "Dieser Teil ist fachlich der Übergang von einer bekannten Größe zur nächsten kaufmännisch relevanten Größe. "
        f"Der Wert {result_value if separator else 'aus diesem Schritt'} ist deshalb nicht isoliert zu sehen, sondern beantwortet die Frage, welche Menge, Fläche, Preisbasis oder Marge in diesem Moment gebraucht wird."
    )


def fallback_step_explanation(task, question_text):
    lines = solution_lines(task)
    joined = " ".join(lines)
    lower_question = question_text.lower()
    focused_blocks = focused_solution_blocks(task, question_text)

    if focused_blocks:
        if len(focused_blocks) == 1:
            return fallback_focused_block_explanation(task, focused_blocks[0], question_text)
        return " ".join(
            fallback_focused_block_explanation(task, block, question_text)
            for block in focused_blocks[:2]
        )

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

    if task["task_type"] == "running_meter_piece_count":
        return (
            "Bei laufender Ware geht es zuerst darum, wie viele Stücklängen in den gewünschten Laufmeterbedarf passen. "
            "Dafür wird der Bedarf in Laufmetern durch die Länge eines Stücks geteilt. "
            "Wenn eine Kommazahl entsteht, wird auf volle Stück aufgerundet; bei Glattkantbrettern wird anschließend zusätzlich auf volle Bund weitergerechnet."
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
    focused_blocks = focused_solution_blocks(task, question_text)
    focused_text = (
        "\n".join(format_solution_block(block) for block in focused_blocks)
        if focused_blocks
        else "Kein einzelner Schritt wurde eindeutig erkannt; beantworte die Frage anhand des gesamten Rechenwegs."
    )
    prompt = (
        "Du bist ein Lernassistent für die Holzbranche. "
        "Erkläre auf Deutsch eine freie Rückfrage zu einem Muster-Rechenweg. "
        "Sprich ruhig, konkret und fachlich. "
        "Beantworte zuerst direkt die gestellte Frage, bevor du den Rechenweg allgemein erklärst. "
        "Wenn ein fokussierter Rechenschritt angegeben ist, erkläre hauptsächlich diesen Schritt und fasse nicht den ganzen Rechenweg zusammen. "
        "Wiederhole nicht einfach die Formel oder die Berechnung, denn diese stehen bereits sichtbar in der Musterlösung. "
        "Erkläre stattdessen die Geschäftslogik: Welche Größe ist bis zu diesem Schritt bekannt, welche kaufmännische Frage wird jetzt beantwortet, und warum braucht man diesen Schritt im Angebot oder in der Kalkulation? "
        "Du darfst konkrete Zahlen aus dem Rechenschritt verwenden, aber nur, um die fachliche Bedeutung zu erklären. "
        "Wenn die Frage eine Alternative nennt, etwa 'Warum nicht geteilt?', vergleiche diese Alternative ausdrücklich mit der richtigen Rechenrichtung. "
        "Erkläre dann, in welchem umgekehrten Fall die Alternative richtig wäre. "
        "Wenn es eine Umrechnungsaufgabe ist, erkläre die Rechenrichtung aus der Bedeutung der Einheiten heraus, nicht als bloße Formelwiederholung. "
        "Gehe ausdrücklich auf die konkreten Zahlen aus dem Rechenweg ein, nenne die Einheit mit und erkläre warum hier multipliziert oder geteilt wird. "
        "Erkläre bildhaft und anschaulich, zum Beispiel so, dass man sich die Ware oder Platte vor dem inneren Auge vorstellen kann. "
        "Vermeide Formulierungen wie 'gemeint sind hier die Schritte'. "
        "Wenn ein Prozentwert oder ein DB-Faktor vorkommt, erkläre ihn ganz konkret, zum Beispiel 100 minus 25 gleich 75 Prozent und damit 0,75 als Faktor. "
        "Verwende keine allgemeinen Floskeln wie 'die passende Formelrichtung' oder 'dieses Zwischenergebnis wird im nächsten Schritt verwendet'. "
        "Verwende keinen Markdown-Fettdruck, keine Sternchen und keine LaTeX-Schreibweise. "
        "Schreibe Maße und Rechnungen normal im Fließtext, zum Beispiel 6 m x 0,08 m x 0,12 m. "
        "Antworte so, als würde dir jemand die Frage direkt im Gespräch stellen, in 5 bis maximal 6 Sätzen, wenn die Frage das hergibt. "
        f"Fachliche Formellogik: {FORMULA_GUIDE} "
        f"Aufgabentext: {task['prompt']} "
        f"Aufgabentyp: {task['task_type']}. "
        f"Zielgröße: {unit_label(task['unit'])}. "
        f"Fokussierter Rechenschritt:\n{focused_text}\n"
        f"Rechenweg:\n{joined_lines}\n"
        f"Frage: {question_text}"
    )

    try:
        if not get_openai_api_key():
            st.session_state.explanation_backend = "fallback_no_key"
            st.session_state.explanation_backend_error = ""
            return fallback_step_explanation(task, question_text)

        text = call_openai_responses_api(prompt, 340)
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
        st.session_state.show_usage = False
        create_next_task()
        return

    if "show_theory" not in st.session_state:
        st.session_state.show_theory = False

    if "show_usage" not in st.session_state:
        st.session_state.show_usage = False

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
        st.session_state.feedback_text = "Die Eingabe konnte nicht als Rechenweg erkannt werden. Erlaubt sind Zahlen, Klammern, +, -, *, /, x, :, ×, deutsche Tausendertrennzeichen und optional ein Gleichheitszeichen mit Ergebnis."
        return

    task = st.session_state.task
    st.session_state.last_answer_display = format_user_result(answer_value, task)
    st.session_state.result_text = f"Dein Ergebnis: {format_user_result(answer_value, task)} {unit_label(task['unit'])}"
    st.session_state.last_diagnostic_hint = diagnose_common_mistake(task, answer_value, task["expected"])

    if values_match(answer_value, task["expected"], task["round_for_check"], task.get("match_mode")):
        st.session_state.feedback_kind = "success"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = fallback_hint(task, True)
        st.session_state.hint_backend = "local_correct"
        st.session_state.hint_backend_error = ""
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
        st.session_state.hint_text = generate_solution_reveal_feedback(task, answer_value)
        st.session_state.solution_visible = True
        st.session_state.task_finished = True
        st.session_state.guided_visible = False
        st.session_state.main_input_locked = False
        return

    st.session_state.solution_visible = False
    st.session_state.task_finished = False
    st.session_state.guided_visible = True
    st.session_state.main_input_locked = True
    st.session_state.guided_summary = generate_main_guided_start_hint(task, answer_value)
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
        st.session_state.guided_summary = f"{step['label']}: Die Eingabe konnte nicht gelesen werden. Erlaubt sind Zahlen, Klammern, +, -, *, /, x, :, ×, deutsche Tausendertrennzeichen und optional ein Gleichheitszeichen mit Ergebnis."
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
                    generate_resolved_step_message(task, step, raw_value, answer_value),
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
                generate_resolved_step_message(task, step, raw_value, answer_value, next_step),
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
    st.caption("Hier kannst du dir den angezeigten Rechenweg KI-generiert erklären lassen.")
    with st.form("solution_explanation_form", clear_on_submit=False):
        st.text_input(
            "Was möchtest du zum Rechenweg KI-generiert erklärt bekommen?",
            key="explanation_request",
            placeholder="Zum Beispiel: Warum muss ich hier durch 0,75 teilen?",
        )
        explanation_submitted = st.form_submit_button("Schritte per KI erklären", type="primary")

    if explanation_submitted:
        handle_explanation_request()

    if st.session_state.explanation_error:
        st.warning(st.session_state.explanation_error)

    if st.session_state.explanation_text:
        st.info(f"KI-Erklärung: {clean_ai_output(st.session_state.explanation_text)}")


def keypad_append(input_key, token):
    st.session_state[input_key] = f"{st.session_state.get(input_key, '')}{token}"


def keypad_backspace(input_key):
    st.session_state[input_key] = st.session_state.get(input_key, "")[:-1]


def keypad_clear(input_key):
    st.session_state[input_key] = ""


MOBILE_KEYPAD_ACTIVE = False


def render_mobile_keypad(input_key, instance_key, disabled=False):
    # Mobile Eingabehilfe ist vorerst deaktiviert; Code bleibt für die nächste UI-Runde erhalten.
    if not MOBILE_KEYPAD_ACTIVE:
        return

    st.markdown("<div class='mobile-keypad-note'>Mobile Eingabehilfe</div>", unsafe_allow_html=True)
    rows = [
        [("7", "7"), ("8", "8"), ("9", "9"), ("/", "/")],
        [("4", "4"), ("5", "5"), ("6", "6"), ("*", "*")],
        [("1", "1"), ("2", "2"), ("3", "3"), (":", ":")],
        [("0", "0"), (",", ","), ("=", "="), ("-", "-")],
        [("(", "("), (")", ")"), ("x", "x"), ("⌫", "backspace")],
    ]

    for row_index, row in enumerate(rows):
        columns = st.columns(len(row))
        for col_index, (label, token) in enumerate(row):
            key = f"mobile_keypad_{instance_key}_{row_index}_{col_index}"
            if token == "backspace":
                columns[col_index].button(
                    label,
                    key=key,
                    disabled=disabled,
                    on_click=keypad_backspace,
                    args=(input_key,),
                    use_container_width=True,
                )
            else:
                columns[col_index].button(
                    label,
                    key=key,
                    disabled=disabled,
                    on_click=keypad_append,
                    args=(input_key, token),
                    use_container_width=True,
                )

    if st.button(
        "Eingabe leeren",
        key=f"mobile_keypad_{instance_key}_clear",
        disabled=disabled,
        on_click=keypad_clear,
        args=(input_key,),
        use_container_width=True,
    ):
        pass


def go_to_next_task(same_task_type=False):
    st.session_state.task_number += 1
    if same_task_type:
        st.session_state.next_task_type_override = st.session_state.task["task_type"]
    else:
        st.session_state.next_task_type_override = None
    st.session_state.pending_next_task = True
    st.rerun()


st.set_page_config(page_title="Holzrechner", page_icon="🪵", layout="centered")
init_state()

st.markdown(
    """
    <style>
        [data-testid="InputInstructions"] {
            display: none;
        }

        [data-testid="stAppViewContainer"] .block-container {
            padding-top: 1.25rem;
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
            border: 1px solid rgba(148, 163, 184, 0.28);
            background: #111827;
            border-radius: 8px;
            color: #e5e7eb;
            padding: 1.05rem 1.15rem;
            margin: 0.8rem 0;
            line-height: 1.55;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
        }

        .resolved-title {
            font-weight: 700;
            margin-bottom: 0.35rem;
            color: #f9fafb;
        }

        .resolved-message {
            margin-top: 0.45rem;
            margin-bottom: 0.45rem;
        }

        .resolved-formula {
            margin-top: 0.65rem;
            margin-bottom: 0.65rem;
            padding: 0.85rem 0.9rem;
            border-radius: 6px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(2, 6, 23, 0.45);
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }

        .resolved-formula-title {
            color: #cbd5e1;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .resolved-formula-text {
            color: #d1fae5;
            font-weight: 700;
        }

        .resolved-bad {
            color: #fb7185;
            font-weight: 700;
        }

        .resolved-good {
            color: #34d399;
            font-weight: 700;
        }

        .resolved-next {
            color: #86efac;
            font-weight: 700;
            margin-top: 0.35rem;
        }

        .task-reminder {
            border-left: 4px solid #16a34a;
            background: rgba(34, 197, 94, 0.08);
            border-radius: 8px;
            padding: 0.95rem 1rem;
            margin: 1rem 0 1.15rem 0;
            line-height: 1.6;
        }

        .task-reminder p {
            margin: 0 0 0.75rem 0;
        }

        .task-reminder p:last-child {
            margin-bottom: 0;
        }

        .mobile-keypad-note,
        div[class*="st-key-mobile_keypad_"] {
            display: none;
        }

        @media (max-width: 720px) {
            .mobile-keypad-note {
                display: block;
                color: #6b7280;
                font-size: 0.9rem;
                font-weight: 600;
                margin: -0.15rem 0 0.3rem 0;
            }

            div[class*="st-key-mobile_keypad_"] {
                display: block;
                margin: 0 !important;
                padding: 0 !important;
            }

            div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-mobile_keypad_"]) {
                display: grid !important;
                grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
                gap: 0.25rem !important;
                width: 100%;
                margin: 0 0 0.25rem 0 !important;
            }

            div[data-testid="stHorizontalBlock"]:has(div[class*="st-key-mobile_keypad_"]) > div {
                width: 100% !important;
                min-width: 0 !important;
                flex: unset !important;
                padding: 0 !important;
            }

            div[class*="st-key-mobile_keypad_"] button {
                width: 100%;
                min-height: 2.45rem;
                height: 2.45rem;
                padding: 0.2rem 0.15rem;
                border-radius: 8px;
                font-size: 1.05rem;
                font-weight: 700;
            }

            div[class*="st-key-mobile_keypad_"] button p {
                line-height: 1;
            }

            div[class*="st-key-mobile_keypad_"] + div[class*="st-key-mobile_keypad_"] {
                margin-top: 0;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_task_reminder():
    paragraphs = [
        f"<p>{escape(part).replace(chr(10), '<br>')}</p>"
        for part in st.session_state.task["prompt"].split("\n\n")
    ]
    st.markdown(
        f"<div class='task-reminder'>{''.join(paragraphs)}</div>",
        unsafe_allow_html=True,
    )


st.title("Holzrechner")
st.write(
    "Das ist dein Holzrechner zum Üben: Hier kannst du dir in Ruhe das Rechenwissen aneignen, "
    "das du im Holzhandel für Mengen, Preise, Einheiten und Deckungsbeitrag brauchst. "
    "Sauberes Umrechnen ist jeden Tag entscheidend: Volumen, Fläche, Laufmeter, Preise und DB müssen sicher sitzen, "
    "damit Angebote, Kalkulationen und Kundengespräche fachlich stimmen."
)

def render_learning_sections():
    st.subheader("Theorie auffrischen")
    if st.button(
        "Theorie ausblenden" if st.session_state.show_theory else "Theorie anzeigen",
        key="theory_toggle_button",
    ):
        st.session_state.show_theory = not st.session_state.show_theory
        st.rerun()

    if st.session_state.show_theory:
        render_theory_section()
        if st.button("Theorie ausblenden", key="theory_hide_bottom_button"):
            st.session_state.show_theory = False
            st.rerun()

    st.subheader("Bedienung des Holzrechners")
    if st.button(
        "Bedienung ausblenden" if st.session_state.show_usage else "Bedienung anzeigen",
        key="usage_toggle_button",
    ):
        st.session_state.show_usage = not st.session_state.show_usage
        st.rerun()

    if st.session_state.show_usage:
        st.write(
            "Die Aufgaben werden zufällig ausgewählt und die Aufgabentypen wechseln sich laufend ab. "
            "Es gibt keine feste Endaufgabe; du kannst also so lange weiterüben, wie du möchtest."
        )
        st.write(
            "Bei Fehleingaben bekommst du KI-generiertes Feedback: Die Eingabe wird mit der Aufgabenstellung und der passenden "
            "Lösung verglichen, damit der Hinweis möglichst genau auf den wahrscheinlichen Denkfehler eingeht. "
            "Der Ablauf ist dabei bewusst ruhig aufgebaut: Zuerst hast du zwei Versuche für die Hauptaufgabe. "
            "Wenn es dann noch nicht passt, führt dich der Holzrechner Schritt für Schritt durch die Rechnung; auch dort hast du "
            "je Zwischenschritt zwei Versuche, bevor der aktuelle Schritt aufgelöst wird und du mit dem nächsten Wert weiterrechnen kannst. "
            "Am Ende erscheint eine Musterlösung mit dem vollständigen Rechenweg, und zu diesem Rechenweg kannst du dir zusätzlich "
            "KI-generierte Erklärungen geben lassen."
        )
        st.markdown(
            """
Beispiele, die funktionieren:

- **Dividieren mit Schrägstrich:** `0,4536 / 0,0054`
- **Dividieren mit Doppelpunkt und Ergebnis:** `0,4536 : 0,0054 = 84`
- **Multiplizieren mit x:** `6 x 0,08 x 0,12`
- **Multiplizieren mit Sternchen und Ergebnis:** `6*0,08*0,12=0,0576`
- **Mit Klammern rechnen:** `(142,86 - 100) / 142,86 * 100`
- **Klammern beim Dividieren nutzen:** `0,4536 / (0,20 x 0,027)`
- **Leerzeichen und Tausendertrennzeichen:** Leerzeichen sind egal; deutsche Tausendertrennzeichen wie `3.465` werden ebenfalls erkannt.
"""
        )
        st.markdown(
            "**Du kannst direkt das Endergebnis eingeben, den Rechenweg als Formel notieren oder beides mit Gleichheitszeichen "
            "verbinden. Alle Rechenwege und Ergebnisse können direkt hier geprüft werden. Deswegen kannst du deinen Taschenrechner "
            "ganz entspannt zur Seite legen.**"
        )
        st.write(
            "Am angenehmsten lässt sich der Holzrechner an einem Desktop-PC oder Laptop bedienen, weil Formeln, Zwischenschritte "
            "und Erklärungen dort deutlich übersichtlicher bleiben als auf dem Handy."
        )
        if st.button("Bedienung ausblenden", key="usage_hide_bottom_button"):
            st.session_state.show_usage = False
            st.rerun()


st.subheader(f"Aufgabe {st.session_state.task_number}")
st.write(st.session_state.task["prompt"])

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

render_mobile_keypad(
    "answer_input",
    "answer",
    disabled=st.session_state.task_finished or st.session_state.get("main_input_locked", False),
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

if (
    st.session_state.hint_text
    and not st.session_state.solution_visible
    and not st.session_state.guided_visible
):
    if st.session_state.feedback_kind == "success":
        st.success(f"KI-Hinweis: {clean_ai_output(st.session_state.hint_text)}")
    else:
        st.warning(f"KI-Hinweis: {clean_ai_output(st.session_state.hint_text)}")

show_initial_guided_hint = (
    st.session_state.guided_visible
    and not st.session_state.task_finished
    and not st.session_state.solution_visible
    and st.session_state.get("guided_step_index", 0) == 0
    and not st.session_state.get("guided_completed", [])
    and bool(st.session_state.get("guided_summary", ""))
)

if show_initial_guided_hint:
    render_guided_summary()

if (
    st.session_state.guided_visible
    and not st.session_state.task_finished
    and not st.session_state.solution_visible
    and st.session_state.get("guided_step_index", 0) == 0
    and not st.session_state.get("guided_completed", [])
):
    st.warning("Jetzt mit Zwischenergebnissen weiterrechnen: Unten kannst du die Aufgabe Schritt für Schritt aufbauen.")

if st.session_state.guided_visible:
    if not st.session_state.solution_visible:
        render_task_reminder()

    st.subheader("Geführte Zwischenschritte")

    for completed_entry in st.session_state.guided_completed:
        render_guided_completed_entry(completed_entry)

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

        render_mobile_keypad(f"guided_input_{current_index + 1}", f"guided_{current_index + 1}")

        if guided_submitted:
            handle_guided_submission()

    if st.session_state.get("guided_summary", "") and not show_initial_guided_hint:
        render_guided_summary()
    elif st.session_state.get("hint_text", "") and not st.session_state.task_finished:
        st.warning(f"KI-Hinweis: {clean_ai_output(st.session_state.hint_text)}")

if st.session_state.solution_visible:
    if st.session_state.hint_text:
        st.warning(f"KI-Hinweis: {clean_ai_output(st.session_state.hint_text)}")
    else:
        st.warning(
            "Nicht ganz. "
            f"Dein Ergebnis: {st.session_state.last_answer_display} {unit_label(st.session_state.task['unit'])}. "
            f"Richtig wäre: {format_expected(st.session_state.task)} {unit_label(st.session_state.task['unit'])}."
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
        go_to_next_task(same_task_type=repeat_task_type)

render_learning_sections()
