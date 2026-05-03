import ast
import json
import os
import random
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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
]

STRUCTURAL_WIDTHS_BY_LEVEL = {
    1: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12")],
    2: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14")],
    3: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16")],
}
STRUCTURAL_HEIGHTS_BY_LEVEL = {
    1: [Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.16"), Decimal("0.20")],
    2: [Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.20")],
    3: [Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20")],
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
    1: [Decimal("3.0"), Decimal("4.0"), Decimal("5.0"), Decimal("6.0")],
    2: [Decimal("3.0"), Decimal("4.0"), Decimal("4.5"), Decimal("5.0"), Decimal("6.0")],
    3: [Decimal("3.0"), Decimal("4.0"), Decimal("5.0"), Decimal("6.0")],
}
COUNTS_BY_LEVEL = {
    1: [4, 6, 8, 10, 12],
    2: [5, 6, 8, 10, 12, 14],
    3: [5, 7, 9, 11, 14, 18],
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

UNIT_LABELS = {
    "m3": "Kubikmeter",
    "m2": "Quadratmeter",
    "lfm": "Laufmeter",
    "EUR": "Euro",
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


def make_guided_step(label, expected, unit, display_places, round_for_check, correction, formula_hint=None):
    return {
        "label": label,
        "expected": expected,
        "unit": unit,
        "display_places": display_places,
        "round_for_check": round_for_check,
        "correction": correction,
        "formula_hint": formula_hint or correction,
    }


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


def evaluate_expression(text):
    cleaned = text.strip().replace(",", ".")
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


def task_volume_beam(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m = choice_for_level(STRUCTURAL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(STRUCTURAL_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    result = length_m * width_m * height_m * Decimal(count)
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: {count} Stück {product['name']} mit je {format_m(length_m)} m Länge, {width_text} Breite und {height_text} Höhe. In diesem Querschnitt liegen normalerweise {package_count} Stück im Paket.\n\nWie viele Kubikmeter sind das insgesamt?",
            f"Für eine Lieferung {product['name']} liegen {count} Stück mit {format_m(length_m)} m Länge sowie {width_text} x {height_text} Querschnitt vor. Ein volles Paket würde hier {package_count} Stück enthalten.\n\nWie viele Kubikmeter ergeben sich daraus?",
            f"Eine Kundin interessiert sich für {count} Stück {product['name']} mit {format_m(length_m)} m Länge, {width_text} Breite und {height_text} Höhe. Im Paket liegen bei diesem Maß normalerweise {package_count} Stück.\n\nWie viele Kubikmeter Ware sind das?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Kubikmeter = Länge x Breite x Höhe x Stückzahl\n"
        f"2. Gesamtvolumen = {format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x "
        f"{format_decimal(height_m, 2)} Meter x {count} Stück = "
        f"{format_decimal(result, 3)} Kubikmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "volume_beam",
        "correction": "Achte darauf, zuerst das Volumen pro Stück aus Länge x Breite x Höhe zu berechnen und danach mit der Stückzahl zu multiplizieren.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Volumen pro Stück",
                (length_m * width_m * height_m).normalize(),
                "m3",
                3,
                False,
                "Rechne zuerst Länge x Breite x Höhe für ein einzelnes Stück.",
            ),
            make_guided_step(
                "Gesamtvolumen",
                result.normalize(),
                "m3",
                3,
                False,
                "Multipliziere danach das Volumen pro Stück mit der Stückzahl.",
            ),
        ],
    }


def task_price_per_running_meter(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = width_m * height_m * m3_price
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Die Ware kostet {format_decimal(m3_price, 0)} Euro pro Kubikmeter, ist {width_text} breit, {thickness_text} stark und die Bretter sind {format_m(board_length)} m lang.\n\nWie teuer ist 1 Laufmeter?",
            f"Für ein Angebot liegt {display_name} vor. Der Preis beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter. Ein Brett ist {format_m(board_length)} m lang und hat {width_text} x {thickness_text} Querschnitt.\n\nWie teuer ist 1 Laufmeter?",
        ]
    )

    cross_section = width_m * height_m
    solution = (
        "Rechenweg:\n"
        "1. Formel: Euro pro Laufmeter = Euro pro Kubikmeter x Breite x Höhe\n"
        f"2. Preis je Laufmeter = {format_decimal(m3_price, 0)} Euro pro Kubikmeter x {format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter = "
        f"{format_decimal(result, 2)} Euro"
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
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                cross_section.normalize(),
                "m2",
                4,
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
            ),
        ],
    }


def task_price_per_square_meter(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    thickness_m = choice_for_level(THICKNESSES_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = thickness_m * m3_price
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Eine {product['name']} im Format {panel_format} ist {thickness_text} dick. Ein Kubikmeter kostet {format_decimal(m3_price, 0)} Euro.\n\nWie teuer ist 1 Quadratmeter dieser Platte?",
            f"Für eine {product['name']} im Format {panel_format} liegt ein Preis von {format_decimal(m3_price, 0)} Euro pro Kubikmeter vor. Die Platte ist {thickness_text} dick.\n\nWie teuer ist 1 Quadratmeter?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Euro pro Quadratmeter = Euro pro Kubikmeter x Dicke\n"
        f"2. Preis je Quadratmeter = {format_decimal(m3_price, 0)} Euro pro Kubikmeter x {format_decimal(thickness_m, 3)} Meter = "
        f"{format_decimal(result, 2)} Euro"
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
    thickness_m = choice_for_level(THICKNESSES_BY_LEVEL, level)
    if level == 1:
        square_meters = Decimal(random.choice([12, 18, 24, 30, 36, 48]))
    elif level == 2:
        square_meters = Decimal(random.choice([15, 21, 27, 33, 39, 45]))
    else:
        square_meters = Decimal(random.choice([14, 22, 28, 34, 42, 54]))
    total_volume = square_meters * thickness_m
    result = square_meters
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Es liegt eine Ware von {format_decimal(total_volume, 3)} Kubikmeter {product['name']} im Format {panel_format} vor. Die Platte ist {thickness_text} dick.\n\nWie viele Quadratmeter sind das?",
            f"Ein Kunde fragt nach der Fläche einer {product['name']} im Format {panel_format}. Verfügbar sind {format_decimal(total_volume, 3)} Kubikmeter bei {thickness_text} Dicke.\n\nWie viele Quadratmeter ergeben sich?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Quadratmeter = Kubikmeter / Dicke\n"
        f"2. Quadratmeter = {format_decimal(total_volume, 3)} Kubikmeter / {format_decimal(thickness_m, 3)} Meter = "
        f"{format_decimal(result, 0)} Quadratmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m2",
        "display_places": 0,
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
                0,
                False,
                "Teile das Volumen durch die Dicke.",
            ),
        ],
    }


def task_volume_from_square_meters(level):
    product = generate_panel_product()
    panel_format = panel_format_text(product)
    thickness_m = choice_for_level(THICKNESSES_BY_LEVEL, level)
    if level == 1:
        square_meters = Decimal(random.choice([12, 18, 24, 30, 36]))
    elif level == 2:
        square_meters = Decimal(random.choice([15, 21, 27, 33, 39]))
    else:
        square_meters = Decimal(random.choice([14, 22, 28, 34, 42]))
    result = square_meters * thickness_m
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Für eine {product['name']} im Format {panel_format} liegen {format_decimal(square_meters, 0)} Quadratmeter vor. Die Platte ist {thickness_text} dick.\n\nWie viele Kubikmeter sind das?",
            f"Ein Kunde fragt nach dem Volumen einer {product['name']} im Format {panel_format}. Verfügbar sind {format_decimal(square_meters, 0)} Quadratmeter bei {thickness_text} Dicke.\n\nWie viele Kubikmeter ergeben sich?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Kubikmeter = Quadratmeter x Dicke\n"
        f"2. Kubikmeter = {format_decimal(square_meters, 0)} Quadratmeter x {format_decimal(thickness_m, 3)} Meter = "
        f"{format_decimal(result, 3)} Kubikmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "volume_from_square_meters",
        "correction": "Multipliziere die Quadratmeter mit der Dicke in Meter, um auf das Volumen zu kommen.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Kubikmeter",
                result.normalize(),
                "m3",
                3,
                False,
                "Rechne hier direkt Quadratmeter x Dicke in Meter.",
                "Formel: Quadratmeter x Dicke",
            ),
        ],
    }


