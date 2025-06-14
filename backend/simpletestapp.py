from flask import Flask, request, jsonify, Response
from ctm_python_client.core.workflow import *
from ctm_python_client.core.credential import *
from ctm_python_client.core.comm import *
from aapi import *
from my_secrets import *
import subprocess
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from openai import AzureOpenAI  
from job_library import JOB_LIBRARY
import time
from datetime import datetime

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



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/generate_workflow', methods=['POST'])
def generate_workflow():
    data = request.get_json()
    
    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' in request."}), 400

    jobs_data = data['jobs']
    environment = data.get('environment', 'saas_dev')
    folder_name = data.get('folder_name', 'LBA_DEMGEN_VB')
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
    formatted_folder_name = f"{user_code}_{folder_name}"
    formatted_application = f"{user_code}-DMO-GEN"
    formatted_sub_application = f"{user_code}-TEST-APP"

    # ENV & defaults
    my_env = Environment.create_saas(
        endpoint=my_secrets[f'{environment}_endpoint'],
        api_key=my_secrets[f'{environment}_api_key']
    )

    defaults = WorkflowDefaults(
        run_as="ctmagent",
        host="zzz-linux-agents",
        application=formatted_application,
        sub_application=formatted_sub_application
    )

    workflow = Workflow(my_env, defaults=defaults)
    folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
    workflow.add(folder)

    # Group jobs by y-coordinate to identify concurrent jobs
    y_coordinates = {}
    for job_data in jobs_data:
        y = job_data['position']['y']
        if y not in y_coordinates:
            y_coordinates[y] = []
        y_coordinates[y].append(job_data)

    # Create concurrent groups
    concurrent_groups = []
    for y, jobs_at_y in y_coordinates.items():
        if len(jobs_at_y) > 1:
            concurrent_groups.append({
                'id': f'group_{y}',
                'jobs': [job['id'] for job in jobs_at_y]
            })

    # Process jobs and create dependencies
    job_instances = {}
    dependencies = []

    for job_data in jobs_data:
        job_id = job_data['id']
        job_type = job_data['type']
        
        if job_type not in JOB_LIBRARY:
            return jsonify({"error": f"Unknown job type: {job_type}"}), 400

        # Create job instance
        job = JOB_LIBRARY[job_type]()
        job.object_name = f"zzt-{job_data['name']}"
        workflow.add(job, inpath=formatted_folder_name)
        job_instances[job_id] = job

        # Handle dependencies
        if job_data['dependencies']:
            dependencies.append({
                'job': job_id,
                'depends_on': job_data['dependencies']
            })
            # Add wait events for dependencies
            wait_events = [Event(event=f"{dep}_COMPLETE") for dep in job_data['dependencies']]
            job.wait_for_events.append(WaitForEvents(wait_events))

    # Add completion events for concurrent groups
    for group in concurrent_groups:
        completion_event = f"{group['id']}_COMPLETE"
        for job_id in group['jobs']:
            if job_id in job_instances:
                job_instances[job_id].events_to_add.append(AddEvents([Event(event=completion_event)]))

    # Connect jobs based on dependencies
    for dep in dependencies:
        for dep_id in dep['depends_on']:
            if dep_id in job_instances and dep['job'] in job_instances:
                workflow.connect(
                    f"{formatted_folder_name}/{job_instances[dep_id].object_name}",
                    f"{formatted_folder_name}/{job_instances[dep['job']].object_name}"
                )

    raw_json = workflow.dumps_json()

    # Save JSON to output.json
    output_file = "output.json"
    with open(output_file, "w") as f:
        f.write(raw_json)

    # Check for build and deploy errors
    build_errors = workflow.build().errors
    deploy_errors = workflow.deploy().errors

    # If no errors, run CLI commands
    deployment_status = {"success": False, "message": "", "errors": []}
    
    if build_errors is None and deploy_errors is None:
        try:
            # Run the Control-M CLI commands
            build_result = subprocess.run(["ctm", "build", output_file], capture_output=True, text=True, check=True)
            deploy_result = subprocess.run(["ctm", "deploy", output_file], capture_output=True, text=True, check=True)
            
            deployment_status = {
                "success": True,
                "message": "Workflow successfully built and deployed",
                "build_output": build_result.stdout,
                "deploy_output": deploy_result.stdout
            }
        except subprocess.CalledProcessError as e:
            deployment_status = {
                "success": False,
                "message": f"Error during deployment: {str(e)}",
                "errors": [e.stderr] if e.stderr else []
            }
    else:
        deployment_status = {
            "success": False,
            "message": "Workflow validation failed",
            "errors": [build_errors, deploy_errors]
        }

    # Prepare response
    response = {
        "workflow": {
            "name": formatted_folder_name,
            "jobs": [
                {
                    "id": job_id,
                    "name": job_data['name'],
                    "type": job_data['type'],
                    "object_name": job_instances[job_id].object_name
                }
                for job_id, job_data in zip(job_instances.keys(), jobs_data)
            ],
            "concurrent_groups": concurrent_groups,
            "dependencies": dependencies
        },
        "deployment": deployment_status,
        "raw_json": raw_json
    }

    return jsonify(response), 200


