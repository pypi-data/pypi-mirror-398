from pymorphy3 import MorphAnalyzer

__version__ = '0.1.0'
analyzer = MorphAnalyzer()


def pluralize(number: int, word: str, fallback_forms=None) -> str:
    """Преобразование существительного начальной формы в существительное множественного числа"""
    parsed_word = analyzer.parse(word)[0]

    # Если слово не найдено и заданы fallback-формы, используем их
    if fallback_forms and (parsed_word.tag.POS is None or "UNKN" in parsed_word.tag):
        if number % 10 == 1 and number % 100 != 11:
            return f"{number} {fallback_forms[0]}"
        elif 2 <= number % 10 <= 4 and not (11 <= number % 100 <= 14):
            return f"{number} {fallback_forms[1]}"
        else:
            return f"{number} {fallback_forms[2]}"

    form = parsed_word.make_agree_with_number(number).word
    return f"{number} {form}"
