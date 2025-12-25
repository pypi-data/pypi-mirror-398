import argparse
import json
from datetime import datetime
from statistics import mean, median, quantiles
from collections import defaultdict
from tabulate import tabulate
import csv
import sys
import re
import os
from pathlib import Path
from . import __version__

TRUNC_PLAN_LEN = 60
TRUNC_APP_LEN = 40
TRUNC_SHAPE_LEN = 80
TRUNC_ERRMSG_LEN = 120


def _truncate(text, max_len, verbose=False):
    if verbose:
        return text
    if text is None:
        return ''
    s = str(text)
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + '…'


def _validate_logfile(logfile_path):
    """Validate that the log file exists and is readable.

    Special case: '-' means read from stdin and is always considered valid.
    """
    if logfile_path == '-':
        return True
    if not logfile_path:
        print("Error: No logfile specified.")
        return False
    
    if not os.path.exists(logfile_path):
        print(f"Error: File '{logfile_path}' not found.")
        print("Please check the file path and try again.")
        return False
    
    if not os.path.isfile(logfile_path):
        print(f"Error: '{logfile_path}' is not a file.")
        return False
    
    try:
        with open(logfile_path, 'r') as f:
            # Try to read the first line to check if file is readable
            f.readline()
    except PermissionError:
        print(f"Error: Permission denied reading '{logfile_path}'.")
        print("Please check file permissions and try again.")
        return False
    except Exception as e:
        print(f"Error: Cannot read '{logfile_path}': {e}")
        return False
    
    return True


def _extract_command_query_shape(command_obj):
    """
    Extract query shape from MongoDB command object.
    Handles both find and aggregate commands properly.
    """
    if not isinstance(command_obj, dict):
        return None
    
    query_shape_parts = []
    
    # Handle find commands
    if 'find' in command_obj:
        query_shape_parts.append('find')
        
        # Add filter information
        if 'filter' in command_obj:
            filter_obj = command_obj['filter']
            if isinstance(filter_obj, dict) and filter_obj:
                # Create a simplified shape representation
                filter_keys = sorted(filter_obj.keys())
                if filter_keys:
                    query_shape_parts.append(f"filter:{','.join(filter_keys)}")
                else:
                    query_shape_parts.append("filter:empty")
            else:
                query_shape_parts.append("filter")
        
        # Add sort information if present
        if 'sort' in command_obj:
            sort_obj = command_obj['sort']
            if isinstance(sort_obj, dict) and sort_obj:
                sort_keys = sorted(sort_obj.keys())
                query_shape_parts.append(f"sort:{','.join(sort_keys)}")
    
    # Handle aggregate commands
    elif 'aggregate' in command_obj:
        query_shape_parts.append('aggregate')
        
        # Add pipeline information
        if 'pipeline' in command_obj:
            pipeline = command_obj['pipeline']
            if isinstance(pipeline, list) and pipeline:
                # Extract stage types from pipeline
                stages = []
                for stage in pipeline:
                    if isinstance(stage, dict):
                        # Get the stage operator (like $match, $group, etc.)
                        stage_ops = [key for key in stage.keys() if key.startswith('$')]
                        if stage_ops:
                            stages.extend(stage_ops)
                
                if stages:
                    query_shape_parts.append(f"pipeline:[{','.join(stages)}]")
                else:
                    query_shape_parts.append(f"pipeline:[{len(pipeline)}]")
            else:
                query_shape_parts.append("pipeline")
    
    # Return joined shape or None if no recognizable pattern
    return ':'.join(query_shape_parts) if query_shape_parts else None


