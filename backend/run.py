"""
Flask Application Factory and Server Entry Point for MORROW.

Initializes Flask, enables CORS, registers route blueprints under /api/v1,
initializes the database connection, loads the ML artifact on startup,
and starts the local server.

Usage:
    python -m backend.run
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import Config
from backend.database import init_db
from backend.services.model_service import init_model
from backend.routes.health_routes import health_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.appointment_routes import appointment_bp
from backend.routes.prediction_routes import prediction_bp
from backend.routes.model_routes import model_bp
from backend.routes.data_quality_routes import data_quality_bp


def create_app(config_class=Config):
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS for all routes (frontend on localhost:5173 or other ports)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints with /api/v1 prefix
    api_prefix = "/api/v1"
    app.register_blueprint(health_bp, url_prefix=api_prefix)
    app.register_blueprint(dashboard_bp, url_prefix=api_prefix)
    app.register_blueprint(appointment_bp, url_prefix=api_prefix)
    app.register_blueprint(prediction_bp, url_prefix=api_prefix)
    app.register_blueprint(model_bp, url_prefix=api_prefix)
    app.register_blueprint(data_quality_bp, url_prefix=api_prefix)

    # Root route
    @app.route("/")
    def index():
        return jsonify({
            "service": "MORROW — Appointment Operations & No-Show Intelligence",
            "version": "1.0.0",
            "documentation": f"{api_prefix}/health",
        })

    # 404 error handler
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    # 500 error handler
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    # Initialize database connection and load ML model artifact ONCE on startup
    with app.app_context():
        init_db(app)
        init_model()

    return app


def main():
    app = create_app()
    port = Config.FLASK_PORT
    debug = Config.FLASK_DEBUG
    print(f"\n============================================================")
    print(f"MORROW Backend Server starting on port {port} (Debug: {debug})")
    print(f"API endpoints registered at http://localhost:{port}/api/v1/")
    print(f"============================================================\n")
    app.run(host="0.0.0.0", port=port, debug=debug)


if __name__ == "__main__":
    main()