def task_total_price_from_volume(level):
    product = random.choice(PRODUCTS)
    total_volume = choice_for_level(TOTAL_VOLUMES_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = total_volume * m3_price

    prompt = random.choice(
        [
            f"Eine Position {product['name']} hat insgesamt {format_decimal(total_volume, 3)} Kubikmeter. Der Preis beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Gesamtpreis?",
            f"Für eine Ware {product['name']} liegt ein Volumen von {format_decimal(total_volume, 3)} Kubikmeter vor. Das Angebot steht bei {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Gesamtpreis?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Gesamtpreis = Volumen x Preis pro Kubikmeter\n"
        f"2. Gesamtpreis = {format_decimal(total_volume, 3)} Kubikmeter x {format_decimal(m3_price, 0)} Euro pro Kubikmeter = "
        f"{format_decimal(result, 2)} Euro"
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
            ),
        ],
    }


def task_square_meters_from_running_meters(level):
    product = generate_hobelware_product()
    display_name = hobelware_display_name(product)
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    thickness_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    board_length = choice_for_level(HOBEL_LENGTHS_BY_LEVEL, level)
    board_count = random.choice([4, 6, 8, 10, 12])
    running_meters = board_length * Decimal(board_count)
    result = running_meters * width_m
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {format_decimal(running_meters, 0)} Laufmeter {display_name}. Ein Brett ist {format_m(board_length)} m lang, die Ware ist {width_text} breit und {thickness_text} stark.\n\nWie viele Quadratmeter sind das?",
            f"Ein Kunde möchte wissen, wie viele Quadratmeter {display_name} aus {format_decimal(running_meters, 0)} Laufmetern ergeben. Die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWie viele Quadratmeter sind das?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Quadratmeter = Laufmeter x Breite\n"
        f"2. Quadratmeter = {format_decimal(running_meters, 0)} Laufmeter x {format_decimal(width_m, 2)} Meter = "
        f"{format_decimal(result, 3)} Quadratmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m2",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "square_meters_from_running_meters",
        "correction": "Für Hobelware rechnest du die Laufmeter mit der Breite in Meter zu Quadratmetern um.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Quadratmeter",
                result.normalize(),
                "m2",
                3,
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
    if level == 1:
        running_meters = Decimal(random.choice([20, 24, 30, 36, 40, 48]))
    elif level == 2:
        running_meters = Decimal(random.choice([18, 26, 32, 38, 44, 50]))
    else:
        running_meters = Decimal(random.choice([21, 27, 35, 41, 45, 55]))
    total_volume = width_m * height_m * running_meters
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Insgesamt liegen {format_decimal(total_volume, 3)} Kubikmeter vor. Die Bretter sind {format_m(board_length)} m lang und haben {width_text} Breite bei {thickness_text} Stärke.\n\nWie viele Laufmeter sind das?",
            f"Ein Kunde möchte wissen, wie viele Laufmeter {display_name} in {format_decimal(total_volume, 3)} Kubikmeter enthalten sind. Ein Brett ist {format_m(board_length)} m lang, die Ware hat {width_text} Breite und {thickness_text} Stärke.\n\nWie viele Laufmeter sind das?",
        ]
    )

    cross_section = width_m * height_m
    solution = (
        "Rechenweg:\n"
        "1. Formel: Laufmeter = Kubikmeter / (Breite x Höhe)\n"
        f"2. Laufmeter = {format_decimal(total_volume, 3)} Kubikmeter / ({format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter) = "
        f"{format_decimal(running_meters, 0)} Laufmeter"
    )

    return {
        "prompt": prompt,
        "expected": running_meters.normalize(),
        "unit": "lfm",
        "display_places": 0,
        "round_for_check": False,
        "task_type": "running_meters_from_volume",
        "correction": "Rechne zuerst Breite x Höhe mit Meterwerten und teile dann das Gesamtvolumen durch dieses Ergebnis.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Breite x Höhe",
                cross_section.normalize(),
                "m2",
                4,
                False,
                "Rechne zuerst Breite x Höhe mit Meterwerten.",
                "Formel: Breite x Höhe",
            ),
            make_guided_step(
                "Laufmeter",
                running_meters.normalize(),
                "lfm",
                0,
                False,
                "Teile danach das Gesamtvolumen durch den Querschnitt.",
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
    square_meters = Decimal(random.choice([12, 18, 24, 30, 36]))
    result = square_meters / width_m
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(thickness_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"{request_intro()}: {display_name}. Verfügbar sind {format_decimal(square_meters, 0)} Quadratmeter. Die Bretter sind {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWie viele Laufmeter sind das?",
            f"Ein Kunde fragt nach den Laufmetern einer {display_name}. Verfügbar sind {format_decimal(square_meters, 0)} Quadratmeter. Die Ware ist {format_m(board_length)} m lang, {width_text} breit und {thickness_text} stark.\n\nWie viele Laufmeter ergeben sich?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Laufmeter = Quadratmeter / Breite\n"
        f"2. Laufmeter = {format_decimal(square_meters, 0)} Quadratmeter / {format_decimal(width_m, 2)} Meter = "
        f"{format_decimal(result, 0)} Laufmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "lfm",
        "display_places": 0,
        "round_for_check": False,
        "task_type": "running_meters_from_square_meters",
        "correction": "Für Hobelware teilst du die Quadratmeter durch die Breite in Meter, um die Laufmeter zu erhalten.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Laufmeter",
                result.normalize(),
                "lfm",
                0,
                False,
                "Rechne hier direkt Quadratmeter / Breite in Meter.",
                "Formel: Quadratmeter / Breite",
            ),
        ],
    }


