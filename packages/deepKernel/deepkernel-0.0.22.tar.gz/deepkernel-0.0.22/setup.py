import setuptools

# Read README.md for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="deepKernel",  # Replace with your desired PyPI package name (must be unique)
    version="0.0.22",  # Initial version number
    author="pz",  # Replace with your name
    author_email="meichiyuan@pzeda.com",  # Replace with your email
    description="A simple example package",  # Short description
    long_description=long_description, # Use README.md as long description
    long_description_content_type="text/markdown", # Format of long description
    url="https://www.pzeda.com/CN",  # Replace with your package's URL (e.g., GitHub repo)
    packages=setuptools.find_packages(), # Automatically find package directories (will find zephyrzhong/)
    classifiers=[ # Package classifiers
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)", # Ensure this matches your LICENSE file
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6', # Specify compatible Python versions
    install_requires=[ # List dependencies here if any
        'pillow>=11.2.1',
        'numpy>=2.2.6',
    ],
)