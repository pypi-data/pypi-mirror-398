from setuptools import setup, find_packages
from pathlib import Path

HERE = Path(__file__).parent

setup(
    name="usekit",
    version="0.1.1",  # pyproject랑 맞추거나 여기 기준으로 통일
    author="ropnfop",
    author_email="withropnfop@gmail.com",
    description="Minimal input, auto path toolkit (mobile-first, Colab+Drive)",
    long_description=(HERE / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",

    packages=find_packages(),   # 루트 usekit 구조와 딱 맞음
    include_package_data=True,  # 핵심

    package_data={
        "usekit": [
            ".env.example",
            "sys/sys_yaml/sys_const.yaml",
        ],
    },

    python_requires=">=3.8",

    install_requires=[
        "PyYAML>=5.1",
        "python-dotenv>=0.19.0",
    ],
)