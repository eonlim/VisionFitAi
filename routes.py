from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import base64
from PIL import Image
import io
import logging
from datetime import datetime, timedelta
import numpy as np

# Handle optional cv2 import
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV (cv2) not available. Some pose detection features may be limited.")

# Import db from extensions to avoid circular imports
from extensions import db
from models import User, FoodLog, Workout
import gemini
from pose_detection import PoseAnalyzer


# Global app variable that will be set by the main app
app = None

# Initialize pose analyzer
pose_analyzer = PoseAnalyzer()

def set_app(flask_app):
    """Set the Flask app instance for route registration"""
    global app
    app = flask_app

# Route definitions
def register_routes(flask_app):
    """Register all routes with the Flask app"""
    global app
    app = flask_app

    @app.route('/')
    def index():
        return render_template('index.html')


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            fitness_level = request.form.get('fitness_level', 'beginner')
            fitness_goals = request.form.get('fitness_goals', '')

            # Check if user exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists')
                return render_template('register.html')

            if User.query.filter_by(email=email).first():
                flash('Email already registered')
                return render_template('register.html')

            # Create new user
            user = User(
                username=username, 
                email=email, 
                fitness_level=fitness_level,
                fitness_goals=fitness_goals
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user)
            return redirect(url_for('dashboard'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get user's recent food logs
        recent_food_logs = FoodLog.query.filter_by(user_id=current_user.id).order_by(FoodLog.logged_at.desc()).limit(5).all()
        
        # Calculate workout statistics
        workouts = Workout.query.filter_by(user_id=current_user.id).all()
        total_workouts = len(workouts)
        
        # Calculate total calories burned
        total_calories_burned = sum(workout.calories_burned or 0 for workout in workouts)
        
        # Calculate average workout duration
        if total_workouts > 0:
            avg_duration = sum(workout.duration_minutes or 0 for workout in workouts) / total_workouts
            avg_duration = f"{int(avg_duration)} min"
        else:
            avg_duration = "0 min"
        
        # Calculate day streak (simplified version - consecutive days with workouts)
        streak = 0
        if workouts:
            # Sort workouts by completion date
            sorted_workouts = sorted(workouts, key=lambda w: w.completed_at, reverse=True)
            
            # Get unique dates of workouts
            workout_dates = set()
            for workout in sorted_workouts:
                workout_dates.add(workout.completed_at.date())
            
            # Count consecutive days
            streak = 0
            today = datetime.utcnow().date()
            
            for i in range(30):  # Check up to 30 days back
                check_date = today - timedelta(days=i)
                if check_date in workout_dates:
                    streak += 1
                else:
                    # Break streak if a day is missed
                    if i < streak:
                        break
        
        return render_template('dashboard.html', 
                              recent_food_logs=recent_food_logs,
                              total_workouts=total_workouts,
                              total_calories_burned=total_calories_burned,
                              avg_duration=avg_duration,
                              streak=streak)

    @app.route('/exercise-analysis')
    @app.route('/exercise_analysis')  # Adding alternative route with underscore
    @login_required
    def exercise_analysis():
        """Render the exercise analysis page"""
        return render_template('exercise_analysis.html')

    @app.route('/api/analyze-pose', methods=['POST'])
    @login_required
    def analyze_pose():
        """API endpoint for real-time pose analysis"""
        try:
            data = request.json
            landmarks = data.get('landmarks')
            exercise_type = data.get('exercise_type')

            if not landmarks or not exercise_type:
                return jsonify({'error': 'Missing landmarks or exercise type'}), 400

            # Analyze pose using the PoseAnalyzer
            result = pose_analyzer.analyze_pose(landmarks, exercise_type)
            return jsonify(result)

        except Exception as e:
            logging.error(f"Error in pose analysis: {e}")
            return jsonify({'error': 'Analysis failed'}), 500

    @app.route('/workout_planner', methods=['GET', 'POST'])
    @login_required
    def workout_planner():
        """Render the workout planner page and handle form submissions"""
        if request.method == 'POST':
            try:
                fitness_level = request.form.get('fitness_level')
                equipment = request.form.get('equipment')
                goals = request.form.get('goals')

                # Get user context
                user_context = f"Fitness level: {fitness_level}, Equipment: {equipment}, Goals: {goals}"

                # Get AI response for workout plan
                plan = gemini.get_workout_plan(user_context)

                return render_template('workout_planner.html', plan=plan)

            except Exception as e:
                flash('Error generating workout plan. Please try again.', 'error')
                return render_template('workout_planner.html')

        return render_template('workout_planner.html')

    @app.route('/exercise_tracker')
    @login_required
    def exercise_tracker():
        """Render the exercise tracker page"""
        return render_template('exercise_tracker.html')



    @app.route('/food-analyzer', methods=['GET', 'POST'])
    @login_required
    def food_analyzer():
        if request.method == 'POST':
            if 'food_image' not in request.files:
                flash('No image uploaded')
                return redirect(request.url)

            file = request.files['food_image']
            if file.filename == '':
                flash('No image selected')
                return redirect(request.url)

            if file:
                try:
                    # Read image data
                    image_data = file.read()

                    # Analyze using AI
                    result = gemini.analyze_food_image(image_data)

                    if result['success']:
                        # Parse the analysis result
                        analysis_text = result['analysis']

                        # Extract calories from analysis text
                        import re
                        calorie_patterns = [
                            r'total.*?(\d+).*?calorie',
                            r'(\d+).*?total.*?calorie',
                            r'calories?[:\s]*(\d+)',
                            r'(\d+)[- ]*(\d+)?\s*calorie',
                            r'approximately?\s*(\d+)'
                        ]

                        estimated_calories = 0
                        for pattern in calorie_patterns:
                            calorie_match = re.search(pattern, analysis_text.lower())
                            if calorie_match:
                                estimated_calories = int(calorie_match.group(1))
                                break

                        # If no calories found, provide a default estimate
                        if estimated_calories == 0:
                            estimated_calories = 250  # Default reasonable estimate

                        # Save food log
                        meal_type = request.form.get('meal_type', 'snack')
                        food_log = FoodLog(
                            user_id=current_user.id,
                            food_items=analysis_text,
                            total_calories=estimated_calories,
                            meal_type=meal_type
                        )
                        db.session.add(food_log)
                        db.session.commit()

                        flash('Food analysis completed successfully!', 'success')
                        return render_template('food_analyzer.html', 
                                             analysis=analysis_text,
                                             estimated_calories=estimated_calories)
                    else:
                        flash(f'Error analyzing food: {result["error"]}')

                except Exception as e:
                    logging.error(f"Error processing food image: {e}")
                    flash('Error processing image. Please try again with a clearer photo.', 'danger')
                    return render_template('food_analyzer.html')

        return render_template('food_analyzer.html')



    @app.route('/api/food-analysis', methods=['POST'])
    @login_required
    def food_analysis_api():
        try:
            # Get image data from request
            if 'image' not in request.files:
                return jsonify({'success': False, 'error': 'No image provided'})

            image_file = request.files['image']

            # Process image with food analysis
            result = gemini.analyze_food_image(image_file)

            return jsonify({'success': True, 'data': result})

        except Exception as e:
            logging.error(f"Error in food analysis API: {e}")
            return jsonify({'success': False, 'error': str(e)})



            db.session.add(workout)
            db.session.flush()  # Get the workout ID

            # Add exercises
            for exercise_data in data.get('exercises', []):
                exercise = Exercise(
                    workout_id=workout.id,
                    name=exercise_data.get('name', ''),
                    reps=exercise_data.get('reps', 0),
                    sets=exercise_data.get('sets', 1),
                    form_accuracy=exercise_data.get('form_accuracy', 0),
                    exercise_type=exercise_data.get('exercise_type', 'cardio')
                )
                db.session.add(exercise)

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Workout saved successfully',
                'workout_id': workout.id
            })

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving workout: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to save workout'
            })

    @app.route('/api/fitness-chat', methods=['POST'])
    @login_required
    def fitness_chat():
        try:
            data = request.get_json()
            question = data.get('question', '')

            if not question:
                return jsonify({'success': False, 'error': 'No question provided'})

            # Get user context
            user_context = f"Fitness level: {current_user.fitness_level}, Goals: {current_user.fitness_goals}"

            # Get AI response
            response = gemini.get_fitness_advice(question, user_context)

            return jsonify({'success': True, 'response': response})

        except Exception as e:
            logging.error(f"Error in fitness chat: {e}")
            return jsonify({'success': False, 'error': 'Sorry, I had trouble processing your request.'})

    @app.route('/api/dashboard-stats')
    @login_required
    def dashboard_stats():
        """Get dashboard statistics for charts"""
        try:
            # Get workout history for last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)

            workouts = Workout.query.filter(
                Workout.user_id == current_user.id,
                Workout.completed_at >= thirty_days_ago
            ).all()

            # Prepare data for charts
            workout_dates = []
            calories_burned = []

            for workout in workouts:
                workout_dates.append(workout.completed_at.strftime('%Y-%m-%d'))
                calories_burned.append(workout.calories_burned or 0)

            return jsonify({
                'success': True,
                'data': {
                    'workout_dates': workout_dates,
                    'calories_burned': calories_burned,
                    'total_workouts': len(workouts),
                    'avg_calories': sum(calories_burned) / len(calories_burned) if calories_burned else 0
                }
            })

        except Exception as e:
            logging.error(f"Error getting dashboard stats: {e}")
            return jsonify({'success': False, 'error': str(e)})



            workout = Workout(
                user_id=current_user.id,
                name=data.get('name', 'Custom Workout'),
                exercises=json.dumps(data.get('exercises', [])),
                duration=data.get('duration', 0),
                calories_burned=data.get('calories_burned', 0),
                difficulty=data.get('difficulty', 'medium')
            )

            db.session.add(workout)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Workout recorded successfully!'})

        except Exception as e:
            logging.error(f"Error recording workout: {e}")
            return jsonify({'success': False, 'error': str(e)})

    # All workout-related code has been removed

    @app.route('/api/save-food-log', methods=['POST'])
    @login_required
    def save_food_log():
        try:
            data = request.get_json()

            food_log = FoodLog(
                user_id=current_user.id,
                food_items=json.dumps(data.get('food_items', [])),
                total_calories=data.get('total_calories', 0),
                meal_type=data.get('meal_type', 'snack')
            )

            db.session.add(food_log)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Food log saved successfully!'})

        except Exception as e:
            logging.error(f"Error saving food log: {e}")
            return jsonify({'success': False, 'error': str(e)})

    # All workout-related code has been removed

    @app.route('/api/get-food-history')
    @login_required
    def get_food_history():
        try:
            food_logs = FoodLog.query.filter_by(user_id=current_user.id).order_by(FoodLog.logged_at.desc()).all()

            food_data = []
            for log in food_logs:
                food_data.append({
                    'id': log.id,
                    'food_items': json.loads(log.food_items) if log.food_items else [],
                    'total_calories': log.total_calories,
                    'meal_type': log.meal_type,
                    'logged_at': log.logged_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            return jsonify({'success': True, 'data': food_data})

        except Exception as e:
            logging.error(f"Error getting food history: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/update-profile', methods=['POST'])
    @login_required
    def update_profile():
        try:
            data = request.get_json()

            current_user.fitness_level = data.get('fitness_level', current_user.fitness_level)
            current_user.fitness_goals = data.get('fitness_goals', current_user.fitness_goals)

            db.session.commit()

            return jsonify({'success': True, 'message': 'Profile updated successfully!'})

        except Exception as e:
            logging.error(f"Error updating profile: {e}")
            return jsonify({'success': False, 'error': str(e)})



    @app.route('/api/delete-food-log/<int:log_id>', methods=['DELETE'])
    @login_required
    def delete_food_log(log_id):
        try:
            food_log = FoodLog.query.filter_by(id=log_id, user_id=current_user.id).first()

            if not food_log:
                return jsonify({'success': False, 'error': 'Food log not found'}), 404

            db.session.delete(food_log)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Food log deleted successfully!'})

        except Exception as e:
            logging.error(f"Error deleting food log: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/export-data')
    @login_required
    def export_data():
        try:
            # Get user's data
            workouts = Workout.query.filter_by(user_id=current_user.id).all()
            food_logs = FoodLog.query.filter_by(user_id=current_user.id).all()

            # Prepare export data
            export_data = {
                'user_info': {
                    'username': current_user.username,
                    'email': current_user.email,
                    'fitness_level': current_user.fitness_level,
                    'fitness_goals': current_user.fitness_goals
                },
                'workouts': [],
                'food_logs': []
            }

            for workout in workouts:
                export_data['workouts'].append({
                    'name': workout.name,
                    'duration': workout.duration,
                    'calories_burned': workout.calories_burned,
                    'completed_at': workout.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'difficulty': workout.difficulty
                })

            for log in food_logs:
                export_data['food_logs'].append({
                    'food_items': json.loads(log.food_items) if log.food_items else [],
                    'total_calories': log.total_calories,
                    'meal_type': log.meal_type,
                    'logged_at': log.logged_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            return jsonify({'success': True, 'data': export_data})

        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/import-data', methods=['POST'])
    @login_required
    def import_data():
        try:
            data = request.get_json()

            # Import workouts
            for workout_data in data.get('workouts', []):
                workout = Workout(
                    user_id=current_user.id,
                    name=workout_data.get('name', 'Imported Workout'),
                    duration=workout_data.get('duration', 0),
                    calories_burned=workout_data.get('calories_burned', 0),
                    difficulty=workout_data.get('difficulty', 'medium')
                )
                db.session.add(workout)

            # Import food logs
            for log_data in data.get('food_logs', []):
                food_log = FoodLog(
                    user_id=current_user.id,
                    food_items=json.dumps(log_data.get('food_items', [])),
                    total_calories=log_data.get('total_calories', 0),
                    meal_type=log_data.get('meal_type', 'snack')
                )
                db.session.add(food_log)

            db.session.commit()

            return jsonify({'success': True, 'message': 'Data imported successfully!'})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error importing data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/backup-data')
    @login_required
    def backup_data():
        try:
            # Get user's data
            workouts = Workout.query.filter_by(user_id=current_user.id).all()
            food_logs = FoodLog.query.filter_by(user_id=current_user.id).all()

            # Create backup data
            backup_data = {
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': current_user.id,
                'workouts': [],
                'food_logs': []
            }

            for workout in workouts:
                backup_data['workouts'].append({
                    'name': workout.name,
                    'duration': workout.duration,
                    'calories_burned': workout.calories_burned,
                    'completed_at': workout.completed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'difficulty': workout.difficulty
                })

            for log in food_logs:
                backup_data['food_logs'].append({
                    'food_items': json.loads(log.food_items) if log.food_items else [],
                    'total_calories': log.total_calories,
                    'meal_type': log.meal_type,
                    'logged_at': log.logged_at.strftime('%Y-%m-%d %H:%M:%S')
                })

            return jsonify({'success': True, 'data': backup_data})

        except Exception as e:
            logging.error(f"Error creating backup: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/restore-data', methods=['POST'])
    @login_required
    def restore_data():
        try:
            data = request.get_json()

            # Clear existing data
            Workout.query.filter_by(user_id=current_user.id).delete()
            FoodLog.query.filter_by(user_id=current_user.id).delete()

            # Restore workouts
            for workout_data in data.get('workouts', []):
                workout = Workout(
                    user_id=current_user.id,
                    name=workout_data.get('name', 'Restored Workout'),
                    duration=workout_data.get('duration', 0),
                    calories_burned=workout_data.get('calories_burned', 0),
                    difficulty=workout_data.get('difficulty', 'medium')
                )
                db.session.add(workout)

            # Restore food logs
            for log_data in data.get('food_logs', []):
                food_log = FoodLog(
                    user_id=current_user.id,
                    food_items=json.dumps(log_data.get('food_items', [])),
                    total_calories=log_data.get('total_calories', 0),
                    meal_type=log_data.get('meal_type', 'snack')
                )
                db.session.add(food_log)

            db.session.commit()

            return jsonify({'success': True, 'message': 'Data restored successfully!'})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error restoring data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/clear-data', methods=['POST'])
    @login_required
    def clear_data():
        try:
            # Clear all user data
            Workout.query.filter_by(user_id=current_user.id).delete()
            FoodLog.query.filter_by(user_id=current_user.id).delete()

            db.session.commit()

            return jsonify({'success': True, 'message': 'All data cleared successfully!'})

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error clearing data: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/health-check')
    def health_check():
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')})

    @app.route('/api/version')
    def version():
        return jsonify({'version': '1.0.0', 'name': 'VisionFitAI'})

    @app.route('/api/pose-detection', methods=['POST'])
    @login_required
    def pose_detection_api():
        try:
            # Get image data from request
            if 'image' not in request.files and 'image_data' not in request.form:
                return jsonify({'success': False, 'error': 'No image provided'})

            # Process image data
            if 'image' in request.files:
                image_file = request.files['image']
                image_data = image_file.read()
            else:
                # Handle base64 encoded image
                image_data = base64.b64decode(request.form['image_data'].split(',')[1])

            # Get exercise type
            exercise_type = request.form.get('exercise_type', 'pushup')

            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Use PoseDetector to process the image
            detector = PoseDetector()
            result = detector.process_image(img)

            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Pose detection successful',
                    'landmarks': result.get('landmarks', [])
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('message', 'Failed to detect pose')
                })

        except Exception as e:
            logging.error(f"Error in pose detection API: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/docs')
    def api_docs():
        return jsonify({
            'endpoints': [
                '/api/pose-detection',
                '/api/food-analysis',
                '/api/fitness-chat',
                '/api/dashboard-stats',
                '/api/complete-workout',
                '/api/save-food-log',
                '/api/get-workout-history',
                '/api/get-food-history',
                '/api/update-profile',
                '/api/delete-workout/<id>',
                '/api/delete-food-log/<id>',
                '/api/export-data',
                '/api/import-data',
                '/api/backup-data',
                '/api/restore-data',
                '/api/clear-data',
                '/api/health-check',
                '/api/version',
                '/api/docs'
            ]
        })


