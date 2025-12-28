#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Date          : 2025-08-27
# Author        : Lancelot PINCET
# GitHub        : https://github.com/LancelotPincet
# Library       : coreLP
# Module        : print

"""
This function overrides python built in print function to add functionnalities.
"""



# %% Libraries



# %% Libraries
from corelp import prop
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from rich import print as richprint
from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
from rich.traceback import Traceback
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    ProgressColumn,
)
import traceback as tb_module
from time import perf_counter
from pathlib import Path
pyprint = print



# %% Class
@dataclass(slots=True, kw_only=True)
class Print() :
    r"""
    Enhanced replacement for the built-in :func:`print` function, adding muting,
    logging, rich formatting, and progress utilities.

    This class is callable and behaves like :func:`print`, with extra arguments.

    Parameters
    ----------
    string : object
        The object to print. Its :meth:`__str__` representation is used.
    verbose : bool, optional
        If ``True`` (default), printing is performed.  
        If ``False``, printing is skipped unless overridden.
    return_string : bool, optional
        If ``True``, return the processed string instead of ``None``.
    file : str or pathlib.Path or None, optional
        If provided, overrides the configured log file.
    mode : {"w", "a"}, optional
        File mode used when writing logs. Default is ``"a"``.
    end : str, optional
        End-of-line character(s). Defaults to ``"\n"``.
    **kwargs :
        Additional keyword arguments passed to :func:`print` or Rich's :func:`Console.print`.

    Examples
    --------
    Basic usage::

        >>> from corelp import print
        >>> s = "Hello *world*!\nThis is a print **example**"
        >>> print(s)

    Muting::

        >>> print.verbose = False
        >>> print(s)                 # muted
        >>> print(s, verbose=True)   # forced printing
        >>> print.verbose = True
        >>> print(s)                 # prints again
        >>> print(s, verbose=False)  # forced mute

    Access to underlying print functions::

        >>> print.pyprint(s)   # built-in print
        >>> print.richprint(s) # rich.print
        >>> print.print(s)     # Console.print
        >>> print.log(s)       # Console.log

    Logging::

        >>> print.file = "log.txt"
        >>> print("Hello")     # also writes to file

    Console styling::

        >>> print.theme = {"success": "green"}
        >>> print("Done!", style="success")
        >>> try:
        ...     1/0
        ... except Exception:
        ...     print.error()
        >>> print.export_html("log.html")

    Progress / Clock::

        >>> from time import sleep
        >>> for i in print.clock(15, "Outer"):
        ...     for j in print.clock(10, "Inner"):
        ...         sleep(1)

    Attributes
    ----------
    verbose : bool
        Global muting switch.
    pyprint : callable
        Built-in Python :func:`print`.
    richprint : callable
        :mod:`rich` print function.
    console : rich.console.Console
        The Rich console instance used for styled printing.
    file : pathlib.Path or None
        Path to the log file.
    progress : rich.progress.Progress
        Active Rich progress manager.
    bars : dict
        Dictionary storing active progress bars.
    theme : dict
        Custom Rich style definitions.
    """

    # Main function
    def __call__(self, string, verbose=None, *, return_string=False, file=None, mode='a', end='\n', **kwargs) :
        # Muting
        verbose = verbose if verbose is not None else self.verbose
        if not verbose :
            return None
        
        # Printing markdown
        string = str(string) + end
        self.print(Markdown(string), **kwargs)

        # Writting to file
        file = file if file is not None else self.file
        if file is not None :
            with open(Path(file), mode) as file :
                file.write(string)

        # Return
        if return_string :
            return string


    # MUTING
    verbose : bool = True # True to print



    # PRINT

    @property
    def print(self) :
        return self.console.print
    @property
    def log(self) :
        return self.console.log
    pyprint = pyprint # python print
    richprint = richprint # rich print



    # LOGGING

    _file : Path = None
    @property
    def file(self) :
        return self._file
    @file.setter
    def file(self, value) :
        self._file = Path(value)



    # CONSOLE

    _theme = {}
    @property
    def theme(self) :
        return self._theme
    @theme.setter
    def theme(self, value) :
        self._theme.update(value)
        self._console = None

    _console : Console = field(default=None, repr=False)
    @prop(cache=True)
    def console(self) :
        theme = Theme(self.theme)
        return Console(theme=theme, record=True)

    def error(self) :
        rich_tb = Traceback.from_exception(*tb_module.sys.exc_info())
        self.console.print(rich_tb)
    
    def print_locals(self) :
        self.console.log(log_locals=True)
    
    def export_html(self, path) :
        if path is None :
            return
        path = Path(path)
        html_content = self.console.export_html(inline_styles=True)
        with open(path, "w", encoding="utf-8") as file:
            file.write(html_content)
    


    # CLOCK

    def clock(self, iterable, title="Working...") :

        # Get iterable
        iterable = range(iterable) if isinstance(iterable, int) else iterable
        iterable = list(iterable)

        # Detect if progressbar already exists
        first_bar = getattr(self, "_progress", None) is None
        progress = self.progress
        bars = self.bars
        
        # Opens progress
        if first_bar :
            verbose = self.verbose
            self.verbose = False

            # Write to file
            if self.file is not None :
                with open(Path(self.file), "a") as file :
                    file.write(f'{title}...\n')
            progress.start()
        
        # Create new task
        task = bars.get(title, None)
        if task is None : # No bar with this name exists
            task = progress.add_task(title, total=len(iterable), avg_time=0.0)
            bars[title] = task # store it
        else :
            progress.reset(task)
        
        # Loop
        loop_counter = 0
        start = perf_counter()
        for item in iterable :
            yield item
            loop_counter += 1
            elapsed = perf_counter() - start
            avg_time = elapsed / loop_counter if loop_counter else 0
            progress.update(task, advance=1, avg_time=avg_time)
        
        # Clean up
        if first_bar :
            progress.stop()
            del(self.bars)
            del(self.progress)
            self.verbose = verbose

    _progress : Progress = field(default=None, repr=False)
    @prop(cache=True)
    def progress(self) :
        return Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[magenta]/{task.total}[/]"),
        TimeElapsedColumn(),
        AvgLoopTimeColumn(),
        TimeRemainingColumn(),
        EndTimeColumn(),
        transient=False
        )
    
    _bars : dict = field(default=None, repr=False)
    @prop(cache=True)
    def bars(self) :
        return {}



# Get instance
print = Print() # Instance to use everywhere

# Custom Progress bar columns
class AvgLoopTimeColumn(ProgressColumn):
    def render(self, task):
        avg_time = task.fields.get("avg_time", None)
        if avg_time is not None and task.completed > 0:
            string = f"[yellow]↻ {avg_time:.2f}s[/]" if avg_time > 1 else f"[yellow]↻ {avg_time*1000:.2f}ms[/]"
            return string
        return ""
class EndTimeColumn(ProgressColumn):
    def render(self, task):
        if task.time_remaining is not None:
            end_time = datetime.now() + timedelta(seconds=task.time_remaining)
            return f"[cyan]{end_time:%m-%d %H:%M:%S}[/] "
        return ""



# %% Test function run
if __name__ == "__main__":
    from corelp import test
    test(__file__)