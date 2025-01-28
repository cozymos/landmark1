import streamlit as st
from typing import List, Dict, Set
import numpy as np
from dataclasses import dataclass
import time

@dataclass
class UserPreference:
    viewed_landmarks: Set[str]  # Set of landmark IDs viewed
    favorite_landmarks: Set[str]  # Set of landmarks marked as favorites
    last_interactions: Dict[str, float]  # Landmark ID to timestamp mapping
    category_weights: Dict[str, float]  # Category to weight mapping

class LandmarkRecommender:
    def __init__(self):
        # Initialize user preferences in session state
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = UserPreference(
                viewed_landmarks=set(),
                favorite_landmarks=set(),
                last_interactions={},
                category_weights={
                    'tourist_attraction': 1.0,
                    'landmark': 1.0,
                    'museum': 1.0,
                    'park': 1.0
                }
            )
    
    def record_interaction(self, landmark_id: str, landmark_type: str):
        """Record user interaction with a landmark"""
        prefs = st.session_state.user_preferences
        prefs.viewed_landmarks.add(landmark_id)
        prefs.last_interactions[landmark_id] = time.time()
        
        # Increase weight for the landmark type
        if landmark_type in prefs.category_weights:
            prefs.category_weights[landmark_type] = min(
                2.0, 
                prefs.category_weights[landmark_type] + 0.1
            )

    def toggle_favorite(self, landmark_id: str):
        """Toggle landmark as favorite"""
        prefs = st.session_state.user_preferences
        if landmark_id in prefs.favorite_landmarks:
            prefs.favorite_landmarks.remove(landmark_id)
            return False
        else:
            prefs.favorite_landmarks.add(landmark_id)
            return True

    def calculate_personalized_score(self, landmark: Dict, user_location: List[float]) -> float:
        """Calculate personalized score for a landmark"""
        prefs = st.session_state.user_preferences
        base_score = landmark['relevance']
        
        # Distance factor (inverse relationship)
        distance_factor = 1.0 / (1.0 + landmark['distance'])
        
        # Category preference factor
        category_factor = prefs.category_weights.get(landmark.get('type', 'landmark'), 1.0)
        
        # Interaction recency factor
        landmark_id = str(landmark['coordinates'])
        if landmark_id in prefs.last_interactions:
            time_diff = time.time() - prefs.last_interactions[landmark_id]
            recency_factor = 1.0 / (1.0 + time_diff / 3600)  # Decay over hours
        else:
            recency_factor = 0.5  # Default for unseen landmarks
        
        # Favorite bonus
        favorite_bonus = 1.5 if landmark_id in prefs.favorite_landmarks else 1.0
        
        # Combine factors with weights
        final_score = (
            base_score * 0.3 +
            distance_factor * 0.2 +
            category_factor * 0.2 +
            recency_factor * 0.15
        ) * favorite_bonus
        
        return min(1.0, max(0.1, final_score))

    def get_recommendations(
        self,
        landmarks: List[Dict],
        user_location: List[float],
        top_n: int = 5
    ) -> List[Dict]:
        """Get personalized landmark recommendations"""
        if not landmarks:
            return []
            
        # Calculate personalized scores
        scored_landmarks = []
        for landmark in landmarks:
            score = self.calculate_personalized_score(landmark, user_location)
            scored_landmarks.append((score, landmark))
        
        # Sort by score and return top N
        scored_landmarks.sort(reverse=True, key=lambda x: x[0])
        return [
            {**landmark, 'personalized_score': score}
            for score, landmark in scored_landmarks[:top_n]
        ]
