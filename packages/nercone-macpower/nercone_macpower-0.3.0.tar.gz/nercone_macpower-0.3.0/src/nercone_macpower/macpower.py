#!/usr/bin/env python3

# ╭──────────────────────────────────────╮
# │ macpower.py on MacPower              │
# │ Nercone <nercone@diamondgotcat.net>  │
# │ Made by Nercone / MIT License        │
# │ Copyright (c) 2025 DiamondGotCat     │
# ╰──────────────────────────────────────╯

from __future__ import annotations

import re
import shlex
import platform
import subprocess
import dataclasses
from datetime import time, datetime, timedelta
from enum import Enum, IntFlag
from typing import Any, Dict, Generator, Iterable, List, Mapping, Optional, Tuple, Union, Literal

class MacPowerError(RuntimeError):
    pass

@dataclasses.dataclass(frozen=True)
class CommandResult:
    args: List[str]
    returncode: int
    stdout: str
    stderr: str

def _ensure_macos() -> None:
    if platform.system() != "Darwin":
        raise MacPowerError("This wrapper is intended for macOS (Darwin) only.")

class PMPowerSource(Enum):
    ACPower = "AC Power"
    BatteryPower = "Battery Power"
    UPSPower = "UPS Power"
    Unknown = "Unknown"

    @staticmethod
    def from_pmset_title(title: str) -> "PMPowerSource":
        title = title.strip()
        if title == "AC Power":
            return PMPowerSource.ACPower
        if title == "Battery Power":
            return PMPowerSource.BatteryPower
        if title == "UPS Power":
            return PMPowerSource.UPSPower
        return PMPowerSource.Unknown

class PMScope(Enum):
    """pmset set scope flags."""
    All = "a"        # -a
    Battery = "b"    # -b
    Charger = "c"    # -c (AC/Charger)
    UPS = "u"        # -u

    def flag(self) -> str:
        return f"-{self.value}"

class PMEventType(Enum):
    Sleep = "sleep"
    Wake = "wake"
    PowerOn = "poweron"
    Shutdown = "shutdown"
    WakeOrPowerOn = "wakeorpoweron"

    def __str__(self) -> str:
        return self.value

class PMRelativeKind(Enum):
    Wake = "wake"
    PowerOn = "poweron"

    def __str__(self) -> str:
        return self.value

class PMBatteryState(Enum):
    Charging = "charging"
    Discharging = "discharging"
    Charged = "charged"
    FinishingCharge = "finishing charge"
    Unknown = "unknown"

class PMWeekday(IntFlag):
    """
    pmset repeat weekday encoding uses: MTWRFSU
    - M=Mon, T=Tue, W=Wed, R=Thu, F=Fri, S=Sat, U=Sun
    """
    M = 1 << 0
    T = 1 << 1
    W = 1 << 2
    R = 1 << 3
    F = 1 << 4
    S = 1 << 5
    U = 1 << 6

    @staticmethod
    def all() -> "PMWeekday":
        return PMWeekday.M | PMWeekday.T | PMWeekday.W | PMWeekday.R | PMWeekday.F | PMWeekday.S | PMWeekday.U

    def to_pmset(self) -> str:
        order = [("M", PMWeekday.M), ("T", PMWeekday.T), ("W", PMWeekday.W), ("R", PMWeekday.R), ("F", PMWeekday.F), ("S", PMWeekday.S), ("U", PMWeekday.U)]
        out = []
        for ch, bit in order:
            if self & bit:
                out.append(ch)
        return "".join(out)

    @staticmethod
    def from_pmset(s: str) -> "PMWeekday":
        s = s.strip().upper()
        m = PMWeekday(0)
        mapping = {"M": PMWeekday.M, "T": PMWeekday.T, "W": PMWeekday.W, "R": PMWeekday.R, "F": PMWeekday.F, "S": PMWeekday.S, "U": PMWeekday.U}
        for ch in s:
            if ch in mapping:
                m |= mapping[ch]
        return m

