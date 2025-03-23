import streamlit as st
from jira_utils import validate_project_key, create_issue
from claude_utils import get_next_epic, get_stories_for_epic
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="JIRA AI Assistant", layout="wide")
st.title("🤖 JIRA Ticket Generator (Claude + JIRA)")

# Session variables
if "step" not in st.session_state:
    st.session_state.step = 0
if "project_key" not in st.session_state:
    st.session_state.project_key = ""
if "requirement_text" not in st.session_state:
    st.session_state.requirement_text = ""
if "epic_queue" not in st.session_state:
    st.session_state.epic_queue = []
if "current_epic" not in st.session_state:
    st.session_state.current_epic = None
if "story_queue" not in st.session_state:
    st.session_state.story_queue = []

# Step 0: Input Requirement Text
if st.session_state.step == 0:
    st.session_state.requirement_text = st.text_area("📝 Paste your product requirements:")
    if st.button("Next") and st.session_state.requirement_text.strip():
        st.session_state.step = 1

# Step 1: Ask for Project Key and validate
if st.session_state.step == 1:
    project_key = st.text_input("🔑 Enter your JIRA Project Key:")
    if st.button("Validate Project Key"):
        if validate_project_key(project_key):
            st.success("✅ Project Key validated!")
            st.session_state.project_key = project_key
            st.session_state.epic_queue = get_next_epic(st.session_state.requirement_text)
            st.session_state.step = 2
        else:
            st.error("❌ Project Key not found. Please try again.")

# Step 2: Epic Creation Loop
if st.session_state.step == 2:
    if st.session_state.current_epic is None and st.session_state.epic_queue:
        st.session_state.current_epic = st.session_state.epic_queue.pop(0)

    if st.session_state.current_epic:
        epic = st.session_state.current_epic
        st.info(f"📘 **Next Epic:**\n\n**{epic['summary']}**\n\n{epic['description']}")
        if st.button("✅ Create Epic"):
            epic_key = create_issue(
                st.session_state.project_key,
                epic['summary'],
                epic['description'],
                issue_type="Epic"
            )
            st.session_state.current_epic_key = epic_key
            st.success(f"✅ Epic created: `{epic_key}`")
            st.session_state.story_queue = get_stories_for_epic(epic['summary'], st.session_state.requirement_text)
            st.session_state.step = 3

# Step 3: Story Creation Loop
if st.session_state.step == 3 and st.session_state.story_queue:
    story = st.session_state.story_queue.pop(0)
    st.info(f"📗 **Story:**\n\n**{story['summary']}**\n\n{story['description']}")
    if st.button("✅ Create Story"):
        story_key = create_issue(
            st.session_state.project_key,
            story['summary'],
            story['description'],
            issue_type="Story",
            parent_key=st.session_state.current_epic_key
        )
        st.success(f"✅ Story created: `{story_key}`")

    # When all stories for the current epic are created
    if not st.session_state.story_queue:
        st.session_state.current_epic = None
        st.session_state.current_epic_key = None
        if st.session_state.epic_queue:
            st.session_state.step = 2  # Go back to next epic
        else:
            st.success("🎉 All Epics and Stories have been created!")
            st.session_state.step = 0
