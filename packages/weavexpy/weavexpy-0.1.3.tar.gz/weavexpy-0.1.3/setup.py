from setuptools import setup

with open("README.md", "r") as arq:
    readme = arq.read()

setup(name='weavexpy',
    version='0.1.3',
    license='MIT License',
    author='João Victor',
    long_description=readme,
    long_description_content_type="text/markdown",
    author_email='joaovictor.dev.git@gmail.com',
    keywords='WeavexPy',
    description=u'WeavexPy - 0.1.3 - beta',
    packages=['WeavexPy'],
    install_requires=['pywebview', 'flask', 'flask_cors'],)