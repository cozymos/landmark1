import streamlit as st
from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Achievement:
    name: str
    description: str
    icon: str
    requirement: int  # Number of landmarks needed

class JourneyTracker:
    def __init__(self):
        # Initialize session state for journey tracking
        if 'discovered_landmarks' not in st.session_state:
            st.session_state.discovered_landmarks = set()
        if 'achievements' not in st.session_state:
            st.session_state.achievements = set()
        if 'last_discovery_time' not in st.session_state:
            st.session_state.last_discovery_time = None
        
        # Define achievements
        self.available_achievements = [
            Achievement("Explorer Novice", "Discover your first 5 landmarks", "🌟", 5),
            Achievement("Seasoned Traveler", "Visit 15 different landmarks", "🏅", 15),
            Achievement("Master Explorer", "Discover 30 unique locations", "🎖️", 30),
            Achievement("Legend of Discovery", "Find 50 fascinating places", "👑", 50)
        ]

    def add_discovery(self, landmark_id: str, landmark_name: str) -> Dict:
        """
        Record a new landmark discovery and return animation/achievement details
        """
        if landmark_id not in st.session_state.discovered_landmarks:
            st.session_state.discovered_landmarks.add(landmark_id)
            st.session_state.last_discovery_time = datetime.now()
            
            # Check for new achievements
            new_achievements = self._check_achievements()
            
            return {
                "is_new": True,
                "discovery_count": len(st.session_state.discovered_landmarks),
                "new_achievements": new_achievements,
                "landmark_name": landmark_name
            }
        
        return {"is_new": False}

    def _check_achievements(self) -> List[Achievement]:
        """Check and award new achievements"""
        new_achievements = []
        current_count = len(st.session_state.discovered_landmarks)
        
        for achievement in self.available_achievements:
            if (current_count >= achievement.requirement and 
                achievement.name not in st.session_state.achievements):
                st.session_state.achievements.add(achievement.name)
                new_achievements.append(achievement)
        
        return new_achievements

    def get_progress(self) -> Dict:
        """Get current journey progress statistics"""
        return {
            "total_discovered": len(st.session_state.discovered_landmarks),
            "achievements": [a for a in self.available_achievements 
                           if a.name in st.session_state.achievements],
            "next_achievement": next(
                (a for a in self.available_achievements 
                 if a.name not in st.session_state.achievements),
                None
            )
        }

    def should_animate(self, landmark_id: str) -> bool:
        """Check if landmark should trigger discovery animation"""
        return (landmark_id not in st.session_state.discovered_landmarks and 
                (st.session_state.last_discovery_time is None or 
                 (datetime.now() - st.session_state.last_discovery_time).seconds > 2))
