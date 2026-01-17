import os
from langchain_classic.agents import create_react_agent, AgentExecutor, ZeroShotAgent
from tools import search_web_tool, append_to_file_tool, rag_query_tool
from langchain_gigachat import GigaChat
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage
from dotenv import get_key
# from langchain_classic.tools import Tool # make tool throught @tool

class ReActAgent:
    def __init__(self):
        """
        Инициализация ReAct-агента
            ## Агент должен:
            `использовать GigaChat`,
            `работать через create_react_agent`,
            `иметь system prompt с инструкциями`,
            `поддерживать инструменты search_web_tool и append_to_file_tool.`
        """
        # print(get_key(dotenv_path='.env', key_to_get='GIGACHAT_CREDENTIALS'))
        
        # Инициализация LLM
        self.llm = GigaChat(
            credentials= get_key(dotenv_path='.env', key_to_get='GIGACHAT_CREDENTIALS'),
            scope="GIGACHAT_API_B2B",
            model="Gigachat-2-Pro",
            verify_ssl_certs=False,
            timeout=30
        )           
        
        # Инициализация инструментов
        self.tools = self._initialize_tools()
        
        # Создание агента
        self.agent_executor = self._create_agent()
    
    def _initialize_tools(self):
        """Инициализация инструментов"""
        return [search_web_tool, append_to_file_tool, rag_query_tool]
    
    def _create_agent(self):
        """Создание ReAct агента"""

        system_prompt = """Вы — интеллектуальный ассистент, использующий фреймворк ReAct (Reasoning + Acting).

        Вы ДОЛЖНЫ всегда строго следовать этому формату:

        Thought: [ваше рассуждение о том, что делать дальше, не говори "Пожалуйста, уточните ваш вопрос.", а извлечь как можно больше информации из полученного заппроса]
        Action: [точное название инструмента для использования - выберите из: [{tool_names}] и их функции соответственно {tools}]
        Action Input: [входные данные для инструмента в виде строки JSON]
        Observation: [результат работы инструмента]
        ... (этот шаблон повторяется, пока у вас не будет ответа)
        Thought: Теперь у меня есть окончательный ответ
        Final Answer: [ваш окончательный ответ пользователю на русском языке]

        ВАЖНЫЕ ПРАВИЛА:
        1. Используйте ТОЛЬКО английский язык для меток Thought, Action, Action Input, Observation, Final Answer
        2. Action Input должен быть корректной строкой JSON
        3. После получения Observation всегда продолжайте с Thought
        4. Когда у вас есть ответ, завершайте строкой "Final Answer:"
        5. Содержимое Final Answer должно быть на русском языке
        6. Cначала использовать rag_query_tool для поиска информации, в случае отсутствия то используй search_web_tool

        Доступные инструменты:
        1. search_web_tool: Поиск в интернете. Аргумент ввода: {{"query": "поисковый запрос"}}
        2. append_to_file_tool: Запись в файл. Аргумент ввода: {{"filepath": "имя файла", "content": "текст для записи"}}
        3. rag_query_tool: Искать нужные инфомации для ответа. Аргумент ввода: {{"query": "поисковый запрос"}}

        ВАЖНО для append_to_file_tool:
        - filepath должен быть строкой, например: "weather.txt"
        - content должен быть строкой с текстом для записи
        - НЕ вкладывайте JSON внутрь JSON

        Примеры:

        Пример 1:
        Thought: Пользователь хочет узнать текущие новости об ИИ. Мне нужно выполнить поиск в интернете.
        Action: search_web_tool
        Action Input: {{"query": "последние новости об искусственном интеллекте 2024"}}
        Observation: [результаты поиска...]
        Thought: Теперь я могу предоставить ответ на основе результатов поиска.
        Final Answer: Вот последние новости об искусственном интеллекте...

        Пример 2:
        Thought: Пользователь хочет сохранить информацию в файл. Мне следует использовать инструмент для работы с файлами.
        Action: append_to_file_tool
        Action Input: {{"filepath": "data.txt", "content": "Важная информация"}}
        Observation: Успешно добавлено в data.txt
        Thought: Файл был успешно сохранён.
        Final Answer: Информация успешно сохранена в файл data.txt

        Теперь начинаем!
        """
        human_prompt = """Question: {input}; Thought: {agent_scratchpad}"""
        # prompt = ChatPromptTemplate.from_template([
        
        prompt = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            ('human', human_prompt),
        ])
    
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            # verbose=True,
            max_iterations=7,
            early_stopping_method="force",
            handle_parsing_errors=True,  # handle parsing error
            return_intermediate_steps=True  # debug
        )

    def ask(self, query: str) -> str:
        """Выполнение запроса"""
        try:
            # print(f"Starting agent for query: {query}")
            result = self.agent_executor.invoke({"input": query})
            # print(f"Agent result: {result}")
            return result.get("output", "Ответ не получен")
        except Exception as e:
            print(f"Agent error: {e}")
            return f"Ошибка выполнения: {str(e)}"

    
    # system_prompt = """
    #     Answer the following questions as best you can. You have access to the following tools:
    #         {tools}

    #     IMPORTANT: When specifying tool names, use plain text without any formatting. 
    #     Do NOT use markdown, asterisks, or any special formatting for tool names.

    #     To use the instrument append_to_file_tool, you have to give two separate arguments in JSON format:
    #     - filepath: file name (example, "weather.txt")
    #     - content: content for recording

    #     Example of correct usage:
    #     Action: append_to_file_tool
    #     Action Input: {{"filepath": "weather.txt", "content": "content for recording"}}

    #     To use the instrument search_web, you have to provide a query string.

    #     Example of correct usage for search_web:
    #     Action: search_web
    #     Action Input: {{"query": "weather in Moscow today"}}

    #     Use the following format:

    #     Question: the input question you must answer
    #     Thought: you should always think about what to do
    #     Action: the action to take, should be one of [{tool_names}]
    #     Action Input: the input to the action
    #     Observation: the result of the action
    #     ... (this Thought/Action/Action Input/Observation can repeat N times)
    #     Thought: I now know the final answer
    #     Final Answer: the final answer to the original input question and use tools when you need

    #     Begin!

    #     Question: {input}
    #     Thought: {agent_scratchpad}
    # """


    # system_prompt = """
    #     Ты - интеллектуальный ассистент, использующий ReAct (Reasoning + Acting) подход.

    #     Твои возможности:
    #     1. Ты можешь использовать инструменты для выполнения задач, а именно {tools}
    #     2. Ты должен мыслить шаг за шагом
    #     3. Ты должен четко различать, когда думать, а когда действовать

    #     Доступные инструменты:
    #     1. search_web_tool(query): Поиск в интернете. Используй для получения свежей информации, новостей или данных, которых нет в твоих знаниях.
    #     2. append_to_file_tool(filename, content): Запись информации в файл.

    #     Формат ответов:
    #     Мысль: [твои размышления о том, что нужно сделать]
    #     Действие: [название инструмента]
    #     Аргумент: [ввод для инструмента в формате JSON]
    #     Наблюдение: [результат от инструмента]
    #     ... (повторяй пока не получишь ответ)
    #     Мысль: У меня есть вся необходимая информация
    #     Ответ: [финальный ответ пользователю]

    #     Важные правила:
    #     - Всегда используй русский язык
    #     - Для вопросов о текущих событиях всегда используй search_web
    #     - Для сохранения информации используй append_to_file
    #     - Будь краток и информативен

    #     Begin!
    #     Question: {input}
    #     Thought: {agent_scratchpad}
    #     Action: [{tool_names}]
    #     """
    #     prompt = ChatPromptTemplate.from_template(system_prompt)

    # Правильный ReAct промпт с форматом, который ожидает LangChain
    
    # system_prompt = """
    # Ты - интеллектуальный ассистент, использующий ReAct (Reasoning + Acting) подход.

    # Ты должен СТРОГО соблюдать следующий формат:

    # Question: вопрос пользователя
    # Thought: твои размышления о том, что нужно сделать
    # Action: название инструмента [{tool_names}]
    # Action Input: ввод для инструмента (в формате JSON строки)
    # Observation: результат выполнения инструмента
    # ... (этот цикл может повторяться N раз)
    # Thought: у меня есть ответ
    # Final Answer: финальный ответ пользователю

    # ВСЕГДА придерживайся этого формата! Не пропускай ни одного шага!

    # Доступные инструменты: {tools}
    # 1. search_web_tool: Поиск в интернете. Входной параметр: {{"query": "поисковый запрос"}}
    # 2. append_to_file_tool: Запись в файл. Входной параметр: {{"filename": "имя файла", "content": "текст для записи"}}

    # Пример 1:
    # Question: Какие последние новости про ИИ?
    # Thought: Пользователь спрашивает о текущих новостях, мне нужно использовать поиск в интернете
    # Action: search_web_tool
    # Action Input: {{"query": "последние новости искусственный интеллект 2024"}}
    # Observation: [результаты поиска]
    # Thought: У меня есть информация о новостях ИИ
    # Final Answer: Вот последние новости про ИИ: [пересказ результатов]

    # Пример 2:
    # Question: Сохрани информацию про ИИ в файл
    # Thought: Пользователь хочет сохранить информацию в файл
    # Action: append_to_file_tool
    # Action Input: {{"filename": "ai_info.txt", "content": "Информация про ИИ"}}
    # Observation: Успешно добавлено в файл ai_info.txt
    # Thought: Информация сохранена
    # Final Answer: Информация успешно сохранена в файл ai_info.txt

    # Важные правила:
    # - Для вопросов о текущих событиях ВСЕГДА используй search_web_tool
    # - Action Input должен быть ВСЕГДА в формате JSON строки
    # - Не создавай вымышленные наблюдения, жди реальный результат от инструмента

    # Question: {input}
    # Thought: {agent_scratchpad}
    # """


    # system_prompt = """You are an intelligent assistant using ReAct (Reasoning + Acting) framework.

    #     You must ALWAYS follow this exact format:

    #     Thought: [your reasoning about what to do next]
    #     Action: [the exact name of the tool to use - choose from: [{tool_names}]]
    #     Action Input: [the input to the tool as a JSON string]
    #     Observation: [the result from the tool]
    #     ... (this pattern repeats until you have the answer)
    #     Thought: I now have the final answer
    #     Final Answer: [your final response to the user in Russian]

    #     IMPORTANT RULES:
    #     1. Use ONLY English for Thought, Action, Action Input, Observation, Final Answer labels
    #     2. Action Input must be a valid JSON string
    #     3. After receiving Observation, always continue with Thought
    #     4. When you have the answer, end with "Final Answer:" 
    #     5. The content of Final Answer should be in Russian

    #     Available tools: [{tools}]
    #     1. search_web_tool: Search the internet. Input: {{"query": "search query"}}
    #     2. append_to_file_tool: Write to a file. Input: {{"filepath": "filename", "content": "text to write"}}

    #     Examples:

    #     Example 1:
    #     Thought: The user wants current news about AI. I need to search the web.
    #     Action: search_web_tool
    #     Action Input: {{"query": "latest AI news 2024"}}
    #     Observation: [search results...]
    #     Thought: Now I can provide the answer based on the search results.
    #     Final Answer: Вот последние новости об искусственном интеллекте...

    #     Example 2:
    #     Thought: The user wants to save information to a file. I should use the file tool.
    #     Action: append_to_file_tool
    #     Action Input: {{"filepath": "data.txt", "content": "Important information"}}
    #     Observation: Successfully appended to data.txt
    #     Thought: The file has been saved successfully.
    #     Final Answer: Информация успешно сохранена в файл data.txt

    #     Now begin!
    #     Question: {input}
    #     Thought: {agent_scratchpad}
    #     """
