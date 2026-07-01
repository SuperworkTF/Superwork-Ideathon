# IDEATHON ’26 — THE FINAL FIVE (전사 투표 쇼케이스)

Kinetic-brutalist, 익명(점수·제안자·순위 비공개) 결선 5작 소개 사이트.
정적 파일만 사용 · GitHub Pages(`gh-pages` 브랜치) 배포.

**LIVE:** https://superworktf.github.io/Superwork-Ideathon/

## 구조
```
site/
├─ index.html          # 인덱스 허브 (5작, 방문마다 무작위 순서)
├─ ideas/*.html        # 아이디어별 상세 (build.cjs로 생성 — 직접 수정 X)
├─ assets/
│  ├─ config.js        # ★ 단일 소스: 문구·마감·투표 URL·아이디어 데이터
│  ├─ app.css          # 디자인 시스템
│  └─ app.js           # 스크램블·리빌·마퀴·카운트다운·무작위 셔플·커서
├─ build.cjs           # config.js → ideas/*.html 생성기 (로컬 전용)
└─ deploy.sh           # 재빌드 + gh-pages 배포 (로컬 전용)
```

## 투표 버튼 켜기 (가장 중요)
`assets/config.js`의 `meta`에서 두 줄만 바꾸세요:
```js
voteUrl: "https://forms.gle/....",   // "#" → 실제 투표 채널 URL (구글폼/슬랙 등)
// deadlineText / voteDeadline 도 필요 시 수정 (카운트다운은 voteDeadline 기준)
```
- `voteUrl`이 `"#"`이면 버튼은 **비활성**(자리만 유지) 상태입니다.
- 실제 URL을 넣으면 모든 “투표하러 가기” 버튼이 새 탭으로 연결됩니다.

## 다시 배포
```bash
bash site/deploy.sh
```
`build.cjs`로 상세 페이지를 재생성하고 `gh-pages` 브랜치에 푸시합니다. 1~2분 뒤 반영.

## 메모
- 검색 노출 차단: 모든 페이지 `<meta name="robots" content="noindex">`.
- 폰트: Wanted Sans(디스플레이) · Pretendard(본문) · Space Mono(시스템) — CDN.
- 번호(F-01~05)는 **ID일 뿐 순위 아님**. 표시 순서는 방문마다 무작위.
