from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("VERSION", "r", encoding="utf-8") as f:
    version = f.read()

setup(
    name='talisman-dm',
    version=version,
    description='Talisman Document Model python implementation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://gitlab.at.ispras.ru/talisman/core/talisman-tdm',
    author='ISPRAS MODIS NLP team',
    author_email='modis@ispras.ru',
    maintainer='Vladimir Mayorov',
    maintainer_email='vmayorov@ispras.ru',
    packages=find_packages(include=['tdm', 'tdm.*']),
    install_requires=['pydantic~=2.5', 'typing-extensions>=4.0.1', 'immutabledict>=2.2.4,<3'],
    data_files=[('', ['VERSION'])],
    python_requires='>=3.7',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License'
    ]
)
