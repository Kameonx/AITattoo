from flask import Flask, render_template_string, request, jsonify, make_response
import requests
import os
import base64
import subprocess
import tempfile
import random
import threading
import time

app = Flask(__name__)

VENICE_API_KEY = "06c-HIVdt8QNWkbgOh9d5RNgtWHPGweBJ8sbuM7s6e" 
VENICE_API_URL = "https://api.venice.ai/api/v1/image/generate" 

# CORS Headers Setup
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Tattoo Generator</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        html, body { 
            height: 100%; 
            background: #0f0f11; 
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .container { 
            max-width: 800px; 
            min-height: 100vh; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
        }
        .neon-container {
            background: rgba(15, 15, 22, 0.7);
            border-radius: 16px;
            padding: 30px;
            width: 90%;
            max-width: 700px;
            position: relative;
            border: 1px solid rgba(120, 130, 255, 0.3);
        }
        h1 {
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 1.5rem;
            text-shadow: 0 0 10px rgba(120, 200, 255, 0.7);
        }
        input, button { 
            border-radius: 8px; 
        }
        input[type="text"] { 
            background: #1a1a25; 
            color: white; 
            border: 1px solid rgba(80, 100, 255, 0.5); 
            padding: 12px;
            box-shadow: 0 0 10px rgba(80, 100, 255, 0.2);
            transition: all 0.3s ease;
        }
        input[type="text"]:focus {
            border-color: rgba(120, 200, 255, 0.8);
            box-shadow: 0 0 15px rgba(120, 200, 255, 0.4);
            outline: none;
        }
        /* Make placeholder text lighter and more visible */
        input[type="text"]::placeholder {
            color: rgba(255, 255, 255, 0.7);
            opacity: 1;
        }
        button { 
            background: linear-gradient(135deg, #4CAF50, #2E7D32); 
            color: white; 
            border: none; 
            padding: 12px 28px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.4);
        }
        button:hover {
            background: linear-gradient(135deg, #57c15b, #358f39);
            transform: translateY(-2px);
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.6);
        }
        .image-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 18px;
            justify-content: center;
            align-items: center;
            margin-top: 30px;
        }
        .image-slot {
            position: relative;
            min-width: 160px;
            min-height: 160px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #181828;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(120, 200, 255, 0.1);
            height: 100%;
        }
        .image-slot .spinner-border {
            z-index: 2;
        }
        .image-slot img {
            max-width: 320px;
            width: 100%;
            border-radius: 8px;
            display: block;
            background: #181828;
        }
        @media (max-width: 900px) {
            .image-grid { grid-template-columns: 1fr; grid-template-rows: repeat(4, 1fr);}
            .image-slot img { max-width: 98vw; }
        }
        @media (max-width: 600px) {
            .image-grid { grid-template-columns: 1fr; grid-template-rows: repeat(4, 1fr);}
            .image-slot img { max-width: 98vw; }
        }
        .loading { 
            display: none; 
            margin-top: 30px;
        }
        .spinner-border { 
            width: 3rem;
            height: 3rem;
            color: #4CAF50 !important;
            border: 0.25em solid #fff !important;
            border-right-color: transparent !important;
            border-radius: 50%;
            animation: spinner-border 0.75s linear infinite;
        }

        @keyframes spinner-border {
            0% {
                transform: rotate(0deg);
            }
            100% {
                transform: rotate(360deg);
            }
        }
        .checkbox-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px 18px;
            align-items: center;
            margin-bottom: 15px;
            justify-content: center;
            row-gap: 10px;
        }
        .checkbox-bar-container {
            width: 100%;
            max-width: 650px;
            margin: 0 auto 18px auto;
            padding: 8px 8px 4px 8px;
            border-radius: 10px;
            background: rgba(30, 30, 50, 0.85);
            border: 1.5px solid #222a38;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .checkbox-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 6px 10px;
            align-items: center;
            justify-content: center;
            width: 100%;
        }
        .checkbox-pair {
            display: flex;
            align-items: center;
            white-space: nowrap;
        }
        .neon-checkbox {
            margin-right: 2px;
            accent-color: #00ffe7;
            width: 16px;
            height: 16px;
            cursor: pointer;
        }
        .checkbox-label {
            color: #eafffa;
            text-shadow: 0 0 6px #00ffe7a0;
            font-size: 0.92rem;
            user-select: none;
            cursor: pointer;
            margin-right: 4px;
            margin-bottom: 0;
            letter-spacing: 0.01em;
            padding: 0 2px;
        }
        .rate-limit-info {
            margin: 10px 0;
            color: #aaffcc;
            font-size: 1.05rem;
            text-shadow: 0 0 4px #1f3;
        }
        .rate-limit-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 18px 0;
            flex-wrap: wrap;
            gap: 10px;
        }
        .reset-section {
            display: flex;
            align-items: center;
            gap: 8px;
            justify-content: flex-end;
        }
        .reset-section input[type="text"] {
            width: 120px;
            padding: 4px 8px;
            font-size: 0.98rem;
            border-radius: 6px;
            border: 1px solid #2a3040;
            background: rgba(15, 15, 22, 0.7);
            color: #666;
        }
        .reset-section input[type="text"]::placeholder {
            color: #555;
        }
        .reset-section button {
            padding: 4px 12px;
            font-size: 0.98rem;
            border-radius: 6px;
            background: #2e7d32;
            color: #fff;
            border: none;
            transition: background 0.2s;
        }
        .reset-section button:hover {
            background: #43a047;
        }
        .reset-message {
            color: #ffb300;
            font-size: 0.97rem;
            margin-left: 8px;
        }
    </style>
