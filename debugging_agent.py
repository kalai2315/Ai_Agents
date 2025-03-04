import subprocess
import os
import google.generativeai as genai
import ast
import datetime
from dotenv import load_dotenv

# Load API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

def refine_manim_script(error_message, original_script):
    """
    Uses an LLM to refine the Manim script based on error messages.
    """
    model = genai.GenerativeModel("gemini-pro")  
    prompt = f"""
    I am using Manim to generate an animation, but my script has errors. 
    You MUST keep the scene class name as GeneratedManimScene.
    
    Here is the script:
    ```python
    {original_script}
    ```
    
    And here is the error message from Manim:
    ```
    {error_message}
    ```
    
    Please correct the script and ensure:
    1. Maintains 'class GeneratedManimScene(Scene):' 
    2. Has proper construct() method
    3. Returns valid Python code only
    """
    response = model.generate_content(prompt)
    # Add code extraction from response
    cleaned_script = response.text.strip()
    if "```python" in cleaned_script:  # Extract code block
        cleaned_script = cleaned_script.split("```python")[1].split("```")[0]
    elif "```" in cleaned_script:
        cleaned_script = cleaned_script.split("```")[1].split("```")[0]
    return cleaned_script

def validate_python_script(script):
    """Enhanced validation with scene class check"""
    try:
        parsed = ast.parse(script)
        # Check for required scene class
        has_scene_class = any(
            isinstance(node, ast.ClassDef) and 
            node.name == "GeneratedManimScene"
            for node in parsed.body
        )
        return has_scene_class
    except SyntaxError as e:
        print(f"Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"Validation Error: {e}")
        return False

def run_manim_code_agent(topic, max_attempts=3):
    """
    Generates a Manim script for the given topic, runs it, and refines it if errors occur.
    Stops retrying after max_attempts to prevent infinite loops.
    """
    try:
        # Step 1: Generate the initial script using Manim_code_agent.py
        subprocess.run(["python", "Manim_code_agent.py", topic], check=True)

        # Step 2: Define path for generated script
        script_path = "generated_manim_script.py"

        attempt = 0
        while attempt < max_attempts:
            print(f"Attempt {attempt + 1} of {max_attempts}")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create required directories if they don't exist
            os.makedirs("error_logs", exist_ok=True)
            os.makedirs("media/images/generated_manim_script", exist_ok=True)
            
            output_image = f"media/images/generated_manim_script/output_attempt_{attempt+1}_{timestamp}.png"
            error_log = f"error_logs/manim_error_{timestamp}.log"

            # Step 3: Run Manim and capture errors in a log file
            with open(error_log, "w") as error_file:
                result = subprocess.run([
                    "manim",
                    "-r", "3840,2160",  # Higher resolution for better quality
                    script_path,
                    "GeneratedManimScene",
                    "-s",
                    "--format=png",
                    "-o", output_image
                ], stderr=error_file, text=True)

            # Check if Manim executed successfully
            if result.returncode == 0:
                print(f"Manim script executed successfully! Output saved at {output_image}")
                # Add scoring after successful generation
                subprocess.run(["python", "score_manim_images.py", output_image, str(attempt+1)])
                return script_path, output_image

            print(f"Error detected. Logs saved at {error_log}, refining script...")

            with open(script_path, "r") as f:
                original_script = f.read()

            with open(error_log, "r") as f:
                error_message = f.read()

            # Step 4: Get refined script from LLM
            refined_script = refine_manim_script(error_message, original_script)

            # Step 5: Validate refined script before writing
            if refined_script.strip() == original_script.strip():
                print("LLM made no changes to the script. Stopping to prevent infinite loop.")
                break

            if not validate_python_script(refined_script):
                print("Refined script has syntax errors. Stopping refinement process.")
                break

            # Step 6: Save the refined script
            with open(script_path, "w") as f:
                f.write(refined_script)

            attempt += 1

        print("Max attempts reached. Manual debugging required.")
        return None, None

    except subprocess.CalledProcessError as e:
        print(f"Manim command failed: {e.stderr}")
        return None, None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, None

# Example usage
run_manim_code_agent("Pythagorean Theorem")
