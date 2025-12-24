from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="polerisk",
    version="1.1.0",
    author="Kyle T. Jones",
    author_email="kyletjones@gmail.com",
    description="Predictive utility pole failure analysis and maintenance optimization platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kylejones200/polerisk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Utilities",
        "Intended Audience :: Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Engineering :: Infrastructure",
        "Topic :: Engineering :: Risk Management",
        "Topic :: Utilities :: Power Management",
        "Topic :: Business :: Operations Research",
    ],
    python_requires='>=3.12',
    install_requires=[
        'numpy>=1.20.0',
        'pandas>=1.3.0',
        'matplotlib>=3.4.0',
        'scipy>=1.7.0',
        'netCDF4>=1.5.0',
        'cartopy>=0.19.0',
        'seaborn>=0.11.0',
        'python-dateutil>=2.8.2',
        'scikit-learn>=1.0.0',
        'joblib>=1.0.0',
        'jinja2>=3.0.0',
        'signalplot>=0.1.2',
        'folium>=0.12.0',
    ],
)
