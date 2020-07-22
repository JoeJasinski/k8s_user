from setuptools import setup, find_packages


setup(
    name="kubernetes-user",
    version="0.0.1",
    author="Joe Jasinski",
    description="A package for creating kubernetes users.",
    url="https://github.com/JoeJasinski/k8s_user",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        "kubernetes",
        "cryptography",
        "pyyaml",
    ],
    extras_require={
        "test":  ["pytest", "pytest-cov", "black", "coverage"],
    },
    entry_points={
        "console_scripts": [
            "k8s_user = k8s_user.__main__:main",
        ],
    }
)