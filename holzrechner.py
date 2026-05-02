import ast
import random
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import streamlit as st


PRODUCTS = [
    {"name": "KVH", "kind": "beam"},
    {"name": "BSH", "kind": "beam"},
    {"name": "Konstruktionslatte", "kind": "beam"},
    {"name": "OSB-Platte", "kind": "panel"},
    {"name": "Siebdruckplatte", "kind": "panel"},
    {"name": "3-Schicht-Platte", "kind": "panel"},
]

BEAM_WIDTHS_BY_LEVEL = {
    1: [Decimal("0.06"), Decimal("0.08"), Decimal("0.10"), Decimal("0.12")],
    2: [Decimal("0.06"), Decimal("0.08"), Decimal("0.09"), Decimal("0.10"), Decimal("0.12")],
    3: [Decimal("0.06"), Decimal("0.075"), Decimal("0.08"), Decimal("0.09"), Decimal("0.10"), Decimal("0.12")],
}
BEAM_HEIGHTS_BY_LEVEL = {
    1: [Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.16"), Decimal("0.20")],
    2: [Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.20")],
    3: [Decimal("0.08"), Decimal("0.10"), Decimal("0.12"), Decimal("0.14"), Decimal("0.16"), Decimal("0.18"), Decimal("0.20")],
}
BEAM_LENGTHS_BY_LEVEL = {
    1: [Decimal("3.0"), Decimal("4.0"), Decimal("5.0"), Decimal("6.0")],
    2: [Decimal("3.5"), Decimal("4.0"), Decimal("4.5"), Decimal("5.0"), Decimal("6.0"), Decimal("7.0")],
    3: [Decimal("3.5"), Decimal("4.5"), Decimal("5.5"), Decimal("6.0"), Decimal("6.5"), Decimal("7.5")],
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


def q(value_str):
    return Decimal(value_str)


def format_decimal(value, places):
    quant = q("1") if places == 0 else q("1." + ("0" * places))
    return str(value.quantize(quant, rounding=ROUND_HALF_UP)).replace(".", ",")


def format_m(value):
    return format_decimal(value, 2).rstrip("0").rstrip(",")


def format_cm(value):
    return format_decimal(value * 100, 1).rstrip("0").rstrip(",")


def unit_label(unit):
    return UNIT_LABELS.get(unit, unit)


def make_guided_step(label, expected, unit, display_places, round_for_check, correction):
    return {
        "label": label,
        "expected": expected,
        "unit": unit,
        "display_places": display_places,
        "round_for_check": round_for_check,
        "correction": correction,
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
        return random.choices([1, 2, 3], weights=[6, 3, 1], k=1)[0]
    if base_level == 2:
        return random.choices([1, 2, 3], weights=[3, 4, 2], k=1)[0]
    return random.choices([1, 2, 3], weights=[2, 3, 4], k=1)[0]


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


def generate_beam_product():
    choices = [p for p in PRODUCTS if p["kind"] == "beam"]
    return random.choice(choices)


def generate_panel_product():
    choices = [p for p in PRODUCTS if p["kind"] == "panel"]
    return random.choice(choices)


def task_volume_beam(level):
    product = generate_beam_product()
    length_m = choice_for_level(BEAM_LENGTHS_BY_LEVEL, level)
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    result = length_m * width_m * height_m * Decimal(count)

    prompt = random.choice(
        [
            f"Eine Position {product['name']} umfasst {count} Stück mit je {format_m(length_m)} m Länge, {format_cm(width_m)} cm Breite und {format_cm(height_m)} cm Höhe.\n\nWie viele Kubikmeter sind das insgesamt?",
            f"Für eine Lieferung {product['name']} liegen {count} Stück mit {format_m(length_m)} m Länge sowie {format_cm(width_m)} cm x {format_cm(height_m)} cm Querschnitt vor.\n\nWie viele Kubikmeter ergeben sich daraus?",
            f"Ein Kunde interessiert sich für {count} Stück {product['name']} mit {format_m(length_m)} m Länge, {format_cm(width_m)} cm Breite und {format_cm(height_m)} cm Höhe.\n\nWie viele Kubikmeter Ware sind das?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. Volumen pro Stück = {format_m(length_m)} x {format_decimal(width_m, 2)} x "
        f"{format_decimal(height_m, 2)} = {format_decimal(length_m * width_m * height_m, 3)} Kubikmeter\n"
        f"2. Gesamtvolumen = {format_decimal(length_m * width_m * height_m, 3)} x {count} = "
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
    product = generate_beam_product()
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = width_m * height_m * m3_price

    prompt = random.choice(
        [
            f"Ein Angebot für {product['name']} liegt bei {format_decimal(m3_price, 0)} Euro pro Kubikmeter. Der Querschnitt beträgt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n\nWie teuer ist 1 Laufmeter?",
            f"Der Kunde fragt nach dem Laufmeterpreis für {product['name']}. Die Ware kostet {format_decimal(m3_price, 0)} Euro pro Kubikmeter und hat {format_cm(width_m)} cm x {format_cm(height_m)} cm Querschnitt.\n\nWie teuer ist 1 Laufmeter?",
        ]
    )

    cross_section = width_m * height_m
    solution = (
        "Rechenweg:\n"
        f"1. Querschnitt in Quadratmetern = {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} = "
        f"{format_decimal(cross_section, 4)} Quadratmeter\n"
        f"2. Volumen von 1 Laufmeter = {format_decimal(cross_section, 4)} x 1 = "
        f"{format_decimal(cross_section, 4)} Kubikmeter\n"
        f"3. Preis je Laufmeter = {format_decimal(cross_section, 4)} x {format_decimal(m3_price, 0)} = "
        f"{format_decimal(result, 2)} Euro"
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "price_per_running_meter",
        "correction": "Prüfe, ob du erst den Querschnitt in Quadratmetern gebildet und daraus das Volumen von 1 Laufmeter bestimmt hast.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                cross_section.normalize(),
                "m2",
                4,
                False,
                "Bilde zuerst den Querschnitt in Quadratmetern aus Breite x Höhe.",
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
    thickness_m = choice_for_level(THICKNESSES_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = thickness_m * m3_price

    prompt = random.choice(
        [
            f"Eine {product['name']} ist {format_cm(thickness_m)} cm dick. Ein Kubikmeter kostet {format_decimal(m3_price, 0)} Euro.\n\nWie teuer ist 1 Quadratmeter dieser Platte?",
            f"Für eine {product['name']} liegt ein Preis von {format_decimal(m3_price, 0)} Euro pro Kubikmeter vor. Die Platte ist {format_cm(thickness_m)} cm dick.\n\nWie teuer ist 1 Quadratmeter?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. Volumen von 1 Quadratmeter Platte = 1 x {format_decimal(thickness_m, 3)} = "
        f"{format_decimal(thickness_m, 3)} Kubikmeter\n"
        f"2. Preis je Quadratmeter = {format_decimal(thickness_m, 3)} x {format_decimal(m3_price, 0)} = "
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
                "Volumen von 1 Quadratmeter",
                thickness_m.normalize(),
                "m3",
                3,
                False,
                "Ein Quadratmeter Platte mal Dicke ergibt das Volumen.",
            ),
            make_guided_step(
                "Preis je Quadratmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere dieses Volumen mit dem Preis pro Kubikmeter.",
            ),
        ],
    }


def task_square_meters_from_volume(level):
    product = generate_panel_product()
    thickness_m = choice_for_level(THICKNESSES_BY_LEVEL, level)
    if level == 1:
        square_meters = Decimal(random.choice([12, 18, 24, 30, 36, 48]))
    elif level == 2:
        square_meters = Decimal(random.choice([15, 21, 27, 33, 39, 45]))
    else:
        square_meters = Decimal(random.choice([14, 22, 28, 34, 42, 54]))
    total_volume = square_meters * thickness_m
    result = square_meters

    prompt = random.choice(
        [
            f"Es liegt eine Ware von {format_decimal(total_volume, 3)} Kubikmeter {product['name']} vor. Die Platte ist {format_cm(thickness_m)} cm dick.\n\nWie viele Quadratmeter sind das?",
            f"Ein Kunde fragt nach der Fläche einer {product['name']}. Verfügbar sind {format_decimal(total_volume, 3)} Kubikmeter bei {format_cm(thickness_m)} cm Dicke.\n\nWie viele Quadratmeter ergeben sich?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        "1. Formel: Quadratmeter = Kubikmeter / Dicke\n"
        f"2. Quadratmeter = {format_decimal(total_volume, 3)} / {format_decimal(thickness_m, 3)} = "
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
        f"2. Gesamtpreis = {format_decimal(total_volume, 3)} x {format_decimal(m3_price, 0)} = "
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


def task_running_meters_from_volume(level):
    product = generate_beam_product()
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    if level == 1:
        running_meters = Decimal(random.choice([20, 24, 30, 36, 40, 48]))
    elif level == 2:
        running_meters = Decimal(random.choice([18, 26, 32, 38, 44, 50]))
    else:
        running_meters = Decimal(random.choice([21, 27, 35, 41, 45, 55]))
    total_volume = width_m * height_m * running_meters

    prompt = random.choice(
        [
            f"Für {product['name']} liegen insgesamt {format_decimal(total_volume, 3)} Kubikmeter vor. Der Querschnitt beträgt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n\nWie viele Laufmeter sind das?",
            f"Ein Kunde möchte wissen, wie viele Laufmeter {product['name']} in {format_decimal(total_volume, 3)} Kubikmeter enthalten sind. Der Querschnitt beträgt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n\nWie viele Laufmeter sind das?",
        ]
    )

    cross_section = width_m * height_m
    solution = (
        "Rechenweg:\n"
        f"1. Querschnitt in Quadratmetern = {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} = "
        f"{format_decimal(cross_section, 4)} Quadratmeter\n"
        "2. Formel: Laufmeter = Kubikmeter / Querschnitt\n"
        f"3. Laufmeter = {format_decimal(total_volume, 3)} / {format_decimal(cross_section, 4)} = "
        f"{format_decimal(running_meters, 0)} Laufmeter"
    )

    return {
        "prompt": prompt,
        "expected": running_meters.normalize(),
        "unit": "lfm",
        "display_places": 0,
        "round_for_check": False,
        "task_type": "running_meters_from_volume",
        "correction": "Bilde zuerst den Querschnitt in Quadratmetern und teile dann das Gesamtvolumen durch diesen Querschnitt.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                cross_section.normalize(),
                "m2",
                4,
                False,
                "Bilde zuerst den Querschnitt in Quadratmetern aus Breite x Höhe.",
            ),
            make_guided_step(
                "Laufmeter",
                running_meters.normalize(),
                "lfm",
                0,
                False,
                "Teile danach das Gesamtvolumen durch den Querschnitt.",
            ),
        ],
    }


def task_db_sale_price(level):
    product = generate_beam_product()
    length_m = choice_for_level(BEAM_LENGTHS_BY_LEVEL, level)
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
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

    prompt = random.choice(
        [
            f"Ein Kubikmeter {product['name']} kostet im EK {format_decimal(ek_price_m3, 0)} Euro. Du hast {count} Stück im Format {format_m(length_m)} m x {format_cm(width_m)} cm x {format_cm(height_m)} cm. Es soll ein DB von {format_decimal(db_percent, 0)} % erzielt werden.\n\nWie hoch ist der gesamte VK für diese Position?",
            f"Für eine Anfrage liegen {count} Stück {product['name']} im Format {format_m(length_m)} m x {format_cm(width_m)} cm x {format_cm(height_m)} cm vor. Der EK liegt bei {format_decimal(ek_price_m3, 0)} Euro pro Kubikmeter, der Ziel-DB bei {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der gesamte VK?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. Gesamtvolumen = {format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x {count} = "
        f"{format_decimal(total_volume, 3)} Kubikmeter\n"
        f"2. Gesamter EK = {format_decimal(total_volume, 3)} x {format_decimal(ek_price_m3, 0)} = "
        f"{format_decimal(total_ek, 2)} Euro\n"
        f"3. VK bei {format_decimal(db_percent, 0)} % DB = {format_decimal(total_ek, 2)} / {format_decimal(divisor, 2)} = "
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
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere das Gesamtvolumen mit dem EK pro Kubikmeter.",
            ),
            make_guided_step(
                "Gesamter VK",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den gesamten EK durch 1 minus DB-Satz.",
            ),
        ],
    }


def task_volume_from_running_meters(level):
    product = generate_beam_product()
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    running_meters = Decimal(random.choice([18, 24, 30, 36, 42, 48]))
    result = width_m * height_m * running_meters

    prompt = random.choice(
        [
            f"Ein Kunde plant {format_decimal(running_meters, 0)} Laufmeter {product['name']} mit einem Querschnitt von {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n\nWie viele Kubikmeter sind das?",
            f"Für eine Position {product['name']} liegen {format_decimal(running_meters, 0)} Laufmeter bei {format_cm(width_m)} cm x {format_cm(height_m)} cm Querschnitt vor.\n\nWie viele Kubikmeter ergeben sich daraus?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. Querschnitt in Quadratmetern = {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} = {format_decimal(width_m * height_m, 4)} Quadratmeter\n"
        f"2. Volumen = {format_decimal(width_m * height_m, 4)} x {format_decimal(running_meters, 0)} = {format_decimal(result, 3)} Kubikmeter"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "volume_from_running_meters",
        "correction": "Bilde zuerst den Querschnitt in Quadratmetern und multipliziere diesen dann mit den Laufmetern.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                (width_m * height_m).normalize(),
                "m2",
                4,
                False,
                "Bilde zuerst den Querschnitt in Quadratmetern aus Breite x Höhe.",
            ),
            make_guided_step(
                "Gesamtvolumen",
                result.normalize(),
                "m3",
                3,
                False,
                "Multipliziere danach den Querschnitt mit den Laufmetern.",
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
        f"2. Volumen = {format_decimal(total_price, 2)} / {format_decimal(m3_price, 0)} = {format_decimal(total_volume, 3)} Kubikmeter"
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
    product = generate_beam_product()
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    price_per_lfm = choice_for_level(RUNNING_METER_PRICES_BY_LEVEL, level)
    cross_section = width_m * height_m
    result = price_per_lfm / cross_section

    prompt = random.choice(
        [
            f"Ein Laufmeter {product['name']} kostet {format_decimal(price_per_lfm, 2)} Euro. Der Querschnitt beträgt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n\nWie hoch ist der Preis pro Kubikmeter?",
            f"Für {product['name']} liegt ein Laufmeterpreis von {format_decimal(price_per_lfm, 2)} Euro vor. Der Querschnitt beträgt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n\nWie hoch ist der Preis pro Kubikmeter?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. Querschnitt in Quadratmetern = {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} = {format_decimal(cross_section, 4)} Quadratmeter\n"
        f"2. Preis pro Kubikmeter = {format_decimal(price_per_lfm, 2)} / {format_decimal(cross_section, 4)} = {format_decimal(result, 2)} Euro"
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "m3_price_from_running_meter",
        "correction": "Teile den Laufmeterpreis durch den Querschnitt in Quadratmetern, um auf den Kubikmeterpreis zu kommen.",
        "solution": solution,
        "guided_steps": [
            make_guided_step(
                "Querschnitt",
                cross_section.normalize(),
                "m2",
                4,
                False,
                "Bilde zuerst den Querschnitt in Quadratmetern aus Breite x Höhe.",
            ),
            make_guided_step(
                "Preis pro Kubikmeter",
                result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Teile den Laufmeterpreis durch den Querschnitt.",
            ),
        ],
    }


def task_ek_from_vk_db(level):
    product = generate_beam_product()
    length_m = choice_for_level(BEAM_LENGTHS_BY_LEVEL, level)
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    db_percent = Decimal(random.choice([25, 30, 35]) if level == 1 else random.choice([27, 30, 33, 35]) if level == 2 else random.choice([28, 31, 34, 37]))
    ek_price_m3 = choice_for_level(M3_PRICES_BY_LEVEL, level)

    total_volume = length_m * width_m * height_m * Decimal(count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    total_vk = total_ek / divisor

    prompt = random.choice(
        [
            f"Für {count} Stück {product['name']} im Format {format_m(length_m)} m x {format_cm(width_m)} cm x {format_cm(height_m)} cm liegt ein VK von {format_decimal(total_vk, 2)} Euro vor. Kalkuliert wurde mit {format_decimal(db_percent, 0)} % DB.\n\nWie hoch ist der gesamte EK?",
            f"Ein Angebot über {count} Stück {product['name']} im Format {format_m(length_m)} m x {format_cm(width_m)} cm x {format_cm(height_m)} cm endet bei {format_decimal(total_vk, 2)} Euro VK. Der DB beträgt {format_decimal(db_percent, 0)} %.\n\nWie hoch ist der gesamte EK?",
        ]
    )

    solution = (
        "Rechenweg:\n"
        f"1. EK = VK x (1 - DB)\n"
        f"2. EK = {format_decimal(total_vk, 2)} x {format_decimal(divisor, 2)} = {format_decimal(total_ek, 2)} Euro"
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
            ),
            make_guided_step(
                "Gesamter EK",
                total_ek.quantize(q("1.00"), rounding=ROUND_HALF_UP),
                "EUR",
                2,
                True,
                "Multipliziere den VK mit dem DB-Faktor.",
            ),
        ],
    }


TASK_GENERATORS = [
    task_volume_beam,
    task_volume_from_running_meters,
    task_volume_from_total_price,
    task_running_meters_from_volume,
    task_price_per_running_meter,
    task_m3_price_from_running_meter,
    task_price_per_square_meter,
    task_square_meters_from_volume,
    task_total_price_from_volume,
    task_db_sale_price,
    task_ek_from_vk_db,
]

TASKS_BY_LEVEL = {
    1: [
        task_volume_beam,
        task_volume_from_running_meters,
        task_total_price_from_volume,
        task_price_per_square_meter,
        task_db_sale_price,
    ],
    2: [
        task_volume_beam,
        task_volume_from_running_meters,
        task_volume_from_total_price,
        task_total_price_from_volume,
        task_price_per_square_meter,
        task_square_meters_from_volume,
        task_running_meters_from_volume,
        task_price_per_running_meter,
        task_db_sale_price,
        task_ek_from_vk_db,
    ],
    3: TASK_GENERATORS,
}


def values_match(user_value, expected_value, round_for_check):
    if round_for_check:
        return user_value.quantize(q("1.00"), rounding=ROUND_HALF_UP) == expected_value
    return user_value == expected_value


def format_expected(task):
    return format_decimal(task["expected"], task["display_places"])


def format_value_for_task(value, task):
    return format_decimal(value, task["display_places"])


def format_value_for_step(value, step):
    return format_decimal(value, step["display_places"])


def fallback_hint(task, is_correct):
    if is_correct:
        return (
            "Das passt fachlich. Geh den Rechenweg noch einmal kurz durch und prüfe, "
            "welche Größe du zuerst umgerechnet hast und warum das Ergebnis in dieser Einheit stimmig ist."
        )
    return (
        f"{task['correction']} Prüfe danach noch einmal, welche Eingangsgröße gegeben ist "
        "und auf welche Zielgröße du tatsächlich kommen sollst."
    )


def generate_hint(task, answer_value, is_correct):
    prompt = (
        "Du bist ein Lernassistent für die Holzbranche. "
        "Gib auf Deutsch einen hilfreichen Hinweis mit drei bis fünf kurzen Sätzen. "
        "Sprich klar, ruhig und fachlich. "
        "Wenn die Antwort richtig ist, bestätige das knapp, benenne den richtigen Rechenansatz und gib einen kurzen Merksatz für ähnliche Aufgaben. "
        "Wenn die Antwort falsch ist, erkläre knapp, an welcher Stelle der Denkweg wahrscheinlich abgebogen ist, "
        "welche Zwischenrechnung als Nächstes sinnvoll wäre und worauf bei der Einheit geachtet werden muss. "
        "Prüfe dabei ausdrücklich auf typische Fehler wie Zahlendreher, falschen Preiswert, falsche Einheit, "
        "mal statt geteilt, geteilt statt mal, falsche Reihenfolge im Rechenweg oder eine passende Formel mit der falschen Eingabezahl. "
        "Wenn so ein Muster wahrscheinlich ist, benenne es ausdrücklich. "
        "Gib nicht die komplette Musterlösung Wort für Wort aus. "
        f"Aufgabentext: {task['prompt']} "
        f"Aufgabentyp: {task['task_type']}. "
        f"Nutzerergebnis: {format_value_for_task(answer_value, task)} {unit_label(task['unit'])}. "
        f"Korrekte Lösung: {format_expected(task)} {unit_label(task['unit'])}. "
        f"Bewertung: {'richtig' if is_correct else 'falsch'}. "
        f"Lokaler Korrekturhinweis: {task['correction']}"
    )

    try:
        from openai import OpenAI

        api_key = None
        if "OPENAI_API_KEY" in st.secrets:
            api_key = st.secrets["OPENAI_API_KEY"]
        elif "openai_api_key" in st.secrets:
            api_key = st.secrets["openai_api_key"]

        if not api_key:
            return fallback_hint(task, is_correct)

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            max_output_tokens=160,
        )
        text = (response.output_text or "").strip()
        return text if text else fallback_hint(task, is_correct)
    except Exception:
        return fallback_hint(task, is_correct)


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
    st.session_state.solution_visible = False
    st.session_state.task_finished = False
    st.session_state.answer_input = ""
    st.session_state.hint_text = ""
    st.session_state.guided_visible = False
    st.session_state.guided_summary = ""
    st.session_state.guided_step_feedback = []
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
    st.session_state.result_text = f"Dein Ergebnis: {format_value_for_task(answer_value, task)} {unit_label(task['unit'])}"

    if values_match(answer_value, task["expected"], task["round_for_check"]):
        st.session_state.feedback_kind = "success"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = "Hey, super gemacht, auf zur nächsten Aufgabe."
        st.session_state.solution_visible = True
        st.session_state.task_finished = True
        st.session_state.guided_visible = False
        st.session_state.guided_summary = ""
        st.session_state.guided_step_feedback = []
        return

    if st.session_state.attempt < 4:
        st.session_state.feedback_kind = "warning"
        rest = 4 - st.session_state.attempt
        st.session_state.feedback_text = ""
        st.session_state.hint_text = f"{generate_hint(task, answer_value, False)} Du hast noch {rest} Versuch(e)."
        st.session_state.guided_visible = True
        st.session_state.guided_summary = ""
        st.session_state.guided_step_feedback = []
        st.session_state.attempt += 1
        return

    st.session_state.feedback_kind = "warning"
    st.session_state.feedback_text = ""
    st.session_state.hint_text = f"{generate_hint(task, answer_value, False)} Die Aufgabe wird jetzt aufgelöst."
    st.session_state.solution_visible = True
    st.session_state.task_finished = True
    st.session_state.guided_visible = False


def handle_guided_submission():
    guided_steps = st.session_state.task.get("guided_steps", [])
    feedback = []
    all_correct = True
    has_error = False

    for index, step in enumerate(guided_steps, start=1):
        raw_value = st.session_state.get(f"guided_input_{index}", "").strip()

        if not raw_value:
            all_correct = False
            feedback.append(
                {
                    "kind": "warning",
                    "text": f"{step['label']}: Bitte gib hier einen Rechenweg oder ein Ergebnis ein.",
                }
            )
            continue

        try:
            answer_value = evaluate_expression(raw_value)
        except (InvalidOperation, SyntaxError, ZeroDivisionError):
            all_correct = False
            has_error = True
            feedback.append(
                {
                    "kind": "error",
                    "text": f"{step['label']}: Die Eingabe konnte nicht gelesen werden. Erlaubt sind Zahlen, Klammern sowie +, -, *, /, x und :",
                }
            )
            continue

        if values_match(answer_value, step["expected"], step["round_for_check"]):
            feedback.append(
                {
                    "kind": "success",
                    "text": f"{step['label']}: passt. Ergebnis {format_value_for_step(answer_value, step)} {unit_label(step['unit'])}.",
                }
            )
            continue

        all_correct = False
        feedback.append(
            {
                "kind": "warning",
                "text": (
                    f"{step['label']}: noch nicht richtig. {step['correction']} "
                    f"Richtig wären {format_value_for_step(step['expected'], step)} {unit_label(step['unit'])}."
                ),
            }
        )

    st.session_state.guided_step_feedback = feedback

    if all_correct:
        st.session_state.feedback_kind = "success"
        st.session_state.feedback_text = ""
        st.session_state.hint_text = "Hey, super gemacht, auf zur nächsten Aufgabe."
        st.session_state.guided_summary = "Alle Zwischenschritte passen. Damit ist auch die Aufgabe sauber gelöst."
        st.session_state.solution_visible = True
        st.session_state.task_finished = True
        return

    st.session_state.feedback_kind = "error" if has_error else "warning"
    st.session_state.feedback_text = ""
    st.session_state.guided_summary = "Geh die Zwischenschritte noch einmal in Ruhe durch. Du kannst die Felder direkt hier weiterverwenden."


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

        div.stButton > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"] {
            background-color: #16a34a;
            border-color: #16a34a;
            color: white;
        }

        div.stButton > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
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

col1, col2 = st.columns(2)
col1.metric("Aufgabe", st.session_state.task_number)
col2.metric("Schwierigkeit", st.session_state.level)

st.subheader("Aufgabe")
st.write(st.session_state.task["prompt"])
st.caption("Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein.")

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

if st.session_state.result_text:
    st.write(st.session_state.result_text)

if st.session_state.hint_text:
    if st.session_state.feedback_kind == "success":
        st.success(f"Hinweis: {st.session_state.hint_text}")
    else:
        st.warning(f"Hinweis: {st.session_state.hint_text}")

if st.session_state.guided_visible and not st.session_state.task_finished:
    st.subheader("Geführte Zwischenschritte")
    st.write("Wenn du magst, kannst du die Aufgabe hier Schritt für Schritt auflösen.")

    with st.form("guided_steps_form", clear_on_submit=False):
        for index, step in enumerate(st.session_state.task.get("guided_steps", []), start=1):
            st.text_input(
                f"{step['label']} in {unit_label(step['unit'])}",
                key=f"guided_input_{index}",
                placeholder="Zum Beispiel 0,96 * 350",
            )
        guided_submitted = st.form_submit_button("Zwischenschritte prüfen", type="primary")

    if guided_submitted:
        handle_guided_submission()

    if st.session_state.guided_summary:
        if st.session_state.feedback_kind == "success":
            st.success(st.session_state.guided_summary)
        else:
            st.warning(st.session_state.guided_summary)

    for item in st.session_state.guided_step_feedback:
        if item["kind"] == "success":
            st.success(item["text"])
        elif item["kind"] == "error":
            st.error(item["text"])
        else:
            st.warning(item["text"])

if st.session_state.solution_visible:
    st.info(f"Richtige Lösung: {format_expected(st.session_state.task)} {unit_label(st.session_state.task['unit'])}")
    st.code(st.session_state.task["solution"])

if st.session_state.task_finished:
    if st.button("Nächste Aufgabe", type="primary"):
        st.session_state.task_number += 1
        st.session_state.pending_next_task = True
        st.rerun()
