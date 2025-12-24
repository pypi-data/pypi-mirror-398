from setuptools import setup,find_packages

setup(
    name="noamath",
    version="0.0.8",
    author="Noah Edward Holmén",
    author_email="GanonBlasterTheGrey@gmail.com",
    description="A Math Library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["numpy"],
    python_requires=">=3.6",
    license="Source Available License (see LICENSE file)",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Free To Use But Restricted",
        "Operating System :: OS Independent",
    ],
    zip_safe=False
)
