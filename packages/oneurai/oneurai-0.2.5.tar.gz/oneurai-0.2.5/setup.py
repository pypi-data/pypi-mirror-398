from setuptools import setup, find_packages

setup(
    name="oneurai",
    version="0.2.5",  # 👈 الإصدار الجديد
    author="MTMA",
    author_email="mtma.1@hotmail.com",
    description="A powerful AI client library for Oneurai MLOps platform",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://oneurai.com",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
    install_requires=[
        "requests",
        "torch",
        "tqdm",
        "colorama"  # ✅ تمت إضافتها
    ],
)