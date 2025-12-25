from setuptools import setup, find_packages

setup(
    name="supercore",
    version="2.1",
    author="@NacDevs",
    author_email="yuvrajmodz@gmail.com",
    description="Simple CLI to create supervisor processes easily",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yuvrajmodz/SuperCore",
    packages=find_packages(),
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'supercore=supercore.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)