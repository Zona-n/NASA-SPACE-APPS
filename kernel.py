import os
import json
from dotenv import load_dotenv
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from load_publications import load_all_publications, create_knowledge_base_text

# Load environment variables
load_dotenv()

# Azure OpenAI settings
model_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_API_KEY")

# Load publications data
print("Loading publications...")
publications = load_all_publications('data/SB_publication')
print(f"Loaded {len(publications)} publications")

# Create knowledge base
knowledge_base = create_knowledge_base_text(publications[:50])  # Use first 50 for context size

# Create kernel
kernel = Kernel()
kernel.add_service(
    AzureChatCompletion(
        deployment_name=model_id,
        endpoint=endpoint,
        api_key=api_key
    )
)

async def search_publications(query):
    """Search publications using AI"""
    prompt = f"""You are a NASA bioscience research assistant. Based on the following database of research publications, answer the user's question.

Database:
{knowledge_base}

User Question: {query}

Provide a concise, accurate answer based only on the information in the database. If the information isn't available, say so. Include relevant paper IDs when referencing specific studies."""

    response = await kernel.invoke_prompt(prompt, KernelArguments())
    return str(response)

# Test function
async def main():
    test_query = "What research has been done on bone density in mice?"
    result = await search_publications(test_query)
    print("Question:", test_query)
    print("Answer:", result)

if __name__ == "__main__":
    asyncio.run(main())