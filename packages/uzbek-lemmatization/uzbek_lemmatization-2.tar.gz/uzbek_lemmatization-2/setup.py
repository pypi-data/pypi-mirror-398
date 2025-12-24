from setuptools import setup, find_packages

setup(
    name='uzbek_lemmatization',
    version='2',
    authors='Maksud Sharipov, Dasturbek',
    author_email='sobirovogabek0409@gmail.com',
    description='Finds the lemma of Uzbek words',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ddasturbek/UzbekLemma',
    packages=find_packages(),
    package_data={
        'uzbek_lemmatization': ['suzlar/*']
    },
    include_package_data=True,
    install_requires=[

    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
