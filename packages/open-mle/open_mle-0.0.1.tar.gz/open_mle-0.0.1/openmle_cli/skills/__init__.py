"""Skills module for deepagents CLI.

Public API:
- SkillsMiddleware: Middleware for integrating skills into agent execution
- execute_skills_command: Execute skills subcommands (list/create/info)
- setup_skills_parser: Setup argparse configuration for skills commands

All other components are internal implementation details.
"""

from openmle_cli.skills.commands import (
    execute_skills_command,
    setup_skills_parser,
)
from openmle_cli.skills.middleware import SkillsMiddleware

__all__ = [
    "SkillsMiddleware",
    "execute_skills_command",
    "setup_skills_parser",
]
