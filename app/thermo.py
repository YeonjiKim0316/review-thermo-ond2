"""리뷰 온도 계산 규칙."""


def to_label(score: float) -> str:
    """긍정 확률이 0.5 이상이면 positive, 아니면 negative를 반환한다."""
    return "positive" if score >= 0.5 else "negative"


def to_temperature(score: float) -> float:
    """긍정 확률을 0~100℃로 환산하고 소수점 첫째 자리까지 반올림한다."""
    return round(score * 100, 1)


def is_mismatch(rating: int, label: str) -> bool:
    """별점 4~5의 부정 리뷰 또는 별점 1~2의 긍정 리뷰면 True를 반환한다."""
    return (rating >= 4 and label == "negative") or (rating <= 2 and label == "positive")

# © 2026 김연지. All rights reserved. 수강생 개인 학습용 · 무단 강의·복제·배포·수정 금지 (LICENSE.md)
