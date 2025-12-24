def hard_round(value: float, decimals: int = 2) -> float:
    """
    Rounds a float to a specified number of decimal places with hard rounding.

    Required Arguments:

    - value (float): The float value to be rounded.

    Optional Arguments:

    - decimals (int): The number of decimal places to round to.
        - Default: 2

    Returns:

    - float: The rounded float value.
    """
    factor = 10**decimals
    return round(value * factor) / factor
