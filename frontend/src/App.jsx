import { useState } from "react";
import axios from "axios";

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [prompt, setPrompt] = useState("");
  
  // We use resultUrl now, not resultB64
  const [resultUrl, setResultUrl] = useState(null);
  const [loading, setLoading] = useState(false);

  const onFile = (e) => {
    const f = e.target.files[0];
    setFile(f);
    setPreview(f ? URL.createObjectURL(f) : null);
    setResultUrl(null);
  };

  const run = async () => {
    if (!file) return alert("Upload an image first");
    setLoading(true);

    const fd = new FormData();
    fd.append("image", file);
    fd.append("prompt", prompt || "Cartoonify this photo in a 90s style");

    try {
      const res = await axios.post("https://ai-cartoon-api.onrender.com", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 180000, 
      });

      if (res.data.error) {
        alert("Backend Error: " + res.data.error);
      } else {
        // CAPTURE THE URL HERE
        console.log("Response URL:", res.data.url); // Check your browser console for this!
        setResultUrl(res.data.url);
      }
    } catch (err) {
      console.error(err);
      alert("Request to backend failed — check backend logs");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, fontFamily: "system-ui", maxWidth: 700 }}>
      <h2>Cartoonify (flux-kontext-pro)</h2>

      <input type="file" accept="image/*" onChange={onFile} />
      {preview && (
        <div style={{ marginTop: 12 }}>
          <div>Preview:</div>
          <img src={preview} alt="preview" style={{ maxWidth: "100%", borderRadius: 8 }} />
        </div>
      )}

      <div style={{ marginTop: 12 }}>
        <input
          placeholder="Prompt (e.g. '90s cartoon' or 'vibrant pastel cartoon')"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          style={{ width: "100%", padding: 8 }}
        />
      </div>

      <div style={{ marginTop: 12 }}>
        <button onClick={run} disabled={loading}>
          {loading ? "Processing (may take 10-60s)..." : "Run Cartoonify"}
        </button>
      </div>

      {/* RENDER THE URL DIRECTLY */}
      {resultUrl && (
        <div style={{ marginTop: 20 }}>
          <div>Result:</div>
          <img src={resultUrl} alt="result" style={{ maxWidth: "100%", borderRadius: 8 }} />
        </div>
      )}
    </div>
  );
}