import shutil


def get_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns
