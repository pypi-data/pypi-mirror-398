import pytest

from kiarina.llm.run_context import create_run_context


# fmt: off
@pytest.mark.parametrize("name", [
    "MyApp",
    "My App",
    "My-App",
    "My_App",
    "My.App",
    "My App v1.0",
    "Test-App_v2.1",
    "Test App ",  # Trailing space is stripped, so this becomes valid
    "Test ",      # Trailing space is stripped, so this becomes valid
])
# fmt: on
def test_fs_name_valid(name):
    """Test that valid FSName values are accepted"""
    context = create_run_context(app_author=name, app_name=name)
    assert context.app_author == name
    assert context.app_name == name


# fmt: off
@pytest.mark.parametrize("name,expected_match", [
    # Names ending with dots (spaces are stripped, so they're actually valid)
    ("Test App.", "cannot end with a dot or space"),
    ("Test.", "cannot end with a dot or space"),

    # Names starting with dots
    (".hidden", "cannot start with a dot"),
    (".test", "cannot start with a dot"),
    (".myapp", "cannot start with a dot"),

    # Windows reserved names
    ("CON", "is a reserved name on Windows"),
    ("con", "is a reserved name on Windows"),
    ("Con", "is a reserved name on Windows"),
    ("PRN", "is a reserved name on Windows"),
    ("prn", "is a reserved name on Windows"),
    ("Prn", "is a reserved name on Windows"),
    ("AUX", "is a reserved name on Windows"),
    ("aux", "is a reserved name on Windows"),
    ("Aux", "is a reserved name on Windows"),
    ("NUL", "is a reserved name on Windows"),
    ("nul", "is a reserved name on Windows"),
    ("Nul", "is a reserved name on Windows"),
    ("COM1", "is a reserved name on Windows"),
    ("com1", "is a reserved name on Windows"),
    ("Com1", "is a reserved name on Windows"),
    ("COM9", "is a reserved name on Windows"),
    ("com9", "is a reserved name on Windows"),
    ("Com9", "is a reserved name on Windows"),
    ("LPT1", "is a reserved name on Windows"),
    ("lpt1", "is a reserved name on Windows"),
    ("Lpt1", "is a reserved name on Windows"),
    ("LPT9", "is a reserved name on Windows"),
    ("lpt9", "is a reserved name on Windows"),
    ("Lpt9", "is a reserved name on Windows"),

    # Empty string
    ("", None),  # No specific match pattern for empty string

    # Invalid characters
    ("Test/App", None),
    ("Test\\App", None),
    ("Test:App", None),
    ("Test*App", None),
    ("Test?App", None),
    ("Test\"App", None),
    ("Test<App", None),
    ("Test>App", None),
    ("Test|App", None),
    ("Test@App", None),
    ("Test#App", None),
])
# fmt: on
def test_fs_name_invalid(name, expected_match):
    """Test that invalid FSName values are rejected"""
    if expected_match:
        with pytest.raises(ValueError, match=expected_match):
            create_run_context(app_author=name)
    else:
        with pytest.raises(ValueError):
            create_run_context(app_author=name)
