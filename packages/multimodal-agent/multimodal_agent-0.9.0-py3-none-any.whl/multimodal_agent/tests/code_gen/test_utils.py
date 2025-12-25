from multimodal_agent.codegen.utils import sanitize_class_name, to_snake_case


def test_sanitize_class_name_basic():
    assert sanitize_class_name("my widget") == "MyWidget"
    assert sanitize_class_name("my-widget") == "MyWidget"
    assert sanitize_class_name("my_widget") == "MyWidget"


def test_sanitize_class_name_handles_numbers():
    assert sanitize_class_name("123widget") == "W123widget"


def test_sanitize_class_name_empty_input():
    assert sanitize_class_name("") == "GeneratedWidget"


def test_to_snake_case_basic():
    assert to_snake_case("MyWidget") == "my_widget"
    assert to_snake_case("MyWidgetScreen") == "my_widget_screen"


def test_to_snake_case_with_specials():
    assert to_snake_case("my widget") == "my_widget"
    assert to_snake_case("my-widget") == "my_widget"
    assert to_snake_case("my@weird#name") == "myweirdname"


def test_sanitize_removes_invalid_chars():
    assert sanitize_class_name("my@widget!") == "MyWidget"


def test_sanitize_leading_numbers():
    assert sanitize_class_name("42screen") == "W42screen"


def test_sanitize_all_invalid():
    assert sanitize_class_name("@#$%") == "GeneratedWidget"


def test_snake_case_camel_case():
    assert to_snake_case("MyAwesomeWidget") == "my_awesome_widget"


def test_snake_case_removes_specials():
    assert to_snake_case("my@invalid-name!") == "myinvalid_name"
