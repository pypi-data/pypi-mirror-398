from setuptools import setup, find_packages
from pathlib import Path

BASE_DIR = Path(__file__).parent
README = (BASE_DIR / "README.md").read_text(encoding="utf-8")

setup(
    name="sslwatch",
    version="0.0.1",
    description="Library Python untuk pemantauan sertifikat SSL/TLS",
    long_description=README,
    long_description_content_type="text/markdown",

    author="Your Name",
    author_email="your.email@example.com",

    url="https://github.com/yourname/sslwatch",
    project_urls={
        "Documentation": "https://github.com/yourname/sslwatch#readme",
        "Source": "https://github.com/yourname/sslwatch",
        "Tracker": "https://github.com/yourname/sslwatch/issues",
    },

    license="MIT",
    license_files=("LICENSE",),

    packages=find_packages(exclude=("tests*",)),

    python_requires=">=3.8",

    install_requires=[],

    extras_require={
        "dev": ["pytest", "black", "flake8", "mypy"],
        "docs": ["sphinx", "sphinx-rtd-theme"],
    },

    include_package_data=True,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],

    keywords="ssl tls certificate monitoring security",
    zip_safe=False,
)
