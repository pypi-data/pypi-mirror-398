from setuptools import setup, find_packages
from pathlib import Path

HERE = Path(__file__).parent

setup(
    name="usekit",
    version="0.1.1a0",
    author="ropnfop",
    author_email="withropnfop@gmail.com",
    description="Minimal input, auto path toolkit (mobile-first, Colab+Drive)",
    long_description=(HERE / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,  # MANIFEST.in + package_data를 함께 쓰면 안정적
    package_data={
        "usekit": [".env.example"],
    },
    python_requires=">=3.8",
)