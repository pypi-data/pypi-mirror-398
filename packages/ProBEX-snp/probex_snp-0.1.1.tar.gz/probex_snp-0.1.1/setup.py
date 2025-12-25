from setuptools import setup, find_packages
classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
setup(
    name='ProBEX-snp',
    version='0.1.1',
    author='Shreya Sharma, PhD student @IITR',
    author_email='shreya_s@bt.iitr.ac.in',
    description='A tool for SNP-based Poisson binding analysis on SNP-bind-n-seq sequencing data',
    license='MIT',
    url='https://github.com/Shreya-droid/SNPoiss_bind_n_seq',
    packages=find_packages(),
    install_requires=['pandas>=1.3.5',
        'numpy>=1.21.6',
        'scikit-learn>=1.0.2',
        "scipy>=1.7.3",
        "matplotlib",
        "seaborn",
        "openpyxl",
        "adjustText",
        "jinja2",
        "pylatex",
        "psutil"],

    entry_points={
        'console_scripts': [
            'ProBEX = ProBEX.run_all:main',
        ],
    },
    include_package_data=True,
)
