from .Migration import Migration
import xml.etree.ElementTree as ET #creacion y manipulacion de estructuras XMLs
from xml.dom import minidom #formateo de XMLs con salto de linea e identado


class SkosMigration(Migration):
    """
        Clase para el formateo de texto plano descargado de GeoNames a un formatos XML Skos para la migracion de estos datos geograficos a vocabularios controlados como lo seria TemaTres
    """
    
    def __init__(self, path, split_separator='\t', colums=None, namespaces = None, scheme_uri = 'http://www.example.org/example_uri'):
        """
            1)--se pasan los parametros al padre
            2)--se definen los namespaces o prefijos que se usaranen la generacion del skos, si no se pasan por parametros se toman los que estan por defecto
            3)--se define el elemento raiz del <rdf:RDF> formateado con su namespaces
            4)--se define el scheme_uri (esta es la uri que identificara el vocabulario que se va a generar)
        """
        super().__init__(path, split_separator, colums)
        self.namespaces = namespaces if namespaces != None else {
            'rdf': 'http//:www.w3.org/1999/02/22/-rdf-syntax-ns#',
            'skos': 'http://www.w3.org/2004/02/skos/core#',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
        self.root = ET.Element('{{{}}}RDF'.format(self.namespaces['rdf']))
        self.scheme_uri = scheme_uri
    
    def prettyfyXML(self, xml_elem):
        """
            Devuelve una cadena XML fromateada y legible a partir del elemento XML pasado por parametro
            # el elemento xml se convierte en una cadena de texto plana en formato utf-8
            #toma la cadena y la analiza para su posterior formateo
            # se aplica el formateo al elemnto xml
        """
        rough_string = ET.tostring(xml_elem, 'utf-8') 
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent= "   ")
    
    def createConceptScheme(self, scheme_name):
        """
            agrega el ConceptScheme al skos a generar. seria como la raiz dentro del documento que engloba todos los terminos del vocabulario controlado
            args:
            scheme_uri: uri unica para identificar el vocabulario
            scheme_name: nombre legible para usuarios humanos del vocabulario
        """
        scheme_element = ET.SubElement(self.root, '{{{}}}ConceptScheme'.format(self.namespaces['skos']))
        scheme_element.set('{{{}}}about'.format(self.namespaces['rdf']), self.scheme_uri)
        
        pref_label = ET.SubElement(scheme_element, '{{{}}}prefLabel'.format(self.namespaces['skos']))
        pref_label.set('{{{}}}lang'.format(self.namespaces['xml']), 'es')
        pref_label.text = scheme_name
        
        return scheme_element
    
    def createConcept(self, geonameid, name, alternatenames, base_concept_uri = 'http://sws.geonames.org/'):
        """
            Crea un concepto SKOS de un lugar proporcionado por los datos de geonames para ser guardado en el vocabulario
            args:
            geonameid: id unico proporcionado por geonames
            name: nombre del lugar a guardar como termino
            alternatenames: nombres alternativos a guardar como terminos relacionados
            base_concept_uri: uri base a guardar para el nuevo concepto a crear
        """
        concept_uri = base_concept_uri + str(geonameid) + '/'
        
        concept_element = ET.SubElement(self.root, '{{{}}}Concept'.format(self.namespaces['skos']))
        concept_element.set('{{{}}}about'.format(self.namespaces['rdf']), concept_uri)
        
        pref_label = ET.SubElement(concept_element, '{{{}}}prefLabel'.format(self.namespaces['skos']))
        pref_label.set('{{{}}}lang'.format(self.namespaces['xml']), 'es')
        pref_label.text = name
        
        notation = ET.SubElement(concept_element, '{{{}}}notation'.format(self.namespaces['skos']))
        notation.text = str(geonameid)
        
        for alt_name in alternatenames:
            alt_name = alt_name.strip()
            if alt_name:
                alt_label = ET.SubElement(concept_element, '{{{}}}altLabel'.format(self.namespaces['skos']))
                alt_label.set('{{{}}}lang'.format(self.namespaces['xml']), 'es')
                alt_label.text = alt_name
                
        in_scheme = ET.SubElement(concept_element, '{{{}}}inScheme'.format(self.namespaces['skos']))
        in_scheme.set('{{{}}}resource'.format(self.namespaces['rdf']), self.scheme_uri)
        
        return concept_element
    
    def exportToSKOS(self, scheme_name, output_file):
        """
            metodo para migrar de un txt plano proporcionado por geonames a un formato rdf skos para vocabularios controlados. usando el nombre de los lugares como termino y sus nombres alternativos como terminos relacionados
            args:
            scheme_name: nombre del esquema principal del rdf a crear
            input_file: archivo txt de geonames
            output_file: archivo rdf skos
        """
        self.createConceptScheme(scheme_name = scheme_name)
        with open(self.path, 'r', encoding = 'utf_8') as txt:
            for row in txt:
                data = super().rowtoDict(row.strip().split(self.split_separator))
                self.createConcept(geonameid = data['geonameid'] ,name = data['name'], alternatenames = data['alternatenames'])
            txt.close()
        with open(output_file, 'w', encoding = 'utf-8') as rdf:
            rdf.write(self.prettyfyXML(self.root))
            rdf.close()