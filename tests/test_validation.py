from app.modules.validation.response import ResponseValidator


def test_valid_customer_support_json():
    result = ResponseValidator().validate(
        {
            "category": "duplicate_charge",
            "priority": "high",
            "suggested_response": "ok",
        },
        output_format="json",
        task_type="customer_support",
    )
    assert result.ok


def test_invalid_when_not_dict():
    result = ResponseValidator().validate(
        "texto libre",
        output_format="json",
        task_type="customer_support",
    )
    assert not result.ok
    assert "invalid_json_structure" in result.errors