def _ensure_user_path_updated():
    """Attempt to ensure the user install bin directory is on PATH.

    This is a best-effort, non-interactive helper. It prepends the bin path for the
    running interpreter's user base (e.g. ~/Library/Python/3.13/bin on macOS) to PATH for
    the current process and, if not already present in the user's shell startup file,
    appends a line to ~/.zprofile (preferred for login shells) or ~/.zshrc as fallback.

    Opt-out: set environment variable QUERYHOUND_SKIP_PATH_UPDATE=1 before running.
    """
    if os.environ.get("QUERYHOUND_SKIP_PATH_UPDATE") == "1":
        return
    try:
        user_base = sys.base_prefix  # fallback; better via site.getusersitepackages()
        try:
            import site
            user_base = site.getuserbase()
        except Exception:
            pass
        candidate_bin = Path(user_base) / "bin"
        if not candidate_bin.exists():
            # macOS user installs often are in ~/Library/Python/{major.minor}/bin
            alt = Path.home() / "Library" / "Python" / f"{sys.version_info.major}.{sys.version_info.minor}" / "bin"
            if alt.exists():
                candidate_bin = alt
        # Update in-process PATH
        path_parts = os.environ.get("PATH", "").split(":")
        if str(candidate_bin) not in path_parts:
            os.environ["PATH"] = f"{candidate_bin}:{os.environ.get('PATH','')}"
        # Persist for future shells if missing
        zprofile = Path.home() / ".zprofile"
        zshrc = Path.home() / ".zshrc"
        target_rc = zprofile if zprofile.exists() else zshrc
        export_line = f'export PATH="{candidate_bin}:$PATH"'\
            if str(candidate_bin) not in os.environ.get("PATH", "") else None
        if export_line:
            try:
                # Only append if not already present in the file
                if target_rc.exists():
                    existing = target_rc.read_text(errors="ignore")
                    if str(candidate_bin) in existing:
                        return
                with target_rc.open("a") as fh:
                    fh.write(f"\n# Added by queryhound to ensure qh is on PATH\n{export_line}\n")
            except Exception:
                pass
    except Exception:
        pass


def parse_date(date_str):
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            if fmt.endswith("%z") and "+00:00" not in date_str and "-" not in date_str[-6:]:
                date_str += "+00:00"
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}")


def parse_log_line(line):
    try:
        entry = json.loads(line)
        timestamp = entry.get("t", {}).get("$date")
        if timestamp:
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        attr = entry.get("attr", {})
        ns = attr.get("ns")
        ms = attr.get("durationMillis") or attr.get("ms")
        query = attr.get("query") or attr.get("filter")
        plan = attr.get("planSummary")
        command = entry.get("msg", "")
        # Command object (raw) for deriving query shape when available
        command_obj = attr.get("command") if isinstance(attr.get("command"), dict) else None
        query_shape_hash = attr.get("queryShapeHash") or attr.get("queryShapeId")
        query_shape = None
        if query_shape_hash:
            query_shape = query_shape_hash
        elif command_obj:
            op_keys_priority = ["find", "aggregate", "update", "delete", "insert", "count"]
            primary = next((k for k in op_keys_priority if k in command_obj), None)
            if not primary and command_obj:
                primary = next(iter(command_obj.keys()))
            extras = []
            if "pipeline" in command_obj and isinstance(command_obj.get("pipeline"), list):
                extras.append(f"pipeline[{len(command_obj['pipeline'])}]")
            if "filter" in command_obj:
                extras.append("filter")
            if "query" in command_obj:
                extras.append("query")
            # Shallow detection of $match stage
            try:
                snippet = json.dumps(command_obj, default=str)[:800]
                if "$match" in snippet:
                    extras.append("$match")
            except Exception:
                pass
            parts = [p for p in [primary] + extras if p]
            if parts:
                query_shape = ":".join(parts)
        # Try multiple locations for application name seen in connection metadata
        app_name = (
            attr.get("appName")
            or attr.get("applicationName")
            or (attr.get("client", {}).get("application", {}).get("name") if isinstance(attr.get("client"), dict) else None)
            or ""
        )
        keys_examined = attr.get("keysExamined", 0)
        docs_examined = attr.get("docsExamined", 0)
        nreturned = attr.get("nreturned", 0)
        remote_ip = attr.get("remote", "")
        if remote_ip:
            remote_ip = remote_ip.split(":")[0]
        app_name_cleaned = re.sub(r" v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", "", app_name)
        app_name_cleaned = re.sub(r"\s*\(.*\)", "", app_name_cleaned)

        operation = "Unknown"
        cmd_l = command.lower()
        attr_type = attr.get("type")
        # Detect connection acceptance events
        if "connection accepted" in cmd_l or ("connection" in cmd_l and "accepted" in cmd_l):
            operation = "Connection"
        elif attr_type:  # Prefer explicit attr.type when present
            operation = str(attr_type).capitalize()
        elif 'find' in command.lower():
            operation = "Find"
        elif 'insert' in command.lower():
            operation = "Insert"
        elif 'update' in command.lower():
            operation = "Update"
        elif 'delete' in command.lower():
            operation = "Delete"

        return {
            'timestamp': timestamp,
            'namespace': ns,
            'ms': ms,
            'query': query,
            'plan': plan,
            'command': command,
            'operation': operation,
            'app_name': app_name_cleaned,
            'keys_examined': keys_examined,
            'docs_examined': docs_examined,
            'nreturned': nreturned,
            'line': line.strip(),
            'remote_ip': remote_ip,
            'query_shape': query_shape
        }

    except json.JSONDecodeError:
        return None


