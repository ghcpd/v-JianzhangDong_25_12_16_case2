#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import sqlite3, os
DB='appdata.db'
if os.path.exists(DB):
    print('DB exists')
else:
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    c.execute('CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
    c.execute('INSERT INTO profiles (id,name,balance) VALUES (1, "alice", 100.0)')
    conn.commit(); conn.close(); print('DB created')
PY
mkdir -p configs logs || true
cat > configs/sample.yaml <<'YAML'
welcome: true
version: 1
YAML
echo "Setup complete. Create necessary env vars before running the service:" 
echo "  export PAYMENT_TOKEN=REPLACE_ME"
echo "  export MAIL_SERVER_KEY=REPLACE_ME"
echo "  export INTERNAL_AUTH=REPLACE_ME"
echo "  export ADMIN_API_KEY=REPLACE_ME"
echo "You can run tests: ./run_test.sh" 
