#!/usr/bin/env bash
#
# Tests for rotate-logs.sh. Every line of the script has to run in one of
# them: `make coverage` runs this file under kcov and fails below 100%.
# Each case runs the script as its own bash process, the way cron would, in
# a scratch directory that is removed afterwards.

set -o errexit
set -o pipefail
set -o nounset

__script="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/rotate-logs.sh"
__scratch="$(mktemp -d)"
trap 'rm -rf "${__scratch}"' EXIT
__failures=0

# Runs the script with the given arguments and records its exit status,
# standard output and standard error for the assertions below.
run() {
  __status=0
  bash "${__script}" "$@" >"${__scratch}/out" 2>"${__scratch}/err" || __status=$?
}

check() {
  local name="${1}" want_status="${2}" stream="${3}" want_text="${4}"
  if [[ "${__status}" -ne "${want_status}" ]]; then
    echo "FAIL ${name}: exit ${__status}, wanted ${want_status}" >&2
    __failures=$((__failures + 1))
  elif ! grep --quiet --fixed-strings -- "${want_text}" "${__scratch}/${stream}"; then
    echo "FAIL ${name}: '${want_text}' not in std${stream}" >&2
    __failures=$((__failures + 1))
  else
    echo "ok ${name}"
  fi
}

# Records a failed expectation about the files the script left behind.
fail() {
  echo "FAIL ${1}" >&2
  __failures=$((__failures + 1))
}

# A log directory with one file past the default 14 day window and one
# inside it.
fresh_logs() {
  rm -rf "${__scratch}/logs"
  mkdir "${__scratch}/logs"
  touch -d '30 days ago' "${__scratch}/logs/old.log"
  touch "${__scratch}/logs/new.log"
}

fresh_logs
run --log-dir "${__scratch}/logs" --dry-run
check "dry run lists the old log" 0 out "Would compress: ${__scratch}/logs/old.log"
[[ -f "${__scratch}/logs/old.log" ]] || fail "dry run changed a file"

run --log-dir "${__scratch}/logs"
check "compresses the old log" 0 out "Compressed: ${__scratch}/logs/old.log.gz"
[[ ! -f "${__scratch}/logs/old.log" && -f "${__scratch}/logs/new.log" ]] ||
  fail "compressed something other than only the old log"

fresh_logs
run --log-dir "${__scratch}/logs" --retention-days 60
check "a wider window leaves both" 0 out "Nothing older than 60 days"

fresh_logs
__status=0
DEBUG=true bash "${__script}" --log-dir "${__scratch}/logs" --dry-run \
  >"${__scratch}/out" 2>"${__scratch}/err" || __status=$?
# Only that it still runs: the trace itself goes to kcov, not stderr, when
# `make coverage` runs this, because kcov measures bash through xtrace.
check "DEBUG still runs normally" 0 out "Would compress: ${__scratch}/logs/old.log"

run --help
check "help prints usage" 1 out "Usage:"

run --bogus
check "an unknown option is refused" 1 err "Unknown option: --bogus"

run
check "the log directory is required" 1 err "--log-dir is required"

run --log-dir "${__scratch}/absent"
check "a missing directory exits 2" 2 err "does not exist"

if [[ "${__failures}" -gt 0 ]]; then
  echo "${__failures} failed" >&2
  exit 1
fi
