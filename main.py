import os
from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase
import uvicorn


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Neo4j connection setup
neo4j_uri = os.getenv("NEO4J_CONNECTION_URI")
neo4j_username = os.getenv("NEO4J_USERNAME")
neo4j_password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

llm = ChatOpenAI(model="gpt-4o-mini", openai_api_key=os.getenv('OPENAI_API_KEY'))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    print('Request for index page received')
    return templates.TemplateResponse('index.html', {"request": request})

@app.get('/favicon.ico')
async def favicon():
    file_name = 'favicon.ico'
    file_path = './static/' + file_name
    return FileResponse(path=file_path, headers={'mimetype': 'image/vnd.microsoft.icon'})

@app.post('/hello', response_class=HTMLResponse)
async def hello(request: Request, name: str = Form(...)):
    if name:
        print('Request for hello page received with name=%s' % name)
        neo4j_response = await generate_seed_question()
        print('Neo4j response received.')
        llm_response = await llm.ainvoke(name)
        print('LLM response received.')
        return templates.TemplateResponse('hello.html', {"request": request, 'name':name,
                                                         'question':neo4j_response['question'],
                                                         'llm_response':llm_response.content})
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return RedirectResponse(request.url_for("index"), status_code=status.HTTP_302_FOUND)

async def generate_seed_question() -> dict:
    query = """MATCH (q: Question) RETURN q.QuestionTitle, q.QuestionDescription, q.GoldenSolution LIMIT 1"""
    record, _, _ = driver.execute_query(query)
    result = record[0]
    if result:
        title, description, solution = result
        return {
            "question": title,
            "description": description,
            "correct_answer": solution
        }
    else:
        return {
            "question": "No question available",
            "description": "Please try again later",
            "correct_answer": ""
        }


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)

