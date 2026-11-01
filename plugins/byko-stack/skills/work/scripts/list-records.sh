#!/bin/sh
# byko-stack work 진입 때 이 프로젝트의 작업 기록을 최근 수정 순으로 보여 준다.
# 읽기만 한다. 무엇이 실패해도 0으로 끝난다(0이 아니면 스킬 호출 전체가 멈춘다).
# 본문 앞부분이 압축 뒤 다시 붙는 5,000토큰 안에 들도록 최근 5개만 보인다.
root="$*"
[ -n "$root" ] || root="${CLAUDE_PROJECT_DIR:-$PWD}"
dir="$root/.byko/work"
if [ ! -d "$dir" ]; then
  echo "(기록 없음: $dir)"
  exit 0
fi
all=$(ls -1t "$dir"/*/record.md 2>/dev/null)
out=$(printf '%s\n' "$all" | sed '/^$/d' | head -n 5 | while IFS= read -r rec; do
  d=$(dirname "$rec")
  # 한 줄이 길어도 주입량이 커지지 않게 각 칸을 90바이트로 자르고, 잘린 글자는 버린다.
  title=$(head -n 1 "$d/brief.md" 2>/dev/null | sed 's/^# *//' | head -c 90 | iconv -c -f UTF-8 -t UTF-8 2>/dev/null)
  now=$(grep -m 1 '^지금:' "$rec" 2>/dev/null | head -c 90 | iconv -c -f UTF-8 -t UTF-8 2>/dev/null)
  echo "- $(basename "$d") | ${title:-brief.md 없음} | ${now:-지금 줄 없음}"
done)
if [ -n "$out" ]; then
  echo "$out"
  n=$(printf '%s\n' "$all" | sed '/^$/d' | wc -l | tr -d ' ')
  [ "$n" -gt 5 ] && echo "(이전 기록 $((n - 5))개 더: $dir)"
else
  echo "(기록 없음: $dir)"
fi
exit 0
