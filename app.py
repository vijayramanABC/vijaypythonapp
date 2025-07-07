from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

app = FastAPI()

# --- Config ---

# OpenAI Azure endpoint and key
OPENAI_AZURE_ENDPOINT = "https://vijay15apr2.openai.azure.com/"
OPENAI_API_KEY = "9mJmzN7n9NFtvK2qLca4tb1DsD0DWVQGVmNRVbITVrfnwete4yZpJQQJ99BDACfhMk5XJ3w3AAABACOGiAbm"
OPENAI_API_VERSION = "2025-01-01-preview"

# Azure Search
SEARCH_ENDPOINT = "https://vijayaisearch.search.windows.net"
SEARCH_API_KEY = "Uu7vNqo3rOmsInCMiNzQKUgJF4UAVqZpfT5quZQ8qbAzSeBh2CGX"
SEARCH_INDEX_NAME = "multimodal-rag-1751364945777"

# Azure Blob Storage
BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=vijayaistorage;AccountKey=hIZGQYe02nk9dOwfbU6iLdAV8Jq7WqJ/eyXohtcuc6036GhKEW5qwoQKOSFRY6FsyobWDjE+fCtR+AStgKVSzg==;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME = "vijayimagecontainer"

# --- Routes ---


# Home page: Text Q&A with OpenAI
@app.get("/", response_class=HTMLResponse)
async def text_qa_form():
    return """
    <html><body>
        <h2>Text Q&A with OpenAI</h2>
        <form action="/" method="post">
            <input type="text" name="question" placeholder="Ask something..." style="width:400px;" required />
            <button type="submit">Ask</button>
        </form>
        <br/>
        <a href="/generate-image">Go to Image Generation</a><br/>
        <a href="/search-image">Go to Image Search</a>
    </body></html>
    """

@app.post("/", response_class=HTMLResponse)
async def text_qa_post(question: str = Form(...)):
    client = AzureOpenAI(
        azure_endpoint=OPENAI_AZURE_ENDPOINT,
        api_key=OPENAI_API_KEY,
        api_version=OPENAI_API_VERSION,
    )
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
    )
    answer = completion.choices[0].message.content

    return f"""
    <html><body>
        <h2>Question:</h2>
        <p>{question}</p>
        <h2>Answer:</h2>
        <p>{answer}</p>
        <br/>
        <a href="/">Ask another question</a><br/>
        <a href="/generate-image">Go to Image Generation</a><br/>
        <a href="/search-image">Go to Image Search</a>
    </body></html>
    """


# Image generation page
@app.get("/generate-image", response_class=HTMLResponse)
async def generate_image_form():
    return """
    <html><body>
        <h2>Generate Image with OpenAI</h2>
        <form action="/generate-image" method="post">
            <input type="text" name="prompt" placeholder="Describe an image..." style="width:400px;" required />
            <button type="submit">Generate</button>
        </form>
        <br/>
        <a href="/">Back to Text Q&A</a><br/>
        <a href="/search-image">Go to Image Search</a>
    </body></html>
    """

@app.post("/generate-image", response_class=HTMLResponse)
async def generate_image_post(prompt: str = Form(...)):
    client = AzureOpenAI(
        azure_endpoint=OPENAI_AZURE_ENDPOINT,
        api_key=OPENAI_API_KEY,
        api_version=OPENAI_API_VERSION,
    )
    response = client.images.generate(
        prompt=prompt,
        model="dalle-3",
        size="1024x1024",
        n=1,
    )
    image_url = response.data[0].url

    return f"""
    <html><body>
        <h2>Prompt:</h2>
        <p>{prompt}</p>
        <h2>Generated Image:</h2>
        <img src="{image_url}" alt="Generated Image" style="max-width:512px;"/>
        <br/><br/>
        <a href="/generate-image">Generate another image</a><br/>
        <a href="/">Back to Text Q&A</a><br/>
        <a href="/search-image">Go to Image Search</a>
    </body></html>
    """


# Image search page using Azure Search + Blob SAS URL
@app.get("/search-image", response_class=HTMLResponse)
async def search_image_form():
    return """
    <html><body>
        <h2>Search for an Image</h2>
        <form action="/search-image" method="post">
            <input type="text" name="query" placeholder="Enter search text" style="width:1024px;" required />
            <button type="submit">Search</button>
        </form>
        <br/>
        <a href="/">Back to Text Q&A</a><br/>
        <a href="/generate-image">Go to Image Generation</a>
    </body></html>
    """

@app.post("/search-image", response_class=HTMLResponse)
async def search_image_post(query: str = Form(...)):
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )
    results = search_client.search(search_text=query, top=1)

    blob_name = None
    for r in results:
        blob_name = r.get("document_title")  # <-- Update if your field name differs
        break

    if not blob_name:
        return f"""
        <html><body>
            <h2>No results found for "{query}"</h2>
            <a href="/search-image">Try again</a><br/>
            <a href="/">Back to Text Q&A</a><br/>
            <a href="/generate-image">Go to Image Generation</a>
        </body></html>
        """

    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=BLOB_CONTAINER_NAME,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
    )
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{BLOB_CONTAINER_NAME}/{blob_name}?{sas_token}"

    return f"""
    <html><body>
        <h2>Search results for: "{query}"</h2>
        <img src="{blob_url}" alt="Search Result Image" style="max-width:512px;"/>
        <br/><br/>
        <a href="/search-image">Search again</a><br/>
        <a href="/">Back to Text Q&A</a><br/>
        <a href="/generate-image">Go to Image Generation</a>
    </body></html>
    """
