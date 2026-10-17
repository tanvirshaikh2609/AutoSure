"""Streamlit UI helpers used by the dashboard."""

import streamlit as st


def show_quick_actions(user: dict):
    """Role-based shortcut buttons."""
    if not user or 'role' not in user:
        return

    role = user.get('role', '')
    quick_actions = {
        'admin': [
            {'label': '➕ New Work Order', 'page': 'Service Orders'},
            {'label': '🧾 Invoices', 'page': 'Invoices'},
            {'label': '👤 Add Customer', 'page': 'Customers'},
            {'label': '📦 Inventory', 'page': 'Inventory'},
            {'label': '📈 Reports', 'page': 'Reports'},
        ],
        'manager': [
            {'label': '➕ New Work Order', 'page': 'Service Orders'},
            {'label': '🧾 Invoices', 'page': 'Invoices'},
            {'label': '👤 Add Customer', 'page': 'Customers'},
            {'label': '📦 Inventory', 'page': 'Inventory'},
            {'label': '📈 Reports', 'page': 'Reports'},
        ],
        'technician': [
            {'label': '🔧 My Work Orders', 'page': 'Service Orders'},
            {'label': '📦 Inventory', 'page': 'Inventory'},
        ],
        'cashier': [
            {'label': '🧾 Invoices', 'page': 'Invoices'},
            {'label': '🔍 Customers', 'page': 'Customers'},
            {'label': '🔧 Work Orders', 'page': 'Service Orders'},
        ],
    }

    actions = quick_actions.get(role, [])
    if not actions:
        st.info("No quick actions available for your role.")
        return

    st.markdown("### Quick Actions")
    cols = st.columns(min(len(actions), 3))
    for idx, action in enumerate(actions):
        with cols[idx % 3]:
            if st.button(action['label'], key=f"quick_action_{idx}", use_container_width=True):
                st.session_state['navigate_to'] = action['page']
                st.rerun()
