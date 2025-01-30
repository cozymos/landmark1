import streamlit as st
from typing import List, Dict, Set, Optional
import numpy as np
from dataclasses import dataclass
import time
from datetime import datetime
from collections import defaultdict

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
    geographical_clusters: Dict[str, List[tuple]]  # Store geographical clusters of visited locations
    visit_day_preferences: Dict[str, float]  # Track preferred days of week
    travel_patterns: Dict[str, float]  # Store identified travel patterns

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
                },
                geographical_clusters={},
                visit_day_preferences={
                    'weekday': 1.0,
                    'weekend': 1.0
                },
                travel_patterns=defaultdict(float)
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

    def is_weekend(self) -> bool:
        """Check if current day is weekend"""
        return datetime.now().weekday() >= 5

    def update_geographical_clusters(self, coordinates: tuple):
        """Update geographical clusters based on new visit"""
        prefs = st.session_state.user_preferences
        cluster_radius = 5.0  # km

        # Find nearest cluster or create new one
        min_dist = float('inf')
        nearest_cluster = None

        for cluster_id, points in prefs.geographical_clusters.items():
            if points:
                cluster_center = np.mean(points, axis=0)
                dist = np.sqrt((coordinates[0] - cluster_center[0])**2 + 
                             (coordinates[1] - cluster_center[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_cluster = cluster_id

        if min_dist <= cluster_radius and nearest_cluster:
            prefs.geographical_clusters[nearest_cluster].append(coordinates)
        else:
            new_cluster_id = f"cluster_{len(prefs.geographical_clusters)}"
            prefs.geographical_clusters[new_cluster_id] = [coordinates]

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

        # Update time preferences
        time_of_day = self.get_time_of_day()
        season = self.get_season()
        day_type = 'weekend' if self.is_weekend() else 'weekday'

        prefs.time_of_day_preferences[time_of_day] *= 1.1
        prefs.seasonal_preferences[season] *= 1.1
        prefs.visit_day_preferences[day_type] *= 1.1

        # Update geographical clusters
        if 'coordinates' in landmark_id:
            try:
                coords = tuple(map(float, landmark_id.strip('()').split(',')))
                self.update_geographical_clusters(coords)
            except:
                pass

        # Update travel patterns
        self.update_travel_patterns(distance, time_of_day, day_type)

    def update_travel_patterns(self, distance: float, time_of_day: str, day_type: str):
        """Analyze and update travel patterns"""
        prefs = st.session_state.user_preferences
        pattern_key = f"{day_type}_{time_of_day}"

        if distance < 5:
            pattern_key += "_local"
        elif distance < 20:
            pattern_key += "_medium"
        else:
            pattern_key += "_far"

        prefs.travel_patterns[pattern_key] = prefs.travel_patterns.get(pattern_key, 1.0) * 1.1

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

        # Time relevance factors
        time_of_day = self.get_time_of_day()
        season = self.get_season()
        day_type = 'weekend' if self.is_weekend() else 'weekday'

        time_factor = prefs.time_of_day_preferences.get(time_of_day, 1.0)
        season_factor = prefs.seasonal_preferences.get(self.get_season(), 1.0)
        day_type_factor = prefs.visit_day_preferences.get(day_type, 1.0)

        # Travel pattern factor
        pattern_key = f"{day_type}_{time_of_day}"
        if landmark['distance'] < 5:
            pattern_key += "_local"
        elif landmark['distance'] < 20:
            pattern_key += "_medium"
        else:
            pattern_key += "_far"
        travel_pattern_factor = prefs.travel_patterns.get(pattern_key, 1.0)

        # Geographical cluster factor
        cluster_factor = 1.0
        if 'coordinates' in landmark:
            coords = landmark['coordinates']
            for cluster_points in prefs.geographical_clusters.values():
                if cluster_points:
                    cluster_center = np.mean(cluster_points, axis=0)
                    dist = np.sqrt((coords[0] - cluster_center[0])**2 + 
                                 (coords[1] - cluster_center[1])**2)
                    if dist <= 5.0:  # Within cluster radius
                        cluster_factor = 1.2
                        break

        # Combine all factors
        final_score = (
            base_score * 0.20 +
            distance_factor * 0.15 +
            category_factor * 0.15 +
            time_factor * 0.10 +
            season_factor * 0.10 +
            day_type_factor * 0.10 +
            travel_pattern_factor * 0.10 +
            cluster_factor * 0.10
        )

        # Apply favorite bonus
        if str(landmark['coordinates']) in prefs.favorite_landmarks:
            final_score *= 1.5

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

    def get_travel_insights(self) -> Dict:
        """Get insights about user's travel preferences"""
        prefs = st.session_state.user_preferences

        return {
            'favorite_time': max(prefs.time_of_day_preferences.items(), key=lambda x: x[1])[0],
            'preferred_season': max(prefs.seasonal_preferences.items(), key=lambda x: x[1])[0],
            'avg_distance': np.mean(prefs.preferred_distances) if prefs.preferred_distances else None,
            'frequent_categories': sorted(
                prefs.category_weights.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3],
            'num_clusters': len(prefs.geographical_clusters),
            'preferred_day_type': max(prefs.visit_day_preferences.items(), key=lambda x: x[1])[0]
        }