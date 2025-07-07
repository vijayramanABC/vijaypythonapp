from fastapi import FastAPI
import uvicorn
from openai import AzureOpenAI

app = FastAPI()

@app.get("/")
def read_root():
    client = AzureOpenAI(azure_endpoint="https://vijay15apr2.openai.azure.com/", api_key="9mJmzN7n9NFtvK2qLca4tb1DsD0DWVQGVmNRVbITVrfnwete4yZpJQQJ99BDACfhMk5XJ3w3AAABACOGiAbm", api_version="2025-01-01-preview")
    completion = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": "Names of Ganpati"}])
    return completion.choices[0].message.content
