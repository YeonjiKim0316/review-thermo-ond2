import pytest
from fastapi.testclient import TestClient

from app.deps import get_predict
from app.main import app


@pytest.mark.parametrize(
    (
        "text",
        "rating",
        "score",
        "expected_label",
        "expected_temperature",
        "expected_mismatch",
    ),
    [
        pytest.param("좋아요", 5, 0.9, "positive", 90.0, False, id="rating-5-score-0.9"),
        pytest.param("배송 최악", 5, 0.2, "negative", 20.0, True, id="rating-5-score-0.2"),
        pytest.param("무난해요", 3, 0.5, "positive", 50.0, False, id="rating-3-score-0.5"),
        pytest.param("좋아요", 4, 0.4999, "negative", 50.0, True, id="rating-4-score-0.4999"),
        pytest.param("좋아요", 2, 0.5, "positive", 50.0, True, id="rating-2-score-0.5"),
        pytest.param("배송 최악", 1, 0.1, "negative", 10.0, False, id="rating-1-score-0.1"),
        pytest.param("아주 좋아요", 5, 1.0, "positive", 100.0, False, id="rating-5-score-1.0"),
        pytest.param("그저 그래요", 3, 0.0, "negative", 0.0, False, id="rating-3-score-0.0"),
    ],
)
def test_review_thermometer_examples(
    text: str,
    rating: int,
    score: float,
    expected_label: str,
    expected_temperature: float,
    expected_mismatch: bool,
) -> None:
    app.dependency_overrides[get_predict] = lambda: lambda _texts: [score]
    try:
        response = TestClient(app).post(
            "/v1/reviews/analyze",
            json={"text": text, "rating": rating},
        )
    finally:
        app.dependency_overrides.pop(get_predict, None)

    assert response.status_code == 200
    assert response.json() == {
        "label": expected_label,
        "score": score,
        "temperature": expected_temperature,
        "mismatch": expected_mismatch,
    }
