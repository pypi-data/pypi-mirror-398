"""
Keeping click (or rich_click) lower level logic in one place.
"""

from rich_click import RichCommand, RichContext, RichGroup, RichHelpFormatter, Context, Parameter, option

def version_callback(ctx: Context, param: Parameter, value: bool) -> None:
    """
    Custom version printing logic to go and get install path and the smp version
    """
    if not value or ctx.resilient_parsing:
        return
    
    import sys
    import subprocess
    import importlib.metadata
    import os

    try:
        results = subprocess.run(["session-manager-plugin", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        print("session-manager-plugin not found", file=sys.stderr)
    
    pkg_dir = os.path.join(os.path.dirname(__file__), "..")
    pkg_dir = os.path.abspath(pkg_dir)
    print(f"ssm-cli {importlib.metadata.version('ssm-cli')} from {pkg_dir}")
    v = sys.version_info
    print(f"python {v.major}.{v.minor}.{v.micro}")
    print(f"session-manager-plugin {results.stdout.strip()}")
    ctx.exit()

def version_option(*param_decls):
    """
    Use like the click.version_option.
    """
    return option(*param_decls, is_flag=True, expose_value=False, is_eager=True, help="Show the version and exit", callback=version_callback)

class PluginCommand(RichCommand):
    def format_help(self, ctx: RichContext, formatter: RichHelpFormatter) -> None:
        # Subcommand help doesn't contain the options of global, so pull them in now
        if ctx.parent is not None:
            ctx.command.panels += ctx.parent.command.panels
            ctx.command.params += ctx.parent.command.params
        
        super().format_help(ctx, formatter)

class PluginGroup(RichGroup):
    def __init__(self, **kwargs) -> None:
        self.command_class = PluginCommand
        
        super().__init__(context_settings={
            "allow_interspersed_args": True,
            # When developing the allow_interspersed_args, I kept finding these other settings in examples.
            # I haven't found them necessary, so leaving commented if they become useful:
            # "allow_extra_args": True,
            # "ignore_unknown_options": True
        }, **kwargs)
    
    def parse_args(self, ctx, args):
        # Intercept parsing args in the case of help because of the allow_interspersed_args setting.
        # All we need to do is find out if a command is in the args as well and then pass the context down to that command.
        # This is not perfect as it doesnt handle this example well: 
        #   `--help --profile shell`
        # Work arounds could be done but cannot see this happening in the wild. This is a complex fix for little gain.
        # Time spent so far: 2 hours
        args_set = set(args)
        help_args = args_set & set(self.get_help_option_names(ctx))
        if help_args:
            cmd_args = args_set & set(self.list_commands(ctx))
            if cmd_args:
                cmd = self.get_command(ctx, cmd_args.pop())
                if cmd:
                    parent_ctx = ctx
                    args.remove(cmd.name)
                    ctx = cmd.make_context(cmd.name, args, parent=parent_ctx)

        return super().parse_args(ctx, args)