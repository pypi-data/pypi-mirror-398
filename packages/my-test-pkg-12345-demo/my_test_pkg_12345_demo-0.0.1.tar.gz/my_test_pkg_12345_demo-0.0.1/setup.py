from setuptools import setup, find_packages

setup(
    name="my-test-pkg-12345-demo",  # Use a unique random name
    version="0.0.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="A harmless test package to demonstrate PyPI publishing",
    packages=find_packages(),
    python_requires=">=3.6",
)

