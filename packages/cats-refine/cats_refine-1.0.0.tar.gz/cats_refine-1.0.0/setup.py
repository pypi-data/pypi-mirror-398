from setuptools import setup, find_packages

setup(
    name='cats_refine',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'reportlab',
        'openpyxl',
    ],
    author='Louati Mahdi',
    description='A matrix-based metaheuristic optimizer with automated reporting.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/cats_refine', # Change to your link
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)