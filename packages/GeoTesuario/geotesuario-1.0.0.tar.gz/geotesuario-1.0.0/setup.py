from setuptools import setup, find_packages

setup(
    name="GeoTesuario",
    version="1.0.0",
    author="Yorjandy Martínez Lamas",
    author_email="yorjandy5@gmail.com",
    description="Biblioteca para la migración de datos de GeoNames a vocabularios controlados en formato SKOS y texto etiquetado. Garantiza la generacion de archivos JSON, CSV con los datos completos de los lugares de geonames segun se le pase un txt con los datos en crudo que proprociona GeoNames. Tambien los puede exportar a formato de texto etuiquetado y rdf:skos para poder importar los loguares y sus nombres alternativos a un vocabulario controlado como por ejemplo TemaTres",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Yorjandy/geo_tesuario.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[],
    include_package_data=True,
)
