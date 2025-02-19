import json
import os
from openai import OpenAI
from typing import Dict

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class LandmarkAIHandler:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found in environment variables")

    def enhance_landmark_description(self, landmark: Dict) -> Dict:
        """Enhance a landmark's description using AI."""
        try:
            prompt = f"""Analyze this landmark and provide enhanced details in JSON format:
            Name: {landmark.get('title')}
            Description: {landmark.get('description', '')}
            Location: {landmark.get('lat')}, {landmark.get('lon')}

            Please provide:
            1. A more engaging description
            2. Historical significance
            3. Best times to visit
            4. Three interesting facts

            Respond with JSON in this format:
            {{
                "enhanced_description": "string",
                "historical_significance": "string",
                "best_times": "string",
                "interesting_facts": ["fact1", "fact2", "fact3"]
            }}
            """

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )

            enhanced_data = json.loads(response.choices[0].message.content)
            landmark.update(enhanced_data)
            return landmark

        except Exception as e:
            print(f"Error enhancing landmark description: {e}")
            return landmark