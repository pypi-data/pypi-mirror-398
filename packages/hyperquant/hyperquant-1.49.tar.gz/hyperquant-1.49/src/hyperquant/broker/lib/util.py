from decimal import ROUND_HALF_UP, Decimal


def fmt_value(price: float, tick: float) -> str:
    tick_dec = Decimal(str(tick))
    price_dec = Decimal(str(price))
    return str(
        (price_dec / tick_dec).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * tick_dec
    )


def place_to_step(place: int) -> float:
    """
    把 pricePlace / volumePlace 转换成 tick_size / lot_size

    Args:
        place (int): 小数位数，例如 pricePlace=1, volumePlace=2

    Returns:
        float: 步长 (step)，例如 0.1, 0.01
    """
    return 10 ** (-place)