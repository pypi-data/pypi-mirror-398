from setuptools import setup, find_packages
import os

# read README for PyPI long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="crystalwindow",
    version="5.7",  # Force metadata refresh
    packages=find_packages(include=["crystalwindow", "crystalwindow.*"]),

    include_package_data=True,  # include package_data files
    package_data={
        "crystalwindow": [
            "docs/*.md",
        ],
    },

    author="CrystalBallyHereXD",
    author_email="mavilla.519@gmail.com",

    description="A Tkinter powered window + GUI toolkit made by Crystal (ME)! Easier apps, smoother UI and all-in-one helpers!, Gui, Buttons, FileHelper, Sprites, Animations, Colors, Math, Gravity, Camera, 3D and more!",
    long_description=long_description,
    long_description_content_type="text/markdown",

    python_requires=">=3.6",

    url="https://pypi.org/project/crystalwindow/",

    project_urls={
        "Homepage": "https://github.com/yourusername/crystalwindow",
        "YouTube": "https://www.Youtube.com/@CrystalBallyHereXD",
        "PiWheels": "https://www.piwheels.org/project/crystalwindow/",
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: User Interfaces",
        "License :: OSI Approved :: MIT License",
    ],

    keywords="tkinter gui window toolkit easy crystalwindow crystal cw player moveable easygui python py file math gravity hex color",

    install_requires=[
        "requests",
        "packaging",
        "pillow"
    ],

)
