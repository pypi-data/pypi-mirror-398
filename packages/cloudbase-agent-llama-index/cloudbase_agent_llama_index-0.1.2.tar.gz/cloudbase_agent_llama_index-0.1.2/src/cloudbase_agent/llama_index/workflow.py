from typing import Callable, Dict, Any, List, Optional, Awaitable, Union
from ag_ui.core import RunAgentInput, EventType, ToolCallResultEvent
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.workflow import Workflow
from llama_index.protocols.ag_ui.agent import AGUIChatWorkflow
from llama_index.protocols.ag_ui.events import (
    TextMessageStartWorkflowEvent,
    TextMessageContentWorkflowEvent,
    TextMessageChunkWorkflowEvent,
    TextMessageEndWorkflowEvent,
    ToolCallStartWorkflowEvent,
    ToolCallArgsWorkflowEvent,
    ToolCallChunkWorkflowEvent,
    ToolCallEndWorkflowEvent,
    StateSnapshotWorkflowEvent,
    StateDeltaWorkflowEvent,
    MessagesSnapshotWorkflowEvent,
    TextMessageChunkEvent,
    CustomWorkflowEvent
)

from cloudbase_agent.server.send_message.models import (
    InterruptEvent,
    ErrorEvent
)


AG_UI_EVENTS = (
    TextMessageStartWorkflowEvent,
    TextMessageContentWorkflowEvent,
    TextMessageEndWorkflowEvent,
    ToolCallStartWorkflowEvent,
    ToolCallArgsWorkflowEvent,
    ToolCallEndWorkflowEvent,
    StateSnapshotWorkflowEvent,
    StateDeltaWorkflowEvent,
    MessagesSnapshotWorkflowEvent,
    TextMessageChunkWorkflowEvent,
    ToolCallChunkWorkflowEvent,
    CustomWorkflowEvent,
    ToolCallResultEvent,
)


def workflow_event_to_send_ag_ui_event(workflow_event) -> Union[
    TextMessageChunkWorkflowEvent,TextMessageChunkEvent, TextMessageContentWorkflowEvent, ToolCallStartWorkflowEvent, ToolCallArgsWorkflowEvent, ToolCallEndWorkflowEvent, ToolCallResultEvent, InterruptEvent, ErrorEvent, List[Union[ToolCallStartWorkflowEvent, ToolCallArgsWorkflowEvent, ToolCallEndWorkflowEvent]]
]:
    # if isinstance(workflow_event, MessagesSnapshotWorkflowEvent):
    #      print("MessagesSnapshotWorkflowEvent",workflow_event)
    #      for m in workflow_event.messages:
    #          print("m",m, "role:", m.role)
    #          if m.role == "tool":
    #              # Get tool_call_id from additional_kwargs
    #              tool_call_id = None
    #              if hasattr(m, 'tool_call_id'):
    #                  tool_call_id = m.tool_call_id
    #
    #              # Get content from the message
    #              content = ""
    #              if hasattr(m, 'content'):
    #                  content = m.content
    #              print("tool_call_id",tool_call_id,"content",content)
    #              # Create ToolCallResultEvent if we have the required fields
    #              if tool_call_id and content:
    #                  result = ToolCallResultEvent(
    #                      type=EventType.TOOL_CALL_RESULT,
    #                      tool_call_id=tool_call_id,
    #                      content=content,
    #                      message_id=m.id
    #                  )
    #                  print("result")
    #                  return result
    """Convert workflow event to SendMessageEvent type."""
    if isinstance(workflow_event, TextMessageChunkWorkflowEvent):
        return TextMessageChunkEvent(
            type=EventType.TEXT_MESSAGE_CHUNK,
            timestamp=workflow_event.timestamp,
            delta=workflow_event.delta,
            raw_event={"data": {"chunk": {"content": workflow_event.delta}}}
        )
    elif isinstance(workflow_event, ToolCallChunkWorkflowEvent):
        # Split ToolCallChunkWorkflowEvent into three separate events
        events = []
        print("ToolCallChunkWorkflowEvent",workflow_event)
        # 1. ToolCallStartEvent
        start_event = ToolCallStartWorkflowEvent(
            type=EventType.TOOL_CALL_START,
            timestamp=workflow_event.timestamp,
            tool_call_id=workflow_event.tool_call_id,
            tool_call_name=workflow_event.tool_call_name,
            parent_message_id=workflow_event.parent_message_id,
            raw_event={"data": {"chunk": {"additional_kwargs": {"tool_calls": [{"function": {"arguments": None}}]}}}}
        )
        events.append(start_event)
        
        # 2. ToolCallArgsEvent (if there's delta content)
        if workflow_event.delta and workflow_event.delta != "{}":
            args_event = ToolCallArgsWorkflowEvent(
                type=EventType.TOOL_CALL_ARGS,
                timestamp=workflow_event.timestamp,
                tool_call_id=workflow_event.tool_call_id,
                delta=workflow_event.delta
            )
            events.append(args_event)
        
        # 3. ToolCallEndEvent
        end_event = ToolCallEndWorkflowEvent(
            type=EventType.TOOL_CALL_END,
            timestamp=workflow_event.timestamp,
            tool_call_id=workflow_event.tool_call_id
        )
        events.append(end_event)
        return events

    return workflow_event

