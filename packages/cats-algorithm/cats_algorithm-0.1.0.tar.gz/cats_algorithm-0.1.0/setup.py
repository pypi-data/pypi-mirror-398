from setuptools import setup, find_packages

with open('docs/user_guide.md', 'r') as f:
    long_description = f.read()

setup(
    name='cats_algorithm',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy',  # Add if your objective functions need it (optional)
    ],
    extras_require={
        'tuning': ['optuna'],
    },
    author='Your Name',
    author_email='your@email.com',
    description='CATS: A matrix-based metaheuristic optimizer',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/cats_algorithm',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)