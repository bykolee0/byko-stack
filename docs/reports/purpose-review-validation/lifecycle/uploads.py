def accept(records, customer_id, request_id, filename, content):
    """접수 ID를 반환하며, 같은 요청의 내용이 달라지면 ValueError를 발생시킨다."""
    for record in records:
        if record["customer_id"] == customer_id and record["request_id"] == request_id:
            if record["content"] != content:
                raise ValueError("request_id already accepted with different content")
            return record["id"]

    record = {"id": len(records) + 1, "customer_id": customer_id,
              "request_id": request_id, "filename": filename, "content": content}
    records.append(record)
    return record["id"]

