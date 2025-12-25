import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="auroradns-cli",
    version="0.3.5",
    author="Loek Geleijn",
    author_email="loek@pcextreme.nl",
    description="A simple CLI client for AuroraDNS",
    keywords="pcextreme auroradns auroradns-cli auroradns_cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/loekg/auroradns-cli",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["auroradns-cli=auroradns.cli:main"]},
    scripts=["auroradns/bin/auroradns-cli"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
    python_requires=">=3",
    install_requires=["apache-libcloud", "requests", "tldextract", "urllib3"],
)
