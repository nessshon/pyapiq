import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="apiq",
    version="0.0.9",
    author="nessshon",
    description="APIQ is a modern Python toolkit for building both synchronous and asynchronous API clients with clean, minimal code and full type safety.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nessshon/apiq",
    project_urls={
        "Source": "https://github.com/nessshon/apiq",
        "Issues": "https://github.com/nessshon/apiq/issues",
    },
    packages=setuptools.find_packages(include=["apiq", "apiq.*"]),
    package_data={"apiq": ["py.typed"]},
    python_requires=">=3.10",
    install_requires=[
        "aiohttp>=3.7.0,<=3.12.2",
        "aiolimiter~=1.2.1",
        "pydantic>=2.0,<3.0",
        "requests~=2.32.4",
        "ratelimiter~=1.2.0.post0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
        "Environment :: Console",
    ],
    keywords="api client async sync http aiohttp requests pydantic",
    license="MIT",
)
