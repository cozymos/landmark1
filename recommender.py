import streamlit as st
from typing import List, Dict, Set, Optional
import numpy as np
from dataclasses import dataclass
import time
from datetime import datetime

@dataclass
class UserPreference:
    viewed_landmarks: Set[str]  # Set of landmark IDs viewed
    favorite_landmarks: Set[str]  # Set of landmarks marked as favorites
    last_interactions: Dict[str, float]  # Landmark ID to timestamp mapping
    category_weights: Dict[str, float]  # Category to weight mapping
    interaction_counts: Dict[str, int]  # Track number of interactions per landmark
    preferred_distances: List[float]  # Track preferred distances for recommendations
    time_of_day_preferences: Dict[str, float]  # Track when user tends to explore
    seasonal_preferences: Dict[str, float]  # Track seasonal preferences

class LandmarkRecommender:
    def __init__(self):
        # Initialize user preferences in session state with enhanced tracking
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = UserPreference(
                viewed_landmarks=set(),
                favorite_landmarks=set(),
                last_interactions={},
                category_weights={
                    'tourist_attraction': 1.0,
                    'landmark': 1.0,
                    'museum': 1.0,
                    'park': 1.0,
                    'historical_site': 1.0,
                    'cultural_site': 1.0
                },
                interaction_counts={},
                preferred_distances=[],
                time_of_day_preferences={
                    'morning': 1.0,
                    'afternoon': 1.0,
                    'evening': 1.0
                },
                seasonal_preferences={
                    'spring': 1.0,
                    'summer': 1.0,
                    'fall': 1.0,
                    'winter': 1.0
                }
            )

    def get_time_of_day(self) -> str:
        """Get current time of day category"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        else:
            return 'evening'

    def get_season(self) -> str:
        """Get current season"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return 'spring'
        elif 6 <= month <= 8:
            return 'summer'
        elif 9 <= month <= 11:
            return 'fall'
        else:
            return 'winter'

    def record_interaction(self, landmark_id: str, landmark_type: str, distance: float):
        """Record user interaction with enhanced tracking"""
        prefs = st.session_state.user_preferences
        prefs.viewed_landmarks.add(landmark_id)
        current_time = time.time()
        prefs.last_interactions[landmark_id] = current_time

        # Update interaction count
        prefs.interaction_counts[landmark_id] = prefs.interaction_counts.get(landmark_id, 0) + 1

        # Update category weight with decay for others
        decay_factor = 0.95
        for category in prefs.category_weights:
            if category == landmark_type:
                prefs.category_weights[category] = min(2.0, prefs.category_weights[category] * 1.1)
            else:
                prefs.category_weights[category] *= decay_factor

        # Update distance preferences
        prefs.preferred_distances.append(distance)
        if len(prefs.preferred_distances) > 10:  # Keep last 10 distances
            prefs.preferred_distances.pop(0)

        # Update time and seasonal preferences
        time_of_day = self.get_time_of_day()
        season = self.get_season()

        prefs.time_of_day_preferences[time_of_day] *= 1.1
        prefs.seasonal_preferences[season] *= 1.1

    def toggle_favorite(self, landmark_id: str) -> bool:
        """Toggle landmark as favorite with preference update"""
        prefs = st.session_state.user_preferences
        if landmark_id in prefs.favorite_landmarks:
            prefs.favorite_landmarks.remove(landmark_id)
            return False
        else:
            prefs.favorite_landmarks.add(landmark_id)
            return True

    def calculate_personalized_score(self, landmark: Dict, user_location: List[float]) -> float:
        """Calculate personalized score with enhanced factors"""
        prefs = st.session_state.user_preferences

        # Base relevance from landmark
        base_score = landmark['relevance']

        # Distance factor (gaussian distribution around preferred distances)
        if prefs.preferred_distances:
            mean_preferred_distance = np.mean(prefs.preferred_distances)
            distance_factor = np.exp(-((landmark['distance'] - mean_preferred_distance) ** 2) / (2 * 5 ** 2))
        else:
            distance_factor = 1.0 / (1.0 + landmark['distance'])

        # Category preference factor
        category_factor = prefs.category_weights.get(landmark.get('type', 'landmark'), 1.0)

        # Interaction history factor
        landmark_id = str(landmark['coordinates'])
        interaction_count = prefs.interaction_counts.get(landmark_id, 0)
        interaction_factor = 1.0 / (1.0 + interaction_count * 0.2)  # Reduce score for frequently visited places

        # Time relevance factors
        time_factor = prefs.time_of_day_preferences.get(self.get_time_of_day(), 1.0)
        season_factor = prefs.seasonal_preferences.get(self.get_season(), 1.0)

        # Recency factor
        if landmark_id in prefs.last_interactions:
            time_diff = time.time() - prefs.last_interactions[landmark_id]
            recency_factor = 1.0 / (1.0 + time_diff / 3600)  # Decay over hours
        else:
            recency_factor = 0.5  # Default for unseen landmarks

        # Favorite bonus
        favorite_bonus = 1.5 if landmark_id in prefs.favorite_landmarks else 1.0

        # Combine factors with weights
        final_score = (
            base_score * 0.25 +
            distance_factor * 0.20 +
            category_factor * 0.15 +
            interaction_factor * 0.10 +
            time_factor * 0.10 +
            season_factor * 0.10 +
            recency_factor * 0.10
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