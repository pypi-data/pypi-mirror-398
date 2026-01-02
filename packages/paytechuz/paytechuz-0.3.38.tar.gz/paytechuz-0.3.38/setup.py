"""Setup script for PayTechUZ package."""

import pathlib
from setuptools import setup
from setuptools.dist import Distribution

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""
    def has_ext_modules(self):
        return True

setup(
    name='paytechuz',
    version='0.3.38',
    license='MIT',
    author="Muhammadali Akbarov",
    author_email='muhammadali17abc@gmail.com',
    description="Unified Python package for Uzbekistan payment gateways (Payme, Click, Uzum, Paynet)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Muhammadali-Akbarov/paytechuz',

    packages=[
        'paytechuz',
        'paytechuz.core',
        'paytechuz.gateways',
        'paytechuz.gateways.payme',
        'paytechuz.gateways.click',
        'paytechuz.gateways.uzum',
        'paytechuz.gateways.paynet',
        'paytechuz.integrations',
        'paytechuz.integrations.django',
        'paytechuz.integrations.django.migrations',
        'paytechuz.integrations.fastapi',
    ],
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        '': ['*.so', '*.pyd', '*.dll', '*.dylib'],
    },
    python_requires='>=3.6',

    install_requires=[
        'requests>=2.0,<3.0',
        "dataclasses>=0.6,<1.0; python_version<'3.7'",
        'environs',
    ],

    extras_require={
        'django': [
            'django>=3.0,<6.0'
        ],
        'fastapi': [
            'fastapi>=0.68.0,<1.0.0',
            'sqlalchemy>=1.4,<3.0',
            'httpx>=0.20,<1.0',
            'python-multipart==0.0.20',
            'pydantic>=1.8,<2.0',
        ],
        'flask': [
            'flask>=2.0,<3.0',
            'flask-sqlalchemy>=2.5,<3.0',
        ],
    },



    keywords=[
        "paytechuz", "payme", "click", "uzum", "paynet", "uzbekistan", "payment", "gateway",
        "payment-gateway", "payment-processing", "django", "flask", "fastapi"
    ],

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    distclass=BinaryDistribution,
    zip_safe=False,
)
