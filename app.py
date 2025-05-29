from flask import Flask, render_template_string, request, jsonify, make_response
import requests
import os
import base64
import subprocess
import tempfile

app = Flask(__name__)

VENICE_API_KEY = "-Y3up9vlEXoVFf1ZsrXhB4rbPXd8V6ywgiSZziI3bR"  # Replace with your actual key
VENICE_API_URL = "https://api.venice.ai/api/v1/image/generate"  # Correct endpoint

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
    <title>HiDream Image Generator</title>
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
            box-shadow: 
                0 0 10px rgba(80, 100, 255, 0.5),
                0 0 30px rgba(80, 100, 255, 0.3),
                0 0 60px rgba(130, 80, 255, 0.2);
            backdrop-filter: blur(5px);
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
        #generated-image { 
            max-width: 100%; 
            margin-top: 30px;
            border-radius: 8px;
            box-shadow: 0 0 20px rgba(120, 200, 255, 0.3);
        }
        .loading { 
            display: none; 
            margin-top: 30px;  /* Added space to avoid overlap */
        }
        .spinner-border { 
            width: 3rem; 
            height: 3rem;
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container text-center">
        <div class="neon-container">
            <h1 class="mb-4">HiDream Image Generator</h1>
            <div class="mb-4">
                <input type="text" class="form-control w-100" id="prompt" placeholder="Enter your image prompt...">
            </div>
            <button onclick="generateImage()" class="btn btn-primary px-4" id="generate-btn">Generate Image</button>
            <div class="loading" id="loading">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Generating your masterpiece...</p>
            </div>
            <img id="generated-image" src="" alt="Generated Image" class="mt-5 d-none">
            <div id="error-message" class="text-danger mt-3"></div>
        </div>
    </div>
    <script>
        async function generateImage() {
            const prompt = document.getElementById('prompt').value.trim();
            if (!prompt) {
                showError('Please enter a prompt');
                return;
            }

            const loadingDiv = document.getElementById('loading');
            const imgElement = document.getElementById('generated-image');
            const errorDiv = document.getElementById('error-message');
            const btn = document.getElementById('generate-btn');

            loadingDiv.style.display = 'block';
            imgElement.classList.add('d-none');
            errorDiv.textContent = '';
            btn.disabled = true;

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });

                const data = await response.json();

                if (data.image_url) {
                    imgElement.onload = () => imgElement.classList.remove('d-none');
                    imgElement.onerror = () => showError('Image failed to load');
                    imgElement.src = data.image_url;
                } else {
                    showError(data.error || 'API error');
                }
            } catch (err) {
                showError('Network error. Check console.');
                console.error(err);
            } finally {
                loadingDiv.style.display = 'none';
                btn.disabled = false;
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
    else:
        prompt = ''
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    # Update payload to match API documentation
    payload = {
        "prompt": prompt,
        "model": "hidream",
        "format": "png",  # Explicitly request PNG format
        "return_binary": False,  # We want base64 data
        "safe_mode": True,  # Optional: disable content filtering
        "hide_watermark": True  # Remove Venice watermark
    }

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
        # Try to return the API's error message if available
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

    # Extract image from response according to API documentation
    image_url = None
    
    if isinstance(data, dict):
        # According to documentation, the images field should contain base64 encoded data
        if "images" in data and isinstance(data["images"], list) and data["images"]:
            # Convert first base64 image to data URL
            base64_img = data["images"][0]
            if isinstance(base64_img, str):
                # For safety, remove any existing data URL prefix if present
                if base64_img.startswith("data:"):
                    # Extract just the base64 part
                    base64_content = base64_img.split(",", 1)[1]
                else:
                    base64_content = base64_img
                    
                # Create a proper data URL for the image (assuming PNG as requested)
                image_url = f"data:image/png;base64,{base64_content}"
                print("Created data URL from base64 image data")
    
    # If we still can't find an image, try the old extraction methods
    if not image_url:
        print("Primary extraction failed, trying fallback methods...")
        # Direct URL in data
        if "url" in data:
            image_url = data["url"]
        elif "image" in data:
            image_url = data["image"] if isinstance(data["image"], str) else None
        elif "image_url" in data:
            image_url = data["image_url"]
        # Venice API specific formats
        elif "output" in data:
            output = data["output"]
            if isinstance(output, str):  # Direct URL string
                image_url = output
            elif isinstance(output, dict):
                image_url = output.get("url") or output.get("image_url") or output.get("image")
            elif isinstance(output, list) and output:  # List of URLs or objects
                first_item = output[0]
                if isinstance(first_item, str):
                    image_url = first_item
                elif isinstance(first_item, dict):
                    image_url = first_item.get("url") or first_item.get("image_url")
        # Nested response formats
        elif "result" in data:
            result = data["result"]
            if isinstance(result, str):  # Direct URL string
                image_url = result
            elif isinstance(result, dict):
                image_url = result.get("url") or result.get("image_url") or result.get("image")
        # List formats
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
        # Data wrapper format
        elif "data" in data:
            data_obj = data["data"]
            if isinstance(data_obj, str):
                image_url = data_obj
            elif isinstance(data_obj, dict):
                image_url = (data_obj.get("url") or data_obj.get("image_url") or
                            data_obj.get("image"))
            elif isinstance(data_obj, list) and data_obj:
                first_item = data_obj[0]
                if isinstance(first_item, str):
                    image_url = first_item
                elif isinstance(first_item, dict):
                    image_url = first_item.get("url") or first_item.get("image_url")
    
    # Print the extracted URL for debugging
    print("Extracted image URL:", image_url)
    
    # Handle JXL format conversion
    if image_url and image_url.startswith("data:image/jxl;base64"):
        try:
            jxl_data = base64.b64decode(image_url.split(',', 1)[1])
            with tempfile.NamedTemporaryFile(suffix='.jxl', delete=False) as jxl_file:
                jxl_file.write(jxl_data)
                jxl_path = jxl_file.name
            png_path = tempfile.mktemp(suffix='.png');

            subprocess.run(['djxl', jxl_path, png_path], check=True);

            with open(png_path, 'rb') as png_file:
                png_data = base64.b64encode(png_file.read()).decode();
                image_url = f"data:image/png;base64,{png_data}";

            os.remove(jxl_path);
            os.remove(png_path);
        except Exception as e:
            print(f"JXL conversion failed: {e}")
            return jsonify({"error": "Failed to process image format"}), 500

    if not image_url or (not image_url.startswith("http") and not image_url.startswith("data:image")):
        return jsonify({
            "error": "Image URL not found",
            "api_response": data  # Debug data [REF]0
        }), 500

    return jsonify({"image_url": image_url})

if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)