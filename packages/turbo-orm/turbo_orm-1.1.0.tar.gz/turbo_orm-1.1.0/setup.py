from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="turbo-orm",
    version="1.0.0",
    author="Turbo ORM Team",
    author_email="team@turbo-orm.dev",
    description="Ultra-fast Python ORM - 15.2x faster than SQLAlchemy with advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/turbo-orm/turbo-orm",
    packages=find_packages(exclude=["tests", "demos", "staging", "build", "*.egg-info"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: AsyncIO",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core ORM has zero dependencies for lightweight deployment
    ],
    extras_require={
        "async": ["aiosqlite>=0.19.0"],
        "redis": ["redis>=4.5.0"],
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.0.0", "mypy>=1.0.0"],
    },
    entry_points={
        "console_scripts": [
            "turbo=turbo.cli:main",
        ],
    },
    keywords="orm database sqlite performance async turbo fast querybuilder",
    project_urls={
        "Documentation": "https://github.com/turbo-orm/turbo-orm#readme",
        "Bug Reports": "https://github.com/turbo-orm/turbo-orm/issues",
        "Source": "https://github.com/turbo-orm/turbo-orm",
        "Changelog": "https://github.com/turbo-orm/turbo-orm/releases",
    },
)
