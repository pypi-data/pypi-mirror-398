from setuptools import setup, find_packages
import codecs
import os

def readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='PyPetka-Script',
    version='4.0.0',  # Изменил на семантическое версионирование
    author='Chorelin',
    author_email='miheevila6@gmail.com',
    description='Русскоязычная библиотека Python с 150+ функциями для студентов и разработчиков. Упрощение работы с Python, математикой, шифрованием и алгоритмами.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/IlyaChaek/PyPetka-Script',
    packages=find_packages(),
    install_requires=[],  # Нет внешних зависимостей
    classifiers=[
        # Поддерживаемые версии Python
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        
        # Лицензия (поменял на MIT для PyPI)
        'License :: OSI Approved :: MIT License',
        
        # Операционные системы
        'Operating System :: OS Independent',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        
        # Статус разработки
        'Development Status :: 5 - Production/Stable',
        
        # Целевая аудитория
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        
        # Тематика
        'Topic :: Education',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Security :: Cryptography',
        'Topic :: Utilities',
        
        # Язык
        'Natural Language :: Russian',
    ],
    keywords=[
        'python', 
        'russian', 
        'education', 
        'library', 
        'students',
        'math', 
        'cryptography', 
        'algorithms',
        'pypetka',
        'programming',
        'development',
        'tools',
        'utilities'
    ],
    project_urls={
        'Homepage': 'https://github.com/IlyaChaek/PyPetka-Script',
        'Documentation': 'https://github.com/IlyaChaek/PyPetka-Script/blob/main/README.md',
        'Bug Reports': 'https://github.com/IlyaChaek/PyPetka-Script/issues',
        'Source Code': 'https://github.com/IlyaChaek/PyPetka-Script',
        'Changelog': 'https://github.com/IlyaChaek/PyPetka-Script/releases',
    },
    python_requires='>=3.6',  # Изменил с 2.8 на 3.6 (более реалистично)
    # Добавил дополнительные метаданные
    license='MIT',
    platforms=['any'],
    
    # Опциональные зависимости для разработки
    extras_require={
        'dev': [
            'twine>=4.0.0',
            'wheel>=0.40.0',
        ],
    },
    
    # Указываем что это чистый Python пакет
    zip_safe=True,

)