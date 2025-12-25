from setuptools import setup, find_packages

setup(
    name="qmatrix",
    version="1.2.8",
    description="A high-performance, aesthetically pleasing Matrix rain TUI with horror elements.",
    author="Rex Ackermann",
    author_email="rex@example.com",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/rexackermann/qmatrix",
    py_modules=["qmatrix", "constants"],
    install_requires=[
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "qmatrix=qmatrix:main_wrapper",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)
