#!/bin/bash
set -e
git pull origin
. env/bin/activate
pip install -r requirements.txt
npm ci
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python manage.py collectstatic --no-input
python manage.py migrate --no-input
systemctl daemon-reload
systemctl reload nginx
systemctl stop star-burger
systemctl start star-burger
last_commit_hash=$(git rev-parse HEAD)
curl -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST 'https://api.rollbar.com/api/1/deploy' \
     -d '{"environment": "production","revision": "'$last_commit_hash'","rollbar_name": "nurbek","local_username": "root","status": "succeeded"}' \
     -s >/dev/null
echo 'Deploy has been successfully completed!'
