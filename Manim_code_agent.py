import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from Topic_analysis_agent import TopicAnalysisAgent
from visual_plan_agent import VisualPlanAgent, VisualPlan, ManimObject
from manim import *

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

class VisualPlan(BaseModel):
    Topic: str
    Description: str
    ManimObjects: List[str]  
    Animations: List[str] = []
    #Labels: List[str]


class ManimCode(BaseModel):
    Code: str
    Description: str

MANIM_CODE_SYSTEM_PROMPT = """
You are a Manim Code Generation Agent. Your task is to generate valid Python code using the Manim library for static visualizations.  
Follow these guidelines to ensure high-quality output:  

### **1. Code Structure:**  
- Generate a Manim Scene class (class MyScene(Scene):) as the foundation.  
- Ensure the code follows standard Manim syntax and structure. 
- **The output MUST contain a Manim Scene class (class MyScene(Scene):).**
- The Scene class should include:
  - Object creation
  - Static labels & formulas 

### **2. Object Creation:**  
- Create necessary Manim objects based on the visual plan.  
- Supported objects: Circle, Square, Line, NumberPlane, Tex (text), Axes, Graphs, etc.  

### **3. Static Visualization:**  
- Implement static visualizations without animations.
- Use Add() or Display() to show objects without dynamic changes.

### **4. Text and Labels:**  
- Add text annotations and mathematical formulas using Tex() or MathTex().  
- Position labels clearly to enhance readability.  

### **5. Formatting & Readability:**  
- Include meaningful **comments** explaining different sections of the code.  
- Ensure proper indentation and spacing for readability.  
- The output must be clean and executable without errors. 

### **6. Grid Lines:**  
- By default, do not include grid lines in the NumberPlane unless specified in the visual plan.
- If grid lines are necessary, ensure they do not clutter the visualization.


### ** Chain-of-Thought Prompting:**
- Think through the code structure step-by-step.
- Consider how each part of the visual plan translates into static Manim code.
- Ensure the code is logically organized and executable.

### ** Few-Shot Learning Examples:**

#### **Example 1: Equality of Vectors**
**Visual Plan:**
Topic: Equality of Vectors
Description: \"""This visualization demonstrates the concept of vector equality. 
Two vectors of the same magnitude and direction are shown at different positions on a coordinate plane. 
The animation includes labeled vectors, a reference coordinate system, 
and a concluding annotation explaining that the vectors are equal.\"""
Objects: Circle, Text, vectors, MathTex

**Generated Manim Code:**
python

from manim import *

class EqualVectors(Scene):
    def construct(self):
        # Title
        title = Text("Equality of Vectors", font_size=36).to_edge(UP)
        self.add(title)

        # Create axes for reference
        axes = Axes(x_range=[-5, 5, 1], y_range=[-3, 3, 1], axis_config={"color": GREY})
        self.add(axes)

        # Define two equal vectors (same magnitude and direction)
        vector_1 = Vector([2, 1], color=BLUE).shift(LEFT * 3)  # Position 1
        vector_2 = Vector([2, 1], color=BLUE).shift(RIGHT * 2)  # Position 2

        # Labels for vectors
        label_1 = MathTex("\\vec{A}").next_to(vector_1, UP).set_color(BLUE)
        label_2 = MathTex("\\vec{B}").next_to(vector_2, UP).set_color(BLUE)

        # Add vectors to the scene
        self.add(GrowArrow(vector_1), FadeIn(label_1))
        self.add(GrowArrow(vector_2), FadeIn(label_2))

        # Add annotation for equality
        annotation = MathTex("\\vec{A} = \\vec{B}").to_edge(DOWN).set_color(YELLOW)
        self.add(annotation)

        # Hold the final scene
        self.wait(2)

"""

