from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sixfinger",
    version="2.0.0",  # 🔼 Version bump: yeni feature
    author="Sixfinger Team",
    author_email="sixfingerdev@gmail.com",
    description="Ultra-fast AI platform: API client + On-device language models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://sfapi.pythonanywhere.com",
    project_urls={
        "Documentation": "https://sfapi.pythonanywhere.com/docs",
        "Source": "https://github.com/sixfinger/sixfinger-python",
        "Changelog": "https://github.com/sixfinger/sixfinger-python/blob/main/CHANGELOG.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "async": ["aiohttp>=3.8.0"],
        "transformers": [  # 🆕 On-device models
            "numpy>=1.19.0",
            "tqdm>=4.50.0",
        ],
        "transformers-fast": [  # 🆕 With acceleration
            "numpy>=1.19.0",
            "tqdm>=4.50.0",
            "numba>=0.53.0",
        ],
        "all": [  # Hepsi
            "aiohttp>=3.8.0",
            "numpy>=1.19.0",
            "tqdm>=4.50.0",
        ],
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.9",
        ],
    },
    keywords="ai chatbot api llm sixfinger artificial-intelligence transformers on-device",
    entry_points={
        "console_scripts": [
            "sixfinger-train=sixfinger.transformers.cli.train:main [transformers]",
            "sixfinger-generate=sixfinger.transformers.cli.generate:main [transformers]",
        ],
    },
)