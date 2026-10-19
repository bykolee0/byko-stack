def deduct(stock, sku, quantity):
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("positive integer required")
    available = stock[sku]
    if quantity > available:
        raise ValueError("insufficient stock")
    stock[sku] = available - quantity
    return stock[sku]

