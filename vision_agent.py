import subprocess
import base64
import logging
from PIL import Image
import io
import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionAgent:
    def __init__(self):
        logger.info("Loading LLaVA vision model...")
        
        # Use smaller LLaVA model for faster inference
        model_id = "llava-hf/llava-1.5-7b-hf"
        
        self.processor = AutoProcessor.from_pretrained(model_id)
        self.model = LlavaForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        
        logger.info("✅ Vision model loaded")
    
    def take_screenshot(self, filename="screenshot.png"):
        """Take screenshot of current screen"""
        try:
            # Use scrot on Linux
            subprocess.run(["scrot", filename], check=True)
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None
    
    def analyze_image(self, image_path, question="What do you see in this image?"):
        """Analyze image with LLaVA"""
        try:
            # Load image
            image = Image.open(image_path)
            
            # Prepare prompt
            prompt = f"USER: <image>\n{question}\nASSISTANT:"
            
            # Process
            inputs = self.processor(text=prompt, images=image, return_tensors="pt")
            
            # Move to same device as model
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    do_sample=False
                )
            
            # Decode
            response = self.processor.decode(outputs[0], skip_special_tokens=True)
            
            # Extract assistant response
            if "ASSISTANT:" in response:
                response = response.split("ASSISTANT:")[-1].strip()
            
            logger.info(f"Vision analysis: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return f"Error analyzing image: {e}"
    
    def see_screen(self, question="What's on the screen?"):
        """Take screenshot and analyze it"""
        screenshot = self.take_screenshot()
        
        if screenshot:
            return self.analyze_image(screenshot, question)
        else:
            return "Failed to capture screen"

# Test
if __name__ == "__main__":
    agent = VisionAgent()
    
    print("\nTaking screenshot and analyzing...")
    result = agent.see_screen("Describe what you see on this screen in detail")
    print(f"\nJARVIS sees: {result}")
