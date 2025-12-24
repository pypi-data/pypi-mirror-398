from setuptools import setup, find_namespace_packages

setup(
    name="basalam.hermes-messaging-sdk",
    author="Hasan Golparvar",
    author_email="h.golparvar1383@gmail.com",
    description="Python SDK to integrate and interact with Hermes Marketing Automation Platform",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/basalam/hermes-messaging-sdk",
    packages=find_namespace_packages(where='src', include=['basalam.hermes_messaging_sdk']),
    package_dir={'': 'src'},
    namespace_packages=["basalam"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        "httpx>=0.24.0",
    ],
    keywords="hermes marketing automation messaging sdk api client",
)
