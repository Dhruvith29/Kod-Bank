import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def delete_old_index():
    try:
        pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY', ''))
        index_name = "kodbank-fundamental"
        existing = [idx.name for idx in pc.list_indexes()]
        if index_name in existing:
            print(f"Deleting existing index: {index_name} (old dimensions)")
            pc.delete_index(index_name)
            print("Successfully deleted. It will be recreated with 3072 dimensions on next app start.")
        else:
            print("No existing index found to delete.")
    except Exception as e:
        print("Error deleting index:", str(e))

if __name__ == "__main__":
    delete_old_index()
