#!/usr/bin/env python3

# ╭──────────────────────────────────────╮
# │ __main__.py on MacPower              │
# │ Nercone <nercone@diamondgotcat.net>  │
# │ Made by Nercone / MIT License        │
# │ Copyright (c) 2025 DiamondGotCat     │
# ╰──────────────────────────────────────╯

from __future__ import annotations

import sys
import json
import argparse
from datetime import time, datetime
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from .macpower import (
        MacPower,
        MacPowerError,
        PMGetOption,
        PMPowerSource,
        PMScope,
        PMSetting,
        PMEventType,
        PMWeekday,
        PMRepeatEvent,
        PMSectionedKeyValues,
    )
else:
    try:
        from .macpower import (
            MacPower,
            MacPowerError,
            PMGetOption,
            PMPowerSource,
            PMScope,
            PMSetting,
            PMEventType,
            PMWeekday,
            PMRepeatEvent,
            PMSectionedKeyValues,
        )
    except ImportError:  # pragma: no cover
        from macpower import (  # type: ignore[reportMissingImports]
            MacPower,
            MacPowerError,
            PMGetOption,
            PMPowerSource,
            PMScope,
            PMSetting,
            PMEventType,
            PMWeekday,
            PMRepeatEvent,
            PMSectionedKeyValues,
        )

def _console() -> Any:
    if Console is None:
        return None
    return Console()

def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)

def _parse_scope(scope: str) -> PMScope:
    return PMScope(scope)

def _parse_source(name: str) -> Optional[PMPowerSource]:
    name = name.strip().lower()
    if name in ("ac", "charger", "c"):
        return PMPowerSource.ACPower
    if name in ("battery", "batt", "b"):
        return PMPowerSource.BatteryPower
    if name in ("ups", "u"):
        return PMPowerSource.UPSPower
    if name in ("system", "systemwide", "system-wide", "sw", "none"):
        return None
    return None

def _try_parse_datetime(s: str) -> datetime:
    s = s.strip()
    fmts = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Invalid datetime format: {s!r}")

def _parse_time_hms(s: str) -> time:
    s = s.strip()
    fmts = ["%H:%M:%S", "%H:%M"]
    for fmt in fmts:
        try:
            t = datetime.strptime(s, fmt).time()
            return t.replace(second=0) if fmt == "%H:%M" else t
        except ValueError:
            pass
    raise ValueError(f"Invalid time format: {s!r}")

def _parse_weekdays(s: str) -> PMWeekday:
    s = s.strip().upper()
    if s in ("ALL", "DAILY", "*"):
        return PMWeekday.all()
    return PMWeekday.from_pmset(s)

def _pm_factory(ns: argparse.Namespace) -> MacPower:
    return MacPower(
        pmset_path=ns.pmset_path,
        sudo=ns.sudo,
        sudo_path=ns.sudo_path,
        timeout_sec=ns.timeout,
    )

def _print_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))

def _render_kv_table(title: str, kv: Dict[str, Any]) -> None:
    con = _console()
    if con is None:
        print(f"[{title}]")
        for k in sorted(kv.keys()):
            print(f"{k}\t{kv[k]}")
        return

    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("Key", overflow="fold")
    table.add_column("Value", overflow="fold")
    for k in sorted(kv.keys()):
        table.add_row(str(k), str(kv[k]))
    con.print(table)

def _render_sectioned_kv(obj: Any, *, json_out: bool, title: str) -> None:
    if json_out:
        out: Dict[str, Any] = {"raw": obj.raw, "sections": {}}
        for sec, kv in obj.sections.items():
            out["sections"][sec] = dict(kv)
        _print_json(out)
        return

    con = _console()
    if con is None:
        print(obj.raw, end="" if obj.raw.endswith("\n") else "\n")
        return

    if not obj.sections:
        con.print(Panel(Text(obj.raw.strip()), title=title))
        return

    for sec, kv in obj.sections.items():
        _render_kv_table(f"{title}: {sec}", dict(kv))

