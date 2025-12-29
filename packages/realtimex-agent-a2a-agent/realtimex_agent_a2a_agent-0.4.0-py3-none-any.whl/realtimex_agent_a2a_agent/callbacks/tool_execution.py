from uuid import uuid4
import json
import time
import os
import redis
import sys

from any_agent.callbacks import Callback, Context
from any_agent.tracing.attributes import GenAI

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=1)
r = redis.Redis(connection_pool=pool)

class ShowToolCalling(Callback):
    def before_tool_execution(self, context: Context, *args, **kwargs) -> Context:
        span = context.current_span

        operation_name = span.attributes.get(GenAI.OPERATION_NAME, "")

        if operation_name != "execute_tool":
            return context

        tool_name = span.attributes.get(GenAI.TOOL_NAME, "")
        tool_input = span.attributes.get(GenAI.TOOL_ARGS, "{}")
        tool_call_id = span.attributes.get("gen_ai.tool.call.id","")

        toolName = tool_name
        toolIcon = "pencil-ruler"
        mainTask = "Tool is executing..."

        if tool_name.startswith("call_"):
            toolIcon = "bot"
            toolName = f"Call sub-agent {tool_name.replace('call_','')}"
            mainTask = "Sub-agent is working..."

        if tool_name == "final_answer":
            return context

        block_id = str(uuid4())
        context.shared[f"show_tool_calling_block_id_{tool_call_id}"] = block_id
        context.shared[f"show_tool_calling_start_time_{tool_call_id}"] = round(time.time() * 1000)
        
        current_session_id = None
        if "_current_session_id" in context.shared:
            current_session_id = context.shared['_current_session_id']

        print("current_session_id", current_session_id)

        message_content = {
            "uuid": str(uuid4()),
            "type": "responseData",
            "dataType": "toolUse",
            "data": {
                "toolName": toolName,
                "toolIcon": toolIcon,
                "mainTask" : mainTask,
                "input": [tool_input],
                "content": "",
                "meta": {"blockId":block_id, "status": "processing", "durationMs": 0 }
            }
        }

        if message_content:
            # print(f"<message>{json.dumps(message_content)}</message>")
            pub = r.publish(
                current_session_id,
                f'.message {json.dumps(message_content)}'
            )

        return context



    def after_tool_execution(self, context: Context, *args, **kwargs) -> Context:
        span = context.current_span

        operation_name = span.attributes.get(GenAI.OPERATION_NAME, "")

        if operation_name != "execute_tool":
            return context

        tool_name = span.attributes.get(GenAI.TOOL_NAME, "")
        tool_input = span.attributes.get(GenAI.TOOL_ARGS, "{}")
        tool_call_id = span.attributes.get("gen_ai.tool.call.id","")

        toolName = tool_name
        toolIcon = "pencil-ruler"
        mainTask = "Tool executed completely."

        if tool_name.startswith("call_"):
            toolIcon = "bot"
            toolName = f"Call sub-agent {tool_name.replace('call_','')}"
            mainTask = "Sub-agent has completed the task."

        # if tool_name == "final_answer":
        #     return context

        if f"show_tool_calling_block_id_{tool_call_id}" in context.shared:
            block_id = context.shared[f"show_tool_calling_block_id_{tool_call_id}"]
        else:
            block_id = str(uuid4())
        
        execution_time = 0
        if f"show_tool_calling_start_time_{tool_call_id}" in context.shared:
            execution_time = round(time.time() * 1000) - context.shared[f"show_tool_calling_start_time_{tool_call_id}"]
        else:
            execution_time = 1000

        current_session_id = None
        if "_current_session_id" in context.shared:
            current_session_id = context.shared['_current_session_id']

        # print("current_session_id", current_session_id)

        # context.shared[f"show_tool_calling_start_time_{tool_call_id}"] = round(time.time() * 1000)
        ui_components = []
        flow_as_output = False
        flow_output_data = None

        message_content = None
        if output := span.attributes.get(GenAI.OUTPUT, None):
            output_type = span.attributes.get(GenAI.OUTPUT_TYPE, "text")

            if toolName == "final_answer":
                # message_content = {
                #     "uuid": str(uuid4()),
                #     "type": "responseData",
                #     "content": output,
                #     "dataType": "markdown",
                #     "data": {"content": output, "language": None},
                # }
                # pub = r.publish(
                #     current_session_id,
                #     f'.message {json.dumps(message_content)}'
                # )
                return context


            if output_type == "json":
                output_data = json.loads(output)

                if "ui-components" in output_data:
                    if output_data["ui-components"]:
                        for ui_component in output_data["ui-components"]:
                            ui_component["uuid"] = str(uuid4())
                            ui_component["type"] = "responseData"
                            ui_components.append(ui_component)

                    del output_data['ui-components']
                
                if "flow_as_output" in output_data:
                    if output_data["flow_as_output"]:
                        flow_as_output = True
                        if "output" in output_data:
                            flow_output_data = str(output_data["output"])

                message_content = {
                    "uuid": str(uuid4()),
                    "type": "responseData",
                    "dataType": "toolUse",
                    "data": {
                        "toolName": toolName,
                        "toolIcon": toolIcon,
                        "mainTask" : mainTask,
                        "input": [tool_input],
                        "content": {
                            "dataType": "json",
                            "data": {
                                "content": output_data, 
                                "language": None
                            }
                        },
                        "meta": {"blockId":block_id, "status": "completed", "durationMs": execution_time }
                    }
                }
                    

            else:
                message_content = {
                    "uuid": str(uuid4()),
                    "type": "responseData",
                    "dataType": "toolUse",
                    "data": {
                        "toolName": toolName,
                        "toolIcon": toolIcon,
                        "mainTask" : mainTask,
                        "input": [tool_input],
                        "content": {
                            "dataType": "markdown",
                            "data": {
                                "content": output, 
                                "language": None
                            }
                        },
                        "meta": {"blockId":block_id, "status": "completed", "durationMs": execution_time }
                    }
                }
        else:
            message_content = {
                "uuid": str(uuid4()),
                "type": "responseData",
                "dataType": "toolUse",
                "data": {
                    "toolName": toolName,
                    "toolIcon": toolIcon,
                    "mainTask" : mainTask,
                    "input": [tool_input],
                    "content": {
                        "dataType": "markdown",
                        "data": {
                            "content": "No outputs.", 
                            "language": None
                        }
                    },
                    "meta": {"blockId":block_id, "status": "completed", "durationMs": execution_time }
                }
            }

        if message_content:
            # print(f"<message>{json.dumps(message_content)}</message>")
            pub = r.publish(
                current_session_id,
                f'.message {json.dumps(message_content)}'
            )
        if len(ui_components) > 0:
            for ui_component in ui_components:
                pub = r.publish(
                    current_session_id,
                    f'.message {json.dumps(ui_component)}'
                )

        if flow_as_output:
            pass
            # message_content = {
            #     "uuid": str(uuid4()),
            #     "type": "responseData",
            #     "dataType": "markdown",
            #     "data": {
            #         "content": flow_output_data, 
            #         "language": None
            #     }
            # }
            # pub = r.publish(
            #     current_session_id,
            #     f'.message {json.dumps(message_content)}'
            # )
            # raise RuntimeError("Reached Return Direct Tool.")

        return context
