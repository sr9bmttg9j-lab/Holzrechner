import ast
import random
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

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


def q(value_str):
    return Decimal(value_str)


def format_decimal(value, places):
    quant = q("1") if places == 0 else q("1." + ("0" * places))
    return str(value.quantize(quant, rounding=ROUND_HALF_UP))


def format_m(value):
    return format_decimal(value, 2).rstrip("0").rstrip(".")


def format_cm(value):
    return format_decimal(value * 100, 1).rstrip("0").rstrip(".")


def current_level(task_number):
    if task_number >= 7:
        return 3
    if task_number >= 4:
        return 2
    return 1


def pick_level(task_number):
    base_level = current_level(task_number)
    if base_level == 1:
        return 1
    if base_level == 2:
        return random.choices([1, 2], weights=[1, 3], k=1)[0]
    return random.choices([1, 2, 3], weights=[1, 2, 4], k=1)[0]


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

    prompt = (
        "Aufgabe:\n"
        f"Ein Posten {product['name']} besteht aus {count} Stueck mit je {format_m(length_m)} m Laenge, "
        f"{format_cm(width_m)} cm Breite und {format_cm(height_m)} cm Hoehe.\n"
        "Wie viele Kubikmeter sind das insgesamt?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    solution = (
        "Rechenweg:\n"
        f"1. Volumen pro Stueck = {format_m(length_m)} x {format_decimal(width_m, 2)} x "
        f"{format_decimal(height_m, 2)} = {format_decimal(length_m * width_m * height_m, 3)} m3\n"
        f"2. Gesamtvolumen = {format_decimal(length_m * width_m * height_m, 3)} x {count} = "
        f"{format_decimal(result, 3)} m3"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m3",
        "display_places": 3,
        "round_for_check": False,
        "task_type": "volume_beam",
        "correction": "Achte darauf, zuerst das Volumen pro Stueck aus Laenge x Breite x Hoehe zu berechnen und danach mit der Stueckzahl zu multiplizieren.",
        "solution": solution,
    }


