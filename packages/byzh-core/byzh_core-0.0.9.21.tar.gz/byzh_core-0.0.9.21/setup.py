from setuptools import setup, find_namespace_packages
import byzh
setup(
    name='byzh-core',
    version=byzh.__version__,
    author="byzh_rc",
    description="byzh-core是byzh系列的核心库，包含了一些常用的工具函数和类。",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    packages=find_namespace_packages(include=["byzh.*"]),
    install_requires=[
        'wcwidth',
    ],
    entry_points={
        "console_scripts": [
            "b_zip=byzh.core.__main__:b_zip", # b_zip 路径
            "b_dirtree=byzh.core.__main__:b_dirtree", # b_dirtree 路径
        ]
    },
)
