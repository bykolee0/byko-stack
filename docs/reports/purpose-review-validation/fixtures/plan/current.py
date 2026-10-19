def accept(records, customer_id, request_id, filename, content):
    record = {"id": len(records) + 1, "customer_id": customer_id,
              "request_id": request_id, "filename": filename, "content": content}
    records.append(record)
    return record["id"]