</head>
<body>
    <div class="container text-center">
        <div class="neon-container">
            <h1 class="mb-4">AI Tattoo Generator</h1>
            <div class="mb-4">
                <input type="text" class="form-control w-100" id="prompt" placeholder="Enter your image prompt...">
            </div>
            <div class="checkbox-bar-container">
                <div class="checkbox-bar">
                    <span class="checkbox-pair">
                        <input type="checkbox" id="tattoo-checkbox" class="neon-checkbox" checked>
                        <label for="tattoo-checkbox" class="checkbox-label">Tattoo</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="anime-checkbox" class="neon-checkbox">
                        <label for="anime-checkbox" class="checkbox-label">Anime</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="realism-checkbox" class="neon-checkbox">
                        <label for="realism-checkbox" class="checkbox-label">Realism</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="portrait-checkbox" class="neon-checkbox">
                        <label for="portrait-checkbox" class="checkbox-label">Portrait</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="colorful-checkbox" class="neon-checkbox">
                        <label for="colorful-checkbox" class="checkbox-label">Colorful</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="letters-checkbox" class="neon-checkbox">
                        <label for="letters-checkbox" class="checkbox-label">Letters</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="watercolor-checkbox" class="neon-checkbox">
                        <label for="watercolor-checkbox" class="checkbox-label">Watercolor</label>
                    </span>
                </div>
            </div>
            <button onclick="generateImage()" class="btn btn-primary px-4" id="generate-btn">Generate Image</button>
            
            <div class="rate-limit-container">
                <div class="rate-limit-info" id="rate-limit-info">
                    Generations left: <span id="generations-left">...</span> / 50
                </div>
                <div class="reset-section">
                    <input type="text" id="reset-code" placeholder="Enter code">
                    <button onclick="resetLimit()">Reset</button>
                    <span class="reset-message" id="reset-message"></span>
                </div>
            </div>
            
            <div class="loading" id="loading" style="margin-bottom:0;">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Generating your art...</p>
            </div>
            <div class="image-grid" id="image-grid"></div>
            <div id="error-message" class="text-danger mt-3"></div>
        </div>
    </div>
    <script>
        async function generateImage() {
            const promptInput = document.getElementById('prompt').value.trim();
            if (!promptInput) {
                showError('Please enter a prompt');
                return;
            }
            // Collect all checked styles
            const styleMap = [
                { id: 'tattoo-checkbox', label: 'tattoo' },
                { id: 'anime-checkbox', label: 'anime' },
                { id: 'realism-checkbox', label: 'realism' },
                { id: 'portrait-checkbox', label: 'portrait' },
                { id: 'colorful-checkbox', label: 'colorful' },
                { id: 'letters-checkbox', label: 'letters' },
                { id: 'watercolor-checkbox', label: 'watercolor' }
            ];
            let prompt = promptInput;
            styleMap.forEach(style => {
                const cb = document.getElementById(style.id);
                if (cb && cb.checked && style.label !== "tattoo") {
                    prompt += " " + style.label;
                }
            });
            // Always add "tattoo" if tattoo-checkbox is checked
            if (document.getElementById('tattoo-checkbox').checked) {
                prompt += " tattoo";
            }

            const imgGrid = document.getElementById('image-grid');
            const errorDiv = document.getElementById('error-message');
            const btn = document.getElementById('generate-btn');
            const loadingDiv = document.getElementById('loading');

            imgGrid.innerHTML = '';
            errorDiv.textContent = '';
            btn.disabled = true;
            loadingDiv.style.display = 'block';

            // Show 4 loading slots in a 2x2 grid
            const slots = [];
            for (let i = 0; i < 4; i++) {
                const slot = document.createElement('div');
                slot.className = 'image-slot';
                slot.innerHTML = '<div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div>';
                imgGrid.appendChild(slot);
                slots.push(slot);
            }

            // Make 4 requests, each with a random seed
            let completed = 0;
            for (let i = 0; i < 4; i++) {
                const seed = Math.floor(Math.random() * 2_000_000_000) - 1_000_000_000;
                fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, seed })
                })
                .then(res => res.json())
                .then(data => {
                    slots[i].innerHTML = '';
                    if (data.image_urls && Array.isArray(data.image_urls) && data.image_urls[0]) {
                        const img = document.createElement('img');
                        img.src = data.image_urls[0];
                        img.alt = "Generated Image";
                        img.onload = () => img.classList.remove('d-none');
                        img.onerror = () => showError('Image failed to load');
                        slots[i].appendChild(img);
                    } else if (data.image_url) {
                        const img = document.createElement('img');
                        img.src = data.image_url;
                        img.alt = "Generated Image";
                        img.onload = () => img.classList.remove('d-none');
                        img.onerror = () => showError('Image failed to load');
                        slots[i].appendChild(img);
                    } else {
                        slots[i].innerHTML = '<span style="color:#f66;">Error</span>';
                        showError(data.error || 'API error');
                    }
                })
                .catch(err => {
                    slots[i].innerHTML = '<span style="color:#f66;">Error</span>';
                    showError('Network error. Check console.');
                    console.error(err);
                })
                .finally(() => {
                    completed++;
                    if (completed === 4) {
                        loadingDiv.style.display = 'none';
                        btn.disabled = false;
                    }
                });
            }
        }
        function showError(msg) {
            document.getElementById('error-message').textContent = msg;
        }
        document.getElementById('prompt').addEventListener('keydown', e => {
            if (e.key === 'Enter') generateImage();
        });
        async function updateGenerationsLeft() {
            try {
                const res = await fetch('/rate_limit_status');
                const data = await res.json();
                document.getElementById('generations-left').textContent = data.generations_left;
                
                // Disable the generate button if no generations left
                const generateBtn = document.getElementById('generate-btn');
                generateBtn.disabled = data.generations_left <= 0;
            } catch (e) {
                document.getElementById('generations-left').textContent = '?';
            }
        }
        async function resetLimit() {
            const code = document.getElementById('reset-code').value.trim();
            const msg = document.getElementById('reset-message');
            msg.textContent = '';
            if (!code) {
                msg.textContent = 'Enter code';
                return;
            }
            try {
                const res = await fetch('/reset_limit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });
                const data = await res.json();
                if (data.success) {
                    msg.textContent = 'Reset successful!';
                    updateGenerationsLeft();
                } else {
                    msg.textContent = data.message || 'Reset failed';
                }
            } catch (e) {
                msg.textContent = 'Network error';
            }
        }
        // Update on load and after each generation
        updateGenerationsLeft();
        // Patch generateImage to update after generation
        const origGenerateImage = generateImage;
        generateImage = async function() {
            await origGenerateImage();
            updateGenerationsLeft();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# --- Simple in-memory rate limiter ---
RATE_LIMIT = 50  # max requests per hour per IP
rate_limit_data = {}
rate_limit_lock = threading.Lock()

def cleanup_rate_limit():
    """Background thread to clean up old IPs every hour."""
    while True:
        now = int(time.time())
        with rate_limit_lock:
            to_delete = [ip for ip, (count, ts) in rate_limit_data.items() if now - ts > 3600]
            for ip in to_delete:
                del rate_limit_data[ip]
        time.sleep(600)  # Clean up every 10 minutes

threading.Thread(target=cleanup_rate_limit, daemon=True).start()

def is_rate_limited(ip):
    now = int(time.time())
    with rate_limit_lock:
        count, ts = rate_limit_data.get(ip, (0, now))
        if now - ts > 3600:
            # Reset count if more than 1 hour passed
            rate_limit_data[ip] = (1, now)
            return False
        if count >= RATE_LIMIT:
            return True
        rate_limit_data[ip] = (count + 1, ts)
        return False

@app.route('/generate', methods=['POST'])
def generate_image():
    # --- Rate limiting ---
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if is_rate_limited(ip):
        return jsonify({"error": "Rate limit exceeded. Max 50 generations per hour."}), 429
    
    if request.json:
        prompt = request.json.get('prompt', '').strip()
        seed = request.json.get('seed')
    else:
        prompt = ''
        seed = None
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    # Add a random seed if provided, to ensure different generations
    payload = {
        "prompt": prompt,
        "model": "hidream",
        "format": "png",
        "return_binary": False,
        "safe_mode": True,
        "hide_watermark": True
    }
    if seed is not None:
        payload["seed"] = seed
    else:
        payload["seed"] = random.randint(-999_999_999, 999_999_999)

    headers = {
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }

    response = None
    try:
        response = requests.post(VENICE_API_URL, json=payload, headers=headers, timeout=60)
        print("Venice API status:", response.status_code)
        print("Venice API response:", response.text[:500] + "..." if len(response.text) > 500 else response.text)
        response.raise_for_status()
        data = response.json()
        print("Response top-level keys:", list(data.keys()) if isinstance(data, dict) else "Not a dictionary")
    except requests.exceptions.HTTPError as e:
        error_data = None
        if response is not None:
            try:
                error_data = response.json()
            except Exception:
                error_data = response.text
        return jsonify({
            "error": f"API request failed: {str(e)}",
            "api_response": error_data
        }), response.status_code if response is not None else 500
    except Exception as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500

    # Extract images from response according to API documentation
    image_urls = []
    if isinstance(data, dict):
        if "images" in data and isinstance(data["images"], list) and data["images"]:
            for base64_img in data["images"]:
                if isinstance(base64_img, str):
                    if base64_img.startswith("data:"):
                        base64_content = base64_img.split(",", 1)[1]
                    else:
                        base64_content = base64_img
                    image_urls.append(f"data:image/png;base64,{base64_content}")
    # If we still can't find an image, try the old extraction methods
    if not image_urls:
        print("Primary extraction failed, trying fallback methods...")
        # Direct URL in data
        if "url" in data:
            image_url = data["url"];
        elif "image" in data:
            image_url = data["image"] if isinstance(data["image"], str) else None;
        elif "image_url" in data:
            image_url = data["image_url"];
        # Venice API specific formats
        elif "output" in data:
            output = data["output"];
            if isinstance(output, str):  # Direct URL string
                image_url = output;
            elif isinstance(output, dict):
                image_url = output.get("url") or output.get("image_url") or output.get("image");
            elif isinstance(output, list) and output:  # List of URLs or objects
                first_item = output[0];
                if isinstance(first_item, str):
                    image_url = first_item;
                elif isinstance(first_item, dict):
                    image_url = first_item.get("url") or first_item.get("image_url");
        # Nested response formats
        elif "result" in data:
            result = data["result"];
            if isinstance(result, str):  # Direct URL string
                image_url = result;
            elif isinstance(result, dict):
                image_url = result.get("url") or result.get("image_url") or result.get("image");
        # List formats
        elif "images" in data:
            images = data["images"];
            if isinstance(images, list) and images:
                first_image = images[0];
                if isinstance(first_image, str):
                    image_url = first_image;
                elif isinstance(first_image, dict):
                    image_url = first_image.get("url");
            elif isinstance(images, str):
                image_url = images;
            elif isinstance(images, dict):
                image_url = images.get("url");
        # Data wrapper format
        elif "data" in data:
            data_obj = data["data"];
            if isinstance(data_obj, str):
                image_url = data_obj;
            elif isinstance(data_obj, dict):
                image_url = (data_obj.get("url") or data_obj.get("image_url") or
                            data_obj.get("image"));
            elif isinstance(data_obj, list) and data_obj:
                first_item = data_obj[0];
                if isinstance(first_item, str):
                    image_url = first_item;
                elif isinstance(first_item, dict):
                    image_url = first_item.get("url") or first_item.get("image_url");
    
    # Print the extracted URL for debugging
    print("Extracted image URLs:", image_urls);
    
    # Handle JXL format conversion for all images
    for idx, img_url in enumerate(image_urls):
        if img_url and img_url.startswith("data:image/jxl;base64"):
            try:
                jxl_data = base64.b64decode(img_url.split(',', 1)[1])
                with tempfile.NamedTemporaryFile(suffix='.jxl', delete=False) as jxl_file:
                    jxl_file.write(jxl_data)
                    jxl_path = jxl_file.name
                png_path = tempfile.mktemp(suffix='.png')
                subprocess.run(['djxl', jxl_path, png_path], check=True)
                with open(png_path, 'rb') as png_file:
                    png_data = base64.b64encode(png_file.read()).decode()
                    image_urls[idx] = f"data:image/png;base64,{png_data}"
                os.remove(jxl_path)
                os.remove(png_path);
            except Exception as e:
                print(f"JXL conversion failed: {e}")
                return jsonify({"error": "Failed to process image format"}), 500

    if not image_urls or not any(url.startswith("http") or url.startswith("data:image") for url in image_urls):
        return jsonify({
            "error": "Image URL not found",
            "api_response": data  # Debug data [REF]0
        }), 500;

    return jsonify({"image_urls": image_urls});

@app.route('/rate_limit_status', methods=['GET'])
def rate_limit_status():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    now = int(time.time())
    with rate_limit_lock:
        count, ts = rate_limit_data.get(ip, (0, now))
        if now - ts > 3600:
            count = 0
    return jsonify({
        "generations_left": max(0, RATE_LIMIT - count),
        "limit": RATE_LIMIT
    })

@app.route('/reset_limit', methods=['POST'])
def reset_limit():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    data = request.get_json(silent=True) or {}
    code = data.get('code', '')
    if code == 'Kameon':
        with rate_limit_lock:
            rate_limit_data[ip] = (0, int(time.time()))
        return jsonify({"success": True, "message": "Generations reset."})
    return jsonify({"success": False, "message": "Invalid code."}), 403

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000);
