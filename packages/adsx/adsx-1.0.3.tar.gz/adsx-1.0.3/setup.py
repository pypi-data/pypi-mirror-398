from setuptools import setup, find_packages

setup(
    name="adsx",
    version="1.0.3",   # 🔼 bump version EVERY fix
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "adsx": ["payload/*"]
    },
    entry_points={
        "console_scripts": [
            "adsx=adsx.cli:run"
        ]
    },
    python_requires=">=3.8",
)
