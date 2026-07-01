/*
 * SUPERWORK IDEATHON '26 — THE FINAL FIVE
 * Single source of truth for the anonymized showcase (browser + Node generator).
 * NO scores, NO submitters, NO judge critique — fair-vote safe.
 *
 * Catalog codes (F-01…F-05) are an ARBITRARY, NON-SCORE ordering.
 * Index display order is shuffled per visit; codes travel with ideas.
 */
(function (root, factory) {
  var data = factory();
  if (typeof module === "object" && module.exports) module.exports = data; // Node
  if (typeof window !== "undefined") window.IDEATHON = data;                // browser
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  return {
    meta: {
      event: "SUPERWORK IDEATHON",
      edition: "'26",
      title: "THE FINAL FIVE",
      titleKo: "결선 5選",
      kicker: "전사 투표 · COMPANY-WIDE VOTE",
      // --- EDIT THESE BEFORE LAUNCH ---
      voteUrl: "https://gw.nasmedia.co.kr/app/survey/327",  // 사내 그룹웨어 설문 (임직원 PC/사내망 접근)
      voteLabel: "투표하러 가기",
      voteDeadline: "2026-07-03T18:00:00+09:00",    // 마감 (KST)
      deadlineText: "2026.07.03 (금) 18:00 KST",
      resultText: "결과 발표 · 추후 공지",
      // --------------------------------
      disclaimer: "결선 5개 · 순위 없음. 각 코드(DS·MR 등)는 식별용일 뿐 순위가 아닙니다. 표시 순서는 방문마다 무작위이며, 점수·제안자는 공정한 투표를 위해 비공개됩니다.",
      stakes: "당신의 한 표가 결과를 만듭니다."
    },

    ideas: [
      {
        code: "01", mono: "DS", slug: "doomsquat", name: "둠스쿼트", en: "DoomSquat",
        tagline: "스크롤하려면, 일단 앉았다 일어나",
        category: "웰빙·습관 / 온디바이스 AI",
        tags: ["웰빙·습관", "ON-DEVICE AI"],
        accent: "#FF5A1F", accentInk: "#0B0B0C",
        hook: "밤마다 뚫리는 “15분 더”. 그 탭 한 번을, 스쿼트 한 세트로 바꾼다.",
        problem: "침대에 누워 “딱 5분”이 한 시간이 되는 밤. 진짜 문제는 시간 낭비가 아니라 ‘무력화된 통제’다. 스크린타임을 걸어도 ‘15분 더’·‘무시’를 습관적으로 눌러 매일 밤 제한이 종이벽처럼 뚫린다. 취침 지연 → 수면 부족 → 다음 날 집중력 저하의 반복.",
        target: "제한 의지는 있는데 탭 한 번에 뚫려 매번 실패하는 사람. 야근 후 누워 릴스·쇼츠를 켜는 30대 직장인.",
        features: [
          { title: "운동 인증 잠금 게이트", label: "Squat-to-Unlock", body: "차단할 앱·해제 조건(스쿼트 N회)·허용 시간을 미리 설정. 차단 앱을 여는 순간 전체화면 게이트가 뜨고, 온디바이스 포즈 추정이 자세를 실시간 확인해 목표 개수를 채워야 잠금이 풀린다. ‘한 번의 탭’을 ‘실제 신체 행동’으로 치환해 무의식적 진입을 끊는다. 카메라 영상은 전량 온디바이스 처리·무저장·무전송." },
          { title: "습관 리포트 + 가벼운 공유", label: "Habit Report", body: "막아낸 진입 수, 대신 한 스쿼트 수, 절약한 시간, 취침 시각 변화를 카드·주간 그래프로. 리포트를 이미지로 내보내 팀 챌린지의 씨앗으로." }
        ],
        impact: "취침 직전 무의식적 진입에 ‘운동 한 세트’의 물리적 마찰을 걸어 숏폼 시간을 줄이고 취침을 앞당긴다. 덤으로, 낭비하던 시간이 근력 운동으로 남는 순(純)전환."
      },
      {
        code: "02", mono: "MR", slug: "moodrental", name: "무드렌탈", en: "MoodRental",
        tagline: "감정 한 줄로 빌리는, 영화 같은 하루",
        category: "여가·로컬 / LLM 연출",
        tags: ["여가·로컬", "LLM"],
        accent: "#7A5CFF", accentInk: "#FFFFFF",
        hook: "“오늘 뭐 하지”를 검색하다 지쳐 침대로 끝나는 하루. 감정 한 줄이면, 완성된 하루가 떠먹여진다.",
        problem: "혼자 잘 쉬고 싶은 사람일수록 막상 쉬는 날 “뭐 하지”를 검색하다 지쳐 침대와 넷플릭스로 하루를 끝낸다. 기존 코스·예약 앱은 커플·친구 동반 전제라 혼자 쓰기 어색하고, ‘AI 추천’을 내세워도 결국 장소 목록만 줄 뿐 동선·시간·예산을 조립하는 노동은 사용자 몫으로 남는다.",
        target: "혼자 잘 놀고 싶은 2030 1인 가구. 잘 쉬고 싶은 욕구는 크지만 코스 짜기가 막막하고 혼자라 더 귀찮은 사람. 결정·결제·사용이 모두 본인.",
        features: [
          { title: "감정 → 하나의 이야기", label: "Emotion to Story", body: "“위로받고 싶다” 같은 감정 한 줄과 위치·시간·예산을 넣으면, AI가 목록이 아니라 아침에서 저녁으로 흐르는 하나의 하루를 연출한다. “11시 햇빛 드는 창가 카페 → 13시 잔잔한 전시 → 16시 강변 산책 → 18시 1인석 좋은 식당” — 각 코스엔 ‘왜 지금 네 기분에 맞는지’ 한 줄 내레이션." },
          { title: "추천에서 실제 소비로", label: "Book in One Tap", body: "예약·결제·재고를 직접 만들지 않는다. 코스의 각 장소를 네이버예약·캐치테이블·프립·클룩 등 기존 예약 페이지로 원클릭 연결하고 어필리에이트로 수익화. 공급 확보 부담 없이 ‘추천 → 실소비’를 곧장 잇는다." }
        ],
        impact: "‘구경만’ 하던 여가 앱을 실제 외출과 소비로 바꾸는 커머스형 서비스. 혼자서도 영화 같은 하루를 연출받는 경험. 커플·친구·외국인 관광객 모드로 확장 여지."
      },
      {
        code: "03", mono: "FK", slug: "freshkeep", name: "다썼다", en: "Freshkeep",
        tagline: "사진 한 장으로 끝나는 유통기한 관리",
        category: "생활·소비 / AI 비전",
        tags: ["생활·소비", "AI VISION"],
        accent: "#B8FF2E", accentInk: "#0B0B0C",
        hook: "사서 다 못 쓰고 버리는 손실, 매주 반복된다. 다썼다는 사진 한 장으로 그 고리를 끊는다.",
        problem: "필요해서 샀지만 다 쓰지 못하고 버리는 손실이 매주 반복된다. 냉장고 안쪽 식품은 유통기한을 넘겨 폐기되고, 화장품은 개봉 후 사용기한을 몰라 방치되며, 상비약은 유효기간이 지난 채 쌓인다. 뭐가 집에 있는지 몰라 중복 구매도 잦다. 1~2인 가구에서 특히 크지만, 일일이 기록하는 번거로움 탓에 관리가 안 된다.",
        target: "냉장고·욕실·약통 관리가 어려운 자취 2030 1인가구. 관리 의지는 있으나 실행이 어려운 층.",
        features: [
          { title: "사진 한 장으로 끝나는 AI 자동 입력", label: "Snap to Log", body: "상품이나 영수증을 찍으면 비전 AI가 품목·카테고리·사용기한을 자동으로 채운다. 종류별 기한 엔진 자동 적용(식품 OCR / 화장품 개봉 후 사용기한 / 의약품 유효기간 / 생활용품 소진주기). 인식이 애매하면 추정값을 1탭으로 보정 — 입력 마찰을 0에 가깝게. (작동하는 PoC로 품목 인식 정확도를 이미 실측.)" },
          { title: "만료 임박을 레시피로 잇는 재방문 엔진", label: "Expiry to Recipe", body: "사용기한이 임박하면 알림에 그치지 않고, 지금 가진 곧 만료될 재료로 만들 수 있는 요리를 AI가 제안한다(우유·계란·식빵 → 프렌치토스트). “치약 있나?” 검색으로 중복 구매도 방지. 알림이 부담이 아니라 실질 효용이 되어 주 단위 재방문 습관을 만든다." }
        ],
        impact: "폐기·중복 구매 손실을 줄이고 기록의 수고를 없앤다. 음식물 쓰레기 절감이라는 사회적 효용까지."
      },
      {
        code: "04", mono: "TO", slug: "tryon", name: "입어봐AI", en: "Tryon AI",
        tagline: "내 사진 위에, 실제로 입어보는 하루",
        category: "커머스·AI / 가상 피팅",
        tags: ["커머스·패션", "VIRTUAL TRY-ON"],
        accent: "#FF3D9A", accentInk: "#0B0B0C",
        hook: "“이거 나한테 어울릴까?” 결제 직전의 망설임을, 내 사진 위 가상 피팅으로 없앤다.",
        problem: "온라인으로 옷을 살 때 가장 큰 고민은 “나한테 어울릴까, 내 체형에 맞을까”. 모델 컷만 보고 샀다가 안 어울려 반품하는 비용과 시간이 크다. 매장 피팅룸은 줄 서고 갈아입는 피로가 크고, 기존 2D 스티커식 가상 피팅은 옷을 얹은 티가 나 결정에 도움이 안 된다.",
        target: "패션에 관심 많고 온라인 쇼핑을 즐기지만 실패 없는 쇼핑을 원하는 1030 프로 쇼핑러. 장바구니에 담아두고 며칠째 결제를 망설이는 사람.",
        features: [
          { title: "원클릭 AI 가상 피팅", label: "Virtual Try-On", body: "전신(또는 상반신) 사진을 한 번 등록하면, 앱 속 옷이나 쇼핑몰 옷 이미지를 골랐을 때 AI가 주름·그림자·체형 굴곡까지 반영해 자연스럽게 입혀준다." },
          { title: "믹스앤매치 레이어드 룸", label: "Mix & Match", body: "상의와 하의를 각각 골라 동시에 입혀본다. “내 청바지”에 “새로 살 니트”를 매치해 코디를 미리 보고 저장." }
        ],
        impact: "직접 입어보지 않고도 어울림을 확인해 온라인 패션 쇼핑의 실패율을 낮춘다. 쇼핑몰엔 ‘입어보기’ 위젯으로 반품률을 낮추는 B2B 확장, 어필리에이트 연동으로 구매까지 매끄럽게. (고성능 가상 피팅 AI가 저렴한 API로 열려 짧은 기간에도 구현 가능.)"
      },
      {
        code: "05", mono: "GD", slug: "gudokja", name: "구독자", en: "Gudokja",
        tagline: "다음 달도 낼 건가요? — 결제 전에 다시 묻는다",
        category: "핀테크·절약",
        tags: ["핀테크·절약", "SUBSCRIPTION"],
        accent: "#00C2FF", accentInk: "#0B0B0C",
        hook: "조용히 빠져나가는 구독료. 결제되기 전에 딱 한 번, 다시 보게 만든다.",
        problem: "가입은 기억해도 해지는 자주 잊는다. 무료체험은 어느새 유료로 바뀌고, OTT·멤버십·앱스토어·클라우드 구독료가 카드 문자·카톡 알림·이메일 영수증에 흩어져 있다. “내가 지금 뭘 구독하지?”를 확인하려면 여러 앱을 뒤져야 하고, 그새 매달 몇 만 원이 샌다.",
        target: "OTT·멤버십·앱스토어·클라우드·생산성 도구를 여러 개 쓰는 2030~40 직장인. 무료체험 해지를 잊은 적 있는 사람. 가족 구독까지 대신 내는 사람도.",
        features: [
          { title: "구독 후보 자동 탐지", label: "Auto-Detect", body: "카드 문자·결제 알림·영수증·스크린샷을 공유하면 AI가 결제처·금액·주기와 ‘정기결제/월정액’ 키워드를 분석해 구독 후보를 찾는다. 첫 결제로 단정하지 않고 1탭 확인을 거쳐, 비슷한 금액이 27~33일 주기로 반복되면 월 구독으로 확정." },
          { title: "결제 전 컷 알림 + 해지 도우미", label: "Cut Before Charge", body: "다음 결제 3일 전 “이번 달도 유지할까요?”라고 묻는다. 해지를 고르면 서비스별 해지 경로·구독 관리 바로가기·체크리스트를 제공. 월간 리포트로 유지 중인 구독, 안 쓰는 구독 의심, 끊어서 아낀 금액을 한눈에." }
        ],
        impact: "매달 조용히 새던 고정비를 결제 전에 다시 보게 만들어 불필요한 지출을 줄인다. 개인 절약에서 가족 구독 관리, 카드사·마이데이터 제휴까지 확장."
      }
    ]
  };
});
