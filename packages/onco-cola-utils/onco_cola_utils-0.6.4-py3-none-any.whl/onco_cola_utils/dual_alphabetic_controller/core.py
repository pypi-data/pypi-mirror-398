from functools import cached_property
from typing import Final, Optional

from ..logger import log


print = log


class DualAlphabeticController:
    """Контроллер для конвертации между визуально похожими латинскими и кириллическими символами.

    Определяет преобладающий алфавит в строке и конвертирует все DAB-символы (Dual-Alphabet Letters)
    в соответствующие символы выбранного алфавита.
    """

    LATIN_TO_CYRILLIC: Final[dict[str, str]] = {
        'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'K': 'К',
        'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х',
        'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х',
    }

    CYRILLIC_TO_LATIN: Final[dict[str, str]] = {v: k for k, v in LATIN_TO_CYRILLIC.items()}

    # Объединяем все DAB символы в один set для быстрой проверки
    ALL_DAB_CHARS: Final[set[str]] = (
        set(LATIN_TO_CYRILLIC.keys()) | set(LATIN_TO_CYRILLIC.values())
    )

    def __init__(self, string: str):
        self._string: str = string
        self._result: Optional[str] = None

    def main_process(self) -> None:
        """Основной процесс определения и выполнения конвертации."""
        filtered_chars = [c for c in self._string if self._is_alphabetic(c) and not self._is_dab(c)]

        # Используем генераторы для экономии памяти
        latin_score = sum(1 for c in filtered_chars if self._detect_char_alphabet(c) == 'latin')
        cyrillic_score = sum(
            1 for c in filtered_chars if self._detect_char_alphabet(c) == 'cyrillic'
        )

        self._result = (
            self._to_latin(self._string)
            if latin_score >= cyrillic_score
            else self._to_cyrillic(self._string)
        )

    @cached_property
    def checker_alphabets(self) -> list[str]:
        """Возвращает список алфавитов для каждого буквенного символа в результате."""
        return [self._detect_char_alphabet(c) for c in self._result if c.isalpha()]

    @staticmethod
    def checker_set_len_alphabets(alphabets: list[str]) -> int:
        """Возвращает количество уникальных алфавитов в списке."""
        return len(set(alphabets))

    @property
    def result(self) -> str:
        """Возвращает результат конвертации с проверкой корректности."""
        if self._result is None:
            self.main_process()

        # УБИРАЕМ ВАЛИДАЦИЮ - НЕ ВСЁ МОЖНО СКОНВЕРТИРОВАТЬ
        # if not self.checker_alphabets:  # Если нет буквенных символов
        #     return self._result
        #
        # if self.checker_set_len_alphabets(self.checker_alphabets) > 1:
        #     # err = {
        #     #     'result': self._result,
        #     #     'alphabets': self.checker_alphabets
        #     # }
        #     # pretty_print(err, title=f"err", m2d=False)
        #     # raise ValueError("Результат содержит буквы из разных алфавитов.")
        #     return self._result

        return self._result

    def _detect_char_alphabet(self, ch: str) -> str:
        """Определяет алфавит символа."""
        if '\u0041' <= ch <= '\u005A' or '\u0061' <= ch <= '\u007A':  # Unicode латиница
            return 'latin'
        elif '\u0410' <= ch <= '\u044F' or ch in ('Ё', 'ё'):  # Unicode кириллица + Ё/ё
            return 'cyrillic'
        return 'other'

    def _is_dab(self, ch: str) -> bool:
        """Проверяет, является ли символ DAB (имеет визуально похожий аналог)."""
        return ch in self.ALL_DAB_CHARS

    def _is_alphabetic(self, ch: str) -> bool:
        """Проверяет, является ли символ буквенным."""
        return ch.isalpha()

    def _count_dual_alphabet_letters(self, s: str) -> int:
        """Считает количество DAB-символов в строке."""
        return sum(1 for c in s if self._is_dab(c))

    def _to_latin(self, s: str) -> str:
        """Конвертирует все возможные символы в латиницу."""
        return s.translate(str.maketrans(self.CYRILLIC_TO_LATIN))

    def _to_cyrillic(self, s: str) -> str:
        """Конвертирует все возможные символы в кириллицу."""
        return s.translate(str.maketrans(self.LATIN_TO_CYRILLIC))

    def has_mixed_alphabet(self) -> bool:
        """
        Проверяет, содержит ли исходная строка смешанные алфавиты (латиница и кириллица)
        среди буквенных символов, игнорируя неалфавитные и не-DAB символы.

        Returns:
            bool: True, если есть символы из обоих алфавитов, иначе False.
        """
        seen_alphabets: set[str] = set()

        for char in self._string:
            if not self._is_alphabetic(char):
                continue

            alphabet = self._detect_char_alphabet(char)
            if alphabet in ('latin', 'cyrillic'):
                seen_alphabets.add(alphabet)
                # Оптимизация: если уже оба есть — можно выйти
                if len(seen_alphabets) > 1:
                    return True

        return len(seen_alphabets) == 2

    @cached_property
    def highlight(self) -> str:
        """
        Возвращает строку с выделением символов, не соответствующих доминирующему алфавиту.
        Выделение — в скобках: например, "прив(e)т".

        Использует ту же логику определения доминирующего алфавита, что и main_process.
        """
        if not self._string:
            return self._string

        # Шаг 1: определяем доминирующий алфавит (выполняем main_process, если ещё не делали)
        if self._result is None:
            self.main_process()

        # Шаг 2: получаем доминирующий алфавит из анализа чистых букв
        filtered_chars = [
            c for c in self._string
            if self._is_alphabetic(c) and not self._is_dab(c)
        ]

        latin_count = sum(1 for c in filtered_chars if self._detect_char_alphabet(c) == 'latin')
        cyrillic_count = sum(
            1 for c in filtered_chars if self._detect_char_alphabet(c) == 'cyrillic'
        )

        dominant_alphabet = 'latin' if latin_count >= cyrillic_count else 'cyrillic'

        # Шаг 3: строим строку с подсветкой
        highlighted = []
        for char in self._string:
            if self._is_alphabetic(char) and self._detect_char_alphabet(char) != dominant_alphabet:
                highlighted.append(f"({char})")  # выделяем чужие буквы
            else:
                highlighted.append(char)

        return ''.join(highlighted)
