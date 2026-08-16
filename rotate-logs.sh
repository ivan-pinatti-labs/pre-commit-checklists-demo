#!/usr/bin/env bash

: '
  Compresses log files older than a retention window and removes the
  uncompressed originals. Meant to run from cron or a systemd timer.

  Exit status codes:
    0 - success (including "nothing to do")
    1 - usage error
    2 - log directory not found
'

if [ "${DEBUG:-false}" = true ]; then
  set -x
fi

set -o errexit
set -o pipefail
set -o nounset

__log_dir=""
__retention_days=14
__dry_run=false

usage() {
  cat <<EOF
Usage: $(basename "${0}") --log-dir <path> [--retention-days <n>] [--dry-run]

Compresses (gzip) every *.log file under --log-dir last modified more than
--retention-days ago, then removes the uncompressed original.

Arguments:
  --log-dir <path>        Directory to scan. Must already exist.
  --retention-days <n>    Age in days before a log is compressed. Default: 14.
  --dry-run                Print what would be compressed, change nothing.

Examples:
  $(basename "${0}") --log-dir /var/log/myapp
  $(basename "${0}") --log-dir /var/log/myapp --retention-days 7 --dry-run
EOF
  exit 1
}

while [ $# -gt 0 ]; do
  case "${1}" in
  --log-dir)
    __log_dir="${2:-}"
    shift 2
    ;;
  --retention-days)
    __retention_days="${2:-}"
    shift 2
    ;;
  --dry-run)
    __dry_run=true
    shift
    ;;
  -h | --help)
    usage
    ;;
  *)
    echo "Unknown option: ${1}" >&2
    usage
    ;;
  esac
done

if [ -z "${__log_dir}" ]; then
  echo "Error: --log-dir is required." >&2
  usage
fi

if [ ! -d "${__log_dir}" ]; then
  echo "Error: log directory '${__log_dir}' does not exist." >&2
  exit 2
fi

__found=0
while IFS= read -r -d '' __file; do
  __found=$((__found + 1))
  if [ "${__dry_run}" = true ]; then
    echo "Would compress: ${__file}"
    continue
  fi
  gzip --force "${__file}"
  echo "Compressed: ${__file}.gz"
done < <(find "${__log_dir}" -maxdepth 1 -name '*.log' -mtime "+${__retention_days}" -print0)

if [ "${__found}" -eq 0 ]; then
  echo "Nothing older than ${__retention_days} days under ${__log_dir}."
fi
