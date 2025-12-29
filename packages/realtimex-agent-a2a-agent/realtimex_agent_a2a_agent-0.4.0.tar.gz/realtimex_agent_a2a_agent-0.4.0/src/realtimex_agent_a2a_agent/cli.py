from datetime import datetime
def print_time(text):
    # Get the current date and time
    now = datetime.now()

    # Extract and print only the time
    current_time = now.strftime("%H:%M:%S")
    print(f"{text}: ", current_time)

print_time("begin")

from .agent import RealTimeXAgent
 
import json
import os
import asyncio
import httpx
import sys
# from inputimeout import inputimeout, TimeoutOccurred
import threading

from any_agent.serving import A2AServingConfig
from any_agent import AgentConfig, AnyAgent

from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard

from uuid import uuid4

from a2a.types import MessageSendParams, SendMessageRequest, TaskState

print_time("after import")

# Create the httpx client
httpx_client = httpx.AsyncClient()

import nest_asyncio

nest_asyncio.apply()

async def run():
    print_time("begin run")
    # Prepare kwargs
    # print(sys.argv)
    payload = json.loads(sys.argv[1])
    # kwargs = {"workspace_slug": "test", "query": "hi", "messages": [{"role": "user", "content": "hi"}], "user_id": "user_14", "session_id": "500b4358-5d85-415d-acf0-8b12b4d896cc", "db_url": "sqlite:///C:\\Users\\Web team\\.realtimex.ai\\Resources/test_accounting_sessions.db", "default_model": "gpt-4o-mini", "litellm_api_key": "sk-tYJFmnnGzFpI9Tr1735989A9252944A9A8960c95FcCaD9Bc", "litellm_api_base": "https://llm.realtimex.ai/v1", "aci_linked_account_owner_id": "3e0bb6de-d64e-41f4-8cc7-f01a00398826", "aci_api_key": "b3bc24bb36ec940309e0dc31e22578f711b64038c7091ae92d59890dd03480a0", "agent_id": "63a42f8d-239d-4e2e-82bd-016d54110a90", "agent_data": {"name": "test-agent", "description": "Default RealTimeX Agent", "instructions": "You are the agent - please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user. Only terminate your turn when you are sure that the problem is solved, or if you need more info from the user to solve the problem.\n\nALWAYS ask required inputs from user to make sure to have correct inputs while calling functions.\n\nIf you are not sure about anything pertaining to the user's request, use your tools to read files and gather the relevant information: do NOT guess or make up an answer.\n\nYou MUST plan extensively before each function call, and reflect extensively on the outcomes of the previous function calls. DO NOT do this entire process by making function calls only, as this can impair your ability to solve the problem and think insightfully.\n\nRELATED MEMORIES:\n{##MEMORIES##}\n\nRELATED KNOWLEDGES:\n{##KNOWLEDGES##}", "execution_config": {"cmd": ["uvx", "realtimex-agent-a2a-agent"], "data": {}, "models": {"provider": "realtimexai", "default_model": "gpt-3.5-turbo"}, "framework": "tinyagent"}, "recommended_agent_flows": [], "recommended_aci_mcp_apps": []}, "thread_id": None, "knowledges": [], "memory_id": "aab7f86e-8f94-46a2-9f16-5bf0c58902dc", "memory_path": "C:\\Users\\Web team\\.realtimex.ai\\memories", "realtimex_access_token": "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJORlVmWGlMZHlxVmtSdGFJUlFGVGlZVXZBWXUwdXpSSXp2OEZaTGpnbGdnIn0.eyJleHAiOjE3NTYyODE2ODgsImlhdCI6MTc1NjI4MDc4OCwiYXV0aF90aW1lIjoxNzU2MTczNTA4LCJqdGkiOiI5NWRkYmFlNy03YmFjLTRlMzgtYTBlNi1kNDg0ODJkNWM2YjUiLCJpc3MiOiJodHRwczovL2FjY291bnRzLnJlYWx0aW1leC5jby9hdXRoL3JlYWxtcy9yZWFsdGltZXgiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiMGNhYTM5ZmItYzRiOS00MzYzLTljMmMtYWZjNDQ4ZDUyZjkwIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoicmVhbHRpbWV4LWFwcCIsIm5vbmNlIjoiY2Y0NGE3ZDctYjAyMy00NmQyLTllODktNDgyNmU0MGUxZDdmIiwic2Vzc2lvbl9zdGF0ZSI6IjEzOTRlZmRmLWEyZmMtNDgzMS1hM2FlLTBkYzgwNTMzZWVlNiIsImFjciI6IjEiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtcnR3b3JrLWluYyJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIG9mZmxpbmVfYWNjZXNzIGVtYWlsIHByb2ZpbGUiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmFtZSI6IlBodW9uZyBOZ3V5ZW4iLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJwaHVvbmdubTE1OTMiLCJnaXZlbl9uYW1lIjoiUGh1b25nIiwiZmFtaWx5X25hbWUiOiJOZ3V5ZW4iLCJlbWFpbCI6InBodW9uZ25tMTU5M0BnbWFpbC5jb20ifQ.jYWqbKAvXND5fACOBCsi6PPJkU7yDGwnqgJ-qSn0Wz2hSzRYl4Gymc2HSlLASO4aDO24Ar7Ob4R26xpAyfkXMjFWHR94MxajK9CZlVfV4NOpVCRXq1R--3aNA1oNWu-FbRMDKNQIJDd1se2fjJfMa79C9yVXlUs2R_-1ktTHjBnblsWkkh2p8frGNKsLq_kacXpV4YGe5IAf96z5XfYJKTV2ykVFPV67f5-brlNfXLBx88I0ZGY41K_VCkoL0wsHUB1FlBjHzfomsRfHrjMzrIFvx1B6tIV-kLOnjeuDZdysmtjR0L7w4gKsXxRl2bV8B0lWqHknytEnvciMZduDEQ"}

    a2a_port = sys.argv[2]

    system_prompt = None
    agent_framework = None
    agent_description = None
    default_model = None
    provider_name = None
    llm_setting = None

    agent_id = payload["agent_id"]
    agent_data = payload["agent_data"]
    user_id = payload["user_id"]
    workspace_slug = payload["workspace_slug"]
    thread_id = payload["thread_id"]
    knowledges = payload["knowledges"]
    memory_id = payload["memory_id"]
    memory_path = payload["memory_path"]
    execution_id = payload["session_id"]
    message = payload["query"]
    messages = payload["messages"]
    aci_linked_account_owner_id = payload["aci_linked_account_owner_id"]
    aci_agent_first_api_key = payload["aci_api_key"]
    realtimex_access_token = payload["realtimex_access_token"]


    if "agent_description" in payload:
        agent_description = payload["agent_description"]
    if "agent_framework" in payload:
        agent_framework = payload["agent_framework"]
    if "system_prompt" in payload:
        system_prompt = payload["system_prompt"]
    if "llm_setting" in payload:
        llm_setting = payload["llm_setting"]

    default_openai_base_url = payload["litellm_api_base"]
    default_openai_api_key = payload["litellm_api_key"]

    # Load MCP tools
    
    # Create agent
    agent = RealTimeXAgent(current_session_id=execution_id)

    await agent.load_default_agent(agent_id, agent_data, payload)
    
    server_url = await agent.serve_as_a2a(
        a2a_serving_config={"port":a2a_port,"stream_tool_usage":True}
    )

    print(f"<server-url>{server_url}</server-url>")

    # input("Waiting...")

    # async with httpx.AsyncClient() as client:
    #     while True:
    #         try:
    #             await client.get(server_url, timeout=1.0)
    #             print(f"Server is ready at {server_url}")

    #             agent_card: AgentCard = await A2ACardResolver(
    #                 httpx_client,
    #                 base_url=server_url,
    #             ).get_agent_card(http_kwargs=None)
    #             # print(agent_card.model_dump_json(indent=2))

    #             client = A2AClient(httpx_client=httpx_client, agent_card=agent_card)

    #             send_message_payload = {
    #                 "message": {
    #                     "role": "user",
    #                     "parts": [{"kind": "text", "text": f"{message}"}],
    #                     "messageId": uuid4().hex,
    #                     # "contextId": "bce7de7a-5050-4b74-822c-af0e13073036",  # Same context to continue conversation
    #                     # "taskId": "159e8a1b-788c-47ef-998d-9419b8f5fb5a",  # type: ignore[union-attr]
    #                 },
    #             }
    #             request = SendMessageRequest(
    #                 id=str(uuid4()), params=MessageSendParams(**send_message_payload)
    #             )
    #             response = await client.send_message(request, http_kwargs={"timeout": 300.0})
    #             print("response",response)
    #             # response = json.loads(response.root.result.status.message.parts[0].root.text)
    #             # # print(response["result"])
    #             # print("response",response)
    #             response_message = response.root.result.status.message
    #             response_text = json.loads(response_message.parts[0].root.text)["result"]
    #             response_state = response.root.result.status.state
    #             context_id = response.root.result.context_id
    #             task_id = response.root.result.id

    #             message_content = {
    #                 "uuid": str(uuid4()),
    #                 "type": "responseData",
    #                 "content": response_text,
    #                 "dataType": "markdown",
    #                 "data": {"content": response_text, "language": None},
    #             }

    #             print(f"<message>{json.dumps(message_content)}</message>")
    #             print(f"<signal>session-end</signal>")

                
                
    #             # while response_state == TaskState.input_required:
    #             while True:
    #                 # user_input = input(response_text)
    #                 user_input = input('Enter message: ')
    #                 if user_input is None:
    #                     break
                    
    #                 if response_state == TaskState.completed:
    #                     send_message_payload = {
    #                         "message": {
    #                             "role": "user",
    #                             "parts": [{"kind": "text", "text": f"{user_input}"}],
    #                             "messageId": uuid4().hex,
    #                             "contextId": response.root.result.context_id,  # Same context to continue conversation
    #                         },
    #                     }
    #                 else:
    #                     send_message_payload = {
    #                         "message": {
    #                             "role": "user",
    #                             "parts": [{"kind": "text", "text": f"{user_input}"}],
    #                             "messageId": uuid4().hex,
    #                             "contextId": response.root.result.context_id,  # Same context to continue conversation
    #                             "taskId": response.root.result.id,  # type: ignore[union-attr]
    #                         },
    #                     }

    #                 request = SendMessageRequest(
    #                     id=str(uuid4()), params=MessageSendParams(**send_message_payload)
    #                 )
    #                 response = await client.send_message(request, http_kwargs={"timeout": 300.0})

    #                 print("send_message_payload",send_message_payload)
    #                 print("response",response)

    #                 response_message = response.root.result.status.message
    #                 response_text = json.loads(response_message.parts[0].root.text)["result"]
    #                 response_state = response.root.result.status.state

    #                 message_content = {
    #                     "uuid": str(uuid4()),
    #                     "type": "responseData",
    #                     "content": response_text,
    #                     "dataType": "markdown",
    #                     "data": {"content": response_text, "language": None},
    #                 }

    #                 print(f"<message>{json.dumps(message_content)}</message>")
    #                 print(f"<signal>session-end</signal>")


                

    #             # print(response)
    #             # Close the httpx client when done
    #             await httpx_client.aclose()

    #             break
    #         except (httpx.RequestError, httpx.TimeoutException):
    #             await asyncio.sleep(poll_interval)
    #             attempts += 1
    #             if attempts >= max_attempts:
    #                 msg = f"Could not connect to {server_url}. Tried {max_attempts} times with {poll_interval} second interval."
    #                 raise ConnectionError(msg)


    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.get(server_url, timeout=1.0)
                print(f"<signal>server-listening</signal>")
            except (httpx.RequestError, httpx.TimeoutException):
                print(f"<signal>server-stopped</signal>")
            await asyncio.sleep(30)


def main():
    print_time("begin main")
    asyncio.run(run())
