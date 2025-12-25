from pip_setuptools import requirements, setup, find_packages, readme, clean

clean()
setup(
    name='git-clear-cache',
    version='0.1.0',
    author="Маг Ильяс DOMA",
    author_email='magilyas.doma.09@list.ru',
    install_requires=requirements(),
    packages=find_packages(),
    url='https://github.com/MagIlyasDOMA/git-clear-cache',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: 3 :: Only',
    ],
    entry_points={
        'console_scripts': [
            'git-clear-cache=git_clear_cache:main',
        ]
    }
)
