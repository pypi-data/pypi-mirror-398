from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    description = f.read()

setup(
    name='sec_eagle',
    version='0.1.300',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pandas',
        'beautifulsoup4',
        'numpy',
        'lxml'
    ],
    python_requires='>=3.6',
    description='A Python package for parsing SEC data',
    author='Bryce Gerber',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    long_description=description,
    long_description_content_type="text/markdown"
)