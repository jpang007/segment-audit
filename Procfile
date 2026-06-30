web: gunicorn app:app --bind 0.0.0.0:8000 --timeout 120 --workers 1 --threads 4 --worker-class gthread --worker-tmp-dir /dev/shm --log-file - --access-logfile - --error-logfile - --log-level info