@app.route("/generate_optimal_order", methods=["POST"])
def generate_optimal_order():
    """
    Generate an optimized order for selected technologies based on a use case using GPT.
    """
    try:
        data = request.get_json()
        app.logger.info(f"Received Data: {json.dumps(data, indent=2)}")

        technologies = data.get("technologies")
        use_case = data.get("use_case")

        if not technologies or not use_case:
            return jsonify({"error": "Technologies and use case are required."}), 400

        # Use the OpenAI client to determine optimal order
        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert BMC Control-M workflow architect that determines the optimal execution order of technologies based on technical dependencies and business requirements.

                    CRITICAL RULES:
                    1. You MUST include ALL technologies provided in your response
                    2. Do not add or remove any technologies
                    3. Order technologies based on these technical principles:
                       - Data dependencies (which jobs need data from other jobs)
                       - Resource dependencies (which jobs need resources from other jobs)
                       - Logical flow (which jobs must complete before others can start)
                       - Error handling and recovery considerations
                       - Performance optimization
                    4. The order must be technically sound and follow BMC Control-M best practices
                    5. The same input (technologies + use case) must ALWAYS produce the same optimal order
                    6. Consider the use case's specific requirements when determining dependencies
                    7. Return the exact same technologies, just in the optimal technical order

                    Your response must be deterministic - the same input must always produce the same output."""
                },
                {
                    "role": "user",
                    "content": f"""Analyze these technologies and determine their optimal execution order based on the use case:
                    Technologies: {technologies}
                    Use Case: {use_case}

                    Consider:
                    1. Technical dependencies between jobs
                    2. Data flow requirements
                    3. Resource dependencies
                    4. Error handling needs
                    5. Performance optimization
                    6. Use case specific requirements

                    Provide the optimal order in JSON format: {{"workflow_order": ["Technology1", "Technology2"]}}
                    Remember to include ALL technologies in your response."""
                }
            ]
        )

        response_content = completion.choices[0].message.content.strip()
        app.logger.info(f"GPT Response: {response_content}")

        def extract_json_from_response(text):
            try:
                start = text.find('{')
                end = text.rfind('}') + 1
                return json.loads(text[start:end])
            except Exception as e:
                app.logger.error(f"Error parsing GPT JSON: {e}")
                return None

        ordered_workflow = extract_json_from_response(response_content)
        if ordered_workflow:
            # Verify that all technologies are included in the response
            workflow_order = ordered_workflow.get("workflow_order", [])
            if set(workflow_order) == set(technologies):
                return jsonify({"optimal_order": workflow_order}), 200
            else:
                app.logger.warning("AI response missing some technologies, using original order")
                return jsonify({"optimal_order": technologies}), 200
        else:
            return jsonify({"optimal_order": technologies}), 200

    except Exception as e:
        app.logger.error(f"Exception in /generate: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate-narrative", methods=["POST"])
def generate_narrative():
    try: 
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400
        
        app.logger.info(f"📝 Generating Narrative with:")
        app.logger.info(f"Technologies: {technologies}")
        app.logger.info(f"Use Case: {use_case}")
        app.logger.info(f"Ordered Workflow: {ordered_workflow}")

        def generate_stream():
            try:
                completion = client.chat.completions.create(
                    model=azure_openai_deployment,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an AI assistant that generates structured, professional narratives for BMC Control-M workflows.
                            Your response must follow this exact structure and formatting:
                            
                            # Workflow Name
                            [A concise, descriptive name based on the use case]

                            ## Introduction
                            [A brief overview of the workflow's purpose and business value]

                            ## Use Case Overview
                            [High-level description of the business need and objectives]

                            ## Technical Implementation
                            [Detailed technical explanation of how the workflow operates, including:
                            - Data flow between jobs
                            - Dependencies and relationships
                            - Error handling and recovery
                            - Performance considerations]

                            ## Job Types and Technologies
                            [List of the Job Types in the workflow:
                            1. [Technology Name]
                            
                            2. [Technology Name]

                            And so on for each technology...]

                            Format your response with clear section headers and professional, technical language.
                            Use markdown formatting for better readability."""
                        },
                        {
                            "role": "user",
                            "content": f"""Generate a structured narrative for the following workflow:
                            Technologies: {technologies}
                            Workflow Order: {ordered_workflow}
                            Use Case: {use_case}
                            
                            Follow the exact structure provided, with clear section headers."""
                        }
                    ],
                    stream=True
                )

                for chunk in completion:
                    if chunk.choices and hasattr(chunk.choices[0], "delta"):
                        content = getattr(chunk.choices[0].delta, "content", None)
                        if content:
                            yield content
            except Exception as e:
                app.logger.error(f"❌ Error during streaming: {str(e)}")
                yield json.dumps({"error": str(e)})

        return Response(generate_stream(), content_type="text/plain")

    except Exception as e:
        app.logger.error(f"❌ Error generating narrative: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/proposed_workflow", methods=["POST"])
