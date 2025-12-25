from setuptools import setup, find_packages

setup(
    name='cd3_connector',
    version='0.3.1',
    description='Biblioteca para facilitar conexão e comunicação com o Market Data Cedro',
    author='Cedro Technologies',
    author_email='cd3connector@cedrotech.com',
    packages=find_packages(),  # Isso deve incluir seu pacote cd3_connector
    package_data={
        'cd3_connector': ['*.pyc'],  # Inclui todos os arquivos .pyc do pacote
    },
    include_package_data=True,  # Garante que os arquivos listados em MANIFEST.in sejam incluídos
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
)
