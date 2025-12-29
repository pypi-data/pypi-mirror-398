from __future__ import annotations


def meanScore(numbers: list[float]) -> float | None:
    """
    Calculate the mean of a list of numbers.
    :param numbers: A list of numbers.
    :return: The mean of the list of numbers.
    """
    if len(numbers) == 0:
        return None  # Handle empty list case
    total_sum = sum(numbers)
    mean = total_sum / len(numbers)
    return mean
