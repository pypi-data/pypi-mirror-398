from pathlib import Path
from setuptools import find_namespace_packages, setup

# Load packages from requirements.txt
BASE_DIR = Path(__file__).parent
with open(Path(BASE_DIR, "requirements.txt"), "r") as file:
    required_packages = [ln.strip() for ln in file.readlines()]

# Define our package
setup(
    name="CloudApiRequest",
    version="1.3.0",
    author="天润-测试",
    author_email="wangwd@ti-net.com.cn",
    description="天润cloud接口测试库",
    url="https://www.ti-net.com.cn/",
    packages=find_namespace_packages(),
    python_requires=">=3.7",
    install_requires=[required_packages],
    license='MIT',
) 



#username = wangwdcloud
# password = Wangweida1995$
# python setup.py sdist bdist_wheel
# twine upload dist/*
# twine upload --repository pypi --config-file .pypirc dist/*
# 账号: __token__
# 密码:pypi-AgEIcHlwaS5vcmcCJDc3ZWVlZDc1LTZjN2QtNGZiZC04MDVhLTM4MjQ4NDgwMTk2MAACKlszLCI1OWUxNWIyOS03YzdjLTRjYjYtYTJhNi1iMGY0MjY5MzNlODEiXQAABiAqZJVp612sqOHGB1dj7ufFEdgNqYJnan8IsxzzrlaZ5Q
#PyPI recovery codes
#bd896b842f7d7a38
#b46a129ee113865d
#d03c7002ac60ae38
#18118dcb7d9ba37c
#1880c2535d548ffc
#a6faa2b59c6adebc
#c978c3071ea93a32
#d01a6198bf942d61


# username = wangwdcloud
# password = Showmethe1$
# python setup.py sdist bdist_wheel
# twine upload dist/*
# twine upload --repository testpypi --config-file .pypirc dist/*
# 账号: __token__
# 密码:pypi-AgENdGVzdC5weXBpLm9yZwIkNmMyOTg0NWEtZDg2Yi00OGVlLWJiZDAtNzAyZGU0Y2RlMWUyAAIqWzMsIjFhOGNjODUyLTkwNjItNDU5Yi1hNjQzLWI4MTI4YzlkZTYxMSJdAAAGIFu7HNytLTHb6caaWeQIX19QIufLfT4rEUxYMN-EgmI5
#testPyPI recovery codes
#e7d4638b0e6e38c0
#b8e69995b38c13e2
#9db436d2b3d1f20f
#5e312d3f97ee177e
#e3cc8debde6a47cc
#aed38c17471f4e45
#7798c75dabc853d6
#bc7fb28eaaa48a27