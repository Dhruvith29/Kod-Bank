import os
from dotenv import load_dotenv
import google.generativeai as genai
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import traceback

load_dotenv()

with open("python_test_log.txt", "w") as f:
    f.write("Testing GitHub Model (Llama)...\n")
    try:
        client = ChatCompletionsClient(
            endpoint="https://models.github.ai/inference",
            credential=AzureKeyCredential(os.environ.get('GITHUB_TOKEN', '')),
        )
        response = client.complete(
            messages=[UserMessage(content="Reply with 'hello' only.")], 
            model="meta/Llama-4-Scout-17B-16E-Instruct",
            max_tokens=10
        )
        f.write("GitHub Success: " + response.choices[0].message.content + "\n")
    except Exception as e:
        f.write("GitHub Model Failed:\n" + traceback.format_exc() + "\n")

    f.write("\nTesting Gemini Model (Embedding)...\n")
    try:
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY', ''))
        result = genai.embed_content(
            model="models/embedding-001",
            content="Test content",
            task_type="retrieval_document"
        )
        if "embedding" in result:
             f.write("Gemini Embeddings Success: Received vector of length " + str(len(result["embedding"])) + "\n")
        
        f.write("\nTesting Gemini Model (Generate)...\n")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Reply with 'hello' only.")
        f.write("Gemini Generate Success: " + response.text.strip() + "\n")
        
    except Exception as e:
        f.write("Gemini Model Failed:\n" + traceback.format_exc() + "\n")
