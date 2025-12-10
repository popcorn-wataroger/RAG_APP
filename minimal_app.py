# minimal_app.py - 最小限のテスト用FastAPIアプリ
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Minimal Test")

class AskIn(BaseModel):
    query: str

class AskOut(BaseModel):
    query: str
    answer: str

@app.get("/")
def root():
    return {"message": "Server is running"}

@app.post("/ask", response_model=AskOut)
def ask_endpoint(body: AskIn):
    return AskOut(query=body.query, answer="Test response")
