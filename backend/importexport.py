from flask import Blueprint, request, jsonify, Response
import json
import base64
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from ctm_python_client.core.workflow import *
from ctm_python_client.core.credential import *
from ctm_python_client.core.comm import *
from aapi import *
from my_secrets import *
from job_library import JOB_LIBRARY
import docx
import PyPDF2
import pdfplumber
import time
import pandas as pd
import io

load_dotenv()

# GitHub Config (store token securely in .env)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found in environment variables. Please set GITHUB_TOKEN in your .env file.")
REPO_OWNER = "BMCDBA-Presales"
REPO_NAME = "GEN-AI-demo-generator"  # Replace with your repo name
BRANCH = "main"
BASE_FOLDER_PATH = "jobs"  # Folder where files will be uploaded

importexport_bp = Blueprint('importexport', __name__)

def connect_to_github(file_path, content, message):
    """Uploads a file to GitHub repository using GitHub API."""
    if not GITHUB_TOKEN:
        return {"status": "error", "message": "GitHub token is not configured"}

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        # Get the SHA if the file exists (needed for updates)
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            # File doesn't exist yet, that's okay
            sha = None
        elif response.status_code != 200:
            error_msg = response.json().get("message", "Unknown error")
            return {"status": "error", "message": f"Error checking file existence: {error_msg}"}
        else:
            sha = response.json().get("sha")

        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": BRANCH,
        }
        if sha:
            data["sha"] = sha  # Required for updates

        upload_response = requests.put(url, headers=headers, data=json.dumps(data))
        
        if upload_response.status_code in [200, 201]:
            return {"status": "success", "file": file_path}
        else:
            error_msg = upload_response.json().get("message", "Unknown error")
            return {"status": "error", "message": f"Error uploading file: {error_msg}"}
    except Exception as e:
        return {"status": "error", "message": f"Exception during upload: {str(e)}"}


@importexport_bp.route('/download_workflow', methods=['POST'])
def download_workflow():
    data = request.get_json()
    
    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' in request."}), 400

    requested_jobs = data['jobs']
    environment = data.get('environment', 'saas_dev')
    folder_name = data.get('folder_name', 'LBA_demo-genai')
    user_code = data.get('user_code', 'LBA')

    # Validate environment
    valid_environments = ['saas_dev', 'saas_preprod', 'saas_prod', 'vse_dev', 'vse_qa', 'vse_prod']
    if environment not in valid_environments:
        return jsonify({"error": f"Invalid environment. Must be one of: {valid_environments}"}), 400

    # Set Control-M server based on environment
    if environment.startswith('saas'):
        controlm_server = "IN01"
    elif environment == 'vse_dev':
        controlm_server = "DEV"
    elif environment == 'vse_qa':
        controlm_server = "QA"
    elif environment == 'vse_prod':
        controlm_server = "PROD"
    else:
        return jsonify({"error": "Invalid environment configuration"}), 400

    # Format folder and application names with user code
    formatted_folder_name = f"{user_code}_demo-genai"
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    # ENV & defaults
    my_env = Environment.create_saas(
        endpoint=my_secrets[f'{environment}_endpoint'],
        api_key=my_secrets[f'{environment}_api_key']
    )

    defaults = WorkflowDefaults(
        run_as="ctmagent",
        host="demogenai",
        application=formatted_application,
        sub_application=formatted_sub_application
    )

    workflow = Workflow(my_env, defaults=defaults)
    folder = Folder(formatted_folder_name, site_standard="lba_DemoGen AI", controlm_server=controlm_server)
    workflow.add(folder)

    job_paths = []

    for job_key in requested_jobs:
        if job_key not in JOB_LIBRARY:
            return jsonify({"error": f"Unknown job: {job_key}"}), 400

        job = JOB_LIBRARY[job_key]()
        workflow.add(job, inpath=formatted_folder_name)
        job_paths.append(f"{formatted_folder_name}/{job.object_name}")

    #Chaining jobs
    for i in range(len(job_paths) - 1):
        workflow.connect(job_paths[i], job_paths[i + 1])

    raw_json = workflow.dumps_json()
    
    # Return the JSON with appropriate headers for download
    return Response(
        raw_json,
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=workflow_{formatted_folder_name}.json'
        }
    )


