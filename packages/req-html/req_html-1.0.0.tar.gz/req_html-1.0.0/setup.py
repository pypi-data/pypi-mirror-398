from setuptools import setup, find_packages

setup(
    name="req-html",
    version="1.0.0",
    author="PixelPirate-bit",
    description="Tool to analyze website and APIs via HTTP requests",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/PixelPirate-bit/tool-REQ-HTML",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "pyfiglet>=0.8.post1",
        "colorama>=0.4.4"
    ],
    entry_points={
        "console_scripts": [
            "req-html=req_html.main:main"
        ]
    },
    python_requires='>=3.8',

)