import os
import time
import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import ClientError

# 1. Update this with your fresh API key
API_KEY = "AQ.Ab8RN6IyeaI0YaoYlHOPEqLVIPHpR4M5yiuQwQ4T_WV_88WjCw"
client = genai.Client(api_key=API_KEY)

# 2. Local Handbook RAG
class SimpleLocalRAG:
    def __init__(self, filepath="college_handbook.txt"):
        self.chunks = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(base_dir, filepath)
        
        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                text = f.read()
            self.chunks = [p.strip() for p in text.split("\n\n") if p.strip()]

    def search(self, query: str) -> str:
        if not self.chunks:
            return "No handbook data available."
        words = set(query.lower().split())
        ranked = sorted(
            self.chunks,
            key=lambda c: sum(1 for w in words if w in c.lower()),
            reverse=True,
        )
        return ranked[0] if ranked else self.chunks[0]

rag = SimpleLocalRAG()

# 3. Tools
def college_rules_search(query: str) -> str:
    """Searches official college attendance regulations, timings, bus schedules, and syllabus details."""
    return rag.search(query)

def get_campus_notices(query: str) -> str:
    """Checks recent campus circulars, exam dates, and payment deadlines."""
    notices = {
        "exam": "Midterm examinations commence on October 12. Hall tickets will be released on October 5.",
        "fee": "The deadline for semester fee submission without late fees is September 25.",
        "holiday": "Campus remains closed this Friday for the regional festival.",
    }
    for key, val in notices.items():
        if key in query.lower():
            return val
    return "No urgent notices found for this query."

# 4. Streamlit UI
st.set_page_config(page_title="AI Student Support Assistant", layout="centered")
st.title("🎓 Campus AI Student Support Assistant")

if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction="You are the official College Student Support Assistant. Ground your answers using your available tools whenever applicable.",
            tools=[college_rules_search, get_campus_notices],
        ),
    )
    st.session_state.history = []

for role, text in st.session_state.history:
    st.chat_message(role).write(text)

user_input = st.chat_input("Ask about college timings, assembly, bus, or syllabus...")
if user_input:
    st.chat_message("user").write(user_input)
    st.session_state.history.append(("user", user_input))

    with st.spinner("Processing..."):
        try:
            response = st.session_state.chat.send_message(user_input)
            reply = response.text
            st.chat_message("assistant").write(reply)
            st.session_state.history.append(("assistant", reply))
        except ClientError as e:
            if "429" in str(e):
                error_msg = "⚠️ Daily/Per-minute API quota reached. Please generate a fresh key from Google AI Studio or wait 30 seconds."
            else:
                error_msg = f"⚠️ API Error: {e.message}"
            st.error(error_msg)