"""
Salesforce Toolkit - DEPRECATED - Please use 'kinetic-core' instead.
"""

from setuptools import setup

setup(
    name="salesforce-toolkit",
    version="1.1.1",
    author="Antonio Trento",
    author_email="info@antoniotrento.net",
    description="DEPRECATED - Please use 'kinetic-core' instead.",
    long_description="This package has been deprecated. Please use 'kinetic-core' instead.",
    long_description_content_type="text/plain",
    url="https://github.com/antonio-backend-projects/salesforce-toolkit",
    packages=["salesforce_toolkit"],
    classifiers=[
        "Development Status :: 7 - Inactive",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
    install_requires=["kinetic-core"],
    zip_safe=False,
)
