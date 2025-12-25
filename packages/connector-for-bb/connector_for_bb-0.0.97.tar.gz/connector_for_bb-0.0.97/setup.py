import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.sdist import sdist as sdist_orig


ROOT = os.path.dirname(__file__)
VERSION = os.path.join(ROOT, "VERSION")


def format_version(raw_version):
    """
    Преобразование версии в формат PEP 440.
    Если версия содержит некорректные символы, добавляем их как метаданные.
    """
    if raw_version.startswith("v"):  # Удаляем префикс v, если он есть
        raw_version = raw_version[1:]

    parts = raw_version.split("-")
    if len(parts) == 1:
        return raw_version  # Версия уже корректна
    elif len(parts) == 3:
        base, distance, commit_hash = parts
        return f"{base}.dev{distance}+{commit_hash}"
    else:
        # Если версия не в ожидаемом формате, добавляем её как метаданные
        return f"0.1.0+{raw_version}"


def project_version():
    """Получение версии проекта из git(Пока что убрал)
    или файла VERSION."""
    version = None

    # Попытка получить версию из Git
    try:
        with open(VERSION) as verfile:
            raw_version = verfile.read().strip()

        # output = subprocess.check_output(
        #     ["git", "describe", "--tags", "--always"],
        #     stderr=open(os.devnull, "wb"),
        # ).strip().decode()
        # version = format_version(f"{raw_version}{output}")
        version = format_version(raw_version)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"Warning: Unable to retrieve version from git: {e}")

    if not version and os.path.exists(VERSION):
        with open(VERSION) as verfile:
            raw_version = verfile.read().strip()
            version = format_version(raw_version)

    if not version:
        raise RuntimeError("Cannot detect project version")

    return version


class sdist(sdist_orig):

    def run(self):
        version = project_version()
        with open(VERSION, "w") as verfile:
            verfile.write(version)
        sdist_orig.run(self)


if __name__ == "__main__":
    setup(
        version=project_version(),
        cmdclass={"sdist": sdist},
    )
