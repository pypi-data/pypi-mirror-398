from multimodal_agent.codegen.engine import CodegenEngine


def test_extract_code_no_fence():
    eng = CodegenEngine()
    raw = "class A {}"
    assert eng.extract_code(raw) == "class A {}"


def test_extract_code_with_dart_fence():
    eng = CodegenEngine()
    raw = "```dart\nclass A {}\n```"
    assert eng.extract_code(raw) == "class A {}"


def test_extract_code_with_plain_fence():
    eng = CodegenEngine()
    raw = "``` \nclass A {}\n```"
    assert eng.extract_code(raw) == "class A {}"
