from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='tbot223-core',
    version='2.0.8',
    description='A core utility package for tbot223 projects.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='tbot223',
    author_email='tbotxyz@gmail.com',
    url='https://github.com/Tbot223/Core',
    install_requires=[],
    packages=find_packages(include=['tbot223_core', 'tbot223_core.*']),
    keywords=['pypi', 'package', 'utilities', 'python', 'tbot223'],
    python_requires='>=3.10',
    classifiers=[
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: Apache Software License',
    ],
)
