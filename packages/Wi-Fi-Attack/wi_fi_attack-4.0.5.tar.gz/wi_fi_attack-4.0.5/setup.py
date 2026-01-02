from setuptools import setup, find_packages
from pathlib import Path

# Read files safely
this_dir = Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8")
requirements = (this_dir / "requirements.txt").read_text().splitlines()

setup(
    name="Wi-Fi-Attack",               # PyPI package name
    version="4.0.5",
    author="cyb2rS2c",
    url="https://github.com/cyb2rS2c/Wi-Fi_ATTACK",
    description="Wi-Fi attack toolkit for penetration testing (educational use only)",
    
    # Python package structure
    packages=find_packages(where="src"),  # Look for packages under `src/`
    package_dir={"": "src"},              # Directs setuptools to search for packages inside `src/`
    
    install_requires=requirements,        # Read dependencies from requirements.txt
    include_package_data=True,            # Includes any non-Python files specified in MANIFEST.in
    long_description=long_description,    # Long description from README
    long_description_content_type="text/markdown",
    license="MIT",
    
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX :: Linux",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Development Status :: 5 - Production/Stable",
    ],

    
    python_requires=">=3.6",  # Python version requirement

    entry_points={
        "console_scripts": [
            "wifi-cracker=wi_fi_attack.wifi_cracker:main"
        ]
    },
)
