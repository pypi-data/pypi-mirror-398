from setuptools import setup, find_packages

setup(
    name="59chat",
    version="0.3.6",
    author="YourName",
    description="59-second zero-trace terminal chat (Ultra-Light Edition)",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/59chat",
    packages=find_packages(),
    install_requires=[
        "textual>=0.45.0",
        "httpx>=0.25.0",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        "console_scripts": [
            "59chat=chat59.main:main_func",
        ],
    },
    python_requires=">=3.8",
)
