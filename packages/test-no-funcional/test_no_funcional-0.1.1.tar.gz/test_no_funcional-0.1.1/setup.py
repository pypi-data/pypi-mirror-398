from setuptools import setup, find_packages

#Leer el contenido del archivo README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="test_no_funcional",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[],
    author="Ditenz",
    description="Consultas de cursos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    utl="https://hack4u.io"

)
