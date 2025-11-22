import streamlit as st
import json
import os
import re

# Page Config
st.set_page_config(
    page_title="Output Visualizer",
    page_icon="📋",
    layout="wide"
)

# Paths to the files
OUTPUT_FILE_PATH = os.path.join("docs", "output_v2_with_matches.jsonl")  # Use pre-computed matches
INPUT_FILE_PATH = os.path.join("docs", "LOD_1121.jsonl")

# Entity Styling Configuration
ENTITY_STYLES = {
    "User": {"color": "#3498db", "icon": "👤"},
    "Event": {"color": "#9b59b6", "icon": "📅"},
    "OnlineMeeting": {"color": "#8e44ad", "icon": "📹"},
    "File": {"color": "#e67e22", "icon": "📄"},
    "Chat": {"color": "#2ecc71", "icon": "💬"},
    "ChannelMessage": {"color": "#27ae60", "icon": "📢"},
    "Email": {"color": "#e74c3c", "icon": "✉️"},
    "Other": {"color": "#95a5a6", "icon": "📦"}
}

def get_entity_card_header(etype, title):
    style = ENTITY_STYLES.get(etype, ENTITY_STYLES["Other"])
    color = style["color"]
    icon = style["icon"]
    return f"""
    <div style="
        background-color: {color}; 
        padding: 8px 12px; 
        border-radius: 5px; 
        color: white; 
        margin-bottom: 10px;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 8px;
    ">
        <span style="font-size: 1.2em;">{icon}</span>
        <span>{title}</span>
    </div>
    """

def render_user_card(item):
    """Render a professional card for a User entity."""
    display_name = item.get('DisplayName', 'Unknown')
    job_title = item.get('JobTitle', '')
    department = item.get('Department', '')
    email = item.get('MailNickName', '')
    phone = item.get('PhoneNumber', '')
    location = item.get('OfficeLocation', '')
    manager = item.get('Manager', '')
    
    # Address
    address = item.get('Address', {})
    full_address = f"{address.get('Street', '')}, {address.get('City', '')}, {address.get('State', '')} {address.get('PostalCode', '')}" if address else ""

    html = f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #ddd; color: #333;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <h3 style="margin: 0; color: #2c3e50;">{display_name}</h3>
                <p style="margin: 2px 0; color: #7f8c8d; font-style: italic;">{job_title} {f"| {department}" if department else ""}</p>
            </div>
            <div style="text-align: right; font-size: 0.9em; color: #7f8c8d;">
                <div>{location}</div>
            </div>
        </div>
        <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em;">
            <div>
                <strong>📧 Email:</strong> {email}<br>
                <strong>📞 Phone:</strong> {phone}<br>
                <strong>👔 Manager:</strong> {manager}
            </div>
            <div>
                <strong>📍 Address:</strong><br>
                {full_address}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_generic_card(item):
    """Render a generic card for other entities."""
    # Filter out complex objects for the summary view
    simple_fields = {k: v for k, v in item.items() if isinstance(v, (str, int, float, bool)) and k not in ['type', 'Content']}
    
    # Create a markdown table
    md = "| Field | Value |\n|---|---|\n"
    for k, v in simple_fields.items():
        md += f"| **{k}** | {v} |\n"
    
    st.markdown(md)

def render_file_card(item, key_suffix=""):
    """Render a card for File entities with content side-by-side."""
    content = item.get('Content', 'No content available.')
    
    # Filter simple fields for metadata
    simple_fields = {k: v for k, v in item.items() if isinstance(v, (str, int, float, bool)) and k not in ['type', 'Content']}
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📄 Metadata")
        # Create a markdown table
        md = "| Field | Value |\n|---|---|\n"
        for k, v in simple_fields.items():
            md += f"| **{k}** | {v} |\n"
        st.markdown(md)
        
    with col2:
        st.markdown("#### 📝 Content")
        # Use tabs to allow switching between rendered markdown and raw text
        tab1, tab2 = st.tabs(["📄 Preview", "ℹ️ Raw Source"])
        
        with tab1:
            # Render markdown in a bordered container to simulate a document page
            with st.container(border=True):
                if content and content.strip():
                    st.markdown(content)
                else:
                    st.caption("No content to preview.")
        
        with tab2:
            st.text_area("File Content", content, height=400, disabled=True, label_visibility="collapsed", key=f"file_content_{key_suffix}")

@st.cache_data
def load_data(path):
    """Load JSONL data from the given path."""
    data = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return data

def get_meeting_subject(item):
    """Extract meeting subject from utterance or entities."""
    utterance = item.get('UTTERANCE', {}).get('text', '')
    
    # 1. Try to extract text inside single quotes
    match = re.search(r"'([^']*)'", utterance)
    if match:
        return match.group(1)
        
    # 2. Try to find Event entity Subject
    entities = item.get('ENTITIES_TO_USE', [])
    for entity in entities:
        if entity.get('type') == 'Event' and 'Subject' in entity:
            return entity['Subject']
            
    # 3. Fallback to truncated utterance
    return utterance[:50] + "..." if len(utterance) > 50 else utterance

