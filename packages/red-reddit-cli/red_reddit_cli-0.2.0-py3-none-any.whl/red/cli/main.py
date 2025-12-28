#!/usr/bin/env python
# Copyright 2025 George Kontridze

"""red CLI core."""

import re
import sys
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast

import xdg_base_dirs
import yaml
from click import Command
from click.core import Context
from praw import Reddit
from rich.console import Console
from rich.table import Column, Table
from typer import Option, Typer
from typer.core import TyperGroup

if TYPE_CHECKING:
    from praw.models import Multireddit
    from praw.reddit import Subreddit

CTX_SETTINGS: dict[str, Any] = {"help_option_names": ["-h", "--help"]}
RED_CFG = xdg_base_dirs.xdg_config_home() / "red.yaml"


class AliasGroup(TyperGroup):
    """Typer Group that configures aliased commands."""

    _CMD_SPLIT_P = re.compile(r" ?[,|] ?")

    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        """
        Override for super().get_command() that checks for aliases.

        Returns:
            click Command or Nont

        """
        cmd_name = self._group_cmd_name(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _group_cmd_name(self, default_name: str) -> str:
        for cmd in self.commands.values():
            name = cmd.name
            if name and default_name in self._CMD_SPLIT_P.split(name):
                return name

        return default_name


def aliases(names: list[str]) -> str:
    """
    Format list of aliases into special alias string format.

    Returns:
        specially-formatted alias string

    """
    return " | ".join(names)


root = Typer(
    name="red",
    cls=AliasGroup,
    context_settings=CTX_SETTINGS,
    invoke_without_command=True,
    no_args_is_help=True,
    help="""
    Red - a Reddit CLI

    Not a fully-fledged API CLI, rather a convenience helper for organizing
    """,
)

client = Reddit()
console = Console()


class SubSortKey(StrEnum):
    """Subreddit sort key."""

    url = "url"
    display_name = "display_name"
    title = "title"  # type: ignore[assignment]
    subscribers = "subscribers"


subs = Typer(
    name="subs",
    cls=AliasGroup,
    context_settings=CTX_SETTINGS,
    no_args_is_help=True,
    help="Manage subreddits. CRUD for now",
)


@subs.command(aliases(["list", "ls", "l"]))
def list_subs(
    sort: Annotated[SubSortKey, Option("-s", "--sort")] = SubSortKey.url,
) -> None:
    """List all subscribed subreddits."""
    table = Table(
        *(Column(n) for n in ["url", "display_name", "title", "subscribers", "feed"])
    )

    multis = client.user.multireddits()
    sub_to_multi: dict[Subreddit, set[Multireddit]] = defaultdict(set)
    for m in multis:
        for s in m.subreddits:
            sub_to_multi[s.url].add(m)

    for sub in sorted(
        client.user.subreddits(limit=None),  # type: ignore[arg-type]
        key=lambda s: getattr(s, sort),
        reverse=sort == SubSortKey.subscribers,
    ):
        s = cast("Subreddit", sub)
        table.add_row(
            s.url,
            s.display_name,
            s.title,
            f"{s.subscribers:,}",
            (
                ", ".join(m.name for m in sub_to_multi[sub.url])
                if s.url in sub_to_multi
                else None
            ),
        )

    console.print(table)


@subs.command(aliases(["subscribe", "sub", "s"]))
def subscribe(sub_names: list[str]) -> None:
    """Subscribe to subreddits."""
    for sub_name in sub_names:
        client.subreddit(sub_name).subscribe()
        console.print(f"Subscribed to r/{sub_name}")


@subs.command(aliases(["unsubscribe", "unsub", "un", "u"]))
def unsubscribe(sub_names: list[str]) -> None:
    """Unsubscribe from subreddits."""
    for sub_name in sub_names:
        client.subreddit(sub_name).unsubscribe()
        console.print(f"Unsubscribed from r/{sub_name}")


root.add_typer(subs, name=subs.info.name, help="Subreddit commands")


multis = Typer(
    name="multis",
    cls=AliasGroup,
    context_settings=CTX_SETTINGS,
    no_args_is_help=True,
    help="Manage custom feeds (multireddits).",
)


class MultiRedditSortKey(StrEnum):
    """multireddit sort key."""

    name = "name"  # type: ignore[assignment]
    sub_count = "sub_count"


@multis.command(aliases(["list", "ls", "l"]))
def list_multis(
    sort: Annotated[
        MultiRedditSortKey,
        Option("-s", "--sort"),
    ] = MultiRedditSortKey.name,  # type: ignore[arg-type]
    reverse: Annotated[bool, Option("-r", "--reverse", "Reverse sort")] = False,  # noqa: FBT002
) -> None:
    """List all multireddits (custom feeds)."""
    table = Table(*(Column(n) for n in ["name", "sub_count"]))

    for multi in sorted(
        client.user.multireddits(),
        key=(
            lambda m: getattr(m, sort)
            if sort != MultiRedditSortKey.sub_count
            else len(m.subreddits)
        ),
        reverse=reverse,
    ):
        m = cast("Multireddit", multi)
        table.add_row(m.name, str(len(m.subreddits)))

    console.print(table)


def suburl_to_name(u: str) -> str:
    """
    Given a subreddit url, return its name.

    Args:
        u: subreddit url

    Returns:
        subreddit name

    """
    return u.split("/")[2]


@multis.command(aliases(["genconf", "gen", "g"]))
def genconf(out: Annotated[Path, Option("-o", "--output")] = RED_CFG) -> None:
    """Generate multisub config."""
    conf: dict[str, list[str]] = {}

    for multi in sorted(client.user.multireddits(), key=lambda m: m.name):
        conf[multi.name] = sorted([suburl_to_name(s.url) for s in multi.subreddits])

    match out.name:
        case "-":
            yaml.dump(conf, sys.stdout)

        case _:
            with out.open("w") as f:
                yaml.dump(conf, f)

            console.print(f"wrote {out.resolve().as_posix()}")


class NoAuthenticatedUserError(RuntimeError):
    """Raised when there is no authenticated user."""

    def __init__(self, *_: object) -> None:
        """Raise with simple message."""
        super().__init__("could not determine authenticated user")


@multis.command(aliases(["apply", "app", "a"]))
def apply(infile: Annotated[Path, Option("-i", "--input")] = RED_CFG) -> None:
    """
    Apply multisub config.

    Raises:
        NoAuthenticatedUserError: If the authenticated user cannot be determined.

    """
    me = client.user.me()
    if me is None:
        raise NoAuthenticatedUserError

    my_subs = {s.display_name.lower() for s in client.user.subreddits()}

    cfg: dict[str, list[str]] = {}

    match infile.name:
        case "-":
            console.print("reading config from stdin")
            cfg = yaml.load(sys.stdin, yaml.SafeLoader)

        case _:
            console.print(f"reading config from {infile}")
            with infile.open() as f:
                cfg = yaml.load(f, yaml.SafeLoader)

    local_multis = set(cfg.keys())
    remote_multis = {
        m.name for m in sorted(client.user.multireddits(), key=lambda m: m.name)
    }

    # Remove what's on remote but not in config
    deleted = set()
    for to_delete_multi in remote_multis - local_multis:
        console.print(f"{to_delete_multi} not in config - removing")
        client.multireddit(name=to_delete_multi, redditor=me.name).delete()
        deleted.add(to_delete_multi)

    # Add what's in config but not on remote
    added = set()
    for to_create_multi in local_multis - remote_multis:
        if not cfg[to_create_multi]:
            console.print(f"{to_create_multi} has no subs under it - skipping")
        console.print(
            f"{to_create_multi} does not exist yet - creating and adding subs",
        )
        client.multireddit.create(
            display_name=to_create_multi.capitalize(),
            subreddits=cfg[to_create_multi],  # type: ignore[arg-type]
        )
        for newsub in cfg[to_create_multi]:
            if newsub in my_subs:
                continue

            console.print(f"not subbsed to {newsub} - subbing")
            client.subreddit(newsub).subscribe()

        added.add(to_create_multi)

    # Update what's in config and on remote
    updated = defaultdict(lambda: {"added": [], "removed": []})
    for to_update_multi in local_multis & remote_multis:
        local_subs = set(cfg[to_update_multi])
        remote_subs = {
            sub.display_name
            for sub in client.multireddit(
                name=to_update_multi,
                redditor=me.name,
            ).subreddits
        }
        if local_subs == remote_subs:
            continue

        console.print(
            f"updating {to_update_multi} with {len(cfg[to_update_multi])} subs",
        )
        client.multireddit(name=to_update_multi, redditor=me.name).update(
            subreddits=cfg[to_update_multi],  # type: ignore[arg-type]
        )

        updated[to_update_multi]["added"] = list(local_subs - remote_subs)
        updated[to_update_multi]["removed"] = list(remote_subs - local_subs)

    console.print(f"removed multireddits: {deleted}")
    console.print(f"added multireddits: {added}")
    console.print(f"updated multireddits: {updated.items()}")


root.add_typer(
    multis, name=multis.info.name, help="Manage multireddits (custom feeds)."
)


def main() -> None:
    """Execute the red CLI."""
    root()


if __name__ == "__main__":
    main()
