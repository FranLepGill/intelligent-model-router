from app.modules.evaluations.dataset_cases import CUSTOMER_SUPPORT_CASES, build_customer_support_cases
from app.modules.evaluations.scoring import score_case


def test_dataset_has_at_least_50_cases():
    assert len(CUSTOMER_SUPPORT_CASES) >= 50
    assert len(CUSTOMER_SUPPORT_CASES) == 80


def test_dataset_covers_all_demo_categories():
    categories = {c["expected_output"]["category"] for c in CUSTOMER_SUPPORT_CASES}
    assert categories == {
        "password_problem",
        "duplicate_charge",
        "refund_problem",
        "account_blocked",
        "general_question",
    }


def test_case_keys_are_unique():
    keys = [c["case_key"] for c in CUSTOMER_SUPPORT_CASES]
    assert len(keys) == len(set(keys))


def test_build_customer_support_cases_respects_target():
    assert len(build_customer_support_cases(60)) == 60


def test_score_case_exact_match():
    score, correct = score_case(
        expected={"category": "duplicate_charge", "priority": "high"},
        obtained={"category": "duplicate_charge", "priority": "high"},
        valid_output=True,
    )
    assert score == 1.0
    assert correct is True


def test_score_case_category_only():
    score, correct = score_case(
        expected={"category": "duplicate_charge", "priority": "high"},
        obtained={"category": "duplicate_charge", "priority": "medium"},
        valid_output=True,
    )
    assert score == 0.75
    assert correct is True


def test_score_case_invalid_output():
    score, correct = score_case(
        expected={"category": "duplicate_charge"},
        obtained=None,
        valid_output=False,
    )
    assert score == 0.0
    assert correct is False
