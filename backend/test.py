# save as run_replicate.py
import replicate
import base64
import os
import requests
import mimetypes

from dotenv import load_dotenv
load_dotenv()  # now os.getenv('REPLICATE_API_TOKEN') will work


# Put your key here (you already did this in chat — replace if needed)
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

# Build client with token
client = replicate.Client(api_token=REPLICATE_API_TOKEN)

# local input image path (Windows)
local_image = r"C:\Users\karan\Downloads\WhatsApp Image 2025-11-28 at 3.30.43 PM.jpeg"

# convert to data URL (model accepts uri format like data:image/jpeg;base64,...)
def file_to_data_url(path):
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"

data_url = file_to_data_url(local_image)

inputs = {
    "prompt": "Make this a 90s cartoon",
    "input_image": data_url,        # data URL satisfies 'uri' format
    "output_format": "jpg"
}

# Run the model (use the same ref you used previously)
model_ref = "black-forest-labs/flux-kontext-pro"

print("Sending job to Replicate...")
output = client.run(model_ref, input=inputs)
print("Model output (raw):", output)

# output may be a URL or a list of URLs
if isinstance(output, list):
    url = output[-1]
elif isinstance(output, str):
    url = output
else:
    # try to extract URL if the model returned a dict-like structure
    try:
        url = output.get("image") or output.get("url") or output[0]
    except Exception:
        raise SystemExit("Unexpected output structure. See printed raw output above.")

print("Result URL:", url)

# Download and save
resp = requests.get(url, stream=True)
resp.raise_for_status()
with open("output.jpg", "wb") as f:
    for chunk in resp.iter_content(8192):
        f.write(chunk)
print("Saved output.jpg")