class PMGetOption(Enum):
    # pmset -g options (PMSET(1) GETTING)
    Live = "live"
    Custom = "custom"
    Cap = "cap"
    Sched = "sched"
    UPS = "ups"
    PS = "ps"
    Batt = "batt"

    PSLog = "pslog"
    RawLog = "rawlog"

    Therm = "therm"
    ThermLog = "thermlog"

    Assertions = "assertions"
    AssertionsLog = "assertionslog"

    SysLoad = "sysload"
    SysLoadLog = "sysloadlog"

    Adapter = "ac"
    AdapterAlias = "adapter"

    Log = "log"

    UUID = "uuid"
    UUIDLog = "uuidlog"

    History = "history"
    HistoryDetailed = "historydetailed"

    PowerState = "powerstate"
    PowerStateLog = "powerstatelog"

    Stats = "stats"
    SystemState = "systemstate"
    Everything = "everything"

    def __str__(self) -> str:
        return self.value

class PMSetting(Enum):
    # Idle timers (minutes; 0 disables)
    Sleep = "sleep"
    DisplaySleep = "displaysleep"
    DiskSleep = "disksleep"

    # Wake / networking
    Womp = "womp"
    Ring = "ring"
    ProximityWake = "proximitywake"

    # Power Nap
    PowerNap = "powernap"

    # Restart / wake triggers
    AutoRestart = "autorestart"
    LidWake = "lidwake"
    ACWake = "acwake"

    # Display brightness behavior
    LessBright = "lessbright"
    HalfDim = "halfdim"

    # Sudden Motion Sensor
    SMS = "sms"

    # Hibernate / standby / autopoweroff
    HibernateMode = "hibernatemode"
    HibernateFile = "hibernatefile"

    Standby = "standby"
    StandbyDelay = "standbydelay"

    StandbyDelayHigh = "standbydelayhigh"
    StandbyDelayLow = "standbydelaylow"
    HighStandbyThreshold = "highstandbythreshold"

    AutoPowerOff = "autopoweroff"
    AutoPowerOffDelay = "autopoweroffdelay"

    # TTY keep awake
    TtyKeepAwake = "ttyskeepawake"

    # Networking presentation during sleep (unsupported on some platforms)
    NetworkOverSleep = "networkoversleep"

    # FileVault key handling on standby
    DestroyFVKeyOnStandby = "destroyfvkeyonstandby"

    def __str__(self) -> str:
        return self.value

@dataclasses.dataclass(frozen=True)
class PMBatteryStatus:
    source: PMPowerSource
    percent: Optional[int]
    state: PMBatteryState
    time_remaining: Optional[timedelta]
    present: Optional[bool]
    raw: str

