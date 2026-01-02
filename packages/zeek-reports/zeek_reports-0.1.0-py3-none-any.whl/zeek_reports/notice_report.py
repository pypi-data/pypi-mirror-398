import argparse
import csv
import datetime as dt
import gzip
import ipaddress
import json
import os
import statistics
from collections import Counter, defaultdict


SPECIAL_NOTICES = [
    "DNS_AXFR::Attempt",
    "SSH::Ebury_Victim",
    "RDP::PasswordGuessing",
    "Weird::ActivitySYN_after_partial",
]

NOTE_SEVERITY_OVERRIDES = {
    "SSH::Ebury_Victim": "critical",
    "RDP::PasswordGuessing": "high",
    "DNS_AXFR::Attempt": "high",
    "Weird::ActivitySYN_after_partial": "medium",
}

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def parse_separator(line):
    # Example: "#separator \\x09"
    sep_raw = line.split(None, 1)[1].strip()
    return bytes(sep_raw, "utf-8").decode("unicode_escape")


def read_notice_file(path):
    opener = gzip.open if path.endswith(".gz") else open
    fields = None
    sep = "\t"
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith("#separator"):
                sep = parse_separator(line)
                continue
            if line.startswith("#fields"):
                fields = line.split(sep)[1:]
                continue
            if line.startswith("#"):
                continue
            if not fields:
                continue
            values = line.split(sep)
            if len(values) != len(fields):
                continue
            yield dict(zip(fields, values))


def load_internal_networks(path):
    networks = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cidr = line.split()[0]
            try:
                networks.append(ipaddress.ip_network(cidr))
            except ValueError:
                continue
    return networks


def ip_role(ip, networks):
    if not ip or ip in ("-", "(empty)"):
        return "unknown"
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "unknown"
    for net in networks:
        if addr in net:
            return "internal"
    return "external"


def iter_dates(start_date, end_date):
    current = start_date
    while current < end_date:
        yield current
        current += dt.timedelta(days=1)


def notice_files_for_range(log_root, start_date, end_date):
    files = []
    today = dt.date.today()
    for day in iter_dates(start_date, end_date):
        day_dir = os.path.join(log_root, day.isoformat())
        if os.path.isdir(day_dir):
            for name in os.listdir(day_dir):
                if not name.startswith("notice."):
                    continue
                if not (name.endswith(".log") or name.endswith(".log.gz")):
                    continue
                files.append(os.path.join(day_dir, name))
        if day == today:
            current_path = os.path.join(log_root, "current", "notice.log")
            if os.path.isfile(current_path):
                files.append(current_path)
    return sorted(set(files))


def parse_ts(ts_value):
    if not ts_value or ts_value in ("-", "(empty)"):
        return None
    try:
        ts = float(ts_value)
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(ts)


def percentile(values, p):
    if not values:
        return 0
    if p <= 0:
        return values[0]
    if p >= 1:
        return values[-1]
    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def note_severity(note):
    if note in NOTE_SEVERITY_OVERRIDES:
        return NOTE_SEVERITY_OVERRIDES[note]
    if not note or note in ("-", "(empty)"):
        return "info"
    lowered = note.lower()
    if "ebury" in lowered or "compromise" in lowered:
        return "critical"
    if "passwordguess" in lowered or "bruteforce" in lowered or "axfr" in lowered:
        return "high"
    if "scan" in lowered or lowered.startswith("weird::"):
        return "medium"
    return "info"


def format_top(counter, networks, limit=10):
    lines = []
    for ip, count in counter.most_common(limit):
        role = ip_role(ip, networks)
        lines.append(f"{ip} ({role}) - {count}")
    return lines


