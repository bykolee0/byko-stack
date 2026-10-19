Python 표준 라이브러리만 사용하는 파일 접수 로직. accept가 프로젝트의 공개 진입점이고 외부 서비스/DB는 없다. 이 디렉터리 안의 제품 코드·테스트·문서를 수정할 수 있다.

`accept(records, customer_id, request_id, filename, content)`는 접수 ID를 반환한다.
같은 고객과 `request_id`의 bytes 내용이 같으면 기존 ID를 반환하고 저장을 추가하지 않는다.
파일명만 바뀐 재전송도 기존 파일명과 내용을 유지한다. 내용이 다르면 `ValueError`가 발생하며 기존 접수는 그대로 유지된다.
다른 고객이나 다른 `request_id`는 별도 접수이며, 파일명은 표시용이다.
단일 프로세스의 순차 호출을 대상으로 한다.

검증: `python3 -m unittest -v`

설계와 사전 검토 기준: [spec.md](docs/specs/upload-retry/spec.md).
진행·검증·리뷰 기록: [progress.md](docs/specs/upload-retry/progress.md).