def is_within_date(timestamp, start_date, end_date):
    if not timestamp:
        return False
    if start_date and timestamp < start_date:
        return False
    if end_date and timestamp > end_date:
        return False
    return True


def process_log(file_path, args):
    if not _validate_logfile(file_path):
        return {}, []
    
    results = defaultdict(lambda: {'ms_list': [], 'count': 0, 'plan': '', 'namespace': '', 'operation': '', 'app_name': '', 'keys_examined': 0, 'docs_examined': 0, 'nreturned': 0, 'remote_ip': '', 'query_shape': ''})
    log_lines = []

    try:
        stream = sys.stdin if file_path == '-' else open(file_path, 'r')
        try:
            for line in stream:
                if args.filter and not any(m.lower() in line.lower() for m in args.filter):
                    continue

                entry = parse_log_line(line)
                if not entry:
                    continue

                if not is_within_date(entry['timestamp'], args.start_date, args.end_date):
                    continue
                if args.min_ms is not None and (entry['ms'] is None or entry['ms'] < args.min_ms):
                    continue
                # Scan mode: include any plan summaries that contain COLLSCAN
                if args.scan and (entry['plan'] is None or "COLLSCAN" not in str(entry['plan'])):
                    continue
                if args.slow and (entry['ms'] is None or entry['ms'] < 100):
                    continue
                if args.namespace and args.namespace != entry['namespace']:
                    continue
                if entry['ms'] is None:
                    continue
                # Connection aggregation handled separately

                key = (entry['operation'], entry['plan'], entry['namespace'], str(entry['query']))
                results[key]['ms_list'].append(entry['ms'])
                results[key]['count'] += 1
                results[key]['plan'] = entry['plan']
                results[key]['namespace'] = entry['namespace']
                results[key]['operation'] = entry['operation']
                results[key]['app_name'] = entry['app_name']
                results[key]['keys_examined'] += entry['keys_examined']
                results[key]['docs_examined'] += entry['docs_examined']
                results[key]['nreturned'] += entry['nreturned']
                results[key]['remote_ip'] = entry['remote_ip']
                if entry.get('query_shape') and not results[key]['query_shape']:
                    results[key]['query_shape'] = entry['query_shape']

                if args.filter:
                    log_lines.append(entry['line'])
        finally:
            if stream is not sys.stdin:
                stream.close()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return {}, []

    return results, log_lines


