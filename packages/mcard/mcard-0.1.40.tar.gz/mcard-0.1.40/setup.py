from setuptools import setup, find_packages

setup(
    name="mcard",
    version="0.1.40",  # IO Monad Effects feature
    description="MCard - Local-first Content Addressable Storage with Content Type Detection",
    author="Ben Koo",
    author_email="koo0905@gmail.com",
    url="https://github.com/xlp0/MCard_TDD",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.9",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "ptr=mcard.cli:main",
        ],
    },
)
