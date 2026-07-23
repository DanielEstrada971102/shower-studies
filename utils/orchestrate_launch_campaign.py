#!/usr/bin/env python3

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def run_cmd(
    cmd: List[str],
    cwd: Path,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        check=check,
        text=True,
        capture_output=capture,
    )


def git_output(repo: Path, *args: str) -> str:
    cp = run_cmd(["git", *args], cwd=repo, check=True, capture=True)
    return cp.stdout.strip()


def detect_repo_root(repo_hint: Path) -> Path:
    try:
        top = git_output(repo_hint, "rev-parse", "--show-toplevel")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Could not detect git repository root.") from exc
    return Path(top)


def get_initial_ref(repo: Path) -> Tuple[Optional[str], str]:
    branch: Optional[str]
    try:
        branch = git_output(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
        if not branch:
            branch = None
    except subprocess.CalledProcessError:
        branch = None
    commit = git_output(repo, "rev-parse", "HEAD")
    return branch, commit


def ensure_commit_exists(repo: Path, commit: str) -> None:
    run_cmd(["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=repo, check=True, capture=True)

def short_commit(repo: Path) -> str:
    return git_output(repo, "rev-parse", "--short", "HEAD")

def checkout_detached(repo: Path, commit: str) -> None:
    run_cmd(["git", "checkout", "--detach", commit], cwd=repo, check=True, capture=True)


def restore_checkout(repo: Path, branch: Optional[str], commit: str) -> None:
    if branch:
        run_cmd(["git", "checkout", branch], cwd=repo, check=True, capture=True)
    else:
        run_cmd(["git", "checkout", "--detach", commit], cwd=repo, check=True, capture=True)


def shell_double_quote_escape(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace("$", "\\$")
    escaped = escaped.replace("`", "\\`")
    return escaped


def format_launcher_value(var_name: str, value: Any) -> List[str]:
    if var_name == "INPUTS":
        if isinstance(value, str):
            items = [value]
        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            items = value
        else:
            raise RuntimeError("INPUTS override must be a string or a list of strings.")

        block = ["INPUTS=("]
        for item in items:
            escaped = shell_double_quote_escape(item)
            block.append(f'    "{escaped}"')
        block.append(")")
        return block

    if isinstance(value, bool):
        rendered = "true" if value else "false"
    elif isinstance(value, (int, float)):
        rendered = str(value)
    elif isinstance(value, str):
        escaped = shell_double_quote_escape(value)
        rendered = f'"{escaped}"'
    else:
        raise RuntimeError(
            f"Unsupported value type for {var_name}: {type(value).__name__}"
        )

    return [f"{var_name}={rendered} # managed by orchestrate_launch_campaign.py"]


def update_launcher_vars(launcher_text: str, updates: Dict[str, Any]) -> str:
    lines = launcher_text.splitlines()

    for var_name, value in updates.items():
        if var_name == "INPUTS":
            start_idx = next(
                (i for i, line in enumerate(lines) if line.lstrip().startswith("INPUTS=(")),
                None,
            )
            if start_idx is None:
                raise RuntimeError("Could not find INPUTS block in launcher script.")

            end_idx = None
            for j in range(start_idx, len(lines)):
                if lines[j].strip() == ")":
                    end_idx = j
                    break
            if end_idx is None:
                raise RuntimeError("Could not find end of INPUTS block in launcher script.")

            replacement_block = format_launcher_value(var_name, value)
            lines[start_idx : end_idx + 1] = replacement_block
            continue

        target_prefix = f"{var_name}="
        target_idx = next(
            (i for i, line in enumerate(lines) if line.lstrip().startswith(target_prefix)),
            None,
        )
        if target_idx is None:
            raise RuntimeError(f"Could not find {var_name}= in launcher script.")

        replacement_line = format_launcher_value(var_name, value)[0]
        lines[target_idx] = replacement_line

    return "\n".join(lines) + "\n"

def sanitize_name(raw: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", raw)

def write_report_line(report_file: Path, item: Dict[str, Any]) -> None:
    import json
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with report_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, sort_keys=True) + "\n")

import time


def parse_run_directory(stdout: str) -> Optional[Path]:
    match = re.search(r"^Run directory:\s*(.+)$", stdout, re.MULTILINE)
    if not match:
        return None
    return Path(match.group(1).strip())


def next_retry_log_index(run_log_dir: Path, run_id: str) -> int:
    highest_index = -1
    for candidate in run_log_dir.glob(f"stdout_run_{run_id}_retry_*.log"):
        match = re.match(rf"stdout_run_{re.escape(run_id)}_retry_(\d+)\.log$", candidate.name)
        if match:
            highest_index = max(highest_index, int(match.group(1)))
    return highest_index + 1

def parse_job_ids(stdout: str) -> List[str]:
    """Extract Slurm job IDs from 'Submitted batch job XXXXXX' lines."""
    return re.findall(r"Submitted batch job (\d+)", stdout)


def wait_until_jobs_running(
    job_ids: List[str],
    poll_interval: int = 15,
    timeout: int = 600,
) -> bool:
    """
    Poll squeue until all jobs have left the PENDING state (i.e. are RUNNING
    or have already finished/failed). Returns True if all started, False on timeout.
    """
    if not job_ids:
        return True

    ids_csv = ",".join(job_ids)
    deadline = time.time() + timeout
    print(f"  Waiting for jobs {ids_csv} to start...")

    while time.time() < deadline:
        try:
            cp = subprocess.run(
                ["squeue", "-j", ids_csv, "-h", "-o", "%i %t"],
                text=True, capture_output=True, check=False
            )
            # squeue returns only *still-queued* jobs; missing IDs have already ended
            lines = cp.stdout.strip().splitlines()
            pending = [l for l in lines if l.split()[1] == "PD"]

            if not pending:
                print(f"  All jobs running/done.")
                return True

            print(f"  {len(pending)}/{len(job_ids)} still pending, retrying in {poll_interval}s...")
        except Exception as exc:
            eprint(f"  squeue error: {exc}")

        time.sleep(poll_interval)

    eprint(f"  Timeout waiting for jobs {ids_csv} to start.")
    return False


def main() -> int:
    DRY_RUN = False
    RETRY = False
    COMMAND = "dtpr dump-events"
    OUTDIR = "/lustrefs/L1T/dtntuples/MinBias_200PU/v1p2-proc"
    MAXEVENTS = -1
    # =========================
    # USER CONFIG - EDIT THIS
    # =========================
    vars = {
        "INPUTS": [
            "/lustrefs/L1T/dtntuples/MinBias_200PU/v1p2",
        ],
        "CHUNK_SIZE": 84,
        "COMMAND": COMMAND,
    }
    CAMPAIGN = {
        # "old_sample$A": {
        #     "commit": "f64dc8617b2dea85dac69ac281fdc0c5d6bbb8f5",
        #     "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _old_sample_A__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/A.yaml",
        #     "vars": {
        #         "INPUTS": [
        #             "/lustrefs/L1T/dtntuples/ZprimeToMuMu_M-6000_PU200/v1/",
        #         ],
        #         "CHUNK_SIZE": 21,
        #         "COMMAND": COMMAND,
        #     },
        # },
        "sample$B": {
            "commit": "f64dc8617b2dea85dac69ac281fdc0c5d6bbb8f5",
            "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _B__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/B.yaml",
            "vars": vars
        },
        "$B+fix_tps_angle$C": {
            "commit": "640e6a2a4a526abb63793f389237c9505cb95504",
            "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _C__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/C.yaml",
            "vars": vars
        },
        # "$C+using_jpshowers$D":{
        #     "commit": "cf913ffa1ce8de16a7b5d9d209683cb3be3c3f5e",
        #     "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _D__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/D.yaml",
        #     "vars": vars
        # },
        # "$D+dnn$E":{
        #     "commit": "cf913ffa1ce8de16a7b5d9d209683cb3be3c3f5e",
        #     "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _E__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/E.yaml",
        #     "vars": vars
        # },
        # "$E+fix_rs$F":{
        #     "commit": "439ec54efeb1c0c9b61a61223ae07889ab4f1939",
        #     "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _F__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/E.yaml",
        #     "vars": vars
        # },
        "$C+fix_rs$G":{
            "commit": "439ec54efeb1c0c9b61a61223ae07889ab4f1939",
            "args": f"--maxevents={MAXEVENTS} -o {OUTDIR}/roots/ --tag _G__TASK_ID__ -cf /nfs/fanae/user/destrada/Public/shower-studies/utils/yamls/G.yaml",
            "vars": vars
        },
    }

    repo = detect_repo_root(Path("."))
    launcher_path = Path(repo, "./utils/new_launch_cmd_on_chunks.sh")
    report_dir = Path(OUTDIR, "./campaign-reports")

    if not launcher_path.exists():
        eprint(f"Launcher not found: {launcher_path}")
        return 2

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"campaign_{timestamp}.json"

    initial_branch, initial_commit = get_initial_ref(repo)
    campaign_failed = False

    print(f"Repo root: {repo}")
    print(f"Launcher: {launcher_path}")
    print(f"Report: {report_file}")
    print(f"Initial ref: {initial_branch or initial_commit}")

    try:
        for profile_name, profile_cfg in CAMPAIGN.items():
            if not isinstance(profile_cfg, dict):
                eprint(f"[ERROR] profile={profile_name}: config must be a dictionary")
                campaign_failed = True
                continue

            commit = profile_cfg.get("commit")
            profile_args = profile_cfg.get("args")
            var_overrides = profile_cfg.get("vars", {})
            profile_log_root = report_dir / "logs" / sanitize_name(profile_name)
            profile_log_root.mkdir(parents=True, exist_ok=True)
            var_overrides["LOG_DIR"] = profile_log_root.as_posix()

            if not isinstance(commit, str) or not commit.strip():
                eprint(f"[ERROR] profile={profile_name}: missing/invalid 'commit'")
                campaign_failed = True
                continue
            if not isinstance(profile_args, str) or not profile_args.strip():
                eprint(f"[ERROR] profile={profile_name}: missing/invalid 'args'")
                campaign_failed = True
                continue
            if not isinstance(var_overrides, dict):
                eprint(f"[ERROR] profile={profile_name}: 'vars' must be a dictionary")
                campaign_failed = True
                continue

            ensure_commit_exists(repo, commit)
            checkout_detached(repo, commit)
            current_short = short_commit(repo)
            print(f"\n=== Profile {profile_name} | Commit {commit} ({current_short}) ===")
            print("VERSION: " , git_output(repo, "log", "-1", "--oneline"))

            launcher_original = launcher_path.read_text(encoding="utf-8")

            started = datetime.now().isoformat(timespec="seconds")
            status = "ok"
            returncode = 0

            print(f"[RUN] commit={current_short} profile={profile_name}")

            try:
                updates = {"ARGS": profile_args}
                updates.update(var_overrides)
                patched = update_launcher_vars(launcher_original, updates)
                launcher_path.write_text(patched, encoding="utf-8")

                launch_cmd = ["bash", str(launcher_path), "--mode", "slurm"]
                if DRY_RUN:
                    launch_cmd.append("--dry-run")
                if RETRY:
                    launch_cmd.append("--retry")

                cp = run_cmd(
                    launch_cmd,
                    cwd=repo,
                    check=False,
                    capture=True,
                )
                returncode = cp.returncode
                run_log_dir = parse_run_directory(cp.stdout or "")
                if run_log_dir is None:
                    raise RuntimeError("Could not parse run directory from launcher output.")

                run_log_dir.mkdir(parents=True, exist_ok=True)
                run_id = run_log_dir.name.removeprefix("run_")

                if RETRY:
                    retry_index = next_retry_log_index(run_log_dir, run_id)
                    stdout_log = run_log_dir / f"stdout_run_{run_id}_retry_{retry_index}.log"
                    stderr_log = run_log_dir / f"stderr_run_{run_id}_retry_{retry_index}.log"
                else:
                    stdout_log = run_log_dir / f"stdout_run_{run_id}.log"
                    stderr_log = run_log_dir / f"stderr_run_{run_id}.log"

                stdout_log.write_text(cp.stdout or "", encoding="utf-8")
                stderr_log.write_text(cp.stderr or "", encoding="utf-8")

                if cp.returncode != 0:
                    status = "failed"
                    campaign_failed = True
                    eprint(
                        f"[FAIL] commit={current_short} profile={profile_name} returncode={cp.returncode}"
                    )
                else:
                    job_ids = parse_job_ids(cp.stdout or "")
                    print(f"[OK] Submitted {len(job_ids)} jobs: {', '.join(job_ids)}")

                    if not DRY_RUN:
                        started_ok = wait_until_jobs_running(job_ids)
                        if not started_ok:
                            eprint(f"[WARN] Timeout reached — proceeding anyway, jobs may share code version")


            except Exception as exc:  # pylint: disable=broad-except
                status = "error"
                returncode = 99
                campaign_failed = True
                eprint(
                    f"[ERROR] commit={current_short} profile={profile_name}: {exc}"
                )
            finally:
                # Restore launcher content so checkout to next commit is clean.
                launcher_path.write_text(launcher_original, encoding="utf-8")

            ended = datetime.now().isoformat(timespec="seconds")
            write_report_line(
                report_file,
                {
                    "commit": commit,
                    "commit_short": current_short,
                    "profile": profile_name,
                    "mode": "slurm",
                    "args": profile_args,
                    "vars": var_overrides,
                    "launcher_run_dir": str(run_log_dir.resolve()),
                    "launcher_run_id": run_id,
                    "status": status,
                    "returncode": returncode,
                    "started": started,
                    "ended": ended,
                    "stdout_log": str(stdout_log.resolve()),
                    "stderr_log": str(stderr_log.resolve()),
                },
            )

        return 1 if campaign_failed else 0

    finally:
        try:
            restore_checkout(repo, initial_branch, initial_commit)
            print(f"\nRestored checkout to: {initial_branch or initial_commit}")
        except Exception as exc:  # pylint: disable=broad-except
            eprint(f"Failed to restore original checkout: {exc}")


if __name__ == "__main__":
    raise SystemExit(main())
