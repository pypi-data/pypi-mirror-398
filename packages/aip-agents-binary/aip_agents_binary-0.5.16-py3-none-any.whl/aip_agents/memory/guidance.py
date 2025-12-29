"""Guidance text helpers for Mem0-based memory recall.

Authors:
    - Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import textwrap

MEM0_MEMORY_RECALL_GUIDANCE = textwrap.dedent("""
    Memory Recall Guidance:
    - Use `built_in_mem0_search` whenever you need facts from long-term memory.
    - You can also use `built_in_mem0_search` for explicit recall or recap requests of
      conversation/chat/discussion by the user.
      Reach for it when prior context such as but not limited to: names, decisions, or
      preferences, will help you respond.
      It is also appropriate when the user asks about the AI's previous responses.
    - Provide a concise `query` that describes what you are looking for (e.g., 'project plan', 'user preferences').
    - If the user specifies a time period for a memory, set `time_period` according to user query
      to retrieve memories based on that time period.
    """).strip()
