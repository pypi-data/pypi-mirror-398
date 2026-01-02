from setuptools import setup, find_packages
import os

setup(
    name="tunnelify",
    version="0.3.2",
    packages=find_packages(),
    include_package_data=True,
    author="Yusuf YILDIRIM",
    author_email="yusuf@tachion.tech",
    description="A simple package for easily creating Cloudflare or Localtunnel tunnels.",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/MYusufY/tunnelify",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: System :: Networking",
    ],
    python_requires=">=3.6",
)