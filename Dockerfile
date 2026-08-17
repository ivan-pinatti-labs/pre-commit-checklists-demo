# Runs rotate-logs.sh and check_disk_usage.py as a sidecar container,
# mounted against the log directory of whatever it is rotating logs for.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

COPY check_disk_usage.py rotate-logs.sh config.yaml ./
RUN chmod +x rotate-logs.sh check_disk_usage.py

ENTRYPOINT ["./rotate-logs.sh"]
CMD ["--log-dir", "/var/log/myapp"]
