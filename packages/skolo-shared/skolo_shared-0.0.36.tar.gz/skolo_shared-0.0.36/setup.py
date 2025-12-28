from setuptools import setup, find_packages

# Read the README file for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="skolo-shared",
    version="0.0.36",
    description="Shared SQLAlchemy models for School Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Skolo Cloud",
    author_email="contact@skolo.cloud",
    url="https://github.com/skolo-cloud/skolo-shared",
    project_urls={
        "Source": "https://github.com/skolo-cloud/skolo-shared",
        "Issues": "https://github.com/skolo-cloud/skolo-shared/issues",
        "Changelog": "https://github.com/skolo-cloud/skolo-shared/blob/main/CHANGES.md",
    },
    packages=find_packages(exclude=("tests", "examples")),
    install_requires=[
        "SQLAlchemy>=2.0.0",
        "psycopg2-binary>=2.9.0"
    ],
    python_requires=">=3.10",
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="sqlalchemy orm school-management database models",
)