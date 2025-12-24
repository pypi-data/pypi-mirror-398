#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

if [ -z "${DATABASE_URL}" ]; then
    base_postgres_image_default_user='postgres'
    base_postgres_image_default_password='password'
    export DATABASE_URL="postgres://$base_postgres_image_default_user:$base_postgres_image_default_password@db:5432/postgres"
fi

# Wait for DB to be reachable
# Simple python script to wait for DB connection
python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse

url = urlparse("${DATABASE_URL}")
max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg2.connect(
            dbname=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        conn.close()
        print("Database connected.")
        sys.exit(0)
    except psycopg2.OperationalError:
        print(f"Waiting for database... {i+1}/{max_retries}")
        time.sleep(1)

sys.exit(1)
END

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
