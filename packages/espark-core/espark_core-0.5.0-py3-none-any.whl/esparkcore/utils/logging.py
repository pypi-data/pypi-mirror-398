from datetime import datetime


def log_debug(message: str) -> None:
    print(f'{datetime.now().isoformat()} [DEBUG] {message}')


def log_error(e: Exception) -> None:
    print(f'{datetime.now().isoformat()} [ERROR] {type(e).__name__}: {e}')

    raise e
