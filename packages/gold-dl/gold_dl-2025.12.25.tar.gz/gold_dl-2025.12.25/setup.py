"""
This module contains the setup configuration for the VoLTGoLD-YT package.
"""

from setuptools import find_packages, setup
import os
import re

# قراءة الإصدار مباشرة من الملف بدلاً من الاستيراد لتجنب أخطاء التبعيات
def get_version():
    # محاولة قراءة الإصدار من ملف utils.py
    try:
        with open("gold_dl/utils.py", "r", encoding="utf-8") as f:
            content = f.read()
            version_match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1)
    except FileNotFoundError:
        pass
    
    # إذا لم يتم العثور على الإصدار، استخدم إصدار افتراضي
    return "1.7.1"

# قراءة ملف README لاستخدامه كوصف طويل
with open("README.md", "r", encoding="utf-8") as f:
    description = f.read()

setup(
    # 🔹 اسم الحزمة (اسم الفورك)
    name="gold-dl",

    version=get_version(),

    # 🔹 بياناتك
    author="VOLT5775",
    author_email="VOLT5775@users.noreply.github.com",

    description=(
        "Library GoLD YouTube downloader "
        "(video / audio / shorts / playlists) "
        "with smart caching and auto quality handling"
    ),

    long_description=description,
    long_description_content_type="text/markdown",

    keywords=[
        "youtube",
        "download",
        "cli",
        "gold-dl",
        "voltgold",
        "yt-downloader",
        "pytubefix",
        "pytube",
        "youtube-dl",
    ],

    license="MIT",

    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Multimedia :: Video",
        "Topic :: Utilities",
    ],

    include_package_data=True,

    python_requires=">=3.6",

    install_requires=[
        "pytubefix>=0.4.0",
        "inquirer>=3.0.0",
        "yaspin>=3.0.0",
        "typer>=0.9.0",
        "requests>=2.28.0",
        "rich>=13.0.0",
        "termcolor>=2.0.0",
        "moviepy>=1.0.0",
    ],

    # إزالة setuptools لأنه مثبت مسبقاً مع بايثون
    setup_requires=[],

    entry_points={
        "console_scripts": [
            # 🔹 اسم الأمر في التيرمنال
            "gold-dl=gold_dl:cli.app",
        ],
    },

    project_urls={
        "Homepage": "https://github.com/VOLT5775/VoLTGoLD-YT",
        "Source Code": "https://github.com/VOLT5775/VoLTGoLD-YT",
        "Bug Tracker": "https://github.com/VOLT5775/VoLTGoLD-YT/issues",
        "Documentation": "https://github.com/VOLT5775/VoLTGoLD-YT",
        "Author": "https://github.com/VOLT5775",
    },

    platforms=["Linux", "Windows", "MacOS"],
    packages=find_packages(),
)