from setuptools import setup, find_packages

setup(
    name="mp4fixer",
    version="0.2.0",
    packages=find_packages(),
    entry_points = {
        "console_scripts": ["mp4fixer = mp4fixer.fix:main","mp4analyzer = mp4fixer.mp4analyzer:main"]
    },
    install_requires=[
        "argparse",
        "colorama",
        "lolpython",
        "pyfiglet",
        "signal"
    ],
    include_package_data=True,
    package_data={"mp4fixer": ["mf","fp"]},
    author="Abdul Moeez",
    description="A powerful mp4 files fixer and analyzer that fix 70% to 90% of mp4 files",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/mp4fixer",
    python_requires=">=3.7",
)
