from setuptools import setup, find_packages
import os


setup(
    name="bestv_common_util",
    version="0.3.9",
    author="liu.qingchen",
    author_email="liu.qingchen@bestv.com.cn",
    description="Bestv Common Util",
    long_description_content_type="text/markdown",
    long_description=open('README.md', encoding="UTF8").read(),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=['requests', 'pandas'],
    keywords=['bestv_common_util', 'nacos', 'kms'],
    # data_files=[('cut_video', ['cut_video/clip_to_erase.json'])],
    entry_points={
        'console_scripts': [

        ]
    },
    license="MIT",
    url="",
    scripts=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows"
    ]
)