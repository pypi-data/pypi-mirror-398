from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bit_audio_tag",  # 包名称
    version="1.0.0",  # 版本号
    author="Bitliker",  # 作者名
    author_email="gongpengming@163.com",  # 作者邮箱
    description="A package for audio tagging",  # 简短描述
    long_description=long_description,  # 详细描述
    long_description_content_type="text/markdown",  # 描述格式
    url="https://github.com/Bitliker/audio_tag",  # 项目地址
    packages=find_packages(),  # python setup.py sdist bdist_wheel
    classifiers=[  # 分类器
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",  # Python 版本要求
    install_requires=[
        "mutagen>=1.47.0",
        # "pandas>=1.1.0",
    ],
)