class AGKitAgent:
    def __init__(self, workflow_factory: Callable[[], Awaitable[Workflow]]):
        self.workflow_factory = workflow_factory

    async def run(self, raw_input: RunAgentInput):
        """Run the workflow and yield events as an async generator."""
        workflow = await self.workflow_factory()

        handler = workflow.run(
            input_data=raw_input,
        )

        try:
            async for ev in handler.stream_events():
                print(f"Raw event from handler.stream_events: {ev}")
                if ev is None:
                    print("WARNING: Received None event from handler.stream_events")
                    continue
                if isinstance(ev, AG_UI_EVENTS):
                    # Convert workflow event to raw agui event
                    send_message_event = workflow_event_to_send_ag_ui_event(ev)
                    print("send_message_event", send_message_event)
                    if send_message_event is not None:
                        # Handle both single events and lists of events
                        if isinstance(send_message_event, list):
                            for event in send_message_event:
                                print(f"Yielding event from list: {event}")
                                yield event
                        else:
                            print(f"Yielding single event: {send_message_event}")
                            yield send_message_event
                    else:
                        print(f"Skipping event {ev} - no conversion available")
                else:
                    print(f"Event {ev} is not in AG_UI_EVENTS, skipping")

            # Finish the run
            _ = await handler

        except Exception as e:
            yield ErrorEvent(error=str(e))
            await handler.cancel_run()
            raise


def get_default_workflow_factory(
    llm: Optional[FunctionCallingLLM] = None,
    frontend_tools: Optional[List[str]] = None,
    backend_tools: Optional[List[str]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
    timeout: Optional[float] = 120,
) -> Callable[[], Workflow]:
    async def workflow_factory():
        return AGUIChatWorkflow(
            llm=llm,
            frontend_tools=frontend_tools,
            backend_tools=backend_tools,
            initial_state=initial_state,
            system_prompt=system_prompt,
            timeout=timeout,
        )

    return workflow_factory


def new_agent(
    workflow_factory: Optional[Callable[[], Awaitable[Workflow]]] = None,
            llm: Optional[FunctionCallingLLM] = None,
    frontend_tools: Optional[List[str]] = None,
    backend_tools: Optional[List[str]] = None,
    initial_state: Optional[Dict[str, Any]] = None,
            system_prompt: Optional[str] = None,
    timeout: Optional[float] = 120,
) -> Any:
    workflow_factory = workflow_factory or get_default_workflow_factory(
        llm, frontend_tools, backend_tools, initial_state, system_prompt, timeout
    )
    return AGKitAgent(workflow_factory)