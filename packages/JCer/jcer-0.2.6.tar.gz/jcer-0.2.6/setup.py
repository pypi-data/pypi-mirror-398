import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="JCer",
    version="0.2.6",
    author="YANGRENRUIYRR",
    author_email="yangrenruiyrr@yeah.net",
    description="A package for remote control with screen capture and input handling",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YANGRENRUIYRR/JCer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires='>=3.6',
    install_requires=[
        "blinker>=1.5",
        "click>=7.1.2",
        "colorama>=0.4.5",
        "Flask>=1.1.4",
        "itsdangerous>=1.1.0",
        "Jinja2>=2.11.3",
        "MarkupSafe>=2.0.1",
        "pyotp>=2.7.0",
        "waitress>=2.0.0",
        "Werkzeug>=1.0.1",
        "certifi>=2025.4.26",
        "charset-normalizer>=2.0.0",
        "idna>=3.10",
        "ipaddress>=1.0.23",
        "mss>=7.0.1",
        "Pillow>=8.4.0",
        "pynput>=1.8.1",
        "requests>=2.27.1",
        "six>=1.17.0",
        "urllib3>=1.26.20",
    ],
    extras_require={
        ":python_version == '3.6'": [
            "dataclasses>=0.8",
            "importlib-metadata>=4.8.3",
            "typing-extensions>=4.1.1",
            "zipp>=3.6.0",
        ],
        ":python_version == '3.7'": [
            "importlib-metadata>=4.8.3",
            "typing-extensions>=4.1.1",
            "zipp>=3.6.0",
        ],
        ":python_version == '3.8'": [
            "importlib-metadata>=4.8.3",
            "typing-extensions>=4.1.1",
            "zipp>=3.6.0",
        ],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "jcer-server = JCer.server:main",
            "jcer-client = JCer.client:main",
        ],
    },
)