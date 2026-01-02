import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "cdk8s-plone",
    "version": "0.1.16",
    "description": "Provides a CMS Plone Backend and Frontend for Kubernetes with cdk8s",
    "license": "Apache-2.0",
    "url": "https://github.com/bluedynamics/cdk8s-plone.git",
    "long_description_content_type": "text/markdown",
    "author": "Jens W. Klein<jk@kleinundpartner.at>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/bluedynamics/cdk8s-plone.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "cdk8s_plone",
        "cdk8s_plone._jsii"
    ],
    "package_data": {
        "cdk8s_plone._jsii": [
            "cdk8s-plone@0.1.16.jsii.tgz"
        ],
        "cdk8s_plone": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "cdk8s-plus-30>=2.4.10, <3.0.0",
        "cdk8s>=2.70.37, <3.0.0",
        "constructs>=10.4.2, <11.0.0",
        "jsii>=1.122.0, <2.0.0",
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
