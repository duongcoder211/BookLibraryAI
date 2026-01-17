import pandas as pd
from pathlib import Path


path = Path().resolve()/"static"/"books"/"literature.json"

book_data = pd.read_json(path_or_buf=path)

book_data_list = list(book_data.to_dict()['books'].values())
