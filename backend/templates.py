from flask import Blueprint, request, jsonify
import os
import json
import time
from datetime import datetime

templates_bp = Blueprint('templates', __name__)

@templates_bp.route('/save_template', methods=['POST'])
def save_template():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'technologies', 'workflowOrder', 'useCase']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Generate a unique template ID
        template_id = f"template_{int(time.time())}"
        
        # Add metadata and all workflow information
        template_data = {
            "templateId": template_id,
            "createdDate": datetime.now().isoformat(),
            "lastModified": datetime.now().isoformat(),
            "name": data.get('name'),
            "category": data.get('category'),
            "technologies": data.get('technologies', []),
            "workflowOrder": data.get('workflowOrder', []),
            "useCase": data.get('useCase'),
            "narrative": data.get('narrative', ''),
            "environment": data.get('environment', 'saas_dev'),
            "userCode": data.get('userCode', 'LBA'),
            "folderName": data.get('folderName', 'demo-genai'),
            "application": data.get('application', 'demo-genai'),
            "subApplication": data.get('subApplication', 'demo-genai')
        }

        # Save template to a JSON file
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        template_file = os.path.join(templates_dir, f"{template_id}.json")
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)

        return jsonify({
            "message": "Template saved successfully",
            "templateId": template_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@templates_bp.route('/list_templates', methods=['GET'])
def list_templates():
    try:
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            return jsonify({"templates": []}), 200

        templates = []
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(templates_dir, filename), 'r') as f:
                        template_data = json.load(f)
                        templates.append(template_data)
                except Exception as e:
                    continue

        # Sort templates by last modified date
        templates.sort(key=lambda x: x.get('lastModified', ''), reverse=True)
        
        return jsonify({"templates": templates}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@templates_bp.route('/delete_template', methods=['POST'])
def delete_template():
    try:
        data = request.json
        template_id = data.get('templateId')
        
        if not template_id:
            return jsonify({"error": "Template ID is required"}), 400
        
        template_file = os.path.join("templates", f"{template_id}.json")
        
        if not os.path.exists(template_file):
            return jsonify({"error": "Template not found"}), 404

        os.remove(template_file)
        
        return jsonify({"message": "Template deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@templates_bp.route('/check_template_exists', methods=['POST'])
def check_template_exists():
    try:
        data = request.json
        template_name = data.get('name')
        template_category = data.get('category')
        
        if not template_name or not template_category:
            return jsonify({"error": "Template name and category are required"}), 400
        
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            return jsonify({"exists": False}), 200

        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(templates_dir, filename), 'r') as f:
                        template_data = json.load(f)
                        if (template_data.get('name') == template_name and 
                            template_data.get('category') == template_category):
                            return jsonify({
                                "exists": True,
                                "templateId": template_data.get('templateId')
                            }), 200
                except Exception as e:
                    continue

        return jsonify({"exists": False}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@templates_bp.route('/update_template', methods=['POST'])
def update_template():
    try:
        data = request.json
        template_id = data.get('templateId')
        
        if not template_id:
            return jsonify({"error": "Template ID is required"}), 400
        
        # Load existing template to preserve metadata
        template_file = os.path.join("templates", f"{template_id}.json")
        if not os.path.exists(template_file):
            return jsonify({"error": "Template not found"}), 404

        with open(template_file, 'r') as f:
            existing_template = json.load(f)

        # Update template data while preserving metadata
        updated_template = {
            **existing_template,  # Keep existing metadata
            "name": data.get('name'),
            "category": data.get('category'),
            "technologies": data.get('technologies'),
            "workflowOrder": data.get('workflowOrder'),
            "useCase": data.get('useCase'),
            "narrative": data.get('narrative'),
            "environment": data.get('environment'),
            "userCode": data.get('userCode'),
            "folderName": data.get('folderName'),
            "application": data.get('application'),
            "subApplication": data.get('subApplication'),
            "lastModified": datetime.now().isoformat()  # Update last modified date
        }

        # Save updated template
        with open(template_file, 'w') as f:
            json.dump(updated_template, f, indent=2)

        return jsonify({
            "message": "Template updated successfully",
            "templateId": template_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500 