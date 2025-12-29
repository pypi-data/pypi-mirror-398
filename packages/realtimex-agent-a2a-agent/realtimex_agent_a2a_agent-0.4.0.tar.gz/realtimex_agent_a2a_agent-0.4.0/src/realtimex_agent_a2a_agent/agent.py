from any_agent import AgentConfig, AnyAgent
from any_agent.config import MCPStdio
import json
import os
from typing import Callable, Dict, Literal, Optional, Union, Any

from .tools import send_email
from .callbacks.tool_execution import ShowToolCalling
from any_agent.callbacks import get_default_callbacks
from mem0 import Memory
from any_agent.tools import a2a_tool_async
from any_agent.serving import A2AServingConfig


MEMORIES_GLOBAL_VIRTUAL_ROOT = "/memories/global/"
MEMORIES_WORKSPACE_VIRTUAL_ROOT_PREFIX = "/memories/workspace/"
SKILLS_GLOBAL_VIRTUAL_ROOT = "/skills/global/"
SKILLS_WORKSPACE_VIRTUAL_ROOT_PREFIX = "/skills/workspace/"


def get_user_dir():
    return os.path.join(os.path.expanduser("~"),".realtimex.ai")

def get_base_user_dir():
    return os.path.join(os.path.expanduser("~"))

def get_uvx_executable():
    unix_realtimex_uvx_path = os.path.join(get_user_dir(),"Resources","envs","bin","uvx")
    if os.path.exists(unix_realtimex_uvx_path):
        return unix_realtimex_uvx_path
    win_realtimex_uvx_path = os.path.join(get_user_dir(),"Resources","envs","Scripts","uvx.exe")
    if os.path.exists(win_realtimex_uvx_path):
        return win_realtimex_uvx_path
    return "uvx"

def get_nvm_dir():
    path = os.path.join(get_base_user_dir(),".nvm")
    if os.path.exists(path):
        return path
    path = os.path.join('c:', os.sep, "nvm")
    if os.path.exists(path):
        return path
    return ""


def get_nvm_inc():
    # /Users/phuongnguyen/.nvm/versions/node/v22.16.0/include/node
    path = os.path.join(get_nvm_dir(),"versions","node","v22.16.0","include","node")
    if os.path.exists(path):
        return path
    path = os.path.join('c:', os.sep, "nvm")
    if os.path.exists(path):
        return path
    return ""

def get_nvm_bin():
    # /Users/phuongnguyen/.nvm/versions/node/v22.16.0/include/node
    path = os.path.join(get_nvm_dir(),"versions","node","v22.16.0","bin")
    if os.path.exists(path):
        return path
    path = os.path.join('c:', os.sep, "nvm")
    if os.path.exists(path):
        return path
    return ""

def get_npx_executable():
    unix_realtimex_npx_path = os.path.join(get_base_user_dir(),".nvm","versions","node","v22.16.0","bin","npx")
    if os.path.exists(unix_realtimex_npx_path):
        return unix_realtimex_npx_path
    win_realtimex_npx_path = os.path.join('c:', os.sep, "nvm", "v22.16.0", "npx.cmd")
    if os.path.exists(win_realtimex_npx_path):
        return win_realtimex_npx_path
    return "npx"


def get_deepagents_agent_path(scope, agent_id, workspace_slug=None):
    """
    Get the agent.md path for DeepAgents.
    
    Args:
        scope: 'global' or 'workspace'
        agent_id: The agent identifier
        workspace_slug: Required when scope is 'workspace'
    
    Returns:
        Path string if file exists, None otherwise
    """
    if scope == "global":
        path = os.path.join(
            get_user_dir(), "Resources", "agent-skills", "global", agent_id, "agent.md"
        )
    elif scope == "workspace" and workspace_slug:
        path = os.path.join(
            get_user_dir(), "Resources", "agent-skills", "workspaces", workspace_slug, agent_id, "agent.md"
        )
    else:
        return None
    
    return path if os.path.isfile(path) else None


