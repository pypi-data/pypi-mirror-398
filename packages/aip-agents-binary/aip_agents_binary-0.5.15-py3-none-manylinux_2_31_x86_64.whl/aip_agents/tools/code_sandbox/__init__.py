# flake8: noqa: F401
"""Code Sandbox Tools for AI Agents.

This package provides code execution capabilities for AI agents through integration
with E2B Cloud Sandbox environment.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

import warnings

try:
    import e2b

    from aip_agents.tools.code_sandbox.e2b_sandbox_tool import E2BCodeSandboxTool

    __all__ = ["E2BCodeSandboxTool"]

except ImportError:
    warnings.warn(
        "Code sandbox tools not available. Install with: pip install aip-agents[code-sandbox]",
        ImportWarning,
        stacklevel=2,
    )
    __all__ = []