def process_connections(file_path, args):
    """Aggregate connection-accepted events by remote IP and app name."""
    if not _validate_logfile(file_path):
        return []
    
    from collections import Counter
    counts = Counter()
    try:
        stream = sys.stdin if file_path == '-' else open(file_path, 'r')
        try:
            for line in stream:
                if args.filter and not any(m.lower() in line.lower() for m in args.filter):
                    continue
                entry = parse_log_line(line)
                if not entry:
                    continue
                # Date filtering if present
                if not is_within_date(entry['timestamp'], args.start_date, args.end_date):
                    continue
                if entry.get('operation') != 'Connection':
                    continue
                ip = entry.get('remote_ip') or 'Unknown'
                app = entry.get('app_name') or ''
                counts[(ip, app)] += 1
        finally:
            if stream is not sys.stdin:
                stream.close()
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return []
    # Prepare rows sorted by count desc
    rows = [ (ip, app, cnt) for (ip, app), cnt in counts.most_common() ]
    return rows


def process_queries(logfile_path, args):
    """
    Process distinct queries: Extract query shapes, count executions,
    and track source information (app name or IP) for top 10 queries.
    Specifically looks for COMMAND entries (c: "COMMAND") with aggregate or find operations.
    """
    if not _validate_logfile(logfile_path):
        return []
    
    query_stats = defaultdict(lambda: {'count': 0, 'sources': set()})
    
    try:
        stream = sys.stdin if logfile_path == '-' else open(logfile_path, 'r')
        try:
            for line in stream:
                try:
                    # Parse raw JSON to check for COMMAND entries
                    raw_entry = json.loads(line)
                    
                    # Only process COMMAND entries
                    if raw_entry.get('c') != 'COMMAND':
                        continue
                    
                    # Check for command structure in attr
                    attr = raw_entry.get('attr', {})
                    command_obj = attr.get('command', {})
                    
                    # Must have aggregate or find command
                    if not ('aggregate' in command_obj or 'find' in command_obj):
                        continue
                    
                    # Parse using existing function for consistency with date filtering
                    entry = parse_log_line(line)
                    if not entry:
                        continue
                    
                    if not is_within_date(entry['timestamp'], args.start_date, args.end_date):
                        continue
                    if args.namespace and args.namespace != entry['namespace']:
                        continue
                    if args.min_ms is not None and (entry['ms'] is None or entry['ms'] < args.min_ms):
                        continue
                    
                    # Extract query shape from command structure
                    query_shape = _extract_command_query_shape(command_obj)
                    
                    if not query_shape:
                        continue
                    
                    # Determine source (app name or IP)
                    source = entry.get('app_name', '').strip()
                    if not source:
                        source = entry.get('remote_ip', '').strip()
                    if not source:
                        source = 'Unknown'
                    
                    query_stats[query_shape]['count'] += 1
                    query_stats[query_shape]['sources'].add(source)
                    
                except Exception:
                    continue
        finally:
            if stream is not sys.stdin:
                stream.close()
    except Exception as e:
        print(f"Error reading file '{logfile_path}': {e}")
        return []
    
    # Convert to list and sort by count (top 10)
    result = []
    for shape, stats in query_stats.items():
        sources_str = ', '.join(sorted(list(stats['sources']))[:3])  # Show up to 3 sources
        if len(stats['sources']) > 3:
            sources_str += f" (+{len(stats['sources']) - 3} more)"
        
        result.append([
            _truncate(shape, TRUNC_SHAPE_LEN, args.verbose),
            stats['count'],
            _truncate(sources_str, TRUNC_APP_LEN * 2, args.verbose)
        ])
    
    # Sort by count descending and return top 10
    return sorted(result, key=lambda x: x[1], reverse=True)[:10]


