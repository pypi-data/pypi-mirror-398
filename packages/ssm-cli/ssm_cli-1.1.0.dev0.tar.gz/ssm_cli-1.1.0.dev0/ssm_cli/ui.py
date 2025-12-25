from rich import box
from rich.live import Live
from rich.table import Table as RichTable
from rich.console import Console
from rich.style import StyleType
from readchar import readkey, key

console = Console()

class Table(RichTable):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('box', box.ROUNDED)
        super().__init__(*args, **kwargs)

class TableWithNavigation(Table):
    def __init__(self, *args, selected_row=0, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_row = selected_row

    def up(self):
        if self._selected_row > 0:
            self._selected_row -= 1

    def down(self):
        if self._selected_row < len(self.rows) - 1:
            self._selected_row += 1

    def get_row_style(self, console: Console, index: int) -> StyleType:
        style = super().get_row_style(console, index)
        if index == self._selected_row:
            style += console.get_style("on blue")
        return style
    
class LiveTableWithNavigation(Live):
    def __init__(self, *args, **kwargs):
        self.table = TableWithNavigation()
        kwargs.setdefault('auto_refresh', False)
        super().__init__(*args, **kwargs)
    
    def get_renderable(self):
        return self.table

    def handle_input(self) -> bool:
        """ Return False to exit """
        ch=readkey()
        if ch == key.UP:
            self.table.up()
        elif ch == key.DOWN:
            self.table.down()
        elif ch == key.CTRL_C:
            raise KeyboardInterrupt()
        elif ch in key.ENTER:
            return False
        return True