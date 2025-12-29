from setuptools import setup, find_packages

setup(
    name="RedditMiner",
    version="1.0.0",
    description="A Python tool for scraping images, galleries, and comments from Reddit using browser cookies.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Misbah Khan",
    author_email="your-email@example.com",
    url="https://github.com/MisbahKhan0009/RedditMiner",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.0.0"
    ],
    include_package_data=True,
    package_data={
        "": ["cookies.txt", "assets/logo.svg"]
    },
    entry_points={
        "console_scripts": [
            "redditminer=main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Utilities"
    ],
    license="MIT",
    keywords="reddit scraper images gallery comments download",
)