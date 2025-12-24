from setuptools import setup, find_packages

setup(
    name='Jarvis_STT_byArsh',
    version='0.1',
    author='Mohammad Ammar Shaikh {Arsh}',
    author_email='ammarshaikh817716@gmail.com',
    description='This Is STT Package Created By Arsh',
    packages=find_packages(),  # Corrected here
    install_requires=[          # Corrected here
        'selenium',
        'webdriver_manager'
    ],
    python_requires='>=3.6'
)