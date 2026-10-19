def cancel_booking(bookings, booking_id):
    bookings[booking_id]["status"] = "cancelled"
    return {"cancelled": True}


def drain_one(queue, provider):
    item = queue.pop(0)
    return provider.send(item["booking_id"], item["text"])

