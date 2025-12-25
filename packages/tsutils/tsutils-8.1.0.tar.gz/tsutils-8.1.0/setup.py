import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tsutils",
    version="8.1.0",
    author="The Tsubotki Team",
    author_email="69992611+TsubakiBotPAD@users.noreply.github.com",
    license="MIT",
    description="A collection of helper commands for Red-DiscordBot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=[
        "backoff==1.10.0",
        "discord_menu>=0.16.13",
        "Red-DiscordBot>=3.5.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
