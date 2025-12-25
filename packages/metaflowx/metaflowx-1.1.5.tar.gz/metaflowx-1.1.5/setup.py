from setuptools import setup, find_packages

setup(
    name="metaflowx",
    version="1.1.5",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "numpy",
        "scipy",
        "pandas",
        "autograd",
        "statsmodels",
        "pmdarima",
        "jinja2",
        "tqdm"
    ],
    author="Suchana Chakraborty",
    description="Numerical optimization toolkit — BFGS, CG, Newton, Steepest Descent, and more.",
    python_requires=">=3.7",
)