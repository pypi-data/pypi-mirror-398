from pygeai.core.rerank.managers import RerankManager


rerank_manager = RerankManager()

query = "What is the Capital of the United States?"
model = "cohere/rerank-v3.5"
documents = [
    "Carson City is the capital city of the American state of Nevada.",
    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
    "Washington, D.C. is the capital of the United States.",
    "Capital punishment has existed in the United States since before it was a country."
]
top_n = 3

response = rerank_manager.rerank_chunks(query=query, model=model, documents=documents, top_n=top_n)


print(response)
