from colorama import Fore


def colour(message: str, code: Fore) -> str:
    return f"{code}{message}{Fore.RESET}"


def red(message: str) -> str:
    return colour(message, Fore.RED)


def blue(message: str) -> str:
    return colour(message, Fore.BLUE)


def yellow(message: str) -> str:
    return colour(message, Fore.YELLOW)


def green(message: str) -> str:
    return colour(message, Fore.GREEN)


def cyan(message: str) -> str:
    return colour(message, Fore.CYAN)


def magenta(message: str) -> str:
    return colour(message, Fore.MAGENTA)