def get_deepagents_skills_dir(scope, agent_id, workspace_slug=None):
    """
    Get the skills directory path for DeepAgents.
    
    Args:
        scope: 'global' or 'workspace'
        agent_id: The agent identifier
        workspace_slug: Required when scope is 'workspace'
    
    Returns:
        Path string if directory exists, None otherwise
    """
    if scope == "global":
        path = os.path.join(
            get_user_dir(), "Resources", "agent-skills", "global", agent_id, "skills"
        )
    elif scope == "workspace" and workspace_slug:
        path = os.path.join(
            get_user_dir(), "Resources", "agent-skills", "workspaces", workspace_slug, agent_id, "skills"
        )
    else:
        return None
    
    return path if os.path.isdir(path) else None

class RealTimeXAgent():
    def __init__(
        self, current_session_id
    ):
        self.agent_id: str = None
        self.agent_data: Dict = None
        self.agent: AnyAgent = None
        self.agent_name: str = None
        self.system_prompt: str = None
        self.agent_framework: str = None
        self.agent_description: str = None
        self.default_model:str = None
        self.recommended_agent_flows = None
        self.recommended_aci_mcp_apps = None
        self.recommended_local_mcp_apps = None
        self.recommended_team_members = None
        self.memory:Memory = None

        self.current_session_id = current_session_id

    async def prepare_llm(self, provider_name,model_name,api_base,api_key):
        def get_provider_name(provider_name):
            if provider_name == "realtimexai":
                return "openai"
            elif provider_name == "litellm":
                return "openai"
            elif provider_name == "openai":
                return "openai"
            elif provider_name == "ollama":
                return "ollama"
            elif provider_name == "gemini":
                return "google"
            elif provider_name == "google":
                return "google"
        
        def get_model_name(model_name):
            return model_name

        provider_name = get_provider_name(provider_name)
        model_name = get_model_name(model_name)

        # if provider_name == "openai":
        #     os.environ['OPENAI_BASE_URL'] = api_base
        #     os.environ['OPENAI_API_KEY'] = api_key

        # return {
        #     "api_base": api_base,
        #     "api_key": api_key,
        #     "model_id": f"{provider_name}:{model_name}"
        # }

        return {
            "api_base": api_base,
            "api_key": api_key,
            "model_id": f"{provider_name}/{model_name}"
        }

        # return {
        #     "api_base": api_base,
        #     "api_key": api_key,
        #     "model_id": model_name
        # }

    async def create_subagents(self,instructions=None,tools=[],llm_config=None):
        from openai import OpenAI
        client = OpenAI(
            api_key=llm_config["api_key"],
            base_url=llm_config["api_base"],
        )

        system_prompt = self.system_prompt
        if not instructions:
            system_prompt = instructions
        
        schema = {
            "title": "subagents",
            "description": "The list of subagents to do the task well and effectively.",
            "required": [
                "subagents",
            ],
            "type": "object",
            "properties": {
                "subagents":{
                    "type": "array",
                    "description": "The list of subagents to do the task well and effectively.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the sub-agent"
                            },
                            "description": {
                                "type": "string",
                                "description": "A description of the sub-agent"
                            },
                            "prompt": {
                                "type": "string",
                                "description": "The prompt used by the sub-agent"
                            },
                            # "tools": {
                            #     "type": "array",
                            #     "description": "Optional list of tools name the sub-agent can use",
                            #     "items": {
                            #         "type": "string"
                            #     }
                            # }
                        },
                        "required": ["name", "description", "prompt"],
                        "additionalProperties": False
                    }
                }
            },
            "additionalProperties": False
        }

        # print("schema", json.dumps(schema))

        response_format = { "type": "json_schema", "json_schema": {"strict": True, "name": schema["title"], "schema": schema}}

