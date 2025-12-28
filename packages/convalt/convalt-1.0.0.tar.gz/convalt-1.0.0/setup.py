from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="convalt",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A universal format converter for images and audio files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/convalt",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/convalt/issues",
        "Documentation": "https://github.com/yourusername/convalt#readme",
        "Source Code": "https://github.com/yourusername/convalt",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    py_modules=["Convalt"],
    python_requires=">=3.7",
    install_requires=[
        "Pillow>=10.0.0",
        "pydub>=0.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
)