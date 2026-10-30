"""SPEC_COUPON.md 명세의 예시표를 검증하는 테스트 (세션 4용).

규칙 R1~R5에 정의된 경계값 및 중복 방지, 입력 거절 예시를 검증합니다.
"""

import pytest
from fastapi.testclient import TestClient

from app.deps import get_predict
from app.main import app


# R1, R2, R3: 쿠폰 발급(사과/감사) 및 미발급 예시표 (총 10개 행)
COUPON_RULE_CASES = [
    # R1: 사과 쿠폰 발급 (온도 <= 20.0)
    pytest.param("r1", "최악입니다", 0.0, True, "APOLOGY", 3000, "APOLOGY-r1", id="r1-temp-0.0"),
    pytest.param("r2", "별로예요", 20.0, True, "APOLOGY", 3000, "APOLOGY-r2", id="r2-temp-20.0"),
    pytest.param("r3", "아쉬워요", 20.1, False, None, None, None, id="r3-temp-20.1"),
    # R2: 감사 쿠폰 발급 (온도 >= 85.0 and 길이 >= 30)
    pytest.param("r4", "배송도 정말 빠르고 품질도 아주 훌륭해서 대만족합니다!", 85.0, True, "THANKS", 1000, "THANKS-r4", id="r4-len-30-temp-85.0"),
    pytest.param("r5", "디자인도 예쁘고 마감도 깔끔해서 가족들 모두 만족스럽게 잘 쓰고 있습니다. 강력 추천해요!", 100.0, True, "THANKS", 1000, "THANKS-r5", id="r5-len-40-temp-100.0"),
    pytest.param("r6", "배송도 정말 빠르고 품질도 아주 훌륭해서 대만족합니다!", 84.9, False, None, None, None, id="r6-len-30-temp-84.9"),
    pytest.param("r7", "배송 빠르고 품질 훌륭해서 대만족합니다 최고입니다!!", 85.0, False, None, None, None, id="r7-len-29-temp-85.0"),
    pytest.param("r8", "배송 빠르고 품질 훌륭해서 대만족합니다 최고입니다!!", 95.0, False, None, None, None, id="r8-len-29-temp-95.0"),
    # R3: 쿠폰 대상 제외
    pytest.param("r9", "보통이에요 쓸만합니다", 50.0, False, None, None, None, id="r9-len-15-temp-50.0"),
    pytest.param("r10", "포장 상태도 좋고 상품도 무난해서 그럭저럭 쓸만하네요 나쁘지 않아요", 84.9, False, None, None, None, id="r10-len-35-temp-84.9"),
]


@pytest.mark.parametrize(
    (
        "review_id",
        "text",
        "temperature",
        "expected_issued",
        "expected_type",
        "expected_amount",
        "expected_code",
    ),
    COUPON_RULE_CASES,
)
def test_coupon_issue_rules(
    review_id: str,
    text: str,
    temperature: float,
    expected_issued: bool,
    expected_type: str | None,
    expected_amount: int | None,
    expected_code: str | None,
) -> None:
    """R1~R3 예시표: 사과/감사 쿠폰 발급 및 미발급 검증."""
    score = temperature / 100.0
    app.dependency_overrides[get_predict] = lambda: lambda _texts: [score]
    try:
        response = TestClient(app).post(
            "/v1/coupons/issue",
            json={"review_id": review_id, "text": text},
        )
    finally:
        app.dependency_overrides.pop(get_predict, None)

    assert response.status_code == 200
    assert response.json() == {
        "issued": expected_issued,
        "coupon_type": expected_type,
        "amount": expected_amount,
        "code": expected_code,
    }


def test_coupon_duplicate_prevented():
    """R4: 동일 review_id 중복 발급 시 409 Conflict."""
    score = 0.15  # 온도 15.0℃ -> 발급 대상
    app.dependency_overrides[get_predict] = lambda: lambda _texts: [score]
    client = TestClient(app)
    try:
        # 1회차: 최초 발급 성공
        r1 = client.post("/v1/coupons/issue", json={"review_id": "r-dup-1", "text": "불만족스러워요"})
        assert r1.status_code == 200
        assert r1.json()["issued"] is True

        # 2회차(재요청): 중복 발급 시 409
        r2 = client.post("/v1/coupons/issue", json={"review_id": "r-dup-1", "text": "불만족스러워요"})
        assert r2.status_code == 409
    finally:
        app.dependency_overrides.pop(get_predict, None)


@pytest.mark.parametrize(
    ("review_id", "text"),
    [
        pytest.param("", "좋아요", id="empty-review-id"),
        pytest.param("r-invalid-1", "   ", id="blank-text"),
        pytest.param("r-invalid-2", "a" * 501, id="over-500-text"),
    ],
)
def test_coupon_invalid_input_rejected(review_id: str, text: str):
    """R5: 잘못된 입력 거절 (HTTP 422)."""
    response = TestClient(app).post(
        "/v1/coupons/issue",
        json={"review_id": review_id, "text": text},
    )
    assert response.status_code == 422
