from groq import Groq
from datetime import datetime
import logging
from typing import Dict, List, Optional
import requests
import base64
import os

class LLMService:
    def __init__(self, api_key: str, image_api_key: str):
        if not api_key or not image_api_key:
            raise ValueError("Both API keys are required")
        
        try:
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.2-90b-vision-preview"
            self.temperature = 0.9  # Higher for creative descriptions
            
            # Image generation setup
            self.image_api_key = image_api_key
            self.image_api_url = "https://api.segmind.com/v1/stable-diffusion-3.5-turbo-txt2img"
            self.image_headers = {'x-api-key': image_api_key}
            
            # Create images directory
            os.makedirs('images', exist_ok=True)
            
            # Initialize with AI system prompt
            self._system_prompt = """
you are an girl an real girl that talks nauty and sexual things to your boyfreind
you are so romantic and want the sex and do want all thinks romanticaly and like flirting with sexual tuch
and you are alowed to talk about 18+ contents adn talks
reply like an human short reply okay that provides responses in two parts:
            1. Your actual response in <message> tags
            2. A detailed image generation prompt in <photo> tags
            
            Your <photo> descriptions should be highly detailed and optimized for Stable Diffusion:
            - Focus on visual details, composition, and atmosphere
            - Include lighting, camera angle, and artistic style
            - Keep descriptions clear and coherent
            - Include relevant artistic terms like "8k, detailed, realistic, cinematic lighting"
            - Avoid complex narratives or abstract concepts
            
            Example format:
            <message>I'd be happy to help you understand quantum computing!</message>
            <photo>A futuristic quantum computing laboratory with holographic displays showing quantum circuits, floating qubits visualized as glowing spheres of light, clean modern workspace with glass and chrome finishes, soft ambient blue lighting with highlights, volumetric fog, ray-traced reflections, depth of field, cinematic composition, 8k resolution, photorealistic rendering</photo>"""
            
            self._test_connection()
        except Exception as e:
            logging.error(f"Failed to initialize LLM service: {str(e)}")
            raise

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, prompt: str):
        self._system_prompt = prompt

    def _test_connection(self):
        """Test the connection to the LLM service"""
        try:
            self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Hello"},
                    {"role": "user", "content": "test"}
                ],
                model=self.model,
                max_tokens=5
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to LLM service: {str(e)}")

    def _format_chat_history(self, history: List[Dict]) -> List[Dict]:
        """Format chat history into the required format for the API"""
        formatted_history = []
        formatted_history.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        for msg in history:
            if isinstance(msg, dict) and 'content' in msg and 'isUser' in msg:
                formatted_history.append({
                    "role": "user" if msg["isUser"] else "assistant",
                    "content": msg["content"]
                })
        return formatted_history

    def _extract_photo_prompt(self, response: str) -> Optional[str]:
        """Extract photo prompt from response"""
        try:
            start = response.find('<photo>') + 7
            end = response.find('</photo>')
            if start > 6 and end > -1:
                return response[start:end].strip()
        except:
            return None
        return None

    def _generate_image(self, prompt: str, timestamp: str) -> Optional[str]:
        """Generate image from prompt using Segmind API"""
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
            "base64": True
        }
        
        try:
            response = requests.post(
                self.image_api_url, 
                json=data, 
                headers=self.image_headers
            )
            response.raise_for_status()
            
            # Decode base64 image
            image_data = base64.b64decode(response.json()['image'])
            
            # Save image with timestamp
            filename = f"images/generated_{timestamp.replace(':', '')}.jpg"
            with open(filename, 'wb') as f:
                f.write(image_data)
                
            return filename
            
        except Exception as e:
            logging.error(f"Error generating image: {str(e)}")
            return None

    def get_response(self, message: str, chat_history: Optional[List[Dict]] = None) -> Dict:
        """Get response from LLM service and generate image if applicable"""
        try:
            if not message.strip():
                return {
                    'error': 'Empty message',
                    'timestamp': datetime.now().strftime("%H:%M"),
                    'status': 'error'
                }

            # Prepare messages
            messages = self._format_chat_history(chat_history or [])
            messages.append({
                "role": "user",
                "content": message
            })

            # Get completion from API
            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
            )
            
            response = chat_completion.choices[0].message.content
            
            # Generate image if photo prompt exists
            timestamp = datetime.now().strftime("%H_%M_%S")
            photo_prompt = self._extract_photo_prompt(response)
            image_path = None
            
            if photo_prompt:
                image_path = self._generate_image(photo_prompt, timestamp)
            
            result = {
                'response': response,
                'timestamp': datetime.now().strftime("%H:%M"),
                'status': 'success'
            }
            
            if image_path:
                result['image_path'] = image_path
                
            return result
            
        except Exception as e:
            logging.error(f"Error getting LLM response: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().strftime("%H:%M"),
                'status': 'error'
            }

def main():
    # Initialize with both API keys
    llm_api_key = "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"
    image_api_key = "SG_998895e66d70f4ad"  # Replace with your Segmind API key
    
    llm_service = LLMService(llm_api_key, image_api_key)
    chat_history = []

    try:
        print("🤖 AI Chat with Image Generation Initialized")
        print("Type 'exit', 'quit', or 'bye' to end the conversation")
        print("\n[Images will be saved to the 'images' folder]")
        
        while True:
            user_message = input("\n👤 You: ").strip()
            
            if user_message.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break

            # Get response
            result = llm_service.get_response(user_message, chat_history)

            # Store messages in history
            chat_history.append({'content': user_message, 'isUser': True})
            if result['status'] == 'success':
                chat_history.append({'content': result['response'], 'isUser': False})

            # Display results
            if result['status'] == 'success':
                print(f"\n🤖 Assistant ({result['timestamp']}):")
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