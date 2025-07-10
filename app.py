from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from fastapi.responses import StreamingResponse
from io import BytesIO
from PIL import Image
import httpx

app = FastAPI()

# --- Config ---

# OpenAI Azure endpoint and key
OPENAI_AZURE_ENDPOINT = "https://vijay15apr2.openai.azure.com/"
OPENAI_API_KEY = "9mJmzN7n9NFtvK2qLca4tb1DsD0DWVQGVmNRVbITVrfnwete4yZpJQQJ99BDACfhMk5XJ3w3AAABACOGiAbm"
OPENAI_API_VERSION = "2025-01-01-preview"

# Azure Search
SEARCH_ENDPOINT = "https://vijayaisearch.search.windows.net"
SEARCH_API_KEY = "Uu7vNqo3rOmsInCMiNzQKUgJF4UAVqZpfT5quZQ8qbAzSeBh2CGX"
SEARCH_INDEX_NAME = "captionindex"

# Azure Blob Storage
BLOB_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=vijayaistorage;AccountKey=hIZGQYe02nk9dOwfbU6iLdAV8Jq7WqJ/eyXohtcuc6036GhKEW5qwoQKOSFRY6FsyobWDjE+fCtR+AStgKVSzg==;EndpointSuffix=core.windows.net"
BLOB_CONTAINER_NAME = "vijayimagecontainer"

# --- Routes ---


# Home page: Text Q&A with OpenAI
@app.get("/", response_class=HTMLResponse)
async def text_qa_form():
    return """
    <html>
    <head>
        <title>Text Q&A</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="card p-4 shadow">
                <h2 class="mb-3">Text Q&A with OpenAI</h2>
                <form action="/" method="post" class="mb-3">
                    <div class="input-group">
                        <input type="text" name="question" class="form-control" placeholder="Ask something..." required />
                        <button class="btn btn-primary" type="submit">Ask</button>
                    </div>
                </form>
                <div class="d-flex gap-3">
                    <a href="/generate-image" class="btn btn-outline-secondary">Image Generation</a>
                    <a href="/search-image" class="btn btn-outline-secondary">Image Search</a>
                </div>
            </div>
        </div>
    </body>
    </html>
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
        azure_endpoint="https://vijay-mcswd6jl-australiaeast.cognitiveservices.azure.com/openai/deployments/dall-e-3/images/generations?api-version=2024-02-01/",
        api_key="8yz1IMGzHFZaAXZNNPx4FS7AyTm4cQJypzBBxKZCcOjXuwPmy6vYJQQJ99BGACL93NaXJ3w3AAAAACOGZHAw",
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
    <html>
    <head>
        <title>Image Search</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="card p-4 shadow">
                <h2>Search for an Image</h2>
                <form action="/search-image" method="post">
                    <div class="input-group mb-3">
                        <input type="text" name="query" class="form-control" placeholder="Enter search text..." required />
                        <button class="btn btn-primary" type="submit">Search</button>
                    </div>
                </form>
                <div class="d-flex gap-3">
                    <a href="/" class="btn btn-outline-secondary">Back to Q&A</a>
                    <a href="/generate-image" class="btn btn-outline-secondary">Image Generation</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/search-image", response_class=HTMLResponse)
async def search_image_post(query: str = Form(...)):
    # Search the AI search index using caption field
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_API_KEY),
    )

    results = search_client.search(search_text=query, top=1)

    image_url = None
    blob_name = None

    for r in results:
        image_url = r.get("image_url")
        print("*****************************")
        print(r)
        print("*****************************")
        blob_name = image_url.split("/")[-1].split("?")[0]  # extract blob name from URL
        break

    if not image_url:
        return f"""
        <html><body>
            <h2>No results found for*** "{image_url}"</h2>
            <a href="/search-image">Try again</a><br/>
            <a href="/">Back to Text Q&A</a><br/>
            <a href="/generate-image">Go to Image Generation</a>
        </body></html>
        """

    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2>Search results for: "{query}"</h2>
        <img src="{image_url}" alt="Search Result Image" style="max-width:512px; border: 1px solid #ccc;"/>
        <br/><br/>
        <a href="{image_url}" download="{blob_name}">
            <button style="margin-right:10px;">Download Image</button>
        </a>
        <a href="/download/jpeg/{blob_name}">
            <button style="margin-right:10px;">Download JPEG</button>
        </a>
        <a href="/download/tiff/{blob_name}">
            <button>Download TIFF</button>
        </a>
        <br/><br/>
        <a href="/search-image">Search again</a><br/>
        <a href="/">Back to Text Q&A</a><br/>
        <a href="/generate-image">Go to Image Generation</a>
    </body>
    </html>
    """



@app.get("/download/jpeg/{blob_name}")
async def download_jpeg(blob_name: str):
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

    async with httpx.AsyncClient() as client:
        response = await client.get(blob_url)
        response.raise_for_status()
        jpeg_bytes = response.content

    return StreamingResponse(BytesIO(jpeg_bytes), media_type="image/jpeg", headers={
        "Content-Disposition": f"attachment; filename={blob_name}"
    })


@app.get("/download/tiff/{blob_name}")
async def download_tiff(blob_name: str):
    # blob_name example: "image1.jpg"
    # We fetch the JPEG and convert to TIFF on the fly

    print("Inside TIFF")
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

    async with httpx.AsyncClient() as client:
        response = await client.get(blob_url)
        response.raise_for_status()
        jpeg_bytes = response.content

    # Convert JPEG bytes to TIFF in-memory
    img = Image.open(BytesIO(jpeg_bytes))
    tiff_bytes_io = BytesIO()
    img.save(tiff_bytes_io, format="TIFF")
    tiff_bytes_io.seek(0)

    tiff_filename = blob_name.rsplit(".", 1)[0] + ".tiff"

    return StreamingResponse(tiff_bytes_io, media_type="image/tiff", headers={
        "Content-Disposition": f"attachment; filename={tiff_filename}"
    })
