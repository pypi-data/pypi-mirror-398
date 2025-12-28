import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

install_requires = [

]

extras_require = {

}
setuptools.setup(
    # 包的分发名称，使用字母、数字、_、-
    name="matplotlib_cn",
    # 版本号, 版本号规范：https://www.python.org/dev/peps/pep-0440/
    version="1.0.4",
    # 作者名
    author="matplotlib_cn",
    # 作者邮箱
    author_email="matplotlib_cn@qq.com",
    # 包的简介描述
    description="matplotlib_cn",
    # 包的详细介绍(一般通过加载README.md)
    long_description=long_description,
    # 和上条命令配合使用，声明加载的是markdown文件
    long_description_content_type="text/markdown",
    # 项目开源地址
    url="https://github.com/Castlebin/matplotlib-cn",
    # 如果项目由多个文件组成，我们可以使用find_packages()自动发现所有包和子包，而不是手动列出每个包，在这种情况下，包列表将是example_pkg
    packages=setuptools.find_packages(),
    # 关于包的其他元数据(metadata)
    classifiers=[
        # 该软件包兼容性: Python 3.8
        "Programming Language :: Python :: 3.8",
        # 许可证开源信息
        "License :: OSI Approved :: Apache Software License",
        # 与操作系统无关
        "Operating System :: OS Independent",
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    include_package_data=True,
)
