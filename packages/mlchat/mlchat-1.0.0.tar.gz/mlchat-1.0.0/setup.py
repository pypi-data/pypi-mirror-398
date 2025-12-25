import setuptools
import json

# 参考:https://www.jb51.net/article/202841.htm
# 打包需将此文件和MANIFEST.in文件置于mengling_tool包同目录
# 包中必须有__init__.py文件存在才能在pip时正常导入
# pip install --upgrade setuptools wheel -i https://pypi.douban.com/simple
# python setup.py sdist bdist_wheel
# pip install twine
# twine upload dist/*
'''
python setup.py sdist bdist_wheel
twine upload -u user -p password dist/*
'''

name = 'mlchat'

with open('../config.json', encoding='utf-8') as file:
    definfo, opmap = json.loads(file.read())
setuptools.setup(
    name=name,
    packages=setuptools.find_packages(),
    **{**definfo, **opmap[name]}
)