@dataclasses.dataclass(frozen=True)
class PMSettingsBlock:
    """
    One block of settings (AC/Battery/UPS/System-wide).
    Provides:
      - .values (raw mapping)
      - .get(PMSetting|str)
      - attribute access for keys (e.g. block.displaysleep)
    """
    title: str
    source: Optional[PMPowerSource]
    values: Mapping[str, Union[int, str]]

    def _key_to_str(self, key: Union[PMSetting, str]) -> str:
        return key.value if isinstance(key, PMSetting) else str(key)

    def get(self, key: Union[PMSetting, str], default: Any = None) -> Any:
        return self.values.get(self._key_to_str(key), default)

    def get_int(self, key: Union[PMSetting, str]) -> Optional[int]:
        v = self.get(key, None)
        return v if isinstance(v, int) else None

    def get_str(self, key: Union[PMSetting, str]) -> Optional[str]:
        v = self.get(key, None)
        return v if isinstance(v, str) else None

    def __getattr__(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        raise AttributeError(name)

@dataclasses.dataclass(frozen=True)
class PMSettingsSnapshot:
    """
    Parsed snapshot from `pmset -g` or `pmset -g custom`.
    """
    raw: str
    system_wide: Optional[PMSettingsBlock]
    ac: Optional[PMSettingsBlock]
    battery: Optional[PMSettingsBlock]
    ups: Optional[PMSettingsBlock]

    def for_source(self, source: PMPowerSource) -> Optional[PMSettingsBlock]:
        if source == PMPowerSource.ACPower:
            return self.ac
        if source == PMPowerSource.BatteryPower:
            return self.battery
        if source == PMPowerSource.UPSPower:
            return self.ups
        return None

@dataclasses.dataclass(frozen=True)
class PMRepeatEvent:
    event_type: PMEventType
    weekdays: PMWeekday
    time: time

    def to_pmset_args(self) -> List[str]:
        return [self.event_type.value, self.weekdays.to_pmset(), self.time.strftime("%H:%M:%S")]

@dataclasses.dataclass(frozen=True)
class PMScheduledEvent:
    """
    One-time scheduled power event (from `pmset -g sched`).
    Best-effort parse; raw line always included.
    """
    event_type: str
    when: Optional[datetime]
    owner: Optional[str]
    index: Optional[int]
    raw: str

@dataclasses.dataclass(frozen=True)
class PMScheduleSnapshot:
    """
    Parsed result from `pmset -g sched`.
    """
    raw: str
    one_time: List[PMScheduledEvent]
    repeating: List[PMRepeatEvent]

@dataclasses.dataclass(frozen=True)
class PMSectionedKeyValues:
    """
    Generic "Section: key value" parser result for outputs like cap/ups/adapter/systemstate etc.
    If parsing fails, sections may be empty but raw is always present.
    """
    raw: str
    sections: Mapping[str, Mapping[str, Union[int, str]]]

    def section(self, name: str) -> Mapping[str, Union[int, str]]:
        return self.sections.get(name, {})

def _parse_key_value_lines(text: str) -> Dict[str, Union[int, str]]:
    """
    Parse lines like:
      displaysleep          10
      womp                  1
    into dict. Keeps string if not int.
    """
    out: Dict[str, Union[int, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^(Battery Power|AC Power|UPS Power|System-wide power settings)\s*:?\s*$", line):
            continue
        m = re.match(r"^([A-Za-z0-9_\-\.]+)\s+(.+?)\s*$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if re.fullmatch(r"-?\d+", val):
            out[key] = int(val)
        else:
            out[key] = val
    return out

def _parse_g_blocks(text: str) -> Dict[str, Dict[str, Union[int, str]]]:
    """
    Parse classic block style outputs (pmset -g, -g custom):
      Battery Power:
       ...
      AC Power:
       ...
      System-wide power settings:
       ...
    """
    blocks: Dict[str, Dict[str, Union[int, str]]] = {}
    current_title: Optional[str] = None
    current_lines: List[str] = []

    def flush() -> None:
        nonlocal current_title, current_lines
        if current_title is not None:
            blocks[current_title] = _parse_key_value_lines("\n".join(current_lines))
        current_lines = []

    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^(Battery Power|AC Power|UPS Power)\s*:\s*$", s)
        if m:
            flush()
            current_title = m.group(1)
            continue
        m2 = re.match(r"^(System-wide power settings)\s*:\s*$", s)
        if m2:
            flush()
            current_title = m2.group(1)
            continue

        if current_title is not None:
            current_lines.append(line)

    flush()
    return blocks

def _parse_settings_snapshot(text: str) -> PMSettingsSnapshot:
    raw = text
    blocks = _parse_g_blocks(raw)

    def mk(title: str, source: Optional[PMPowerSource]) -> Optional[PMSettingsBlock]:
        if title not in blocks or not blocks[title]:
            return None
        return PMSettingsBlock(title=title, source=source, values=blocks[title])

    system_wide = mk("System-wide power settings", None)
    ac = mk("AC Power", PMPowerSource.ACPower)
    battery = mk("Battery Power", PMPowerSource.BatteryPower)
    ups = mk("UPS Power", PMPowerSource.UPSPower)

    if not any([system_wide, ac, battery, ups]):
        system_wide = PMSettingsBlock(
            title="(unlabeled)",
            source=None,
            values=_parse_key_value_lines(raw),
        )

    return PMSettingsSnapshot(raw=raw, system_wide=system_wide, ac=ac, battery=battery, ups=ups)

def _parse_batt_output(text: str) -> PMBatteryStatus:
    raw = text
    source = PMPowerSource.Unknown
    percent: Optional[int] = None
    state = PMBatteryState.Unknown
    time_remaining: Optional[timedelta] = None
    present: Optional[bool] = None

    m = re.search(r"Now drawing from '([^']+)'", raw)
    if m:
        source = PMPowerSource.from_pmset_title(m.group(1))

    m = re.search(r"(\d+)%", raw)
    if m:
        try:
            percent = int(m.group(1))
        except ValueError:
            percent = None

    state_candidates = [
        (PMBatteryState.FinishingCharge, r"\bfinishing charge\b"),
        (PMBatteryState.Charging, r"\bcharging\b"),
        (PMBatteryState.Discharging, r"\bdischarging\b"),
        (PMBatteryState.Charged, r"\bcharged\b"),
    ]
    for st, pat in state_candidates:
        if re.search(pat, raw, flags=re.IGNORECASE):
            state = st
            break

    m = re.search(r"\b(\d+):(\d+)\s+remaining\b", raw, flags=re.IGNORECASE)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        time_remaining = timedelta(hours=hh, minutes=mm)

    m = re.search(r"\bpresent:\s*(true|false)\b", raw, flags=re.IGNORECASE)
    if m:
        present = (m.group(1).lower() == "true")

    return PMBatteryStatus(
        source=source,
        percent=percent,
        state=state,
        time_remaining=time_remaining,
        present=present,
        raw=raw,
    )

def _try_parse_datetime_pmset(s: str) -> Optional[datetime]:
    s = s.strip()
    fmts = [
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%m/%d/%Y %H:%M",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None

def _parse_sched_output(text: str) -> PMScheduleSnapshot:
    raw = text
    one_time: List[PMScheduledEvent] = []
    repeating: List[PMRepeatEvent] = []

    one_time_re = re.compile(
        r"^\s*(?:\[(\d+)\])?\s*([A-Za-z]+)\s+at\s+(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?)"
        r"(?:\s+by\s+'([^']+)')?\s*$",
        re.IGNORECASE,
    )

    repeat_re = re.compile(
        r"^\s*([A-Za-z]+)\s+at\s+(\d{1,2}:\d{2}:\d{2})\s+([MTWRFSU]+)\s*$",
        re.IGNORECASE,
    )

    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue

        m = one_time_re.match(s)
        if m:
            idx = int(m.group(1)) if m.group(1) is not None else None
            ev_type = m.group(2)
            when = _try_parse_datetime_pmset(m.group(3))
            owner = m.group(4) if m.group(4) else None
            one_time.append(PMScheduledEvent(event_type=ev_type, when=when, owner=owner, index=idx, raw=line))
            continue

        m2 = repeat_re.match(s)
        if m2:
            ev_type = m2.group(1).lower()
            t = datetime.strptime(m2.group(2), "%H:%M:%S").time()
            wd = PMWeekday.from_pmset(m2.group(3))
            try:
                et = PMEventType(ev_type)
            except ValueError:
                continue
            repeating.append(PMRepeatEvent(event_type=et, weekdays=wd, time=t))
            continue

    return PMScheduleSnapshot(raw=raw, one_time=one_time, repeating=repeating)

def _parse_sectioned_kv(text: str) -> PMSectionedKeyValues:
    """
    Best-effort generic parser for outputs that look like:

      Section Name:
        key  value
        key2 value2
    """
    raw = text
    sections: Dict[str, Dict[str, Union[int, str]]] = {}
    current: Optional[str] = None
    buf: List[str] = []

    header_re = re.compile(r"^([^\s].*?)\s*:\s*$")

    def flush() -> None:
        nonlocal current, buf
        if current is not None:
            kv = _parse_key_value_lines("\n".join(buf))
            sections[current] = kv
        buf = []

    for line in raw.splitlines():
        m = header_re.match(line)
        if m:
            flush()
            current = m.group(1).strip()
            continue
        if current is not None:
            buf.append(line)

    flush()

    if not sections:
        kv = _parse_key_value_lines(raw)
        if kv:
            sections["(unsectioned)"] = kv

    return PMSectionedKeyValues(raw=raw, sections=sections)

class MacPower:
    """
    High-level pmset wrapper with typed convenience layer.

    Features covered:
      - All pmset subcommands in PMSET(1): schedule/repeat/relative/touch/sleepnow/displaysleepnow/boot
        + restoredefaults/noidle/resetdisplayambientparams
      - All pmset -g options in PMSET(1) (via dedicated methods + generic get_raw())
      - Settings can be set via PMSetting or raw string keys.
    """

    def __init__(self, sudo: bool = False, sudo_path: str = "sudo", pmset_path: str = "pmset", shutdown_path: str = "/sbin/shutdown", timeout_sec: Optional[float] = 30.0) -> None:
        _ensure_macos()
        self.sudo = sudo
        self.sudo_path = sudo_path
        self.pmset_path = pmset_path
        self.shutdown_path = shutdown_path
        self.timeout_sec = timeout_sec

    def _cmd(self, args: List[str]) -> List[str]:
        base = [self.pmset_path] + args
        if self.sudo:
            return [self.sudo_path] + base
        return base

    def _sys_cmd(self, args: List[str]) -> List[str]:
        base = args
        if self.sudo:
            return [self.sudo_path] + base
        return base

    def system_run(self, *args: str, check: bool = True) -> CommandResult:
        """
        Run a non-pmset system command with the same timeout/sudo behavior.
        """
        cmd = self._sys_cmd(list(args))
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_sec,
        )
        res = CommandResult(args=cmd, returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
        if check and p.returncode != 0:
            raise MacPowerError(
                f"system command failed (rc={p.returncode}).\n"
                f"CMD: {shlex.join(cmd)}\n"
                f"STDERR:\n{p.stderr.strip()}"
            )
        return res

    def run(self, *args: str, check: bool = True) -> CommandResult:
        cmd = self._cmd(list(args))
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.timeout_sec,
        )
        res = CommandResult(args=cmd, returncode=p.returncode, stdout=p.stdout, stderr=p.stderr)
        if check and p.returncode != 0:
            raise MacPowerError(
                f"pmset command failed (rc={p.returncode}).\n"
                f"CMD: {shlex.join(cmd)}\n"
                f"STDERR:\n{p.stderr.strip()}"
            )
        return res

    def stream(self, *args: str) -> Generator[str, None, None]:
        cmd = self._cmd(list(args))
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
            assert proc.stdout is not None
            for line in proc.stdout:
                yield line.rstrip("\n")

    def get_raw(self, option: Optional[Union[str, PMGetOption]] = None) -> Dict[str, Any]:
        """
        Compatibility-oriented getter:
            pm.get_raw()                  -> pmset -g
            pm.get_raw("cap")             -> pmset -g cap
            pm.get_raw(PMGetOption.Cap)   -> pmset -g cap
        Always includes "raw" and "stderr".
        """
        if option is None:
            r = self.run("-g")
        else:
            opt = option.value if isinstance(option, PMGetOption) else str(option)
            r = self.run("-g", opt)
        return {"raw": r.stdout, "stderr": r.stderr}

    def get_text(self, option: Union[str, PMGetOption]) -> str:
        opt = option.value if isinstance(option, PMGetOption) else str(option)
        return self.run("-g", opt).stdout

    @property
    def power_source(self) -> PMPowerSource:
        """Current power source derived from `pmset -g batt`."""
        return self.battery_status().source

    def battery_status(self) -> PMBatteryStatus:
        r = self.run("-g", "batt")
        return _parse_batt_output(r.stdout)

    def settings_snapshot(self) -> PMSettingsSnapshot:
        r = self.run("-g")
        return _parse_settings_snapshot(r.stdout)

    def live_settings(self) -> PMSettingsSnapshot:
        r = self.run("-g", "live")
        return _parse_settings_snapshot(r.stdout)

    def custom_settings(self) -> PMSettingsSnapshot:
        r = self.run("-g", "custom")
        return _parse_settings_snapshot(r.stdout)

    def available_settings(self, *, use_custom: bool = True) -> Dict[str, List[str]]:
        """
        Discover keys currently reported by pmset on this machine.
        Returns dict with keys: system_wide/ac/battery/ups -> list of setting keys.
        """
        snap = self.custom_settings() if use_custom else self.settings_snapshot()
        out: Dict[str, List[str]] = {}
        if snap.system_wide:
            out["system_wide"] = sorted(snap.system_wide.values.keys())
        if snap.ac:
            out["ac"] = sorted(snap.ac.values.keys())
        if snap.battery:
            out["battery"] = sorted(snap.battery.values.keys())
        if snap.ups:
            out["ups"] = sorted(snap.ups.values.keys())
        return out

    def cap(self) -> PMSectionedKeyValues:
        return _parse_sectioned_kv(self.run("-g", "cap").stdout)

    def sched(self) -> PMScheduleSnapshot:
        return _parse_sched_output(self.run("-g", "sched").stdout)

    def ups_info(self) -> PMSectionedKeyValues:
        return _parse_sectioned_kv(self.run("-g", "ups").stdout)

    def ps(self) -> str:
        return self.run("-g", "ps").stdout

    def batt(self) -> str:
        return self.run("-g", "batt").stdout

    def therm(self) -> str:
        return self.run("-g", "therm").stdout

    def assertions(self) -> str:
        return self.run("-g", "assertions").stdout

    def sysload(self) -> str:
        return self.run("-g", "sysload").stdout

    def adapter(self) -> PMSectionedKeyValues:
        return _parse_sectioned_kv(self.run("-g", "ac").stdout)

    def log(self) -> str:
        return self.run("-g", "log").stdout

    def uuid(self) -> str:
        return self.run("-g", "uuid").stdout

    def history(self) -> str:
        return self.run("-g", "history").stdout

    def history_detailed(self, uuid: str) -> str:
        return self.run("-g", "historydetailed", uuid).stdout

    def powerstate(self, *class_names: str) -> str:
        args = ["-g", "powerstate"]
        args += list(class_names)
        return self.run(*args).stdout

    def stats(self) -> str:
        return self.run("-g", "stats").stdout

    def systemstate(self) -> str:
        return self.run("-g", "systemstate").stdout

    def everything(self) -> str:
        return self.run("-g", "everything").stdout

    def pslog(self) -> Generator[str, None, None]:
        return self.stream("-g", "pslog")

    def rawlog(self) -> Generator[str, None, None]:
        return self.stream("-g", "rawlog")

    def assertionslog(self) -> Generator[str, None, None]:
        return self.stream("-g", "assertionslog")

    def sysloadlog(self) -> Generator[str, None, None]:
        return self.stream("-g", "sysloadlog")

    def uuidlog(self) -> Generator[str, None, None]:
        return self.stream("-g", "uuidlog")

    def thermlog(self) -> Generator[str, None, None]:
        return self.stream("-g", "thermlog")

    def powerstatelog(self, interval_sec: Optional[int] = None, *class_names: str) -> Generator[str, None, None]:
        args = ["-g", "powerstatelog"]
        if interval_sec is not None:
            args += ["-i", str(interval_sec)]
        args += list(class_names)
        return self.stream(*args)

    def set_settings(self, settings: Mapping[Union[PMSetting, str], Union[int, str]], scope: Union[PMScope, Literal["a", "b", "c", "u"]] = PMScope.All) -> None:
        """
        Set one or more pmset settings:
          pm.set_settings({PMSetting.DisplaySleep: 10, PMSetting.Sleep: 30}, scope=PMScope.All)

        For uncommon/unknown keys:
          pm.set_settings({"tcpkeepalive": 1}, scope=PMScope.Battery)
        """
        if isinstance(scope, str):
            scope_enum = PMScope(scope)
        else:
            scope_enum = scope

        args: List[str] = [scope_enum.flag()]
        for k, v in settings.items():
            key_str = k.value if isinstance(k, PMSetting) else str(k)
            args += [key_str, str(v)]
        self.run(*args, check=True)

    def set_setting(self, key: Union[PMSetting, str], value: Union[int, str], scope: Union[PMScope, Literal["a", "b", "c", "u"]] = PMScope.All) -> None:
        self.set_settings({key: value}, scope=scope)

    def set_ups_thresholds(self, haltlevel: Optional[int] = None, haltafter_min: Optional[int] = None, haltremain_min: Optional[int] = None, *, off: bool = False) -> None:
        """
        UPS-specific args (PMSET(1) UPS SPECIFIC ARGUMENTS).
        If off=True, uses -1 to disable the specified threshold(s).
        """
        args: List[str] = [PMScope.UPS.flag()]
        if haltlevel is not None:
            args += ["haltlevel", "-1" if off else str(haltlevel)]
        if haltafter_min is not None:
            args += ["haltafter", "-1" if off else str(haltafter_min)]
        if haltremain_min is not None:
            args += ["haltremain", "-1" if off else str(haltremain_min)]
        if len(args) == 1:
            raise ValueError("At least one of haltlevel/haltafter_min/haltremain_min must be provided.")
        self.run(*args, check=True)

    def schedule(self, event_type: Union[PMEventType, str], when: Union[str, datetime], owner: Optional[str] = None) -> None:
        """
        One-time schedule:
          pmset schedule <type> "MM/dd/yy HH:mm:ss" [owner]
        Note: subprocess argument handling means quoting is not required here.
        """
        if isinstance(event_type, PMEventType):
            event_str = event_type.value
        else:
            event_str = str(event_type)

        if isinstance(when, datetime):
            when_str = when.strftime("%m/%d/%y %H:%M:%S")
        else:
            when_str = when

        args = ["schedule", event_str, when_str]
        if owner:
            args.append(owner)
        self.run(*args, check=True)

    def schedule_cancel(self, event_type: Union[PMEventType, str]) -> None:
        ev = event_type.value if isinstance(event_type, PMEventType) else str(event_type)
        self.run("schedule", "cancel", ev, check=True)

    def schedule_cancelall(self) -> None:
        self.run("schedule", "cancelall", check=True)

    def repeat_cancel(self) -> None:
        self.run("repeat", "cancel", check=True)

    def repeat(self, *events: PMRepeatEvent) -> None:
        """
        Typed repeating events (1 or 2 events).
          pm.repeat(PMRepeatEvent(PMEventType.Shutdown, PMWeekday.from_pmset("TWRFS"), time(23,0)))

        For paired:
          pm.repeat(PMRepeatEvent(PMEventType.WakeOrPowerOn, PMWeekday.M, time(9,0)),
                    PMRepeatEvent(PMEventType.Sleep, PMWeekday.all(), time(20,0)))
        """
        if not (1 <= len(events) <= 2):
            raise ValueError("repeat accepts 1 or 2 events.")
        args = ["repeat"]
        for ev in events:
            args += ev.to_pmset_args()
        self.run(*args, check=True)

    def relative(self, kind: Union[PMRelativeKind, Literal["wake", "poweron"]], seconds: int) -> None:
        k = kind.value if isinstance(kind, PMRelativeKind) else str(kind)
        self.run("relative", k, str(int(seconds)), check=True)

    def touch(self) -> None:
        self.run("touch", check=True)

    def sleepnow(self) -> None:
        self.run("sleepnow", check=True)

    def displaysleepnow(self) -> None:
        self.run("displaysleepnow", check=True)

    def hibernatenow(self, *, fallback_set_mode: bool = False, hibernatemode: int = 25, scope: Union[PMScope, Literal["a", "b", "c", "u"]] = PMScope.All) -> None:
        """
        Attempt to hibernate immediately.

        Strategy:
            1) Try `pmset hibernateforce` (works on some macOS versions/configurations; usually requires sudo).
            2) If that fails and fallback_set_mode=True:
               set hibernatemode=<hibernatemode> (default 25) then `pmset sleepnow`.

        IMPORTANT:
            - The fallback path changes `hibernatemode` persistently. It cannot be restored after sleep/hibernate
              because this process will be suspended/terminated.
            - For reliable behavior, run with sudo (--sudo) and understand your platform's supported modes.
        """
        r = self.run("hibernateforce", check=False)
        if r.returncode == 0:
            return
        if not fallback_set_mode:
            raise MacPowerError(
                "pmset hibernateforce failed on this system.\n"
                    f"CMD: {shlex.join(r.args)}\n"
                    f"STDERR:\n{(r.stderr or '').strip()}\n"
                    "Enable fallback_set_mode=True to try setting hibernatemode=25 then sleepnow."
            )
        self.set_setting(PMSetting.HibernateMode, int(hibernatemode), scope=scope)
        self.sleepnow()

    def shutdownnow(self) -> None:
        """
        Power off the machine immediately (shutdown -h now).
        Typically requires sudo.
        """
        self.system_run(self.shutdown_path, "-h", "now", check=True)

    def restartnow(self) -> None:
        """
        Restart the machine immediately (shutdown -r now).
        Typically requires sudo.
        """
        self.system_run(self.shutdown_path, "-r", "now", check=True)

    def boot(self) -> None:
        self.run("boot", check=True)

    def restoredefaults(self) -> None:
        self.run("restoredefaults", check=True)

    def resetdisplayambientparams(self) -> None:
        self.run("resetdisplayambientparams", check=True)

    def noidle(self) -> Generator[str, None, None]:
        """
        pmset noidle (deprecated in favor of caffeinate(8) per PMSET(1)).
        This blocks while active; stop by terminating the process (Ctrl-C).
        Some systems produce no stdout; generator is kept for symmetry.
        """
        return self.stream("noidle")

    def set_dim(self, value: Union[int, str], scope: Union[PMScope, Literal["a", "b", "c", "u"]] = PMScope.All) -> None:
        """
        Legacy 'dim' argument (deprecated in favor of displaysleep).
        """
        self.set_setting("dim", value, scope=scope)

    def set_spindown(self, value: Union[int, str], scope: Union[PMScope, Literal["a", "b", "c", "u"]] = PMScope.All) -> None:
        """
        Legacy 'spindown' argument (deprecated in favor of disksleep).
        """
        self.set_setting("spindown", value, scope=scope)