@importexport_bp.route('/upload_workflow', methods=['POST'])
def upload_workflow():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({"error": "File must be a JSON file"}), 400

        # Read and parse the JSON file
        try:
            file_content = file.read().decode('utf-8')
            workflow_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            return jsonify({"error": "Invalid JSON file"}), 400

        # Validate the workflow structure
        if not isinstance(workflow_data, dict):
            return jsonify({"error": "Invalid workflow format"}), 400

        # Extract job information from object names
        jobs = []
        folder_name = next(iter(workflow_data.keys()))  # Get the folder name
        
        # Get all keys that start with 'zzt-'
        object_names = [key for key in workflow_data[folder_name].keys() if key.startswith('zzt-')]

        # Validate each object name against JOB_LIBRARY
        for obj_name in object_names:
            # Remove the 'zzt-' prefix to get the base name
            base_name = obj_name[4:]  # Remove 'zzt-' prefix
            
            # Find matching job in JOB_LIBRARY
            found_job = None
            for job_name, job_class in JOB_LIBRARY.items():
                # Create an instance of the job to check its object_name
                job_instance = job_class()
                if job_instance.object_name == obj_name:
                    found_job = job_name
                    break
            
            if found_job:
                jobs.append(found_job)

        if not jobs:
            return jsonify({"error": "No valid jobs found in the workflow"}), 400
        
        return jsonify({
            "message": "Workflow uploaded successfully",
            "jobs": jobs,
            "workflow_data": workflow_data
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@importexport_bp.route("/upload-github", methods=["POST"])
def upload_github():
    """Endpoint to upload workflow and narrative files to GitHub."""
    try:
        if not GITHUB_TOKEN:
            return jsonify({"error": "GitHub token is not configured"}), 500

        data = request.json
        narrative_text = data.get("narrative_text", "")
        user_code = data.get("user_info", "unknown_user")

        if not narrative_text:
            return jsonify({"error": "Missing narrative"}), 400

        # Read the output.json file
        try:
            with open("output.json", "r") as f:
                workflow_json = f.read()
        except Exception as e:
            return jsonify({"error": f"Failed to read output.json: {str(e)}"}), 500

        # Generate a unique folder name (Timestamp format: YYYY-MM-DD_HH-MM-SS)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{BASE_FOLDER_PATH}/{user_code}_workflow_{timestamp}"

        # Define file paths inside this user-specific folder
        workflow_file = f"{folder_name}/{user_code}_workflow.json"
        narrative_file = f"{folder_name}/{user_code}_narrative.txt"
        metadata_file = f"{folder_name}/{user_code}_metadata.txt"

        # Upload both files
        upload_workflow = connect_to_github(workflow_file, workflow_json, "Added workflow JSON")
        if upload_workflow["status"] == "error":
            return jsonify({"error": upload_workflow["message"]}), 500

        upload_narrative = connect_to_github(narrative_file, narrative_text, "Added workflow narrative")
        if upload_narrative["status"] == "error":
            return jsonify({"error": upload_narrative["message"]}), 500

        # Optional: Upload metadata (user info, timestamp, etc.)
        metadata_content = f"Upload Time: {timestamp}\nUser Code: {user_code}"
        upload_metadata = connect_to_github(metadata_file, metadata_content, "Added metadata")
        if upload_metadata["status"] == "error":
            return jsonify({"error": upload_metadata["message"]}), 500

        return jsonify({
            "workflow": upload_workflow,
            "narrative": upload_narrative,
            "metadata": upload_metadata
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@importexport_bp.route("/analyze_documentation", methods=["POST"])
def analyze_documentation():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        use_case = request.form.get('use_case', '')
        
        if not file:
            return jsonify({"error": "No file selected"}), 400
            
        if not file.filename.endswith(('.txt', '.doc', '.docx', '.pdf', '.xlsx', '.xls')):
            return jsonify({"error": "Invalid file format. Please upload .txt, .doc, .docx, .pdf, .xlsx, or .xls files"}), 400

        # Read file content based on file type
        file_content = ""
        try:
            if file.filename.endswith('.txt'):
                file_content = file.read().decode('utf-8')
            elif file.filename.endswith(('.doc', '.docx')):
                # Save the file temporarily
                temp_path = f"temp_{int(time.time())}.docx"
                file.save(temp_path)
                
                # Read the Word document
                doc = docx.Document(temp_path)
                file_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                # Clean up temporary file
                os.remove(temp_path)
                
            elif file.filename.endswith('.pdf'):
                # Save the file temporarily
                temp_path = f"temp_{int(time.time())}.pdf"
                file.save(temp_path)
                
                # Try using pdfplumber first (better for text extraction)
                try:
                    with pdfplumber.open(temp_path) as pdf:
                        file_content = "\n".join([page.extract_text() for page in pdf.pages])
                except Exception as e:
                    # Fallback to PyPDF2
                    with open(temp_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        file_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                
                # Clean up temporary file
                os.remove(temp_path)
                
            elif file.filename.endswith(('.xlsx', '.xls')):
                # Read Excel file
                try:
                    # Read all sheets from the Excel file
                    excel_data = pd.read_excel(file, sheet_name=None)
                    
                    # Combine all sheet data into a single text representation
                    excel_content_parts = []
                    
                    for sheet_name, df in excel_data.items():
                        excel_content_parts.append(f"Sheet: {sheet_name}")
                        excel_content_parts.append("Column Headers: " + ", ".join(df.columns.tolist()))
                        excel_content_parts.append("Data Preview:")
                        
                        # Get first 10 rows as preview
                        preview_rows = df.head(10)
                        for index, row in preview_rows.iterrows():
                            row_data = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                            excel_content_parts.append(f"Row {index}: {row_data}")
                        
                        excel_content_parts.append(f"Total Rows: {len(df)}")
                        excel_content_parts.append("---")
                    
                    file_content = "\n".join(excel_content_parts)
                    
                except Exception as e:
                    return jsonify({"error": f"Error reading Excel file: {str(e)}"}), 500
                
        except Exception as e:
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500

        if not file_content.strip():
            return jsonify({"error": "No readable content found in the file"}), 400

        # Get list of available technologies from JOB_LIBRARY
        available_technologies = list(JOB_LIBRARY.keys())
        
        # Import OpenAI client here to avoid circular imports
        from openai import AzureOpenAI
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Load Azure OpenAI credentials from .env
        azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
        azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        # Initialize Azure OpenAI client
        client = AzureOpenAI(
            api_key=azure_openai_key,
            api_version=azure_openai_api_version,
            azure_endpoint=azure_openai_endpoint
        )
        
        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an AI assistant that analyzes documentation to extract workflow requirements and technologies.
                    Your response must be in JSON format with this structure:
                    {{
                        "extracted_use_case": "Detailed use case extracted from documentation",
                        "suggested_technologies": ["Technology1", "Technology2", "Technology3", "Technology4", "Technology5", "Technology6", "Technology7", "Technology8", "Technology9", "Technology10"],
                        "workflow_order": ["Technology1", "Technology2", "Technology3", "Technology4", "Technology5", "Technology6", "Technology7", "Technology8", "Technology9", "Technology10"],
                        "analysis_summary": "Brief summary of the analysis",
                        "technologies_for_manual_workflow": ["Technology1", "Technology2", "Technology3", "Technology4", "Technology5", "Technology6", "Technology7", "Technology8", "Technology9", "Technology10"]
                    }}
                    
                    CRITICAL REQUIREMENTS:
                    1. You MUST suggest AT LEAST 10 technologies from this exact list: {available_technologies}
                    2. Do NOT suggest technologies that are not in the provided list
                    3. Extract the most relevant use case details from the documentation
                    4. Consider both the provided use case and the documentation content
                    5. Suggest technologies that best match the requirements and create a comprehensive workflow
                    6. Provide a logical workflow order based on dependencies
                    7. The "technologies_for_manual_workflow" field should contain the same technologies as "suggested_technologies" - this is for direct input to the manual workflow generation
                    8. For Excel files, analyze the data structure, column headers, and data patterns to understand the workflow requirements
                    9. If the documentation doesn't clearly indicate 10 technologies, select additional relevant technologies from the list to create a comprehensive workflow
                    10. Ensure the workflow covers data ingestion, processing, storage, analysis, and reporting phases
                    11. Return ONLY the JSON object, no additional text
                    
                    TECHNOLOGY SELECTION STRATEGY:
                    - Always include data processing technologies (AWS_Glue, Azure_Databricks, GCP_Dataflow, etc.)
                    - Include database/storage technologies (AWS_Redshift, Azure_Synapse, GCP_BigQuery, etc.)
                    - Include orchestration technologies (AWS_StepFunctions, GCP_Workflows, etc.)
                    - Include monitoring/notification technologies (AWS_SNS, AWS_SQS, etc.)
                    - Include compute technologies (AWS_EC2, Azure_VM, GCP_VM, etc.)
                    - Include serverless technologies (AWS_Lambda, Azure_Functions, etc.)
                    - Include integration technologies (AWS_AppFlow, Azure_LogicApps, etc.)
                    - Include backup/security technologies (AWS_Backup, etc.)
                    - Include analytics/BI technologies (AWS_QuickSight, MS_PowerBI, Tableau, etc.)
                    - Include DevOps technologies (AZURE_DevOps, Jenkins, etc.)"""
                },
                {
                    "role": "user",
                    "content": f"""Analyze this documentation and use case to extract workflow requirements and suggest technologies:
                    
                    Documentation Content:
                    {file_content}
                    
                    Additional Use Case Context:
                    {use_case}
                    
                    File Type: {file.filename.split('.')[-1].upper()}
                    
                    CRITICAL REQUIREMENTS:
                    - You MUST suggest AT LEAST 10 technologies from this list: {available_technologies}
                    - Do NOT suggest technologies outside this list
                    - Create a comprehensive workflow that covers multiple phases (ingestion, processing, storage, analysis, reporting)
                    - If the documentation doesn't clearly indicate 10 technologies, select additional relevant technologies to create a complete workflow
                    
                    Return ONLY a JSON object with the extracted use case, suggested technologies (minimum 10), workflow order, analysis summary, and technologies_for_manual_workflow array."""
                }
            ]
        )

        response_content = completion.choices[0].message.content.strip()
        
        try:
            # Extract JSON from response
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            json_str = response_content[start:end]
            analysis_result = json.loads(json_str)
            
            # Verify that all suggested technologies are valid
            valid_technologies = [tech for tech in analysis_result['suggested_technologies'] 
                                if tech in available_technologies]
            
            if not valid_technologies:
                return jsonify({"error": "No valid technologies found in the analysis"}), 400
            
            # Ensure we have at least 10 technologies
            if len(valid_technologies) < 10:
                # Add more technologies from the available list to reach minimum of 10
                remaining_technologies = [tech for tech in available_technologies if tech not in valid_technologies]
                
                # Prioritize technologies by category to ensure comprehensive coverage
                priority_technologies = []
                
                # Add data processing technologies first
                data_processing_techs = ['AWS_Glue', 'Azure_Databricks', 'GCP_Dataflow', 'AWS_EMR', 'GCP_Dataproc']
                for tech in data_processing_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add database/storage technologies
                database_techs = ['AWS_Redshift', 'Azure_Synapse', 'GCP_BigQuery', 'AWS_DynamoDB', 'AWS_Athena']
                for tech in database_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add orchestration technologies
                orchestration_techs = ['AWS_StepFunctions', 'GCP_Workflows', 'GCP_Composer', 'Apache_Airflow']
                for tech in orchestration_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add monitoring/notification technologies
                monitoring_techs = ['AWS_SNS', 'AWS_SQS', 'AZURE_Service_Bus']
                for tech in monitoring_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add compute technologies
                compute_techs = ['AWS_EC2', 'Azure_VM', 'GCP_VM', 'OCI_VM']
                for tech in compute_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add serverless technologies
                serverless_techs = ['AWS_Lambda', 'AZURE_Functions', 'GCP_Functions']
                for tech in serverless_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add integration technologies
                integration_techs = ['AWS_AppFlow', 'AZURE_LogicApps', 'GCP_CloudRun']
                for tech in integration_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add analytics/BI technologies
                analytics_techs = ['AWS_QuickSight', 'MS_PowerBI', 'Tableau', 'DBT']
                for tech in analytics_techs:
                    if tech in remaining_technologies and tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Add any remaining technologies to fill up to 10
                for tech in remaining_technologies:
                    if tech not in priority_technologies:
                        priority_technologies.append(tech)
                
                # Take only what we need to reach 10 technologies
                needed_count = 10 - len(valid_technologies)
                additional_technologies = priority_technologies[:needed_count]
                
                # Combine original valid technologies with additional ones
                valid_technologies.extend(additional_technologies)
                
                # Update the analysis result
                analysis_result['suggested_technologies'] = valid_technologies
                analysis_result['workflow_order'] = valid_technologies  # Use the same order for workflow
                analysis_result['analysis_summary'] += f" Note: Added {len(additional_technologies)} additional technologies to ensure comprehensive workflow coverage."
                
            analysis_result['suggested_technologies'] = valid_technologies
            analysis_result['workflow_order'] = [tech for tech in analysis_result['workflow_order'] 
                                               if tech in valid_technologies]
            
            # Ensure technologies_for_manual_workflow is properly set
            if 'technologies_for_manual_workflow' not in analysis_result:
                analysis_result['technologies_for_manual_workflow'] = valid_technologies
            else:
                # Validate and clean the technologies_for_manual_workflow array
                valid_manual_technologies = [tech for tech in analysis_result['technologies_for_manual_workflow'] 
                                           if tech in available_technologies]
                analysis_result['technologies_for_manual_workflow'] = valid_manual_technologies
            
            return jsonify(analysis_result), 200
            
        except json.JSONDecodeError as e:
            return jsonify({"error": "Failed to parse AI response"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500 