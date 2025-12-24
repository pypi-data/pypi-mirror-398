from setuptools import setup, find_packages

setup(
    name="MTC-HandTracker",
    version="1.0.0",
    description="A professional, modular hand tracking library for robotics.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Majd Aburas (McMaster Technology Club)",
    author_email="aburasm@mcmaster.ca",
    url="https://github.com/BTech-Robotics-Club/Hand-Tracking",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "opencv-python",
        "mediapipe",
        "numpy",
        "pyyaml"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.8, <3.13',
)
