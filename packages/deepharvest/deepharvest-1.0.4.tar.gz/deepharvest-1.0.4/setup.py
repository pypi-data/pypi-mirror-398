"""
DeepHarvest Setup
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8") if (Path(__file__).parent / "README.md").exists() else "DeepHarvest - The World's Most Complete Web Crawler"

setup(
    name="deepharvest",
    version="1.0.4",
    author="DeepHarvest Contributors",
    description="The world's most complete, resilient, multilingual web crawler",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anajrajeev/DeepHarvest",
    project_urls={
        "Bug Tracker": "https://github.com/Anajrajeev/DeepHarvest/issues",
        "Source Code": "https://github.com/Anajrajeev/DeepHarvest",
    },
    packages=find_packages(),
    license="Apache-2.0",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies
        "aiohttp>=3.9.0",
        
        # HTML Parsing
        "lxml>=4.9.0",
        "beautifulsoup4>=4.12.0",
        "html5lib>=1.1",
        
        # JavaScript Rendering
        "playwright>=1.40.0",
        
        # Content Extraction
        "PyMuPDF>=1.23.0",  # PDF
        "python-docx>=1.1.0",  # DOCX
        "python-pptx>=0.6.21",  # PPTX
        "openpyxl>=3.1.0",  # XLSX
        "Pillow>=10.1.0",  # Images
        "pytesseract>=0.3.10",  # OCR
        
        # Structured Data
        "extruct>=0.15.0",
        
        # Multilingual
        "chardet>=5.2.0",
        "charset-normalizer>=3.3.0",
        "langdetect>=1.0.9",
        
        # ML/AI
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "simhash>=2.1.0",
        "datasketch>=1.6.0",
        "mmh3>=4.0.0",
        
        # Distributed
        "redis[hiredis]>=5.0.0",
        
        # Storage
        "boto3>=1.28.0",  # S3
        "psycopg2-binary>=2.9.0",  # PostgreSQL
        
        # CLI
        "click>=8.1.0",
        "pyyaml>=6.0",
        
        # Monitoring
        "prometheus-client>=0.19.0",
        
        # Utilities
        "tqdm>=4.66.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
        ],
        "full": [
            "torch>=2.1.0",  # For advanced ML models
            "transformers>=4.35.0",  # For LLM-based extraction
        ],
    },
    entry_points={
        "console_scripts": [
            "deepharvest=deepharvest.cli.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

