"""Setup configuration for agentbill-crewai package."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentbill-py-crewai",
    version="7.16.0",
    author="AgentBill",
    author_email="dominic@agentbill.io",
    description="AgentBill integration for CrewAI - Zero-config crew tracking",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://agentbill.io",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "crewai>=0.1.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pylint>=2.15.0",
            "black>=22.0.0",
        ],
    },
    keywords="crewai ai agent billing usage-tracking agentbill crew",
    project_urls={
        "Documentation": "https://docs.agentbill.io",
    },
)
