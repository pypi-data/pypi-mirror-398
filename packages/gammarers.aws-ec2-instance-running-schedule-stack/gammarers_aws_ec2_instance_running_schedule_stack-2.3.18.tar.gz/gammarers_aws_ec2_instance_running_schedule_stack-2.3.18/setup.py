import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "gammarers.aws-ec2-instance-running-schedule-stack",
    "version": "2.3.18",
    "description": "AWS EC2 Instance Running Scheduler",
    "license": "Apache-2.0",
    "url": "https://github.com/gammarers/aws-ec2-instance-running-schedule-stack.git",
    "long_description_content_type": "text/markdown",
    "author": "yicr<yicr@users.noreply.github.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/gammarers/aws-ec2-instance-running-schedule-stack.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "gammarers.aws_ec2_instance_running_schedule_stack",
        "gammarers.aws_ec2_instance_running_schedule_stack._jsii"
    ],
    "package_data": {
        "gammarers.aws_ec2_instance_running_schedule_stack._jsii": [
            "aws-ec2-instance-running-schedule-stack@2.3.18.jsii.tgz"
        ],
        "gammarers.aws_ec2_instance_running_schedule_stack": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.120.0, <3.0.0",
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
