from setuptools import setup

# Most metadata is now handled by pyproject.toml
setup(
    name="castorscribe",
    py_modules=["main", "scanner", "generator"],
    entry_points={
        "console_scripts": [
            "castorscribe=main:run_tool",
        ],
    },
)