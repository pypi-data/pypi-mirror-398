from setuptools import setup, find_packages

setup(
    name="arprint",
    version="0.1.1",
    author="youcef",
    author_email="youcef.dev0@gmail.com",
    description="A simple library to print Arabic text correctly in terminal",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'arabic-reshaper',
        'python-bidi',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

