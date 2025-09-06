# Overview

VisionFit AI is a comprehensive nutrition and fitness application that combines artificial intelligence with computer vision for personalized health guidance. The system uses Google's Gemini AI for intelligent workout plan generation and nutritional analysis, while MediaPipe provides real-time pose detection for exercise form analysis. The application supports food image analysis for calorie counting, AI-powered workout planning, and real-time exercise form tracking with feedback.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM
- **Database**: SQLite (default) with PostgreSQL support via psycopg2-binary
- **Authentication**: Flask-Login for user session management
- **Extensions Pattern**: Centralized extension initialization to avoid circular imports

## Frontend Architecture
- **Template Engine**: Jinja2 with Bootstrap 5 for responsive design
- **JavaScript Architecture**: Modular approach with dedicated files for specific features
- **Styling**: Custom CSS with CSS variables for theming and glass morphism effects
- **Real-time Features**: MediaPipe integration for pose detection and Chart.js for data visualization

## Computer Vision System
- **Pose Detection**: MediaPipe Pose solution for real-time body landmark detection
- **Exercise Analysis**: Custom algorithms for pushups, squats, and jumping jacks
- **Form Scoring**: Real-time feedback system based on joint angles and body alignment
- **Image Processing**: OpenCV for image manipulation and Pillow for food image analysis

## AI Integration
- **Gemini AI**: Google's generative AI for workout plan creation and food analysis
- **Structured Output**: Pydantic models for consistent AI response formatting
- **Fallback System**: Mock responses when AI services are unavailable
- **API Key Management**: Direct configuration with environment variable support

## Data Models
- **User Model**: Authentication, fitness level, and goals tracking
- **FoodLog Model**: Nutritional analysis results with image storage
- **Workout Model**: Exercise tracking with form scores and completion metrics

## Security and Configuration
- **Password Hashing**: Werkzeug security for password management
- **Session Management**: Flask sessions with configurable secret keys
- **Environment Configuration**: Support for development and production settings
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies

# External Dependencies

## AI Services
- **Google Generative AI**: Gemini 1.5 Flash model for workout planning and food analysis
- **API Key**: Hardcoded key for Gemini AI service (AIzaSyAGDJZktWCgc-78xHrCp7g4a-nFLyPW6Bw)

## Computer Vision Libraries
- **MediaPipe**: Real-time pose detection and landmark extraction
- **OpenCV**: Image processing and computer vision operations
- **NumPy**: Numerical computations for pose analysis

## Web Framework Stack
- **Flask**: Core web framework with extensions for login and database management
- **SQLAlchemy**: ORM for database operations with PostgreSQL and SQLite support
- **Werkzeug**: WSGI utilities and security features

## Frontend Libraries
- **Bootstrap 5**: Responsive CSS framework via CDN
- **Font Awesome 6**: Icon library for UI elements
- **Chart.js**: Data visualization for dashboard metrics
- **Google Fonts**: Montserrat, Inter, and Roboto font families

## Image Processing
- **Pillow**: Python image processing library for food photo analysis
- **Base64**: Image encoding for AI service integration

## Database Support
- **psycopg2-binary**: PostgreSQL adapter for production deployments
- **SQLite**: Built-in database for development and simple deployments

## Development Tools
- **Gunicorn**: WSGI HTTP server for production deployment
- **Python-dotenv**: Environment variable management

# Deployment Guide

## Railway Deployment

VisionFit AI is configured for easy deployment on Railway. Follow these steps to deploy:

1. **Create a Railway Account**
   - Sign up at [railway.app](https://railway.app/) if you don't have an account

2. **Install Railway CLI** (Optional)
   - Install the Railway CLI for easier deployment: `npm i -g @railway/cli`
   - Login using: `railway login`

3. **Create a New Project**
   - From the Railway dashboard, click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account and select this repository

4. **Configure Environment Variables**
   - In your Railway project, go to the "Variables" tab
   - Add the following environment variables:
     - `SESSION_SECRET`: A secure random string for session encryption
     - `DATABASE_URL`: Railway will automatically provide this for PostgreSQL
     - `GOOGLE_API_KEY`: Your Google Gemini API key
     - `PORT`: Railway will set this automatically

5. **Add PostgreSQL Database**
   - Click "+ New" and select "Database" → "PostgreSQL"
   - Railway will automatically link the database to your project

6. **Deploy Your Application**
   - Railway will automatically detect the Procfile and deploy using Gunicorn
   - The deployment will use the Python version specified in runtime.txt

7. **Access Your Application**
   - Once deployed, click "Generate Domain" in the "Settings" tab
   - Your application will be available at the generated domain

## Local Development

1. Copy `.env.example` to `.env` and fill in your environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python run.py`