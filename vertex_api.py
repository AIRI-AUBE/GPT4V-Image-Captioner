"""
Vertex AI API integration for GPT4V-Image-Captioner
Based on Google Generative AI (Vertex AI) for image captioning
"""
from google import genai
from google.genai import types
import base64
import os
import json
from typing import List, Tuple, Optional, Union
from PIL import Image
import io
import requests


class VertexAIClient:
    def __init__(self, service_account_path: str = None, project_id: str = None, location: str = "us-central1"):
        """
        Initialize Vertex AI client
        
        Args:
            service_account_path: Path to service account JSON file
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
        """
        self.service_account_path = service_account_path
        self.project_id = project_id
        self.location = location
        self.client = None
        self.model = "gemini-2.0-flash-exp"
        
        # Default prompt for image captioning
        self.default_prompt = """As an AI image tagging expert, please provide precise tags for these images to enhance CLIP model's understanding of the content. Employ succinct keywords or phrases, steering clear of elaborate sentences and extraneous conjunctions. Prioritize the tags by relevance. Your tags should capture key elements such as the main subject, setting, artistic style, composition, image quality, color tone, filter, and camera specifications, and any other tags crucial for the image. When tagging photos of people, include specific details like gender, nationality, attire, actions, pose, expressions, accessories, makeup, composition type, age, etc. For other image categories, apply appropriate and common descriptive tags as well. Recognize and tag any celebrities, well-known landmark or IPs if clearly featured in the image. Your tags should be accurate, non-duplicative, and within a 20-75 word count range. These tags will use for image re-creation, so the closer the resemblance to the original image, the better the tag quality. Tags should be comma-separated. Exceptional tagging will be rewarded with $10 per image."""
        
    def initialize_client(self):
        """Initialize the Vertex AI client with authentication"""
        try:
            # 1) Resolve service account path
            sa_path = self.service_account_path
            if not sa_path:
                # Prefer env var if set, else look for ./service_account.json next to this file
                sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                default_sa = os.path.join(os.path.dirname(__file__), "service_account.json")
                if not sa_path and os.path.exists(default_sa):
                    sa_path = default_sa

            if sa_path and os.path.exists(sa_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_path
                # If project_id not provided, try to read from service account file
                if not self.project_id:
                    try:
                        with open(sa_path, "r", encoding="utf-8") as f:
                            sa = json.load(f)
                        pj = sa.get("project_id") or sa.get("projectId")
                        if pj:
                            self.project_id = pj
                    except Exception:
                        pass

            # If still no project_id, fall back to env var
            if not self.project_id:
                self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")

            # Propagate project to env for downstream libs, if we have it
            if self.project_id:
                os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id

            # 2) Build client with explicit project/location when available
            client_kwargs = {"vertexai": True}
            if self.project_id:
                client_kwargs["project"] = self.project_id
            if self.location:
                client_kwargs["location"] = self.location

            self.client = genai.Client(**client_kwargs)
            return True
        except Exception as e:
            print(f"Failed to initialize Vertex AI client: {e}")
            return False
    
    def process_image(self, image_input: Union[str, Image.Image]) -> str:
        """
        Process image input and convert to base64 format
        
        Args:
            image_input: Image path (str), URL (str), or PIL Image object
            
        Returns:
            Base64 encoded image string
        """
        try:
            if isinstance(image_input, str):
                # URL
                if image_input.startswith("http://") or image_input.startswith("https://"):
                    response = requests.get(image_input)
                    image_data = response.content
                    pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
                # Base64
                elif image_input.startswith("data:image/"):
                    base64_data = image_input.split(",")[1]
                    image_data = base64.b64decode(base64_data)
                    pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
                # File path
                else:
                    pil_image = Image.open(image_input).convert('RGB')
            # PIL Image
            elif isinstance(image_input, Image.Image):
                pil_image = image_input.convert('RGB')
            else:
                raise ValueError("Unsupported image input type")
            
            # Convert to base64
            buffer = io.BytesIO()
            pil_image.save(buffer, format="JPEG", quality=85)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            raise ValueError(f"Error processing image: {e}")
    
    def generate_caption(self, image_path: str, prompt: str = None, 
                        temperature: float = 1.0, max_tokens: int = 1024) -> str:
        """
        Generate caption for a single image using Vertex AI
        
        Args:
            image_path: Path to the image file or image URL
            prompt: Custom prompt for captioning (optional)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated caption text
        """
        if not self.client:
            if not self.initialize_client():
                return "Error: Failed to initialize Vertex AI client"
        
        try:
            # Process image
            image_base64 = self.process_image(image_path)
            
            # Use custom prompt or default
            text_prompt = prompt if prompt else self.default_prompt
            
            # Create message parts
            msg_text = types.Part.from_text(text=text_prompt)
            msg_image = types.Part.from_bytes(
                data=base64.b64decode(image_base64),
                mime_type="image/jpeg",
            )
            
            # Create content
            contents = [
                types.Content(
                    role="user",
                    parts=[msg_text, msg_image]
                ),
            ]
            
            # Generate content config
            generate_config = types.GenerateContentConfig(
                temperature=temperature,
                top_p=0.95,
                seed=0,
                max_output_tokens=max_tokens,
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="OFF"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="OFF"
                    )
                ],
            )
            
            # Generate response
            response_text = ""
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_config,
            ):
                response_text += chunk.text
            
            return response_text.strip()
            
        except Exception as e:
            return f"API error: {str(e)}"
    
    def batch_generate_captions(self, image_paths: List[str], prompt: str = None,
                              temperature: float = 1.0, max_tokens: int = 1024) -> List[Tuple[str, str]]:
        """
        Generate captions for multiple images
        
        Args:
            image_paths: List of image file paths
            prompt: Custom prompt for captioning
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens per caption
            
        Returns:
            List of tuples (image_path, caption)
        """
        results = []
        for image_path in image_paths:
            caption = self.generate_caption(image_path, prompt, temperature, max_tokens)
            results.append((image_path, caption))
        return results