def summarize_results(results, pvalue=None, include_pstats=False, verbose=False, truncate=False):
    table = []

    for (operation, plan, namespace, query), data in results.items():
        ms_list = data['ms_list']
        count = data['count']
        if not ms_list:
            continue
        # Truncate fields for non-verbose display
        if truncate:
            display_plan = _truncate(plan, TRUNC_PLAN_LEN, verbose=verbose)
            display_app = _truncate(data['app_name'], TRUNC_APP_LEN, verbose=verbose)
            display_shape = _truncate(data.get('query_shape') or '', TRUNC_SHAPE_LEN, verbose=verbose)
        else:
            display_plan = plan
            display_app = data['app_name']
            display_shape = data.get('query_shape') or ''

        row = [operation, display_plan, display_shape]
        if pvalue and pvalue.lower() == 'p50':
            row.append(round(median(ms_list), 2))

        avg_ms = round(mean(ms_list), 2)
        row.append(avg_ms)
        row.extend([
            data['keys_examined'],
            data['docs_examined'],
            data['nreturned']
        ])

        if include_pstats or (pvalue and pvalue.lower() in ['p75', 'p90', 'p99']):
            try:
                q = quantiles(ms_list, n=100)
            except:
                q = []

            if include_pstats or (pvalue and pvalue.lower() == 'p75'):
                row.append(q[74] if len(q) > 74 else '-')
            if include_pstats or (pvalue and pvalue.lower() == 'p90'):
                row.append(q[89] if len(q) > 89 else '-')
            if include_pstats or (pvalue and pvalue.lower() == 'p99'):
                row.append(q[98] if len(q) > 98 else '-')

        row.extend([
            data['operation'],
            count,
            display_app
        ])
        table.append(row)

    return table


def write_csv(output_file, data, headers):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        writer.writerows(data)