def proposed_workflow():
    try:
        data = request.json
        use_case = data.get("use_case")

        if not use_case:
            return jsonify({"error": "Use case is required."}), 400
        
        app.logger.info(f"🤖 Generating Proposed Workflow for Use Case: {use_case}")

        def generate_stream():
            try:
                # Get list of available technologies from JOB_LIBRARY
                available_technologies = list(JOB_LIBRARY.keys())
                
                completion = client.chat.completions.create(
                    model=azure_openai_deployment,
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are an AI assistant that suggests optimal technology workflows for BMC Control-M based on business use cases.
                            You MUST ONLY suggest technologies from this exact list: {available_technologies}
                            Your response should be in JSON format with this structure:
                            {{
                                "technologies": ["Technology1", "Technology2"],
                                "workflow_order": ["Technology1", "Technology2"]
                            }}
                            IMPORTANT: 
                            1. Only use technologies from the provided list
                            2. Return ONLY the JSON object, no markdown formatting, no code blocks, no additional text
                            3. Make sure the response is valid JSON"""
                        },
                        {
                            "role": "user",
                            "content": f"""Based on the following use case, suggest a workflow of technologies that would best solve this business need.
                            Use Case: {use_case}
                            
                            Remember to ONLY use technologies from this list: {available_technologies}
                            
                            Return ONLY a JSON object with the technologies and their suggested order. No markdown, no code blocks, no additional text."""
                        }
                    ],
                    stream=True
                )

                for chunk in completion:
                    if chunk.choices and hasattr(chunk.choices[0], "delta"):
                        content = getattr(chunk.choices[0].delta, "content", None)
                        if content:
                            # Clean any markdown formatting from the content
                            content = content.replace("```json", "").replace("```", "").strip()
                            yield content
            except Exception as e:
                app.logger.error(f"❌ Error during streaming: {str(e)}")
                yield json.dumps({"error": str(e)})

        return Response(generate_stream(), content_type="text/plain")

    except Exception as e:
        app.logger.error(f"❌ Error generating proposed workflow: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/rename_technologies", methods=["POST"])
def rename_technologies():
    try:
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400
        
        app.logger.info(f"🔄 Renaming Technologies for Use Case: {use_case}")

        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant that renames technology jobs to be more descriptive and relevant to specific use cases.
                    Your response must be in JSON format with this structure:
                    {
                        "renamed_technologies": {
                            "original_name": "new_name",
                            ...
                        }
                    }
                    Rules for renaming:
                    1. Keep names concise under 3 words but descriptive
                    2. Include relevant business context
                    3. Maintain consistency in naming convention
                    4. Only return the JSON object, no additional text"""
                },
                {
                    "role": "user",
                    "content": f"""Rename these technologies to be more relevant to this use case:
                    Technologies: {technologies}
                    Workflow Order: {ordered_workflow}
                    Use Case: {use_case}
                    
                    Return ONLY a JSON object with the original names as keys and new names as values."""
                }
            ]
        )

        response_content = completion.choices[0].message.content.strip()
        
        # Clean any markdown formatting and parse JSON
        try:
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            json_str = response_content[start:end]
            renamed_technologies = json.loads(json_str)
            return jsonify(renamed_technologies), 200
        except Exception as e:
            app.logger.error(f"❌ Error parsing renamed technologies: {str(e)}")
            return jsonify({"error": "Failed to parse renamed technologies"}), 500

    except Exception as e:
        app.logger.error(f"❌ Error renaming technologies: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/deploy_personalized_workflow", methods=["POST"])
