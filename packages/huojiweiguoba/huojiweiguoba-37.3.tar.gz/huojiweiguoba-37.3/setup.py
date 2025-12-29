import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="huojiweiguoba",  # 模块名称
    version="37.3",  # 当前版本
    author="lbw",  # 作者
    author_email="819577544@qq.com",  # 作者邮箱
    description="人生有梦 各自精彩",  # 模块简介
    long_description=long_description,  # 模块详细介绍
    # long_description_content_type="text/markdown",  # 模块详细介绍格式
    url="https://github.com/ycyxycm/huojiweiguoba",  # 模块github地址
    packages=setuptools.find_packages(),  # 自动找到项目中导入的模块
    # 模块相关的元数据
    # classifiers=[
    #     "Programming Language :: Python :: 3",
    #     "License :: OSI Approved :: MIT License",
    #     "Operating System :: OS Independent",
    # ],
    # 依赖模块
    install_requires=[
        'peewee',
        'pymysql',
        'pandas',
        'python-dotenv',
        'openpyxl',
        'passlib'
    ],
    # python_requires='>=3',
)

#python3 setup.py sdist bdist_wheel
#twine upload dist/*