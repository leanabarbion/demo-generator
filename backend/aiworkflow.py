from flask import Blueprint, request, jsonify
import json
import re
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from ctm_python_client.core.workflow import *
from ctm_python_client.core.credential import *
from ctm_python_client.core.comm import *
from aapi import *
from my_secrets import *
from job_library import JOB_LIBRARY

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

aiworkflow_bp = Blueprint('aiworkflow', __name__)

def sanitize_name(name, user_code):
    """
    Sanitize names to follow the naming standard: [usercode]-* with only letters, digits, and hyphens.
    
    Args:
        name (str): The original name to sanitize
        user_code (str): The user code to prefix the name with
    
    Returns:
        str: Sanitized name in format [usercode]-[sanitized-name]
    """
    # Remove any existing user code prefix if present
    if name.startswith(f"{user_code}-"):
        name = name[len(f"{user_code}-"):]
    
    # Replace any non-alphanumeric characters with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9]', '-', name)
    
    # Remove multiple consecutive hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    
    # Remove leading and trailing hyphens
    sanitized = sanitized.strip('-')
    
    # Ensure the name is not empty after sanitization
    if not sanitized:
        sanitized = "default"
    
    # Convert to lowercase
    sanitized = sanitized.lower()
    
    # Add user code prefix
    return f"{user_code}-{sanitized}"


@aiworkflow_bp.route('/ai_generated_workflow', methods=['POST'])
def ai_generated_workflow():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided in request."}), 400

    # Check if this is an AI-generated workflow request
    use_case = data.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing 'use_case' in request."}), 400

    # AI-powered workflow generation
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
            
        except Exception as e:
            return jsonify({"error": "Failed to parse AI-generated workflow"}), 500
                

    except Exception as e:
        return jsonify({"error": "Failed to generate AI workflow"}), 500

    # Common workflow creation logic
    environment = data.get('environment', 'saas_dev')
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
    formatted_folder_name = sanitize_name(folder_name, user_code)
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    try:
        # Create environment connection
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
        workflow = Workflow(my_env, defaults=defaults)
        
        # Create main folder
        folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
        workflow.add(folder)

        # Create subfolders
        subfolder_map = {}
        for subfolder_data in subfolders_data:
            subfolder_name = sanitize_name(subfolder_data['name'], user_code)
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
            job.object_name = sanitize_name(job_data['name'], user_code)
            
            # Add job to appropriate subfolder or main folder
            if 'subfolder' in job_data and job_data['subfolder'] in subfolder_map:
                subfolder_name = sanitize_name(job_data['subfolder'], user_code)
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

        # Generate JSON
        raw_json = workflow.dumps_json()

        # Save JSON to output.json
        output_file = "output.json"
        with open(output_file, "w") as f:
            f.write(raw_json)

        # Build the workflow using Python client
        build_result = workflow.build()
        if build_result.errors:
            deployment_status = {
                "success": False,
                "message": "Workflow build failed",
                "errors": build_result.errors
            }
        else:
            # Deploy the workflow using Python client
            deploy_result = workflow.deploy()
            if deploy_result.errors:
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
        return jsonify({
            "error": "AI workflow generation failed",
            "details": str(e)
        }), 500


@aiworkflow_bp.route('/ai_prompt_workflow', methods=['POST'])
def ai_prompt_workflow():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided in request."}), 400

    # Check if this is an AI-generated workflow request
    use_case = data.get('use_case')
    if not use_case:
        return jsonify({"error": "Missing 'use_case' in request."}), 400

    # AI-powered workflow generation
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
        return jsonify({"error": "Failed to generate AI workflow"}), 500


@aiworkflow_bp.route('/deploy_ai_workflow', methods=['POST'])
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

    except Exception as e:
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
    formatted_folder_name = sanitize_name(folder_name, user_code)
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    try:
        # Create environment connection
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
        workflow = Workflow(my_env, defaults=defaults)
        
        # Create main folder
        folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
        workflow.add(folder)

        # Create subfolders
        subfolder_map = {}
        for subfolder_data in subfolders_data:
            subfolder_name = sanitize_name(subfolder_data['name'], user_code)
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
            job.object_name = sanitize_name(job_data['name'], user_code)
            
            # Add job to appropriate subfolder or main folder
            if 'subfolder' in job_data and job_data['subfolder'] in subfolder_map:
                subfolder_name = sanitize_name(job_data['subfolder'], user_code)
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

        # Generate JSON
        raw_json = workflow.dumps_json()

        # Save JSON to output.json
        output_file = "output.json"
        with open(output_file, "w") as f:
            f.write(raw_json)

        # Build the workflow using Python client
        build_result = workflow.build()
        if build_result.errors:
            deployment_status = {
                "success": False,
                "message": "Workflow build failed",
                "errors": build_result.errors
            }
        else:
            # Deploy the workflow using Python client
            deploy_result = workflow.deploy()
            if deploy_result.errors:
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
        return jsonify({
            "error": "AI workflow deployment failed",
            "details": str(e)
        }), 500 