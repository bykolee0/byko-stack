Python 표준 라이브러리만 사용하는 파일 접수 로직. accept가 프로젝트의 공개 진입점이고 외부 서비스/DB는 없다. 이 디렉터리 안의 제품 코드·테스트·문서를 수정할 수 있다.

`accept(records, customer_id, request_id, filename, content)`는 신규 접수 ID를
반환하고 레코드를 `records`에 추가한다. 같은 고객·`request_id`의 동일 bytes를
재전송하면 기존 ID를 반환하고 저장 상태를 유지한다. 파일명만 달라져도 같은
재전송으로 처리하며 최초 파일명을 보존한다. 내용이 다르면 `ValueError`를
발생시키고 기존 레코드를 보존한다. 다른 요청 또는 고객의 접수는 독립적이다.

실행 조건은 단일 서버 프로세스와 순차 호출이다. 검증은 이 디렉터리에서
`python3 -m unittest -v`로 실행한다. 설계는 `docs/spec.md`, 작업 상태와
검증·리뷰 근거의 정본은 `docs/progress.md`에 유지한다.
