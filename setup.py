import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="update-route53",
    version="0.0.1",
    author="Christopher Coakley",
    author_email="update-route53@tekabal.com",
    description="Updates route53 for a name and IP address.",
    install_requires=['boto3>=1.9.28'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ccoakley/update-route53",
    packages=setuptools.find_packages(exclude=['conf', 'docs', 'tests']),
    py_modules=['update_route53'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'update-route53 = update_route53:main_func'
        ]
    }
)
