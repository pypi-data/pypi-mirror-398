from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="industrial-readers-client",
    version="1.0.0",
    author="Industrial Readers Team",
    author_email="contact@example.com",
    description="High-performance Python client for Industrial Readers Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/soberonlineemail/profilereaders",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": ["pytest>=6.0", "black", "flake8"],
    },
    keywords="document reader excel word pdf powerpoint file parsing",
    project_urls={
        "Bug Reports": "https://gitlab.com/soberonlineemail/profilereaders/-/issues",
        "Source": "https://gitlab.com/soberonlineemail/profilereaders",
        "Documentation": "https://gitlab.com/soberonlineemail/profilereaders/-/blob/main/README.md",
    },
)