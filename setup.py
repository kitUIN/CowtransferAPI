import setuptools
from CowtransferAPI.__version__ import __version__
requirements = [
    requirement.strip() for requirement in open('requirements.txt', 'r', encoding='utf-8').readlines()
]

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="CowtransferAPI",
    version=__version__,
    author="kitUIN",
    author_email="kulujun@gmail.com",
    description="CowTransfer API for Python 3.6+ 适用于 Python 3.6+ 奶牛快穿API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kitUIN/CowtransferAPI",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ], install_requires=requirements,
    python_requires='>=3.6',
)
