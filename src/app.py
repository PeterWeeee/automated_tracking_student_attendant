import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from src.config import Config
from src.services.ai_worker import start_ai_worker, load_ai_data_from_db
from src.routes.api_routes import api_bp
from src.routes.web_routes import web_bp

def create_app():
    app = Flask(__name__, template_folder=Config.TEMPLATE_DIR, static_folder=Config.STATIC_DIR)
    app.secret_key = Config.SECRET_KEY
    app.json.ensure_ascii = False

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)

    # Initialize data and background tasks
    load_ai_data_from_db()
    start_ai_worker()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
