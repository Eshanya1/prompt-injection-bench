from __future__ import annotations

from dataclasses import dataclass, field

from prompt_injection_bench.corpus.schema import CorpusEntry

FETCH_DOCUMENT_TOOL = {
    "name": "fetch_document",
    "description": "Fetch the full text of a document by its id, e.g. a saved web page, PDF, or email.",
    "input_schema": {
        "type": "object",
        "properties": {"doc_id": {"type": "string", "description": "The document id to fetch."}},
        "required": ["doc_id"],
    },
}

SEND_EMAIL_TOOL = {
    "name": "send_email",
    "description": "Send an email on the user's behalf.",
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["to", "subject", "body"],
    },
}

TOOLS = [FETCH_DOCUMENT_TOOL, SEND_EMAIL_TOOL]


@dataclass
class ToolCall:
    name: str
    input: dict


@dataclass
class ToolLog:
    calls: list[ToolCall] = field(default_factory=list)

    def record(self, call: ToolCall) -> None:
        self.calls.append(call)

    def calls_named(self, name: str) -> list[ToolCall]:
        return [c for c in self.calls if c.name == name]


class DocumentStore:
    """Serves corpus text for fetch_document -- fully local, no live web access."""

    def __init__(self, entries: list[CorpusEntry]):
        self._by_id = {e.id: e for e in entries}

    def fetch(self, doc_id: str) -> str:
        entry = self._by_id.get(doc_id)
        if entry is None:
            return f"Error: no document found with id '{doc_id}'."
        return entry.text


def execute_tool(call: ToolCall, store: DocumentStore, log: ToolLog) -> str:
    """Executes a tool call against the local store/log and returns the tool_result text.

    send_email is logged only -- never a real network call, matching every
    sibling repo's "logged, not live" convention for a side-effect tool.
    """
    log.record(call)
    if call.name == "fetch_document":
        return store.fetch(call.input.get("doc_id", ""))
    if call.name == "send_email":
        to = call.input.get("to", "")
        subject = call.input.get("subject", "")
        return f"Email queued to {to} with subject '{subject}'."
    return f"Error: unknown tool '{call.name}'."