def report_range(start_dt, end_dt, log_root, networks, details=True):
    totals = Counter()
    note_counts = Counter()
    src_counts = Counter()
    dst_counts = Counter()
    src_role_counts = Counter()
    dst_role_counts = Counter()
    ext_to_int_src = Counter()
    ext_to_int_dst = Counter()
    int_to_ext_src = Counter()
    int_to_ext_dst = Counter()
    hourly_counts = Counter()
    daily_counts = Counter()
    severity_counts = Counter()
    missing_src = 0
    missing_dst = 0
    note_src_counts = defaultdict(Counter) if details else None
    note_dst_counts = defaultdict(Counter) if details else None
    note_samples = defaultdict(list) if details else None
    ext_src_unique_int_dsts = defaultdict(set) if details else None
    ext_src_unique_ports = defaultdict(set) if details else None
    int_dst_unique_ext_srcs = defaultdict(set) if details else None

    files = notice_files_for_range(log_root, start_dt.date(), end_dt.date())
    for path in files:
        for record in read_notice_file(path):
            event_dt = parse_ts(record.get("ts"))
            if not event_dt or not (start_dt <= event_dt < end_dt):
                continue
            totals["notices"] += 1
            hour_bucket = event_dt.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour_bucket.isoformat(sep=" ")] += 1
            daily_counts[event_dt.date().isoformat()] += 1
            note = record.get("note", "-")
            note_counts[note] += 1
            severity_counts[note_severity(note)] += 1
            src = record.get("id.orig_h", "-")
            dst = record.get("id.resp_h", "-")
            if src in ("-", "(empty)"):
                missing_src += 1
            else:
                src_counts[src] += 1
            if dst in ("-", "(empty)"):
                missing_dst += 1
            else:
                dst_counts[dst] += 1
            src_role = ip_role(src, networks)
            dst_role = ip_role(dst, networks)
            src_role_counts[src_role] += 1
            dst_role_counts[dst_role] += 1

            if src_role == "external" and dst_role == "internal":
                if src not in ("-", "(empty)"):
                    ext_to_int_src[src] += 1
                if dst not in ("-", "(empty)"):
                    ext_to_int_dst[dst] += 1
                if details:
                    if src not in ("-", "(empty)") and dst not in ("-", "(empty)"):
                        ext_src_unique_int_dsts[src].add(dst)
                        int_dst_unique_ext_srcs[dst].add(src)
                    resp_port = record.get("id.resp_p", "-")
                    if src not in ("-", "(empty)") and resp_port not in ("-", "(empty)"):
                        ext_src_unique_ports[src].add(resp_port)
            if src_role == "internal" and dst_role == "external":
                if src not in ("-", "(empty)"):
                    int_to_ext_src[src] += 1
                if dst not in ("-", "(empty)"):
                    int_to_ext_dst[dst] += 1

            if details:
                sev = note_severity(note)
                if note in SPECIAL_NOTICES or SEVERITY_ORDER.get(sev, 0) >= 2:
                    if src not in ("-", "(empty)"):
                        note_src_counts[note][src] += 1
                    if dst not in ("-", "(empty)"):
                        note_dst_counts[note][dst] += 1
                if (
                    note in SPECIAL_NOTICES
                    or SEVERITY_ORDER.get(sev, 0) >= 3
                ) and len(note_samples[note]) < 5:
                    note_samples[note].append(
                        {
                            "ts": event_dt.isoformat(sep=" "),
                            "uid": record.get("uid", "-"),
                            "note": note,
                            "proto": record.get("proto", "-"),
                            "id.orig_h": src,
                            "id.orig_p": record.get("id.orig_p", "-"),
                            "id.resp_h": dst,
                            "id.resp_p": record.get("id.resp_p", "-"),
                            "msg": record.get("msg", "-"),
                            "sub": record.get("sub", "-"),
                        }
                    )

    return {
        "totals": totals,
        "note_counts": note_counts,
        "src_counts": src_counts,
        "dst_counts": dst_counts,
        "src_role_counts": src_role_counts,
        "dst_role_counts": dst_role_counts,
        "hourly_counts": hourly_counts,
        "daily_counts": daily_counts,
        "severity_counts": severity_counts,
        "ext_to_int_src": ext_to_int_src,
        "ext_to_int_dst": ext_to_int_dst,
        "int_to_ext_src": int_to_ext_src,
        "int_to_ext_dst": int_to_ext_dst,
        "missing_src": missing_src,
        "missing_dst": missing_dst,
        "files": files,
        "note_src_counts": note_src_counts,
        "note_dst_counts": note_dst_counts,
        "note_samples": note_samples,
        "ext_src_unique_int_dsts": ext_src_unique_int_dsts,
        "ext_src_unique_ports": ext_src_unique_ports,
        "int_dst_unique_ext_srcs": int_dst_unique_ext_srcs,
    }


