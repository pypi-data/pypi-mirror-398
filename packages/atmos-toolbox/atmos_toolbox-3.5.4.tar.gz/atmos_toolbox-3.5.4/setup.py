import setuptools #导入setuptools打包工具

from os import path
this_directory = path.abspath(path.dirname(__file__))
long_description = None
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()
    
setuptools.setup(
    name="atmos_toolbox", 
    version="3.5.4",   
    author="Mingxi Zhang",   
    author_email="zhang.mingxi@outlook.com",    
    description="A python toolbox for data analysis in meteorology & atmospheric sciences",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
)