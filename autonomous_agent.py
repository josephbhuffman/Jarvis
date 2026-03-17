import pyautogui
import time
import logging
from vision_agent import VisionAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Safety: Enable fail-safe (move mouse to corner to abort)
pyautogui.FAILSAFE = True

class AutonomousAgent:
    def __init__(self):
        self.vision = VisionAgent()
        logger.info("✅ Autonomous agent initialized")
    
    def click(self, x, y):
        """Click at specific coordinates"""
        try:
            pyautogui.click(x, y)
            logger.info(f"🖱️ Clicked at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    def type_text(self, text):
        """Type text"""
        try:
            pyautogui.write(text, interval=0.1)
            logger.info(f"⌨️ Typed: {text}")
            return True
        except Exception as e:
            logger.error(f"Typing failed: {e}")
            return False
    
    def press_key(self, key):
        """Press a key (enter, tab, etc)"""
        try:
            pyautogui.press(key)
            logger.info(f"⌨️ Pressed: {key}")
            return True
        except Exception as e:
            logger.error(f"Key press failed: {e}")
            return False
    
    def find_and_click(self, target_description):
        """Use vision to find something and click it"""
        try:
            # Take screenshot and analyze
            logger.info(f"🔍 Looking for: {target_description}")
            
            screenshot_path = self.vision.take_screenshot()
            if not screenshot_path:
                return False
            
            # Ask vision AI to locate the target
            question = f"Where on the screen is {target_description}? Describe its exact position (top/bottom/left/right/center) and approximate coordinates if possible."
            
            result = self.vision.analyze_image(screenshot_path, question)
            logger.info(f"👁️ Vision says: {result}")
            
            # For now, return the description
            # In future: parse coordinates from result and click
            return result
            
        except Exception as e:
            logger.error(f"Find and click failed: {e}")
            return False
    
    def execute_task(self, task_description):
        """Execute a high-level task using vision + control"""
        logger.info(f"🤖 Executing task: {task_description}")
        
        # Take screenshot
        screenshot = self.vision.take_screenshot()
        if not screenshot:
            return "Failed to capture screen"
        
        # Ask vision AI what to do
        question = f"I want to: {task_description}. What do you see on screen that I should interact with? Describe the element and where it is located."
        
        analysis = self.vision.analyze_image(screenshot, question)
        
        logger.info(f"📋 Task analysis: {analysis}")
        return analysis
    
    def get_screen_info(self):
        """Get screen size and current mouse position"""
        screen_width, screen_height = pyautogui.size()
        mouse_x, mouse_y = pyautogui.position()
        
        return {
            'screen_width': screen_width,
            'screen_height': screen_height,
            'mouse_x': mouse_x,
            'mouse_y': mouse_y
        }

# Test
if __name__ == "__main__":
    agent = AutonomousAgent()
    
    print("\n=== Autonomous Agent Test ===")
    
    # Get screen info
    info = agent.get_screen_info()
    print(f"\nScreen: {info['screen_width']}x{info['screen_height']}")
    print(f"Mouse: ({info['mouse_x']}, {info['mouse_y']})")
    
    # Test vision + analysis
    print("\n--- Analyzing current screen ---")
    result = agent.execute_task("open a web browser")
    print(f"\nAgent sees: {result}")
