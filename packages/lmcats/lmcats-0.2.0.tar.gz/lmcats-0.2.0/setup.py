from setuptools import setup, find_packages

with open('docs/user_guide.md', 'r') as f:
    long_description = f.read()

setup(
    name='lmcats',
    version='0.2.0',
    packages=find_packages(),
    install_requires=['numpy', 'reportlab'],
    extras_require={
        'tuning': ['optuna'],
        'excel': ['openpyxl'],
    },
    author='Louati Mahdi',
    author_email='louatimahdi390@gmail.com',
    description='lmcats: Advanced metaheuristic optimization with reporting',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mahdi123-tech',  # Update with your repo
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)