def task_db_sale_price(level):
    product = generate_structural_product()
    length_m = choice_for_level(STRUCTURAL_LENGTHS_BY_LEVEL, level)
    width_m = choice_for_level(STRUCTURAL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(STRUCTURAL_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    ek_price_m3 = choice_for_level(M3_PRICES_BY_LEVEL, level)
    if level == 1:
        db_percent = Decimal(random.choice([25, 30, 35]))
    elif level == 2:
        db_percent = Decimal(random.choice([27, 30, 33, 35]))
    else:
        db_percent = Decimal(random.choice([28, 31, 34, 37]))

    total_volume = length_m * width_m * height_m * Decimal(count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    result = total_ek / divisor
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. Ein Kubikmeter kostet im EK {format_decimal(ek_price_m3, 0)} Euro, bei diesem Querschnitt liegen {package_count} Stück im Paket. Es soll ein DB von {format_decimal(db_percent, 0)} % erzielt werden.\n\nWie hoch ist der gesamte VK für diese Position?",
            f"Für eine Anfrage liegen {count} Stück {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text} vor. Der EK liegt bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter, der Ziel-DB bei {format_decimal(db_percent, 0)} %. Ein Paket in diesem Maß enthält {package_count} Stück.\n\nWie hoch ist der gesamte VK?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Gesamtvolumen = Länge x Breite x Höhe x Stückzahl\n"
        f"2. Gesamtvolumen = {format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter x {count} Stück = "
        f"{format_decimal(total_volume, 3)} Kubikmeter\n"
        f"3. Gesamter EK = {format_decimal(total_volume, 3)} Kubikmeter x {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter = "
        f"{format_decimal(total_ek, 2)} Euro\n"
        f"4. VK bei {format_decimal(db_percent, 0)} % DB = {format_decimal(total_ek, 2)} Euro / {format_decimal(divisor, 2)} = "
        f"{format_decimal(result, 2)} Euro"
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "db_sale_price",
        "correction": "Rechne zuerst das Gesamtvolumen und daraus den gesamten EK. Für den VK mit DB teilst du den EK durch 1 minus DB-Satz, also zum Beispiel durch 0,70 bei 30 % DB.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Gesamtvolumen",
                total_volume.normalize(),
                "m3",
                3,
                False,
                "Rechne zuerst Länge x Breite x Höhe x Stückzahl.",
                "Formel: Länge x Breite x Höhe x Stückzahl",
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
    width_m = choice_for_level(HOBEL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(HOBEL_THICKNESSES_BY_LEVEL, level)
    running_meters = Decimal(random.choice([18, 24, 30, 36, 42, 48]))
    result = width_m * height_m * running_meters
    width_text = display_measure(width_m, ("cm", "m"))
    thickness_text = display_measure(height_m, ("mm", "cm"))

    prompt = random.choice(
        [
            f"Ein Kunde plant {format_decimal(running_meters, 0)} Laufmeter {product['name']} mit einem Querschnitt von {width_text} x {thickness_text}.\n\nWie viele Kubikmeter sind das?",
            f"Für eine Position {product['name']} liegen {format_decimal(running_meters, 0)} Laufmeter bei {width_text} x {thickness_text} Querschnitt vor.\n\nWie viele Kubikmeter ergeben sich daraus?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Kubikmeter = Laufmeter x Breite x Höhe\n"
        f"2. Volumen = {format_decimal(running_meters, 0)} Laufmeter x {format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter = {format_decimal(result, 3)} Kubikmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "volume_from_running_meters",
        "correction": "Rechne die Laufmeter direkt mit Breite und Höhe in Meter zu Kubikmeter um.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Gesamtvolumen",
                result.normalize(),
                "m3",
                3,
                False,
                "Rechne hier direkt Laufmeter x Breite x Höhe.",
                "Formel: Laufmeter x Breite x Höhe",
            ),
        ],
    }


def task_volume_from_total_price(level):
    product = random.choice(PRODUCTS)
    total_volume = choice_for_level(TOTAL_VOLUMES_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    total_price = total_volume * m3_price

    prompt = random.choice(
        [
            f"Für {product['name']} liegt ein Gesamtpreis von {format_decimal(total_price, 2)} Euro vor. Der Preis beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie viele Kubikmeter sind angeboten?",
            f"Ein Angebot über {product['name']} endet bei {format_decimal(total_price, 2)} Euro. Berechnet wird mit {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie viele Kubikmeter Ware stecken dahinter?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. Volumen = Gesamtpreis / Preis pro Kubikmeter\n"
        f"2. Volumen = {format_decimal(total_price, 2)} Euro / {format_decimal(m3_price, 0)} Euro pro Kubikmeter = {format_decimal(total_volume, 3)} Kubikmeter"
    )

    return {
        "prompt": prompt,
        "expected": total_volume.normalize(),
        "unit": "m3",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "volume_from_total_price",
        "correction": "Teile den Gesamtpreis durch den Preis pro Kubikmeter.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Kubikmeter",
                total_volume.normalize(),
                "m3",
                3,
                False,
                "Teile den Gesamtpreis durch den Preis pro Kubikmeter.",
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

    solution = (
        "Rechenweg:\n"
        "1. Formel: Euro pro Kubikmeter = Euro pro Laufmeter / (Breite x Höhe)\n"
        f"2. Preis pro Kubikmeter = {format_decimal(price_per_lfm, 2)} Euro pro Laufmeter / ({format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter) = {format_decimal(result, 2)} Euro pro Kubikmeter"
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
        "guided_steps": [
            make_guided_step(
                "Breite x Höhe",
                cross_section.normalize(),
                "m2",
                4,
                False,
                "Rechne zuerst Breite x Höhe mit Meterwerten.",
                "Formel: Breite x Höhe",
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
    width_m = choice_for_level(STRUCTURAL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(STRUCTURAL_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    package_count = structural_package_count(width_m, height_m)
    db_percent = Decimal(random.choice([25, 30, 35]) if level == 1 else random.choice([27, 30, 33, 35]) if level == 2 else random.choice([28, 31, 34, 37]))
    ek_price_m3 = choice_for_level(M3_PRICES_BY_LEVEL, level)

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

    solution = (
        "Rechenweg:\n"
        f"1. EK = VK x (1 - DB)\n"
        f"2. EK = {format_decimal(total_vk, 2)} Euro x {format_decimal(divisor, 2)} = {format_decimal(total_ek, 2)} Euro"
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
    width_m = choice_for_level(STRUCTURAL_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(STRUCTURAL_HEIGHTS_BY_LEVEL, level)
    package_count = structural_package_count(width_m, height_m)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = length_m * width_m * height_m * Decimal(package_count) * m3_price
    width_text, height_text = display_measure_pair_same_unit(width_m, height_m, ("cm", "m"))

    prompt = random.choice(
        [
            f"{request_intro()}: ein volles Paket {product['name']} im Format {format_m(length_m)} m x {width_text} x {height_text}. In diesem Querschnitt liegen {package_count} Stück im Paket. Der EK liegt bei {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Paketpreis im EK?",
            f"Für ein Angebot liegt ein volles Paket {product['name']} vor. Das Maß beträgt {format_m(length_m)} m x {width_text} x {height_text}, im Paket liegen {package_count} Stück und der EK beträgt {format_decimal(m3_price, 0)} Euro pro Kubikmeter.\n\nWie hoch ist der Paketpreis?",
        ]
    )

    total_volume = length_m * width_m * height_m * Decimal(package_count)
    solution = (
        "Rechenweg:\n"
        "1. Formel: Paketpreis = Länge x Breite x Höhe x Stückzahl x Euro pro Kubikmeter\n"
        f"2. Paketpreis = {format_m(length_m)} Meter x {format_decimal(width_m, 2)} Meter x {format_decimal(height_m, 2)} Meter x {package_count} Stück x {format_decimal(m3_price, 0)} Euro pro Kubikmeter = {format_decimal(result, 2)} Euro\n"
        f"3. Kontrollschritt: Das Paket hat insgesamt {format_decimal(total_volume, 3)} Kubikmeter."
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "package_price",
        "correction": "Rechne zuerst das gesamte Paketvolumen aus Länge x Breite x Höhe x Stückzahl und multipliziere danach mit dem Preis pro Kubikmeter.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Paketvolumen",
                total_volume.normalize(),
                "m3",
                3,
                False,
                "Rechne zuerst Länge x Breite x Höhe x Stückzahl.",
                "Formel: Länge x Breite x Höhe x Stückzahl",
            ),
            make_guided_step(
                "Paketpreis",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere das Paketvolumen mit dem Preis pro Kubikmeter.",
                "Formel: Paketvolumen x Euro pro Kubikmeter",
            ),
        ],
    }


TASK_GENERATORS = [
    task_volume_beam,
    task_volume_from_running_meters,
    task_volume_from_square_meters,
    task_volume_from_total_price,
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
    task_package_price,
]

TASKS_BY_LEVEL = {
    1: [
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
        task_package_price,
    ],
    2: [
        task_volume_beam,
        task_volume_from_running_meters,
        task_volume_from_square_meters,
        task_volume_from_total_price,
        task_total_price_from_volume,
        task_price_per_square_meter,
        task_square_meters_from_volume,
        task_square_meters_from_running_meters,
        task_running_meters_from_volume,
        task_running_meters_from_square_meters,
        task_price_per_running_meter,
        task_db_sale_price,
        task_ek_from_vk_db,
        task_package_price,
    ],
    3: TASK_GENERATORS,
}


def values_match(user_value, expected_value, round_for_check):
    if round_for_check:
        return user_value.quantize(q("1.00"), rounding=ROUND_HALF_UP) == expected_value
    return user_value == expected_value


def guided_values_match(user_value, expected_value, round_for_check, current_index, unit):
    if values_match(user_value, expected_value, round_for_check):
        return True

    if current_index == 0 or unit == "EUR":
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
    if task["unit"] == "EUR":
        return format_decimal(value, 2)

    if value == value.quantize(q("1"), rounding=ROUND_HALF_UP):
        return format_decimal(value, 0)

    return format_decimal(value, 4).rstrip("0").rstrip(",")


def format_value_for_step(value, step):
    return format_decimal(value, step["display_places"])


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
        "price_per_running_meter": "Achte besonders auf Querschnitt, Volumen von 1 Laufmeter und die richtige Preisbasis.",
        "price_per_square_meter": "Achte besonders auf die Dicke der Platte und auf die Preisbasis pro Kubikmeter.",
        "square_meters_from_volume": "Achte besonders auf die Richtung der Umrechnung zwischen Kubikmeter und Quadratmeter.",
        "volume_from_square_meters": "Achte besonders auf die Richtung der Umrechnung von Quadratmeter zu Kubikmeter über die Dicke.",
        "total_price_from_volume": "Achte besonders darauf, ob Volumen und Preisbasis wirklich zur Zielgröße Gesamtpreis passen.",
        "running_meters_from_volume": "Achte besonders auf die Richtung Kubikmeter zu Laufmeter und auf den Querschnitt.",
        "square_meters_from_running_meters": "Achte besonders auf die Richtung Laufmeter zu Quadratmeter über die Breite der Hobelware.",
        "running_meters_from_square_meters": "Achte besonders auf die Richtung Quadratmeter zu Laufmeter über die Breite der Hobelware.",
        "db_sale_price": "Achte besonders auf die Reihenfolge Gesamtvolumen, EK und danach VK mit DB.",
        "volume_from_running_meters": "Achte besonders auf Querschnitt mal Laufmeter und auf vollständige Maße.",
        "volume_from_total_price": "Achte besonders auf die richtige Richtung Preis zu Volumen, also teilen statt multiplizieren.",
        "m3_price_from_running_meter": "Achte besonders auf die richtige Preisbasis und auf Teilen statt Multiplizieren.",
        "ek_from_vk_db": "Achte besonders auf die Rückwärtsrechnung vom VK über den DB-Faktor zum EK.",
    }
    return focus.get(task["task_type"], "Achte besonders auf die passende Einheit, die Rechenrichtung und die Preisbasis.")


def progressive_main_hint(task, answer_value, attempt):
    if attempt <= 1:
        return generate_hint(task, answer_value, False)
    if attempt == 2:
        first_step = task.get("guided_steps", [{}])[0]
        return f"{generate_hint(task, answer_value, False)} {first_step.get('formula_hint', '')}".strip()
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


def fallback_hint(task, is_correct):
    if is_correct:
        return "Passt. Das Ergebnis stimmt fachlich."
    diagnostic = st.session_state.get("last_diagnostic_hint", "")
    return f"{diagnostic} {task['correction']}".strip()


def generate_hint(task, answer_value, is_correct):
    local_diagnostic = diagnose_common_mistake(task, answer_value, task["expected"])
    formula_line = solution_lines(task)[0] if solution_lines(task) else ""
    prompt = (
        "Du bist ein Lernassistent für den Holzhandel. "
        "Antworte auf Deutsch kurz und konkret in maximal 3 Sätzen. "
        "Wenn die Antwort richtig ist, bestätige das knapp. "
        "Wenn die Antwort falsch ist, nenne kurz den wahrscheinlichsten Fehler und genau den nächsten Rechenschritt. "
        "Keine Floskeln, keine lange Musterlösung. "
        f"Aufgabe: {task['prompt']} "
        f"Antwort des Nutzers: {format_user_result(answer_value, task)} {unit_label(task['unit'])}. "
        f"Korrekte Lösung: {format_expected(task)} {unit_label(task['unit'])}. "
        f"Formel: {formula_line} "
        f"Typische Fehler: {local_diagnostic or likely_error_focus(task)} "
        f"Zusatzhinweis: {task['correction']}"
    )

    try:
        if not get_openai_api_key():
            st.session_state.hint_backend = "fallback_no_key"
            st.session_state.hint_backend_error = ""
            return fallback_hint(task, is_correct)

        text = call_openai_responses_api(prompt, 100)
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
        f"{completed_step['label']} passt: {format_value_for_step(completed_value, completed_step)} "
        f"{unit_label(completed_step['unit'])}. "
        f"Als Nächstes: {next_step['label']}. {next_step['formula_hint']}"
    )


def generate_guided_transition_hint(task, completed_step, completed_value, next_step):
    prompt = (
        "Du bist ein Lernassistent für den Holzhandel. "
        "Ein Zwischenschritt wurde richtig gelöst. "
        "Antworte auf Deutsch in maximal 2 kurzen Sätzen. "
        "Nenne das Zwischenergebnis mit Einheit und erkläre konkret, wie damit im nächsten Schritt weitergerechnet wird. "
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

        text = call_openai_responses_api(prompt, 90)
        if text:
            return text
    except Exception:
        pass

    return fallback_guided_transition(completed_step, completed_value, next_step)


def solution_lines(task):
    return [line for line in task["solution"].splitlines() if line and line != "Rechenweg:"]


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
        "Beziehe dich direkt auf die gestellte Frage. "
        "Wenn es eine Umrechnungsaufgabe ist, nenne zuerst die zugrunde liegende Formelrichtung und erst danach die eingesetzten Zahlen. "
        "Gehe ausdrücklich auf die konkreten Zahlen aus dem Rechenweg ein, nenne die Einheit mit und erkläre genau, warum hier multipliziert oder geteilt wird. "
        "Erkläre bildhaft und anschaulich, zum Beispiel so, dass man sich die Ware oder Platte vor dem inneren Auge vorstellen kann. "
        "Vermeide Formulierungen wie 'gemeint sind hier die Schritte'. "
        "Wenn ein Prozentwert oder ein DB-Faktor vorkommt, erkläre ihn ganz konkret, zum Beispiel 100 minus 25 gleich 75 Prozent und damit 0,75 als Faktor. "
        "Verwende keine allgemeinen Floskeln wie 'die passende Formelrichtung' ohne sie direkt mit der konkreten Formel und den Zahlen zu verbinden. "
        "Antworte so, als würde dir jemand die Frage direkt im Gespräch stellen. "
        f"Fachliche Formellogik: {FORMULA_GUIDE} "
        f"Aufgabentext: {task['prompt']} "
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


def choose_task(level, recent_task_types):
    candidates = TASKS_BY_LEVEL[level]
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
    task = choose_task(level, st.session_state.recent_task_types)(level)
    st.session_state.task = task
    st.session_state.level = level
    st.session_state.attempt = 1
    st.session_state.feedback_kind = None
    st.session_state.feedback_text = ""
    st.session_state.result_text = ""
    st.session_state.last_answer_display = ""
    st.session_state.solution_visible = False
    st.session_state.task_finished = False
    st.session_state.answer_input = ""
    st.session_state.hint_text = ""
    st.session_state.last_diagnostic_hint = ""
    st.session_state.hint_backend = ""
    st.session_state.hint_backend_error = ""
    st.session_state.guided_visible = False
    st.session_state.guided_summary = ""
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
    st.session_state.recent_task_types.append(task["task_type"])
    st.session_state.recent_task_types = st.session_state.recent_task_types[-3:]
    for index, _step in enumerate(task.get("guided_steps", []), start=1):
        st.session_state[f"guided_input_{index}"] = ""


def init_state():
    if "task_number" not in st.session_state:
        st.session_state.task_number = 1
        st.session_state.recent_task_types = []
        st.session_state.pending_next_task = False
        create_next_task()
        return

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
        st.session_state.feedback_text = "Die Eingabe konnte nicht als Rechenweg erkannt werden. Erlaubt sind Zahlen, Klammern sowie +, -, *, /, x und :"
        return

    task = st.session_state.task
    st.session_state.last_answer_display = format_user_result(answer_value, task)
    st.session_state.result_text = f"Dein Ergebnis: {format_user_result(answer_value, task)} {unit_label(task['unit'])}"
    st.session_state.last_diagnostic_hint = diagnose_common_mistake(task, answer_value, task["expected"])

    if values_match(answer_value, task["expected"], task["round_for_check"]):
        st.session_state.feedback_kind = "success"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = generate_hint(task, answer_value, True)
        st.session_state.solution_visible = False
        st.session_state.task_finished = True
        st.session_state.guided_visible = False
        st.session_state.guided_summary = ""
        st.session_state.guided_step_feedback = []
        st.session_state.explanation_text = ""
        return

    if st.session_state.attempt < 4:
        st.session_state.feedback_kind = "warning"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = progressive_main_hint(task, answer_value, st.session_state.attempt)
        st.session_state.guided_visible = st.session_state.attempt >= 2
        st.session_state.guided_summary = ""
        st.session_state.guided_step_feedback = []
        st.session_state.attempt += 1
        return

    st.session_state.feedback_kind = "warning"
    st.session_state.feedback_text = ""
    st.session_state.hint_text = generate_hint(task, answer_value, False)
    st.session_state.solution_visible = True
    st.session_state.task_finished = True
    st.session_state.guided_visible = False


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
        st.session_state.guided_step_feedback = []
        return

    try:
        answer_value = evaluate_expression(raw_value)
    except (InvalidOperation, SyntaxError, ZeroDivisionError):
        st.session_state.feedback_kind = "error"
        st.session_state.feedback_text = ""
        st.session_state.guided_summary = f"{step['label']}: Die Eingabe konnte nicht gelesen werden. Erlaubt sind Zahlen, Klammern sowie +, -, *, /, x und :"
        st.session_state.guided_step_feedback = []
        return

    if guided_values_match(answer_value, step["expected"], step["round_for_check"], current_index, step["unit"]):
        success_text = (
            f"{step['label']}: {raw_value} = "
            f"{format_value_for_step(answer_value, step)} {unit_label(step['unit'])}. Passt."
        )
        completed = st.session_state.guided_completed
        completed.append(success_text)
        st.session_state.guided_completed = completed
        st.session_state.guided_step_feedback = []

        if current_index == len(guided_steps) - 1:
            st.session_state.feedback_kind = "success"
            st.session_state.feedback_text = ""
            st.session_state.hint_text = ""
            st.session_state.guided_summary = "Alle Zwischenschritte passen. Schau dir den Rechenweg gerne noch einmal in Ruhe an."
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
        st.rerun()

    attempts = st.session_state.guided_step_attempts
    step_attempt = attempts.get(current_index, 0) + 1
    attempts[current_index] = step_attempt
    st.session_state.guided_step_attempts = attempts
    st.session_state.feedback_kind = "warning"
    st.session_state.feedback_text = ""
    st.session_state.guided_summary = progressive_step_hint(task, step, answer_value, step_attempt)
    st.session_state.guided_step_feedback = []


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
    "Du musst hier nichts im Taschenrechner ausrechnen. Es reicht, wenn du deinen Rechenweg als Formel eingibst, "
    "also zum Beispiel mit mal und geteilt."
)

st.subheader(f"Aufgabe {st.session_state.task_number}")
st.write(st.session_state.task["prompt"])
st.caption("Bitte gib deinen Rechenweg als Formel ein.")

with st.form("answer_form", clear_on_submit=False):
    st.text_input(
        "Deine Eingabe",
        key="answer_input",
        placeholder="Zum Beispiel 6 * 0,08 * 0,12 * 10",
        disabled=st.session_state.task_finished,
    )
    submitted = st.form_submit_button(
        "Bestätigen",
        disabled=st.session_state.task_finished,
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

if st.session_state.guided_visible:
    st.subheader("Geführte Zwischenschritte")
    st.write("Wenn du magst, kannst du die Aufgabe hier Schritt für Schritt auflösen.")

    for completed_text in st.session_state.guided_completed:
        st.success(completed_text)

    guided_steps = st.session_state.task.get("guided_steps", [])
    current_index = st.session_state.guided_step_index

    if not st.session_state.task_finished and current_index < len(guided_steps):
        current_step = guided_steps[current_index]

        with st.form("guided_steps_form", clear_on_submit=False):
            st.text_input(
                current_step["label"],
                key=f"guided_input_{current_index + 1}",
                placeholder="Zum Beispiel 0,96 * 350",
            )
            guided_submitted = st.form_submit_button("Schritt prüfen", type="primary")

        if guided_submitted:
            handle_guided_submission()

    if st.session_state.guided_summary:
        if st.session_state.feedback_kind == "success":
            st.success(st.session_state.guided_summary)
        else:
            st.warning(st.session_state.guided_summary)

if st.session_state.solution_visible:
    st.warning(
        "Nicht ganz. "
        f"Dein Ergebnis: {st.session_state.last_answer_display} {unit_label(st.session_state.task['unit'])}. "
        f"Richtig wäre: {format_expected(st.session_state.task)} {unit_label(st.session_state.task['unit'])}. "
        f"{st.session_state.hint_text}"
    )
    st.code(st.session_state.task["solution"])
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

if st.session_state.task_finished:
    if st.button("Nächste Aufgabe", type="primary"):
        st.session_state.task_number += 1
        st.session_state.pending_next_task = True
        st.rerun()
