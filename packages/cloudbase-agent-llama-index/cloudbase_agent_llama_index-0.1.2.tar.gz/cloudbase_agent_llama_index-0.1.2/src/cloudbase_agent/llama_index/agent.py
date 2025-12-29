from typing import Union, List
import json

from ag_ui.core import TextMessageChunkEvent, ToolCallResultEvent, ToolCallEndEvent, ToolCallStartEvent, \
    ToolCallArgsEvent, EventType, RunAgentInput
from llama_index.core.agent import FunctionAgent
from llama_index.core.agent import AgentOutput, ToolCallResult

from cloudbase_agent.server.send_message.models import ErrorEvent, InterruptEvent


def agent_event_to_send_ag_ui_event(workflow_event) -> Union[
    TextMessageChunkEvent, ToolCallResultEvent, InterruptEvent, ErrorEvent,
    List[Union[ToolCallStartEvent,ToolCallArgsEvent, ToolCallResultEvent, ToolCallEndEvent]]
]:
    """Convert workflow event to SendMessageEvent type."""
    if isinstance(workflow_event, AgentOutput):
        return TextMessageChunkEvent(
            type=EventType.TEXT_MESSAGE_CHUNK,
            delta=workflow_event.response.content,
            raw_event={"data": {"chunk": {"content": workflow_event.response.content}}}
        )
    elif isinstance(workflow_event, ToolCallResult):
        # Split ToolCallChunkWorkflowEvent into three separate events
        events = []
        print("ToolCallResult", workflow_event)
        # 1. ToolCallStartEvent
        start_event = ToolCallStartEvent(
            type=EventType.TOOL_CALL_START,
            tool_call_id=workflow_event.tool_id,
            tool_call_name=workflow_event.tool_name,
            raw_event={"data": {"chunk": {"additional_kwargs": {"tool_calls": [{"function": {"arguments": None}}]}}}}
        )
        events.append(start_event)

        # 2. ToolCallArgsEvent
        args_event = ToolCallArgsEvent(
            type=EventType.TOOL_CALL_ARGS,
            tool_call_id=workflow_event.tool_id,
            delta=json.dumps(workflow_event.tool_kwargs, ensure_ascii=False)
        )
        events.append(args_event)

        # 3. ToolCallEndEvent
        end_event = ToolCallEndEvent(
            type=EventType.TOOL_CALL_END,
            tool_call_id=workflow_event.tool_id
        )
        events.append(end_event)

        result_event = ToolCallResultEvent(
            type=EventType.TOOL_CALL_RESULT,
            tool_call_id=workflow_event.tool_id,
            content=str(workflow_event.tool_output),
            message_id=workflow_event.tool_id)
        events.append(result_event)

        return events

    return None


class AgKitFunctionAgent:
    def __init__(self, agent: FunctionAgent):
        self.agent = agent
    async def run(self, input: RunAgentInput):
        # Process the input and generate a response
        handler = self.agent.run(str(input.messages))

        try:
            async for event in handler.stream_events():
                send_message_event = agent_event_to_send_ag_ui_event(event)
                if send_message_event is not None:
                    # Handle both single events and lists of events
                    if isinstance(send_message_event, list):
                        for event in send_message_event:
                            yield event
                    else:
                        yield send_message_event

            _ = await handler

        except Exception as e:
            print(f"Error occurred: {e}")
            yield ErrorEvent(error=str(e))
            await handler.cancel_run()
            raise
