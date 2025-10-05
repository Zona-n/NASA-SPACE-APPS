import os
import csv
import json
from dotenv import load_dotenv
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments

# load env
load_dotenv()
model_id = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_API_KEY")

# kernel
kernel = Kernel()
kernel.add_service(
    AzureChatCompletion(
        deployment_name=model_id,
        endpoint=endpoint,
        api_key=api_key
    )
)

# helper function
def extract_pmc_id(url: str) -> str | None:
    """Extracts the PMC ID from a URL."""
    try:
        parts = url.strip("/").split("/")
        for part in reversed(parts):
            if part.startswith("PMC"):
                return part
        return None
    except Exception as e:
        print(f"Error extracting PMC ID from {url}: {e}")
        return None

def load_publications(csv_path: str) -> list[dict]:
    """Load publications from CSV and extract PMC IDs."""
    records = []
    with open(csv_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("Link", "").strip()
            records.append({
                "title": row.get("Title", "").strip().replace("/", "_").replace("\\", "_"),
                "url": url,
                "pmcid": extract_pmc_id(url)
            })
    return records

def load_article_json(pmcid: str) -> dict | None:
    """Load article JSON for a given PMC ID."""
    path = f"data/SB_publication/{pmcid}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# async functions
async def related_pmcs(user_input: str, records: list[dict]) -> list[str]:
    """Return 5 related PMC IDs based on user input and publication records."""
    records_str = "\n".join([f"{r['title']} ({r['pmcid']})" for r in records if r['pmcid']])
    prompt_text = (
        f"User input: {user_input}\n\n"
        f"Go through the following publications:\n{records_str}\n\n"
        f"Provide a list of 5 related PMC IDs, separated by commas."
    )

    response = await kernel.invoke_prompt(prompt_text, KernelArguments())
    pmc_list = [pmc.strip() for pmc in str(response).split(",") if pmc.strip()]
    print("Related PMC IDs:", pmc_list)
    return pmc_list

def extract_text_from_json(pmcid: str) -> str:
    """Extract all text from a PMC JSON file."""
    path = f"data/SB_publication/{pmcid}.json"
    if not os.path.exists(path):
        print(f"File {path} not found.")
        return ""

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = ""
    articles = data if isinstance(data, list) else [data]
    
    for article in articles:
        documents = article.get("documents", [])
        for doc in documents:
            passages = doc.get("passages", [])
            for passage in passages:
                passage_text = passage.get("text", "")
                if passage_text:
                    text += passage_text + "\n"

    return text

async def summarize_article(user_input, pmcid: str) -> str | None:
    """Summarize an article by PMC ID."""
    article_json = extract_text_from_json(pmcid)
    if not article_json:
        print(f"Article JSON for {pmcid} not found.")
        return None
    prompt = f"Based on this user input: {user_input}, extract related information from the following article:\n\n{article_json}\n\n"
    response = await kernel.invoke_prompt(prompt, KernelArguments())
    print(f"Summary for {pmcid}:\n{response}\n")
    return str(response)

# async main
async def main():
    csv_path = "publications.csv"
    records = load_publications(csv_path)
    if not records:
        print("No publications found.")
        return

    user_input = input("Enter your search: ")

    # Get related PMC IDs
    related_ids = await related_pmcs(user_input, records)

    # Summarize each related article
    for pmcid in related_ids:
        await summarize_article(user_input, pmcid)

if __name__ == "__main__":
    asyncio.run(main())