def _render_settings_snapshot(snapshot: Any, *, json_out: bool) -> None:
    if json_out:
        out: Dict[str, Any] = {"raw": snapshot.raw, "blocks": {}}
        for name, block in (
            ("system_wide", snapshot.system_wide),
            ("ac", snapshot.ac),
            ("battery", snapshot.battery),
            ("ups", snapshot.ups),
        ):
            if block is None:
                continue
            out["blocks"][name] = {
                "title": block.title,
                "source": None if block.source is None else block.source.value,
                "values": dict(block.values),
            }
        _print_json(out)
        return

    con = _console()
    if con is None:
        print(snapshot.raw)
        return

    blocks: List[Tuple[str, Any]] = []
    if snapshot.system_wide:
        blocks.append(("System-wide", snapshot.system_wide))
    if snapshot.ac:
        blocks.append(("AC", snapshot.ac))
    if snapshot.battery:
        blocks.append(("Battery", snapshot.battery))
    if snapshot.ups:
        blocks.append(("UPS", snapshot.ups))

    for label, block in blocks:
        _render_kv_table(f"{label}: {block.title}", dict(block.values))

def _coerce_value(s: str) -> Union[int, str]:
    v = s.strip()
    vl = v.lower()
    if vl in ("on", "true", "yes", "y", "enable", "enabled"):
        return 1
    if vl in ("off", "false", "no", "n", "disable", "disabled"):
        return 0
    if v.lstrip("-").isdigit():
        return int(v)
    return v

def _coerce_key(k: str) -> Union[PMSetting, str]:
    k = k.strip()
    try:
        return PMSetting(k)
    except ValueError:
        return k

