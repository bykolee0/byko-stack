# Project conventions

Python 표준 라이브러리만 사용하는 로컬 프로젝트다. public API는 store.add_task(path, label)이다. 저장 형식은 JSON 배열이며 원소는 정수 id와 문자열 label을 가진다.

테스트는 python3 -B -m unittest discover -s tests -v로 실행한다. 파일 쓰기를 검증할 때 실제 임시 JSON 파일을 사용한다. 외부 서비스와 배포 대상은 없다. 현재 저장소의 코드가 전체 범위다.
