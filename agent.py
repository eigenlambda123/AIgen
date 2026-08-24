from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.tools import tool

llm = ChatOllama(model="qwen2.5:7b")

# tools
@tool
def calculator(expression: str) -> str:
    """A calculator that can evaluate mathematical expressions."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# we can add all created tools here
tools = [calculator]

# the actual agent build
agent = create_agent(
    model=llm,  
    tools=tools,
    system_prompt="You are a helpful assistant."
)

# user input
user_query = "what is 1+1?"

# full response
response = agent.invoke({
    "messages": [{"role": "user", "content": user_query}]
})

ai_response = response["messages"][-1].content

print("\nResponse:")
print(ai_response)