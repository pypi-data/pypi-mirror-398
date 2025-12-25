from setuptools import setup

setup(
    name="sageodata_db",
    packages=["sageodata_db"],
    package_data={"sageodata_db": ["queries/*.sql"]},
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    description="SA Geodata database querying tool/wrapper/library",
    long_description=open("README.md", mode="r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dew-waterscience/sageodata_db",
    author="DEW Water Science (Kent Inverarity)",
    author_email="groundwater@sa.gov.au",
    license="All rights reserved",
    classifiers=("Programming Language :: Python :: 3",),
    keywords="science",
    install_requires=(
        "oracledb",
        "pandas",
        "python-sa-gwdata",
        "sqlparse",
        "pillow",
        "pyautogui",
    ),
)
