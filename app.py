from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from openai import AzureOpenAI
import uvicorn

app = FastAPI()

# Your existing text-based page
text_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Ask OpenAI (Text)</title>
</head>
<body>
    <h2>Ask OpenAI a Question</h2>
    <form action="/ask" method="post">
        <input type="text" name="prompt" placeholder="Enter your question" style="width: 300px;" required />
        <button type="submit">Submit</button>
    </form>
    <br/>
    <a href="/generate-image">Go to Image Generation Page</a>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return text_html

@app.post("/ask", response_class=HTMLResponse)
async def ask_openai(prompt: str = Form(...)):
    client = AzureOpenAI(
        azure_endpoint="https://vijay15apr2.openai.azure.com/",
        api_key="9mJmzN7n9NFtvK2qLca4tb1DsD0DWVQGVmNRVbITVrfnwete4yZpJQQJ99BDACfhMk5XJ3w3AAABACOGiAbm",
        api_version="2025-01-01-preview"
    )
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    result = completion.choices[0].message.content

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
            <br/>
            <a href="/">Back to Text Q&A</a><br/>
            <a href="/generate-image">Go to Image Generation Page</a>
        </body>
    </html>
    """

# New Image generation page form
image_form_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Generate Image with OpenAI</title>
</head>
<body>
    <h2>Enter a prompt to generate an image</h2>
    <form action="/generate-image" method="post">
        <input type="text" name="prompt" placeholder="Describe an image" style="width:300px;" required />
        <button type="submit">Generate</button>
    </form>
    <br/>
    <a href="/">Back to Text Q&A</a>
</body>
</html>
"""

@app.get("/generate-image", response_class=HTMLResponse)
async def get_image_form():
    return image_form_html

@app.post("/generate-image", response_class=HTMLResponse)
async def generate_image(prompt: str = Form(...)):
    client = AzureOpenAI(
        azure_endpoint="https://vijay-mcswd6jl-australiaeast.openai.azure.com/",
        api_key="8yz1IMGzHFZaAXZNNPx4FS7AyTm4cQJypzBBxKZCcOjXuwPmy6vYJQQJ99BGACL93NaXJ3w3AAAAACOGZHAw",
        api_version="2025-01-01-preview"
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        n=1
    )
    image_url = response.data[0].url

    return f"""
    <html>
        <body>
            <h2>Generated Image for: "{prompt}"</h2>
            <img src="{image_url}" alt="Generated Image" style="max-width:1024px;"/>
            <br/><br/>
            <a href="/generate-image">Generate another image</a><br/>
            <a href="/">Back to Text Q&A</a>
        </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
