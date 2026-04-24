"""
Image Generator Service - Featured image generation for blog posts.

Uses OpenAI DALL-E API to generate relevant featured images.
Constructs image prompts from blog content analysis.
"""

import os
from typing import Optional
from pathlib import Path

from src.config import OPENAI_API_KEY, DEFAULT_OUTPUT_DIR
from src.models.schemas import GeneratedImage

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class ImageGeneratorService:
    """
    Service for generating featured images using AI image APIs.
    
    Primary: OpenAI DALL-E 3
    Fallback: Save prompt for manual generation
    """
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.has_api_key = bool(self.api_key) and HAS_OPENAI
        
        if self.has_api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None
        else:
            self.client = None
    
    def generate_featured_image(self, blog_title: str, keywords: list, output_dir: str = None) -> Optional[GeneratedImage]:
        prompt = self._construct_prompt(blog_title, keywords)
        
        if not self.client:
            print("No OpenAI API key configured. Image prompt saved for manual generation.")
            return GeneratedImage(prompt=prompt, image_path=None, image_url=None)
        
        try:
            output_path = self._generate_image_file(prompt, blog_title, output_dir)
            return GeneratedImage(prompt=prompt, image_path=output_path, image_url=None)
        except Exception as e:
            print(f"Image generation failed: {e}")
            return GeneratedImage(prompt=prompt, image_path=None, image_url=None)
    
    def _construct_prompt(self, title: str, keywords: list) -> str:
        theme = title.split(':')[0].strip()
        visual_keywords = [k for k in keywords[:3] if len(k) > 3]
        
        base_prompt = f"A professional, modern illustration representing {theme}"
        
        if visual_keywords:
            elements = ", ".join(visual_keywords)
            base_prompt += f", incorporating elements of {elements}"
        
        style_modifiers = (
            "clean composition, vibrant but professional color palette, "
            "suitable for a technology blog header, wide aspect ratio, "
            "digital art style, high quality, no text, no logos"
        )
        
        return f"{base_prompt}. {style_modifiers}"
    
    def _generate_image_file(self, prompt: str, title: str, output_dir: str = None) -> str:
        import requests
        
        output_dir = Path(output_dir or DEFAULT_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        
        safe_name = self._sanitize_filename(title)
        image_path = output_dir / f"{safe_name}_featured.png"
        
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        return str(image_path)
    
    def _sanitize_filename(self, title: str) -> str:
        import re
        safe = re.sub(r'[^\w\s-]', '', title.lower())
        safe = re.sub(r'[-\s]+', '-', safe)
        return safe.strip('-')[:50]
