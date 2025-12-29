from setuptools import setup,find_packages
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ffseval",
    version="0.5.4",
    description="Evaluation of fitness for service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shinsuke Sakai",
    author_email='sakaishin0321@gmail.com',
    url='https://github.com/ShinsukeSakai0321/FFS',
    packages=find_packages(),
    install_requires=[
        "numpy==1.26.4",
        "scikit-learn",
        "matplotlib",
        "Kriging",
        "typing",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    package_data={
        'FFSeval': ['data/*.csv'],  # パッケージ名とファイルパターン
    },
    include_package_data=True,
    python_requires='>=3.6',
)