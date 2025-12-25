import traceback
from pathlib import Path


class FileReaderController:
    _encoding = "utf-8"

    @classmethod
    def save_text(cls, file_path: Path, content: str):
        """
        Безопасно записывает текст в файл с указанной кодировкой.
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)  # создаем директорию если нужно
            file_path.write_text(content, encoding=cls._encoding)
        except Exception as e:
            traceback.print_exc()
            return False
        else:
            return True

    @classmethod
    def read_text(cls, file_path: Path):
        """
        Чтение файла
        """

        try:
            content = file_path.read_text(encoding=cls._encoding)
        except Exception as e:
            traceback.print_exc()
            return False
        else:
            return content
