from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma
from langchain_gigachat.chat_models import GigaChat
from langchain_core.tools import tool
from typing_extensions import List
from dotenv import get_key
from openai import OpenAI

# Шаг 4.2: Создайте промпт-шаблон:
prompt_template = """Ты -- научный ассистент, специализирующийся на анализе научных статей.
Твоя задача -- отвечать на вопросы пользователя, основываясь ТОЛЬКО на предоставленном контексте из научных статей ArXiv.

Правила:
1. Используй только информацию из контекста ниже
2. Если в контексте нет информации для ответа, честно скажи об этом
3. Указывай, из каких статей взята информация (если есть метаданные)
4. Отвечай на русском языке, четко и структурированно
5. Если вопрос касается технических деталей, будь точным

Контекст из научных статей: {context}

Вопрос пользователя: {question}

Ответ:"""

prompt = ChatPromptTemplate.from_template(prompt_template)

llm = GigaChat(
    credentials="OThhZGViNTgtN2E0Mi00YmExLTgzMTctM2YwNjFmNGI0NzNkOmM2YzYzMGJlLTczMGQtNDk3MC04MjRlLWQwZjBkZWRkM2U5Mg==",
    scope="GIGACHAT_API_B2B",
    model="Gigachat-2-Pro",
    verify_ssl_certs=False,
    timeout=30
)

client = OpenAI(
    api_key=get_key('.env', "OPEN_AI_KEY"),
    base_url="https://foundation-models.api.cloud.ru/v1"
)

# Создание экземпляра эмбеддингов
class CustomEmbeddings(Embeddings):
    """Кастомный класс эмбеддингов для работы с API"""

    def __init__(self, client, model="BAAI/bge-m3"):
        self.client = client
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Получение эмбеддингов для списка документов"""
        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            embeddings.append(response.data[0].embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Получение эмбеддинга для запроса"""
        response = self.client.embeddings.create(
            input=[text],
            model=self.model
        )
        return response.data[0].embedding
    
embeddings = CustomEmbeddings(client)

# Использование vectorstore после создания векторного хранилища (chroma_db уже сушествует) чтобы не занимать еще время создания хранилища
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="arxiv_papers"
)

def format_docs(docs):
    """
    Форматирует список документов в единую строку контекста

    Args:
        docs: Список документов Document
        
    Returns:
        str: Форматированный контекст
    """
    context_parts = []
    for i, doc in enumerate(docs, 1):
        context_parts.append(f"[Документ {i}]")
        context_parts.append(doc.page_content)
        if doc.metadata:
            context_parts.append(f"Метаданные: {doc.metadata}")
        context_parts.append("") # Пустая строка для разделения
    return "\n".join(context_parts)

def get_embedding(text: str, client, model="BAAI/bge-m3") -> list:
    """Получает эмбеддинг текста"""
    response = client.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding

# Проверка работы хранилища
def test_saver():
    test_query = "машинное обучение и нейронные сети"
    results = vectorstore.similarity_search(test_query, k=3)
    print(f"\nРезультаты поиска по запросу '{test_query}':")
    for i, doc in enumerate(results, 1):
        print(f"\n{i}. {doc.page_content[:200]}...")
        print(f"Метаданные: {doc.metadata}")

# Создание базового ретривера с поиском по схожести
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5} # Возвращать топ-5 документов
)

# Тестирование ретривера
def test_retriever(query: str = "глубокое обучение для обработки изображений"):
    retrieved_docs = retriever.invoke(query)
    print(f"Найдено документов: {len(retrieved_docs)}")
    for i, doc in enumerate(retrieved_docs, 1):
        print(f"\nДокумент {i}:")
        print(doc.page_content[:150] + "...")
# test_retriever()

# Шаг 3.2: Попробуйте ретривер с MMR (Maximum Marginal Relevance):
# MMR балансирует между релевантностью и разнообразием результатов
retriever_mmr = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 20, # Количество документов для первичной выборки
        "lambda_mult": 0.5 # Баланс между релевантностью (1.0) и разнообразием (0.0)
    }
)

# Шаг 3.3: Создайте ретривер с порогом схожести:
# Ретривер с фильтрацией по оценке схожести
retriever_threshold = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.2, # Минимальная оценка схожести
        "k": 10
    }
)
 
# Шаг 4.4: Соберите RAG-цепочку:
# Создание RAG-цепочки
rag_chain = (
    {
        "context": retriever | format_docs, # Извлекаем и форматируем документы
        "question": RunnablePassthrough()   # Передаем вопрос как есть
    }
    | prompt  # Формируем промпт
    | llm     # Отправляем в языковую модель
)

# Тестирование RAG-системы
@tool(
    name_or_callable='rag_query_tool',
    description='Искать нужные инфомации для ответа'
    # description='query relevance document in vector store'
)
def rag_query_tool(query:str):
    # questions = [
    #     "Какие методы машинного обучения используются для обработки изображений?",
    #     "Расскажи о применении трансформеров в обработке естественного языка",
    #     "Какие существуют подходы к обучению нейронных сетей?"
    # ]
    # print("=== RAG-системы ===\n")
    # for i, question in enumerate(questions, 1):
    #     print(f"Вопрос {i}: {question}")
    #     print("-" * 80)

    try:
        response = rag_chain.invoke(query)
        return response.content or "Ничего не найдено."
        # print(f"Ответ: {response.content}\n")
    except Exception as e:
        print(f"\nОшибка: {e} in rag_query_tool\n")
        return "Ничего не найдено."

