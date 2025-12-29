from setuptools import find_packages, setup

setup(
    name='talos_python3',
    version='3.1.3',
    author='huyumei',
    author_email='huyumei@xiaomi.com',
    maintainer='fangchengjin',
    maintainer_email='fangchengjin@xiaomi.com',
    description='talos python3 sdk',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'cffi',
        'python-snappy==0.6.1',
        'atomic',
        'dnspython',
        'requests',
        'IPy'
    ],
)

