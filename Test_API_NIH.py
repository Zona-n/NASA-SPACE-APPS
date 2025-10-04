# import requests
# import json

# url = "https://api.reporter.nih.gov/v2/publications/search"
# payload = {
#     "criteria": {
#         "pmids": [25058045]
#     },
#     "offset": 0,
#     "limit": 10,
#     "sort_field": "core_project_num",
#     "sort_order": "asc"
# }
# response = requests.post(url, json=payload)
# print(response.json())

import requests
import json

pmcID = "PMC4136787"
url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmcID}/unicode"

response = requests.get(url)
if response.status_code == 200:
    # try:
    data = response.json()
    with open("bioc_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("✅ Data saved to bioc_output.json")

        # print("Raw JSON:", data)

    #     # If data is a list, access the first item directly
    #     if isinstance(data, list):
    #         first_doc = data[0]
    #     elif isinstance(data, dict):
    #         first_doc = data.get("documents", [{}])[0]
    #     else:
    #         print("Unexpected data format.")
    #         exit()

    #     passages = first_doc.get("passages", [])
    #     for i, passage in enumerate(passages):
    #         text = passage.get("text", "").strip()
    #         if text:
    #             print(f"Passage {i+1}: {text}\n")

    # except Exception as e:
    #     print("Error parsing JSON:", e)
else:
    print("Error:", response.status_code)
