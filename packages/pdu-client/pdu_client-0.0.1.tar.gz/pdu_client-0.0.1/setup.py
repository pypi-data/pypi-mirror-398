from setuptools import setup, find_packages

setup(
    name="pdu_client",
    version="0.0.1",
    author="Larry Shen",
    author_email="larry.shen@nxp.com",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
    ],
    scripts=["pdu-client"],
)
