"""
klogg cli tool - used to create work log entries
- log files are split per month
- Each log line is in format:
    YYYY-MM-DD HH:MM:SS>  <optional_marker> multi-word description of the log
- Possible markers are <start> and <break>
- Timestamp on each line marks the end time of the task and duration is calculated as difference between it and the timestamp on previous line
"""

import os
import re
import sys
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Callable

import click
from click_aliases import ClickAliasedGroup
# Use the package-provided single-source version (falls back to pyproject when not installed)
from . import __version__

# Log directory and default path (keep for backwards compatibility)
LOG_DIR = os.path.expanduser("~/.config/klogg")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def ensure_log_path(path: Optional[str] = None) -> None:
    """
    Ensure the directory for the given log path exists. If path is None,
    use the default log directory.
    """
    target_dir = LOG_DIR if path is None else os.path.dirname(path)
    os.makedirs(target_dir, exist_ok=True)


def _month_log_path_for(dt: Optional[datetime] = None) -> str:
    """
    Return the log file path for the given datetime (or now if None),
    e.g. ~/.config/klogg/2025-12.log
    """
    if dt is None:
        dt = datetime.now()
    filename = f"{dt.year:04d}-{dt.month:02d}.log"
    return os.path.join(LOG_DIR, filename)


def list_log_files() -> List[str]:
    """
    Return a list of existing log file paths sorted ascending by name.
    Recognizes files named YYYY-MM.log and default.log.
    """
    try:
        names = os.listdir(LOG_DIR)
    except FileNotFoundError:
        return []
    matched: List[str] = []
    for nm in names:
        if re.fullmatch(r"\d{4}-\d{2}\.log", nm) or nm == "default.log":
            matched.append(os.path.join(LOG_DIR, nm))
    matched.sort()
    return matched


def get_latest_log_file() -> Optional[str]:
    """
    Return the path to the latest log file (highest YYYY-MM or default.log),
    or None if no log files exist.
    """
    files = list_log_files()
    if not files:
        return None
    return files[-1]


def append_log(message: str) -> str:
    """
    Append a timestamped line to the current month's log and return the
    written line (without the trailing newline).
    """
    path = _month_log_path_for(None)
    ensure_log_path(path)
    timestamp = datetime.now().strftime(TIME_FORMAT)
    line = f"{timestamp}>  {message}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    return line.rstrip("\n")


def parse_date_arg(arg: str) -> date:
    """
    Parse arg as one of:
      - YYYY-MM-DD
      - MM-DD   (assume current year)
      - DD      (assume current month & year)
    Returns a datetime.date
    """
    today = date.today()

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", arg):
        # YYYY-MM-DD
        return date.fromisoformat(arg)

    if re.fullmatch(r"\d{1,2}-\d{1,2}", arg):
        # MM-DD
        month_s, day_s = arg.split("-", 1)
        month = int(month_s)
        day = int(day_s)
        return date(today.year, month, day)

    if re.fullmatch(r"\d{1,2}", arg):
        # DD
        day = int(arg)
        return date(today.year, today.month, day)

    raise ValueError(f"Unrecognized date format: {arg}")





