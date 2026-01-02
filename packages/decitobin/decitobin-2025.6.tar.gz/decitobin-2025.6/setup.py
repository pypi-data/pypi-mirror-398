from setuptools import setup, find_packages

setup(
    name="decitobinary",
    version="1.0.0",
    description="A simple Decimal to Binary converter with GUI",
    author="Your Name",
    packages=find_packages(),  # tự động tìm thư mục có __init__.py
    python_requires=">=3.10",
    entry_points={
        "gui_scripts": [
            "decitobin = decitobin.__init__:decimal_to_binary"
        ]
    },
    url="https://github.com/Thailam12/decimal-to-binary",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)