"""
Setup script for Rohkun CLI v2
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="rohkun",
    version="3.3.3.4",
    description="Client-side code analysis tool for API connections",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Rohkun Labs",
    author_email="support@rohkun.com",
    url="https://rohkun.com",
    packages=find_packages(),
    package_data={
        "rohkun_cli": [
            "rendertell_engine/dist/*.js",
            "rendertell_engine/dist/*.d.ts",
            "rendertell_engine/dist/*.map",
            "rendertell_engine/package.json",
            "knowledge_graph/designer_handoff/*",
            "knowledge_graph/documentation/*",
            "knowledge_graph/ui/*",
        ],
    },
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
        "pyperclip>=1.8.2",
        "tree-sitter>=0.20.0",
        "tree-sitter-python>=0.20.0",
        "tree-sitter-javascript>=0.20.0",
        "tree-sitter-typescript>=0.20.0",
        "tree-sitter-go>=0.20.0",
        "tree-sitter-java>=0.20.0",
    ],
    entry_points={
        "console_scripts": [
            "rohkun=rohkun_cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)
