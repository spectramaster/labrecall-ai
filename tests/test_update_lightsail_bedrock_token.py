from pathlib import Path

import pytest

from scripts.update_lightsail_bedrock_token import replace_token


def test_replace_token_preserves_all_other_settings() -> None:
    original = (
        "LABRECALL_MODE=cloud\n"
        "DATABASE_URL=postgresql://example\n"
        "AWS_BEARER_TOKEN_BEDROCK=old\n"
        "MEMORY_NAMESPACE=public-demo\n"  # pragma: allowlist secret
    )

    assert replace_token(original, "new-token") == (
        "LABRECALL_MODE=cloud\n"
        "DATABASE_URL=postgresql://example\n"
        "AWS_BEARER_TOKEN_BEDROCK=new-token\n"
        "MEMORY_NAMESPACE=public-demo\n"  # pragma: allowlist secret
    )


@pytest.mark.parametrize(
    "content",
    [
        "DATABASE_URL=postgresql://example\n",
        "AWS_BEARER_TOKEN_BEDROCK=one\nAWS_BEARER_TOKEN_BEDROCK=two\n",
    ],
)
def test_replace_token_requires_exactly_one_entry(content: str) -> None:
    with pytest.raises(ValueError, match="expected exactly one"):
        replace_token(content, "new-token")


def test_script_contains_no_environment_specific_secret() -> None:
    script = Path("scripts/update_lightsail_bedrock_token.py").read_text(encoding="utf-8")
    assert "postgresql://" not in script
    assert "ABSK" not in script
