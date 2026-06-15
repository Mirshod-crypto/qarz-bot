"""
O'zbek lotin <-> Kirill transliteratsiya moduli
"""

# Lotin -> Kirill
LATIN_TO_CYRILLIC = {
    "ch": "ч", "sh": "ш", "ng": "нг", "gh": "ғ",
    "Ch": "Ч", "Sh": "Ш", "Ng": "Нг", "Gh": "Ғ",
    "CH": "Ч", "SH": "Ш", "NG": "НГ", "GH": "Ғ",
    "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф",
    "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к",
    "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
    "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у",
    "v": "в", "x": "х", "y": "й", "z": "з",
    "A": "А", "B": "Б", "D": "Д", "E": "Е", "F": "Ф",
    "G": "Г", "H": "Ҳ", "I": "И", "J": "Ж", "K": "К",
    "L": "Л", "M": "М", "N": "Н", "O": "О", "P": "П",
    "Q": "Қ", "R": "Р", "S": "С", "T": "Т", "U": "У",
    "V": "В", "X": "Х", "Y": "Й", "Z": "З",
    "o'": "ў", "g'": "ғ", "O'": "Ў", "G'": "Ғ",
    "o`": "ў", "g`": "ғ", "O`": "Ў", "G`": "Ғ",
    "'": "ъ", "`": "ъ",
}

# Kirill -> Lotin
CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": "'", "ы": "i", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D",
    "Е": "E", "Ё": "Yo", "Ж": "J", "З": "Z", "И": "I",
    "Й": "Y", "К": "K", "Л": "L", "М": "M", "Н": "N",
    "О": "O", "П": "P", "Р": "R", "С": "S", "Т": "T",
    "У": "U", "Ф": "F", "Х": "X", "Ц": "Ts", "Ч": "Ch",
    "Ш": "Sh", "Щ": "Sh", "Ъ": "'", "Ы": "I", "Ь": "",
    "Э": "E", "Ю": "Yu", "Я": "Ya",
    # O'zbek Kirilliga xos harflar
    "ғ": "g'", "қ": "q", "ң": "ng", "ҳ": "h", "ў": "o'",
    "Ғ": "G'", "Қ": "Q", "Ң": "Ng", "Ҳ": "H", "Ў": "O'",
}

def is_cyrillic(text: str) -> bool:
    """Matn kirillcha ekanligini tekshirish"""
    cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯғқңҳўҒҚҢҲЎ')
    count = sum(1 for c in text if c in cyrillic_chars)
    return count > len(text) * 0.3  # 30% dan ko'p kirill bo'lsa

def is_latin_uzbek(text: str) -> bool:
    """Matn lotin o'zbekcha ekanligini tekshirish"""
    latin_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    count = sum(1 for c in text if c in latin_chars)
    return count > len(text) * 0.3

def uz_to_cyrillic(text: str) -> str:
    """O'zbek lotin -> Kirill"""
    if not text:
        return text
    if is_cyrillic(text):
        return text  # Allaqachon kirillcha

    result = text
    # Avval ko'p harflilarni almashtir
    for lat, cyr in [
        ("o'", "ў"), ("g'", "ғ"), ("O'", "Ў"), ("G'", "Ғ"),
        ("o`", "ў"), ("g`", "ғ"), ("O`", "Ў"), ("G`", "Ғ"),
        ("ch", "ч"), ("Ch", "Ч"), ("CH", "Ч"),
        ("sh", "ш"), ("Sh", "Ш"), ("SH", "Ш"),
        ("ng", "нг"), ("Ng", "Нг"), ("NG", "НГ"),
        ("gh", "ғ"), ("Gh", "Ғ"),
    ]:
        result = result.replace(lat, cyr)

    # Keyin bitta harflarni
    single = {
        "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф",
        "g": "г", "h": "ҳ", "i": "и", "j": "ж", "k": "к",
        "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
        "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у",
        "v": "в", "x": "х", "y": "й", "z": "з",
        "A": "А", "B": "Б", "D": "Д", "E": "Е", "F": "Ф",
        "G": "Г", "H": "Ҳ", "I": "И", "J": "Ж", "K": "К",
        "L": "Л", "M": "М", "N": "Н", "O": "О", "P": "П",
        "Q": "Қ", "R": "Р", "S": "С", "T": "Т", "U": "У",
        "V": "В", "X": "Х", "Y": "Й", "Z": "З",
    }
    final = ""
    for char in result:
        final += single.get(char, char)

    return final

def cyrillic_to_uz(text: str) -> str:
    """Kirill -> O'zbek lotin"""
    if not text:
        return text
    if not is_cyrillic(text):
        return text  # Allaqachon lotincha

    result = ""
    i = 0
    while i < len(text):
        char = text[i]
        translated = CYRILLIC_TO_LATIN.get(char, char)
        result += translated
        i += 1

    return result

def smart_translate(text: str, viewer_lang: str) -> str:
    """
    Matnni ko'ruvchining tiliga o'girish.
    viewer_lang: 'latin' yoki 'cyrillic'
    """
    if not text:
        return text

    if viewer_lang == "cyrillic":
        return uz_to_cyrillic(text)
    else:
        return cyrillic_to_uz(text)
