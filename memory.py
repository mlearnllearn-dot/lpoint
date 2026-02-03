chat_memory = {}

def get_memory(session_id: str):
    return chat_memory.get(session_id, [])

def save_memory(session_id: str, messages):
    chat_memory[session_id] = messages

def clear_memory(session_id: str):
    chat_memory.pop(session_id, None)
