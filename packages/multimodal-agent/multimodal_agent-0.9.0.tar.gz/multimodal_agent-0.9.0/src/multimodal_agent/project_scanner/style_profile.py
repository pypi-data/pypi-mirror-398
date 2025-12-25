def extract_style_profile(scan_result: dict) -> dict:
    """
    Convert raw scanner output into a clean style profile.
    """
    getter = (
        scan_result.get
        if isinstance(scan_result, dict)
        else lambda k, default=None: getattr(scan_result, k, default)
    )
    style = {
        "package_name": getter("package_name"),
        "uses_bloc": getter("uses_bloc", False),
        "uses_getx": getter("uses_getx", False),
        "uses_riverpod": getter("uses_riverpod", False),
        "architecture": getter("architecture", None),
        "indentation": 2,  # placeholder
        "quotes": "single",
        "naming": {
            "classes": "PascalCase",
            "methods": "camelCase",
        },
        "lint_rules": getter("lint_rules", {}),
    }

    return style
