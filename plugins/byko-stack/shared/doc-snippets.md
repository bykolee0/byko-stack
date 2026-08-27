# 문서 컴포넌트 모음

`spec.html` / `implementation-plan.html`을 저작할 때 복사해 쓰는 조각들. 규약은 `doc-system.md`, 실물 예시는 `examples/spec-example.html`.

모든 컴포넌트는 다크/라이트·인쇄에서 자동으로 맞는다. **색을 직접 지정하지 않는다** — 클래스와 `data-rv`만 쓴다.

---

## 1. 챕터

문서의 기본 단위. `id`와 `data-nav`(상단 네비에 뜨는 짧은 라벨)를 반드시 붙인다.

```html
<section class="chapter" id="c3" data-nav="3. 정상 흐름">
  <div class="wrap">
    <p class="chapter-no reveal">Chapter 3 · 정상 흐름</p>
    <h2 class="reveal">아무 문제 없는 날,<br>한 건을 따라가 보자</h2>
    <p class="chapter-intro reveal">이 장에서 무엇을 보게 되는지 한두 문장.</p>
    …
  </div>
</section>
```

`class="reveal"`은 스크롤 등장 효과다. 붙이지 않아도 되고, JS가 없으면 그냥 보인다.

## 2. 표지

```html
<header class="hero">
  <div class="wrap">
    <p class="kicker">BYKO-STACK SPEC · PROJECT · 2026-08-01</p>
    <h1>앞줄은 상황<br><span class="accent">뒷줄은 핵심</span></h1>
    <p class="hero-sub">이 문서가 어떤 여정인지 한 문단. 누가 읽어도 따라올 수 있게.</p>
    <div class="hero-cta">
      <a class="primary" href="#c0">처음부터 읽기</a>
      <a href="#c6">내가 결정할 것만 보기</a>
    </div>
    <div class="remember">
      <span class="n">3</span>
      <p>끝까지 기억할 단어는 세 개뿐입니다. <strong>A</strong>는 …, <strong>B</strong>는 …, <strong>C</strong>는 …입니다.</p>
    </div>
    <div class="toolbar" style="margin-top:2rem"></div>
  </div>
</header>
```

## 3. 스토리 — 한 건이 어떻게 처리되나

정상 흐름은 기본, 문제 지점은 `.problem`(빨강), 해법은 `.fix`(초록).

```html
<div class="story">
  <div class="story-step reveal">
    <div class="story-index">1</div>
    <div class="story-copy">
      <h3>"취소할게요"</h3>
      <p>앱이 <code>POST /orders/{id}/cancel</code>을 호출합니다. <strong>강조할 사실</strong>은 이렇게.</p>
    </div>
  </div>
  <div class="story-step problem reveal">
    <div class="story-index">2</div>
    <div class="story-copy"><h3>여기서 막힌다</h3><p>…</p></div>
  </div>
  <div class="story-step fix reveal">
    <div class="story-index">3</div>
    <div class="story-copy"><h3>이렇게 푼다</h3><p>…</p></div>
  </div>
</div>
```

## 4. 개념 정의 — 실물에 빗대기

`.like`는 비유 부분(앰버로 뜬다). `cols-2` / `cols-3` 선택.

```html
<div class="terms cols-3">
  <div class="term reveal">
    <span class="big-word">주문 아이템</span>
    <p><span class="like">영수증의 한 줄.</span> 상품·단가·수량을 가집니다.
      재고와 배송은 원래부터 <strong>이 줄 단위</strong>로 움직입니다.</p>
  </div>
</div>
```

같은 컴포넌트를 마지막 장의 "기억할 것"에도 쓴다 (`cols-2`).

## 5. 구조 지도 — 지금 무엇이 무엇을 책임지나

```html
<div class="map cols-3">
  <div class="map-box reveal">
    <span class="plane-tag">주문 도메인</span>
    <span class="name">OrderService</span>
    <span class="role">무엇을 책임지나. 한두 줄로.</span>
    <span class="code-ref">src/order/service.py:214</span>
  </div>
  <div class="map-box accent" style="--k: var(--green)">
    <span class="name">강조할 노드</span>
    <span class="role">…</span>
    <span class="map-pin">여기가 바뀝니다</span>
  </div>
</div>
```

가로 흐름이 필요하면 `.flow.row` — 넓은 화면에서 가로로 늘어선다.

```html
<div class="flow row reveal">
  <div class="map-box"><span class="name">잠근다</span><span class="role">…</span></div>
  <div class="arrow">→</div>
  <div class="map-box"><span class="name">검사한다</span><span class="role">…</span></div>
</div>
```

## 6. 전 / 후 비교

