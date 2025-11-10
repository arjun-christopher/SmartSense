"""
Setup script for SmartSense AI Assistant.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="smartsense-ai-assistant",
    version="1.0.0",
    author="Arjun Christopher",
    author_email="arjun@smartsense.ai",
    description="A multimodal AI assistant for Windows with text, voice, and image understanding",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arjun-christopher/SmartSense",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics :: Capture :: Screen Capture",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.3.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "build": [
            "PyInstaller>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "smartsense=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
        "assets": ["*.*"],
        "config": ["*.yaml", "*.yml"],
    },
    zip_safe=False,
    keywords="ai assistant multimodal nlp computer vision automation voice speech windows",
    project_urls={
        "Bug Reports": "https://github.com/arjun-christopher/SmartSense/issues",
        "Source": "https://github.com/arjun-christopher/SmartSense",
        "Documentation": "https://github.com/arjun-christopher/SmartSense/blob/main/README.md",
    },
)