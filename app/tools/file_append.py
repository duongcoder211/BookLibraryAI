from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from langchain.tools import tool
import re

DATA_DIR = Path("agent_data")
DATA_DIR.mkdir(exist_ok=True)

# class AppendArgs(BaseModel):
#     filepath: str = Field(..., description="Имя файла внутри agent_data/")
#     content: str = Field(..., description="Текст для записи")

def clean_arg(str):
    pattern = r'("filepath": )(.*)(, "content": )(.*)'
    str = f'''{str}'''
    result = re.findall(pattern=pattern, string=str)
    output = {
        'filepath': result[0][1].strip("\"").strip(),
        'content': result[0][3].strip("\"").strip()
    }
    return dict(output)
    # return str

@tool(
    'append_to_file_tool',
    description="Write text content to a file inside agent_data/ directory.",
    # description='Записать файл c текстом внутри agent_data/',
    # args_schema=AppendArgs
)

# def append_to_file_tool(filepath: str, content : str) -> str:
#     clean_args = clean_arg(rf'''{content}''')

def append_to_file_tool(json_arg : str) -> str:
    clean_args = clean_arg(rf'''{json_arg}''')

    filepath, content = clean_args['filepath'], clean_args['content']

    file = (DATA_DIR / Path(filepath).name).absolute()

    stamp = datetime.now().strftime("[%d.%m.%Y %H:%M] ")

    with file.open("a", encoding="utf-8") as f:
        f.write(stamp + content.rstrip() + "\n")

    return f"Записано в {file.name}"

    # try:
        # # Извлекаем найденную часть
        # clean_json = match.group(0)
        # # 2. Преобразуем в словарь
        # data_dict = json.loads(clean_json)
        # # 3. Преобразуем словарь в кортеж (значения: путь и контент)
        # result_tuple = tuple(data_dict.values())
        # print("Результат (кортеж):", result_tuple)
        # filepath, content = result_tuple

        # s = s.strip().strip("{}")
        # # Делим на части по ключу "content :"
        # parts = s.split(", content:")
        
        # filepath = parts[0].replace("filepath:", "").strip()
        # content = parts[1].strip() if len(parts) > 1 else ""
        # # return (filepath, content)
        
        # text = json_arg.strip().strip("{}").strip()
    
        # # 2. Разделяем строку на путь и контент. 
        # # Используем " , content :" как разделитель, так как это уникальный маркер.
        # if ', "content":' in text:
        #     parts = text.split(', "content":', 1)
        #     filepath = parts[0].replace('"filepath":', "").replace('\"', '').strip()
        #     content = parts[1].strip()
        # else:
        #     # Если разделитель не найден, пробуем упрощенный поиск
        #     filepath = "weather.txt"
        #     content = text
    # except json.JSONDecodeError as e:
    #     print(f"Ошибка в формате JSON: {e}")


# file_append_tool = Tool(
#     name="append_to_file",
#     func=append_to_file,
#     description="Записать файла внутри agent_data/"
# )
# output = append_to_file_tool.invoke()

# append_to_file_tool.run({"filepath": "test.txt", "content": "Nội dung test"})