class ManimCodeAgent:
    def __init__(self):
        self.system_prompt = MANIM_CODE_SYSTEM_PROMPT
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.validation_prompt = """
        **Code Validation Rules:**
        1. Ensure all objects from VisualPlan.ManimObjects are present
        2. Verify proper spatial organization (no overlapping labels)
        3. Check for required educational elements (equations, labels)
        4. Validate Manim syntax and scene structure
        """

    def validate_and_correct(self, generated_code: str, visual_plan: VisualPlan) -> str:
        """Self-correcting mechanism with visual plan validation"""
        correction_prompt = f"""
        Identify and fix issues in this Manim code based on the visual plan:
        
        Visual Plan Requirements:
        - Topic: {visual_plan.Topic}
        - Objects: {[obj.Object for obj in visual_plan.ManimObjects]}
        - Key Elements: {visual_plan.Description}
        
        Code to Validate:
        {generated_code}
        
        Common Issues to Check:
        1. Missing MathTex for equations
        2. Improper object positioning
        3. Absent labels/annotations
        4. Incorrect scene hierarchy
        
        Provide corrected code with comments explaining fixes.
        """
        response = self.model.generate_content(self.system_prompt + self.validation_prompt + correction_prompt)
        return self._extract_code(response.text)
        
    def generate_code(self, visual_plan: VisualPlan) -> ManimCode:
        max_attempts = 3
        for attempt in range(max_attempts):
            code = self._generate_initial_code(visual_plan)
            validated_code = self.validate_and_correct(code, visual_plan)
            
            if self._passes_validation(validated_code, visual_plan):
                return ManimCode(Code=validated_code, Description=f"Validated in {attempt+1} attempts")
            
        return ManimCode(Code=validated_code, Description="Best effort after validation attempts")

    def _passes_validation(self, code: str, visual_plan: VisualPlan) -> bool:
        # Check for required elements using regex patterns
        required_elements = [
            r"Text\(.*?\)",  # Labels
            r"MathTex\(.*?\)",  # Equations
            *[re.escape(obj.Object) for obj in visual_plan.ManimObjects]
        ]
        
        return all(re.search(pattern, code) for pattern in required_elements)

    def _generate_initial_code(self, visual_plan: VisualPlan) -> str:
        return f"""
from manim import *
from manim.utils.color import *

class {visual_plan.Topic.replace(' ', '')}Scene(Scene):
    def construct(self):
        # Add amsmath package for Greek letters
        self.add(Text(' ', font_size=0.1).set_color_by_tex("amsmath", WHITE))  
        # ... rest of scene code ...
"""

    def _extract_code(self, response_text: str) -> str:
        # Improved code extraction with markdown code block detection
        code_match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
        if not code_match:
            # Fallback pattern for code without markdown formatting
            code_match = re.search(r'(from manim import.*?)(?=\n\n|\Z)', response_text, re.DOTALL)
        
        if code_match:
            return code_match.group(1).strip()
        else:
            print(f"Debug: Failed to extract code from:\n{response_text}")
            return response_text  # Return raw text for debugging


if __name__ == "__main__":  
    topic_agent = TopicAnalysisAgent()
    visual_agent = VisualPlanAgent()
    manim_agent = ManimCodeAgent()

    # Get required inputs from user
    topic = input("Enter topic: ").strip()
    chapter = input("Enter chapter: ").strip()  # Add chapter input
    grade = input("Enter grade: ").strip()      # Add grade input
    output_filename = "generated_manim_script"

    # Pass all required parameters to analyze_topic
    topic_analysis = topic_agent.analyze_topic(topic, chapter, grade)

    if not topic_analysis:
        print("Failed to generate topic analysis.")
        exit()

    visual_plan = visual_agent.generate_plan(topic_analysis, chapter, grade)
    if not visual_plan:
        print("Failed to generate visual plan.")
        exit()

    print("Extracted Visual Plan:")
    print(visual_plan.model_dump_json(indent=4))

    manim_code = manim_agent.generate_code(visual_plan)

    if manim_code:
        print("Generated Manim Code:")
        print(manim_code.Code)
        
        # Write to standardized output file
        with open(f"{output_filename}.py", "w", encoding="utf-8") as f:
            f.write(manim_code.Code)
            
        print(f"Manim code saved to '{output_filename}.py'.")
    else:
        print("Failed to generate Manim code.")