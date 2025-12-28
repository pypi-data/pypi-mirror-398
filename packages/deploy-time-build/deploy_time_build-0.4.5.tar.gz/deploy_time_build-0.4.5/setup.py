import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "deploy-time-build",
    "version": "0.4.5",
    "description": "Build during CDK deployment.",
    "license": "MIT",
    "url": "https://github.com/tmokmss/deploy-time-build.git",
    "long_description_content_type": "text/markdown",
    "author": "tmokmss<tomookam@live.jp>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/tmokmss/deploy-time-build.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "deploy_time_build",
        "deploy_time_build._jsii"
    ],
    "package_data": {
        "deploy_time_build._jsii": [
            "deploy-time-build@0.4.5.jsii.tgz"
        ],
        "deploy_time_build": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.38.0, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
        "jsii>=1.114.1, <2.0.0",
        "publication>=0.0.3",
        "typeguard>=2.13.3,<4.3.0"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
