from opentelemetry import trace
from typing import Any
from contextlib import contextmanager

from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from ..utils.logger import logger

tracer = trace.get_tracer(__name__)
propagator = TraceContextTextMapPropagator()


@contextmanager
def trace_node_execution(node_id: str, node_type: str, **attributes):
    span_attributes = {
        "node.id": node_id,
        "node.type": node_type,
    }
    span_attributes.update(attributes)
    
    with tracer.start_as_current_span(
        f"node.{node_id}",
        attributes=span_attributes
    ) as span:
        logger.info(f"Started tracing node: {node_id} ({node_type})")
        yield span
        logger.info(f"Finished tracing node: {node_id}")


@contextmanager
def trace_agent_invocation(agent_name: str, model: str, **attributes):
    span_attributes = {
        "agent.name": agent_name,
        "agent.model": model,
    }
    span_attributes.update(attributes)
    
    with tracer.start_as_current_span(
        "agent.invoke",
        attributes=span_attributes
    ) as span:
        yield span


@contextmanager
def trace_workflow_execution(workflow_name: str, **attributes):
    span_attributes = {
        "workflow.name": workflow_name,
    }
    span_attributes.update(attributes)
    
    with tracer.start_as_current_span(
        "workflow.execute",
        attributes=span_attributes
    ) as span:
        yield span


def add_node_result(span, field: str, value: Any, status: str):
    if span and span.is_recording():
        span.set_attribute(f"field.{field}", str(value) if value is not None else "None")
        span.set_attribute("node.status", status)


def add_agent_result(span, response_length: int, tool_calls: int = 0):
    if span and span.is_recording():
        span.set_attribute("agent.response.length", response_length)
        if tool_calls > 0:
            span.set_attribute("agent.tool_calls.count", tool_calls)
