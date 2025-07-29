import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import CodeInterpreterTool

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Create an Azure AI Client from an endpoint, copied from your Azure AI Foundry project.
# You need to login to Azure subscription via Azure CLI and set the environment variables
project_endpoint = os.environ["PROJECT_ENDPOINT"]  # Ensure the PROJECT_ENDPOINT environment variable is set

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),  # Use Azure Default Credential for authentication
    # if get error of "(BadRequest) API version not supported", 
    #   check the API version by clicking into the AIProjectClient definition as part of SDK
    api_version="2025-05-15-preview"
)

code_interpreter = CodeInterpreterTool()
with project_client:
    # Create an agent with the Bing Grounding tool
    agent = project_client.agents.create_agent(
        model=os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"],  # Model deployment name
        name="my-agent",  # Name of the agent
        instructions="You are a helpful agent",  # Instructions for the agent
        tools=code_interpreter.definitions,  # Attach the tool
    )
    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")
    
    # Add a message to the thread
    message = project_client.agents.messages.create(
        thread_id=thread.id,
        role="user",  # Role of the message sender
        content="What is the weather in Seattle today?",  # Message content
    )
    print(f"Created message, ID: {message['id']}")
    
    # Create and process an agent run
    run = project_client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")
    
    # Check if the run failed
    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    
    # Fetch and log all messages
    messages = project_client.agents.messages.list(thread_id=thread.id)
    for message in messages:
        print(f"Role: {message.role}, Content: {message.content}")
    
    # Delete the agent when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")