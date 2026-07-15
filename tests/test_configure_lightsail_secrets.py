from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "configure_lightsail_secrets.py"
SPEC = spec_from_file_location("configure_lightsail_secrets", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_database_password_is_url_encoded() -> None:
    url = MODULE.build_database_url("a:b/@ c%")

    assert "a%3Ab%2F%40%20c%25" in url
    assert "sslmode=verify-full" in url
    assert "sslrootcert=/home/ec2-user/.postgresql/root.crt" in url


def test_environment_has_only_expected_keys() -> None:
    rendered = MODULE.render_environment("postgresql://example", "token")

    assert rendered.splitlines() == [
        "LABRECALL_MODE=cloud",
        "AWS_REGION=us-east-1",
        "MEMORY_NAMESPACE=public-demo",
        "RETRIEVAL_MIN_SIMILARITY=0.65",
        "DATABASE_URL=postgresql://example",
        "AWS_BEARER_TOKEN_BEDROCK=token",
    ]
