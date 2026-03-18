#!/bin/bash
mkdir -p /app/.streamlit
cat > /app/.streamlit/secrets.toml << EOF
AIRTABLE_API_KEY = "${AIRTABLE_API_KEY}"
AIRTABLE_BASE_ID = "${AIRTABLE_BASE_ID}"
COMPANIES_TABLE  = "${COMPANIES_TABLE}"
PROJECTS_TABLE   = "${PROJECTS_TABLE}"
STUDENTS_TABLE   = "${STUDENTS_TABLE}"
MAGIC_LINK_SECRET = "${MAGIC_LINK_SECRET}"
RESEND_API_KEY   = "${RESEND_API_KEY}"
FROM_EMAIL       = "${FROM_EMAIL}"
APP_URL          = "${APP_URL}"
ADMIN_KEY        = "${ADMIN_KEY}"
EOF
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
