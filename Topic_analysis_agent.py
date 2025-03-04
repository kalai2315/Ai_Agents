import google.generativeai as genai
import json
import os
import re
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define data models
class Definition(BaseModel):
    Term: str
    Definition: str

class Relationship(BaseModel):
    Concept1: str
    Concept2: str
    Relationship: str

class TopicAnalysis(BaseModel):
    CoreTopic: str
    KeyConcepts: List[str]
    Definitions: List[Definition]
    Relationships: List[Relationship]
    Formulas: List[str]
    VisualCues: List[str]
    Examples: List[str]

# System prompt for AI analysis
SYSTEM_PROMPT = """
You are an AI assistant that extracts structured information from textbook topics for visualization.
---
### Instructions:
1. Identify **Core Topic**
2. Extract **Key Concepts**
3. Extract **Definitions**
4. Identify **Relationships** between concepts
5. Extract **Formulas**
6. Identify **Visual Cues**
7. Extract **Examples**

### JSON Output Format:
```json
{
  "CoreTopic": "<Extracted Core Topic>",
  "KeyConcepts": ["<List of key concepts>"],
  "Definitions": [{"Term": "<Concept>", "Definition": "<Definition>"}],
  "Relationships": [{"Concept1": "<First Concept>", "Concept2": "<Second Concept>", "Relationship": "<Description>"}],
  "Formulas": ["<Extracted formulas>"],
  "VisualCues": ["<Visualization suggestions>"],
  "Examples": ["<Examples>"]
}
```"""

class TopicAnalysisAgent:
    """AI-driven agent for analyzing textbook topics."""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def analyze_topic(self, topic: str, chapter: str, grade: str) -> Optional[TopicAnalysis]:
        """Generates structured topic analysis using AI."""
        
        prompt = f"""
        ### Educational Context:
        - Chapter: {chapter}
        - Grade: {grade}
        - Topic: {topic}
        
        Provide analysis considering:
        1. Grade-level complexity
        2. Chapter learning objectives
        3. Relevant examples
        """

        response = self.model.generate_content(SYSTEM_PROMPT + prompt)

        if not response.candidates:
            print("Error: No response received.")
            return None

        response_text = response.candidates[0].content.parts[0].text.strip()

        try:
            # Improved JSON cleaning
            json_str = re.sub(
                r'(?m)^\s*//.*?$|//.*',  # Remove both line and inline comments
                '', 
                response_text
            ).strip()
            
            # Remove JSON markdown tags
            json_str = re.sub(r'^```json|```$', '', json_str, flags=re.MULTILINE)
            
            # Fix trailing commas in JSON arrays/objects
            json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
            
            parsed = json.loads(json_str)
            
            # Add validation for required fields
            if not all(key in parsed for key in ['CoreTopic', 'KeyConcepts', 'Definitions']):
                print("Error: Missing required fields in JSON response")
                return None
                
            return TopicAnalysis(**parsed)
            
        except json.JSONDecodeError as e:
            print(f"JSON Error: {str(e)}")
            print("Received Response:\n", response_text)  # Debug output
            return None
        except ValidationError as ve:
            print(f"Validation Error: {ve.errors()}")
            return None

if __name__ == "__main__":  
    agent = TopicAnalysisAgent()
    topic = input("Enter topic: ").strip()
    chapter = input("Enter chapter: ").strip()
    grade = input("Enter grade: ").strip()
    
    result = agent.analyze_topic(topic, chapter, grade)

    if result:
        print(json.dumps(result.model_dump(), indent=4))
    else:
        print("Analysis failed.")
