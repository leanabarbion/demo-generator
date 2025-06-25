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
import base64
import requests
import docx
import PyPDF2
import pdfplumber

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

# GitHub Config (store token securely in .env)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found in environment variables. Please set GITHUB_TOKEN in your .env file.")
REPO_OWNER = "leanabarbion"
REPO_NAME = "workflow-repo"  # Replace with your repo name
BRANCH = "main"
BASE_FOLDER_PATH = "jobs"  # Folder where files will be uploaded


def connect_to_github(file_path, content, message):
    """Uploads a file to GitHub repository using GitHub API."""
    if not GITHUB_TOKEN:
        app.logger.error("❌ GitHub token is not set")
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
            app.logger.error(f"❌ Error checking file existence: {error_msg}")
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
            app.logger.info(f"✅ Successfully uploaded file: {file_path}")
            return {"status": "success", "file": file_path}
        else:
            error_msg = upload_response.json().get("message", "Unknown error")
            app.logger.error(f"❌ Error uploading file: {error_msg}")
            return {"status": "error", "message": f"Error uploading file: {error_msg}"}
    except Exception as e:
        app.logger.error(f"❌ Exception during GitHub upload: {str(e)}")
        return {"status": "error", "message": f"Exception during upload: {str(e)}"}


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/generate_workflow', methods=['POST'])
def generate_workflow():
    data = request.get_json()
    
    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' in request."}), 400

    jobs_data = data['jobs']
    subfolders_data = data.get('subfolders', [])
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
    formatted_folder_name = f"{user_code}-{folder_name}"
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    try:
        # Create environment connection
        app.logger.info(f"🔧 Creating environment connection for {environment}")
        my_env = Environment.create_saas(
            endpoint=my_secrets[f'{environment}_endpoint'],
            api_key=my_secrets[f'{environment}_api_key']
        )

        # Create workflow defaults
        defaults = WorkflowDefaults(
            run_as="ctmagent",
            host="zzz-linux-agents",
            application=formatted_application,
            sub_application=formatted_sub_application
        )

        # Create workflow
        app.logger.info("🔨 Creating workflow object")
        workflow = Workflow(my_env, defaults=defaults)
        
        # Create main folder
        folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
        workflow.add(folder)

        # Create subfolders
        subfolder_map = {}
        for subfolder_data in subfolders_data:
            subfolder_name = f"{user_code}-{subfolder_data['name']}"
            subfolder = SubFolder(subfolder_name)
            
            # Add events
            if subfolder_data['events']['add']:
                add_events = [Event(event=event, date=Event.Date.OrderDate) 
                             for event in subfolder_data['events']['add']]
                subfolder.events_to_add.append(AddEvents(add_events))
            
            # Add wait events
            if subfolder_data['events']['wait']:
                wait_events = [Event(event=event, date=Event.Date.OrderDate) 
                              for event in subfolder_data['events']['wait']]
                subfolder.wait_for_events.append(WaitForEvents(wait_events))
            
            # Add delete events
            if subfolder_data['events']['delete']:
                delete_events = [Event(event=event, date=Event.Date.OrderDate) 
                                for event in subfolder_data['events']['delete']]
                subfolder.delete_events_list.append(DeleteEvents(delete_events))
            
            folder.sub_folder_list.append(subfolder)
            subfolder_map[subfolder_data['name']] = subfolder

        # Group jobs by concurrent groups within subfolders
        concurrent_groups = {}
        for job_data in jobs_data:
            subfolder_name = job_data.get('subfolder', '')
            concurrent_group = job_data.get('concurrent_group', 'default')
            
            if subfolder_name not in concurrent_groups:
                concurrent_groups[subfolder_name] = {}
            if concurrent_group not in concurrent_groups[subfolder_name]:
                concurrent_groups[subfolder_name][concurrent_group] = []
            
            concurrent_groups[subfolder_name][concurrent_group].append(job_data['id'])

        # Process jobs and create dependencies
        job_instances = {}
        job_paths = {}  # Store full paths for each job

        for job_data in jobs_data:
            job_id = job_data['id']
            job_type = job_data['type']
            
            if job_type not in JOB_LIBRARY:
                return jsonify({"error": f"Unknown job type: {job_type}"}), 400

            # Create job instance
            job = JOB_LIBRARY[job_type]()
            job.object_name = f"{user_code}-{job_data['name']}"
            
            # Add job to appropriate subfolder or main folder
            if 'subfolder' in job_data and job_data['subfolder'] in subfolder_map:
                subfolder_name = f"{user_code}-{job_data['subfolder']}"
                subfolder_path = f"{formatted_folder_name}/{subfolder_name}"
                workflow.add(job, inpath=subfolder_path)
                job_paths[job_id] = f"{subfolder_path}/{job.object_name}"
            else:
                workflow.add(job, inpath=formatted_folder_name)
                job_paths[job_id] = f"{formatted_folder_name}/{job.object_name}"
                
            job_instances[job_id] = job

        # Add completion events for concurrent groups
        for subfolder_name, groups in concurrent_groups.items():
            for group_name, job_ids in groups.items():
                if len(job_ids) > 1:  # Only create events for actual concurrent groups
                    completion_event = f"{subfolder_name}_{group_name}_COMPLETE"
                    for job_id in job_ids:
                        if job_id in job_instances:
                            job_instances[job_id].events_to_add.append(AddEvents([Event(event=completion_event)]))

        # Create logical dependencies between subfolders using events
        # This is handled through the subfolder events (wait/add/delete) defined in the AI response

        # Generate JSON
        raw_json = workflow.dumps_json()

        # Save JSON to output.json
        output_file = "output.json"
        with open(output_file, "w") as f:
            f.write(raw_json)

        # Build the workflow using Python client
        app.logger.info("🔨 Building workflow")
        build_result = workflow.build()
        if build_result.errors:
            app.logger.error(f"❌ Build errors: {build_result.errors}")
            deployment_status = {
                "success": False,
                "message": "Workflow build failed",
                "errors": build_result.errors
            }
        else:
            # Deploy the workflow using Python client
            app.logger.info("🚀 Deploying workflow")
            deploy_result = workflow.deploy()
            if deploy_result.errors:
                app.logger.error(f"❌ Deploy errors: {deploy_result.errors}")
                deployment_status = {
                    "success": False,
                    "message": "Workflow deployment failed",
                    "errors": deploy_result.errors
                }
            else:
                deployment_status = {
                    "success": True,
                    "message": "Workflow successfully built and deployed",
                    "build_result": str(build_result),
                    "deploy_result": str(deploy_result)
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
                        "object_name": job_instances[job_id].object_name,
                        "subfolder": job_data.get('subfolder', None)
                    }
                    for job_id, job_data in zip(job_instances.keys(), jobs_data)
                ],
                "folder_name": "industry-specific-job-name",
                        "subfolders": [
                    {
                        "name": subfolder_data['name'],
                        "description": subfolder_data.get('description', ''),
                        "events": subfolder_data['events']
                    }
                    for subfolder_data in subfolders_data
                ],
                "concurrent_groups": concurrent_groups,
            },
            "deployment": deployment_status,
            "raw_json": raw_json
        }

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"❌ Error during workflow generation: {str(e)}")
        return jsonify({
            "error": "Workflow generation failed",
            "details": str(e)
        }), 500


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


