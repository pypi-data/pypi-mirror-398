import rich_click as click
import confclasses

from ssm_cli.click import PluginGroup, version_option
from ssm_cli.logging import set_log_level
from ssm_cli.xdg import get_conf_root, get_conf_file, get_ssh_hostkey
from ssm_cli.config import CONFIG
from ssm_cli.ui import console, Table

GREY = "grey50"

import logging
logger = logging.getLogger(__name__)

@click.group(cls=PluginGroup)
@click.option_panel("Global Options", options=['--profile', '--log-level', '--version', '--help'])
@click.option('--profile', type=str, required=False, help="Which AWS profile to use")
@click.option('--log-level', type=str, required=False, help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
@version_option('--version')
def app(profile, log_level):
    # Allow setup stuff to log at the right level if passed in
    if log_level:
        set_log_level(log_level)

    try:
        with open(get_conf_file(), 'r') as file:
            confclasses.load(CONFIG, file)
            logger.debug(f"Config: {CONFIG}")
    except EnvironmentError as e:
        console.print(f"Invalid config: {e}", style="red")
    
    if log_level:
        CONFIG.log.level = log_level
    if profile:
        CONFIG.aws_profile = profile

    if not log_level:
        set_log_level(CONFIG.log.level)
    elif log_level != logging.DEBUG:
        for logger_name, level in CONFIG.log.loggers.items():
            set_log_level(level, name=logger_name)


@app.command(help='list all instances in a group, if no group provided, will list all available groups')
@click.argument('group', required=False, type=str, help="group to run against")
def list(group):
    import ssm_cli.instances
    logger.info(f"running list action (group: {group})")

    instances = ssm_cli.instances.Instances()
    table = Table()

    if group:
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("IP")
        table.add_column("Ping")
        for instance in instances.list_instances(group, True):
            table.add_row(instance.id, instance.name, instance.ip, instance.ping)
        console.print(table)
    else:
        table.add_column("Group")
        table.add_column("Total")
        table.add_column("Online")
        for group in sorted(instances.list_groups(), key=lambda x: x['name']):
            table.add_row(group['name'], str(group['total']), str(group['online']))
        console.print(table)


@app.command(help='connects to instance using AWS-StartSession')
@click.argument('group', type=str, help="group to run against")
def shell(group):
    import ssm_cli.instances

    logger.info(f"running shell action (group: {group})")

    instances = ssm_cli.instances.Instances()
    try:
        instance = instances.select_instance(group, "tui")
    except KeyboardInterrupt:
        logger.error("user cancelled")
        console.print(f":x: [bold red]user cancelled[/bold red]")
        return

    if instance is None:
        logger.error("failed to select host")
        console.print(f":x: [bold red]failed to select host[/bold red]")
        return

    logger.info(f"connecting to {repr(instance)}")
    console.print(f":computer: [bold green]connecting to {instance.name} ({instance.id})[/bold green]")

    instance.start_session()

@app.command(help="ssh proxy, used for automatic tunnels without ssh auth")
@click.argument('group', type=str, help="group to run against")
def sshproxy(group):
    import ssm_cli.instances
    import ssm_cli.ssh_proxy.server

    logger.info(f"running proxycommand action (group: {group})")

    instances = ssm_cli.instances.Instances()
    instance = instances.select_instance(group, "first")

    if instance is None:
        logger.error("failed to select host")
        raise RuntimeError("failed to select host")

    logger.info(f"connecting to {repr(instance)}")
    
    server = ssm_cli.ssh_proxy.server.SshServer(instance)
    server.start()

@app.command(help="setups up ssm-cli, can be rerun safely")
@click.option("--replace-config", is_flag=True, help="if we should replace existing config file")
@click.option("--replace-hostkey", is_flag=True, help="if we should replace existing hostkey file (be careful with this option)")
def setup(replace_config, replace_hostkey):
    # Create the root config directory
    root = get_conf_root(False)
    logger.debug(f"Checking if {root} exists")
    if root.exists():
        logger.debug(f"{root} exists")
        if not root.is_dir():
            logger.error(f"{root} already exists and is not a directory. Manual cleanup is likely needed.")
            console.print(f"{root} already exists and is not a directory. Manual cleanup is likely needed.", style="red bold")
            return
        console.print(f"{root} - skipping (already exists)", style=GREY)
    else:
        root.mkdir(511, True, True)
        console.print(f"{root} created", style="green")


    # Create the config file
    path = get_conf_file(False)
    logger.debug(f"Checking if {path} exists")
    create_config = False
    if path.exists():
        logger.debug(f"{path} exists")
        if replace_config:
            logger.info(f"{path} exists and --replace-config was set, unlink {path}")
            console.print(f"{path} removing", style="green")
            path.unlink(True)
            create_config = True
    else:
        logger.debug(f"{path} does not exist")
        create_config = True

    if create_config:
        import rich.markup

        logger.info(f"{path} creating")
        console.print(f"{path} creating", style="green")
        confclasses.from_dict(CONFIG, {})
        text = rich.markup.escape(f"What tag to use to split up the instances [{CONFIG.group_tag_key}]: ")
        tag_key = console.input(text)
        CONFIG.group_tag_key = tag_key or CONFIG.group_tag_key
        console.print(f"Using '{CONFIG.group_tag_key}' as the group tag", style=GREY)
        logger.info(f"Writing config to {path}")

        with path.open("w+") as f:
            confclasses.save(CONFIG, f)
            console.print(f"{path} created", style="green")

    # Create the ssh hostkey
    path = get_ssh_hostkey(False)
    create_key = False
    if path.exists():
        logger.debug(f"{path} exists")
        console.print(f"{path} skipping (already exists)")
        if replace_hostkey:
            logger.info(f"{path} exists and --replace-hostkey was set, unlink {path}")
            console.print(f"{path} removing", style="green")
            path.unlink(True)
            create_key = True
    else:
        logger.debug(f"{path} does not exist")
        create_key = True
    
    if create_key:
        import paramiko

        logger.info(f"{path} creating")
        host_key = paramiko.RSAKey.generate(1024)
        host_key.write_private_key_file(path)
        console.print(f"{path} created")
