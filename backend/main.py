import os, time, base64, mimetypes, re
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import replicate

load_dotenv()
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')
if REPLICATE_API_TOKEN:
    os.environ['REPLICATE_API_TOKEN'] = REPLICATE_API_TOKEN

# instantiate replicate client
try:
    client = replicate.Client(api_token=REPLICATE_API_TOKEN) if REPLICATE_API_TOKEN else replicate.Client()
except Exception as e:
    print("Could not initialize Replicate client:", e)
    client = None

MODEL_REF = "black-forest-labs/flux-kontext-pro"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

def filebytes_to_data_uri(file_bytes: bytes, filename: str = None) -> str:
    mime_type, _ = (mimetypes.guess_type(filename) if filename else (None, None))
    if not mime_type:
        mime_type = "image/jpeg"
    b64 = base64.b64encode(file_bytes).decode('utf-8')
    return f"data:{mime_type};base64,{b64}"

_url_rx = re.compile(r"https?://[^\s'\"<>]+")

def extract_result_url(output):
    """
    Try many ways to get a usable URL from replicate output.
    Returns a string URL or raises RuntimeError.
    """
    # 1) str
    if isinstance(output, str):
        return output
    # 2) list-like
    if isinstance(output, (list, tuple)):
        if len(output) == 0:
            raise RuntimeError("Replicate output list empty")
        # prefer the last item
        out = output[-1]
        return extract_result_url(out)
    # 3) dict-like
    try:
        if hasattr(output, "get"):
            # common keys
            for key in ("image", "url", "output", "result"):
                val = output.get(key)
                if val:
                    return extract_result_url(val)
    except Exception:
        pass
    # 4) object with attributes (replicate objects sometimes)
    try:
        # try common attr names
        for attr in ("url", "image", "output"):
            if hasattr(output, attr):
                val = getattr(output, attr)
                if val:
                    return extract_result_url(val)
    except Exception:
        pass
    # 5) finally, try scraping any URL from the string representation
    s = str(output)
    m = _url_rx.search(s)
    if m:
        return m.group(0)
    raise RuntimeError(f"Unexpected replicate output structure: {output}")

@app.get("/api/health")
def health():
    return {"status":"ok"}

@app.post("/api/edit")
async def edit_image(image: UploadFile = File(...), prompt: str = Form("")):
    start = time.time()
    try:
        raw = await image.read()
        filename = getattr(image, 'filename', None)
        data_uri = filebytes_to_data_uri(raw, filename)

        inputs = {
            "prompt": prompt or "Make this a 90s cartoon",
            "input_image": data_uri,
            "output_format": "jpg"
        }

        if client is None:
            raise RuntimeError("Replicate client not initialized. Check REPLICATE_API_TOKEN.")

        # print("Sending job to Replicate (flux-kontext-pro)...")
        output = client.run(MODEL_REF, input=inputs)
        print("Replicate raw output:", output)

        # robustly extract a URL
        result_url = extract_result_url(output)
        print("Extracted result URL:", result_url)

        elapsed = time.time() - start
        
        # Return URL directly so frontend can load it
        return JSONResponse({"url": result_url, "elapsed": elapsed})

    except replicate.exceptions.ReplicateError as re:
        print("ReplicateError:", re)
        return JSONResponse({"error": f"Replicate error: {re}"}, status_code=500)
    except Exception as e:
        print("Error in /api/edit:", e)
        return JSONResponse({"error": str(e)}, status_code=500)