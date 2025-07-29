import time
import json
import os

from azure.ai.agents.models import McpTool, MessageTextContent, ListSortOrder, SubmitToolApprovalAction, RequiredMcpToolCall, ToolApproval
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

PROJECT_ENDPOINT = os.environ["PROJECT_ENDPOINT"] 
MODEL_DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_MODEL_DEPLOYMENT_NAME"]

mcp_tool = McpTool(
    server_label="git",
    server_url="https://gitmcp.io/Azure/azure-rest-api-specs",
    allowed_tools=[],  # Optional
)

# Create an AIProjectClient instance
project_client = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential()
)

with project_client:

    agents_client = project_client.agents

    # Create an agent with the MCP tool
    agent = agents_client.create_agent(
        model=MODEL_DEPLOYMENT_NAME,
        name="my-mcp-agent", 
        instructions="""You are a helpful assistant.
        Use the tools provided to answer the user's questions. 
        Be sure to cite your sources.""", 
        tools=mcp_tool.definitions,
    )

    print(f"Created agent, ID: {agent.id}")

    # Create a thread for communication
    thread = agents_client.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Add a message to the thread
    message = agents_client.messages.create(
        thread_id=thread.id,
        role="user",  # Role of the message sender
        content="Please summarize the Azure REST API specifications Readme",  # Message content
    )
    print(f"Created message, ID: {message['id']}")


    mcp_tool.update_headers("SuperSecret", "123456")
       
    # By default require_approval is set to "always"
    print(f"mcp_tool.require_approval: {mcp_tool._require_approval}")

    # Create and automatically process the run, handling tool calls internally
    run = agents_client.runs.create(thread_id=thread.id, agent_id=agent.id)

    # Poll the run as long as run status is queued or in progress
    while run.status in ["queued", "in_progress", "requires_action"]:
        # Wait for a second
        time.sleep(1)
        run = agents_client.runs.get(thread_id=thread.id, run_id=run.id)
        
        if run.status == "requires_action" and isinstance(run.required_action, SubmitToolApprovalAction):
            tool_calls = run.required_action.submit_tool_approval.tool_calls
            if not tool_calls:
                print("No tool calls provided - cancelling run")
                agents_client.runs.cancel(thread_id=thread.id, run_id=run.id)
                break

            tool_approvals = []
            for tool_call in tool_calls:
                if isinstance(tool_call, RequiredMcpToolCall):
                    try:
                        print(f"Approving tool call: {tool_call}")
                        tool_approvals.append(
                            ToolApproval(
                                tool_call_id=tool_call.id,
                                approve=True,
                                headers=mcp_tool.headers,
                            )
                        )
                    except Exception as e:
                        print(f"Error approving tool_call {tool_call.id}: {e}")

            print(f"tool_approvals: {tool_approvals}")
            if tool_approvals:
                agents_client.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_approvals=tool_approvals
                )

        print(f"Current run status: {run.status}")

    if run.status == "failed":
        print(f"Run error: {run.last_error}")


    # Retrieve the generated response:
        # By default it is descending order, if you want ascending order, use ListSortOrder.ASCENDING
    messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    print("\nConversation:")
    print("-" * 50)

    for msg in messages:
        if msg.text_messages:
            last_text = msg.text_messages[-1]
            print(f"{msg.role.upper()}: {last_text.text.value}")
            print("-" * 50)


    agents_client.delete_agent(agent.id)
    print(f"\nDeleted agent, agent ID: {agent.id}")