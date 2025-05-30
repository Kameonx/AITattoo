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
        .input-container {
            position: relative;
            margin-bottom: 1rem;
            width: 100%;
        }
        .upload-icon {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: rgba(120, 200, 255, 0.7);
            cursor: pointer;
            font-size: 1.5rem;
            transition: color 0.2s;
        }
        .upload-icon:hover {
            color: rgba(120, 200, 255, 1);
        }
        #file-input {
            display: none;
        }
        .image-preview {
            max-width: 200px;
            max-height: 200px;
            margin-bottom: 15px;
            border-radius: 8px;
            display: none;
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="container text-center">
        <div class="neon-container">
            <h1 class="mb-4">AI Tattoo Generator</h1>
            <div class="mb-4 input-container">
                <input type="text" class="form-control w-100" id="prompt" placeholder="Enter your image prompt...">
                <label for="file-input" class="upload-icon"><i class="fas fa-upload"></i></label>
                <input type="file" id="file-input" accept="image/*">
            </div>
            <img src="" alt="Preview" id="image-preview" class="image-preview">
            <div class="checkbox-bar-container">
                <div class="checkbox-bar">
                    <span class="checkbox-pair">
                        <input type="checkbox" id="tattoo-checkbox" class="neon-checkbox" checked>
                        <label for="tattoo-checkbox" class="checkbox-label">Tattoo</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="symmetrical-checkbox" class="neon-checkbox">
                        <label for="symmetrical-checkbox" class="checkbox-label">Symmetrical</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="anime-checkbox" class="neon-checkbox">
                        <label for="anime-checkbox" class="checkbox-label">Anime Style</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="letters-checkbox" class="neon-checkbox">
                        <label for="letters-checkbox" class="checkbox-label">Letters</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="watercolor-checkbox" class="neon-checkbox">
                        <label for="watercolor-checkbox" class="checkbox-label">Watercolor</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="geometric-checkbox" class="neon-checkbox">
                        <label for="geometric-checkbox" class="checkbox-label">Geometric</label>
                    </span>
                </div>
            </div>
            <button onclick="generateImage()" class="btn btn-primary px-4" id="generate-btn">Generate Image</button>
            
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
        let uploadedImage = null;

        document.getElementById('file-input').addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                const imgPreview = document.getElementById('image-preview');
                imgPreview.src = e.target.result;
                imgPreview.style.display = 'block';
                uploadedImage = e.target.result;
                
                // Focus the prompt input for easy submission
                document.getElementById('prompt').focus();
            };
            reader.readAsDataURL(file);
        });

        function generateImage() {
            const promptInput = document.getElementById('prompt').value.trim();
            if (!promptInput && !uploadedImage) {
                showError('Please enter a prompt or upload an image');
                return;
            }
            
            // Collect all checked styles
            const styleMap = [
                { id: 'tattoo-checkbox', label: 'tattoo' },
                { id: 'symmetrical-checkbox', label: 'symmetrical' },
                { id: 'anime-checkbox', label: 'anime style' },
                { id: 'letters-checkbox', label: 'letters' },
                { id: 'watercolor-checkbox', label: 'watercolor' },
                { id: 'geometric-checkbox', label: 'geometric' }
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
                    body: JSON.stringify({ 
                        prompt, 
                        seed,
                        image: uploadedImage
                    })
                })
                .then(res => res.json())
                .then((data) => {
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
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate_image():
    if request.json:
        prompt = request.json.get('prompt', '').strip()
        seed = request.json.get('seed')
        input_image = request.json.get('image')
    else:
        prompt = ''
        seed = None
        input_image = None

    # If an image is uploaded, use the Venice /image/upscale endpoint with enhancement
    if input_image:
        VENICE_UPSCALE_URL = "https://api.venice.ai/api/v1/image/upscale"
        # Only send the base64 part, not the data URL header
        if isinstance(input_image, str) and input_image.startswith('data:'):
            image_data = input_image.split(',', 1)[1]
        else:
            image_data = input_image

        # Compose the enhancePrompt from the prompt and checked styles
        enhance_prompt = prompt.strip() if prompt else ""
        # Optionally, you can always append "tattoo" if tattoo-checkbox is checked on the frontend
        # (the frontend already does this, so just use the prompt as received)

        payload = {
            "image": image_data,
            "enhance": True,
            "enhancePrompt": enhance_prompt if enhance_prompt else "tattoo",
            "scale": 1,
            "replication": 0.35,
            "enhanceCreativity": 0.5
        }
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        response = None
        try:
            response = requests.post(VENICE_UPSCALE_URL, json=payload, headers=headers, timeout=60)
            print("Venice API status:", response.status_code)
            print("Venice API response:", response.text[:200] + "..." if len(response.text) > 200 else response.text)
            response.raise_for_status()
            try:
                data = response.json()
                print("Response top-level keys:", list(data.keys()) if isinstance(data, dict) else "Not a dictionary")
            except Exception:
                print("Non-JSON response, treating as binary image.")
                image_bytes = response.content
                if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                    mime = "image/png"
                elif image_bytes[:2] == b'\xff\xd8':
                    mime = "image/jpeg"
                else:
                    mime = "application/octet-stream"
                b64 = base64.b64encode(image_bytes).decode()
                return jsonify({"image_urls": [f"data:{mime};base64,{b64}"]})
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

        # Extract image from response (if JSON)
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
            elif "image" in data and isinstance(data["image"], str):
                image_urls = [data["image"]]
            elif "url" in data and isinstance(data["url"], str):
                image_urls = [data["url"]]
        print("Extracted image URLs:", image_urls)
        if not image_urls or not any(url.startswith("http") or url.startswith("data:image") for url in image_urls):
            return jsonify({
                "error": "Image URL not found",
                "api_response": data
            }), 500
        return jsonify({"image_urls": image_urls})

    # If no image, use the normal text-to-image endpoint
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

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
        response.raise_for_status();
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
    if not image_urls:
        print("Primary extraction failed, trying fallback methods...")
        image_url = None;
        if "url" in data:
            image_url = data["url"]
        elif "image" in data:
            image_url = data["image"] if isinstance(data["image"], str) else None
        elif "image_url" in data:
            image_url = data["image_url"]
        elif "output" in data:
            output = data["output"]
            if isinstance(output, str):
                image_url = output
            elif isinstance(output, dict):
                image_url = output.get("url") or output.get("image_url") or output.get("image")
            elif isinstance(output, list) and output:
                first_item = output[0]
                if isinstance(first_item, str):
                    image_url = first_item
                elif isinstance(first_item, dict):
                    image_url = first_item.get("url") or first_item.get("image_url")
        elif "result" in data:
            result = data["result"]
            if isinstance(result, str):
                image_url = result
            elif isinstance(result, dict):
                image_url = result.get("url") or result.get("image_url") or result.get("image")
        elif "images" in data:
            images = data["images"]
            if isinstance(images, list) and images:
                first_image = images[0]
                if isinstance(first_image, str):
                    image_url = first_image
                elif isinstance(first_image, dict):
                    image_url = first_image.get("url")
            elif isinstance(images, str):
                image_url = images
            elif isinstance(images, dict):
                image_url = images.get("url")
        elif "data" in data:
            data_obj = data["data"]
            if isinstance(data_obj, str):
                image_url = data_obj
            elif isinstance(data_obj, dict):
                image_url = (data_obj.get("url") or data_obj.get("image_url") or data_obj.get("image"))
            elif isinstance(data_obj, list) and data_obj:
                first_item = data_obj[0]
                if isinstance(first_item, str):
                    image_url = first_item
                elif isinstance(first_item, dict):
                    image_url = first_item.get("url") or first_item.get("image_url")
        if image_url:
            image_urls = [image_url]

    print("Extracted image URLs:", image_urls)

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
                    png_data = base64.b64encode(png_file.read()).decode();
                    image_urls[idx] = f"data:image/png;base64,{png_data}"
                os.remove(jxl_path)
                os.remove(png_path)
            except Exception as e:
                print(f"JXL conversion failed: {e}")
                return jsonify({"error": "Failed to process image format"}), 500

    if not image_urls or not any(url.startswith("http") or url.startswith("data:image") for url in image_urls):
        return jsonify({
            "error": "Image URL not found",
            "api_response": data  # Debug data [REF]0
        }), 500

    return jsonify({"image_urls": image_urls})

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)
