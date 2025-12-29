from setuptools import setup, find_packages

setup(
    name='mns_common',
    version='1.5.5.4',
    # packages=["mns_common", "mns_common.api",
    #           "mns_common.api.akshare",
    #           "mns_common.api.em",
    #           "mns_common.api.ths",
    #
    #           "mns_common.db", 'mns_common.utils', 'mns_common.component'],
    packages=find_packages(),
    install_requires=[],  # 如果有依赖项，可以在这里列出
)
