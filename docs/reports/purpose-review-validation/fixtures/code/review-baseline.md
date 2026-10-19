# 구현 전 검토 가안
- V1: A=5,B=9에서 A를2차감 → 반환3, A=3,B=9.
- V2: A=5에서5차감 → 반환0,A=0.
- V3: A=5,B=9에서6차감 → ValueError, 전체 상태 불변.
- V4: quantity가0,음수,bool,문자열 → ValueError, 상태 불변.
- V5: 없는SKU → KeyError, 상태 불변.
근거: CONTRACT.md. 각 사례에서 반환/예외뿐 아니라 stock 전체를 확인한다. 이 문서는 후보 구현 전 작성한 기준이다.
