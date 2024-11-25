import os
from datetime import datetime
from typing import List, Dict
import requests
import base64
from llm_service import LLMService

class ImageGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.segmind.com/v1/stable-diffusion-3.5-turbo-txt2img"
        self.headers = {'x-api-key': api_key}
        
        # Create images directory if it doesn't exist
        os.makedirs('images', exist_ok=True)
        
    def generate_and_save_image(self, prompt: str, timestamp: str) -> str:
        """Generate image from prompt and save it"""
        data = {
            "prompt": prompt,
            "negative_prompt": "low quality, blurry, distorted, disfigured, bad anatomy",
            "steps": 4,
            "guidance_scale": 1,
            "seed": 98552302,
            "sampler": "dpmpp_2m",
            "scheduler": "sgm_uniform",
            "width": 1024,
            "height": 1024,
            "aspect_ratio": "custom",
            "batch_size": 1,
            "image_format": "jpeg",
            "image_quality": 95,
            "base64": True  # Get base64 response
        }
        
        try:
            response = requests.post(self.url, json=data, headers=self.headers)
            response.raise_for_status()
            
            # Decode base64 image
            image_data = base64.b64decode(response.json()['image'])
            
            # Create filename with timestamp
            filename = f"images/generated_{timestamp.replace(':', '')}.jpg"
            
            # Save image
            with open(filename, 'wb') as f:
                f.write(image_data)
                
            return filename
            
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None

class ChatSystem:
    def __init__(self, llm_api_key: str, image_api_key: str):
        """Initialize the chat system with LLM and Image Generation services"""
        try:
            self.llm = LLMService(api_key=llm_api_key)
            self.image_generator = ImageGenerator(api_key=image_api_key)
            self.conversation_history = []
            
            system_prompt = """You are a helpful AI assistant that provides responses with two components:
            1. Your message in <message> tags
            2. A detailed image prompt in <photo> tags suitable for image generation.
            
            Your <photo> descriptions should be highly detailed and optimized for Stable Diffusion image generation:
            - Focus on visual details, composition, and atmosphere
            - Include lighting, camera angle, and artistic style
            - Keep descriptions clear and coherent
            - Avoid complex narratives or abstract concepts
            - Include relevant artistic terms like "8k, detailed, realistic, cinematic lighting"
            
            Example format:
            <message>I'd be happy to help you with that!</message>
            <photo>A friendly AI assistant in a modern tech workspace, holographic displays with code floating around, sleek minimalist desk, ambient blue lighting, ray-traced reflections, volumetric lighting, 8k resolution, photorealistic, cinematic composition, ultra detailed</photo>"""
            
            self.llm.system_prompt = system_prompt
            self.llm.temperature = 0.9
            
        except Exception as e:
            print(f"Error initializing services: {e}")
            raise

    def extract_photo_prompt(self, response: str) -> str:
        """Extract photo prompt from response"""
        try:
            start = response.find('<photo>') + 7
            end = response.find('</photo>')
            if start > 6 and end > -1:
                return response[start:end].strip()
        except:
            pass
        return None

    def chat(self, user_message: str) -> Dict:
        """Process chat message, generate response and image"""
        try:
            if not user_message.strip():
                raise ValueError("Empty message")

            # Store user message
            self.conversation_history.append({
                'content': user_message,
                'isUser': True
            })

            # Get response from LLM service
            result = self.llm.get_response(user_message, self.conversation_history)

            if result.get('status') == 'error':
                raise Exception(result.get('error'))

            # Store assistant response
            self.conversation_history.append({
                'content': result['response'],
                'isUser': False
            })

            # Generate image from photo prompt
            timestamp = datetime.now().strftime("%H_%M_%S")
            photo_prompt = self.extract_photo_prompt(result['response'])
            
            if photo_prompt:
                image_path = self.image_generator.generate_and_save_image(
                    photo_prompt, 
                    timestamp
                )
                result['image_path'] = image_path

            return result

        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().strftime("%H:%M"),
                'status': 'error'
            }

def main():
    # Initialize chat system with both API keys
    llm_api_key = "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"
    image_api_key = "SG_998895e66d70f4ad"  # Replace with your Segmind API key
    
    chat_system = ChatSystem(llm_api_key, image_api_key)

    try:
        print("💫 AI Chat with Image Generation Initialized")
        print("Type 'exit', 'quit', or 'bye' to end the conversation")
        print("\n[Images will be saved to the 'images' folder]")
        
        while True:
            user_message = input("\n👤 You: ").strip()
            
            if user_message.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            result = chat_system.chat(user_message)

            if result['status'] == 'success':
                print(f"\n🤖 Assistant ({datetime.now().strftime('%H:%M')}):")
                print(f"\n💬 {result['response']}")
                
                if 'image_path' in result:
                    print(f"\n🎨 Generated image saved to: {result['image_path']}")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n\n👋 Chat session terminated by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()