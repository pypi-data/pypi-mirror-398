"""
Basic usage example for Tiramisu Framework
"""
from tiramisu import TiramisuRAG
import os

# Set your OpenAI API key
os.environ['OPENAI_API_KEY'] = 'your-api-key-here'

# Initialize the RAG system with example documents
rag = TiramisuRAG(
    documents_path='./documents',
    experts=['strategic_planning', 'digital_transformation', 'innovation'],
    model='gpt-4o',
    chunk_size=800,
    chunk_overlap=150
)

# Build the vector index
print("Building index...")
rag.build_index()

# Single query
response = rag.analyze("How can we improve our digital strategy?")
print(f"Answer: {response.answer}")
print(f"Sources: {response.sources}")

# Conversational mode
print("\n--- Starting conversation ---")
conversation_id = rag.start_conversation("Digital Strategy Discussion")

# First message
response1 = rag.continue_conversation(
    conversation_id, 
    "What are the key elements of digital transformation?"
)
print(f"Bot: {response1}")

# Follow-up with context
response2 = rag.continue_conversation(
    conversation_id,
    "How do we measure success?"
)
print(f"Bot: {response2}")

# View conversation history
history = rag.get_conversation_history(conversation_id)
print(f"\nConversation has {len(history)} messages")
