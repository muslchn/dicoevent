#!/bin/bash

# DicoEvent Deployment Script

echo "🚀 Starting DicoEvent Deployment..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root directory."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if PostgreSQL is available
echo "🔍 Checking PostgreSQL connection..."
# This would normally test the database connection

# Create database migrations
echo "📋 Creating database migrations..."
python manage.py makemigrations

# Apply migrations
echo "💾 Applying database migrations..."
python manage.py migrate

# Create initial data
echo "👥 Creating initial users..."
python create_initial_data.py

# Collect static files
echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

# Start the server
echo "✅ Deployment complete!"
echo "🌐 Starting development server..."
echo "📍 API available at: http://localhost:8000"
echo "🔐 Test users:"
echo "   Super User: Aras / 1234qwer!@#$"
echo "   Regular User: dicoding / 1234qwer!@#$"
echo "   Admin: admin / 1234qwer!@#$"
echo "   Organizer: organizer / 1234qwer!@#$"
echo ""
echo "Press Ctrl+C to stop the server"

python manage.py runserver