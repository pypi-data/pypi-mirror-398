from setuptools import setup, find_packages

setup(
    name='itssussh',
    version='3.0.0',
    description='connect SVPS WebSocket Client',
    author='Eternals',
    packages=find_packages(),
    install_requires=[
        'websocket-client',
    ],
    entry_points={
        'console_scripts': [
            'sussh=sussh.core:main', 
        ],
    },
)

