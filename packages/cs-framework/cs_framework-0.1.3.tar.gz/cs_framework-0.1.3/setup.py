from setuptools import setup, find_packages

setup(
    name="cs-framework",
    version="0.1.2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "cs_framework": [
            "skills/**/*",
            "tools/speckit_integration/templates/*",
        ],
    },
    install_requires=[
        "rdflib>=7.0.0",
        "nicegui>=1.4.0",
        "pyyaml>=6.0",
        "loguru>=0.7.0",
        "networkx>=3.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "csfw=cs_framework.cli:main",
        ],
    },
)
