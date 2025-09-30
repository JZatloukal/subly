#!/bin/bash

# Subly Production Startup Script
echo "🚀 Starting Subly application..."

# Set environment
export FLASK_APP=app.py

# Run database migrations
echo "📊 Running database migrations..."
flask db upgrade

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Migration failed, using fallback..."
    python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('✅ Database tables created (fallback)')
"
fi

# Start the application
echo "🌟 Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT app:app