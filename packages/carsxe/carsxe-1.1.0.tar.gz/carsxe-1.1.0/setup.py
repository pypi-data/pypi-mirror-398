from setuptools import setup, find_packages

setup(
    name='carsxe',
    version='0.2.2',
    author='CarsXE',
    author_email='developer@carsxe.com',
    description='CarsXE API PIP Package',
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'requests',
        'urllib3',
    ],
    python_requires=">=3.7",
    include_package_data=True,
)