def main():
    # Ensure PATH includes user scripts dir so invoking `qh` after install works without manual edits.
    _ensure_user_path_updated()
    parser = argparse.ArgumentParser(description="QueryHound - MongoDB Log Filter Tool")
    parser.add_argument("logfile", nargs='?', help="Path to MongoDB JSON log file, or '-' to read from stdin")
    parser.add_argument("--scan", action="store_true", help="Only show COLLSCAN queries")
    parser.add_argument("--slow", action="store_true", help="Only show slow queries (ms >= 100)")
    parser.add_argument("--start-date", type=str, help="Start date (ISO 8601 or 'YYYY-MM-DD')")
    parser.add_argument("--end-date", type=str, help="End date (ISO 8601 or 'YYYY-MM-DD')")
    parser.add_argument("--namespace", type=str, help="Filter by namespace (db.collection)")
    parser.add_argument("--min-ms", type=int, help="Minimum duration (ms)")
    parser.add_argument("--pstats", action="store_true", help="Include P75, P90, P99 stats")
    parser.add_argument("--pvalue", type=str, choices=['P50', 'P75', 'P90', 'P99'], help="Specify a specific p-stat to include")
    parser.add_argument("--output-csv", type=str, help="Write output to CSV")
    parser.add_argument("--filter", nargs='*', type=str, help="Search for lines containing any of the specified strings")
    parser.add_argument("--connections", action="store_true", help="Displays connection counts grouped by IP and app name")
    parser.add_argument("--error", action="store_true", help="Show only error / fatal log lines (severity E/F)")
    parser.add_argument("-q", "--query", action="store_true", help="Show top 10 distinct queries with shape, count, and source")
    parser.add_argument("--verbose", action="store_true", help="Show full field values without truncation")
    parser.add_argument("-v", "--version", action="store_true", help="Show version and exit")

    args = parser.parse_args()

    # If no logfile provided and stdin is being piped, default to '-'
    if not args.logfile and not sys.stdin.isatty():
        args.logfile = '-'

    try:
        if args.version:
            print(f"queryhound version {__version__}")
            sys.exit(0)

        # Connections mode doesn't require other options
        if args.connections:
            if not args.logfile:
                parser.print_help()
                print("\nError: logfile or stdin is required for --connections mode.")
                sys.exit(2)
            try:
                # parse dates if provided
                results = process_connections(args.logfile, args)
                if results:
                    print("\nConnections:")
                    # Truncate app name unless verbose
                    if not args.verbose:
                        display_rows = []
                        for ip, app, cnt in results:
                            display_rows.append([ip, _truncate(app, TRUNC_APP_LEN, verbose=False), cnt])
                    else:
                        display_rows = results
                    print(tabulate(display_rows, headers=["Remote IP", "App Name", "Count"], tablefmt="pretty"))
                else:
                    print("No connections found in the provided timeframe.")
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                sys.exit(1)
            except Exception as e:
                print(f"Error processing connections: {e}")
                sys.exit(1)
            sys.exit(0)

        # Query mode - show top 10 distinct queries
        if args.query:
            if not args.logfile:
                parser.print_help()
                print("\nError: logfile or stdin is required for --query mode.")
                sys.exit(2)
            try:
                results = process_queries(args.logfile, args)
                if results:
                    print("\nTop 10 Distinct Queries:")
                    print(tabulate(results, headers=["Query Shape", "Count", "Sources"], tablefmt="pretty"))
                else:
                    print("No queries found in the provided timeframe.")
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                sys.exit(1)
            except Exception as e:
                print(f"Error processing queries: {e}")
                sys.exit(1)
            sys.exit(0)

        # Error mode
        if args.error:
            if not args.logfile:
                parser.print_help()
                print("\nError: logfile or stdin is required for --error mode.")
                sys.exit(2)
            # Process errors
            rows = []
            try:
                stream = sys.stdin if args.logfile == '-' else open(args.logfile, 'r')
                try:
                    for line in stream:
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        sev = entry.get('s')
                        if sev not in ('E','F'):
                            continue
                        ts_raw = entry.get('t',{}).get('$date')
                        try:
                            ts_disp = datetime.fromisoformat(ts_raw.replace('Z','+00:00')).isoformat() if ts_raw else '-'
                        except Exception:
                            ts_disp = ts_raw or '-'
                        comp = entry.get('c','')
                        _id = entry.get('id','')
                        msg = entry.get('msg','')
                        if not args.verbose:
                            msg = _truncate(msg, TRUNC_ERRMSG_LEN, verbose=False)
                        sev_disp = 'Error' if sev=='E' else 'Fatal'
                        rows.append([ts_disp, sev_disp, comp, _id, msg])
                finally:
                    if stream is not sys.stdin:
                        stream.close()
                if rows:
                    print("\nErrors:")
                    print(tabulate(rows, headers=["Timestamp","Severity","Component","ID","Message"], tablefmt="pretty"))
                else:
                    print("No error/fatal entries found.")
            except Exception as e:
                print(f"Error processing error log lines: {e}")
                sys.exit(1)
            sys.exit(0)

        if not args.logfile:
            parser.print_help()
            print("\nError: logfile or stdin is required unless --version is used.")
            sys.exit(2)
        args.start_date = parse_date(args.start_date) if args.start_date else None
        args.end_date = parse_date(args.end_date) if args.end_date else None
    except ValueError as e:
        print(f"Date parsing error: {e}")
        sys.exit(1)

    try:
        results, log_lines = process_log(args.logfile, args)

        table = []
        headers = []

        if results and (args.scan or args.slow or args.pstats or args.pvalue):
            table = summarize_results(
                results,
                pvalue=args.pvalue,
                include_pstats=args.pstats,
                verbose=args.verbose,
                truncate=(not args.verbose and (args.slow or args.scan))
            )
            if table:
                headers = ["Operation", "Plan", "Query Shape"]
                if args.pvalue and args.pvalue.lower() == 'p50':
                    headers.append("P50")
                headers += ["Avg ms", "Keys Examined", "Docs Examined", "NReturned"]
                if args.pstats or (args.pvalue and args.pvalue.lower() in ['p75', 'p90', 'p99']):
                    if args.pstats or (args.pvalue and args.pvalue.lower() == 'p75'):
                        headers.append("P75")
                    if args.pstats or (args.pvalue and args.pvalue.lower() == 'p90'):
                        headers.append("P90")
                    if args.pstats or (args.pvalue and args.pvalue.lower() == 'p99'):
                        headers.append("P99")
                headers += ["Operation Type", "Count", "App Name"]

                print("\nSummary Table:")
                print(tabulate(table, headers=headers, tablefmt="pretty"))

        if args.filter and log_lines:
            print("\nMatching Log Lines:")
            for line in log_lines:
                print(line)

        if args.output_csv and table:
            write_csv(args.output_csv, table, headers)

    except Exception as e:
        print(f"Error processing the log file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    
def run():
    main()