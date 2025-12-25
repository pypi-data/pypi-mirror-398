import random


def exponential_backoff_with_jitter(
    attempt: int,
    base_wait_time: float = 1.0,
    max_wait_time: float = 30.0,
    jitter: bool = True,
) -> float:
    """
    지터와 최대 대기 시간을 포함한 지수 백오프 시간을 계산합니다.

    Args:
        attempt (int): 현재 재시도 횟수 (1부터 시작).
        base_wait_time (float): 기본 대기 시간 (초).
        max_wait_time (float): 최대 대기 시간 (초).
        jitter (bool): 무작위 지터 추가 여부.

    Returns:
        float: 최종 백오프 대기 시간 (초).
    """
    # 기본 백오프 시간 계산
    backoff_time = base_wait_time * (2 ** (attempt - 1))

    # 지터 추가 (full jitter)
    if jitter:
        backoff_time = random.uniform(0, backoff_time)

    # 최대 대기 시간 적용
    final_wait_time = min(backoff_time, max_wait_time)

    return final_wait_time