@click.version_option(__version__, prog_name="klogg")
@click.group(cls=ClickAliasedGroup, invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """
    klogg - simple work logger

    When run with no subcommand, behave like "day" and show today's entries.
    Use "add" (or alias "a") to append a log entry:
      klogg add Fixed the widget
      klogg a quick note
    """
    # Default action when no subcommand is provided: call the "day" command (shows today's entries)
    if ctx.invoked_subcommand is None:
        # invoke the day command so that behavior is consistent with using "klogg day"
        ctx.invoke(day_cmd)
        return


@main.command("add", aliases=["a"])
@click.argument("message", nargs=-1)
@click.pass_context
def add_cmd(ctx: click.Context, message: List[str]) -> None:
    """
    Add a new log entry. Alias: 'a'
    """
    if not message:
        click.echo("Usage: klogg add <message>", err=True)
        ctx.exit(1)
    msg = " ".join(message).strip()
    line = append_log(msg)
    click.echo(f"{line}")


@main.command("break", aliases=["b", "p"])
@click.argument("message", nargs=-1)
def break_cmd(message: List[str]) -> None:
    """
    Record a short break marker. Alias: 'b'

    This appends the literal "<break>" (with angle brackets) as a log entry.
    If additional arguments are provided they are appended after the marker,
    e.g. "<break> grabbed coffee".
    """
    if message:
        msg = "<break> " + " ".join(message).strip()
    else:
        msg = "<break>"
    line = append_log(msg)
    click.echo(f"{line}")


@main.command("start", aliases=["s"])
def start_cmd() -> None:
    """
    Record a start marker. Alias: 's'

    This appends the exact string "<start>" (with angle brackets) as a log entry.
    """
    line = append_log("<start>")
    click.echo(f"{line}")


@main.command("ls")
@click.argument("when", required=False)
def ls_cmd(when: Optional[str]) -> None:
    """
    Print raw log lines for a month.

    WHEN (optional) accepts:
      - YYYY-MM   (exact month)
      - MM        (assumes current year)

    If omitted, assumes the current month.

    This command prints the raw log lines (including marker lines) from the
    monthly log file. If the requested month has no log file, the command
    exits silently.
    """
    today = date.today()

    if when:
        # YYYY-MM
        if re.fullmatch(r"\d{4}-\d{2}", when):
            try:
                year_s, month_s = when.split("-", 1)
                year = int(year_s)
                month = int(month_s)
                # validate month range
                if not (1 <= month <= 12):
                    raise ValueError("month out of range")
            except Exception as e:
                click.echo(f"Error parsing month: {e}", err=True)
                sys.exit(2)
        # MM (assume current year)
        elif re.fullmatch(r"\d{1,2}", when):
            try:
                year = today.year
                month = int(when)
                if not (1 <= month <= 12):
                    raise ValueError("month out of range")
            except Exception as e:
                click.echo(f"Error parsing month: {e}", err=True)
                sys.exit(2)
        else:
            click.echo("Invalid month format. Use YYYY-MM or MM", err=True)
            sys.exit(2)
    else:
        year = today.year
        month = today.month

    # Read the monthly log file for the requested month and print raw lines
    month_dt = datetime(year, month, 1)
    path = _month_log_path_for(month_dt)
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            click.echo(ln.rstrip("\n"))


@main.command("rm")
def rm_cmd() -> None:
    """
    Remove the last log entry from the most recent log file.

    The command prints the last entry and prompts the user (Y/n) before deleting.
    """
    files = list_log_files()
    if not files:
        click.echo("No log entries found.", err=True)
        return

    # Look for the last non-empty line by scanning files from newest to oldest
    last_fp: Optional[str] = None
    last_idx: Optional[int] = None
    last_entry: Optional[str] = None

    for fp in reversed(files):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                lines = [ln.rstrip("\n") for ln in f]
        except FileNotFoundError:
            continue

        # Find last non-empty line in this file
        idx = len(lines) - 1
        while idx >= 0 and lines[idx] == "":
            idx -= 1
        if idx >= 0:
            last_fp = fp
            last_idx = idx
            last_entry = lines[idx]
            break

    if last_entry is None:
        click.echo("No log entries found.", err=True)
        return

    click.echo(last_entry)
    if not click.confirm("Delete this entry?", default=True):
        click.echo("Aborted.")
        return

    # Remove the entry from its file and write back (we already read 'lines' above)
    assert last_fp is not None and last_idx is not None
    # 'lines' was populated when scanning files for the last entry.
    del lines[last_idx]
    # Overwrite the file directly (no indirection).
    ensure_log_path(last_fp)
    with open(last_fp, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(f"{ln}\n")
    click.echo("Deleted.")


# Helper: parse individual log lines into timestamp + message
def _parse_log_line(ln: str) -> Optional[Tuple[datetime, str]]:
    """
    Parse a log line of the form:
      2025-12-15 11:15:00>  Message
    Returns (datetime, message) or None if the line doesn't match.
    """
    m = re.match(r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})>\s*(?P<msg>.*)$", ln)
    if not m:
        return None
    try:
        ts = datetime.strptime(m.group("ts"), TIME_FORMAT)
    except Exception:
        return None
    return ts, m.group("msg")


def _read_and_parse_log_file(path: str) -> List[Tuple[datetime, str]]:
    """
    Read a single monthly log file (path) and return a list of parsed entries
    as (datetime, message). If the file does not exist or is unreadable, an
    empty list is returned.

    This is the common parsing helper that replaces reading all log files for
    the day/week/month commands — only the relevant monthly file needs to be
    read and parsed.
    """
    if not os.path.exists(path):
        return []
    parsed: List[Tuple[datetime, str]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for ln in f:
                ln = ln.rstrip("\n")
                p = _parse_log_line(ln)
                if p:
                    parsed.append(p)
    except FileNotFoundError:
        # race condition or removed file; return empty
        return []
    return parsed


def _format_timedelta_hm(td: Optional[timedelta]) -> str:
    """
    Format timedelta as HH:MM (hours without trimming, zero-padded to 2 digits).
    If td is None, return "-".
    """
    if td is None:
        return "-"
    total_seconds = int(td.total_seconds())
    hours, rem = divmod(total_seconds, 3600)
    minutes, _seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}"


# Common helper to print entries that match a given predicate and output total.
def _print_entries_and_total(
    parsed: List[Tuple[datetime, str]],
    matches: "Callable[[datetime, str], bool]",
    grep: Optional[str] = None,
) -> bool:
    """
    Given a list of parsed entries (datetime, message) sorted by timestamp,
    print entries that satisfy the `matches(ts, msg)` predicate (and optional
    case-insensitive `grep` substring) and append a total line summarizing
    accumulated time (excluding <break> entries).

    Returns True if any matching entries were printed, False otherwise.
    """
    # Build lists of previous timestamps and durations for each entry
    prev_ts_list: List[Optional[datetime]] = []
    durations: List[Optional[timedelta]] = []
    prev_ts: Optional[datetime] = None
    for ts, _ in parsed:
        prev_ts_list.append(prev_ts)
        if prev_ts is None:
            durations.append(None)
        else:
            durations.append(ts - prev_ts)
        prev_ts = ts

    found = False
    total_td = timedelta(0)
    total_counted = False

    # Pre-lower grep once for efficiency
    grep_l = grep.lower() if grep is not None else None

    for (ts, msg), prev_ts, dur in zip(parsed, prev_ts_list, durations):
        # Time predicate first
        if not matches(ts, msg):
            continue
        # Grep substring filtering (case-insensitive)
        if grep_l is not None and grep_l not in msg.lower():
            continue
        # Do not display the "<start>" marker line; it only marks the start time for the next entry
        if msg == "<start>":
            continue
        found = True
        # start timestamp: previous entry's timestamp if present, otherwise use this entry's timestamp
        start_ts = prev_ts if prev_ts is not None else ts
        start_str = start_ts.strftime(TIME_FORMAT)
        dur_str = _format_timedelta_hm(dur)
        click.echo(f"{start_str} [{dur_str}]>  {msg}")

        # Accumulate total time excluding "<break>" entries (including those with extra text)
        if dur is not None and not msg.startswith("<break>"):
            total_td += dur
            total_counted = True

    if not found:
        return False

    # Print total time excluding breaks
    total_str = _format_timedelta_hm(total_td if total_counted else None)
    click.echo(f"------------ Total: [{total_str}]")
    return True


@main.command("day", aliases=["d"])
@click.option("--grep", "-g", "grep", required=False, default=None, help="Filter entries by substring (case-insensitive).")
@click.argument("when", required=False)
def day_cmd(when: Optional[str], grep: Optional[str]) -> None:
    """
    Show all work logs for a given day.

    WHEN (optional) accepts the same formats as other commands:
      - YYYY-MM-DD
      - MM-DD   (assumes current year)
      - DD      (assumes current month & year)
      - N       (negative integer, e.g. -1 for yesterday)

    If omitted, assumes today.

    Output format for each displayed entry:
      YYYY-MM-DD HH:MM:SS [HH:MM]>  MARKER_AND_DESCRIPTION

    The "start timestamp" is the timestamp of the previous log entry (or the
    entry's own timestamp if no previous entry exists). Duration is the
    difference between the entry's timestamp and the previous entry's
    timestamp (or '-' if unknown).

    Additionally, this command prints the total time spent on tasks for the
    day, excluding any "<break>" entries (including those that have extra
    text like "<break> grabbed coffee").
    """
    if when:
        # Support negative offsets like "-1" meaning relative days from today
        if re.fullmatch(r"-\d+", when):
            try:
                offset_days = int(when)
                target = date.today() + timedelta(days=offset_days)
            except Exception as e:
                click.echo(f"Error parsing day offset: {e}", err=True)
                sys.exit(2)
        else:
            try:
                target = parse_date_arg(when)
            except Exception as e:
                click.echo(f"Error parsing date: {e}", err=True)
                sys.exit(2)
    else:
        target = date.today()

    # Read and parse only the monthly log file that contains the target date.
    month_path = _month_log_path_for(datetime(target.year, target.month, 1))
    parsed: List[Tuple[datetime, str]] = _read_and_parse_log_file(month_path)

    if not parsed:
        return

    # Use common printer with a predicate for the target day
    _print_entries_and_total(parsed, lambda ts, _msg: ts.date() == target, grep)


@main.command("week", aliases=["w"])
@click.option("--grep", "-g", "grep", required=False, default=None, help="Filter entries by substring (case-insensitive).")
@click.argument("when", required=False)
def week_cmd(when: Optional[str], grep: Optional[str]) -> None:
    """
    Show all work logs for a given ISO week.

    WHEN (optional) accepts:
      - WW        (week number, assumes current year)
      - YYYY-WW   (year-week, e.g. 2025-52)
      - -N        (negative integer, e.g. -1 for previous week)

    If omitted, assumes the current ISO week.

    Output and totals behave the same as 'day'/'month', but filter entries
    by ISO week number and ISO year.
    """
    today = date.today()

    # Determine target ISO year and week
    if when:
        if re.fullmatch(r"-\d+", when):
            try:
                weeks_offset = int(when)
                target_date = today + timedelta(weeks=weeks_offset)
                iso = target_date.isocalendar()
                year = iso[0]
                week = iso[1]
            except Exception as e:
                click.echo(f"Error parsing week offset: {e}", err=True)
                sys.exit(2)
        elif re.fullmatch(r"\d{1,2}", when):
            year = today.year
            week = int(when)
        elif re.fullmatch(r"\d{4}-\d{1,2}", when):
            try:
                year_s, week_s = when.split("-", 1)
                year = int(year_s)
                week = int(week_s)
            except Exception as e:
                click.echo(f"Error parsing year-week: {e}", err=True)
                sys.exit(2)
        else:
            click.echo("Invalid week format. Use WW, YYYY-WW or -N", err=True)
            sys.exit(2)
    else:
        iso = today.isocalendar()
        year = iso[0]
        week = iso[1]

    # Read and parse only the monthly log file(s) that overlap the target ISO week.
    # A week can span two months, so include both months if necessary.
    try:
        start_date = date.fromisocalendar(year, week, 1)
    except Exception:
        # Fallback: compute an approximate start (shouldn't generally happen)
        start_date = today
    end_date = start_date + timedelta(days=6)

    months = {(start_date.year, start_date.month)}
    months.add((end_date.year, end_date.month))

    parsed: List[Tuple[datetime, str]] = []
    for y, m in sorted(months):
        path = _month_log_path_for(datetime(y, m, 1))
        parsed.extend(_read_and_parse_log_file(path))

    # Ensure entries are sorted by timestamp
    parsed.sort(key=lambda x: x[0])

    if not parsed:
        return

    # Use common printer with a predicate for the target ISO week
    _print_entries_and_total(
        parsed, lambda ts, _msg: ts.isocalendar()[0] == year and ts.isocalendar()[1] == week, grep
    )


@main.command("month", aliases=["m"])
@click.option("--grep", "-g", "grep", required=False, default=None, help="Filter entries by substring (case-insensitive).")
@click.argument("when", required=False)
def month_cmd(when: Optional[str], grep: Optional[str]) -> None:
    """
    Show all work logs for a given month.

    WHEN (optional) accepts:
      - YYYY-MM   (exact month)
      - MM        (assumes current year)
      - -N        (negative integer, e.g. -1 for previous month)

    If omitted, assumes the current month.

    Output format for each displayed entry:
      YYYY-MM-DD HH:MM:SS [HH:MM]>  MARKER_AND_DESCRIPTION

    The "start timestamp" is the timestamp of the previous log entry (or the
    entry's own timestamp if no previous entry exists). Duration is the
    difference between the entry's timestamp and the previous entry's
    timestamp (or '-' if unknown).

    Additionally, this command prints the total time spent on tasks for the
    month, excluding any "<break>" entries (including those that have extra
    text like "<break> grabbed coffee").
    """
    # Parse month argument
    today = date.today()
    if when:
        # support negative offsets like "-1" = previous month
        if re.fullmatch(r"-\d+", when):
            try:
                offset = int(when)
                # compute target year/month by shifting months
                total_months = today.year * 12 + (today.month - 1) + offset
                year = total_months // 12
                month = (total_months % 12) + 1
            except Exception as e:
                click.echo(f"Error parsing month offset: {e}", err=True)
                sys.exit(2)
        elif re.fullmatch(r"\d{4}-\d{2}", when):
            year_s, month_s = when.split("-", 1)
            year = int(year_s)
            month = int(month_s)
        elif re.fullmatch(r"\d{1,2}", when):
            year = today.year
            month = int(when)
        else:
            click.echo(f"Error parsing month: Unrecognized format: {when}", err=True)
            sys.exit(2)
    else:
        year = today.year
        month = today.month

    # Read and parse only the monthly log file for the requested month.
    month_dt = datetime(year, month, 1)
    path = _month_log_path_for(month_dt)
    parsed: List[Tuple[datetime, str]] = _read_and_parse_log_file(path)

    if not parsed:
        return

    # Use common printer with a predicate for the target month
    _print_entries_and_total(parsed, lambda ts, _msg: ts.year == year and ts.month == month, grep)
