# Bound only to loopback; Nginx overwrites X-Real-IP. Never bind publicly.
bind='127.0.0.1:8090'
workers=2
worker_class='sync'
timeout=30
limit_request_line=2048
limit_request_fields=40
limit_request_field_size=4096
max_requests=1000
max_requests_jitter=100
accesslog=None
errorlog='-'
