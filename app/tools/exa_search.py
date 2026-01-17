import os
from dotenv import get_key
from exa_py import Exa
from langchain.tools import tool

# exa = Exa(get_key('.env', 'EXA_API_KEY'))
exa = Exa(os.getenv("EXA_API_KEY"))

@tool(
    "search_web_tool",
    description="Search for information on the internet using Exa Search API. Returns a list of brief results.",
    # description="Поиск информации в интернете через Exa Search API. Возвращает список кратких результатов."
)
def search_web_tool(query: str, max_results: int = 5) -> str:
    response = exa.search(query, num_results=max_results)

    items = []
    for r in response.results:
        snippet = r.text[:300].replace("\n", " ") if r.text else ""
        items.append(f"{r.title}: {snippet} — {r.url}")

    return "\n".join(items) or "Ничего не найдено."

# result = search_web_tool.invoke('AI agent')
# print(result)

# search_tool = Tool(
#     name="search_web",
#     func=search_web,
#     description="Поиск информации в интернете через Exa Search API. Возвращает список кратких результатов."
# )