def main():
    st.title("📋 Output Data Visualizer")
    st.markdown("### Author: Kening Ren")
    st.markdown(f"Visualizing contents of: `{OUTPUT_FILE_PATH}` matched with `{INPUT_FILE_PATH}`")

    # Display Prompt File
    PROMPT_FILE_PATH = os.path.join("docs", "step1_v2.md")
    if os.path.exists(PROMPT_FILE_PATH):
        with st.expander("📄 View Generation Prompt (step1_v2.md)"):
            with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
                st.markdown(f"```markdown\n{f.read()}\n```")

    # Load Data
    output_data = load_data(OUTPUT_FILE_PATH)
    input_data = load_data(INPUT_FILE_PATH)

    if not input_data:
        st.error(f"Could not find or load data from {INPUT_FILE_PATH}. Please ensure the file exists.")
        return

    # Create a map for output data: utterance -> output_item
    output_map = {item.get('utterance'): item for item in output_data}

    # Sidebar Navigation
    st.sidebar.header("Select an Entry (from Input Data)")
    
    # Create a list of options for the sidebar based on INPUT data
    # Input data structure: {"UTTERANCE": {"text": "..."}}
    options = []
    for i, item in enumerate(input_data):
        subject = get_meeting_subject(item)
        utterance_text = item.get('UTTERANCE', {}).get('text', 'No Utterance')
        has_output = "✅" if utterance_text in output_map else "❌"
        options.append(f"{i+1}. {has_output} {subject}")
    
    # Use radio buttons for selection if list is small, otherwise selectbox is standard.
    # Streamlit's selectbox shows a dropdown. To show "20 items", we rely on the browser's rendering
    # of the select element, but Streamlit's custom widget handles this.
    # However, users often want a list they can see more of at once.
    # A radio button list inside a scrollable container is a good alternative for "seeing more items".
    
    # Let's use a radio button list for better visibility of multiple items at once
    selected_option = st.sidebar.radio(
        "Choose a meeting context:",
        options,
        index=0
    )
    
    # Extract index from the selected option string "1. ✅ Subject..."
    selected_index = int(selected_option.split('.')[0]) - 1

    # Get selected input item
    input_item = input_data[selected_index]
    utterance_text = input_item.get('UTTERANCE', {}).get('text', '')
    
    # Try to find matching output
    output_item = output_map.get(utterance_text)

    # Display Content
    st.markdown("---")
    
    # Utterance Section
    st.subheader("🗣️ Utterance")
    st.info(utterance_text)

    # Input Data Toggle
    with st.expander("📥 View Input Context (LOD Data)", expanded=False):
        # View Mode Toggle
        view_mode = st.radio("View Mode", ["Card View", "JSON View"], horizontal=True, label_visibility="collapsed")
        
        if view_mode == "JSON View":
            st.json(input_item)
        else:
            # Card View Implementation
            
            # 1. User Info
            st.markdown("#### 👤 User")
            user_data = input_item.get('USER', {})
            if user_data:
                with st.container(border=True):
                    st.markdown(f"**{user_data.get('displayName', 'Unknown')}**")
                    st.caption(f"ID: {user_data.get('id', 'N/A')}")
                    st.json(user_data, expanded=False)
            
            # 2. Entities
            st.markdown("#### 📦 Entities")
            entities = input_item.get('ENTITIES_TO_USE', [])
            
            if entities:
                # Group entities by type
                groups = {}
                for e in entities:
                    etype = e.get('type', 'Other')
                    if etype not in groups:
                        groups[etype] = []
                    groups[etype].append(e)
                
                # View Mode Toggle
                view_mode = st.radio("Display Mode", ["Card View", "JSON View"], horizontal=True, key="entity_view_mode")

                # Controls for Expand/Collapse
                c1, c2, c3, c4 = st.columns(4)
                if c1.button("➕ Groups", help="Expand all entity groups"):
                    st.session_state["groups_expanded"] = True
                if c2.button("➖ Groups", help="Collapse all entity groups"):
                    st.session_state["groups_expanded"] = False
                if c3.button("➕ Details", help="Expand all JSON details"):
                    st.session_state["json_expanded"] = True
                if c4.button("➖ Details", help="Collapse all JSON details"):
                    st.session_state["json_expanded"] = False
                
                groups_expanded = st.session_state.get("groups_expanded", False)
                json_expanded = st.session_state.get("json_expanded", True)

                # Display groups
                for etype, group_items in groups.items():
                    # Show statistics in the expander label
                    with st.expander(f"**{etype}** ({len(group_items)} items)", expanded=groups_expanded):
                        for i, item in enumerate(group_items):
                            # Individual Card
                            with st.container(border=True):
                                # Determine a title for the card
                                title = item.get('Subject') or item.get('FileName') or item.get('DisplayName') or item.get('EventId') or "Item"
                                header = get_entity_card_header(etype, title)
                                st.markdown(header, unsafe_allow_html=True)
                                
                                if view_mode == "Card View":
                                    # Render user card or generic card based on entity type
                                    if etype == "User":
                                        render_user_card(item)
                                    elif etype == "File":
                                        render_file_card(item, key_suffix=f"{etype}_{i}")
                                    else:
                                        render_generic_card(item)
                                        with st.expander("Raw JSON"):
                                            st.json(item)
                                else:
                                    st.json(item, expanded=json_expanded)
            else:
                st.info("No entities found in this context.")

    if output_item:
        # Two-column layout for Response and Assertions
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("🤖 Generated Response")
            response_content = output_item.get('response', '*No response content*')
            
            # Apply highlighting
            highlight_matches = st.session_state.get("highlight_matches")
            highlight_term = st.session_state.get("highlight_term")
            
            if highlight_matches:
                # Colors for ranked matches: Strong -> Medium -> Weak
                # Using RGBA for fading effect
                colors = [
                    "rgba(255, 193, 7, 1.0)",  # Rank 1: Strong Yellow
                    "rgba(255, 193, 7, 0.6)",  # Rank 2: Medium Yellow
                    "rgba(255, 193, 7, 0.3)"   # Rank 3: Light Yellow
                ]
                
                for i, match_text in enumerate(highlight_matches):
                    if i < len(colors):
                        color = colors[i]
                        pattern = re.compile(re.escape(match_text), re.IGNORECASE)
                        response_content = pattern.sub(
                            lambda m: f"<mark style='background-color: {color}; color: black; border-radius: 3px;' title='Match Rank: {i+1}'>{m.group(0)}</mark>", 
                            response_content
                        )
            elif highlight_term:
                # Case-insensitive replacement with yellow background
                pattern = re.compile(re.escape(highlight_term), re.IGNORECASE)
                # We use a lambda to preserve the case of the matched text
                response_content = pattern.sub(lambda m: f"<mark style='background-color: #fff3cd; color: black;'>{m.group(0)}</mark>", response_content)
                
            st.markdown(response_content, unsafe_allow_html=True)

        with col2:
            st.subheader("✅ Assertions")
            assertions = output_item.get('assertions', [])
            
            if not assertions:
                st.warning("No assertions found for this entry.")
            else:
                for i, assertion in enumerate(assertions):
                    level = assertion.get('level', 'unknown').lower()
                    
                    # Color coding based on level
                    color_map = {
                        "critical": "red",
                        "expected": "green",
                        "aspirational": "orange"
                    }
                    color = color_map.get(level, "blue")
                    
                    # Card-like expander for each assertion
                    with st.expander(f":{color}[**{level.upper()}**] - {assertion.get('text', '')[:60]}..."):
                        st.markdown(f"**Full Assertion:**\n{assertion.get('text')}")
                        
                        reasoning = assertion.get('reasoning', {})
                        if reasoning:
                            st.markdown("**Reasoning:**")
                            st.info(reasoning.get('reason', 'No reasoning provided.'))
                            
                            source = reasoning.get('source', '')
                            if source:
                                st.markdown("**Source:**")
                                # Highlight the source text in yellow as requested
                                st.markdown(
                                    f"<div style='background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 5px solid #ffc107; color: #856404;'>{source}</div>", 
                                    unsafe_allow_html=True
                                )
                                
                                # Button to locate in response
                                # Check if pre-computed matches exist
                                matched_segments = assertion.get('matched_segments', [])
                                
                                if matched_segments:
                                    # Use pre-computed matches
                                    if st.button(f"🔍 Show Evidence", key=f"locate_{i}"):
                                        st.session_state["highlight_matches"] = matched_segments
                                        st.session_state["active_assertion_index"] = i
                                        st.rerun()
                                else:
                                    st.caption("⚠️ No pre-computed matches found. Run compute_assertion_matches.py first.")
                                
                                # Match display and clear (only for the active assertion)
                                if st.session_state.get("active_assertion_index") == i and st.session_state.get("highlight_matches"):
                                    matches = st.session_state["highlight_matches"]
                                    
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.caption(f"✅ Showing {len(matches)} evidence passages (Strongest to Weakest)")
                                    with col2:
                                        if st.button("❌", key=f"clear_{i}", help="Clear Highlight"):
                                            st.session_state["highlight_matches"] = None
                                            st.session_state["highlight_term"] = None
                                            st.session_state["active_assertion_index"] = None
                                            st.rerun()
                                            st.rerun()
                            st.caption(f"{reasoning.get('reason', 'N/A')}")
                            
                            st.markdown("**Source:**")
                            st.caption(f"{reasoning.get('source', 'N/A')}")
                        else:
                            st.markdown("*No reasoning provided.*")
    else:
        st.warning("⚠️ No generated output found for this input meeting.")

if __name__ == "__main__":
    main()
