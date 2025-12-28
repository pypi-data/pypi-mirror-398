from setuptools import setup, find_packages

setup(
    name="pyOS-kernel",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "pyos": ["boot/*.asm"],
    },
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "pyos=pyos.cli:main",
        ],
    },
)