```html
<div class="beforeafter">
  <div class="ba-card from reveal">
    <span class="label">지금</span>
    <p><strong>한 줄 요약</strong></p>
    <ul><li>…</li><li>…</li></ul>
  </div>
  <div class="ba-arrow reveal">→</div>
  <div class="ba-card to reveal">
    <span class="label">바꾼 뒤</span>
    <p><strong>한 줄 요약</strong></p>
    <ul><li>…</li><li>…</li></ul>
  </div>
</div>
```

선택지 두 개를 나란히 놓을 때도 같은 컴포넌트를 쓴다 (`from`/`to` 없이, 가운데를 `vs`로).

## 7. 완성 조건 — 눌러 보는 시나리오

AC를 표로 나열하지 말고 상황으로 만든다. 버튼과 패널의 개수는 같아야 한다.

```html
<div class="scenario reveal">
  <div class="scn-bar" role="tablist">
    <button class="scn-btn" role="tab">정상</button>
    <button class="scn-btn" role="tab">경계값</button>
  </div>
  <div class="scn-panel">
    <div class="scn-io">
      <div><span class="label">상황 · 요청</span>
        <p class="scn-note">한 문장 상황.</p>
        <code>POST /… · {…}</code></div>
      <div class="out"><span class="label">그러면</span>
        <p class="scn-note"><code>201</code> + 무엇이 어떻게 바뀌는가.</p></div>
    </div>
    <p class="scn-note"><span class="scn-ac">AC-1</span> · integration test로 검증</p>
  </div>
  <div class="scn-panel" hidden>…</div>
</div>
```

전체 AC 표는 접어서 에이전트용으로 둔다 (아래 10번).

## 8. 사람이 결정할 것

```html
<div class="rv reveal" data-rv="risk" data-rv-title="결정 목록에 뜰 한 문장">
  <div class="rv-head">
    <span class="chip" data-rv="risk" data-icon="⚠">되돌릴 수 없음</span>
    <span class="rv-title">…</span>
    <span class="rv-why">왜 사람이 봐야 하나</span>
  </div>
  <p>무엇을 정했는지 · 왜 · <strong>검토했던 대안</strong>.</p>
</div>

<!-- 문장 속 용어 하나를 표시할 때 -->
문장 속에서 <span class="rv-i" data-rv="new" data-rv-title="취소 단위">취소 단위</span>라고 부릅니다.
```

아이콘: `new ◆` · `type ▣` · `data ▲` · `decision ●` · `risk ⚠` · `open ?`

## 9. 콜아웃

```html
<div class="callout reveal"><span class="ct">지금까지</span><p>…</p></div>
<div class="callout warn"><span class="ct">가장 흔한 오해</span><p>…</p></div>
<div class="callout bad"><span class="ct">근본 원인</span><p>…</p></div>
<div class="callout good"><span class="ct">여기까지는 문제없다</span><p>…</p></div>
```

## 10. 만드는 순서 · 표 · 접기

```html
<ul class="pipeline reveal">
  <li class="done"><span class="pl-mark">1</span><span>…</span><span class="badge">롤백 가능</span></li>
  <li class="now"><span class="pl-mark">2</span><span>…</span><span class="badge bad">되돌릴 수 없음</span></li>
  <li class="todo"><span class="pl-mark">3</span><span>…</span><span class="badge warn">합의 필요</span></li>
</ul>

<div class="table-wrap"><table>
  <thead><tr><th>단계</th><th>내용</th></tr></thead>
  <tbody><tr><td>S1</td><td>…</td></tr></tbody>
</table></div>

<details class="agent-only">
  <summary>기계적 변경 목록</summary>
  <ul><li>리네임·이동·반복 치환처럼 판단이 필요 없는 것</li></ul>
</details>
```

## 11. 코드 · 근거 표기

```html
<p>본문 속 식별자는 <code>cancelled_qty</code>처럼.</p>
<span class="code-ref">src/order/service.py:214</span>

<pre><code>class OrderCancellation:
    order_item_id: UUID     # ← 취소 단위의 키
    quantity: int</code></pre>
```

## 12. 예외 — 인라인 SVG

상태 전이처럼 좌표가 꼭 필요한 그림에만 쓴다. 박스-화살표 흐름도는 5번(`.map` / `.flow`)으로 대신한다.

```html
<figure class="diagram">
<svg viewBox="0 0 720 150" role="img" aria-label="상태 전이">
  <rect x="40" y="56" width="130" height="48" rx="24" class="d-box"/>
  <text x="105" y="85" text-anchor="middle" class="d-mono">PAID</text>
  <path d="M170,80 L291,80" class="d-line"/>
</svg>
<figcaption>한 줄로: 이 그림에서 무엇을 읽어야 하는가.</figcaption>
</figure>
```

색은 클래스로만 지정한다: `d-box` `d-box-accent` `d-line` `d-line-dash` `d-label` `d-sub` `d-mono` `d-tag`.
