from setuptools import setup, find_packages


def readme():
    with open('README.md', 'r') as f:
        return f.read()


setup(
    name='pioneergame',
    version='0.0.26',
    author='chebur5581',
    author_email='chebur5581@gmail.com',
    description='Simple Pygame wrap for small kids',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/chebur5581/pioneergame',
    packages=find_packages(),
    install_requires=['pygame>=2.6.0', 'setuptools'],
    classifiers=[
        'Programming Language :: Python :: 3.11',
        'Operating System :: Microsoft :: Windows'
    ],
    keywords='Games Pygame kis Learning pioneergame',
    project_urls={
        'GitHub': 'https://github.com/chebur5581/pioneergame'
    },
    python_requires='>=3.9',
    package_data={'pioneergame': ['Fixedsys.ttf', 'missing_texture.png', 'brick.png', 'metal.png', 'bush.png', 'yellow_tank.png', 'green_tank.png']}
)
