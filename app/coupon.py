"""쿠폰 발급 도메인 규칙 및 중복 검사 로직 (세션 4).

SPEC_COUPON.md 규칙:
- R1: 온도 <= 20.0℃ -> 사과(APOLOGY) 쿠폰 3,000원
- R2: 온도 >= 85.0℃ AND 공백 포함 글자 수 >= 30자 -> 감사(THANKS) 쿠폰 1,000원
- R3: 그 외 -> issued: False (HTTP 200)
- R4: 동일 review_id 중복 발급 시 -> 409 Conflict
"""

from fastapi import HTTPException

from app.schemas import CouponIssueResponse

# 발급 완료된 review_id 목록 추적 (인메모리 저장소)
ISSUED_REVIEWS: set[str] = set()


def clear_issued_reviews() -> None:
    """테스트 간 상태 격리를 위해 발급 목록을 초기화합니다."""
    ISSUED_REVIEWS.clear()


def issue_coupon(review_id: str, text: str, temperature: float) -> CouponIssueResponse:
    """리뷰 온도와 본문 길이를 평가하여 쿠폰을 발급합니다."""
    # R4: 중복 발급 방지 (이미 발급된 리뷰인 경우 409 오류)
    if review_id in ISSUED_REVIEWS:
        raise HTTPException(status_code=409, detail="이미 쿠폰이 발급된 리뷰입니다")

    # R1: 불만 고객 사과 쿠폰 (온도 20.0℃ 이하)
    if temperature <= 20.0:
        ISSUED_REVIEWS.add(review_id)
        return CouponIssueResponse(
            issued=True,
            coupon_type="APOLOGY",
            amount=3000,
            code=f"APOLOGY-{review_id}",
        )

    # R2: 정성 호평 고객 감사 쿠폰 (온도 85.0℃ 이상 AND 글자 수 30자 이상)
    if temperature >= 85.0 and len(text) >= 30:
        ISSUED_REVIEWS.add(review_id)
        return CouponIssueResponse(
            issued=True,
            coupon_type="THANKS",
            amount=1000,
            code=f"THANKS-{review_id}",
        )

    # R3: 쿠폰 대상 제외
    return CouponIssueResponse(
        issued=False,
        coupon_type=None,
        amount=None,
        code=None,
    )

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
