import os
from dotenv import load_dotenv
import google.generativeai as genai
import rag

load_dotenv()
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

user_message = "what is kodnest"
print("1. Getting context...")
try:
    context = rag.get_context(user_message, top_k=3)
    print("Context retrieved:", bool(context))
except Exception as e:
    print("Error in get_context:", e)

print("2. Building prompt...")
system_prompt = (
    "You are KodBank AI...\n"
    + context + "\n\n"
    + f"User Message: {user_message}"
)

print("3. Calling Gemini...")
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(system_prompt, stream=True)
    
    print("4. Streaming response...")
    for chunk in response:
        print("Chunk:", chunk.text)
        
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Error calling Gemini:", e)

print("Done.")
