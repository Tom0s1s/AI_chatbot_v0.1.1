import ollama
import logging
#testings"
def call_ll(query: str) -> str:
    try:
        resp = ollama.chat(
            model="llama2:7b",
            messages=[{"role": "user", "content": query}]
        )
        return resp["message"]["content"]
    except Exception as e:
        logging.exception(f"LLM call failed: {e}")
        return "Sorry, I'm having trouble processing your request right now."
