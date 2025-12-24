from .language_compiler import language_compile, get_translate
translates, language = language_compile()
def fis(
    l: int | str | list[int | str],
    from_system: int | list[int] = 10,
    in_system: int | list[int] = 2,
    alf: str | list = "0123456789ABCDEF",
    alf2: str | list | None = None,
    s: bool | str = False
) -> list[str] | str:
    """
    RU:
    Функция fis выполняет преобразование чисел между системами счисления
    с использованием произвольных алфавитов.

    ENG:
    The fis function converts numbers between numeral systems
    using custom input and output alphabets.

    ------------------------------------------------------------------

    Параметры / Parameters:

    l :
        RU: Входные данные. Может быть:
            - числом (int),
            - строкой (str),
            - списком чисел или строк.
        ENG: Input data. Can be:
            - an integer,
            - a string,
            - a list of integers or strings.

    from_system :
        RU: Исходная система счисления.
            Может быть:
            - числом (одна система для всех элементов l),
            - списком чисел (отдельная система для каждого элемента l).
        ENG: Source numeral system.
            Can be:
            - an integer (one base for all elements of l),
            - a list of integers (individual base for each element).

    in_system :
        RU: Целевая система счисления.
            Аналогично from_system.
        ENG: Target numeral system.
            Same rules as from_system.

    alf :
        RU: Входящий алфавит (символы цифр исходной системы).
            Может быть строкой или списком.
        ENG: Input alphabet (symbols of source system).
            Can be a string or a list.

    alf2 :
        RU: Исходящий алфавит (символы цифр целевой системы).
            Если None — используется alf.
        ENG: Output alphabet (symbols of target system).
            If None, alf is used.

    s :
        RU:
            - False → вернуть список строк,
            - True  → вернуть список списков символов,
            - str   → вернуть одну строку, объединяя элементы через s.
        ENG:
            - False → return list of strings,
            - True  → return list of symbol lists,
            - str   → return one joined string using s as separator.

    ------------------------------------------------------------------

    Возвращаемое значение / Return value:

    RU:
        - список строк,
        - либо одна строка (если s — строка).

    ENG:
        - list of strings,
        - or a single string (if s is a string).
    """
    if isinstance(alf, str):
        alf = list(alf)
    if alf2 is None:
        alf2 = alf
    elif isinstance(alf2, str):
        alf2 = list(alf2)
    if isinstance(l, (int, str)):
        l = [l]
    l = [str(x) for x in l]
    if isinstance(from_system, int):
        from_system = [from_system] * len(l)
    if isinstance(in_system, int):
        in_system = [in_system] * len(l)
    if len(from_system) != len(l) or len(in_system) != len(l):
        raise ValueError(get_translate(translates, language, "Длина from_system и in_system должна совпадать с l"))
    for fs in from_system:
        if fs < 2 or fs > len(alf):
            raise ValueError(get_translate(translates, language, "Некорректная from_system"))
    for ts in in_system:
        if ts < 2 or ts > len(alf2):
            raise ValueError(get_translate(translates, language, "Некорректная in_system"))
    decimals = []
    for num, fs in zip(l, from_system):
        value = 0
        for power, ch in enumerate(reversed(num)):
            if ch not in alf or alf.index(ch) >= fs:
                raise ValueError(get_translate(translates, language, "Символ не принадлежит алфавиту системы"))
            value += alf.index(ch) * (fs ** power)
        decimals.append(value)
    result = []
    for value, ts in zip(decimals, in_system):
        if value == 0:
            digits = [alf2[0]]
        else:
            digits = []
            while value > 0:
                digits.insert(0, alf2[value % ts])
                value //= ts
        result.append(digits if s is True else "".join(digits))
    if isinstance(s, str):
        return s.join(result)
    return result
