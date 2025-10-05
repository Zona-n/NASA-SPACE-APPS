import os
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments

# Populate values from your OpenAI deployment
model_id = "gpt-4o"
endpoint = "https://azin2-nasa-space-apps-resource.openai.azure.com/"
# api_key = "6PVtkmaEivekvLcGjpIw9yuPBtDnmGfDYuh4SKoG1xTvPyjDucfwJQQJ99BJACHYHv6XJ3w3AAAAACOGF5NT"

# Create a kernel and add Azure OpenAI chat completion
kernel = Kernel()
kernel.add_service(
    AzureChatCompletion(
        deployment_name=model_id,
        endpoint=endpoint,
        api_key=api_key
    )
)

# Test the chat completion service
async def main():
    response = await kernel.invoke_prompt(
        "Give me a list of 10 travel destinations in Europe.",
        KernelArguments()
    )
    print("Assistant >", str(response))

asyncio.run(main())