"""
RU:
Модуль для работы с булевыми формулами, перебором значений переменных,
проверкой выполнимости формулы и кэшированием результатов.

Модуль поддерживает логические операции:
≡ (эквивалентность), → (импликация), ∨ (или), ∧ (и), ¬ (не)

ENG:
Module for working with boolean formulas, enumerating variable values,
checking formula satisfiability, and caching results.

Supported logical operations:
≡ (equivalence), → (implication), ∨ (or), ∧ (and), ¬ (not)
"""

from itertools import product
from copy import deepcopy
from json import loads, dump
from os import remove
from .language_compiler import BASE_DIR
version = "4.1.2"
cach_path = BASE_DIR / ".cache.json"
bi = [False, True]
spec_symbols = "≡→∨∧¬()"
_cache = {}


def formula_to_python(expr: str) -> str:
    """
    RU:
    Преобразует логическую формулу в строку Python для вычисления через eval.

    ENG:
    Converts a logical formula into a Python-evaluable string.
    """
    sps = "≡→∨∧¬() "
    expr = "".join(
        i if i in sps else f' a["{i}"] ' for i in expr
    )
    expr = (
        expr.replace("≡", " == ")
            .replace("→", " <= ")
            .replace("∨", " or ")
            .replace("∧", " and ")
            .replace("¬", " not ")
    )
    while "  " in expr:
        expr = expr.replace("  ", " ")
    while "( " in expr:
        expr = expr.replace("( ", "(")
    while " )" in expr:
        expr = expr.replace(" )", ")")
    return expr


def extract_variables(expr: str) -> list[str]:
    """
    RU:
    Извлекает список переменных из логической формулы.

    ENG:
    Extracts a list of variables from a logical formula.
    """
    sps = "≡→∨∧¬() "
    expr = "".join(i if i in sps else i for i in expr)
    for s in "≡→∨∧¬() ":
        expr = expr.replace(s, "")
    return list(expr)


def eval_formula(values: dict, formula: str, mode: int) -> bool:
    """
    RU:
    Вычисляет значение формулы при заданных значениях переменных.

    ENG:
    Evaluates the formula with given variable values.
    """
    a = {k: bool(v) for k, v in values.items()}
    expr = formula_to_python(formula)
    if mode != 1:
        expr = f"not ({expr})"
    return eval(expr)


def all_unique(seq: list) -> bool:
    """
    RU:
    Проверяет, что все элементы списка уникальны.

    ENG:
    Checks that all elements in the list are unique.
    """
    return len(set(seq)) == len(seq)


def map_values(vars_: list, values: list) -> dict:
    """
    RU:
    Создаёт словарь соответствия переменных и их значений.

    ENG:
    Creates a variable-to-value mapping.
    """
    return dict(zip(vars_, values))


def recursive_check(rules, header, formula, symbol="?") -> set:
    """
    RU:
    Рекурсивно проверяет удовлетворимость формулы.

    ENG:
    Recursively checks formula satisfiability.
    """
    result = set()
    pattern, mode = rules[0]

    if symbol in pattern:
        for comb in product(bi, repeat=pattern.count(symbol)):
            current = deepcopy(pattern)
            for v in comb:
                current[current.index(symbol)] = v
            if eval_formula(map_values(header, current), formula, mode):
                if len(rules) == 1:
                    result.add(" ".join(header))
                else:
                    result |= recursive_check(rules[1:], header, formula, symbol)
    else:
        if eval_formula(map_values(header, pattern), formula, mode):
            if len(rules) == 1:
                result.add(" ".join(header))
            else:
                result |= recursive_check(rules[1:], header, formula, symbol)

    return result


def start(
    table: str,
    formula: str,
    enum: bool = False,
    joiner: str = "",
    symbol: str = "?"
) -> set | str:
    """
    RU:
    Основная функция перебора и проверки логической формулы.

    ENG:
    Main function for enumerating and checking a logical formula.
    """
    variables = sorted(set(extract_variables(formula)))
    original_table = table
    cached_result = None
    latest_version = "0.0.0"

    try:
        with open(cach_path, "r", encoding="UTF-8") as f:
            for line in f:
                try:
                    record = loads(line)
                    if record["version"] == version:
                        if (
                            record["a"] == variables
                            and record["fu"] == formula.replace(" ", "")
                            and record["y"] == table
                        ):
                            cached_result = record["result"]
                    elif (
                        list(map(int, record["version"].split(".")))
                        > list(map(int, latest_version.split(".")))
                    ):
                        latest_version = record["version"]
                except:
                    pass
    except:
        with open(cach_path, "w+", encoding="UTF-8"):
            pass

    header = header_refactor(table)
    rules = refactor(table)

    if cached_result:
        result = cached_result
    else:
        result = []
        for comb in product(
            [v for v in "".join(variables) if v not in header],
            repeat=header.count(symbol)
        ):
            test_header = deepcopy(header)
            for v in comb:
                test_header[test_header.index(symbol)] = v
            if all_unique(test_header):
                found = recursive_check(rules, test_header, formula, symbol)
                result.extend(found)

        with open(cach_path, "a+", encoding="UTF-8") as f:
            dump(
                {
                    "version": version,
                    "y": original_table,
                    "a": variables,
                    "fu": formula.replace(" ", ""),
                    "result": result,
                },
                f,
            )
            f.write("\n")

    if enum:
        result = [f"{i}) {v}" for i, v in enumerate(result)]
    if joiner:
        return joiner.join(result)
    return set(result)


def clear_old_cache():
    """
    RU:
    Очищает кэш, оставляя только записи текущей версии.

    ENG:
    Clears cache, keeping only records of the current version.
    """
    valid = []
    try:
        with open(cach_path, "r", encoding="UTF-8") as f:
            for line in f:
                try:
                    record = loads(line)
                    if record["version"] == version:
                        valid.append(record)
                except:
                    pass
    except:
        pass

    with open(cach_path, "w+", encoding="UTF-8") as f:
        for r in valid:
            dump(r, f)
            f.write("\n")


def clear_cache():
    """
    RU:
    Полностью удаляет файл кэша.

    ENG:
    Completely removes the cache file.
    """
    remove(cach_path)


def refactor(table: str) -> list:
    """
    RU:
    Преобразует таблицу ограничений в структурированный формат.

    ENG:
    Converts constraint table into structured format.
    """
    return [
        [
            [int(x) if x.isdigit() else x for x in row[:-2]],
            int(row[-1]) if row[-1].isdigit() else row[-1],
        ]
        for row in map(list, table.split("\n")[1:])
    ]


def header_refactor(table: str) -> list[str]:
    """
    RU:
    Извлекает заголовок таблицы.

    ENG:
    Extracts table header.
    """
    return list(table.split("\n")[0])