def deploy_personalized_workflow():
    try:
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        renamed_technologies = data.get("renamed_technologies")
        ordered_workflow = data.get("optimal_order") or technologies
        environment = data.get('environment', 'saas_dev')  # Default to saas_dev if not specified
        user_code = data.get('user_code', 'LBA')  # Default to LBA if not specified
        folder_name = data.get('folder_name', 'DEMGEN_VB')
        application = data.get('application', 'DMO-GEN')
        sub_application = data.get('sub_application', 'TEST-APP')

        if not technologies or not use_case or not renamed_technologies:
            return jsonify({"error": "Technologies, use case, and renamed technologies are required."}), 400
        
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

        # First, get the AI to convert the names to Control-M format
        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant that converts job names to Control-M format.
                    Your response must be in JSON format with this structure:
                    {
                        "controlm_jobs": {
                            "original_name": "zzt-{converted_name}",
                            ...
                        }
                    }
                    Rules for conversion:
                    1. Convert spaces to hyphens
                    2. Remove special characters
                    3. Keep names concise and clear
                    4. Prefix with 'zzt-'
                    5. Only return the JSON object, no additional text"""
                },
                {
                    "role": "user",
                    "content": f"""Convert these job names to Control-M format:
                    Original Technologies: {technologies}
                    Renamed Technologies: {renamed_technologies}
                    Use Case: {use_case}
                    
                    Return ONLY a JSON object with the original names as keys and Control-M formatted names as values."""
                }
            ]
        )

        response_content = completion.choices[0].message.content.strip()
        
        # Parse the Control-M job names
        try:
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            json_str = response_content[start:end]
            controlm_jobs = json.loads(json_str)["controlm_jobs"]
        except Exception as e:
            return jsonify({"error": "Failed to parse Control-M job names"}), 500

        # Create the workflow with the new job names
        my_env = Environment.create_saas(
            endpoint=my_secrets[f'{environment}_endpoint'],
            api_key=my_secrets[f'{environment}_api_key']
        )

        # Format folder and application names with user code
        formatted_folder_name = f"{user_code}_{folder_name}"
        formatted_application = f"{user_code}-{application}"
        formatted_sub_application = f"{user_code}-{sub_application}"

        defaults = WorkflowDefaults(
            run_as="ctmagent",
            host="zzz-linux-agents",
            application=formatted_application,
            sub_application=formatted_sub_application
        )

        workflow = Workflow(my_env, defaults=defaults)
        folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
        workflow.add(folder)

        job_paths = []
        ordered_jobs = []

        # Use the ordered workflow to maintain the sequence
        for job_key in ordered_workflow:
            if job_key not in JOB_LIBRARY:
                return jsonify({"error": f"Unknown job: {job_key}"}), 400

            # Get the job from the library
            job = JOB_LIBRARY[job_key]()
            
            # Update the object name with the Control-M format
            new_name = controlm_jobs.get(job_key, f"zzt-{job_key}")
            job.object_name = new_name
            
            workflow.add(job, inpath=formatted_folder_name)
            job_paths.append(f"{formatted_folder_name}/{new_name}")
            ordered_jobs.append(new_name)

        # Chain the jobs in the specified order
        for i in range(len(job_paths) - 1):
            workflow.connect(job_paths[i], job_paths[i + 1])

        raw_json = workflow.dumps_json()
        
        # Check for build and deploy errors
        build_errors = workflow.build().errors
        deploy_errors = workflow.deploy().errors

        if build_errors is None and deploy_errors is None:
            # Save JSON to output.json
            with open("output.json", "w") as f:
                f.write(raw_json)
            
            # Run the Control-M CLI commands
            try:
                subprocess.run(["ctm", "build", "output.json"], check=True)
                subprocess.run(["ctm", "deploy", "output.json"], check=True)
                return jsonify({
                    "message": "Personalized workflow deployed successfully",
                    "workflow": raw_json,
                    "ordered_jobs": ordered_jobs,
                    "environment": environment,
                    "controlm_server": controlm_server,
                    "folder_name": formatted_folder_name
                }), 200
            except subprocess.CalledProcessError as e:
                return jsonify({"error": f"Control-M command failed: {str(e)}"}), 500
        else:
            return jsonify({
                "error": "Workflow build or deploy failed",
                "build_errors": build_errors,
                "deploy_errors": deploy_errors
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download_workflow', methods=['POST'])
def download_workflow():
    data = request.get_json()
    
    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' in request."}), 400

    requested_jobs = data['jobs']
    environment = data.get('environment', 'saas_dev')
    folder_name = data.get('folder_name', 'LBA_DEMGEN_VB')
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
    formatted_folder_name = f"{user_code}_DEMGEN_VB"
    formatted_application = f"{user_code}-DMO-GEN"
    formatted_sub_application = f"{user_code}-TEST-APP"

    # ENV & defaults
    my_env = Environment.create_saas(
        endpoint=my_secrets[f'{environment}_endpoint'],
        api_key=my_secrets[f'{environment}_api_key']
    )

    defaults = WorkflowDefaults(
        run_as="ctmagent",
        host="zzz-linux-agents",
        application=formatted_application,
        sub_application=formatted_sub_application
    )

    workflow = Workflow(my_env, defaults=defaults)
    folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
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


@app.route('/upload_workflow', methods=['POST'])
def upload_workflow():
    try:
        app.logger.info("📤 Starting workflow upload process")
        
        if 'file' not in request.files:
            app.logger.error("❌ No file provided in request")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        app.logger.info(f"📄 Received file: {file.filename}")
        
        if file.filename == '':
            app.logger.error("❌ Empty filename")
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.json'):
            app.logger.error(f"❌ Invalid file type: {file.filename}")
            return jsonify({"error": "File must be a JSON file"}), 400

        # Read and parse the JSON file
        try:
            file_content = file.read().decode('utf-8')
            app.logger.info(f"📝 Raw file content: {file_content[:500]}...")  # Log first 500 chars
            
            workflow_data = json.loads(file_content)
            app.logger.info(f"✅ Successfully parsed JSON: {json.dumps(workflow_data, indent=2)}")
        except json.JSONDecodeError as e:
            app.logger.error(f"❌ JSON parsing error: {str(e)}")
            return jsonify({"error": "Invalid JSON file"}), 400

        # Validate the workflow structure
        if not isinstance(workflow_data, dict):
            app.logger.error(f"❌ Invalid workflow format: {type(workflow_data)}")
            return jsonify({"error": "Invalid workflow format"}), 400

        # Extract job information from object names
        jobs = []
        folder_name = next(iter(workflow_data.keys()))  # Get the folder name
        app.logger.info(f"🔍 Processing folder: {folder_name}")
        
        # Get all keys that start with 'zzt-'
        object_names = [key for key in workflow_data[folder_name].keys() if key.startswith('zzt-')]
        app.logger.info(f"📋 Found object names: {object_names}")

        # Validate each object name against JOB_LIBRARY
        for obj_name in object_names:
            # Remove the 'zzt-' prefix to get the base name
            base_name = obj_name[4:]  # Remove 'zzt-' prefix
            app.logger.info(f"🔍 Checking object name: {obj_name} (base name: {base_name})")
            
            # Find matching job in JOB_LIBRARY
            found_job = None
            for job_name, job_class in JOB_LIBRARY.items():
                # Create an instance of the job to check its object_name
                job_instance = job_class()
                if job_instance.object_name == obj_name:
                    found_job = job_name
                    break
            
            if found_job:
                app.logger.info(f"✅ Found matching job: {found_job} for object name: {obj_name}")
                jobs.append(found_job)
            else:
                app.logger.warning(f"⚠️ No matching job found for object name: {obj_name}")

        if not jobs:
            app.logger.error("❌ No valid jobs found in workflow")
            return jsonify({"error": "No valid jobs found in the workflow"}), 400

        app.logger.info(f"✅ Successfully extracted {len(jobs)} jobs: {jobs}")
        
        return jsonify({
            "message": "Workflow uploaded successfully",
            "jobs": jobs,
            "workflow_data": workflow_data
        }), 200

    except Exception as e:
        app.logger.error(f"❌ Error processing workflow upload: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/save_template', methods=['POST'])
def save_template():
    try:
        data = request.json
        app.logger.info(f"📝 Saving template: {json.dumps(data, indent=2)}")
        
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
            "renamedTechnologies": data.get('renamedTechnologies', {}),
            "environment": data.get('environment', 'saas_dev'),
            "userCode": data.get('userCode', 'LBA'),
            "folderName": data.get('folderName', 'DEMGEN_VB'),
            "application": data.get('application', 'DMO-GEN'),
            "subApplication": data.get('subApplication', 'TEST-APP')
        }

        # Save template to a JSON file
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        template_file = os.path.join(templates_dir, f"{template_id}.json")
        with open(template_file, 'w') as f:
            json.dump(template_data, f, indent=2)

        app.logger.info(f"✅ Template saved successfully: {template_id}")
        return jsonify({
            "message": "Template saved successfully",
            "templateId": template_id
        }), 200

    except Exception as e:
        app.logger.error(f"❌ Error saving template: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/list_templates', methods=['GET'])
def list_templates():
    try:
        app.logger.info("📋 Listing templates")
        
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
                    app.logger.error(f"❌ Error reading template {filename}: {str(e)}")
                    continue

        # Sort templates by last modified date
        templates.sort(key=lambda x: x.get('lastModified', ''), reverse=True)
        
        app.logger.info(f"✅ Found {len(templates)} templates")
        return jsonify({"templates": templates}), 200

    except Exception as e:
        app.logger.error(f"❌ Error listing templates: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/delete_template', methods=['POST'])
def delete_template():
    try:
        data = request.json
        template_id = data.get('templateId')
        
        if not template_id:
            return jsonify({"error": "Template ID is required"}), 400

        app.logger.info(f"🗑️ Deleting template: {template_id}")
        
        template_file = os.path.join("templates", f"{template_id}.json")
        
        if not os.path.exists(template_file):
            return jsonify({"error": "Template not found"}), 404

        os.remove(template_file)
        app.logger.info(f"✅ Template deleted successfully: {template_id}")
        
        return jsonify({"message": "Template deleted successfully"}), 200

    except Exception as e:
        app.logger.error(f"❌ Error deleting template: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/check_template_exists', methods=['POST'])
def check_template_exists():
    try:
        data = request.json
        template_name = data.get('name')
        template_category = data.get('category')
        
        if not template_name or not template_category:
            return jsonify({"error": "Template name and category are required"}), 400

        app.logger.info(f"🔍 Checking for existing template: {template_name} in category: {template_category}")
        
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
                    app.logger.error(f"❌ Error reading template {filename}: {str(e)}")
                    continue

        return jsonify({"exists": False}), 200

    except Exception as e:
        app.logger.error(f"❌ Error checking template existence: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/update_template', methods=['POST'])
def update_template():
    try:
        data = request.json
        template_id = data.get('templateId')
        
        if not template_id:
            return jsonify({"error": "Template ID is required"}), 400

        app.logger.info(f"📝 Updating template: {template_id}")
        
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
            "renamedTechnologies": data.get('renamedTechnologies'),
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

        app.logger.info(f"✅ Template updated successfully: {template_id}")
        return jsonify({
            "message": "Template updated successfully",
            "templateId": template_id
        }), 200

    except Exception as e:
        app.logger.error(f"❌ Error updating template: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
