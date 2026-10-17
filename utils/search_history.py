"""
Search History Utility
Manages search history storage and retrieval in session state
"""

import streamlit as st
from typing import List, Optional
from datetime import datetime


class SearchHistory:
    """Manages search history for quick re-execution"""
    
    def __init__(self, context: str, max_history: int = 10):
        """
        Initialize search history manager.
        
        Args:
            context: Context identifier (e.g., 'customers', 'vehicles', 'inventory')
            max_history: Maximum number of searches to store
        """
        self.context = context
        self.max_history = max_history
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for search history"""
        key = f'search_history_{self.context}'
        if key not in st.session_state:
            st.session_state[key] = []
    
    def add_search(self, query: str):
        """
        Add a search query to history.
        
        Args:
            query: Search query string
        """
        if not query or not query.strip():
            return
        
        query = query.strip()
        key = f'search_history_{self.context}'
        history = st.session_state[key]
        
        # Remove duplicate if exists
        if query in history:
            history.remove(query)
        
        # Add to beginning
        history.insert(0, query)
        
        # Limit history size
        st.session_state[key] = history[:self.max_history]
    
    def get_history(self) -> List[str]:
        """
        Get search history.
        
        Returns:
            List of recent search queries
        """
        key = f'search_history_{self.context}'
        return st.session_state.get(key, [])
    
    def clear_history(self):
        """Clear all search history"""
        key = f'search_history_{self.context}'
        st.session_state[key] = []
    
    def render_history_dropdown(self, label: str = "Recent Searches", placeholder: str = "Select a recent search...") -> Optional[str]:
        """
        Render a dropdown with search history.
        
        Args:
            label: Label for the dropdown
            placeholder: Placeholder text
        
        Returns:
            Selected search query or None
        """
        history = self.get_history()
        
        if not history:
            return None
        
        options = [placeholder] + history
        selected = st.selectbox(
            label,
            options=options,
            index=0,
            key=f"history_dropdown_{self.context}"
        )
        
        if selected != placeholder:
            return selected
        
        return None
    
    def render_quick_search_buttons(self, max_buttons: int = 5) -> Optional[str]:
        """
        Render quick search buttons for recent searches.
        
        Args:
            max_buttons: Maximum number of buttons to display
        
        Returns:
            Selected search query or None
        """
        history = self.get_history()
        
        if not history:
            return None
        
        st.markdown("**Recent Searches:**")
        
        # Display buttons in columns
        num_buttons = min(len(history), max_buttons)
        cols = st.columns(num_buttons)
        
        for idx, query in enumerate(history[:num_buttons]):
            with cols[idx]:
                if st.button(f"🔍 {query[:15]}...", key=f"quick_search_{self.context}_{idx}", use_container_width=True):
                    return query
        
        return None