def counter_to_list(counter, networks=None, limit=None):
    items = counter.most_common(limit) if limit else counter.most_common()
    output = []
    for key, count in items:
        entry = {"key": key, "count": count}
        if networks is not None:
            entry["role"] = ip_role(key, networks)
        output.append(entry)
    return output


def summarize_baseline(period, start_dt, end_dt):
    baseline_end = start_dt
    if period == "daily":
        baseline_start = baseline_end - dt.timedelta(days=7)
    elif period == "weekly":
        baseline_start = baseline_end - dt.timedelta(days=28)
    elif period == "monthly":
        year = baseline_end.year
        month = baseline_end.month
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        baseline_start = dt.datetime(year, month, 1)
    else:
        raise ValueError(f"Unknown period: {period}")
    return baseline_start, baseline_end


def rate_per_day(count, start_dt, end_dt):
    days = max(int((end_dt - start_dt).total_seconds() // 86400), 1)
    return count / days


def add_finding(findings, severity, title, description, evidence=None):
    entry = {
        "severity": severity,
        "title": title,
        "description": description,
    }
    if evidence:
        entry["evidence"] = evidence
    findings.append(entry)


def detect_findings(period, start_dt, end_dt, data, networks, baseline):
    findings = []
    base_thresholds = {"daily": 20, "weekly": 50, "monthly": 100}
    base_unique_dst_thresholds = {"daily": 10, "weekly": 25, "monthly": 50}
    base_unique_port_thresholds = {"daily": 10, "weekly": 25, "monthly": 50}
    base_targeted_host_thresholds = {"daily": 20, "weekly": 50, "monthly": 100}

    critical = [
        n for n, c in data["note_counts"].items()
        if note_severity(n) == "critical" and c > 0
    ]
    for note in sorted(critical):
        count = data["note_counts"][note]
        top_src = (
            data["note_src_counts"].get(note, Counter()).most_common(5)
            if data["note_src_counts"]
            else []
        )
        top_dst = (
            data["note_dst_counts"].get(note, Counter()).most_common(5)
            if data["note_dst_counts"]
            else []
        )
        samples = data["note_samples"].get(note, []) if data.get("note_samples") else []
        add_finding(
            findings,
            "critical",
            f"{note} present",
            f"{count} events; investigate immediately.",
            evidence={
                "count": count,
                "top_sources": top_src,
                "top_destinations": top_dst,
                "sample_events": samples,
            },
        )

    for note, count in data["note_counts"].items():
        sev = note_severity(note)
        if sev == "critical":
            continue
        if SEVERITY_ORDER.get(sev, 0) < 3 or count <= 0:
            continue
        baseline_count = baseline["note_counts"].get(note, 0) if baseline else 0
        detail = f"{count} events."
        if baseline:
            current_rate = rate_per_day(count, start_dt, end_dt)
            baseline_rate = rate_per_day(
                baseline_count, baseline["range"]["start_dt"], baseline["range"]["end_dt"]
            )
            if baseline_rate == 0 and count > 0:
                detail += " New vs baseline."
            elif baseline_rate > 0:
                ratio = current_rate / baseline_rate
                if ratio >= 3:
                    detail += f" ~{ratio:.1f}x baseline rate."
        top_src = (
            data["note_src_counts"].get(note, Counter()).most_common(5)
            if data.get("note_src_counts")
            else []
        )
        top_dst = (
            data["note_dst_counts"].get(note, Counter()).most_common(5)
            if data.get("note_dst_counts")
            else []
        )
        samples = data["note_samples"].get(note, []) if data.get("note_samples") else []
        add_finding(
            findings,
            "high",
            f"{note} activity",
            detail,
            evidence={
                "count": count,
                "top_sources": top_src,
                "top_destinations": top_dst,
                "sample_events": samples,
            },
        )

    ext_counts = data["ext_to_int_src"]
    if ext_counts:
        values = sorted(ext_counts.values())
        median = statistics.median(values) if values else 0
        p95 = percentile(values, 0.95) if values else 0
        threshold = max(base_thresholds.get(period, 50), int(p95), int(median * 10))
        top_ext = ext_counts.most_common(10)
        offenders = [(ip, c) for ip, c in top_ext if c >= threshold]
        if offenders:
            evidence = []
            for ip, c in offenders:
                unique_dsts = (
                    len(data["ext_src_unique_int_dsts"].get(ip, set()))
                    if data["ext_src_unique_int_dsts"]
                    else 0
                )
                unique_ports = (
                    len(data["ext_src_unique_ports"].get(ip, set()))
                    if data["ext_src_unique_ports"]
                    else 0
                )
                new = (
                    baseline
                    and ip not in baseline["ext_to_int_src"]
                    and baseline["totals"]["notices"] > 0
                )
                evidence.append(
                    {
                        "ip": ip,
                        "count": c,
                        "unique_internal_dsts": unique_dsts,
                        "unique_ports": unique_ports,
                        "new_vs_baseline": bool(new),
                    }
                )
            add_finding(
                findings,
                "high",
                "High-volume external activity to internal hosts",
                f"{len(offenders)} external source(s) exceed threshold ({threshold}).",
                evidence={"offenders": evidence},
            )

        dst_threshold = base_unique_dst_thresholds.get(period, 25)
        port_threshold = base_unique_port_thresholds.get(period, 25)
        scan_like = []
        if data["ext_src_unique_int_dsts"] and data["ext_src_unique_ports"]:
            for ip, count in ext_counts.most_common(50):
                unique_dsts = len(data["ext_src_unique_int_dsts"].get(ip, set()))
                unique_ports = len(data["ext_src_unique_ports"].get(ip, set()))
                if unique_dsts >= dst_threshold or unique_ports >= port_threshold:
                    scan_like.append(
                        {
                            "ip": ip,
                            "count": count,
                            "unique_internal_dsts": unique_dsts,
                            "unique_ports": unique_ports,
                        }
                    )
        if scan_like:
            add_finding(
                findings,
                "medium",
                "External scan-like behavior",
                f"{len(scan_like)} external source(s) contacted many internal targets/ports.",
                evidence={
                    "sources": scan_like[:10],
                    "thresholds": {
                        "unique_dsts": dst_threshold,
                        "unique_ports": port_threshold,
                    },
                },
            )

    targeted_hosts = data["ext_to_int_dst"]
    if targeted_hosts and data["int_dst_unique_ext_srcs"]:
        threshold = base_targeted_host_thresholds.get(period, 50)
        hot = []
        for dst, count in targeted_hosts.most_common(20):
            unique_sources = len(data["int_dst_unique_ext_srcs"].get(dst, set()))
            if count >= threshold or unique_sources >= 10:
                hot.append(
                    {
                        "ip": dst,
                        "count": count,
                        "unique_external_sources": unique_sources,
                    }
                )
        if hot:
            add_finding(
                findings,
                "high",
                "Internal host(s) heavily targeted from external sources",
                f"{len(hot)} internal destination(s) exceeded thresholds.",
                evidence={"targets": hot},
            )

    hourly = data["hourly_counts"]
    if hourly:
        hour_values = sorted(hourly.values())
        median = statistics.median(hour_values) if hour_values else 0
        top_hour, top_count = hourly.most_common(1)[0]
        if median > 0 and top_count >= max(20, int(median * 5)):
            add_finding(
                findings,
                "medium",
                "Notice burst observed",
                f"Peak hour {top_hour} had {top_count} notices (median {median}).",
            )

    return findings


def build_report_data(
    period,
    start_dt,
    end_dt,
    data,
    networks,
    daily=False,
    baseline_stats=None,
    baseline_range=None,
):
    report = {
        "period": period,
        "range": {
            "start": start_dt.isoformat(sep=" "),
            "end": end_dt.isoformat(sep=" "),
        },
        "notice_files": data["files"],
        "totals": {"notices": data["totals"]["notices"]},
        "targeted_notices": {
            notice: data["note_counts"].get(notice, 0) for notice in SPECIAL_NOTICES
        },
        "top_notice_types": counter_to_list(data["note_counts"], limit=10),
        "top_source_ips": counter_to_list(data["src_counts"], networks=networks, limit=10),
        "top_destination_ips": counter_to_list(
            data["dst_counts"], networks=networks, limit=10
        ),
        "source_roles": counter_to_list(data["src_role_counts"]),
        "destination_roles": counter_to_list(data["dst_role_counts"]),
        "missing_fields": {
            "missing_src": data["missing_src"],
            "missing_dst": data["missing_dst"],
        },
    }

    if daily:
        report["daily_investigation_focus"] = {
            "external_to_internal_sources": counter_to_list(
                data["ext_to_int_src"], networks=networks, limit=10
            ),
            "external_to_internal_destinations": counter_to_list(
                data["ext_to_int_dst"], networks=networks, limit=10
            ),
            "internal_to_external_sources": counter_to_list(
                data["int_to_ext_src"], networks=networks, limit=10
            ),
            "internal_to_external_destinations": counter_to_list(
                data["int_to_ext_dst"], networks=networks, limit=10
            ),
        }

    baseline = None
    if baseline_stats and baseline_range:
        baseline_start_dt, baseline_end_dt = baseline_range
        baseline = {
            "range": {
                "start": baseline_start_dt.isoformat(sep=" "),
                "end": baseline_end_dt.isoformat(sep=" "),
            },
            "range_days": max(int((baseline_end_dt - baseline_start_dt).total_seconds() // 86400), 1),
            "totals": {"notices": baseline_stats["totals"]["notices"]},
            "targeted_notices": {
                notice: baseline_stats["note_counts"].get(notice, 0)
                for notice in SPECIAL_NOTICES
            },
            "note_counts": baseline_stats["note_counts"],
            "ext_to_int_src": baseline_stats["ext_to_int_src"],
        }
        report["baseline"] = {
            "range": baseline["range"],
            "totals": baseline["totals"],
            "targeted_notices": baseline["targeted_notices"],
            "notice_rate_per_day": rate_per_day(
                baseline["totals"]["notices"], baseline_start_dt, baseline_end_dt
            ),
        }
        report["comparisons"] = {
            "current_notice_rate_per_day": rate_per_day(
                report["totals"]["notices"], start_dt, end_dt
            ),
            "baseline_notice_rate_per_day": report["baseline"]["notice_rate_per_day"],
        }

        report["comparisons"]["notice_rate_ratio"] = (
            report["comparisons"]["current_notice_rate_per_day"]
            / report["comparisons"]["baseline_notice_rate_per_day"]
            if report["comparisons"]["baseline_notice_rate_per_day"] > 0
            else None
        )

        baseline_obj = {
            "totals": baseline["totals"],
            "note_counts": baseline["note_counts"],
            "ext_to_int_src": baseline["ext_to_int_src"],
            "range": {
                "start_dt": baseline_start_dt,
                "end_dt": baseline_end_dt,
            },
        }
    else:
        baseline_obj = None

    report["severity_counts"] = counter_to_list(data["severity_counts"])
    report["findings"] = detect_findings(
        period, start_dt, end_dt, data, networks, baseline_obj
    )

    return report


def format_report(period_name, start_dt, end_dt, report, networks, daily=False):
    lines = []
    lines.append(f"{period_name} Zeek Notice Report")
    lines.append(f"Range: {start_dt} to {end_dt}")
    lines.append(f"Notice files: {len(report.get('notice_files', []))}")
    lines.append(f"Total notices: {report['totals']['notices']}")
    if "comparisons" in report and report["comparisons"].get("notice_rate_ratio") is not None:
        ratio = report["comparisons"]["notice_rate_ratio"]
        lines.append(f"Rate vs baseline: {ratio:.2f}x")
    lines.append("")

    lines.append("Targeted notices:")
    for notice in SPECIAL_NOTICES:
        lines.append(f"  {notice}: {report['targeted_notices'].get(notice, 0)}")
    lines.append("")

    lines.append("Top notice types:")
    for item in report.get("top_notice_types", [])[:10]:
        lines.append(f"  {item['key']}: {item['count']}")
    lines.append("")

    lines.append("Top source IPs:")
    for item in report.get("top_source_ips", [])[:10]:
        lines.append(f"  {item['key']} ({item.get('role', 'unknown')}) - {item['count']}")
    lines.append("")

    lines.append("Top destination IPs:")
    for item in report.get("top_destination_ips", [])[:10]:
        lines.append(f"  {item['key']} ({item.get('role', 'unknown')}) - {item['count']}")
    lines.append("")

    lines.append("Source roles:")
    for item in report.get("source_roles", []):
        lines.append(f"  {item['key']}: {item['count']}")
    lines.append("")

    lines.append("Destination roles:")
    for item in report.get("destination_roles", []):
        lines.append(f"  {item['key']}: {item['count']}")
    lines.append("")

    lines.append("Severity (notice type heuristic):")
    for item in report.get("severity_counts", []):
        lines.append(f"  {item['key']}: {item['count']}")
    lines.append("")

    lines.append("Missing fields:")
    lines.append(f"  missing src: {report['missing_fields']['missing_src']}")
    lines.append(f"  missing dst: {report['missing_fields']['missing_dst']}")
    lines.append("")

    if daily:
        lines.append("Daily investigation focus:")
        lines.append("  External source to internal destination (top sources):")
        focus = report.get("daily_investigation_focus", {})
        for item in focus.get("external_to_internal_sources", [])[:10]:
            lines.append(
                f"    {item['key']} ({item.get('role', 'unknown')}) - {item['count']}"
            )
        lines.append("  External source to internal destination (top destinations):")
        for item in focus.get("external_to_internal_destinations", [])[:10]:
            lines.append(
                f"    {item['key']} ({item.get('role', 'unknown')}) - {item['count']}"
            )
        lines.append("  Internal source to external destination (top sources):")
        for item in focus.get("internal_to_external_sources", [])[:10]:
            lines.append(
                f"    {item['key']} ({item.get('role', 'unknown')}) - {item['count']}"
            )
        lines.append("  Internal source to external destination (top destinations):")
        for item in focus.get("internal_to_external_destinations", [])[:10]:
            lines.append(
                f"    {item['key']} ({item.get('role', 'unknown')}) - {item['count']}"
            )
        lines.append("")

    lines.append("Notable findings:")
    findings = report.get("findings", [])
    if not findings:
        lines.append("  (none)")
    else:
        for finding in findings[:20]:
            sev = finding.get("severity", "info").upper()
            title = finding.get("title", "Finding")
            desc = finding.get("description", "")
            lines.append(f"  [{sev}] {title} - {desc}".rstrip())
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_json_report(path, report):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_csv_report(path, report):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["section", "key", "role", "count", "details"])
        for notice, count in report["targeted_notices"].items():
            writer.writerow(["targeted_notice", notice, "", count, ""])
        for item in report["top_notice_types"]:
            writer.writerow(["top_notice_type", item["key"], "", item["count"], ""])
        for item in report["top_source_ips"]:
            writer.writerow(
                ["top_source_ip", item["key"], item.get("role", ""), item["count"], ""]
            )
        for item in report["top_destination_ips"]:
            writer.writerow(
                [
                    "top_destination_ip",
                    item["key"],
                    item.get("role", ""),
                    item["count"],
                    "",
                ]
            )
        for item in report["source_roles"]:
            writer.writerow(["source_role", item["key"], "", item["count"], ""])
        for item in report["destination_roles"]:
            writer.writerow(["destination_role", item["key"], "", item["count"], ""])
        for item in report.get("severity_counts", []):
            writer.writerow(["severity", item["key"], "", item["count"], ""])
        for key, value in report["missing_fields"].items():
            writer.writerow(["missing_field", key, "", value, ""])
        if "baseline" in report:
            writer.writerow(
                [
                    "baseline",
                    "notice_rate_per_day",
                    "",
                    "",
                    report["baseline"].get("notice_rate_per_day"),
                ]
            )
        if "daily_investigation_focus" in report:
            focus = report["daily_investigation_focus"]
            for item in focus["external_to_internal_sources"]:
                writer.writerow(
                    [
                        "daily_external_to_internal_source",
                        item["key"],
                        item.get("role", ""),
                        item["count"],
                        "",
                    ]
                )
            for item in focus["external_to_internal_destinations"]:
                writer.writerow(
                    [
                        "daily_external_to_internal_destination",
                        item["key"],
                        item.get("role", ""),
                        item["count"],
                        "",
                    ]
                )
            for item in focus["internal_to_external_sources"]:
                writer.writerow(
                    [
                        "daily_internal_to_external_source",
                        item["key"],
                        item.get("role", ""),
                        item["count"],
                        "",
                    ]
                )
            for item in focus["internal_to_external_destinations"]:
                writer.writerow(
                    [
                        "daily_internal_to_external_destination",
                        item["key"],
                        item.get("role", ""),
                        item["count"],
                        "",
                    ]
                )
        for finding in report.get("findings", []):
            writer.writerow(
                [
                    "finding",
                    finding.get("title", "Finding"),
                    finding.get("severity", "info"),
                    0,
                    finding.get("description", ""),
                ]
            )


def start_of_today():
    today = dt.date.today()
    return dt.datetime(today.year, today.month, today.day)


def period_range(period, include_today):
    today_start = start_of_today()
    if include_today:
        end_dt = today_start + dt.timedelta(days=1)
    else:
        end_dt = today_start

    if period == "daily":
        start_dt = end_dt - dt.timedelta(days=1)
    elif period == "weekly":
        start_dt = end_dt - dt.timedelta(days=7)
    elif period == "monthly":
        start_dt = dt.datetime(end_dt.year, end_dt.month, 1)
    else:
        raise ValueError(f"Unknown period: {period}")

    return start_dt, end_dt


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate Zeek notice reports from /opt/zeek/logs."
    )
    parser.add_argument(
        "--period",
        choices=["daily", "weekly", "monthly"],
        required=True,
        help="Report period based on local system time.",
    )
    parser.add_argument(
        "--log-root",
        default="/opt/zeek/logs",
        help="Root Zeek log directory (default: /opt/zeek/logs).",
    )
    parser.add_argument(
        "--networks",
        default="/opt/zeek/etc/networks.cfg",
        help="Path to networks.cfg for internal IP ranges.",
    )
    parser.add_argument(
        "--include-today",
        action="store_true",
        help="Include the current day in the report window.",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Skip baseline comparisons (faster, fewer anomalies).",
    )
    parser.add_argument(
        "--output",
        help="Write report to a file instead of stdout.",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/csi/reports/zeek",
        help="Directory to write JSON/CSV reports (default: /home/csi/reports/zeek).",
    )
    return parser


def run_report(args):
    networks = load_internal_networks(args.networks)
    start_dt, end_dt = period_range(args.period, args.include_today)

    baseline_stats = None
    baseline_range = None
    if not args.no_baseline:
        baseline_range = summarize_baseline(args.period, start_dt, end_dt)
        baseline_start_dt, baseline_end_dt = baseline_range
        baseline_stats = report_range(
            baseline_start_dt, baseline_end_dt, args.log_root, networks, details=False
        )

    data = report_range(start_dt, end_dt, args.log_root, networks, details=True)
    report_data = build_report_data(
        args.period,
        start_dt,
        end_dt,
        data,
        networks,
        daily=args.period == "daily",
        baseline_stats=baseline_stats,
        baseline_range=baseline_range,
    )
    report_text = format_report(
        args.period.capitalize(),
        start_dt,
        end_dt,
        report_data,
        networks,
        daily=args.period == "daily",
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(report_text)
    else:
        print(report_text)

    os.makedirs(args.output_dir, exist_ok=True)
    date_stamp = start_dt.strftime("%Y%m%d")
    json_path = os.path.join(
        args.output_dir, f"zeek_notice_{args.period}_{date_stamp}.json"
    )
    csv_path = os.path.join(
        args.output_dir, f"zeek_notice_{args.period}_{date_stamp}.csv"
    )
    write_json_report(json_path, report_data)
    write_csv_report(csv_path, report_data)


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_report(args)


if __name__ == "__main__":
    main()
