import pytest

from apppy.env import AppNames


@pytest.mark.parametrize(
    "prefix, expected_name_lower, expected_name_upper, expected_name_camel, expected_name_camel_upper, expected_env_prefix",  # noqa: E501
    [
        ("", "app", "APP", "app", "App", "APP"),
        ("auth", "authapp", "AUTHAPP", "authApp", "AuthApp", "AUTHAPP"),
    ],
)
def test_app_names_basic(
    prefix: str,
    expected_name_lower: str,
    expected_name_upper: str,
    expected_name_camel: str,
    expected_name_camel_upper: str,
    expected_env_prefix: str,
):
    app_names = AppNames(prefix)

    assert app_names.name_lower == expected_name_lower
    assert app_names.name_upper == expected_name_upper
    assert app_names.name_camel == expected_name_camel
    assert app_names.name_camel_upper == expected_name_camel_upper
    assert app_names.env_prefix == expected_env_prefix

    assert app_names.has_suffix is False
    assert app_names.suffix_lower is None


@pytest.mark.parametrize(
    "prefix, expected_name_lower, expected_name_upper, expected_name_camel, expected_name_camel_upper, expected_env_prefix",  # noqa: E501
    [
        ("", "appsuffix", "APPSUFFIX", "appSuffix", "AppSuffix", "APP_SUFFIX"),
        (
            "auth",
            "authappsuffix",
            "AUTHAPPSUFFIX",
            "authAppSuffix",
            "AuthAppSuffix",
            "AUTHAPP_SUFFIX",
        ),
    ],
)
def test_app_names_with_suffix(
    prefix: str,
    expected_name_lower: str,
    expected_name_upper: str,
    expected_name_camel: str,
    expected_name_camel_upper: str,
    expected_env_prefix: str,
):
    app_names = AppNames(prefix, suffix="suffix")

    assert app_names.name_lower == expected_name_lower
    assert app_names.name_upper == expected_name_upper
    assert app_names.name_camel == expected_name_camel
    assert app_names.name_camel_upper == expected_name_camel_upper
    assert app_names.env_prefix == expected_env_prefix

    assert app_names.has_suffix is True
    assert app_names.suffix_lower == "suffix"
