from fastapi import FastAPI
from pydantic import BaseModel
from g4f.client import Client

# Definir el esquema de entrada
class Query(BaseModel):
    text: str

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API con g4f funcionando gaaa"}

# Endpoint POST para recibir texto
@app.post("/ask")
def ask(query: Query):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": query.text}],
        web_search=True
    )
    return {"answer": response.choices[0].message.content}
