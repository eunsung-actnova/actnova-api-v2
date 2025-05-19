from setuptools import setup, find_packages

setup(
    name="actverse_common",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pika>=1.2.0",
    ],
    description="Actverse API 공통 유틸리티 라이브러리",
)