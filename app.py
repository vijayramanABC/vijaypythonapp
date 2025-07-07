from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from openai import AzureOpenAI
import uvicorn

app = FastAPI()

# HTML form to collect user input
html_form = """
<!DOCTYPE html>
<html>
<head>
    <title>Ask OpenAI</title>
</head>
<body>
    <h2>Ask OpenAI a Question</h2>
    <form action="/ask" method="post">
        <input type="text" name="prompt" placeholder="Enter your question" style="width: 300px;" required />
        <button type="submit">Submit</button>
    </form>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    return html_form

@app.post("/ask", response_class=HTMLResponse)
async def get_response(prompt: str = Form(...)):
    client = AzureOpenAI(
        azure_endpoint="https://vijay15apr2.openai.azure.com/",
        api_key="9mJmzN7n9NFtvK2qLca4tb1DsD0DWVQGVmNRVbITVrfnwete4yZpJQQJ99BDACfhMk5XJ3w3AAABACOGiAbm",  # Replace this before pushing to GitHub
        api_version="2025-01-01-preview"
    )
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    result = completion.choices[0].message.content

    # Return the HTML + result
    return f"""
    <html>
        <body>
            <h2>Ask OpenAI a Question</h2>
            <form action="/ask" method="post">
                <input type="text" name="prompt" value="{prompt}" style="width: 300px;" required />
                <button type="submit">Submit</button>
            </form>
            <h3>Response:</h3>
            <p>{result}</p>
        </body>
    </html>
    """
