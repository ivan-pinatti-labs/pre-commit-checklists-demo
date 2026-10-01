# Runs rotate-logs.sh and check_disk_usage.py as a sidecar container,
# mounted against the log directory of whatever it is rotating logs for.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --require-hashes --only-binary=:all: --requirement requirements.txt

# Owned by root and only executable by the user the container runs as, so
# the scripts cannot be changed from inside it.
COPY --chmod=755 check_disk_usage.py rotate-logs.sh ./
COPY --chmod=644 config.yaml ./

# Not root (`rotator`, by its numeric id so the host can resolve it).
# The log directory mounted in has to be writable by this user,
# since rotating means replacing files in it.
RUN useradd --no-create-home --uid 10001 rotator
USER 10001

ENTRYPOINT ["./rotate-logs.sh"]
CMD ["--log-dir", "/var/log/myapp"]
