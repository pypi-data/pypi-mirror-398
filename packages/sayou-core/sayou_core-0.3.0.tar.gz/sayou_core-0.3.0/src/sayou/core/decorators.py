import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger("SayouCore")


def measure_time(func: Callable) -> Callable:
    """
    [Decorator] 함수 실행 시간을 측정하여 로그로 남깁니다.
    성능 병목 구간을 찾을 때 유용합니다.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            logger.debug(f"[Timer] {func.__qualname__} took {elapsed:.4f}s")

    return wrapper


def safe_run(default_return: Any = None) -> Callable:
    """
    [Decorator] 에러가 발생해도 파이프라인을 죽이지 않고,
    로그를 남긴 뒤 기본값(default_return)을 반환합니다.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"[SafeRun] Error in {func.__qualname__}: {e}", exc_info=True
                )
                return default_return

        return wrapper

    return decorator


def retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0) -> Callable:
    """
    [Decorator] 실패 시 재시도. backoff 인자를 추가하여 대기 시간을 점진적으로 늘립니다.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay  # 초기 딜레이

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"[Retry] {func.__qualname__} failed ({attempt+1}/{max_retries}). Retrying in {current_delay}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff  # 1초 -> 2초 -> 4초...

            logger.error(f"[Retry] Failed after {max_retries} attempts.")
            raise last_exception

        return wrapper

    return decorator
