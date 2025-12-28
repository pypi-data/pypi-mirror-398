from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="cats_presentation-rendering",    # PyPI name (with hyphens)
    version="0.1.0",
    author="Louati Mahdi",
    author_email="louatimahdi390@gmail.com",
    description="Display an embedded cat presentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/cats_presentation-rendering",
    packages=find_packages(),                # Finds `cats_presentation_rendering`
    install_requires=[
        "ipython>=7.0.0",                    # Required for Jupyter display
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics",
    ],
    python_requires=">=3.6",
    keywords="cats presentation document embed",
)