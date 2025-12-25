from setuptools import setup

__version__ = "1.0.0rc11"

with open("README.md", "r") as readme_file, open("CHANGELOG.md", "r") as changelog_file:
    long_description = f"{readme_file.read()}\n\n{changelog_file.read()}"

packages = ["sharepoint"]

setup(
    name="sharepoint_v1_api",
    version=__version__,
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Aske Bluhme Klok",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="Sharepoint",
    packages=packages,
    install_requires=["requests>=2.32.2", "requests-ntlm>=1.3.0"],
    python_requires=">=3.9"
)
