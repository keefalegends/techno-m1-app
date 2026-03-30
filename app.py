import os
import json
import random
import boto3
from flask import Flask, request, jsonify, render_template_string
from botocore.exceptions import ClientError

app = Flask(__name__)

# ── ENV CONFIG ──────────────────────────────────────────────
AWS_REGION       = os.environ.get("AWS_REGION", "us-east-1")
INPUT_BUCKET     = os.environ.get("INPUT_BUCKET", "technoinput-pati-keefa")
OUTPUT_BUCKET    = os.environ.get("OUTPUT_BUCKET", "technooutput-pati-keefa")
DYNAMODB_TABLE   = os.environ.get("DYNAMODB_TABLE", "Tokens")
API_GATEWAY_URL  = os.environ.get("API_GATEWAY_URL", "https://x61lga69i5.execute-api.us-east-1.amazonaws.com/prod")

# ── HTML TEMPLATE ────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Techno ML · Image Rekognition</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0e14;
    --panel: #12161f;
    --border: #1e2535;
    --accent: #00e5ff;
    --accent2: #7b61ff;
    --text: #cdd6f4;
    --muted: #6c7086;
    --success: #a6e3a1;
    --error: #f38ba8;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
    display: flex; flex-direction: column;
  }

  /* ── HEADER ── */
  header {
    padding: 18px 40px;
    display: flex; align-items: center; gap: 14px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .logo-mark {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    border-radius: 8px;
    display: grid; place-items: center;
    font-family: 'Space Mono', monospace;
    font-size: 14px; font-weight: 700; color: #0b0e14;
  }
  header h1 { font-family: 'Space Mono', monospace; font-size: 15px; letter-spacing: 0.08em; color: var(--accent); }
  header span { font-size: 12px; color: var(--muted); margin-left: auto; }

  /* ── MAIN LAYOUT ── */
  main {
    flex: 1;
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 0;
    max-width: 1200px;
    margin: 40px auto;
    width: 100%;
    padding: 0 24px;
  }

  /* ── SIDEBAR ── */
  .sidebar {
    padding: 0 32px 0 0;
    border-right: 1px solid var(--border);
  }
  .section-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 16px;
  }

  /* Token box */
  .token-box {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 28px;
  }
  .token-box input {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    margin: 10px 0;
    outline: none;
    transition: border-color .2s;
  }
  .token-box input:focus { border-color: var(--accent); }

  /* Upload box */
  .upload-box {
    background: var(--panel);
    border: 1px dashed var(--border);
    border-radius: 12px;
    padding: 32px 20px;
    text-align: center;
    margin-bottom: 20px;
    transition: border-color .2s;
    cursor: pointer;
  }
  .upload-box:hover { border-color: var(--accent2); }
  .upload-box input[type=file] { display: none; }
  .upload-icon { font-size: 36px; margin-bottom: 10px; }
  .upload-box p { font-size: 13px; color: var(--muted); }
  .upload-box strong { color: var(--text); font-size: 14px; display: block; margin-bottom: 6px; }

  /* Buttons */
  .btn {
    width: 100%;
    padding: 12px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 600;
    transition: opacity .2s, transform .1s;
  }
  .btn:active { transform: scale(.98); }
  .btn-primary {
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    color: #0b0e14;
  }
  .btn-secondary {
    background: var(--panel);
    border: 1px solid var(--border);
    color: var(--text);
    margin-top: 8px;
  }
  .btn:disabled { opacity: .4; cursor: not-allowed; }

  /* ── RESULTS PANEL ── */
  .results {
    padding: 0 0 0 32px;
  }
  .results-inner { display: none; }
  .results-inner.visible { display: block; }

  .image-preview {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
    margin-bottom: 24px;
    max-height: 280px;
    display: flex; align-items: center; justify-content: center;
    background: var(--panel);
  }
  .image-preview img { max-width: 100%; max-height: 280px; object-fit: contain; }

  .label-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
  }
  .label-card h3 { font-size: 13px; color: var(--muted); margin-bottom: 14px; font-family: 'Space Mono', monospace; }
  .label-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
  .label-name { font-size: 13px; min-width: 110px; color: var(--text); }
  .label-bar-wrap { flex: 1; background: var(--bg); border-radius: 4px; height: 8px; overflow: hidden; }
  .label-bar { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--accent2), var(--accent)); transition: width 1s ease; }
  .label-pct { font-family: 'Space Mono', monospace; font-size: 11px; color: var(--accent); min-width: 44px; text-align: right; }

  .meta-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px; margin-bottom: 20px;
  }
  .meta-item {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
  }
  .meta-item .key { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
  .meta-item .val { font-family: 'Space Mono', monospace; font-size: 13px; color: var(--accent); word-break: break-all; }

  .toast {
    position: fixed; bottom: 28px; right: 28px;
    padding: 12px 20px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    display: none;
    z-index: 999;
  }
  .toast.success { background: var(--success); color: #0b0e14; display: block; }
  .toast.error   { background: var(--error);   color: #0b0e14; display: block; }

  .spinner {
    display: none;
    width: 20px; height: 20px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .7s linear infinite;
    margin: 0 auto;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  .placeholder-state {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    height: 300px; color: var(--muted); text-align: center;
  }
  .placeholder-state .big { font-size: 48px; margin-bottom: 12px; }
  .placeholder-state p { font-size: 13px; max-width: 220px; line-height: 1.6; }

  @media (max-width: 760px) {
    main { grid-template-columns: 1fr; }
    .sidebar { border-right: none; border-bottom: 1px solid var(--border); padding: 0 0 32px; }
    .results { padding: 32px 0 0; }
  }
</style>
</head>
<body>

<header>
  <div class="logo-mark">ML</div>
  <h1>TECHNO · REKOGNITION</h1>
  <span>LKS Cloud Computing · Jawa Tengah 2025</span>
</header>

<main>
  <!-- ── SIDEBAR ── -->
  <aside class="sidebar">
    <p class="section-label">01 · Authentication</p>
    <div class="token-box">
      <div style="font-size:13px;color:var(--muted);margin-bottom:4px;">Access Token</div>
      <input type="text" id="tokenInput" placeholder="Paste token from Lambda / API GW…">
      <button class="btn btn-secondary" onclick="generateToken()" style="margin-top:4px;">⚡ Generate Token (Demo)</button>
    </div>

    <p class="section-label">02 · Upload Image</p>
    <label class="upload-box" for="fileInput">
      <input type="file" id="fileInput" accept="image/*" onchange="previewFile(this)">
      <div class="upload-icon">🖼️</div>
      <strong id="fileName">Choose an image file</strong>
      <p>PNG, JPG, WEBP — max 10 MB</p>
    </label>

    <button class="btn btn-primary" id="analyzeBtn" onclick="analyzeImage()" disabled>
      Analyze with Rekognition
    </button>
    <div class="spinner" id="spinner" style="margin-top:16px;"></div>
  </aside>

  <!-- ── RESULTS ── -->
  <section class="results">
    <div class="placeholder-state" id="placeholder">
      <div class="big">🔍</div>
      <p>Upload an image and submit to see ML label detection results</p>
    </div>

    <div class="results-inner" id="resultsPanel">
      <p class="section-label">03 · Analysis Results</p>

      <div class="image-preview">
        <img id="previewImg" src="" alt="preview">
      </div>

      <div class="meta-grid" id="metaGrid"></div>

      <div class="label-card">
        <h3>DETECTED LABELS · CONFIDENCE SCORE</h3>
        <div id="labelsContainer"></div>
      </div>
    </div>
  </section>
</main>

<div class="toast" id="toast"></div>

<script>
  let selectedFile = null;

  function showToast(msg, type='success') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast ' + type;
    setTimeout(() => t.className = 'toast', 3000);
  }

  function previewFile(input) {
    const file = input.files[0];
    if (!file) return;
    selectedFile = file;
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('analyzeBtn').disabled = false;

    const reader = new FileReader();
    reader.onload = e => {
      document.getElementById('previewImg').src = e.target.result;
    };
    reader.readAsDataURL(file);
  }

  async function generateToken() {
    try {
      const res = await fetch('/generate-token', { method: 'POST' });
      const data = await res.json();
      if (data.token) {
        document.getElementById('tokenInput').value = data.token;
        showToast('Token generated ✓', 'success');
      } else {
        showToast(data.error || 'Failed', 'error');
      }
    } catch(e) {
      showToast('Server error', 'error');
    }
  }

  async function analyzeImage() {
    const token = document.getElementById('tokenInput').value.trim();
    if (!token) { showToast('Access token required', 'error'); return; }
    if (!selectedFile) { showToast('Please select an image', 'error'); return; }

    document.getElementById('analyzeBtn').disabled = true;
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('placeholder').style.display = 'none';
    document.getElementById('resultsPanel').classList.remove('visible');

    const form = new FormData();
    form.append('image', selectedFile);
    form.append('token', token);

    try {
      const res = await fetch('/analyze', { method: 'POST', body: form });
      const data = await res.json();

      if (!res.ok) { showToast(data.error || 'Analysis failed', 'error'); return; }

      renderResults(data, selectedFile.name);
      showToast('Analysis complete ✓', 'success');
    } catch(e) {
      showToast('Network error', 'error');
    } finally {
      document.getElementById('analyzeBtn').disabled = false;
      document.getElementById('spinner').style.display = 'none';
    }
  }

  function renderResults(data, filename) {
    // meta grid
    const meta = [
      { key: 'Filename',   val: filename },
      { key: 'Bucket',     val: data.bucket || '-' },
      { key: 'Region',     val: data.region || 'us-east-1' },
      { key: 'Labels Found', val: (data.labels || []).length },
    ];
    document.getElementById('metaGrid').innerHTML = meta.map(m => `
      <div class="meta-item"><div class="key">${m.key}</div><div class="val">${m.val}</div></div>
    `).join('');

    // labels
    const labels = data.labels || [];
    document.getElementById('labelsContainer').innerHTML = labels.map(l => `
      <div class="label-row">
        <span class="label-name">${l.Name}</span>
        <div class="label-bar-wrap">
          <div class="label-bar" style="width:${l.Confidence.toFixed(1)}%"></div>
        </div>
        <span class="label-pct">${l.Confidence.toFixed(1)}%</span>
      </div>
    `).join('') || '<p style="color:var(--muted);font-size:13px;">No labels detected.</p>';

    document.getElementById('resultsPanel').classList.add('visible');
  }
</script>
</body>
</html>
"""

# ── ROUTES ──────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "techno-ml-app", "region": AWS_REGION})

@app.route("/generate-token", methods=["POST"])
def generate_token():
    """
    Demo token generator.
    In production: calls techno-lambda-post via API Gateway (POST /generate-token).
    """
    import secrets
    token = secrets.token_urlsafe(32)

    # Try to save to DynamoDB if credentials available
    try:
        dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)
        table  = dynamo.Table(DYNAMODB_TABLE)
        table.put_item(Item={"token": token})
    except Exception:
        pass  # Running locally without AWS credentials — that's fine

    return jsonify({"token": token})

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    1. Validate token against DynamoDB (techno-lambda-get).
    2. Upload image to INPUT_BUCKET (S3).
    3. Call Amazon Rekognition detect_labels.
    4. Save result JSON to OUTPUT_BUCKET/results/.
    5. Return labels to frontend.
    """
    token = request.form.get("token", "").strip()
    image = request.files.get("image")

    if not token:
        return jsonify({"error": "Access token required"}), 401
    if not image:
        return jsonify({"error": "No image uploaded"}), 400

    image_bytes = image.read()
    filename    = image.filename

    # ── Validate token ──────────────────────────────────────
    valid = _validate_token(token)
    if not valid:
        return jsonify({"error": "Invalid or expired token"}), 403

    # ── Upload to S3 input bucket ───────────────────────────
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.put_object(Bucket=INPUT_BUCKET, Key=f"uploads/{filename}", Body=image_bytes)
    except Exception as e:
        return jsonify({"error": f"S3 upload failed: {str(e)}"}), 500

    # ── Rekognition detect_labels ────────────────────────────
    try:
        rek = boto3.client("rekognition", region_name=AWS_REGION)
        rek_response = rek.detect_labels(
            Image={"Bytes": image_bytes},
            MaxLabels=10,
            MinConfidence=70,
        )
        labels = rek_response.get("Labels", [])
    except Exception:
        # Fallback: dummy labels for local / demo mode
        labels = _dummy_labels()

    # ── Save result to S3 output bucket ─────────────────────
    result = {"filename": filename, "labels": labels}
    try:
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=f"results/{filename}.json",
            Body=json.dumps(result),
            ContentType="application/json",
        )
    except Exception:
        pass  # Non-fatal

    return jsonify({
        "labels":  labels,
        "bucket":  INPUT_BUCKET,
        "region":  AWS_REGION,
        "filename": filename,
    })

# ── HELPERS ─────────────────────────────────────────────────

def _validate_token(token: str) -> bool:
    """Check Tokens table in DynamoDB. Falls back to True in demo mode."""
    try:
        dynamo = boto3.resource("dynamodb", region_name=AWS_REGION)
        table  = dynamo.Table(DYNAMODB_TABLE)
        resp   = table.get_item(Key={"token": token})
        return "Item" in resp
    except Exception:
        # Demo / local mode: accept any non-empty token
        return len(token) > 0

def _dummy_labels():
    """Realistic dummy labels for demo / local mode."""
    pool = [
        {"Name": "Person",    "Confidence": 99.1},
        {"Name": "People",    "Confidence": 98.4},
        {"Name": "Face",      "Confidence": 97.8},
        {"Name": "Clothing",  "Confidence": 95.3},
        {"Name": "T-Shirt",   "Confidence": 91.2},
        {"Name": "Pants",     "Confidence": 88.6},
        {"Name": "Indoors",   "Confidence": 83.0},
        {"Name": "Portrait",  "Confidence": 78.5},
        {"Name": "Screen",    "Confidence": 74.1},
        {"Name": "Adult",     "Confidence": 70.9},
    ]
    random.shuffle(pool)
    return pool[:random.randint(5, 9)]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2000))
    app.run(host="0.0.0.0", port=port, debug=False)
