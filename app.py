from flask import Flask, render_template, request, jsonify
import requests
import base64
from config import (
    VENICE_API_KEY, VENICE_API_URL, VENICE_UPSCALE_URL, 
    DEFAULT_MODEL, REQUEST_TIMEOUT, AVAILABLE_MODELS,
    enhance_prompt_for_realism,
    create_upscale_payload, create_text_to_image_payload, get_auth_headers
)

app = Flask(__name__)

# CORS Headers Setup
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    return response

@app.route('/')
def index():
    print(f"Available models: {AVAILABLE_MODELS}")
    return render_template('index.html', models=AVAILABLE_MODELS)

@app.route('/generate', methods=['POST'])
def generate_image():
    if not request.json:
        return jsonify({"error": "Invalid request, JSON payload expected"}), 400
    
    prompt = request.json.get('prompt', '').strip()
    seed = request.json.get('seed')
    input_image = request.json.get('image')
    variation_index = request.json.get('variation_index', 0)
    model = request.json.get('model', DEFAULT_MODEL)

    print(f"Request: prompt='{prompt}', model='{model}', variation_index={variation_index}")

    # Enhance the prompt for realism with variation
    enhanced_prompt = enhance_prompt_for_realism(prompt, variation_index) if prompt else "realistic tattoo"

    # If an image is uploaded, use the Venice /image/upscale endpoint with enhancement
    if input_image:
        # Only send the base64 part, not the data URL header
        if isinstance(input_image, str) and input_image.startswith('data:'):
            image_data = input_image.split(',', 1)[1]
        else:
            image_data = input_image

        payload = create_upscale_payload(image_data, enhanced_prompt, variation_index)
        headers = get_auth_headers()
        
        try:
            response = requests.post(VENICE_UPSCALE_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception:
                # Handle binary response
                image_bytes = response.content
                if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                    mime = "image/png"
                elif image_bytes[:2] == b'\xff\xd8':
                    mime = "image/jpeg"
                else:
                    mime = "application/octet-stream"
                b64 = base64.b64encode(image_bytes).decode()
                return jsonify({"image_urls": [f"data:{mime};base64,{b64}"]})
        
        except Exception as e:
            return jsonify({"error": f"API request failed: {str(e)}"}), 500
        
        image_urls = []
        if 'data' in locals() and isinstance(data, dict):
            if "images" in data and isinstance(data["images"], list) and data["images"]:
                for base64_img in data["images"]:
                    if base64_img.startswith("data:"):
                        base64_content = base64_img.split(",", 1)[1]
                    else:
                        base64_content = base64_img
                    image_urls.append(f"data:image/png;base64,{base64_content}")
            elif "image" in data and isinstance(data["image"], str):
                image_urls = [data["image"]]
            elif "url" in data and isinstance(data["url"], str):
                image_urls = [data["url"]]
        
        if not image_urls:
            return jsonify({"error": "Image URL not found", "api_response": data if 'data' in locals() else None}), 500
        return jsonify({"image_urls": image_urls})

    # If no image, use the normal text-to-image endpoint
    else:
        if not prompt:
            return jsonify({"error": "Empty prompt"}), 400

        payload = create_text_to_image_payload(enhanced_prompt, model, variation_index, seed)
        headers = get_auth_headers()

        response = None
        try:
            response = requests.post(VENICE_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
            print(f"Venice API status: {response.status_code}")

            # Check for server errors first
            if response.status_code == 503:
                return jsonify({"error": "Venice API is temporarily unavailable. Please try again in a moment."}), 503
            elif response.status_code >= 500:
                return jsonify({"error": f"Venice API server error: {response.status_code}"}), 500

            response.raise_for_status()

            # Handle the response
            try:
                data = response.json()
                image_urls = []
                if isinstance(data, dict):
                    # Handle the new API response format
                    if "images" in data and isinstance(data["images"], list):
                        for img in data["images"]:
                            if isinstance(img, str):
                                try:
                                    # Validate base64
                                    base64.b64decode(img)
                                    # Use webp format as specified in payload
                                    image_urls.append(f"data:image/webp;base64,{img}")
                                except Exception as b64_error:
                                    print(f"Invalid base64 image: {b64_error}")
                    elif "image" in data and isinstance(data["image"], str):
                        try:
                            base64.b64decode(data["image"])
                            image_urls = [f"data:image/webp;base64,{data['image']}"]
                        except Exception as b64_error:
                            print(f"Invalid base64 image: {b64_error}")
                    elif "url" in data and isinstance(data["url"], str):
                        image_urls = [data["url"]]

                if image_urls:
                    return jsonify({"image_urls": image_urls})
                else:
                    print(f"No valid images found in response: {data}")
                    return jsonify({"error": "No valid images in API response", "api_response": data}), 500

            except Exception as ve:
                return jsonify({"error": str(ve)}), 500

        except requests.exceptions.HTTPError as e:
            try:
                error_json = response.json() if response is not None else {}
                error_message = error_json.get("error") or error_json
            except Exception:
                error_message = response.text if response is not None else str(e)
            print(f"Venice API error body: {error_message}")
            return jsonify({"error": f"Venice API error: {error_message}", "status_code": response.status_code if response is not None else None}), 500
        except Exception as e:
            print(f"Unexpected API Error: {str(e)}")
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