def run_vertex_ai_api(image_path: str, prompt: str, service_account_path: str = None, 
                     project_id: str = None, quality: str = "auto", timeout: int = 30, 
                     model: str = "gemini-2.0-flash-exp") -> str:
    """
    Main function to run Vertex AI API for image captioning
    Compatible with the existing API structure in the project
    
    Args:
        image_path: Path to the image file
        prompt: Text prompt for captioning
        service_account_path: Path to service account JSON (used as api_key equivalent)
        project_id: Google Cloud project ID (used as api_url equivalent)  
        quality: Image quality (maintained for compatibility)
        timeout: Request timeout (maintained for compatibility)
        model: Model name to use
        
    Returns:
        Generated caption or error message
    """
    try:
        # Initialize client
        client = VertexAIClient(service_account_path, project_id)
        
        # Generate caption
        caption = client.generate_caption(
            image_path=image_path,
            prompt=prompt,
            temperature=1.0,
            max_tokens=1024
        )
        
        return caption
        
    except Exception as e:
        return f"Vertex AI API error: {str(e)}"


# Configuration helper functions
def save_vertex_config(service_account_path: str, project_id: str, location: str = "us-central1"):
    """Save Vertex AI configuration to a JSON file"""
    config = {
        "service_account_path": service_account_path,
        "project_id": project_id,
        "location": location
    }
    
    config_path = os.path.join(os.path.dirname(__file__), "vertex_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path


def load_vertex_config():
    """Load Vertex AI configuration from JSON file"""
    config_path = os.path.join(os.path.dirname(__file__), "vertex_config.json")

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding="utf-8") as f:
            return json.load(f)

    # Fallback: auto-detect service_account.json and project_id
    sa_path = os.path.join(os.path.dirname(__file__), "service_account.json")
    project_id = ""
    if os.path.exists(sa_path):
        try:
            with open(sa_path, "r", encoding="utf-8") as f:
                sa = json.load(f)
            project_id = sa.get("project_id") or sa.get("projectId") or ""
        except Exception:
            pass

    return {
        "service_account_path": sa_path if os.path.exists(sa_path) else "",
        "project_id": project_id,
        "location": "us-central1"
    }


def vertex_api_switch(api_name: str = "vertex-ai") -> str:
    """
    Switch to Vertex AI API mode
    Compatible with existing API switching mechanism
    """
    return "Vertex AI"


# Test function
def test_vertex_api():
    """Test function for Vertex AI integration"""
    # Load configuration
    config = load_vertex_config()
    
    if not config.get("service_account_path") or not config.get("project_id"):
        print("Please configure Vertex AI credentials using save_vertex_config()")
        return
    
    # Test with a sample image (you can replace with an actual image path)
    test_prompt = "Describe this image in detail."
    
    # Note: Replace with actual image path for testing
    # result = run_vertex_ai_api("test_image.jpg", test_prompt, 
    #                           config["service_account_path"], 
    #                           config["project_id"])
    # print(f"Test result: {result}")
    
    print("Vertex AI configuration loaded successfully")
    print(f"Service Account: {config['service_account_path']}")
    print(f"Project ID: {config['project_id']}")


if __name__ == "__main__":
    test_vertex_api()