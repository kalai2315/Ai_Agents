import google.generativeai as genai
import json
import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional
from Topic_analysis_agent import TopicAnalysisAgent

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Define Pydantic Models for Visual Plan
class ManimObject(BaseModel):
    Object: str
    Description: str

class VisualPlan(BaseModel):
    Topic: str
    Description: str
    ManimObjects: List[ManimObject]
    SelectedVisualization: str

# System Prompt for AI
VISUAL_PLAN_SYSTEM_PROMPT = """
You are an AI agent generating structured **visualization plans** using **Manim**.
Identify key concepts, select the best representation (Diagram, Table, Flowchart, or Figure), 
and describe the visual plan with Manim objects.

### Expected JSON Output Format:

Example:

```json
{
    "Topic": "Photosynthesis",
    "Description": "A process used by plants to convert light energy into chemical energy.",
    "ManimObjects": [
        {"Object": "Sun", "Description": "Represents the source of energy"},
        {"Object": "Chloroplast", "Description": "Shows where photosynthesis occurs"}
    ],
    "SelectedVisualization": "Flowchart"
}"""

class VisualPlanAgent:
    def __init__(self):
        self.system_prompt = VISUAL_PLAN_SYSTEM_PROMPT
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_plan(self, topic_analysis: dict, chapter: str, grade: str) -> Optional[VisualPlan]:
        """Generate a visual plan based on Topic Analysis."""
        if not topic_analysis:
            print("Error: No valid topic analysis data received.")
            return None

        # Convert Pydantic model to dictionary first
        prompt = f"""
        **Topic Analysis:** {json.dumps(topic_analysis.model_dump(), indent=4)}
        **Chapter:** {chapter}
        **Grade:** {grade}
        """

        response = self.model.generate_content(self.system_prompt + prompt)
        
        # Debugging: Print raw response
        response_text = response.candidates[0].content.parts[0].text.strip() if response.candidates else ""
        print("Raw Response from Gemini:\n", response_text)

        # Extract JSON block
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)

        if not json_match:
            print("Error: JSON block not found in response.")
            return None

        try:
            visual_plan_data = json.loads(json_match.group(1))
            return VisualPlan(**visual_plan_data)
        except json.JSONDecodeError as e:
            print("Error: Invalid JSON format in response.", str(e))
            return None


if __name__ == "__main__":
    topic_agent = TopicAnalysisAgent()
    visual_agent = VisualPlanAgent()

    topic = input("Enter the topic: ").strip()
    chapter = input("Enter the chapter: ").strip()
    grade = input("Enter the grade/class: ").strip()

    topic_analysis = topic_agent.analyze_topic(topic, chapter, grade)

    # Convert Pydantic model to dict 
    if hasattr(topic_analysis, 'model_dump'):
        topic_analysis = topic_analysis.model_dump()
    elif isinstance(topic_analysis, str):
        try:
            topic_analysis = json.loads(topic_analysis)
        except json.JSONDecodeError:
            print("Error: Failed to parse topic analysis JSON.")
            exit()

    visual_plan = visual_agent.generate_plan(topic_analysis, chapter, grade)

    if visual_plan:
        print(json.dumps(visual_plan.model_dump(), indent=4))
    else:
        print("Failed to generate visual plan.")
