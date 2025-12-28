'''                                                                                                                                                                                                                              
IIIIIIIIIIMMMMMMMM               MMMMMMMM        GGGGGGGGGGGGGBBBBBBBBBBBBBBBBB           66666666         444444444  
I::::::::IM:::::::M             M:::::::M     GGG::::::::::::GB::::::::::::::::B         6::::::6         4::::::::4  
I::::::::IM::::::::M           M::::::::M   GG:::::::::::::::GB::::::BBBBBB:::::B       6::::::6         4:::::::::4  
II::::::IIM:::::::::M         M:::::::::M  G:::::GGGGGGGG::::GBB:::::B     B:::::B     6::::::6         4::::44::::4  
  I::::I  M::::::::::M       M::::::::::M G:::::G       GGGGGG  B::::B     B:::::B    6::::::6         4::::4 4::::4  
  I::::I  M:::::::::::M     M:::::::::::MG:::::G                B::::B     B:::::B   6::::::6         4::::4  4::::4  
  I::::I  M:::::::M::::M   M::::M:::::::MG:::::G                B::::BBBBBB:::::B   6::::::6         4::::4   4::::4  
  I::::I  M::::::M M::::M M::::M M::::::MG:::::G    GGGGGGGGGG  B:::::::::::::BB   6::::::::66666   4::::444444::::444
  I::::I  M::::::M  M::::M::::M  M::::::MG:::::G    G::::::::G  B::::BBBBBB:::::B 6::::::::::::::66 4::::::::::::::::4
  I::::I  M::::::M   M:::::::M   M::::::MG:::::G    GGGGG::::G  B::::B     B:::::B6::::::66666:::::64444444444:::::444
  I::::I  M::::::M    M:::::M    M::::::MG:::::G        G::::G  B::::B     B:::::B6:::::6     6:::::6         4::::4  
  I::::I  M::::::M     MMMMM     M::::::M G:::::G       G::::G  B::::B     B:::::B6:::::6     6:::::6         4::::4  
II::::::IIM::::::M               M::::::M  G:::::GGGGGGGG::::GBB:::::BBBBBB::::::B6::::::66666::::::6         4::::4  
I::::::::IM::::::M               M::::::M   GG:::::::::::::::GB:::::::::::::::::B  66:::::::::::::66        44::::::44
I::::::::IM::::::M               M::::::M     GGG::::::GGG:::GB::::::::::::::::B     66:::::::::66          4::::::::4
IIIIIIIIIIMMMMMMMM               MMMMMMMM        GGGGGG   GGGGBBBBBBBBBBBBBBBBB        666666666            4444444444
                                                                                                                      
                                                                                                                                                                                                                                         
                                                                                                                                                                                                                 
This library made for Base64 encode/decode images.
Made by: Wl13Proger9
GitHub: https://github.com/Wl13proger9/IMGB64
PyPi:   ~~~~~~~~~~~~~~~~
'''
import json
import base64
import os
from PIL import Image
from io import BytesIO
import msgpack, gzip


