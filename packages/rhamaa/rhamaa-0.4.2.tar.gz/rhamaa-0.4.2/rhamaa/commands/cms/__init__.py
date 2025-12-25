import click
from .start import start
from .startapp import startapp
from .server import run
from .database import migrate, makemigrations
from .management import check, test, collectstatic, createsuperuser, shell, update_index
from .info import status, info
from .build import build_template

@click.group()
def cms():
    """Manage RhamaaCMS development and deployment."""
    pass

# Register all subcommands
cms.add_command(start)
cms.add_command(startapp)
cms.add_command(run)
cms.add_command(migrate)
cms.add_command(makemigrations)
cms.add_command(check)
cms.add_command(test)
cms.add_command(collectstatic)
cms.add_command(createsuperuser)
cms.add_command(shell)
cms.add_command(update_index)
cms.add_command(status)
cms.add_command(info)
cms.add_command(build_template)