import pathlib
from setuptools import find_packages, setup
from setuptools.dist import Distribution

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

ext_modules = []


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""
    def has_ext_modules(self):
        return True


setup(
    name='payme_pkg',  # Must use underscore for PyPI filename compatibility
    version='3.3.1',
    license='MIT',
    author="Muhammadali Akbarov",
    author_email='muhammadali17abc@gmail.com',
    packages=find_packages(exclude=['payme_source', 'payme_source.*', 'build', 'scripts']),
    url='https://github.com/Muhammadali-Akbarov/payme-pkg',
    keywords='paymeuz paycomuz payme-merchant merchant-api subscribe-api payme-pkg payme-api',
    install_requires=[
        'requests==2.*',
        "dataclasses==0.*;python_version<'3.7'",
        'djangorestframework==3.*',
        'environs>=9.0.0',
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    package_data={
        '': ['*.so', '*.pyd', '*.dll', '*.dylib'],
        'payme': ['*.so', '*.pyd', '*.dll', '*.dylib'],
    },
    ext_modules=ext_modules,
    distclass=BinaryDistribution,
    zip_safe=False,
)
