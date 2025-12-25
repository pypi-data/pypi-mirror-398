from multimodal_agent.codegen.engine import CodegenEngine


def test_insert_material_import_when_missing():
    eng = CodegenEngine()
    code = "class A {}"
    out = eng.ensure_material_import(code)
    assert "import 'package:flutter/material.dart';" in out


def test_does_not_duplicate_import():
    eng = CodegenEngine()
    code = "import 'package:flutter/material.dart';\nclass A {}"
    out = eng.ensure_material_import(code)
    assert out.count("material.dart") == 1