#         tools_str = ""
#         for tool in tools:
#             tools_str = f"""{tools_str}
#   - {tool.__name__}: {tool.__doc__}"""

        completion = client.beta.chat.completions.parse(
            model=llm_config["model_id"],
            messages=[{"role": "system", "content": 
f"""You are tasked with designing a small team of specialized subagents to work together under the guidance of the main agent.

* The main agent’s role and purpose is defined by:
  {system_prompt}

Your job is to create **no more than 5 subagents**. Each subagent must include:

1. Name: lowercase, short, clear, and distinct, only alphabets and underscore allowed.
2. Description: what this subagent is specialized at and how it contributes to the team.
3. System Prompt: clear instructions that define the subagent’s behavior, style, and responsibilities.

Guidelines:

* Each subagent should have a well-defined, non-overlapping role.
* The team should collectively cover all major aspects required for the main agent’s purpose.
* Avoid redundancy—each subagent must bring unique value.
* Keep the team **small (≤5 subagents)** but **effective**.

Finally, return the result as a list of subagent objects in JSON format."""},
                {"role": "user", "content": "Create a team of subagents to do task: {}"},
            ],

            response_format=response_format,
        )



        result = json.loads(completion.choices[0].message.content)

        return result["subagents"]
            
        
    async def prepare_realtimex_agent(self, agent_id, agent_data):
        # directus_client = DirectusClient(server_url = directus_server_url,access_token = directus_access_token)

        # d_agent = directus_client.get_directus_item_by_id("realtimex_agents",agent_id)

        agent_name = agent_data["name"]
        agent_description = agent_data["description"]
        system_prompt = agent_data["instructions"]
        agent_framework = agent_data["execution_config"]["framework"]
        default_model = agent_data["execution_config"]["models"]["default_model"]

        recommended_agent_flows = None
        if "recommended_agent_flows" in agent_data:
            recommended_agent_flows = agent_data["recommended_agent_flows"]

        recommended_aci_mcp_apps = None
        if "recommended_aci_mcp_apps" in agent_data:
            recommended_aci_mcp_apps = agent_data["recommended_aci_mcp_apps"]

        recommended_local_mcp_apps = None
        if "recommended_local_mcp_apps" in agent_data:
            recommended_local_mcp_apps = agent_data["recommended_local_mcp_apps"]
            
        recommended_team_members = None
        if "recommended_team_members" in agent_data:
            recommended_team_members = agent_data["recommended_team_members"]

        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.agent_framework = agent_framework
        self.agent_description = agent_description
        self.default_model = default_model
        self.agent_id = agent_id
        self.agent_data = agent_data
        self.recommended_agent_flows = recommended_agent_flows
        self.recommended_aci_mcp_apps = recommended_aci_mcp_apps
        self.recommended_local_mcp_apps = recommended_local_mcp_apps
        self.recommended_team_members = recommended_team_members

    async def prepare_memory(self,memory_id, memory_path, litellm_base_url, litellm_api_key):
        pass
        # config_dict = {
        #     "version": "v1.1",
        #     "vector_store": {
        #         "provider": "chroma",
        #         "config": {
        #             "collection_name": memory_id,
        #             "path": memory_path,
        #         }
        #     },
        #     "llm": {"provider": "openai", "config": {"api_key": litellm_api_key, "openai_base_url": litellm_base_url, "temperature": 0.2, "model": "gpt-4o-mini"}},
        #     "embedder": {"provider": "openai", "config": {"api_key": litellm_api_key, "openai_base_url": litellm_base_url, "model": "text-embedding-3-small"}},
        #     "history_db_path": "",
        # }
        # print("config_dict",config_dict)
        # memory = Memory.from_config(config_dict=config_dict)
        # self.memory = memory

    async def load_default_callbacks(self):
        return [ShowToolCalling(),*get_default_callbacks()]

    async def load_default_tools(self):
        return []

    async def load_aci_mcp_tools(self, linked_account_owner_id, aci_api_key):
        from any_agent.config import MCPStdio
        mcp_apps = []
        for app in self.recommended_aci_mcp_apps:
            if "realtimex_mcp_server_id" in app:
                mcp_apps.append(app["realtimex_mcp_server_id"]["name"])
            else:
                mcp_apps.append(app["name"])
        # mcp_apps = [app["realtimex_mcp_server_id"]["name"] for app in self.recommended_aci_mcp_apps]
        if len(mcp_apps)>0:
            mcp = MCPStdio(
                # command=get_uvx_executable(),
                # args=["aci-mcp@latest", 'apps-server', '--apps', ','.join(mcp_apps) , '--linked-account-owner-id', linked_account_owner_id],
                command="aci-mcp",
                args=['apps-server', '--apps', ','.join(mcp_apps) , '--linked-account-owner-id', linked_account_owner_id],
                client_session_timeout_seconds=300,
                env={
                    "ACI_SERVER_URL":"https://mcp.realtimex.ai/v1/",
                    "ACI_API_KEY":aci_api_key
                }
            )
            return mcp
        return None

    async def load_local_mcp_tools(self):
        from any_agent.config import MCPStdio
        mcp_apps = [app["config"] for app in self.recommended_local_mcp_apps]
        # mcp_apps = [
        #     {"command":"uvx","args":["mcp-shell-server"],"env":{"ALLOW_COMMANDS":"ls,cat,pwd,grep,wc,touch,find"}}
        # ]
        mcps = []
        default_env = {
            'NVM_INC': get_nvm_inc(),
            'NVM_CD_FLAGS': '-q',
            'NVM_DIR': get_nvm_dir(),
            'PATH': f'{os.environ.copy()["PATH"]}{os.pathsep}{get_nvm_bin()}',
            'NVM_BIN': get_nvm_bin()
        }
        for mcp_app in mcp_apps:
            if mcp_app["command"] == "uvx":
                mcp_app["command"] = get_uvx_executable()
            if mcp_app["command"] == "npx":
                mcp_app["command"] = get_npx_executable()
            if "env" not in mcp_app:
                mcp_app["env"] = {}
            mcp_app["env"] = {**mcp_app["env"],**default_env}
            # print("mcp_app",mcp_app)
            mcp = MCPStdio(
                **mcp_app,
                client_session_timeout_seconds=300,
            )
            mcps.append(mcp)
        return mcps

    async def load_mcp_agent_flow_tools(self, linked_account_owner_id, aci_api_key, litellm_base_url, litellm_api_key, realtimex_access_token, workspace_slug, thread_id):
        from any_agent.config import MCPStdio
        agent_flow_ids = [flow["realtimex_agent_flows_id"]["id"] for flow in self.recommended_agent_flows]
        if len(agent_flow_ids)>0:
            mcp = MCPStdio(
                # command=get_uvx_executable(),
                # args=["--from", "git+https://oauth2:5yTHSE9k34jbWgzXmsxQ@rtgit.rta.vn/rtlab/rtwebteam/mcp-servers/realtimex-ai-agent-flows@main","agent-flows-mcp-server",'--flows',','.join(agent_flow_ids)],
                command="agent-flows-mcp-server",
                args=['--flows',','.join(agent_flow_ids)],
                client_session_timeout_seconds=300,
                env={
                    "AGENT_FLOWS_API_KEY": realtimex_access_token,
                    "LITELLM_API_KEY": litellm_api_key,
                    "LITELLM_API_BASE": litellm_base_url,
                    "MCP_ACI_API_KEY": aci_api_key,
                    "MCP_ACI_LINKED_ACCOUNT_OWNER_ID": linked_account_owner_id,
                    "SESSION_ID": self.current_session_id,
                    "WORKSPACE_SLUG": workspace_slug,
                    "THREAD_ID": thread_id,
                    "AGENT_ID": self.agent_id,
                    # "AGENT_FLOWS_BASE_URL": "https://your-custom-instance.com"  # Optional
                }
            )
            return mcp
        return None

    async def load_a2a_agents_as_tools(self):
        def get_free_port():
            import socket
            sock = socket.socket()
            sock.bind(('', 0))
            return sock.getsockname()[1]

    
        tools = []
        for a2a_agent in self.recommended_team_members:
            agent_id = a2a_agent["agent_id"]
            agent_data = a2a_agent["agent_data"]
            a2a_port = get_free_port()
            # Create agent
            agent = RealTimeXAgent()

            await agent.load_default_agent(agent_id, agent_data, payload=a2a_agent)
            
            agent_server_url = await agent.serve_as_a2a(
                a2a_serving_config={"port":a2a_port,"stream_tool_usage":True},
            )

            # print(agent_server_url)

            tools.append(
                await a2a_tool_async(
                    agent_server_url,
                    http_kwargs={
                        "timeout": 300
                    },  # This gives the time agent up to 30 seconds to respond to each request
                )
            )


        return tools

    async def load_knowledges(self,query, user_id, workspace_slug, thread_id, knowledges=["thread"]):
        memory_session_id = None
        if "user" in knowledges:
            memory_session_id = None
        elif "workspace" in knowledges:
            memory_session_id = workspace_slug
        elif "thread" in knowledges:
            memory_session_id = f"{workspace_slug}_{thread_id}"
        # print("memory_session_id",memory_session_id)
        history_memories = self.memory.search(query=query, user_id=user_id, run_id=memory_session_id,limit=5)
        # history_memories = self.memory.get_all(user_id=user_id, run_id=memory_session_id,limit=20)
        # print("history_memories",history_memories)
        
        memories_str = "\n".join(f"- {entry['memory']}" for entry in history_memories["results"])

        knowledges_str = ""
        all_knowledge_memories = []
        for knowledge_id in knowledges:
            if knowledge_id in ["account","workspace","thread"]:
                continue
            knowledge_memories = self.memory.search(query=query, user_id=user_id, run_id=knowledge_id, limit=5)
            all_knowledge_memories = [*all_knowledge_memories,*knowledge_memories["results"]]

        knowledges_str = "\n".join(f"- {entry['memory']}" for entry in all_knowledge_memories)
        return memories_str, knowledges_str


    async def create_agent(self, agent_framework="tinyagent",agent_config=None,tools=[],callbacks=[], memories_str=None, knowledges_str=None):
        default_agent_config = {
            "name": self.agent_name,
            "model_id": self.default_model,
            "description": self.agent_description,
            "instructions": self.system_prompt,
            "tools": tools,
            "callbacks": callbacks
        }

        default_agent_framework = self.agent_framework

        if agent_config:
            default_agent_config.update(agent_config)

        if agent_framework:
            default_agent_framework = agent_framework
        
        # print("default_agent_config", default_agent_config)
        # print("agent_config", agent_config)

        if memories_str:
            default_agent_config["instructions"] = default_agent_config["instructions"].replace("##MEMORIES##",memories_str)
        if knowledges_str:
            default_agent_config["instructions"] = default_agent_config["instructions"].replace("##KNOWLEDGES##",knowledges_str)
        # print(default_agent_framework)
        # print(default_agent_config)

        self.agent = await AnyAgent.create_async(
            default_agent_framework,  # See all options in https://mozilla-ai.github.io/any-agent/
            AgentConfig(
                **default_agent_config,
                current_session_id=self.current_session_id,
                # agent_args={
                #     "interrupt_after":["get_user_info"]
                # }
            ),
        )
        
        return self.agent
    
    async def serve_as_a2a(self, a2a_serving_config):
        handle = await self.agent.serve_async(A2AServingConfig(**a2a_serving_config))
        server_port = handle.port
        server_url = f"http://localhost:{server_port}"

        return server_url

    async def load_default_agent(self, agent_id, agent_data, payload):
        system_prompt = None
        agent_framework = None
        agent_description = None
        agent_name = None
        default_model = None
        provider_name = None
        llm_setting = None

        user_id = payload["user_id"]
        workspace_slug = payload["workspace_slug"]
        thread_id = payload["thread_id"]
        knowledges = payload["knowledges"]
        memory_id = payload["memory_id"]
        memory_path = payload["memory_path"]
        execution_id = payload["session_id"]
        aci_linked_account_owner_id = payload["aci_linked_account_owner_id"]
        aci_agent_first_api_key = payload["aci_api_key"]
        realtimex_access_token = payload["realtimex_access_token"]

        agent_description = agent_data["description"]
        agent_name = agent_data["name"]
        agent_framework = agent_data["execution_config"]["framework"]

        if "agent_description" in payload:
            agent_description = payload["agent_description"]
        if "agent_name" in payload:
            agent_name = payload["agent_name"]
        if "agent_framework" in payload:
            agent_framework = payload["agent_framework"]
        if "system_prompt" in payload:
            system_prompt = payload["system_prompt"]
        if "llm_setting" in payload:
            llm_setting = payload["llm_setting"]            
            

        default_openai_base_url = payload["litellm_api_base"]
        default_openai_api_key = payload["litellm_api_key"]

        # Load MCP tools
        
        # # Create agent
        # agent = RealTimeXAgent()

        # print("agent_data")

        await self.prepare_realtimex_agent(
            agent_id=agent_id,
            agent_data=agent_data
        )
        
        # await self.prepare_memory(memory_id=memory_id, memory_path=memory_path, litellm_base_url=default_openai_base_url, litellm_api_key=default_openai_api_key)

        default_callbacks = await self.load_default_callbacks()
        
        default_tools = await self.load_default_tools()
        all_tools = [*default_tools]
        
        if self.recommended_aci_mcp_apps:
            aci_mcp = await self.load_aci_mcp_tools(
                linked_account_owner_id=aci_linked_account_owner_id,
                aci_api_key=aci_agent_first_api_key
            )
            if aci_mcp:
                all_tools = [*all_tools,aci_mcp]

        if self.recommended_local_mcp_apps:
            local_mcps = await self.load_local_mcp_tools()
            # print("local_mcps",local_mcps)
            all_tools = [*all_tools,*local_mcps]

        if self.recommended_agent_flows:
            aci_mcp_agent_flow = await self.load_mcp_agent_flow_tools(
                linked_account_owner_id=aci_linked_account_owner_id,
                aci_api_key=aci_agent_first_api_key,
                realtimex_access_token=realtimex_access_token,
                litellm_base_url=default_openai_base_url,
                litellm_api_key=default_openai_api_key,
                workspace_slug=workspace_slug,
                thread_id=thread_id
            )
            if aci_mcp_agent_flow:
                all_tools = [*all_tools,aci_mcp_agent_flow]

        if self.recommended_team_members:
            
            team_members = await self.load_a2a_agents_as_tools()
            # print(team_members)
            if team_members:
                all_tools = [*all_tools,*team_members]

        

        agent_config = {
            "api_base": default_openai_base_url,
            "api_key": default_openai_api_key,
        }

        # print("agent_framework",agent_framework)

        if agent_description:
            agent_config["description"] = agent_description
        if system_prompt:
            agent_config["instructions"] = system_prompt


        if llm_setting:
            llm_config = await self.prepare_llm(**llm_setting["default"])
            # print("llm_config",llm_config)
            agent_config.update(llm_config)


        memories_str = ""
        knowledges_str = ""
        # if knowledges:
        #     memories_str, knowledges_str = await self.load_knowledges(message, user_id, workspace_slug, thread_id, knowledges)

        if agent_framework == "deepagents":
            from deepagents import create_realtimex_deep_agent
            from deepagents.backends import CompositeBackend
            from deepagents.backends.filesystem import FilesystemBackend
            agent_framework = "langchain"
            agent_config["agent_type"] = create_realtimex_deep_agent

            routes = {}
            agent_config["agent_args"] = {"assistant_id": agent_id}

            # Resolve memory paths (global and workspace)
            global_agent_path = get_deepagents_agent_path("global", agent_id)
            workspace_agent_path = get_deepagents_agent_path("workspace", agent_id, workspace_slug)

            # Enable memory if either global or workspace config exists
            agent_config["agent_args"]["enable_memory"] = bool(global_agent_path or workspace_agent_path)
            if global_agent_path:
                global_agent_root = os.path.dirname(global_agent_path)
                routes[MEMORIES_GLOBAL_VIRTUAL_ROOT] = FilesystemBackend(
                    root_dir=global_agent_root,
                    virtual_mode=True,
                )
                agent_config["agent_args"]["global_agent_path"] = f"{MEMORIES_GLOBAL_VIRTUAL_ROOT}agent.md"
            if workspace_agent_path:
                workspace_agent_root = os.path.dirname(workspace_agent_path)
                workspace_memories_root = f"{MEMORIES_WORKSPACE_VIRTUAL_ROOT_PREFIX}{workspace_slug}/"
                routes[workspace_memories_root] = FilesystemBackend(
                    root_dir=workspace_agent_root,
                    virtual_mode=True,
                )
                agent_config["agent_args"]["workspace_agent_path"] = f"{workspace_memories_root}agent.md"

            # Resolve skills paths (global and workspace)
            global_skills_dir = get_deepagents_skills_dir("global", agent_id)
            workspace_skills_dir = get_deepagents_skills_dir("workspace", agent_id, workspace_slug)

            # Enable skills if either global or workspace config exists
            agent_config["agent_args"]["enable_skills"] = bool(global_skills_dir or workspace_skills_dir)
            if global_skills_dir:
                routes[SKILLS_GLOBAL_VIRTUAL_ROOT] = FilesystemBackend(
                    root_dir=global_skills_dir,
                    virtual_mode=True,
                )
                agent_config["agent_args"]["global_skills_dir"] = SKILLS_GLOBAL_VIRTUAL_ROOT
            if workspace_skills_dir:
                workspace_skills_root = f"{SKILLS_WORKSPACE_VIRTUAL_ROOT_PREFIX}{workspace_slug}/"
                routes[workspace_skills_root] = FilesystemBackend(
                    root_dir=workspace_skills_dir,
                    virtual_mode=True,
                )
                agent_config["agent_args"]["workspace_skills_dir"] = workspace_skills_root

            # Backend is always required for deepagents
            agent_config["agent_args"]["backend"] = CompositeBackend(
                default=FilesystemBackend(),
                routes=routes,
            )

            if "subagents" in agent_data["execution_config"]:
                if "_auto" in agent_data["execution_config"]["subagents"]:
                    try:
                        subagents = await self.create_subagents(
                            instructions=system_prompt,
                            tools=[],
                            llm_config={
                                "api_base": agent_config["api_base"],
                                "api_key": agent_config["api_key"],
                                "model_id": agent_config["model_id"]
                            }
                        )
                        if subagents:
                            # Merge subagents into existing agent_args if present
                            if "agent_args" not in agent_config:
                                agent_config["agent_args"] = {}
                            agent_config["agent_args"]["subagents"] = subagents
                    except Exception as e:
                        print(e)
                        
                    # print(agent_config["agent_args"])

        await self.create_agent(
            agent_framework=agent_framework,  # See all options in https://mozilla-ai.github.io/any-agent/
            agent_config=agent_config,
            tools=all_tools,
            callbacks=[*default_callbacks],
            memories_str=memories_str,
            knowledges_str=knowledges_str
        )

        # return agent
