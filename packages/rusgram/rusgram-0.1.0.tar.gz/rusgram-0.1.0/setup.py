from setuptools import setup, find_packages


setup(
    name='rusgram',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['pymorphy3>=2.0.6'],
    author="Маг Ильяс DOMA (MagIlyasDOMA)",
    author_email='magilyas.doma.09@list.ru',
    url='https://github.com/MagIlyasDOMA/rusgram',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
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
    python_requires='>=3.6',
)
