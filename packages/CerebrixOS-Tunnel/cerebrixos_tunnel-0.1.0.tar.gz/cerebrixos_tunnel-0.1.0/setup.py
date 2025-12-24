from setuptools import setup, find_packages

setup(
    name='CerebrixOS-Tunnel',
    version='0.1.0',
    author='ockhamlabs',
    author_email='hello@ockhamlabs.ai',
    description='CerebrixOS Tunnel enables secure zero-trust access to private services via OpenZiti edge tunneling.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cerebrixos-tunnel = cerebrixos_tunnel.main:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    include_package_data=True,
  
)