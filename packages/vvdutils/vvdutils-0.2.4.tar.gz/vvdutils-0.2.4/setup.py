from setuptools import find_packages, setup
import os

str_version = '0.2.4'

# 自动包含所有子包
packages = find_packages()

# 数据文件路径
assets_path = os.path.join('vvdutils', 'assets')
data_files = [
    (assets_path, [os.path.join(assets_path, f) for f in os.listdir(assets_path) 
     if f.endswith('.json') or f.endswith('.jpg')])
]

if __name__ == '__main__':
    # try to import
    # pyzmq scikit-image onnxruntime rasterio pyproj line_profile  func_timeout pypinyin pytest

    setup(
        name='vvdutils',
        version=str_version,
        description='Commonly used function library by VVD',
        url='https://github.com/zywvvd/utils_vvd',
        author='zywvvd',
        author_email='zywvvd@mail.ustc.edu.cn',
        license='MIT',
        packages=packages,
        data_files=data_files,
        include_package_data=True,
        zip_safe=False,
        install_requires= [
            'numpy>=2.2', 
            'opencv-python>=4.12', 
            'scikit-learn>=1.8.0', 
            'pathlib2', 
            'tqdm', 
            'matplotlib', 
            'pandas', 
            'flask', 
            'shapely', 
            'loguru',
            'rasterio',
            'scikit-image',
            'numba',
            'pygltflib'
            ],
        python_requires='>=3.14')