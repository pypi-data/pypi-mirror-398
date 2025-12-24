from setuptools import setup, find_packages

setup(
    name="TubeLine",
    version="0.1.0",
    description="YouTube Timeline Pipeline",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    author="강은성",
    author_email="grootseong@gmail.com",


    packages=find_packages(),
    include_package_data=True,

    python_requires=">=3.10",

    install_requires=[
        "requests>=2.31.0",
        "google-genai>=0.3.0",
        "yt-dlp>=2024.4.9",
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],

    keywords=[
        "youtube",
        "speech-to-text",
        "deepgram",
        "gemini",
        "ai",
        "stt",
        "video-analysis",
        "timeline",
        "time",
        "line",
    ],
)
