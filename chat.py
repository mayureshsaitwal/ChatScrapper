# from litellm import completion
#
# response = completion(
#     model="ollama_chat/llama3.2",
#     messages=[{ "content": "respond in 20 words. who are you?","role": "user"}],
# )
# print(response)
# print(response.content)

import litellm 
litellm._turn_on_debug() # turn on debug to see the request
from litellm import completion

response = completion(
    model="ollama/llama3.2",
    prompt="Hello, world!",
    api_base="http://localhost:11434"
)
print(response)
