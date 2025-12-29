from setuptools import setup, find_packages

setup(
    name="arprint",
    version="0.1.2", 
    author="youcef",
    author_email="youcef.dev0@gmail.com",
    description="A library to print and input Arabic text correctly in terminal with color support",
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/cymoussa/arprint",
    packages=find_packages(),
    install_requires=[
        'arabic-reshaper',
        'python-bidi',
    ],
    keywords=['arabic', 'terminal', 'print', 'input', 'bidi', 'reshaper', 'cybersecurity', 'arprint'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    python_requires='>=3.6',
)
