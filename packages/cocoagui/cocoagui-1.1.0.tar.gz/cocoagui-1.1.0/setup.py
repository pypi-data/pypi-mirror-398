from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cocoagui",
    version="1.1.0",
    author="Camila 'Mocha' Rose",
    author_email="rblossom.dev@gmail.com",
    description="The simplest Python GUI library - create beautiful desktop applications with minimal code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mochacinno-dev/Graphica",
    project_urls={
        "Bug Tracker": "https://github.com/mochacinno-dev/Graphica/issues",
        "Documentation": "https://mochacinno-dev.github.io/Graphica",
        "Source Code": "https://github.com/mochacinno-dev/Graphica",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    packages=find_packages(),
    py_modules=["CocoaGUI"],
    python_requires=">=3.6",
    install_requires=[
        # tkinter comes with Python, no dependencies needed!
    ],
    keywords="gui tkinter ui desktop simple easy beginner-friendly",
    license="MIT",
    include_package_data=True,
)