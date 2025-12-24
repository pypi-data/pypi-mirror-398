import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "gammarers.aws-cdk-errors",
    "version": "1.2.45",
    "description": "@gammarers/aws-cdk-errors",
    "license": "Apache-2.0",
    "url": "https://github.com/gammarers/aws-cdk-errors.git",
    "long_description_content_type": "text/markdown",
    "author": "yicr<yicr@users.noreply.github.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/gammarers/aws-cdk-errors.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "gammarers.aws_cdk_errors",
        "gammarers.aws_cdk_errors._jsii"
    ],
    "package_data": {
        "gammarers.aws_cdk_errors._jsii": [
            "aws-cdk-errors@1.2.45.jsii.tgz"
        ],
        "gammarers.aws_cdk_errors": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "jsii>=1.121.0, <2.0.0",
        "publication>=0.0.3",
        "typeguard==2.13.3"
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
