from flask import Flask, request, jsonify, Response
from ctm_python_client.core.workflow import *
from ctm_python_client.core.credential import *
from ctm_python_client.core.comm import *
from aapi import *
from my_secrets import my_secrets
import subprocess
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from openai import AzureOpenAI  
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



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/generate_workflow', methods=['POST'])
def generate_workflow():
    data = request.get_json()
    
    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' in request."}), 400

    requested_jobs = data['jobs']

    # ENV & defaults
    my_env = Environment.create_saas(
        endpoint=my_secrets['helix_sandbox_endpoint'],
        api_key=my_secrets['helix_sandbox_api_key']
    )

    defaults = WorkflowDefaults(
        run_as="ctmagent",
        host="zzz-linux-agents",
        application="LBA-DMO-GEN",
        sub_application="TEST-APP"
    )

    workflow = Workflow(my_env, defaults=defaults)
    folder_name = "LBA_DEMGEN_VB"
    folder = Folder(folder_name, site_standard="Empty", controlm_server="IN01")
    workflow.add(folder)



    job_paths = []

    for job_key in requested_jobs:
        if job_key not in JOB_LIBRARY:
            return jsonify({"error": f"Unknown job: {job_key}"}), 400

        job = JOB_LIBRARY[job_key]()
        workflow.add(job, inpath=folder_name)
        job_paths.append(f"{folder_name}/{job.object_name}")

    #Chaining jobs
    for i in range(len(job_paths) - 1):
        workflow.connect(job_paths[i], job_paths[i + 1])


       
    raw_json = workflow.dumps_json()
    print(raw_json)


    # Check for build and deploy errors
    build_errors = workflow.build().errors
    deploy_errors = workflow.deploy().errors

    print(build_errors)
    print(deploy_errors)

    # If no errors, save JSON and run CLI commands
    if build_errors is None and deploy_errors is None:
        # Save JSON to output.json
        with open("output.json", "w") as f:
            f.write(raw_json)
        print("Workflow JSON saved to output.json")

        # Run the Control-M CLI commands
        try:
            subprocess.run(["ctm", "build", "output.json"], check=True)
            subprocess.run(["ctm", "deploy", "output.json"], check=True)
            print("Build and deploy commands executed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running Control-M commands: {e}")

        
    
    return Response(raw_json, mimetype='application/json')


@app.route("/generate", methods=["POST"])
def generate():
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
                    "content": "You are an assistant that organizes technologies into an optimized workflow order for BMC Control-M based on a use case."
                },
                {
                    "role": "user",
                    "content": f"Technologies: {technologies}\nUse Case: {use_case}\nProvide the optimal order of technologies in JSON format like this: {{\"workflow_order\": [\"Technology1\", \"Technology2\"]}}."
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
            return jsonify({"optimal_order": ordered_workflow.get("workflow_order")}), 200
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
                            Your response must follow this exact structure:
                            1. Workflow Name: A concise, descriptive name based on the use case
                            2. Introduction: A brief overview of the workflow's purpose
                            3. Use Case Overview: High-level description of the business need
                            4. Use Case Technical Explanation: Detailed technical explanation of how the workflow operates
                            5. Job Types Included: List and description of each technology in the workflow
                            
                            Format your response with clear section headers and professional, technical language."""
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

        if not technologies or not use_case or not renamed_technologies:
            return jsonify({"error": "Technologies, use case, and renamed technologies are required."}), 400
        
        app.logger.info(f"🔄 Deploying Personalized Workflow for Use Case: {use_case}")

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
            app.logger.error(f"❌ Error parsing Control-M job names: {str(e)}")
            return jsonify({"error": "Failed to parse Control-M job names"}), 500

        # Create the workflow with the new job names
        my_env = Environment.create_saas(
            endpoint=my_secrets['helix_sandbox_endpoint'],
            api_key=my_secrets['helix_sandbox_api_key']
        )

        defaults = WorkflowDefaults(
            run_as="ctmagent",
            host="zzz-linux-agents",
            application="LBA-DMO-GEN",
            sub_application="TEST-APP"
        )

        workflow = Workflow(my_env, defaults=defaults)
        folder_name = "LBA_DEMGEN_VB"
        folder = Folder(folder_name, site_standard="Empty", controlm_server="IN01")
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
            
            workflow.add(job, inpath=folder_name)
            job_paths.append(f"{folder_name}/{new_name}")
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
                    "ordered_jobs": ordered_jobs
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
        app.logger.error(f"❌ Error deploying personalized workflow: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
