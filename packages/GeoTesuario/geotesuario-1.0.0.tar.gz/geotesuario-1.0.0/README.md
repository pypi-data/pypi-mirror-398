
# GeoTesuario

GeoTesuario es una biblioteca de Python diseñada para facilitar la migración de datos geográficos desde los archivos de texto plano proporcionados por GeoNames a formatos estructurados como JSON, CSV, texto etiquetado y RDF SKOS. Esto permite integrar estos datos en vocabularios controlados como TemaTres.

## Características

- **Exportación a JSON**: Convierte los datos de GeoNames a un archivo JSON estructurado.
- **Exportación a CSV**: Genera un archivo CSV con los datos organizados en columnas.
- **Exportación a texto etiquetado**: Crea un archivo de texto etiquetado compatible con TemaTres.
- **Exportación a RDF SKOS**: Genera un archivo RDF SKOS para vocabularios controlados, con soporte para términos y nombres alternativos.

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu_usuario/GeoTesuario.git
   ```
2. Navega al directorio del proyecto:
   ```bash
   cd GeoTesuario
   ```
3. Instala la biblioteca:
   ```bash
   pip install .
   ```

## Uso

### 1. Clase `Migration`

La clase `Migration` permite transformar los datos de GeoNames a formatos JSON, CSV y texto etiquetado.

#### Ejemplo de uso:
```python
from GeoTesuario import Migration

# Inicializa la migración
migration = Migration("geonames_data.txt")

# Exporta a JSON
migration.exportToJSON("output.json")

# Exporta a CSV
migration.exportToCSV("output.csv")

# Exporta a texto etiquetado
migration.exportToTaggedText("output.txt")
```

### 2. Clase `SkosMigration`

La clase `SkosMigration` extiende `Migration` y permite exportar los datos a un formato RDF SKOS.

#### Ejemplo de uso:
```python
from GeoTesuario import SkosMigration

# Inicializa la migración SKOS
skos_migration = SkosMigration("geonames_data.txt", scheme_uri="http://example.org/vocab")

# Exporta a SKOS
skos_migration.exportToSKOS("Mi Vocabulario", "output.rdf")
```

## Estructura del Proyecto

```
GeoTesuario/
├── GeoTesuario/
│   ├── __init__.py          # Inicialización del paquete
│   ├── Migration.py         # Clase base para la migración de datos
│   └── SkosMigration.py     # Clase para la exportación a RDF SKOS
├── LICENSE                  # Licencia MIT
├── README.md                # Documentación del proyecto
├── setup.py                 # Configuración para PyPI
└── .gitignore               # Archivos y carpetas ignorados por Git
```

## Detalles Técnicos

### Clase `Migration`

- **Métodos principales**:
  - `exportToJSON(path)`: Exporta los datos a un archivo JSON.
  - `exportToCSV(path)`: Exporta los datos a un archivo CSV.
  - `exportToTaggedText(path)`: Exporta los datos a un archivo de texto etiquetado.

- **Transformaciones**:
  - Convierte nombres alternativos en listas.
  - Reemplaza comas en los datos por punto y coma para evitar conflictos en CSV.

### Clase `SkosMigration`

- **Métodos principales**:
  - `createConceptScheme(scheme_name)`: Crea el esquema principal del vocabulario SKOS.
  - `createConcept(geonameid, name, alternatenames, base_concept_uri)`: Crea un concepto SKOS con términos y nombres alternativos.
  - `exportToSKOS(scheme_name, output_file)`: Exporta los datos a un archivo RDF SKOS.

- **Detalles**:
  - Utiliza `xml.etree.ElementTree` para generar estructuras XML.
  - Formatea el XML con `xml.dom.minidom` para hacerlo legible.

## Requisitos

- Python 3.6 o superior.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más detalles.

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar esta biblioteca, por favor abre un issue o envía un pull request.

## Contacto

- **Autor**: Yorjandy Martínez Lamas
- **Correo**: yorjandy5@gmail.com
- **Repositorio**: [GitHub](https://github.com/Yorjandy/geo_tesuario.git)
