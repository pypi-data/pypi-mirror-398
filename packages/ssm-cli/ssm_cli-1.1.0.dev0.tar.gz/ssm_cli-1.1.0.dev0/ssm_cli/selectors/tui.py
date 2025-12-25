from ssm_cli.ui import console, LiveTableWithNavigation

def select(instances: list):
    with LiveTableWithNavigation(console=console, screen=True) as live:
        table = live.table
        table.add_column("Id")
        table.add_column("Name")
        table.add_column("Ping")
        table.add_column("IP")
        for instance in instances:
            table.add_row(
                instance.id,
                instance.name,
                instance.ping,
                instance.ip,
            )
        
        live.refresh()
        while live.handle_input():
            live.refresh()
        
        return instances[live.table._selected_row]
