from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="dshellInterpreter",
    version="0.2.21.7",
    author="Chronos",
    author_email="vagabonwalybi@gmail.com",
    description="A Discord bot interpreter for creating custom commands and automations.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BOXERRMD/Dshell_Interpreter",
    packages=["Dshell",
              "Dshell._DshellInterpreteur",
              "Dshell._DshellTokenizer",
              "Dshell._DshellParser",
              "Dshell.DISCORD_COMMANDS",
              "Dshell.DISCORD_COMMANDS.utils"],
    install_requires=["py-cord==2.6.1", "requests", "pycordviews"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    license="MIT",
    keywords="discord bot interpreter automation commands",
    project_urls={
        "Bug Tracker": "https://github.com/BOXERRMD/Dshell_Interpreter/issues",
        "Source": "https://github.com/BOXERRMD/Dshell_Interpreter"}

)