@app.route("/generate-talktrack", methods=["POST"])
def generate_talktrack():
    try: 
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400
        
        app.logger.info(f"🎤 Generating Talk Track with:")
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
                            "content": """You are an AI assistant that generates presentation-style talk tracks for BMC Control-M workflow demonstrations.
                            Your response must follow this exact structure and formatting:
                            
                            # Workflow Demonstration Talk Track
                            [A compelling title that captures the essence of the workflow]

                            ## Introduction (30 seconds)
                            [A brief, engaging introduction that hooks the audience and sets up the business context]

                            ## Business Challenge (1 minute)
                            [Describe the business problem or opportunity that this workflow addresses]

                            ## Solution Overview (1 minute)
                            [High-level explanation of how the workflow solves the business challenge]

                            ## Workflow Walkthrough (3-4 minutes)
                            [Step-by-step explanation of the workflow, including:
                            - What each job does
                            - Why it's important
                            - How it connects to the next step
                            - Business value at each stage]

                            ## Key Benefits (1 minute)
                            [Highlight the main advantages and improvements this workflow brings]

                            ## Technical Highlights (1 minute)
                            [Point out the most impressive technical aspects of the implementation]

                            ## Conclusion (30 seconds)
                            [Wrap up with a strong call to action or next steps]

                            Format your response with clear section headers and engaging, presentation-style language.
                            Use markdown formatting for better readability."""
                        },
                        {
                            "role": "user",
                            "content": f"""Generate a presentation talk track for the following workflow:
                            Technologies: {technologies}
                            Workflow Order: {ordered_workflow}
                            Use Case: {use_case}
                            
                            Follow the exact structure provided, with clear section headers and timing guidance."""
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
        app.logger.error(f"❌ Error generating talk track: {str(e)}")
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


@app.route("/create_workflow", methods=["POST"])
def create_workflow():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided in request"}), 400

        technologies = data.get("technologies")
        use_case = data.get("use_case")
        renamed_technologies = data.get("renamed_technologies")
        ordered_workflow = data.get("optimal_order") or technologies
        environment = data.get('environment', 'saas_dev')  # Default to saas_dev if not specified
        user_code = data.get('user_code', 'LBA')  # Default to LBA if not specified
        folder_name = data.get('folder_name', 'demo-genai')
        application = data.get('application', 'demo-genai')
        sub_application = data.get('sub_application', 'demo-genai')
        controlm_server = data.get('controlm_server', 'IN01')

        if not technologies or not use_case or not renamed_technologies:
            return jsonify({"error": "Technologies, use case, and renamed technologies are required."}), 400
        
        # Validate environment
        valid_environments = ['saas_dev', 'saas_preprod', 'saas_prod', 'vse_dev', 'vse_qa', 'vse_prod']
        if environment not in valid_environments:
            return jsonify({"error": f"Invalid environment. Must be one of: {valid_environments}"}), 400

        # First, get the AI to convert the names to Control-M format
        try:
            completion = client.chat.completions.create(
                model=azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an AI assistant that converts job names to Control-M format.
                        Your response must be in JSON format with this structure:
                        {{
                            "controlm_jobs": {{
                                "original_name": "{user_code}-{{converted_name}}",
                                ...
                            }}
                        }}
                        Rules for conversion:
                        1. Convert spaces to hyphens
                        2. Remove special characters
                        3. Keep names concise and clear
                        4. Prefix with '{user_code}-' and no other prefix
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
                return jsonify({"error": f"Failed to parse Control-M job names: {str(e)}"}), 500

        except Exception as e:
            return jsonify({"error": f"Failed to generate Control-M job names: {str(e)}"}), 500

        # Create the workflow with the new job names
        try:
            my_env = Environment.create_saas(
                endpoint=my_secrets[f'{environment}_endpoint'],
                api_key=my_secrets[f'{environment}_api_key']
            )
        except Exception as e:
            return jsonify({"error": f"Failed to create environment: {str(e)}"}), 500

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
        
        # Save JSON to output.json
        try:
            with open("output.json", "w") as f:
                f.write(raw_json)
        except Exception as e:
            return jsonify({"error": f"Failed to save workflow JSON: {str(e)}"}), 500

        return jsonify({
            "message": "Workflow created successfully",
            "workflow": raw_json,
            "ordered_jobs": ordered_jobs,
            "environment": environment,
            "controlm_server": controlm_server,
            "folder_name": formatted_folder_name
        }), 200

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/deploy_personalized_workflow", methods=["POST"])
def deploy_personalized_workflow():
    try:
        app.logger.info("🚀 Starting personalized workflow deployment")
        data = request.json
        if not data:
            app.logger.error("❌ No data provided in request")
            return jsonify({"error": "No data provided in request"}), 400

        # Extract workflow configuration from request
        environment = data.get('environment', 'saas_dev')
        user_code = data.get('user_code', 'LBA')
        folder_name = data.get('folder_name', 'demo-genai')
        application = data.get('application', 'demo-genai')
        sub_application = data.get('sub_application', 'demo-genai')
        technologies = data.get('technologies', [])
        renamed_technologies = data.get('renamed_technologies', {})
        ordered_workflow = data.get('optimal_order') or technologies

        if not technologies or not renamed_technologies:
            app.logger.error("❌ Missing required technologies or renamed technologies")
            return jsonify({"error": "Technologies and renamed technologies are required"}), 400

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

        try:
            # Create environment connection
            app.logger.info(f"🔧 Creating environment connection for {environment}")
            my_env = Environment.create_saas(
                endpoint=my_secrets[f'{environment}_endpoint'],
                api_key=my_secrets[f'{environment}_api_key']
            )

            # Format names
            formatted_folder_name = f"{user_code}_{folder_name}"
            formatted_application = f"{user_code}-{application}"
            formatted_sub_application = f"{user_code}-{sub_application}"

            # Create workflow defaults
            defaults = WorkflowDefaults(
                run_as="ctmagent",
                host="zzz-linux-agents",
                application=formatted_application,
                sub_application=formatted_sub_application
            )

            # Create workflow
            app.logger.info("🔨 Creating workflow object")
            workflow = Workflow(my_env, defaults=defaults)

            # Create folder
            folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
            workflow.add(folder)

            # Add jobs to workflow
            job_paths = []
            ordered_jobs = []

            # Use the ordered workflow to maintain the sequence
            for job_key in ordered_workflow:
                if job_key not in JOB_LIBRARY:
                    app.logger.error(f"❌ Unknown job type: {job_key}")
                    return jsonify({"error": f"Unknown job type: {job_key}"}), 400

                # Get the job from the library
                job = JOB_LIBRARY[job_key]()
                
                # Update the object name with the Control-M format
                new_name = renamed_technologies.get(job_key, f"{user_code}-{job_key}")
                job.object_name = new_name
                
                workflow.add(job, inpath=formatted_folder_name)
                job_paths.append(f"{formatted_folder_name}/{new_name}")
                ordered_jobs.append(new_name)

            # Chain the jobs in the specified order
            for i in range(len(job_paths) - 1):
                workflow.connect(job_paths[i], job_paths[i + 1])

            # Build the workflow
            app.logger.info("🔨 Building workflow")
            build_result = workflow.build()
            if build_result.errors:
                app.logger.error(f"❌ Build errors: {build_result.errors}")
                return jsonify({
                    "error": "Workflow build failed",
                    "details": build_result.errors
                }), 500
            
            # Deploy the workflow
            app.logger.info("🚀 Deploying workflow")
            deploy_result = workflow.deploy()
            if deploy_result.errors:
                app.logger.error(f"❌ Deploy errors: {deploy_result.errors}")
                return jsonify({
                    "error": "Workflow deployment failed",
                    "details": deploy_result.errors
                }), 500
            
            app.logger.info("🎉 Workflow deployment completed successfully")
            return jsonify({
                "message": "Personalized workflow deployed successfully",
                "build_result": str(build_result),
                "deploy_result": str(deploy_result),
                "ordered_jobs": ordered_jobs
            }), 200

        except Exception as e:
            app.logger.error(f"❌ Error during workflow creation/build/deploy: {str(e)}")
            return jsonify({
                "error": "Workflow creation/build/deploy failed",
                "details": str(e)
            }), 500

    except Exception as e:
        app.logger.error(f"❌ Unexpected error in deployment: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route('/download_workflow', methods=['POST'])
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


@app.route("/upload-github", methods=["POST"])
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
        app.logger.error(f"❌ Error in upload_github: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/analyze_documentation", methods=["POST"])
def analyze_documentation():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        use_case = request.form.get('use_case', '')
        
        if not file:
            return jsonify({"error": "No file selected"}), 400
            
        if not file.filename.endswith(('.txt', '.doc', '.docx', '.pdf')):
            return jsonify({"error": "Invalid file format. Please upload .txt, .doc, .docx, or .pdf files"}), 400

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
                    app.logger.warning(f"pdfplumber failed, falling back to PyPDF2: {str(e)}")
                    # Fallback to PyPDF2
                    with open(temp_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        file_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                
                # Clean up temporary file
                os.remove(temp_path)
                
        except Exception as e:
            app.logger.error(f"Error reading file: {str(e)}")
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500

        if not file_content.strip():
            return jsonify({"error": "No readable content found in the file"}), 400

        app.logger.info(f"📄 Analyzing documentation with use case: {use_case}")
        app.logger.info(f"File content length: {len(file_content)} characters")

        # Get list of available technologies from JOB_LIBRARY
        available_technologies = list(JOB_LIBRARY.keys())
        
        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an AI assistant that analyzes documentation to extract workflow requirements and technologies.
                    Your response must be in JSON format with this structure:
                    {{
                        "extracted_use_case": "Detailed use case extracted from documentation",
                        "suggested_technologies": ["Technology1", "Technology2"],
                        "workflow_order": ["Technology1", "Technology2"],
                        "analysis_summary": "Brief summary of the analysis"
                    }}
                    
                    Rules:
                    1. Only suggest technologies from this exact list: {available_technologies}
                    2. Extract the most relevant use case details from the documentation
                    3. Consider both the provided use case and the documentation content
                    4. Suggest technologies that best match the requirements
                    5. Provide a logical workflow order based on dependencies
                    6. Return ONLY the JSON object, no additional text"""
                },
                {
                    "role": "user",
                    "content": f"""Analyze this documentation and use case to extract workflow requirements and suggest technologies:
                    
                    Documentation Content:
                    {file_content}
                    
                    Additional Use Case Context:
                    {use_case}
                    
                    Remember to ONLY use technologies from this list: {available_technologies}
                    
                    Return ONLY a JSON object with the extracted use case, suggested technologies, workflow order, and analysis summary."""
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
                
            analysis_result['suggested_technologies'] = valid_technologies
            analysis_result['workflow_order'] = [tech for tech in analysis_result['workflow_order'] 
                                               if tech in valid_technologies]
            
            return jsonify(analysis_result), 200
            
        except json.JSONDecodeError as e:
            app.logger.error(f"❌ Error parsing AI response: {str(e)}")
            return jsonify({"error": "Failed to parse AI response"}), 500

    except Exception as e:
        app.logger.error(f"❌ Error analyzing documentation: {str(e)}")
        return jsonify({"error": str(e)}), 500




@app.route('/ai_generated_workflow', methods=['POST'])
def ai_generated_workflow():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided in request."}), 400

    # Check if this is an AI-generated workflow request
    use_case = data.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing 'use_case' in request."}), 400

    # AI-powered workflow generation
    app.logger.info(f"🤖 Generating AI-powered workflow for use case: {use_case}")
    
    try:
        # Get available technologies from JOB_LIBRARY
        available_technologies = list(JOB_LIBRARY.keys())
        
        # Generate complex workflow using AI
        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert BMC Control-M workflow architect that creates complex workflows with multiple subfolders, realistic job dependencies, and logical business processes.

                    CRITICAL REQUIREMENTS:
                    1. Create AT LEAST 3 subfolders per workflow representing logical phases
                    2. Use ONLY technologies from this exact list: {available_technologies}
                    3. Subfolder names should be personalized based on the use case
                    4. Create logical dependencies BETWEEN SUBFOLDERS using events
                    5. Each subfolder should have AT LEAST 5 jobs total
                    6. Return ONLY valid JSON with this exact structure:
                    {{
                        "folder_name": "industry-specific-job-name",
                        "subfolders": [
                            {{
                                "name": "subfolder_name",
                                "description": "subfolder description",
                                "phase": "1",
                                "events": {{
                                    "add": ["subfolder_complete_event"],
                                    "wait": ["previous_subfolder_complete_event"],
                                    "delete": ["previous_subfolder_complete_event"]
                                }}
                            }}
                        ],
                        "jobs": [
                            {{
                                "id": "unique_job_id",
                                "name": "descriptive_job_name",
                                "type": "technology_from_list",
                                "subfolder": "subfolder_name",
                                "concurrent_group": "group_1",
                                "wait_for_jobs": ["job_id_1", "job_id_2"]
                            }}
                        ]
                    }}

                    JOB NAMING AND LOGIC:
                    - Each job must have a UNIQUE, DESCRIPTIVE name that makes logical sense for the use case
                    - Each job should not be longer than 3 words
                    - Job names should clearly indicate what the job does (e.g., "extract_customer_data", "validate_inventory", "generate_sales_report")
                    - Avoid generic names like "job1", "process1" - be specific and business-relevant
                    - Names should reflect the actual business process being automated
                    - Use descriptive names like: "Analyse_Data_Hadoop", "Cleansing_Transformation_Spark", "Summary_Power_BI", "Data_SAP_inventory", "Data_SFDC", "Transfer_to_Centralized_Repo"
                    - Job names should be specific to the technology and business function
                    - NEVER use generic names like "job1", "jobA", "process1", "task1" - always be descriptive
                    - Follow the naming pattern: [Action]_[Technology]_[BusinessFunction] or [Technology]_[BusinessFunction]

                    CONCURRENT JOB PATTERNS WITH DEPENDENCIES:
                    - Be flexible and realistic based on the use case
                    - Some subfolders might have 2-3 concurrent jobs, others might have 4-5
                    - Consider what makes sense for the business process
                    - Create realistic intra-subfolder dependencies where some jobs wait for others
                    - Example patterns:
                      * Phase 1: Data collection (3-5 concurrent jobs gathering different data sources)
                      * Phase 2: Data processing (2-3 concurrent jobs processing the collected data)
                      * Phase 3: Reporting/Analysis (1-2 jobs creating final outputs)
                    - Let the use case drive the number of concurrent jobs, not arbitrary rules

                    INTRA-SUBFOLDER DEPENDENCIES:
                    - Some jobs within the same subfolder should wait for other concurrent jobs to finish
                    - Use the "wait_for_jobs" field to specify which jobs must complete first
                    - Create realistic business logic (e.g., data validation waits for data extraction, aggregation waits for individual processing)
                    - Example: In a data processing subfolder:
                      * Jobs 1-3: Extract data from different sources (concurrent)
                      * Job 4: Validate all extracted data (waits for jobs 1-3)
                      * Job 5: Aggregate validated data (waits for job 4)
                    - Mix concurrent and dependent jobs within the same subfolder for realistic workflows
                    - Jobs without "wait_for_jobs" run concurrently with other jobs in the same subfolder
                    - Jobs with "wait_for_jobs" wait for specific jobs to complete before starting
                    - This creates realistic business processes where some tasks can run in parallel while others must wait

                    RULES:
                    - Subfolder names should be descriptive and use case-specific
                    - Job names should be descriptive and relevant to the use case
                    - Each subfolder represents a logical phase of the workflow
                    - Jobs within the same subfolder can have dependencies on other jobs in the same subfolder
                    - Dependencies between subfolders are handled through subfolder events (wait/add/delete)
                    - Use realistic job types that make sense for the use case
                    - Ensure all technologies are from the provided list
                    - Create a logical flow: Phase1 -> Phase2 -> Phase3
                    - Each subfolder should have a unique phase number
                    - Be creative and realistic with concurrent job patterns based on the use case
                    - Each job must have a unique, logical name that clearly describes its purpose"""
                    },
                    {
                        "role": "user",
                        "content": f"""Create a complex BMC Control-M workflow for this use case:
                        
                        Use Case: {use_case}
                        
                        Requirements:
                        - At least 3 subfolders representing logical phases
                        - Create realistic concurrent job patterns based on the use case
                        - Mix concurrent and dependent jobs within subfolders for realistic business logic
                        - Some jobs should run concurrently, others should wait for specific jobs to complete
                        - Use the "wait_for_jobs" field to create logical dependencies within subfolders
                        - Create logical dependencies between subfolders using events
                        - Use only technologies from: {available_technologies}
                        - Each job must have a descriptive, logical name (like "Analyse_Data_Hadoop", "Cleansing_Transformation_Spark")
                        - NEVER use generic names like "job1", "jobA", "process1" - always be descriptive and business-relevant
                        
                        Let the use case drive the workflow design - be creative and realistic with job patterns."""
                    }
                ]
            )

        response_content = completion.choices[0].message.content.strip()

        # Parse the AI response
        try:
            # Extract JSON from response
            start = response_content.find('{')
            end = response_content.rfind('}') + 1
            json_str = response_content[start:end]
            ai_workflow = json.loads(json_str)
            
            # Validate the AI response
            if 'folder_name' not in ai_workflow or 'subfolders' not in ai_workflow or 'jobs' not in ai_workflow:
                raise ValueError("Invalid AI response structure")
            
            # Use the AI-generated workflow data
            folder_name = ai_workflow['folder_name']
            subfolders_data = ai_workflow['subfolders']
            jobs_data = ai_workflow['jobs']
            
            app.logger.info(f"✅ AI generated folder name: {folder_name}")
            app.logger.info(f"✅ AI generated {len(subfolders_data)} subfolders and {len(jobs_data)} jobs")
            
        except Exception as e:
            app.logger.error(f"❌ Error parsing AI response: {str(e)}")
            return jsonify({"error": "Failed to parse AI-generated workflow"}), 500
                

    except Exception as e:
        app.logger.error(f"❌ Error generating AI workflow: {str(e)}")
        return jsonify({"error": "Failed to generate AI workflow"}), 500

    # Common workflow creation logic (same as generate_workflow)
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
    formatted_folder_name = f"{user_code}-{folder_name}"
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    try:
        # Create environment connection
        app.logger.info(f"🔧 Creating environment connection for {environment}")
        my_env = Environment.create_saas(
            endpoint=my_secrets[f'{environment}_endpoint'],
            api_key=my_secrets[f'{environment}_api_key']
        )

        # Create workflow defaults
        defaults = WorkflowDefaults(
            run_as="ctmagent",
            host="zzz-linux-agents",
            application=formatted_application,
            sub_application=formatted_sub_application
        )

        # Create workflow
        app.logger.info("🔨 Creating workflow object")
        workflow = Workflow(my_env, defaults=defaults)
        
        # Create main folder
        folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
        workflow.add(folder)

        # Create subfolders
        subfolder_map = {}
        for subfolder_data in subfolders_data:
            subfolder_name = f"{user_code}-{subfolder_data['name']}"
            subfolder = SubFolder(subfolder_name)
            
            # Add events
            if subfolder_data['events']['add']:
                add_events = [Event(event=event, date=Event.Date.OrderDate) 
                             for event in subfolder_data['events']['add']]
                subfolder.events_to_add.append(AddEvents(add_events))
            
            # Add wait events
            if subfolder_data['events']['wait']:
                wait_events = [Event(event=event, date=Event.Date.OrderDate) 
                              for event in subfolder_data['events']['wait']]
                subfolder.wait_for_events.append(WaitForEvents(wait_events))
            
            # Add delete events
            if subfolder_data['events']['delete']:
                delete_events = [Event(event=event, date=Event.Date.OrderDate) 
                                for event in subfolder_data['events']['delete']]
                subfolder.delete_events_list.append(DeleteEvents(delete_events))
            
            folder.sub_folder_list.append(subfolder)
            subfolder_map[subfolder_data['name']] = subfolder

        # Group jobs by concurrent groups within subfolders
        concurrent_groups = {}
        for job_data in jobs_data:
            subfolder_name = job_data.get('subfolder', '')
            concurrent_group = job_data.get('concurrent_group', 'default')
            
            if subfolder_name not in concurrent_groups:
                concurrent_groups[subfolder_name] = {}
            if concurrent_group not in concurrent_groups[subfolder_name]:
                concurrent_groups[subfolder_name][concurrent_group] = []
            
            concurrent_groups[subfolder_name][concurrent_group].append(job_data['id'])

        # Process jobs and create dependencies
        job_instances = {}
        job_paths = {}  # Store full paths for each job

        for job_data in jobs_data:
            job_id = job_data['id']
            job_type = job_data['type']
            
            if job_type not in JOB_LIBRARY:
                return jsonify({"error": f"Unknown job type: {job_type}"}), 400

            # Create job instance
            job = JOB_LIBRARY[job_type]()
            job.object_name = f"{user_code}-{job_data['name']}"
            
            # Add job to appropriate subfolder or main folder
            if 'subfolder' in job_data and job_data['subfolder'] in subfolder_map:
                subfolder_name = f"{user_code}-{job_data['subfolder']}"
                subfolder_path = f"{formatted_folder_name}/{subfolder_name}"
                workflow.add(job, inpath=subfolder_path)
                job_paths[job_id] = f"{subfolder_path}/{job.object_name}"
            else:
                workflow.add(job, inpath=formatted_folder_name)
                job_paths[job_id] = f"{formatted_folder_name}/{job.object_name}"
                
            job_instances[job_id] = job

        # Add completion events for concurrent groups
        for subfolder_name, groups in concurrent_groups.items():
            for group_name, job_ids in groups.items():
                if len(job_ids) > 1:  # Only create events for actual concurrent groups
                    completion_event = f"{subfolder_name}_{group_name}_COMPLETE"
                    for job_id in job_ids:
                        if job_id in job_instances:
                            job_instances[job_id].events_to_add.append(AddEvents([Event(event=completion_event)]))

        # Create logical dependencies between subfolders using events
        # This is handled through the subfolder events (wait/add/delete) defined in the AI response

        # Generate JSON
        raw_json = workflow.dumps_json()

        # Save JSON to output.json
        output_file = "output.json"
        with open(output_file, "w") as f:
            f.write(raw_json)

        # Build the workflow using Python client
        app.logger.info("🔨 Building workflow")
        build_result = workflow.build()
        if build_result.errors:
            app.logger.error(f"❌ Build errors: {build_result.errors}")
            deployment_status = {
                "success": False,
                "message": "Workflow build failed",
                "errors": build_result.errors
            }
        else:
            # Deploy the workflow using Python client
            app.logger.info("🚀 Deploying workflow")
            deploy_result = workflow.deploy()
            if deploy_result.errors:
                app.logger.error(f"❌ Deploy errors: {deploy_result.errors}")
                deployment_status = {
                    "success": False,
                    "message": "Workflow deployment failed",
                    "errors": deploy_result.errors
                }
            else:
                deployment_status = {
                    "success": True,
                    "message": "Workflow successfully built and deployed",
                    "build_result": str(build_result),
                    "deploy_result": str(deploy_result)
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
                        "object_name": job_instances[job_id].object_name,
                        "subfolder": job_data.get('subfolder', None)
                    }
                    for job_id, job_data in zip(job_instances.keys(), jobs_data)
                ],
                "folder_name": "industry-specific-job-name",
                        "subfolders": [
                    {
                        "name": subfolder_data['name'],
                        "description": subfolder_data.get('description', ''),
                        "events": subfolder_data['events']
                    }
                    for subfolder_data in subfolders_data
                ],
                "concurrent_groups": concurrent_groups,
            },
            "workflow_json": raw_json,
            "environment": environment,
            "controlm_server": controlm_server,
            "folder_name": formatted_folder_name,
            "user_code": user_code,
            "ai_generated": True,
            "use_case": use_case
        }

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"❌ Error during AI workflow generation: {str(e)}")
        return jsonify({
            "error": "AI workflow generation failed",
            "details": str(e)
        }), 500

