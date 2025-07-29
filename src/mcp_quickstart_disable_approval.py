import time
import json
import os

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import McpTool, MessageTextContent, ListSortOrder
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

####################################################################################################
# This code does not work regarding mcp_tool.set_approval_mode("never")
# Even if we have set the approval mode to "never", the MCP tool still requires approval.

# Sample run result:
# ```
# > uv run .\src\mcp_quickstart_disable_approval.py
# Created agent, agent ID: asst_arGl3z9FnBFvKeWxAzsfv4zV
# Created thread, thread ID: thread_6qTiSt9cC7Z9uhujRDle0EQE
# Created message, message ID: msg_UOq9CEfFIYd4mZ27SrmoJRTP
# mcp_tool.require_approval: never
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.IN_PROGRESS
# Run status: RunStatus.REQUIRES_ACTION
# Run status: RunStatus.REQUIRES_ACTION
# Run status: RunStatus.REQUIRES_ACTION
# ````
####################################################################################################


load_dotenv()

PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"] 
MODEL_DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"]

mcp_tool = McpTool(
    server_label="git",
    server_url="https://gitmcp.io/Azure/azure-rest-api-specs",
    allowed_tools=[],  # Optional
)

project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

with project_client:
    agent = project_client.agents.create_agent(
        model=MODEL_DEPLOYMENT_NAME, 
        name="my-mcp-agent", 
        instructions="You are a helpful assistant. Use the tools provided to answer the user's questions. Be sure to cite your sources.",
        tools=mcp_tool.definitions,
        tool_resources=None
    )
    print(f"Created agent, agent ID: {agent.id}")

    thread = project_client.agents.threads.create()
    print(f"Created thread, thread ID: {thread.id}")

    message = project_client.agents.messages.create(
        thread_id=thread.id, role="user", content="<query related to your MCP server>",
    )
    print(f"Created message, message ID: {message.id}")

    # Handle tool approvals
    mcp_tool.update_headers("SuperSecret", "123456")
    mcp_tool.set_approval_mode("never")  # Uncomment to disable approval requirements
    print(f"mcp_tool.require_approval: {mcp_tool._require_approval}")

    run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)

    # Poll the run as long as run status is queued or in progress
    while run.status in ["queued", "in_progress", "requires_action"]:
        # Wait for a second
        time.sleep(1)
        run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)
        print(f"Run status: {run.status}")

    if run.status == "failed":
        print(f"Run error: {run.last_error}")

    run_steps = project_client.agents.run_steps.list(thread_id=thread.id, run_id=run.id)
    for step in run_steps:
        print(f"Run step: {step.id}, status: {step.status}, type: {step.type}")
        if step.type == "tool_calls":
            print(f"Tool call details:")
            for tool_call in step.step_details.tool_calls:
                print(json.dumps(tool_call.as_dict(), indent=2))

    messages = project_client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    for data_point in messages:
        last_message_content = data_point.content[-1]
        if isinstance(last_message_content, MessageTextContent):
            print(f"{data_point.role}: {last_message_content.text.value}")

    project_client.agents.delete_agent(agent.id)
    print(f"\nDeleted agent, agent ID: {agent.id}")