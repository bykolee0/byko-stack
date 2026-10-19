def deduct(stock, sku, quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("positive integer required")
    remaining = max(0, stock[sku] - quantity)
    stock[sku] = remaining
    return remaining

