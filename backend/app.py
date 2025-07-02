from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Import blueprints
from templates import templates_bp
from documentation import documentation_bp
from importexport import importexport_bp
from aiworkflow import aiworkflow_bp
from manualworkflow import manualworkflow_bp

# Load environment variables
load_dotenv()

# Create Flask application
app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(templates_bp, url_prefix='/templates')
app.register_blueprint(documentation_bp, url_prefix='/documentation')
app.register_blueprint(importexport_bp, url_prefix='/importexport')
app.register_blueprint(aiworkflow_bp, url_prefix='/aiworkflow')
app.register_blueprint(manualworkflow_bp, url_prefix='/manualworkflow')

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
