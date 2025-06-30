from flask import Blueprint, request, jsonify, Response
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
# from ctm_python_client.core.folder import SubFolder
# from ctm_python_client.core.event import Event, AddEvents, WaitForEvents, DeleteEvents


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

manualworkflow_bp = Blueprint('manualworkflow', __name__)

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


@manualworkflow_bp.route("/proposed_workflow", methods=["POST"])
def proposed_workflow():
    try:
        data = request.json
        use_case = data.get("use_case")

        if not use_case:
            return jsonify({"error": "Use case is required."}), 400

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
                                "technologies": ["Technology1", "Technology2"]
                            }}
                            IMPORTANT: 
                            1. Only use technologies from the provided list
                            2. Do NOT modify or rename the technologies - use them exactly as they appear in the list
                            3. Return ONLY the JSON object, no markdown formatting, no code blocks, no additional text
                            4. Make sure the response is valid JSON
                            5. Focus on suggesting the most relevant technologies for the use case"""
                        },
                        {
                            "role": "user",
                            "content": f"""Based on the following use case, suggest a list of technologies that would best solve this business need.
                            Use Case: {use_case}
                            
                            Remember to ONLY use technologies from this list: {available_technologies}
                            Do NOT modify the technology names - use them exactly as they appear in the list.
                            
                            Return ONLY a JSON object with the suggested technologies array. No markdown, no code blocks, no additional text."""
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
                yield json.dumps({"error": str(e)})

        return Response(generate_stream(), content_type="text/plain")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@manualworkflow_bp.route("/create_workflow", methods=["POST"])
def create_workflow():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided in request"}), 400

        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies
        environment = data.get('environment', 'saas_dev')  # Default to saas_dev if not specified
        user_code = data.get('user_code', 'LBA')  # Default to LBA if not specified
        folder_name = data.get('folder_name', 'demo-genai')
        application = data.get('application', 'demo-genai')
        sub_application = data.get('sub_application', 'demo-genai')
        controlm_server = data.get('controlm_server', 'IN01')

        if not technologies or not use_case:
            return jsonify({"error": "Technologies and use case are required."}), 400
        
        # Validate environment
        valid_environments = ['saas_dev', 'saas_preprod', 'saas_prod', 'vse_dev', 'vse_qa', 'vse_prod']
        if environment not in valid_environments:
            return jsonify({"error": f"Invalid environment. Must be one of: {valid_environments}"}), 400

        # Create the workflow with the job names from the library
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
            
            # Use the original job name from the library
            job.object_name = job.object_name  # Keep the original name from job library
            
            workflow.add(job, inpath=formatted_folder_name)
            job_paths.append(f"{formatted_folder_name}/{job.object_name}")
            ordered_jobs.append(job.object_name)

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


@manualworkflow_bp.route("/generate_workflow", methods=["POST"])
def generate_workflow():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided in request"}), 400

        requested_jobs = data.get('jobs', [])
        environment = data.get('environment', 'saas_dev')
        folder_name = data.get('folder_name', 'LBA_demo-genai')
        user_code = data.get('user_code', 'LBA')

        if not requested_jobs:
            return jsonify({"error": "No jobs provided in request"}), 400

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
        
        # Save JSON to output.json
        try:
            with open("output.json", "w") as f:
                f.write(raw_json)
        except Exception as e:
            return jsonify({"error": f"Failed to save workflow JSON: {str(e)}"}), 500

        return jsonify({
            "message": "Workflow generated successfully",
            "workflow": raw_json,
            "environment": environment,
            "controlm_server": controlm_server,
            "folder_name": formatted_folder_name
        }), 200

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@manualworkflow_bp.route("/generate_manual_workflow", methods=["POST"])
def generate_manual_workflow():
    """
    Generate a complex workflow with subfolders based on AI suggested and/or manually selected technologies.
    Creates workflow with proper naming standard: [usercode]-* for folders and jobs.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided in request"}), 400

        # Extract input parameters - only the essential ones
        technologies = data.get("technologies", [])
        use_case = data.get("use_case", "")
        user_code = data.get("user_code", "LBA")

        if not technologies:
            return jsonify({"error": "Technologies are required."}), 400

        if not use_case:
            return jsonify({"error": "Use case is required."}), 400

        # Use default values for environment and naming
        environment = 'saas_dev'
        folder_name = 'demo-genai'
        application = 'demo-genai'
        sub_application = 'demo-genai'

        # Set Control-M server based on environment
        controlm_server = "IN01"

        # Generate complex workflow using AI
        try:
            completion = client.chat.completions.create(
                model=azure_openai_deployment,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert BMC Control-M workflow architect that creates complex workflows with multiple subfolders, realistic job dependencies, and logical business processes.

                        CRITICAL REQUIREMENTS:
                        1. Use ALL technologies from this exact list: {technologies} - EVERY technology must be represented by at least one job
                        2. Create AT LEAST 3 subfolders per workflow representing logical phases
                        3. Subfolder names should be personalized based on the use case
                        4. Create logical dependencies BETWEEN SUBFOLDERS using events
                        5. Each subfolder should have AT LEAST 2 jobs total
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

                        MANDATORY TECHNOLOGY USAGE:
                        - You MUST create at least one job for EACH technology in the list: {technologies}
                        - Do NOT skip any technology - every technology must be represented
                        - If you need more jobs to create a realistic workflow, you can use the same technology multiple times
                        - The "type" field for each job must be exactly one of the technologies from the list
                        - Count the technologies and ensure you have at least that many jobs

                        JOB NAMING AND LOGIC:
                        - Each job must have a descriptive, logical name (like "{user_code}-Analyse-Data-Hadoop", "{user_code}-Cleansing-Transformation-Spark")
                        - NEVER use generic names like "job1", "jobA", "process1" - always be descriptive and business-relevant
                        - MANDATORY: Every job name MUST start with "{user_code}-" prefix
                        - MANDATORY: Ensure every technology in {technologies} is used at least once

                        FOLDER AND SUBFOLDER NAMING:
                        - Folder names should be descriptive and use case-specific
                        - Use ONLY letters, digits, and hyphens (-) in folder and subfolder names
                        - NO underscores (_) or other special characters allowed
                        - Examples: "{user_code}-customer-data-processing", "{user_code}-inventory-management", "{user_code}-sales-reporting"
                        - MANDATORY: Every folder and subfolder name MUST start with "{user_code}-" prefix

                        CONCURRENT JOB PATTERNS WITH DEPENDENCIES:
                        - Be flexible and realistic based on the use case
                        - Some subfolders might have 2-3 concurrent jobs, others might have 4-5
                        - Consider what makes sense for the business process
                        - Create realistic intra-subfolder dependencies where some jobs wait for others
                        - Example patterns:
                          * Phase 1: Data collection (2-3 concurrent jobs gathering different data sources)
                          * Phase 2: Data processing (2-3 concurrent jobs processing the collected data)
                          * Phase 3: Reporting/Analysis (1-2 jobs creating final outputs)
                        - Let the use case drive the number of concurrent jobs, not arbitrary rules

                        INTRA-SUBFOLDER DEPENDENCIES:
                        - Some jobs within the same subfolder should wait for other concurrent jobs to finish
                        - Use the "wait_for_jobs" field to specify which jobs must complete first
                        - Create realistic business logic (e.g., data validation waits for data extraction, aggregation waits for individual processing)
                        - Example: In a data processing subfolder:
                          * Jobs 1-2: Extract data from different sources (concurrent)
                          * Job 3: Validate all extracted data (waits for jobs 1-2)
                          * Job 4: Aggregate validated data (waits for job 3)
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
                        - Ensure ALL technologies are from the provided list and ALL are used
                        - Create a logical flow: Phase1 -> Phase2 -> Phase3
                        - Each subfolder should have a unique phase number
                        - Be creative and realistic with concurrent job patterns based on the use case
                        - Each job must have a unique, logical name that clearly describes its purpose
                        - Use the exact technology names from the provided list for the "type" field
                        - MANDATORY: Verify that every technology in {technologies} is used at least once"""
                    },
                    {
                        "role": "user",
                        "content": f"""Create a complex BMC Control-M workflow for this use case:
                        
                        Use Case: {use_case}
                        Technologies: {technologies}
                        
                        CRITICAL REQUIREMENTS:
                        - Use ALL technologies from the list: {technologies} - every technology must be represented
                        - At least 3 subfolders representing logical phases
                        - Create realistic concurrent job patterns based on the use case
                        - Mix concurrent and dependent jobs within subfolders for realistic business logic
                        - Some jobs should run concurrently, others should wait for specific jobs to complete
                        - Use the "wait_for_jobs" field to create logical dependencies within subfolders
                        - Create logical dependencies between subfolders using events
                        - Use only technologies from: {technologies}
                        - Each job must have a descriptive, logical name (like "Analyse-Data-Hadoop", "Cleansing-Transformation-Spark")
                        - NEVER use generic names like "job1", "jobA", "process1" - always be descriptive and business-relevant
                        - MANDATORY: Ensure every technology in {technologies} is used at least once
                        
                        Let the use case drive the workflow design - be creative and realistic with job patterns."""
                    }
                ]
            )

            response_content = completion.choices[0].message.content.strip()

            def extract_json_from_response(text):
                try:
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    return json.loads(text[start:end])
                except Exception as e:
                    return None

            ai_workflow = extract_json_from_response(response_content)
            if ai_workflow and 'folder_name' in ai_workflow and 'subfolders' in ai_workflow and 'jobs' in ai_workflow:
                # Use the AI-generated workflow data
                folder_name = ai_workflow['folder_name']
                subfolders_data = ai_workflow['subfolders']
                jobs_data = ai_workflow['jobs']
                
                # Validate that all technologies are used
                used_technologies = set(job['type'] for job in jobs_data)
                missing_technologies = set(technologies) - used_technologies
                
                if missing_technologies:
                    print(f"WARNING: AI did not use all technologies. Missing: {missing_technologies}")
                    print("Adding missing technologies to the workflow...")
                    
                    # Add missing technologies as additional jobs
                    for i, missing_tech in enumerate(missing_technologies):
                        # Find a suitable subfolder (use the first one if available)
                        target_subfolder = subfolders_data[0]['name'] if subfolders_data else "Main Workflow"
                        
                        # Create a job for the missing technology
                        missing_job = {
                            "id": f"missing-job-{i}",
                            "name": f"Process-{missing_tech}",
                            "type": missing_tech,
                            "subfolder": target_subfolder,
                            "concurrent_group": "missing-group",
                            "wait_for_jobs": []
                        }
                        jobs_data.append(missing_job)
                
                # Log the AI-generated structure
                print(f"AI Generated Workflow Structure:")
                print(f"Folder Name: {folder_name}")
                print(f"Subfolders: {[sf['name'] for sf in subfolders_data]}")
                print(f"Jobs: {[job['name'] for job in jobs_data]}")
                print(f"Technologies used: {[job['type'] for job in jobs_data]}")
                
            else:
                # Fallback to simple structure
                folder_name = f"{use_case.replace(' ', '-').lower()}-workflow"
                subfolders_data = [
                    {
                        "name": "Main-Workflow",
                        "description": f"Workflow for {use_case}",
                        "phase": 1,
                        "events": {
                            "add": [],
                            "wait": [],
                            "delete": []
                        }
                    }
                ]
                jobs_data = [
                    {
                        "id": f"job-{i}",
                        "name": tech,
                        "type": tech,
                        "subfolder": "Main-Workflow",
                        "concurrent_group": "group-1",
                        "wait_for_jobs": []
                    }
                    for i, tech in enumerate(technologies)
                ]

        except Exception as e:
            # Fallback to simple structure if AI fails
            print(f"AI generation failed: {str(e)}")
            folder_name = f"{use_case.replace(' ', '-').lower()}-workflow"
            subfolders_data = [
                {
                    "name": "Main-Workflow",
                    "description": f"Workflow for {use_case}",
                    "phase": 1,
                    "events": {
                        "add": [],
                        "wait": [],
                        "delete": []
                    }
                }
            ]
            jobs_data = [
                {
                    "id": f"job-{i}",
                    "name": tech,
                    "type": tech,
                    "subfolder": "Main-Workflow",
                    "concurrent_group": "group-1",
                    "wait_for_jobs": []
                }
                for i, tech in enumerate(technologies)
            ]

        # Final validation to ensure all technologies are used
        used_technologies = set(job['type'] for job in jobs_data)
        missing_technologies = set(technologies) - used_technologies
        
        if missing_technologies:
            print(f"FINAL VALIDATION: Still missing technologies: {missing_technologies}")
            print("Adding missing technologies as additional jobs...")
            
            # Add missing technologies as additional jobs
            for i, missing_tech in enumerate(missing_technologies):
                # Find a suitable subfolder (use the first one if available)
                target_subfolder = subfolders_data[0]['name'] if subfolders_data else "Main Workflow"
                
                # Create a job for the missing technology
                missing_job = {
                    "id": f"missing-job-{i}",
                    "name": f"Process-{missing_tech}",
                    "type": missing_tech,
                    "subfolder": target_subfolder,
                    "concurrent_group": "missing-group",
                    "wait_for_jobs": []
                }
                jobs_data.append(missing_job)

        # Use AI-generated folder name with proper formatting
        sanitized_folder_name = sanitize_name(folder_name, user_code)

        # Create the workflow
        try:
            my_env = Environment.create_saas(
                endpoint=my_secrets[f'{environment}_endpoint'],
                api_key=my_secrets[f'{environment}_api_key']
            )

            # Format names with user code
            formatted_folder_name = sanitized_folder_name
            formatted_application = sanitize_name(application, user_code)
            formatted_sub_application = sanitize_name(sub_application, user_code)

            defaults = WorkflowDefaults(
                run_as="ctmagent",
                host="zzz-linux-agents",
                application=formatted_application,
                sub_application=formatted_sub_application
            )

            workflow = Workflow(my_env, defaults=defaults)
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

            raw_json = workflow.dumps_json()
            
            # Save JSON to output.json
            try:
                with open("output.json", "w") as f:
                    f.write(raw_json)
            except Exception as e:
                return jsonify({"error": f"Failed to save workflow JSON: {str(e)}"}), 500

            # Create complex workflow structure for frontend
            complex_workflow = {
                "folder_name": formatted_folder_name,
                "subfolders": subfolders_data,
                "jobs": [
                    {
                        "id": job_data['id'],
                        "name": job_data['name'],
                        "type": job_data['type'],
                        "object_name": job_instances[job_data['id']].object_name,
                        "subfolder": job_data.get('subfolder', None),
                        "concurrent_group": job_data.get('concurrent_group', 'default'),
                        "wait_for_jobs": job_data.get('wait_for_jobs', [])
                    }
                    for job_data in jobs_data
                ],
                "concurrent_groups": concurrent_groups,
                "optimal_order": [job_data['id'] for job_data in jobs_data]
            }

            # Log the generated workflow details
            print(f"Generated Manual Workflow:")
            print(f"Folder Name: {formatted_folder_name}")
            print(f"Subfolders: {[sf['name'] for sf in subfolders_data]}")
            print(f"Jobs: {[job['name'] for job in jobs_data]}")
            print(f"Technologies used: {[job['type'] for job in jobs_data]}")
            print(f"Sanitized Job Names: {[job_instances[job_data['id']].object_name for job_data in jobs_data]}")
            print(f"All selected technologies included: {set(technologies) == set(job['type'] for job in jobs_data)}")

            return jsonify({
                "success": True,
                "message": "Complex workflow generated successfully",
                "workflow": complex_workflow,
                "workflow_json": raw_json,
                "environment": environment,
                "controlm_server": controlm_server,
                "folder_name": formatted_folder_name,
                "user_code": user_code,
                "ai_generated": False,
                "use_case": use_case,
                "technologies_used": list(set(job['type'] for job in jobs_data)),
                "all_technologies_included": set(technologies) == set(job['type'] for job in jobs_data)
            }), 200

        except Exception as e:
            return jsonify({
                "error": "Manual workflow generation failed",
                "details": str(e)
            }), 500

    except Exception as e:
        return jsonify({
            "error": "Manual workflow generation failed",
            "details": str(e)
        }), 500


@manualworkflow_bp.route("/deploy_manual_workflow", methods=["POST"])
def deploy_manual_workflow():
    """
    Deploy a manual workflow to Control-M using the output from generate_manual_workflow.
    Follows the same logic as deploy_ai_workflow for complex workflow handling.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided in request"}), 400

        # Add comprehensive logging for troubleshooting
        print("=" * 80)
        print("DEPLOY MANUAL WORKFLOW - INPUT DATA:")
        print("=" * 80)
        print(f"Received data keys: {list(data.keys())}")
        print(f"Data: {json.dumps(data, indent=2)}")
        print()

        # Extract deployment configuration from request
        environment = data.get('environment', 'saas_dev')
        user_code = data.get('user_code', 'LBA')
        folder_name = data.get('folder_name', 'demo-genai')
        application = data.get('application', 'demo-genai')
        sub_application = data.get('sub_application', 'demo-genai')
        
        # Extract workflow data from generate_manual_workflow output
        complex_workflow = data.get('workflow', {})
        technologies = data.get('technologies', [])
        optimal_order = data.get('optimal_order', [])

        print("EXTRACTED DATA:")
        print(f"Environment: {environment}")
        print(f"User Code: {user_code}")
        print(f"Folder Name: {folder_name}")
        print(f"Application: {application}")
        print(f"Sub Application: {sub_application}")
        print(f"Technologies: {technologies}")
        print(f"Optimal Order: {optimal_order}")
        print(f"Complex Workflow Keys: {list(complex_workflow.keys()) if complex_workflow else 'None'}")
        print()

        # Validate required data
        if not complex_workflow:
            return jsonify({"error": "Complex workflow data is required from generate_manual_workflow output"}), 400

        if not technologies:
            return jsonify({"error": "Technologies are required"}), 400

        if not user_code:
            return jsonify({"error": "User code is required"}), 400

        # Validate complex workflow structure
        if 'jobs' not in complex_workflow or 'subfolders' not in complex_workflow:
            return jsonify({"error": "Invalid complex workflow structure - missing jobs or subfolders"}), 400

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

        print("VALIDATION PASSED:")
        print(f"Control-M Server: {controlm_server}")
        print(f"Complex Workflow Jobs Count: {len(complex_workflow.get('jobs', []))}")
        print(f"Complex Workflow Subfolders Count: {len(complex_workflow.get('subfolders', []))}")
        print()

        try:
            # Create environment connection
            print("CREATING ENVIRONMENT CONNECTION...")
            my_env = Environment.create_saas(
                endpoint=my_secrets[f'{environment}_endpoint'],
                api_key=my_secrets[f'{environment}_api_key']
            )
            print("Environment connection created successfully")

            # Sanitize and format names with user code
            sanitized_folder = sanitize_name(folder_name, user_code) if folder_name else 'demo-genai'
            sanitized_app = sanitize_name(application, user_code) if application else 'demo-genai'
            sanitized_sub_app = sanitize_name(sub_application, user_code) if sub_application else 'demo-genai'

            # Format names with user code
            formatted_folder_name = sanitized_folder
            formatted_application = sanitized_app
            formatted_sub_application = sanitized_sub_app

            print("FORMATTED NAMES:")
            print(f"Folder: {formatted_folder_name}")
            print(f"Application: {formatted_application}")
            print(f"Sub Application: {formatted_sub_application}")
            print()

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

            # Extract subfolders and jobs data
            subfolders_data = complex_workflow['subfolders']
            jobs_data = complex_workflow['jobs']

            # Create subfolders
            subfolder_map = {}
            print("CREATING SUBFOLDERS:")
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
                print(f"  Created subfolder: {subfolder_name}")

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

            print("ADDING JOBS TO WORKFLOW:")
            for job_data in jobs_data:
                job_id = job_data['id']
                job_type = job_data['type']
                job_name = job_data['name']
                job_subfolder = job_data.get('subfolder', '')

                print(f"Processing job: {job_type} -> {job_name} in subfolder: {job_subfolder}")

                if job_type not in JOB_LIBRARY:
                    return jsonify({"error": f"Unknown job type: {job_type}"}), 400

                # Create job instance
                job = JOB_LIBRARY[job_type]()
                job.object_name = job_name
                
                # Add job to appropriate subfolder or main folder
                if job_subfolder and job_subfolder in subfolder_map:
                    subfolder_name = sanitize_name(job_subfolder, user_code)
                    subfolder_path = f"{formatted_folder_name}/{subfolder_name}"
                    workflow.add(job, inpath=subfolder_path)
                    job_paths[job_id] = f"{subfolder_path}/{job.object_name}"
                    print(f"  Added job: {job_name} at path: {job_paths[job_id]}")
                else:
                    workflow.add(job, inpath=formatted_folder_name)
                    job_paths[job_id] = f"{formatted_folder_name}/{job.object_name}"
                    print(f"  Added job: {job_name} at path: {job_paths[job_id]}")
                    
                job_instances[job_id] = job

            # Add completion events for concurrent groups
            print("ADDING CONCURRENT GROUP EVENTS:")
            for subfolder_name, groups in concurrent_groups.items():
                for group_name, job_ids in groups.items():
                    if len(job_ids) > 1:  # Only create events for actual concurrent groups
                        completion_event = f"{subfolder_name}_{group_name}_COMPLETE"
                        for job_id in job_ids:
                            if job_id in job_instances:
                                job_instances[job_id].events_to_add.append(AddEvents([Event(event=completion_event)]))
                                print(f"  Added completion event {completion_event} to job {job_id}")

            # Create job dependencies based on wait_for_jobs
            print("CREATING JOB DEPENDENCIES:")
            for job_data in jobs_data:
                job_id = job_data['id']
                wait_for_jobs = job_data.get('wait_for_jobs', [])
                
                if wait_for_jobs:
                    print(f"Job {job_data['name']} waits for: {wait_for_jobs}")
                    for dependency_name in wait_for_jobs:
                        # Find the job with this name
                        for dep_job_data in jobs_data:
                            if dep_job_data['name'] == dependency_name:
                                dep_job_id = dep_job_data['id']
                                if dep_job_id in job_paths and job_id in job_paths:
                                    workflow.connect(job_paths[dep_job_id], job_paths[job_id])
                                    print(f"  Connected: {dependency_name} -> {job_data['name']}")
                                break

            print()

            # Generate JSON
            print("GENERATING WORKFLOW JSON...")
            raw_json = workflow.dumps_json()

            # Save JSON to output.json
            output_file = "output.json"
            with open(output_file, "w") as f:
                f.write(raw_json)
            print("Workflow JSON saved to output.json")

            # Build the workflow
            print("BUILDING WORKFLOW...")
            build_result = workflow.build()
            if build_result.errors:
                print(f"BUILD ERRORS: {build_result.errors}")
                return jsonify({
                    "error": "Workflow build failed",
                    "details": build_result.errors
                }), 500
            print("Workflow built successfully")
            
            # Deploy the workflow
            print("DEPLOYING WORKFLOW...")
            deploy_result = workflow.deploy()
            if deploy_result.errors:
                print(f"DEPLOY ERRORS: {deploy_result.errors}")
                return jsonify({
                    "error": "Workflow deployment failed",
                    "details": deploy_result.errors
                }), 500
            print("Workflow deployed successfully")
            
            print("=" * 80)
            print("DEPLOYMENT SUCCESSFUL!")
            print("=" * 80)
            
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
                    "folder_name": formatted_folder_name,
                    "subfolders": [
                        {
                            "name": subfolder_data['name'],
                            "description": subfolder_data.get('description', ''),
                            "events": subfolder_data['events']
                        }
                        for subfolder_data in subfolders_data
                    ]
                },
                "message": "Manual workflow deployed successfully",
                "build_result": str(build_result),
                "deploy_result": str(deploy_result),
                "environment": environment,
                "controlm_server": controlm_server,
                "folder_name": formatted_folder_name,
                "application": formatted_application,
                "sub_application": formatted_sub_application,
                "total_jobs": len(job_instances),
                "total_subfolders": len(subfolders_data)
            }
            
            return jsonify(response), 200

        except Exception as e:
            print(f"WORKFLOW CREATION/BUILD/DEPLOY ERROR: {str(e)}")
            print("=" * 80)
            return jsonify({
                "error": "Workflow creation/build/deploy failed",
                "details": str(e)
            }), 500

    except Exception as e:
        print(f"UNEXPECTED ERROR: {str(e)}")
        print("=" * 80)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500 