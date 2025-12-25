from setuptools import setup, find_packages

setup(
   name="reckomate_ai_sdk",   # 🔥 UNIQUE PyPI NAME
    version="0.2.0",
    description="Reckomate internal Python SDK",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",

    author="Harish Kumar",
    author_email="your_email@gmail.com",

    packages=find_packages(exclude=("tests*",)),
    include_package_data=True,

    python_requires=">=3.9",

    install_requires=[
        "fastapi",
        "pydantic",
        "python-dotenv",
        "pymongo",
        "qdrant-client",
        "requests"
    ],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