class imgb64:
    __version__ = "v1.7.25.12"


    def js_get(fp:str , key: str):                            #get from json
        '''
        Данная функция получает значение по ключу из JSON файла.
        This function gets a value by key from a JSON file.

        
        Аргументы/Arguments:
              fp: str        
              key: str

                
        Пример/Example:
            imgb64.js_get("test.json", "1.jpg")
        '''
        try:
            with open(fp, 'r', encoding='utf-8') as file: 
                data = json.load(file)
                value = data.get(key, None) 

                #[Возвращение значения]
                if value is not None:return value
                else: return f'Key "{key}" not matching in JSON file.'
        except:return None
        
    def js_set(fp: str, key: str, new_value: str):            #set to json
        '''
        Данная функция записывает значение в JSON файл.
        This function writes a value to a JSON file.

        
        Аргументы/Arguments:
              fp: str        
              key: str
              new_value: str

                
        Пример/Example:
            imgb64.js_set("test.json", "1.jpg", "Something New")
        '''
        try:
            with open(fp, 'r+', encoding='utf-8') as file:
                data = json.load(file)
                data[key] = new_value
                file.seek(0)

                #[Назначение значения]
                json.dump(data, file, ensure_ascii=False, indent=4)
                file.truncate()
                
        except FileNotFoundError:return f'File {fp} not found.'
        except json.JSONDecodeError:return f'Error when parsing: {fp}.'

 

    def decode(file_path: str, img: str):                     #set
        '''
        Данная функция кодирует изображение в Base64.
        This function encodes an image in Base64.

        
        Аргументы/Arguments:
              file_path: str       
              img: str

                
        Пример/Example:
            imgb64.decode("test.json", "1.jpg")
        '''
        try:
            #[Получение Base64 код изображения]
            with open(img, "rb") as image_file:
                encoded_string = base64.b64encode(
                    image_file.read()
                    ).decode("utf-8")
                #print(encoded_string)


            #[Работа с обычным файлом]
            if file_path.endswith(".json"):

                #[Если нет файла то он создаться сам]
                if not os.path.exists(file_path):
                    with open(file_path, "w") as f:f.write("{}")


                #[Запись в .json файл]
                imgb64.js_set(file_path,
                    os.path.basename(img).split('/')[-1],
                    str(encoded_string))


            #[Работа с компрессором]
            elif file_path.endswith(".gz"):

                #[Получение существующих данных или создание новых]
                bin_data = {}
                if os.path.exists(file_path):
                    with gzip.open(file_path, "rb") as f:packed = f.read()
                    bin_data = msgpack.unpackb(packed, raw=False)

                #[Добавление нового изображения]
                img_key = os.path.basename(img).split('/')[-1]
                b64_data = encoded_string
                if b64_data.startswith("data:"):b64_data = b64_data.split(",", 1)[1]
                bin_data[img_key] = base64.b64decode(b64_data)

                #[Запись файла в .gz архив]
                packed = msgpack.packb(bin_data, use_bin_type=True)
                with gzip.open(file_path, "wb", compresslevel=9) as f:f.write(packed)


            #[Если первое или второе действие не соблюдено]
            else: return None
        except: return None

    def encode(file_path: str, img_name: str, text = False):                #get
        '''
        Данная функция декодирует изображение из файла.
        This function decodes an image from a file.

        
        Аргументы/Arguments:
              file_path: str       
              img_name: str
              text = False  #[True]

                
        Пример/Example:
            imgb64.encode("test.json", "1.jpg")
        '''
        try:
            #[Работа с .json]
            if file_path.endswith(".json"):
                if text == True:return imgb64.js_get(file_path, img_name)
                else:return base64.b64decode(imgb64.js_get(file_path, img_name))
        
            #[Работа с .gz]
            elif file_path.endswith(".gz"):
                if not os.path.exists(file_path):return None
                
                with gzip.open(file_path, "rb") as f:packed = f.read()
                data = msgpack.unpackb(packed, raw=False)

                value = data.get(img_name)
                if value is not None:
                    if text == True:return value
                    else:return base64.b64encode(value).decode("utf-8")
                
            else: return None
        except: return None

    def keys(file_path: str):                                 #keys
        '''
        Данная функция выводит все ключи с файла.
        This function decodes an image from a file.

        
        Аргументы/Arguments:
              file_path: str       

                
        Пример/Example:
            imgb64.keys("test.json")
        '''
        try:
            keys = []

            #[Работа с .json]
            if file_path.endswith(".json"):   

                with open(file_path, "r", encoding="utf-8") as f:

                    data = json.load(f)
                    for key in data:keys.append(key)

                return keys
            

            #[Работа с .gz]
            elif file_path.endswith(".gz"):

                with gzip.open(file_path, "rb") as f:packed = f.read()

                data = msgpack.unpackb(packed, raw=False)
                for key in data:keys.append(key)

                return keys

            #[Иначе]
            else:return None
        except: return None

    def b64info(file_path: str, img_name: str, out="all"):    #info
        '''
        Данная функция выводит информацию с ключа.
        This function displays information from the key.

        
        Аргументы/Arguments:
              file_path: str  
              img_name: str    
              out = "all"  #[img_name, img_size, file_size]
            

                
        Пример/Example:
            imgb64.b64info("test.json","1.jpg","all")
        '''
        try:
            #[Проверка .json ли, или .gz файл]
            if file_path.endswith(".json"):
                image_bytes = base64.b64decode(imgb64.encode(file_path, img_name))
                image = Image.open(BytesIO(image_bytes))              
            elif file_path.endswith(".gz"):
                with gzip.open(file_path, "rb") as f:packed = f.read()

                data = msgpack.unpackb(packed, raw=False)
                value = data.get(img_name)
                if value is None:return None
                
                image_bytes = value 
                image = Image.open(BytesIO(image_bytes))           
            else:return None


            #[Получение информации об изображении]
            width, height = image.size
            file_kb = len(image_bytes) / 1024
                
            #[Вывод информации]
            if out == "all":  
                return {
                    "img_name": img_name,
                    "img_size": f'{width}x{height}',
                    "file_size": f'{file_kb}'}#:.1f}'}    
            elif out == "img_name":return img_name
            elif out == "img_size":return f'{width}x{height}'
            elif out == "file_size":return f'{file_kb}'#:.1f}'


            else:return None
        except: return None

    def convert(file_path: str, end_name = "output.gz"):      #convert
        '''
        Данная функция конвертирует файл в его компрессированный вариант, или обратно.
        This function converts a file to its compressed version, or vice versa.

        
        Аргументы/Arguments:
              file_path: str  
              end_name: str  #[default: output.gz]
              

                      
        Пример/Example:
            imgb64.b64info("test.json","1.jpg","all")
        '''
        try:            
            #[Работа с .json]
            if file_path.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:data = json.load(f)
                bin_data = {}

                for k, b64 in data.items():
                    if b64.startswith("data:"):b64 = b64.split(",", 1)[1]
                    bin_data[k] = base64.b64decode(b64)

                packed = msgpack.packb(bin_data, use_bin_type=True)

                if not end_name.endswith(".gz"): end_name += ".gz"
                with gzip.open(end_name, "wb", compresslevel=9) as f:f.write(packed)

            #[Работа с .gz]
            elif file_path.endswith(".gz"):
                if not end_name.endswith(".json"): end_name += ".json"
                    
                with gzip.open(file_path, "rb") as f:packed = f.read()
                data = msgpack.unpackb(packed, raw=False)

                json_data = {}
                for k, bin_data in data.items():
                    json_data[k] = base64.b64encode(bin_data).decode("utf-8")

                with open(end_name, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                            
            else: return None
        except: return None



'''
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#[Пример использования]
imgb64.decode("test2.json", "./test_img/346.jpg")
imgb64.decode("test2.gz", "./test_img/346.jpg")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#[Декодирование]
imgb64.encode('test2.json', "346.jpg")
imgb64.encode('test2.gz', "346.jpg")

print(len(imgb64.encode('test2.json', "346.jpg")))  --> 250852
print(len(imgb64.encode('test2.gz', "346.jpg")))    --> 188139

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        
#[Получение ключей]
print(imgb64.keys("test2.json"))                --> ['346.jpg']
print(imgb64.keys("test2.gz"))                  --> ['346.jpg']

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#[Получение информации]
print(imgb64.b64info("test2.json",'346.jpg'))      --> {'img_name': '346.jpg', 'img_size': '719x1280', 'file_size': '183.7294921875'}
print(imgb64.b64info("test2.gz",'346.jpg'))        --> {'img_name': '346.jpg', 'img_size': '719x1280', 'file_size': '183.7294921875'}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
'''


'''
TODO:
├───────────────────────────────────────────────────┤
│[STEP: 2][Status: False]                           │

│- Добавить PyPi ссылку.                            │
├───────────────────────────────────────────────────┤
│[STEP: 3][Status: False]                           │
│- Вынести код в PyPi.                              │
│- Выложить исходник на GitHub.                     │
├───────────────────────────────────────────────────┤
│[STEP: 4][Status: False]                           │
│- Описать его в PyPi.                              │
│- Описать его на GitHub.                           │
└───────────────────────────────────────────────────┘
'''