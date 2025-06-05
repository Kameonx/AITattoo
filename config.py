import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# API Configuration
VENICE_API_KEY = os.environ.get("VENICE_API_KEY")
VENICE_API_URL = "https://api.venice.ai/api/v1/image/generate"
VENICE_UPSCALE_URL = "https://api.venice.ai/api/v1/image/upscale"

# Generation Configuration
DEFAULT_MODEL = 'hidream'
REQUEST_TIMEOUT = 120

# Available models from Venice AI API (image generation models)
AVAILABLE_MODELS = [
    {
        'id': 'hidream', 
        'name': 'HiDream (Default)', 
        'description': 'High quality realistic images - HiDream-I1-Dev'
    },
    {
        'id': 'venice-sd35', 
        'name': 'Venice SD 3.5', 
        'description': 'Stable Diffusion 3.5 Large - Default model'
    },
    {
        'id': 'flux-dev', 
        'name': 'Flux Dev', 
        'description': 'FLUX.1-dev - Highest quality generation'
    },
    {
        'id': 'flux-dev-uncensored', 
        'name': 'Flux Dev Uncensored', 
        'description': 'FLUX.1-dev uncensored version'
    },
    {
        'id': 'fluently-xl', 
        'name': 'Fluently XL', 
        'description': 'Fluently-XL-Final - Fastest generation'
    },
    {
        'id': 'stable-diffusion-3.5', 
        'name': 'Stable Diffusion 3.5', 
        'description': 'Stable Diffusion 3.5 Large'
    },
    {
        'id': 'pony-realism', 
        'name': 'Pony Realism', 
        'description': 'Most uncensored realistic model'
    },
    {
        'id': 'lustify-sdxl', 
        'name': 'Lustify SDXL', 
        'description': 'NSFW checkpoint model'
    }
]

def enhance_prompt_for_realism(prompt: str, variation_index: int = 0) -> str:
    """Enhanced prompt generation for high-quality realistic tattoos with dramatic variations."""
    realism_base = [
        "professional tattoo photograph",
        "high quality realistic tattoo on human skin",
        "masterpiece tattoo artwork",
        "photorealistic tattoo"
    ]
    
    quality_modifiers = [
        "ultra high definition",
        "professional photography",
        "crisp clean lines",
        "precise linework"
    ]
    
    # Simple style variations
    style_variations = [
        "traditional bold line tattoo style",
        "fine line minimalist tattoo style", 
        "realistic detailed tattoo style",
        "geometric pattern tattoo style"
    ]
    
    selected_style = style_variations[variation_index % 4]
    all_modifiers = realism_base + quality_modifiers + [selected_style]
    
    if "realistic tattoo" not in prompt.lower():
        prompt += ", " + ", ".join(all_modifiers)
    
    return prompt

# Negative prompts for variation
NEGATIVE_PROMPTS = [
    "anime, illustration, vector art, cartoon",
    "3D render, CGI, computer generated",
    "sketchy, unfinished, amateur, poor quality",
    "digital art, unrealistic, fake looking"
]

def create_text_to_image_payload(enhanced_prompt: str, model: str, variation_index: int, seed: Optional[int] = None) -> dict:
    """Create payload for Venice text-to-image API."""
    payload = {
        "model": model,
        "prompt": enhanced_prompt,
        "negative_prompt": NEGATIVE_PROMPTS[variation_index % 4],
        "width": 1024,
        "height": 1024,
        "steps": 20,
        "cfg_scale": 7.5,
        "format": "webp",
        "hide_watermark": True,
        "safe_mode": False,
        "embed_exif_metadata": False,
        "return_binary": False
    }
    
    if seed is not None:
        payload["seed"] = int(seed)
    else:
        import random
        payload["seed"] = random.randint(-999_999_999, 999_999_999)
    
    return payload

def create_upscale_payload(image_data: str, enhanced_prompt: str, variation_index: int) -> dict:
    """Create payload for Venice upscale API."""
    return {
        "image": image_data,
        "enhance": True,
        "enhancePrompt": enhanced_prompt,
        "scale": 1,
        "replication": 0.25 + (variation_index * 0.1),
        "enhanceCreativity": 0.15 + (variation_index * 0.1),
        "hide_watermark": True,
        "safe_mode": False
    }

def get_auth_headers() -> dict:
    """Get authorization headers for Venice API."""
    return {
        "Authorization": f"Bearer {VENICE_API_KEY}",
        "Content-Type": "application/json"
    }
