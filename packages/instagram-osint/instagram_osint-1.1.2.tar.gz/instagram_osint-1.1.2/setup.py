from setuptools import setup, find_packages
import os


def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


setup(
    name="instagram_osint",
    version="1.1.2",
    author="Junaid",
    author_email="contact@abujuni.dev",
    description="A powerful Instagram scraping and OSINT utility",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sudo-junaiddev/fork-InstagramOSINT",
    packages=find_packages(),
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
    ],
    entry_points={
        "console_scripts": [
            "igosint=instagram_osint.cli:main",
            "instagramOSINT=instagram_osint.cli:main",
        ],
    },
    keywords="instagram osint scraper social-media intelligence",
    project_urls={
        "Bug Reports": "https://github.com/sudo-junaiddev/fork-InstagramOSINT/issues",
        "Source": "https://github.com/sudo-junaiddev/fork-InstagramOSINT",
        "Documentation": "https://github.com/sudo-junaiddev/fork-InstagramOSINT#readme",
    },
)
