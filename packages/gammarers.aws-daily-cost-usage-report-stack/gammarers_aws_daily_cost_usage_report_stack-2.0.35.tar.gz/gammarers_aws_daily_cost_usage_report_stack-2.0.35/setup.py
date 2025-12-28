import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "gammarers.aws-daily-cost-usage-report-stack",
    "version": "2.0.35",
    "description": "Cost & Usage Reports",
    "license": "Apache-2.0",
    "url": "https://github.com/gammarers/aws-daily-cost-usage-report-stack.git",
    "long_description_content_type": "text/markdown",
    "author": "yicr<yicr@users.noreply.github.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/gammarers/aws-daily-cost-usage-report-stack.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "gammarers.aws_daily_cost_usage_report-stack",
        "gammarers.aws_daily_cost_usage_report-stack._jsii"
    ],
    "package_data": {
        "gammarers.aws_daily_cost_usage_report-stack._jsii": [
            "aws-daily-cost-usage-report-stack@2.0.35.jsii.tgz"
        ],
        "gammarers.aws_daily_cost_usage_report-stack": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.189.1, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
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