def _cmd_status(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    st = pm.battery_status()

    if ns.json:
        _print_json(
            {
                "source": st.source.value,
                "percent": st.percent,
                "state": st.state.value,
                "time_remaining_sec": None if st.time_remaining is None else int(st.time_remaining.total_seconds()),
                "present": st.present,
                "raw": st.raw,
            }
        )
        return 0

    con = _console()
    if con is None:
        print(st.raw.strip())
        return 0

    lines = []
    lines.append(f"Power Source: {st.source.value}")
    if st.percent is not None:
        lines.append(f"Battery: {st.percent}%")
    lines.append(f"State: {st.state.value}")
    if st.time_remaining is not None:
        lines.append(f"Time Remaining: {st.time_remaining}")
    if st.present is not None:
        lines.append(f"Present: {st.present}")

    con.print(Panel(Text("\n".join(lines)), title="Status"))
    return 0

def _cmd_get(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.get_text(ns.option)
    if ns.json:
        _print_json({"option": str(ns.option), "raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def _cmd_exec(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    r = pm.run(*ns.pmset_args, check=not ns.no_check)
    if ns.json:
        _print_json(
            {
                "args": r.args,
                "returncode": r.returncode,
                "stdout": r.stdout,
                "stderr": r.stderr,
            }
        )
    else:
        if r.stdout:
            print(r.stdout, end="" if r.stdout.endswith("\n") else "\n")
        if r.stderr:
            _eprint(r.stderr.rstrip())
        if r.returncode != 0:
            return int(r.returncode)
    return 0

def _cmd_settings_show(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    kind = ns.kind
    if kind == "custom":
        snap = pm.custom_settings()
    elif kind == "live":
        snap = pm.live_settings()
    else:
        snap = pm.settings_snapshot()
    _render_settings_snapshot(snap, json_out=ns.json)
    return 0

def _cmd_settings_keys(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    keys = pm.available_settings(use_custom=not ns.no_custom)
    if ns.json:
        _print_json(keys)
        return 0

    con = _console()
    if con is None:
        print(keys)
        return 0

    for section, items in keys.items():
        table = Table(title=f"Keys: {section}", show_header=True, header_style="bold")
        table.add_column("Setting Key")
        for k in items:
            table.add_row(k)
        con.print(table)
    return 0

def _cmd_settings_get(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    snap = pm.custom_settings() if ns.custom else pm.settings_snapshot()

    block = None
    if ns.source:
        src = _parse_source(ns.source)
        if src is None:
            block = snap.system_wide
        else:
            block = snap.for_source(src)
    else:
        for b in (snap.system_wide, snap.ac, snap.battery, snap.ups):
            if b and (ns.key in b.values):
                block = b
                break

    if block is None:
        raise MacPowerError(f"Key not found in snapshot: {ns.key}")

    val = block.get(ns.key)
    if ns.json:
        _print_json(
            {
                "key": ns.key,
                "value": val,
                "block_title": block.title,
                "block_source": None if block.source is None else block.source.value,
            }
        )
    else:
        print(val)
    return 0

def _parse_kv_pairs(pairs: List[str]) -> Dict[Union[PMSetting, str], Union[int, str]]:
    out: Dict[Union[PMSetting, str], Union[int, str]] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid setting pair (expected KEY=VALUE): {item!r}")
        k, v = item.split("=", 1)
        key = _coerce_key(k)
        val = _coerce_value(v)
        out[key] = val
    return out

def _cmd_settings_set(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    settings = _parse_kv_pairs(ns.pairs)
    pm.set_settings(settings, scope=_parse_scope(ns.scope))
    if ns.json:
        _print_json({"ok": True, "scope": ns.scope, "applied": {str(k): v for k, v in settings.items()}})
    return 0

def _cmd_legacy_dim(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    pm.set_dim(_coerce_value(ns.value), scope=_parse_scope(ns.scope))
    if ns.json:
        _print_json({"ok": True, "legacy": "dim", "scope": ns.scope, "value": _coerce_value(ns.value)})
    return 0

def _cmd_legacy_spindown(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    pm.set_spindown(_coerce_value(ns.value), scope=_parse_scope(ns.scope))
    if ns.json:
        _print_json({"ok": True, "legacy": "spindown", "scope": ns.scope, "value": _coerce_value(ns.value)})
    return 0

def _cmd_cap_show(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    cap = pm.cap()
    _render_sectioned_kv(cap, json_out=ns.json, title="Capabilities")
    return 0

def _cmd_ups_show(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    ups = pm.ups_info()
    _render_sectioned_kv(ups, json_out=ns.json, title="UPS")
    return 0

def _cmd_ups_thresholds(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    pm.set_ups_thresholds(
        haltlevel=ns.haltlevel,
        haltafter_min=ns.haltafter,
        haltremain_min=ns.haltremain,
        off=ns.off,
    )
    if ns.json:
        _print_json(
            {
                "ok": True,
                "off": bool(ns.off),
                "haltlevel": ns.haltlevel,
                "haltafter_min": ns.haltafter,
                "haltremain_min": ns.haltremain,
            }
        )
    return 0

def _cmd_adapter_show(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    ad = pm.adapter()
    _render_sectioned_kv(ad, json_out=ns.json, title="Adapter (AC)")
    return 0

def _cmd_sched_show(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    snap = pm.sched()

    if ns.json:
        _print_json(
            {
                "raw": snap.raw,
                "one_time": [
                    {
                        "event_type": e.event_type,
                        "when": None if e.when is None else e.when.isoformat(sep=" "),
                        "owner": e.owner,
                        "index": e.index,
                        "raw": e.raw,
                    }
                    for e in snap.one_time
                ],
                "repeating": [
                    {"event_type": str(e.event_type), "weekdays": e.weekdays.to_pmset(), "time": e.time.isoformat()}
                    for e in snap.repeating
                ],
            }
        )
        return 0

    con = _console()
    if con is None:
        print(snap.raw.strip())
        return 0

    if snap.one_time:
        t1 = Table(title="Scheduled (one-time)", show_header=True, header_style="bold")
        t1.add_column("Index", justify="right")
        t1.add_column("Type")
        t1.add_column("When")
        t1.add_column("Owner")
        for e in snap.one_time:
            t1.add_row(
                "" if e.index is None else str(e.index),
                e.event_type,
                "" if e.when is None else e.when.strftime("%Y-%m-%d %H:%M:%S"),
                "" if e.owner is None else e.owner,
            )
        con.print(t1)
    else:
        con.print(Panel("No one-time scheduled events.", title="Scheduled (one-time)"))

    if snap.repeating:
        t2 = Table(title="Scheduled (repeating)", show_header=True, header_style="bold")
        t2.add_column("Type")
        t2.add_column("Weekdays")
        t2.add_column("Time")
        for e in snap.repeating:
            t2.add_row(str(e.event_type), e.weekdays.to_pmset(), e.time.strftime("%H:%M:%S"))
        con.print(t2)
    else:
        con.print(Panel("No repeating events.", title="Scheduled (repeating)"))

    return 0

def _cmd_sched_add(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    when = _try_parse_datetime(ns.when)
    pm.schedule(ns.type, when, owner=ns.owner)
    if ns.json:
        _print_json({"ok": True, "type": str(ns.type), "when": when.isoformat(sep=" "), "owner": ns.owner})
    return 0

def _cmd_sched_cancel(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    if ns.all:
        pm.schedule_cancelall()
        if ns.json:
            _print_json({"ok": True, "cancel": "all"})
        return 0

    pm.schedule_cancel(ns.type)
    if ns.json:
        _print_json({"ok": True, "cancel": str(ns.type)})
    return 0

def _cmd_repeat_set(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)

    ev1 = PMRepeatEvent(
        event_type=PMEventType(str(ns.type1)),
        weekdays=_parse_weekdays(ns.days1),
        time=_parse_time_hms(ns.time1),
    )

    events = [ev1]

    if ns.type2 and ns.days2 and ns.time2:
        ev2 = PMRepeatEvent(
            event_type=PMEventType(str(ns.type2)),
            weekdays=_parse_weekdays(ns.days2),
            time=_parse_time_hms(ns.time2),
        )
        events.append(ev2)

    pm.repeat(*events)

    if ns.json:
        _print_json(
            {
                "ok": True,
                "events": [
                    {"type": str(e.event_type), "days": e.weekdays.to_pmset(), "time": e.time.isoformat()}
                    for e in events
                ],
            }
        )
    return 0

def _cmd_repeat_cancel(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    pm.repeat_cancel()
    if ns.json:
        _print_json({"ok": True})
    return 0

def _cmd_action(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    act = ns.action.strip()

    if act == "sleepnow":
        pm.sleepnow()
    elif act == "displaysleepnow":
        pm.displaysleepnow()
    elif act == "hibernatenow":
        pm.hibernatenow()
    elif act == "shutdownnow":
        pm.shutdownnow()
    elif act == "restartnow":
        pm.restartnow()
    elif act == "touch":
        pm.touch()
    elif act == "boot":
        pm.boot()
    elif act == "restoredefaults":
        pm.restoredefaults()
    elif act == "resetdisplayambientparams":
        pm.resetdisplayambientparams()
    elif act == "noidle":
        for line in pm.noidle():
            print(line)
        return 0
    else:
        raise MacPowerError("Unknown action. Supported immediate actions: sleepnow, displaysleepnow, hibernatenow, shutdownnow, restartnow, touch, boot, restoredefaults, resetdisplayambientparams, noidle.\nIf you intended to set a pmset key, provide VALUE: e.g. `macpower action standby on`")

    if ns.json:
        _print_json({"ok": True, "mode": "action", "action": act})
    return 0

def _cmd_relative(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    pm.relative(ns.kind, int(ns.seconds))
    if ns.json:
        _print_json({"ok": True, "kind": str(ns.kind), "seconds": int(ns.seconds)})
    return 0

def _cmd_stream(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    kind = ns.kind

    if kind == "pslog":
        gen = pm.pslog()
    elif kind == "rawlog":
        gen = pm.rawlog()
    elif kind == "assertionslog":
        gen = pm.assertionslog()
    elif kind == "sysloadlog":
        gen = pm.sysloadlog()
    elif kind == "thermlog":
        gen = pm.thermlog()
    elif kind == "uuidlog":
        gen = pm.uuidlog()
    elif kind == "powerstatelog":
        gen = pm.powerstatelog(ns.interval, *ns.class_names)
    elif kind == "noidle":
        gen = pm.noidle()
    else:
        raise MacPowerError(f"Unknown stream: {kind}")

    for line in gen:
        print(line)
    return 0

def _cmd_history_show(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.history()
    if ns.json:
        _print_json({"raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def _cmd_history_detailed(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.history_detailed(ns.uuid)
    if ns.json:
        _print_json({"uuid": ns.uuid, "raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def _cmd_powerstate(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.powerstate(*ns.class_names)
    if ns.json:
        _print_json({"classes": list(ns.class_names), "raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def _cmd_stats(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.stats()
    if ns.json:
        _print_json({"raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def _cmd_systemstate(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.systemstate()
    if ns.json:
        _print_json({"raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def _cmd_everything(ns: argparse.Namespace) -> int:
    pm = _pm_factory(ns)
    txt = pm.everything()
    if ns.json:
        _print_json({"raw": txt})
    else:
        print(txt, end="" if txt.endswith("\n") else "\n")
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="macpower")
    p.add_argument("--pmset-path", default="pmset", help="Path to pmset (default: pmset)")
    p.add_argument("--sudo", action="store_true", help="Run pmset via sudo")
    p.add_argument("--sudo-path", default="sudo", help="Path to sudo (default: sudo)")
    p.add_argument("--timeout", type=float, default=30.0, help="Command timeout seconds (default: 30)")
    p.add_argument("--json", action="store_true", help="Output as JSON where applicable")

    sub = p.add_subparsers(dest="cmd", required=True)

    # status
    s = sub.add_parser("status", help="Show current battery/power source status")
    s.set_defaults(func=_cmd_status)

    # get
    g = sub.add_parser("get", help="Run pmset -g <option> and print output")
    g.add_argument("option", type=str, help="pmset -g option (e.g. batt, custom, live, cap, sched, log, everything)")
    g.set_defaults(func=_cmd_get)

    # exec
    ex = sub.add_parser("exec", help="Run arbitrary pmset arguments (library .run() equivalent)")
    ex.add_argument("--no-check", action="store_true", help="Do not raise on non-zero return code")
    ex.add_argument("pmset_args", nargs=argparse.REMAINDER, help="Arguments passed to pmset (e.g. -g custom)")
    ex.set_defaults(func=_cmd_exec)

    # settings
    st = sub.add_parser("settings", help="Show / get / set pmset settings")
    stsub = st.add_subparsers(dest="settings_cmd", required=True)

    st_show = stsub.add_parser("show", help="Show settings snapshot")
    st_show.add_argument("--kind", choices=["default", "custom", "live"], default="custom")
    st_show.set_defaults(func=_cmd_settings_show)

    st_keys = stsub.add_parser("keys", help="List setting keys available on this machine")
    st_keys.add_argument("--no-custom", action="store_true", help="Use pmset -g (default snapshot) instead of -g custom")
    st_keys.set_defaults(func=_cmd_settings_keys)

    st_get = stsub.add_parser("get", help="Get a setting value from snapshot")
    st_get.add_argument("key", help="Setting key (e.g. displaysleep, sleep, powernap, ...) or raw key")
    st_get.add_argument(
        "--source",
        default="",
        help="Prefer block: ac|battery|ups|system (optional). If omitted, searches blocks that contain the key.",
    )
    st_get.add_argument("--custom", action="store_true", help="Use pmset -g custom snapshot")
    st_get.set_defaults(func=_cmd_settings_get)

    st_set = stsub.add_parser("set", help="Set one or more settings (KEY=VALUE ...)")
    st_set.add_argument("--scope", choices=["a", "b", "c", "u"], default="a", help="pmset scope: a/b/c/u (default: a)")
    st_set.add_argument("pairs", nargs="+", help="Setting pairs: KEY=VALUE KEY2=VALUE2 ...")
    st_set.set_defaults(func=_cmd_settings_set)

    # legacy shortcuts
    lg = sub.add_parser("legacy", help="Legacy convenience wrappers (dim/spindown)")
    lgsub = lg.add_subparsers(dest="legacy_cmd", required=True)

    lg_dim = lgsub.add_parser("dim", help="Set legacy 'dim' (deprecated; use displaysleep)")
    lg_dim.add_argument("--scope", choices=["a", "b", "c", "u"], default="a")
    lg_dim.add_argument("value", help="Value (int/on/off)")
    lg_dim.set_defaults(func=_cmd_legacy_dim)

    lg_sp = lgsub.add_parser("spindown", help="Set legacy 'spindown' (deprecated; use disksleep)")
    lg_sp.add_argument("--scope", choices=["a", "b", "c", "u"], default="a")
    lg_sp.add_argument("value", help="Value (int/on/off)")
    lg_sp.set_defaults(func=_cmd_legacy_spindown)

    # cap
    cap = sub.add_parser("cap", help="Show pmset capabilities (parsed)")
    cap.set_defaults(func=_cmd_cap_show)

    # ups
    ups = sub.add_parser("ups", help="UPS information and thresholds")
    upssub = ups.add_subparsers(dest="ups_cmd", required=True)

    ups_show = upssub.add_parser("show", help="Show UPS info (parsed from pmset -g ups)")
    ups_show.set_defaults(func=_cmd_ups_show)

    ups_thr = upssub.add_parser("thresholds", help="Set UPS shutdown thresholds (pmset -u ...)")
    ups_thr.add_argument("--haltlevel", type=int, default=None, help="Battery level at which to halt/shutdown")
    ups_thr.add_argument("--haltafter", type=int, default=None, help="Minutes after which to halt/shutdown")
    ups_thr.add_argument("--haltremain", type=int, default=None, help="Minutes remaining at which to halt/shutdown")
    ups_thr.add_argument("--off", action="store_true", help="Disable specified threshold(s) (set -1)")
    ups_thr.set_defaults(func=_cmd_ups_thresholds)

    # adapter
    ad = sub.add_parser("adapter", help="Show AC adapter info (parsed)")
    ad.set_defaults(func=_cmd_adapter_show)

    # sched
    sc = sub.add_parser("sched", help="Manage scheduled power events")
    scsub = sc.add_subparsers(dest="sched_cmd", required=True)

    sc_show = scsub.add_parser("show", help="Show scheduled events (pmset -g sched)")
    sc_show.set_defaults(func=_cmd_sched_show)

    sc_add = scsub.add_parser("add", help="Add one-time schedule (pmset schedule)")
    sc_add.add_argument("type", type=str, help="Event type: wake|sleep|poweron|shutdown|wakeorpoweron")
    sc_add.add_argument("when", help='When: "YYYY-mm-dd HH:MM[:SS]" or "MM/dd/yy HH:MM[:SS]"')
    sc_add.add_argument("--owner", default=None, help="Owner string (optional)")
    sc_add.set_defaults(func=_cmd_sched_add)

    sc_cancel = scsub.add_parser("cancel", help="Cancel schedule (pmset schedule cancel|cancelall)")
    sc_cancel.add_argument("--all", action="store_true", help="Cancel all scheduled events")
    sc_cancel.add_argument("type", nargs="?", default="wake", help="Event type to cancel (ignored if --all)")
    sc_cancel.set_defaults(func=_cmd_sched_cancel)

    # repeat
    rp = sub.add_parser("repeat", help="Manage repeating events (pmset repeat)")
    rpsub = rp.add_subparsers(dest="repeat_cmd", required=True)

    rp_set = rpsub.add_parser("set", help="Set 1 or 2 repeating events")
    rp_set.add_argument("type1", help="Event type 1: wake|sleep|poweron|shutdown|wakeorpoweron")
    rp_set.add_argument("days1", help="Weekdays: MTWRFSU | ALL")
    rp_set.add_argument("time1", help="Time: HH:MM[:SS]")

    rp_set.add_argument("type2", nargs="?", default=None, help="(Optional) Event type 2")
    rp_set.add_argument("days2", nargs="?", default=None, help="(Optional) Weekdays 2")
    rp_set.add_argument("time2", nargs="?", default=None, help="(Optional) Time 2")
    rp_set.set_defaults(func=_cmd_repeat_set)

    rp_cancel = rpsub.add_parser("cancel", help="Cancel repeating events")
    rp_cancel.set_defaults(func=_cmd_repeat_cancel)

    # relative
    rel = sub.add_parser("relative", help="Schedule a relative wake/poweron in N seconds")
    rel.add_argument("kind", choices=["wake", "poweron"])
    rel.add_argument("seconds", type=int)
    rel.set_defaults(func=_cmd_relative)

    # action
    act = sub.add_parser("action", help="Run immediate action, or set a single pmset key (KEY VALUE)")
    act.add_argument("action", help="Action name (sleepnow/displaysleepnow/hibernatenow/shutdownnow/restartnow/touch/boot/restoredefaults/resetdisplayambientparams/noidle)")
    act.add_argument("--scope", choices=["a", "b", "c", "u"], default="a", help="Scope for KEY VALUE mode (default: a)")
    act.set_defaults(func=_cmd_action)

    # stream
    stp = sub.add_parser("stream", help="Stream pmset logs / noidle (blocks until interrupted)")
    stp.add_argument("kind", choices=["pslog", "rawlog", "assertionslog", "sysloadlog", "thermlog", "uuidlog", "powerstatelog", "noidle"])
    stp.add_argument("--interval", type=int, default=None, help="powerstatelog interval seconds (optional)")
    stp.add_argument("class_names", nargs="*", help="(powerstatelog only) Optional class names")
    stp.set_defaults(func=_cmd_stream)

    # history
    hist = sub.add_parser("history", help="Show power history (parsed command wrappers)")
    hsub = hist.add_subparsers(dest="history_cmd", required=True)

    h_show = hsub.add_parser("show", help="Show pmset -g history")
    h_show.set_defaults(func=_cmd_history_show)

    h_det = hsub.add_parser("detailed", help="Show pmset -g historydetailed <uuid>")
    h_det.add_argument("uuid", help="UUID for historydetailed")
    h_det.set_defaults(func=_cmd_history_detailed)

    # powerstate
    ps = sub.add_parser("powerstate", help="Show pmset -g powerstate [class ...]")
    ps.add_argument("class_names", nargs="*", help="Optional class names")
    ps.set_defaults(func=_cmd_powerstate)

    # stats
    stt = sub.add_parser("stats", help="Show pmset -g stats")
    stt.set_defaults(func=_cmd_stats)

    # systemstate
    ss = sub.add_parser("systemstate", help="Show pmset -g systemstate")
    ss.set_defaults(func=_cmd_systemstate)

    # everything
    ev = sub.add_parser("everything", help="Show pmset -g everything")
    ev.set_defaults(func=_cmd_everything)

    return p

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.cmd == "get":
        if ns.option == "adapter":
            ns.option = "ac"

    if ns.cmd == "exec":
        if not ns.pmset_args:
            raise SystemExit("macpower exec: no arguments provided. Example: macpower exec -g custom")

    try:
        return int(ns.func(ns))
    except MacPowerError as e:
        con = _console()
        msg = str(e).rstrip()
        if con is None:
            _eprint(f"ERROR: {msg}")
        else:
            con.print(Panel(Text(msg), title="Error", border_style="red"))
        return 2
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        con = _console()
        msg = f"{type(e).__name__}: {e}"
        if con is None:
            _eprint(f"ERROR: {msg}")
        else:
            con.print(Panel(Text(msg), title="Unhandled Error", border_style="red"))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
