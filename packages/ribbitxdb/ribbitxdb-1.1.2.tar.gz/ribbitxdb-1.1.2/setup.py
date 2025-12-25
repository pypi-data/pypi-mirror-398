from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ribbitxdb",
    version="1.1.2",
    author="RibbitX Team",
    author_email="contact@ribbitx.com",
    description="Production-ready enterprise database with 100% SQL support, client-server architecture, TLS encryption, connection pooling, and advanced features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://ribbitx.com",
    package_dir={'': 'lib'},
    packages=find_packages(where='lib'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
        "server": [
            # Server mode has no extra dependencies - uses stdlib only!
        ],
    },
    entry_points={
        'console_scripts': [
            'ribbitxdb-server=ribbitxdb.server.cli:main',
        ],
    },
    keywords="database, production, stable, sql, client-server, tls, authentication, replication, connection-pool, blake2, lzma, compression, security, lightweight, embedded",
    project_urls={
        "Homepage": "https://ribbitx.com",
        "Bug Reports": "https://lab.ribbitx.com/report",
        "Source": "https://github.com/ribbitxdb/ribbitxdb",
        "Documentation": "https://docs.ribbitx.com",
    },
)
