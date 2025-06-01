from flask import Flask, render_template_string, request, jsonify, make_response
import requests
import os
import base64
import subprocess
import tempfile
import random
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VENICE_API_KEY = os.environ.get("VENICE_API_KEY")
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
        .model-selector-container {
            margin-bottom: 20px;
            width: 100%;
        }
        
        .model-selector {
            background: #1a1a25;
            color: white;
            border: 1px solid rgba(80, 100, 255, 0.5);
            border-radius: 8px;
            padding: 10px;
            width: 100%;
            box-shadow: 0 0 10px rgba(80, 100, 255, 0.2);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .model-selector:focus {
            border-color: rgba(120, 200, 255, 0.8);
            box-shadow: 0 0 15px rgba(120, 200, 255, 0.4);
            outline: none;
        }
        
        .model-selector option {
            background: #1a1a25;
            color: white;
        }
        
        .selector-label {
            display: block;
            margin-bottom: 8px;
            color: #eafffa;
            text-shadow: 0 0 6px #00ffe7a0;
            font-size: 0.95rem;
            text-align: left;
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
                        <input type="checkbox" id="geometric-checkbox" class="neon-checkbox">
                        <label for="geometric-checkbox" class="checkbox-label">Geometric</label>
                    </span>
                    <span class="checkbox-pair">
                        <input type="checkbox" id="traditional-checkbox" class="neon-checkbox">
                        <label for="traditional-checkbox" class="checkbox-label">Traditional</label>
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
            
            <div class="model-selector-container">
                <label for="model-selector" class="selector-label">AI Model:</label>
                <select id="model-selector" class="model-selector">
                    <option value="hidream" selected>HiDream (Default for Tattoos)</option>
                    <option value="venice-sd35">Venice SD 3.5</option>
                    <option value="stable-diffusion-3.5">Stable Diffusion 3.5</option>
                    <option value="fluently-xl">Fluently XL (Fast)</option>
                    <option value="flux-dev">FLUX Dev (High Quality)</option>
                    <option value="flux-dev-uncensored">FLUX Dev Uncensored</option>
                    <option value="pony-realism">Pony Realism</option>
                    <option value="lustify-sdxl">Lustify SDXL</option>
                </select>
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
            const selectedModel = document.getElementById('model-selector').value;
            
            // Collect all checked styles
            const styleMap = [
                { id: 'tattoo-checkbox', label: 'tattoo' },
                { id: 'symmetrical-checkbox', label: 'symmetrical' },
                { id: 'geometric-checkbox', label: 'geometric' },
                { id: 'traditional-checkbox', label: 'traditional' },
                { id: 'letters-checkbox', label: 'letters' },
                { id: 'watercolor-checkbox', label: 'watercolor' }
            ];

            // Get checked checkboxes
            const checkedStyles = styleMap.filter(style => {
                const cb = document.getElementById(style.id);
                return cb && cb.checked;
            });

            let prompt = promptInput;
            // If prompt is empty, build it from checked checkboxes
            if (!prompt) {
                prompt = checkedStyles.map(style => style.label).join(' ');
            } else {
                // If prompt is not empty, append checked styles (except tattoo, which is always appended if checked)
                checkedStyles.forEach(style => {
                    if (style.label !== "tattoo") {
                        prompt += " " + style.label;
                    }
                });
                // Always add "tattoo" if tattoo-checkbox is checked
                if (document.getElementById('tattoo-checkbox').checked) {
                    prompt += " tattoo";
                }
            }

            if (!prompt && !uploadedImage) {
                showError('Please enter a prompt or upload an image');
                return;
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

            // Make 4 requests, each with a random seed and different variation
            let completed = 0;
            for (let i = 0; i < 4; i++) {
                const seed = Math.floor(Math.random() * 2_000_000_000) - 1_000_000_000;
                fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        prompt, 
                        seed,
                        image: uploadedImage,
                        variation_index: i,  // Add variation index
                        model: selectedModel  // Add selected model
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

def enhance_prompt_for_realism(prompt: str, variation_index: int = 0) -> str:
    """
    Radically diversifies the tattoo designs by forcing entirely different
    compositions, perspectives, and artistic interpretations.
    """
    # Base realism modifiers that apply to all
    realism_base = [
        "realistic tattoo on human skin",
        "photograph of tattoo",
        "not digital art, not drawing, not cartoon"
    ]
    
    # Check for common subjects and force diversity
    prompt_lower = prompt.lower()
    
    # Subject-specific diversification
    if "dragon" in prompt_lower:
        dragon_variations = [
            "Eastern Chinese dragon long and sinuous with whiskers flying horizontally",
            "Western European dragon with large wings and upright posture breathing fire",
            "Tribal dragon abstract geometric pattern minimalist",
            "Japanese irezumi dragon with clouds and water elements full back piece"
        ]
        # Add the specific dragon variation to the prompt
        prompt = f"{prompt}, {dragon_variations[variation_index % 4]}"
    
    elif "flower" in prompt_lower or "floral" in prompt_lower:
        flower_variations = [
            "single detailed botanical illustration style flower",
            "scattered small flowers in cluster pattern",
            "large stylized flower with geometric elements",
            "flower with vines and leaves wrapping around limb"
        ]
        prompt = f"{prompt}, {flower_variations[variation_index % 4]}"
    
    elif "skull" in prompt_lower:
        skull_variations = [
            "anatomically detailed human skull front view",
            "sugar skull with decorative elements side profile",
            "animal skull with horns top-down view",
            "stylized geometric skull abstract interpretation"
        ]
        prompt = f"{prompt}, {skull_variations[variation_index % 4]}"
    
    # Force dramatically different composition styles per variation
    compositions = [
        # Force horizontal composition
        "horizontal composition, landscape oriented tattoo design, wrapped around arm",
        
        # Force vertical composition
        "vertical composition, portrait oriented tattoo design, spine placement",
        
        # Force circular composition
        "circular composition, radial balance, medallion style tattoo",
        
        # Force asymmetrical composition
        "asymmetrical composition, dynamic flow, organic placement"
    ]
    
    # Art style variations - much more dramatically different
    art_styles = [
        # Variation 0: Heavy Black Traditional
        [
            "heavy black traditional tattoo",
            "thick bold lines",
            "solid black fills",
            "high contrast work",
            "classic tattoo flash style",
            "traditional americana influence",
            "saturated black ink"
        ],
        
        # Variation 1: Fine Line Minimalist
        [
            "ultra fine line tattoo",
            "delicate micro linework",
            "minimalist design",
            "subtle single needle technique",
            "negative space utilization",
            "contemporary minimalism",
            "precision thin lines only"
        ],
        
        # Variation 2: Engraving/Woodcut
        [
            "engraving style tattoo",
            "woodcut technique",
            "crosshatching shading method",
            "etching art approach",
            "vintage illustration",
            "duplication of print methods",
            "textured line technique"
        ],
        
        # Variation 3: Textural Dotwork
        [
            "dotwork tattoo technique",
            "stippling shading method",
            "pointillism approach",
            "texture through dots",
            "gradient achieved with stippling",
            "high detail through dot density",
            "no lines, only dots"
        ]
    ]
    
    # Perspectives - force totally different angles
    perspectives = [
        "front view, centered composition, symmetrical layout",
        "side profile view, asymmetrical layout",
        "three-quarter angled perspective, dynamic composition",
        "top-down view, flattened perspective"
    ]
    
    # Select variations based on index
    variation_index = max(0, min(variation_index, 3))
    selected_art_style = art_styles[variation_index];
    selected_perspective = perspectives[variation_index];
    selected_composition = compositions[variation_index];
    
    # Style-specific modifications for checked options
    if "traditional" in prompt_lower:
        if variation_index == 0:
            selected_art_style.append("americana sailor jerry style")
        elif variation_index == 1:
            selected_art_style.append("japanese irezumi influence")
        elif variation_index == 2:
            selected_art_style.append("folk art traditional elements")
        else:
            selected_art_style.append("neo-traditional modern interpretation")
    
    if "watercolor" in prompt_lower:
        if variation_index == 0:
            selected_art_style.append("watercolor splashes contained within bold outlines")
        elif variation_index == 1:
            selected_art_style.append("subtle watercolor wash background only")
        elif variation_index == 2:
            selected_art_style.append("bleeding watercolor edges no containment")
        else:
            selected_art_style.append("watercolor drip technique with visible texture")
    
    # Combine modifiers with drastically different composition and perspective directives
    all_modifiers = realism_base + selected_art_style + [selected_composition, selected_perspective]
    
    # Only add if not already present in prompt
    if "realistic tattoo" not in prompt_lower and "real tattoo" not in prompt_lower:
        prompt += ", " + ", ".join(all_modifiers)
    
    return prompt

@app.route('/generate', methods=['POST'])
def generate_image():
    if request.json:
        prompt = request.json.get('prompt', '').strip()
        seed = request.json.get('seed')
        input_image = request.json.get('image')
        variation_index = request.json.get('variation_index', 0)
        # Get selected model with hidream as default
        model = request.json.get('model', 'hidream')
    else:
        prompt = ''
        seed = None
        input_image = None
        variation_index = 0
        model = 'hidream'

    # Enhance the prompt for realism with variation
    enhanced_prompt = enhance_prompt_for_realism(prompt, variation_index) if prompt else "realistic tattoo"

    # If an image is uploaded, use the Venice /image/upscale endpoint with enhancement
    if input_image:
        VENICE_UPSCALE_URL = "https://api.venice.ai/api/v1/image/upscale"
        # Only send the base64 part, not the data URL header
        if isinstance(input_image, str) and input_image.startswith('data:'):
            image_data = input_image.split(',', 1)[1]
        else:
            image_data = input_image

        # Use enhanced prompt for realism with variation
        payload = {
            "image": image_data,
            "enhance": True,
            "enhancePrompt": enhanced_prompt,
            "scale": 1,
            # Vary replication based on variation index for more diversity
            "replication": 0.25 + (variation_index * 0.1),
            # Vary creativity based on variation index
            "enhanceCreativity": 0.15 + (variation_index * 0.1)
        }
        headers = {
            "Authorization": f"Bearer {VENICE_API_KEY}",
            "Content-Type": "application/json"
        }
        response = None
        try:
            response = requests.post(VENICE_UPSCALE_URL, json=payload, headers=headers, timeout=60)
            print("Venice API status:", response.status_code)
            # Avoid accessing response.text for binary responses on Render.com
            content_type = response.headers.get("Content-Type", "") if response is not None else ""
            if response is not None and "application/json" in content_type:
                if hasattr(response, "text"):
                    print("Venice API response (JSON):", response.text[:200] + "..." if len(response.text) > 200 else response.text)
            elif response is not None:
                print("Venice API response (non-JSON, likely image): <binary content>")
            if response is not None:
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
            # Fixed syntax error - was curly braces instead of proper Python except syntax
            error_data = None
            # Fixed syntax error - was curly braces instead of proper Python except syntax
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

    # Apply dramatically different parameters based on variation index
    guidance_scales = [7.0, 9.0, 5.5, 8.0]  # More extreme differences
    cfg_scale = guidance_scales[variation_index % 4]
    
    # Removed style_strength parameter as it's not supported by Venice API
    
    payload = {
        "prompt": enhanced_prompt,
        "model": model,  # Use the selected model instead of hardcoded "hidream"
        "format": "png",
        "return_binary": False,
        "safe_mode": True,
        "hide_watermark": True,
        "cfg_scale": cfg_scale,  # Controls how closely to follow prompt
        # Different negative prompts for each variation
        "negative_prompt": [
            "cartoon, digital art, vibrant colors, bright colors, drawing, animation, similar designs, repetitive elements",
            "anime, illustration, vector art, flat colors, graphic design style, duplicated patterns, symmetry",
            "3D render, CGI, computer generated, perfect symmetry, clip art, generic design, standard template",
            "child's drawing, sketchy, unfinished, amateur, poor quality, stock design, common tattoo motifs"
        ][variation_index % 4]
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
    data = None
    try:
        response = requests.post(VENICE_API_URL, json=payload, headers=headers, timeout=60)
        print("Venice API status:", response.status_code)
        print("Venice API response:", response.text[:500])
        response.raise_for_status();
        data = response.json()
        print("Response top-level keys:", list(data.keys()) if isinstance(data, dict) else "Not a dictionary")
    except Exception as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500

    # Extract images from response according to API documentation
    image_urls = []
    if isinstance(data, dict):
        if "images" in data and isinstance(data["images"], list) and data["images"]:
            for img in data["images"]:
                if isinstance(img, str):
                    if img.startswith("data:"):
                        image_urls.append(img)
                    else:
                        image_urls.append(f"data:image/png;base64,{img}")
        elif "image" in data and isinstance(data["image"], str):
            image_urls = [data["image"]]
        elif "url" in data and isinstance(data["url"], str):
            image_urls = [data["url"]]
    print("Extracted image URLs:", image_urls)

    # Optionally handle JXL format conversion here if needed (not implemented in Python backend)

    return jsonify({"image_urls": image_urls})


if __name__ == '__main__':
    app.run(debug=True, threaded=True, port=5000)
