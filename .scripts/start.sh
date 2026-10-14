#!/bin/bash
source venv/bin/activate

cat <<EOF > /app/settings.ini
$SETTINGS_INI
EOF
cat /app/settings.ini


waitress-serve --listen *:$PORT wsgi:app