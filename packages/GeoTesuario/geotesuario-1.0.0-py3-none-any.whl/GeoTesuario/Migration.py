import os
import json
import csv as CSV

class Migration:
    
    """
        Modulo para la migracion de datos de geonames desde los archivos .txt que proporciona el servicio por defecto a un formato estructurado.
    """
    
    def __init__(self, path, split_separator = '\t', colums = None):
        self.path = path
        self.split_separator = split_separator
        self.COLUMS = colums if colums != None else [
            'geonameid',
            'name',
            'asciiname',
            'alternatenames',
            'latitude',
            'longitude',
            'feature_class',
            'feature_code',
            'country_code',
            'cc2',
            'admin1_code',
            'admin2_code',
            'admin3_code',
            'admin4_code',
            'population',
            'elevation',
            'dem',
            'timezone',
            'modification_date'
        ]
        
    #metodo para la creacion de un diccionario con los nombres de las columnas y una fila de datos
    def rowtoDict(self, row):
        data = {}
        for idx, column in enumerate(self.COLUMS):
            if idx < len(row):
                value = row[idx].strip()
                if column == 'alternatenames':
                    value = value.split(',') if value != "" else []
                data[column] = value if value != "" else None
            else:
                data[column] = None
        return data 
    
    #metodo para la creacion de listas de str listas para guardar en formato CSV
    def rowToCSVList(self, row):
        row_list = []
        for element in row.strip().split(self.split_separator):
            if ',' in element:
                element = ';'.join(element.strip().split(','))
            row_list.append(element)
        return row_list 
    
    #metodo para guardarlos datos del fichero txt en un fichero json ya reestructurados
    def exportToJSON(self, path: str):
        if not os.path.exists(path):
            with open(path, "w", encoding= "utf-8") as jsonl:
                jsonl.close()
                
        with open(self.path, 'r', encoding= "utf-8") as txt, open(path, 'a', encoding= "utf-8") as jsonl:
            jsonl.write('[\n')
            point_line = txt.readline()
            while point_line:
                row_items = point_line.strip().split(self.split_separator)
                data = self.rowtoDict(row_items)
                point_line = txt.readline()
                if point_line:
                    jsonl.write(json.dumps(data, ensure_ascii=False) + ",\n")
                else: 
                    jsonl.write(json.dumps(data, ensure_ascii=False) + "\n")
            jsonl.write(']')
            jsonl.close()
            txt.close()
            
    #metodo para transformar de txt plano de geonames a texto etiquetado que pueda migrar a tematres
    def exportToTaggedText(self, path):
        if not os.path.exists(path):
            with open(path, 'w', encoding= 'utf-8') as structure_text:
                structure_text.close()
                
        with open(self.path, 'r', encoding='utf-8') as txt, open(path, 'a', encoding= 'utf-8') as structure_text:
            for row in txt:
                data = self.rowtoDict(row.strip().split(self.split_separator))
                structure_text.write(data['name'] + '\n')
                for altername in data['alternatenames']:
                    structure_text.write('UF:'+ altername + '\n')
                structure_text.write('\n')
            txt.close()
            structure_text.close()
    
    #metodo para transformar de texto plano de geonames a formato csv
    def exportToCSV(self, path):
        if not os.path.exists(path):
            with open(path, 'w', encoding = 'utf-8') as csv:
                csv.close()
        with open(self.path, 'r', encoding = 'utf-8') as txt, open(path, 'a', encoding = 'utf-8', newline = '') as csv:
            csv_writer = CSV.writer(csv)
            csv_writer.writerow(self.COLUMS)
            for row in txt:
                csv_writer.writerow(self.rowToCSVList(row))
            txt.close()
            csv.close()
            