from pip_setuptools import setup, find_packages, clean

clean()
setup(
    name='django-admin-panel-link',
    version='1.0.1',
    author='Маг Ильяс DOMA (MagIlyasDOMA)',
    author_email='magilyas.doma.09@list.ru',
    url='https://github.com/MagIlyasDOMA/django-admin-link',
    packages=find_packages(exclude=['app_test']),
    include_package_data=True,
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Natural Language :: Russian',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Framework :: Django',
        'Framework :: Django :: 5.2',
        'Framework :: Django :: 6.0',
    ]
)
