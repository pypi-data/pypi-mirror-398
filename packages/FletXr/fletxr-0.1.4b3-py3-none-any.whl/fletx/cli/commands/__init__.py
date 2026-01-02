from fletx.cli.commands.base import (
    CommandRegistry, CommandParser,
    BaseCommand, TemplateCommand
)
from fletx.cli.commands.newproject import (
    NewProjectCommand
)
from fletx.cli.commands.runproject import (
    RunCommand
)
from fletx.cli.commands.generate import (
    ComponentCommand
)

from fletx.cli.commands.testproject import (
    TestCommand
)
from fletx.cli.commands.check import (
    CheckCommand
)

__all__ = [
    'CommandRegistry',
    'CommandParser',
    'BaseCommand',
    'TemplateCommand',
    'NewProjectCommand',
    'RunCommand',
    'TestCommand',
    'CheckCommand'
]