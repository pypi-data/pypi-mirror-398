from setuptools import setup, find_packages

setup(
    name="shad-saber",   # اسم نهایی کتابخونه
    version="0.2.0",
    description="Shad integration library",
    author="saber",
    author_email="mesaber28@gmail.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "pycryptodome"
    ],
    license="MIT",
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)