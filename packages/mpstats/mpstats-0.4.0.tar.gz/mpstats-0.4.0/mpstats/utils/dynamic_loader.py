"""Динамическая загрузка удаленного кода."""

import pathlib

import requests


def load_remote_function(url: str, local_cache_path: str) -> None:
    """Загружает удаленный код."""

    try:
        # Попытка загрузки удаленного кода
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Проверка статуса ответа
        code = response.text

        # Сохранение кода локально для кэширования
        with pathlib.Path(local_cache_path).open("w") as f:
            f.write(code)
        print("Удаленный код успешно загружен и кэширован.")

    except (OSError, requests.RequestException) as e:
        print(f"Ошибка при загрузке удаленного кода: {e}")
        print("Попытка использовать кэшированную версию.")

        # Проверка наличия кэшированной версии
        if pathlib.Path(local_cache_path).exists():
            with pathlib.Path(local_cache_path).open("r") as f:
                code = f.read()
            print("Кэшированная версия успешно загружена.")
        else:
            raise RuntimeError("Не удалось загрузить удаленный код и кэшированная версия отсутствует.")

    # Выполнение загруженного кода
    exec(code, globals())
