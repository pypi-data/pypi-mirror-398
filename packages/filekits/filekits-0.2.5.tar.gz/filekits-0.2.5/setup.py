from setuptools import setup, find_packages

short_description = 'Filekits - Python文件处理工具包，提供文件读写、网络下载、文件夹操作、图片处理等常用功能'

# 读取README文件
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = short_description

# 读取requirements.txt文件
try:
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        install_requires = [line.strip() for line in f if line.strip() and not line.startswith('#')]
except FileNotFoundError:
    install_requires = []

setup(  
    name='filekits',
    version='0.2.5',
    packages=find_packages(),
    install_requires=install_requires,
    author='tinycen',
    author_email='sky_ruocen@qq.com',
    description=short_description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/tinycen/filekits',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    include_package_data=True,
    zip_safe=False,
)
