from multimodal_agent.cli.formatting import detect_language


# Python
def test_detect_python_def():
    code = """
    def hello_world():
        print("hello")
    """
    assert detect_language(code) == "python"


def test_detect_python_class():
    code = """
    class MyClass(Base):
        pass
    """
    assert detect_language(code) == "python"


def test_detect_python_import():
    code = "import os\nimport sys"
    assert detect_language(code) == "python"


# JS/ TS
def test_detect_javascript_arrow_function():
    code = "const x = () => console.log('hi')"
    assert detect_language(code) == "javascript"


def test_detect_javascript_import():
    code = "import { useState } from 'react';"
    assert detect_language(code) == "javascript"


def test_detect_javascript_export_default():
    code = "export default function test() {}"
    assert detect_language(code) == "javascript"


# Java
def test_detect_java_main():
    code = """
    public class Main {
        public static void main(String[] args) {
            System.out.println("Hello");
        }
    }
    """
    assert detect_language(code) == "java"


def test_detect_java_import():
    code = "import java.util.List;"
    assert detect_language(code) == "java"


def test_detect_java_package():
    code = "package com.example.demo;"
    assert detect_language(code) == "java"


# C++
def test_detect_cpp_include():
    code = "#include <iostream>\nint main() {}"
    assert detect_language(code) == "cpp"


def test_detect_cpp_std_namespace():
    code = "std::vector<int> nums;"
    assert detect_language(code) == "cpp"


def test_detect_cpp_template():
    code = "template <typename T> class Box {};"
    assert detect_language(code) == "cpp"


# Swift
def test_detect_swift_func():
    code = """
    import Foundation

    func greet(name: String) -> String {
        return "Hello, \\(name)"
    }
    """
    assert detect_language(code) == "swift"


def test_detect_swift_let_var():
    code = "let x = 10\nvar y = 20"
    assert detect_language(code) == "swift"


# Kotlin
def test_detect_kotlin_fun():
    code = """
    fun greet(name: String): String {
        return "Hello $name"
    }
    """
    assert detect_language(code) == "kotlin"


def test_detect_kotlin_val_var():
    code = "val x = 10\nvar y = 20"
    assert detect_language(code) == "kotlin"


def test_detect_kotlin_suspend():
    code = "suspend fun loadData() { }"
    assert detect_language(code) == "kotlin"


# DART
def test_detect_dart_import():
    code = "import 'package:flutter/material.dart';"
    assert detect_language(code) == "dart"


def test_detect_dart_main():
    code = """
    void main() {
        runApp(MyApp());
    }
    """
    assert detect_language(code) == "dart"


def test_detect_dart_override():
    code = "@override\nWidget build(BuildContext context) {}"
    assert detect_language(code) == "dart"


# Objective-c
def test_detect_objc_interface():
    code = """
    @interface MyClass : NSObject
    @end
    """
    assert detect_language(code) == "objectivec"


def test_detect_objc_implementation():
    code = """
    @implementation MyClass
    - (void)hello { }
    @end
    """
    assert detect_language(code) == "objectivec"


def test_detect_objc_bracket_call():
    code = "[myObj doSomething];"
    assert detect_language(code) == "objectivec"


# FALLBACKS
def test_detect_plain_text():
    text = "This is just normal English text."
    assert detect_language(text) in ("", "plain", None)


def test_detect_empty():
    assert detect_language("") in ("", "plain", None)