@app.route('/ai_prompt_workflow', methods=['POST'])
def ai_prompt_workflow():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided in request."}), 400

    # Check if this is an AI-generated workflow request
    use_case = data.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing 'use_case' in request."}), 400

    # AI-powered workflow generation
    app.logger.info(f"🤖 Generating AI-powered workflow for use case: {use_case}")
    
    try:
        # Get available technologies from JOB_LIBRARY
        available_technologies = list(JOB_LIBRARY.keys())
        
        # Generate complex workflow using AI
        completion = client.chat.completions.create(
            model=azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert BMC Control-M workflow architect that creates complex workflows with multiple subfolders, realistic job dependencies, and logical business processes.

                    CRITICAL REQUIREMENTS:
                    1. Create AT LEAST 3 subfolders per workflow representing logical phases
                    2. Use ONLY technologies from this exact list: {available_technologies}
                    3. Subfolder names should be personalized based on the use case
                    4. Create logical dependencies BETWEEN SUBFOLDERS using events
                    5. Each subfolder should have AT LEAST 5 jobs total
                    6. Return ONLY valid JSON with this exact structure:
                    {{
                        "folder_name": "industry-specific-job-name",
                        "subfolders": [
                            {{
                                "name": "subfolder_name",
                                "description": "subfolder description",
                                "phase": "1",
                                "events": {{
                                    "add": ["subfolder_complete_event"],
                                    "wait": ["previous_subfolder_complete_event"],
                                    "delete": ["previous_subfolder_complete_event"]
                                }}
                            }}
                        ],
                        "jobs": [
                            {{
                                "id": "unique_job_id",
                                "name": "descriptive_job_name",
                                "type": "technology_from_list",
                                "subfolder": "subfolder_name",
                                "concurrent_group": "group_1",
                                "wait_for_jobs": ["job_id_1", "job_id_2"]
                            }}
                        ]
                    }}
                    FOLDER NAMING RULES:
                    - Generate a descriptive folder name based on the use case
                    - Use the format: "industry-specific-job-name" (e.g., "loan-processing", "clinical-data", "inventory-management")
                    - Make it concise but descriptive (2 words max)
                    - Use lowercase with hyphens
                    - Focus on the main business process or industry domain
                    - Examples: "loan-processing", "clinical-data", "inventory-management", "customer-onboarding", "financial-reporting"

                    JOB NAMING AND LOGIC:
                    - Each job must have a UNIQUE, DESCRIPTIVE name that makes logical sense for the use case
                    - Each job should not be longer than 3 words
                    - Job names should clearly indicate what the job does (e.g., "extract_customer_data", "validate_inventory", "generate_sales_report")
                    - Avoid generic names like "job1", "process1" - be specific and business-relevant
                    - Names should reflect the actual business process being automated
                    - Use descriptive names like: "Analyse_Data_Hadoop", "Cleansing_Transformation_Spark", "Summary_Power_BI", "Data_SAP_inventory", "Data_SFDC", "Transfer_to_Centralized_Repo"
                    - Job names should be specific to the technology and business function
                    - NEVER use generic names like "job1", "jobA", "process1", "task1" - always be descriptive
                    - Follow the naming pattern: [Action]_[Technology]_[BusinessFunction] or [Technology]_[BusinessFunction]

                    CONCURRENT JOB PATTERNS WITH DEPENDENCIES:
                    - Be flexible and realistic based on the use case
                    - Some subfolders might have 2-3 concurrent jobs, others might have 4-5
                    - Consider what makes sense for the business process
                    - Create realistic intra-subfolder dependencies where some jobs wait for others
                    - Example patterns:
                      * Phase 1: Data collection (3-5 concurrent jobs gathering different data sources)
                      * Phase 2: Data processing (2-3 concurrent jobs processing the collected data)
                      * Phase 3: Reporting/Analysis (1-2 jobs creating final outputs)
                    - Let the use case drive the number of concurrent jobs, not arbitrary rules

                    INTRA-SUBFOLDER DEPENDENCIES:
                    - Some jobs within the same subfolder should wait for other concurrent jobs to finish
                    - Use the "wait_for_jobs" field to specify which jobs must complete first
                    - Create realistic business logic (e.g., data validation waits for data extraction, aggregation waits for individual processing)
                    - Example: In a data processing subfolder:
                      * Jobs 1-3: Extract data from different sources (concurrent)
                      * Job 4: Validate all extracted data (waits for jobs 1-3)
                      * Job 5: Aggregate validated data (waits for job 4)
                    - Mix concurrent and dependent jobs within the same subfolder for realistic workflows
                    - Jobs without "wait_for_jobs" run concurrently with other jobs in the same subfolder
                    - Jobs with "wait_for_jobs" wait for specific jobs to complete before starting
                    - This creates realistic business processes where some tasks can run in parallel while others must wait

                    RULES:
                    - Subfolder names should be descriptive and use case-specific
                    - Job names should be descriptive and relevant to the use case
                    - Each subfolder represents a logical phase of the workflow
                    - Jobs within the same subfolder can have dependencies on other jobs in the same subfolder
                    - Dependencies between subfolders are handled through subfolder events (wait/add/delete)
                    - Use realistic job types that make sense for the use case
                    - Ensure all technologies are from the provided list
                    - Create a logical flow: Phase1 -> Phase2 -> Phase3
                    - Each subfolder should have a unique phase number
                    - Be creative and realistic with concurrent job patterns based on the use case
                    - Each job must have a unique, logical name that clearly describes its purpose"""
                },
                {
                    "role": "user",
                    "content": f"""Create a complex BMC Control-M workflow for this use case:
                    
                    Use Case: {use_case}
                    
                    Requirements:
                    - At least 3 subfolders representing logical phases
                    - Create realistic concurrent job patterns based on the use case
                    - Mix concurrent and dependent jobs within subfolders for realistic business logic
                    - Some jobs should run concurrently, others should wait for specific jobs to complete
                    - Use the "wait_for_jobs" field to create logical dependencies within subfolders
                    - Create logical dependencies between subfolders using events
                    - Use only technologies from: {available_technologies}
                    - Each job must have a descriptive, logical name (like "Analyse_Data_Hadoop", "Cleansing_Transformation_Spark")
                    - NEVER use generic names like "job1", "jobA", "process1" - always be descriptive and business-relevant
                    
                    Let the use case drive the workflow design - be creative and realistic with job patterns."""
                }
            ]
        )

        response_content = completion.choices[0].message.content.strip()

        return jsonify({
            "response_content": response_content,
            "use_case": use_case,
            "available_technologies": available_technologies
        }), 200

    except Exception as e:
        app.logger.error(f"❌ Error generating AI workflow: {str(e)}")
        return jsonify({"error": "Failed to generate AI workflow"}), 500


@app.route('/deploy_ai_workflow', methods=['POST'])
def deploy_ai_workflow():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided in request."}), 400

    response_content = data.get('response_content')
    use_case = data.get('use_case')
    environment = data.get('environment', 'saas_dev')
    folder_name = data.get('folder_name')
    user_code = data.get('user_code', 'LBA')

    if not response_content or not use_case:
        return jsonify({"error": "Missing 'response_content' or 'use_case' in request."}), 400

    
    

    # Parse the AI response
    try:
            # Add detailed logging to debug the response_content
        app.logger.info("🔍 DEBUG: Received response_content:")
        app.logger.info(f"🔍 DEBUG: response_content type: {type(response_content)}")
        app.logger.info(f"🔍 DEBUG: response_content length: {len(response_content) if response_content else 0}")
        app.logger.info(f"🔍 DEBUG: response_content (first 500 chars): {response_content[:500] if response_content else 'None'}")
        app.logger.info(f"🔍 DEBUG: response_content (last 500 chars): {response_content[-500:] if response_content else 'None'}")
        
        # Extract JSON from response
        start = response_content.find('{')
        end = response_content.rfind('}') + 1
        json_str = response_content[start:end]
        ai_workflow = json.loads(json_str)

        # Validate the AI response
        if 'folder_name' not in ai_workflow or 'subfolders' not in ai_workflow or 'jobs' not in ai_workflow:
            raise ValueError("Invalid AI response structure")

        # Use the AI-generated workflow data
        folder_name = ai_workflow['folder_name']
        subfolders_data = ai_workflow['subfolders']
        jobs_data = ai_workflow['jobs']

        app.logger.info(f"📁 Using AI-generated folder name: {folder_name}")
        app.logger.info(f"✅ AI generated {len(subfolders_data)} subfolders and {len(jobs_data)} jobs")

    except Exception as e:
        app.logger.error(f"❌ Error parsing AI response: {str(e)}")
        return jsonify({"error": "Failed to parse AI-generated workflow"}), 500

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
    formatted_folder_name = f"{user_code}-{folder_name}"
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    try:
        # Create environment connection
        app.logger.info(f"🔧 Creating environment connection for {environment}")
        my_env = Environment.create_saas(
            endpoint=my_secrets[f'{environment}_endpoint'],
            api_key=my_secrets[f'{environment}_api_key']
        )

        # Create workflow defaults
        defaults = WorkflowDefaults(
            run_as="ctmagent",
            host="zzz-linux-agents",
            application=formatted_application,
            sub_application=formatted_sub_application
        )

        # Create workflow
        app.logger.info("🔨 Creating workflow object")
        workflow = Workflow(my_env, defaults=defaults)
        
        # Create main folder
        folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
        workflow.add(folder)

        # Create subfolders
        subfolder_map = {}
        for subfolder_data in subfolders_data:
            subfolder_name = f"{user_code}-{subfolder_data['name']}"
            subfolder = SubFolder(subfolder_name)
            
            # Add events
            if subfolder_data['events']['add']:
                add_events = [Event(event=event, date=Event.Date.OrderDate) 
                             for event in subfolder_data['events']['add']]
                subfolder.events_to_add.append(AddEvents(add_events))
            
            # Add wait events
            if subfolder_data['events']['wait']:
                wait_events = [Event(event=event, date=Event.Date.OrderDate) 
                              for event in subfolder_data['events']['wait']]
                subfolder.wait_for_events.append(WaitForEvents(wait_events))
            
            # Add delete events
            if subfolder_data['events']['delete']:
                delete_events = [Event(event=event, date=Event.Date.OrderDate) 
                                for event in subfolder_data['events']['delete']]
                subfolder.delete_events_list.append(DeleteEvents(delete_events))
            
            folder.sub_folder_list.append(subfolder)
            subfolder_map[subfolder_data['name']] = subfolder

        # Group jobs by concurrent groups within subfolders
        concurrent_groups = {}
        for job_data in jobs_data:
            subfolder_name = job_data.get('subfolder', '')
            concurrent_group = job_data.get('concurrent_group', 'default')
            
            if subfolder_name not in concurrent_groups:
                concurrent_groups[subfolder_name] = {}
            if concurrent_group not in concurrent_groups[subfolder_name]:
                concurrent_groups[subfolder_name][concurrent_group] = []
            
            concurrent_groups[subfolder_name][concurrent_group].append(job_data['id'])

        # Process jobs and create dependencies
        job_instances = {}
        job_paths = {}  # Store full paths for each job

        for job_data in jobs_data:
            job_id = job_data['id']
            job_type = job_data['type']
            
            if job_type not in JOB_LIBRARY:
                return jsonify({"error": f"Unknown job type: {job_type}"}), 400

            # Create job instance
            job = JOB_LIBRARY[job_type]()
            job.object_name = f"{user_code}-{job_data['name']}"
            
            # Add job to appropriate subfolder or main folder
            if 'subfolder' in job_data and job_data['subfolder'] in subfolder_map:
                subfolder_name = f"{user_code}-{job_data['subfolder']}"
                subfolder_path = f"{formatted_folder_name}/{subfolder_name}"
                workflow.add(job, inpath=subfolder_path)
                job_paths[job_id] = f"{subfolder_path}/{job.object_name}"
            else:
                workflow.add(job, inpath=formatted_folder_name)
                job_paths[job_id] = f"{formatted_folder_name}/{job.object_name}"
                
            job_instances[job_id] = job

        # Add completion events for concurrent groups
        for subfolder_name, groups in concurrent_groups.items():
            for group_name, job_ids in groups.items():
                if len(job_ids) > 1:  # Only create events for actual concurrent groups
                    completion_event = f"{subfolder_name}_{group_name}_COMPLETE"
                    for job_id in job_ids:
                        if job_id in job_instances:
                            job_instances[job_id].events_to_add.append(AddEvents([Event(event=completion_event)]))

        # Create logical dependencies between subfolders using events
        # This is handled through the subfolder events (wait/add/delete) defined in the AI response

        # Generate JSON
        raw_json = workflow.dumps_json()

        # Save JSON to output.json
        output_file = "output.json"
        with open(output_file, "w") as f:
            f.write(raw_json)

        # Build the workflow using Python client
        app.logger.info("🔨 Building workflow")
        build_result = workflow.build()
        if build_result.errors:
            app.logger.error(f"❌ Build errors: {build_result.errors}")
            deployment_status = {
                "success": False,
                "message": "Workflow build failed",
                "errors": build_result.errors
            }
        else:
            # Deploy the workflow using Python client
            app.logger.info("🚀 Deploying workflow")
            deploy_result = workflow.deploy()
            if deploy_result.errors:
                app.logger.error(f"❌ Deploy errors: {deploy_result.errors}")
                deployment_status = {
                    "success": False,
                    "message": "Workflow deployment failed",
                    "errors": deploy_result.errors
                }
            else:
                deployment_status = {
                    "success": True,
                    "message": "Workflow successfully built and deployed",
                    "build_result": str(build_result),
                    "deploy_result": str(deploy_result)
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
                        "object_name": job_instances[job_id].object_name,
                        "subfolder": job_data.get('subfolder', None)
                    }
                    for job_id, job_data in zip(job_instances.keys(), jobs_data)
                ],
                "folder_name": "industry-specific-job-name",
                        "subfolders": [
                    {
                        "name": subfolder_data['name'],
                        "description": subfolder_data.get('description', ''),
                        "events": subfolder_data['events']
                    }
                    for subfolder_data in subfolders_data
                ],
                "concurrent_groups": concurrent_groups,
            },
            "workflow_json": raw_json,
            "environment": environment,
            "controlm_server": controlm_server,
            "folder_name": formatted_folder_name,
            "user_code": user_code,
            "ai_generated": True,
            "use_case": use_case
        }

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"❌ Error during AI workflow deployment: {str(e)}")
        return jsonify({
            "error": "AI workflow deployment failed",
            "details": str(e)
        }), 500




if __name__ == '__main__':
    app.run(debug=True)