def task_price_per_running_meter(level):
    product = generate_beam_product()
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = width_m * height_m * m3_price

    prompt = (
        "Aufgabe:\n"
        f"Ein Kubikmeter {product['name']} kostet {format_decimal(m3_price, 0)} Euro.\n"
        f"Der Querschnitt betraegt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n"
        "Wie teuer ist 1 laufender Meter?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    cross_section = width_m * height_m
    solution = (
        "Rechenweg:\n"
        f"1. Querschnitt in m2 = {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} = "
        f"{format_decimal(cross_section, 4)} m2\n"
        f"2. Volumen von 1 Laufmeter = {format_decimal(cross_section, 4)} x 1 = "
        f"{format_decimal(cross_section, 4)} m3\n"
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
        "correction": "Pruefe, ob du erst den Querschnitt in m2 gebildet und daraus das Volumen von 1 Laufmeter bestimmt hast.",
        "solution": solution,
    }


def task_price_per_square_meter(level):
    product = generate_panel_product()
    thickness_m = choice_for_level(THICKNESSES_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = thickness_m * m3_price

    prompt = (
        "Aufgabe:\n"
        f"Eine {product['name']} ist {format_cm(thickness_m)} cm dick.\n"
        f"Ein Kubikmeter kostet {format_decimal(m3_price, 0)} Euro.\n"
        "Wie teuer ist 1 Quadratmeter dieser Platte?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    solution = (
        "Rechenweg:\n"
        f"1. Volumen von 1 m2 Platte = 1 x {format_decimal(thickness_m, 3)} = "
        f"{format_decimal(thickness_m, 3)} m3\n"
        f"2. Preis je m2 = {format_decimal(thickness_m, 3)} x {format_decimal(m3_price, 0)} = "
        f"{format_decimal(result, 2)} Euro"
    )

    return {
        "prompt": prompt,
        "expected": result.quantize(q("1.00"), rounding=ROUND_HALF_UP),
        "unit": "EUR",
        "display_places": 2,
        "round_for_check": True,
        "task_type": "price_per_square_meter",
        "correction": "Hier brauchst du nur die Dicke der Platte. Ein Quadratmeter mal Dicke ergibt das Volumen, und dieses Volumen wird mit dem m3-Preis multipliziert.",
        "solution": solution,
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

    prompt = (
        "Aufgabe:\n"
        f"Du hast {format_decimal(total_volume, 3)} m3 {product['name']}.\n"
        f"Die Platte ist {format_cm(thickness_m)} cm dick.\n"
        "Wie viele Quadratmeter sind das?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    solution = (
        "Rechenweg:\n"
        f"1. Formel: m2 = m3 / Dicke\n"
        f"2. m2 = {format_decimal(total_volume, 3)} / {format_decimal(thickness_m, 3)} = "
        f"{format_decimal(result, 0)} m2"
    )

    return {
        "prompt": prompt,
        "expected": result.normalize(),
        "unit": "m2",
        "display_places": 0,
        "round_for_check": False,
        "task_type": "square_meters_from_volume",
        "correction": "Denk an die Grundformel m2 = m3 / Dicke. Die Zusatzangaben im Text brauchst du dafuer nicht.",
        "solution": solution,
    }


def task_total_price_from_volume(level):
    product = random.choice(PRODUCTS)
    total_volume = choice_for_level(TOTAL_VOLUMES_BY_LEVEL, level)
    m3_price = choice_for_level(M3_PRICES_BY_LEVEL, level)
    result = total_volume * m3_price

    prompt = (
        "Aufgabe:\n"
        f"Ein Posten {product['name']} hat insgesamt {format_decimal(total_volume, 3)} m3.\n"
        f"Der Preis betraegt {format_decimal(m3_price, 0)} Euro pro m3.\n"
        "Wie hoch ist der Gesamtpreis?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    solution = (
        "Rechenweg:\n"
        f"1. Gesamtpreis = Volumen x Preis pro m3\n"
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
        "correction": "Fuer den Gesamtpreis reicht Volumen x Preis pro m3. Die zusaetzlichen Angaben dienen hier nur zur Einordnung.",
        "solution": solution,
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

    prompt = (
        "Aufgabe:\n"
        f"Du hast insgesamt {format_decimal(total_volume, 3)} m3 {product['name']}.\n"
        f"Der Querschnitt betraegt {format_cm(width_m)} cm x {format_cm(height_m)} cm.\n"
        "Wie viele laufende Meter sind das?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    cross_section = width_m * height_m
    solution = (
        "Rechenweg:\n"
        f"1. Querschnitt in m2 = {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} = "
        f"{format_decimal(cross_section, 4)} m2\n"
        f"2. Formel: Laufmeter = m3 / Querschnitt\n"
        f"3. Laufmeter = {format_decimal(total_volume, 3)} / {format_decimal(cross_section, 4)} = "
        f"{format_decimal(running_meters, 0)}"
    )

    return {
        "prompt": prompt,
        "expected": running_meters.normalize(),
        "unit": "lfm",
        "display_places": 0,
        "round_for_check": False,
        "task_type": "running_meters_from_volume",
        "correction": "Bilde zuerst den Querschnitt in m2 und teile dann das Gesamtvolumen durch diesen Querschnitt.",
        "solution": solution,
    }


def task_db_sale_price(level):
    product = generate_beam_product()
    length_m = choice_for_level(BEAM_LENGTHS_BY_LEVEL, level)
    width_m = choice_for_level(BEAM_WIDTHS_BY_LEVEL, level)
    height_m = choice_for_level(BEAM_HEIGHTS_BY_LEVEL, level)
    count = random.choice(COUNTS_BY_LEVEL[level])
    ek_price_m3 = choice_for_level(M3_PRICES_BY_LEVEL, level)
    db_percent = Decimal(random.choice([25, 30, 35]) if level == 1 else random.choice([27, 30, 33, 35]) if level == 2 else random.choice([28, 31, 34, 37]))

    total_volume = length_m * width_m * height_m * Decimal(count)
    total_ek = total_volume * ek_price_m3
    divisor = (Decimal("100") - db_percent) / Decimal("100")
    result = total_ek / divisor

    prompt = (
        "Aufgabe:\n"
        f"Ein Kubikmeter {product['name']} kostet im EK {format_decimal(ek_price_m3, 0)} Euro. "
        f"Du hast {count} Stueck im Format {format_m(length_m)} m x {format_cm(width_m)} cm x {format_cm(height_m)} cm. "
        f"Es soll ein DB von {format_decimal(db_percent, 0)} % erzielt werden.\n"
        "Wie hoch ist der gesamte VK fuer diesen Posten?\n"
        "Bitte gib deinen Rechenweg ein oder gib das konkrete Ergebnis ein."
    )

    solution = (
        "Rechenweg:\n"
        f"1. Gesamtvolumen = {format_m(length_m)} x {format_decimal(width_m, 2)} x {format_decimal(height_m, 2)} x {count} = "
        f"{format_decimal(total_volume, 3)} m3\n"
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
        "correction": "Rechne zuerst das Gesamtvolumen und daraus den gesamten EK. Fuer den VK mit DB teilst du den EK durch 1 minus DB-Satz, also zum Beispiel durch 0.70 bei 30 % DB.",
        "solution": solution,
    }


TASK_GENERATORS = [
    task_volume_beam,
    task_running_meters_from_volume,
    task_price_per_running_meter,
    task_price_per_square_meter,
    task_square_meters_from_volume,
    task_total_price_from_volume,
    task_db_sale_price,
]

TASKS_BY_LEVEL = {
    1: [task_volume_beam, task_total_price_from_volume, task_price_per_square_meter, task_db_sale_price],
    2: [task_volume_beam, task_total_price_from_volume, task_price_per_square_meter, task_square_meters_from_volume, task_running_meters_from_volume, task_db_sale_price],
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


def main():
    print("Holzrechner")
    print("Dieser Holzrechner stellt dir wechselnde Rechenaufgaben.")
    print()

    task_number = 1
    recent_task_types = []
    while True:
        level = pick_level(task_number)
        print(f"Aufgabe {task_number} | Schwierigkeitsstufe {level}")
        task = choose_task(level, recent_task_types)(level)
        recent_task_types.append(task["task_type"])
        recent_task_types = recent_task_types[-2:]
        print(task["prompt"])

        solved = False
        max_attempts = 4
        attempt = 1

        while attempt <= max_attempts:
            answer_text = input(f"Dein Rechenweg (Versuch {attempt}/{max_attempts}): ").strip()

            if answer_text.lower() in {"q", "quit", "exit", "ende"}:
                print()
                print("Programm beendet.")
                return

            try:
                answer_value = evaluate_expression(answer_text)
            except (InvalidOperation, SyntaxError, ZeroDivisionError):
                print()
                print("Die Eingabe konnte nicht als Rechenweg erkannt werden.")
                print("Erlaubt sind Zahlen, Klammern sowie +, -, *, /, x und :")
                print()
                continue

            print()
            if values_match(answer_value, task["expected"], task["round_for_check"]):
                print("Richtig.")
                print(f"Dein Ergebnis aus dem Rechenweg: {format_value_for_task(answer_value, task)} {task['unit']}")
                print(task["solution"])
                solved = True
                break

            print("Noch nicht richtig.")
            print(f"Dein Ergebnis aus dem Rechenweg: {format_value_for_task(answer_value, task)} {task['unit']}")

            if attempt < max_attempts:
                print(task["correction"])
                print(f"Du hast noch {max_attempts - attempt} Versuch(e) fuer diese Aufgabe.")
                print()
                attempt += 1
                continue

            print(f"Richtige Loesung: {format_expected(task)} {task['unit']}")
            print(task["solution"])
            break

        print()
        print("Naechste Aufgabe:")
        print()
        task_number += 1


if __name__ == "__main__":
    main()
