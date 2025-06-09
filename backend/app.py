import os
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, make_response
import json
from flask_cors import CORS
import jobs
import base64
import requests
from datetime import datetime

from simple_workflow import initialize_workflow
from ctm_python_client.core.workflow import JobCommand

from ctm_python_client.core.workflow import *
from ctm_python_client.core.comm import *
from ctm_python_client.core.credential import *
from aapi import *
from my_secrets import my_secrets
import attr
import connectionprofile




# Load environment variables from .env file
load_dotenv()

# # Access the OpenAI API key from environment variables
# openai_api_key = os.getenv("Azure_OpenAI")

# # Initialize OpenAI client
# client = OpenAI(api_key=openai_api_key)


# Load from .env
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

# GitHub Config (store token securely in .env)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "leanabarbion"
REPO_NAME = "workflow-repo"  # Replace with your repo name
BRANCH = "main"
BASE_FOLDER_PATH = "jobs"# Folder where files will be uploaded




# Import all job classes you want to support
from ctm_python_client.core.workflow import (
    JobCommand, JobDatabase, JobDatabaseSQLScript, JobDatabaseEmbeddedQuery,
    JobDatabaseStoredProcedure, JobDatabaseMSSQLAgentJob, JobDatabaseMSSQL_SSIS,
    JobFileTransfer, JobHadoop, JobAwsEC2, JobAwsQuickSight
)

# Dynamic job type to class mapping
job_type_mapping = {
    "JobCommand": JobCommand,
    "JobDatabase": JobDatabase,
    "JobDatabaseSQLScript": JobDatabaseSQLScript,
    "JobDatabaseEmbeddedQuery": JobDatabaseEmbeddedQuery,
    "JobDatabaseStoredProcedure": JobDatabaseStoredProcedure,
    "JobDatabaseMSSQLAgentJob": JobDatabaseMSSQLAgentJob,
    "JobDatabaseMSSQL_SSIS": JobDatabaseMSSQL_SSIS,
    "JobFileTransfer": JobFileTransfer,
    "JobHadoop": JobHadoop,
    "JobAwsEC2": JobAwsEC2,
    "JobAwsQuickSight": JobAwsQuickSight,
}

# Utility: Find required fields of a job class
def get_required_fields(job_class):
    fields = attr.fields(job_class)
    required = []
    for f in fields:
        if f.default == attr.NOTHING and not f.init is False and not f.kw_only:
            required.append(f.name)
        if f.default == attr.NOTHING and f.kw_only:
            required.append(f.name)
    return required

app = Flask(__name__)

@app.route('/job_types', methods=['GET'])
def list_job_types():
    job_type_fields = {}

    for job_type, job_class in job_type_mapping.items():
        fields = attr.fields(job_class)
        required = [
            f.name for f in fields
            if f.default == attr.NOTHING and not f.init is False
        ]
        job_type_fields[job_type] = required

    return jsonify(job_type_fields)


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/generate_workflow_json', methods=['POST','OPTIONS'])
def generate_workflow_json():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.json

    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' list in request."}), 400

    job_definitions = data['jobs']

    if not isinstance(job_definitions, list) or len(job_definitions) < 1:
        return jsonify({"error": "'jobs' must be a list with at least one job definition."}), 400

    # Create the base workflow (environment, defaults)
    workflow, folder_name = initialize_workflow()

    job_names = []  # To connect jobs later

    for job_data in job_definitions:
        job_type = job_data.get('type')
        object_name = job_data.get('object_name')

        if not job_type or not object_name:
            return jsonify({"error": "Each job must have 'type' and 'object_name'."}), 400


        job_class = job_type_mapping.get(job_type)

        if not job_class:
            return jsonify({"error": f"Unsupported job type: {job_type}"}), 400

        # Validate required fields
        required_fields = get_required_fields(job_class)
        missing_fields = [field for field in required_fields if field not in job_data]

        if missing_fields:
            return jsonify({"error": f"Missing required fields for {job_type}: {missing_fields}"}), 400

        # Pass all fields except 'type' into constructor
        job_kwargs = {k: v for k, v in job_data.items() if k != 'type'}

        profile_json = get_connection_profile_for_job(object_name)
        # You can now include this profile in job_kwargs (if the job supports it)
        if "object_name" in [f.name for f in attr.fields(job_class)]:
            # You might want to extract the profile name key from the JSON
            profile_name = list(profile_json.keys())[0]
            job_kwargs.setdefault("object_name", profile_name)

        try:
            job = job_class(**job_kwargs)
        except Exception as e:
            return jsonify({"error": f"Failed to create {job_type}: {str(e)}"}), 400

        workflow.add(job, inpath=folder_name)

        job_names.append(f"{folder_name}/{object_name}")

    # Connect jobs in sequence
    for i in range(len(job_names) - 1):
        workflow.connect(job_names[i], job_names[i+1])    


    workflow_json = json.loads(workflow.dumps_json()) 
   

    return jsonify(workflow_json)



def get_connection_profile_for_job(job_name: str) -> dict:
    """
    Return the connection profile JSON for the given job_name.

    - If a function with the name job_name exists in connectionprofile.py, call it.
    - Otherwise return a default connection profile.
    """
    profile_func = getattr(connectionprofile, job_name, None)

    if callable(profile_func):
        return profile_func()
    else:
        return connectionprofile.Default_Connection_Profile()


def upload_to_github(file_path, content, message):
    """Uploads a file to GitHub repository using GitHub API."""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    # Get the SHA if the file exists (needed for updates)
    response = requests.get(url, headers=headers)
    print("GitHub Response:", response.json()) 
    sha = response.json().get("sha") if response.status_code == 200 else None

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
        return {"status": "error", "message": upload_response.json()}

@app.route("/upload-github", methods=["POST"])
def upload_github():
    """Endpoint to upload workflow and narrative files to GitHub."""
    try:
        data = request.json
        workflow_json = json.dumps(data.get("workflow_json", {}), indent=2)
        narrative_text = data.get("narrative_text", "")
        user_code = data.get("user_info", "unknown_user")

        if not workflow_json or not narrative_text:
            return jsonify({"error": "Missing workflow or narrative"}), 400

        # Generate a unique folder name (Timestamp format: YYYY-MM-DD_HH-MM-SS)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # folder_name = f"{BASE_FOLDER_PATH}/workflow_{timestamp}"  # e.g., jobs/workflow_2025-02-11_13-45-30
        folder_name = f"{BASE_FOLDER_PATH}/{user_code}_workflow_{timestamp}"


        # Define file paths inside this user-specific folder
        workflow_file = f"{folder_name}/{user_code}_workflow.json"
        narrative_file = f"{folder_name}/{user_code}_narrative.txt"
        metadata_file = f"{folder_name}/{user_code}_metadata.txt"

        # Upload both files
        upload_workflow = upload_to_github(workflow_file, workflow_json, "Added workflow JSON")
        upload_narrative = upload_to_github(narrative_file, narrative_text, "Added workflow narrative")

        # Optional: Upload metadata (user info, timestamp, etc.)
        metadata_content = f"Upload Time: {timestamp}\nUser Code: {user_code}"
        upload_metadata = upload_to_github(metadata_file, metadata_content, "Added metadata")


        return jsonify({"workflow": upload_workflow, "narrative": upload_narrative, "metadata": upload_metadata}), 200
        

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

def extract_json_from_response(response_content):
    """
    Extracts and validates a JSON block from the OpenAI response content.
    """
    try:
        if "```json" in response_content:
            json_start = response_content.find("{")
            json_end = response_content.rfind("}")
            if json_start != -1 and json_end != -1:
                json_block = response_content[json_start:json_end + 1]
                return json.loads(json_block)
        return json.loads(response_content)
    except json.JSONDecodeError:
        return None

@app.route("/generate", methods=["POST"])
def generate():
    """
    Generate an optimized order for selected technologies based on a use case using GPT.
    """
    try:
        data = request.json
        app.logger.info(f"Received Data: {json.dumps(data, indent=2)}")  # Debugging log

        print("Received Data:", data)  # Add this for debugging

        technologies = data.get("technologies")
        use_case = data.get("use_case")

        if not technologies or not use_case:
            return jsonify({"error": "Technologies and use case are required."}), 400

        # Use the OpenAI client to determine the best order for the workflow
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that organizes technologies into an optimized workflow order for BMC Control-M based on a use case."
                },
                {
                    "role": "user",
                    "content": f"Technologies: {technologies}\nUse Case: {use_case}\nProvide the optimal order of technologies in JSON format format like this: {{\"workflow_order\": [\"Technology1\", \"Technology2\"]}}."
                }
            ]
        )

        response_content = completion.choices[0].message.content.strip()
        app.logger.info(f"GPT Response: {response_content}")  # Debugging log

        ordered_workflow = extract_json_from_response(response_content)

        if ordered_workflow:
          response = {"optimal_order": ordered_workflow.get("workflow_order") or ordered_workflow.get("workflow")}
        else:
          response = {"optimal_order": technologies} 
    
        app.logger.info(f"Optimal Workflow Order: {json.dumps(response, indent=2)}")
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-workflow', methods=['POST'])
def save_workflow():
    """
    Save a workflow based on selected technologies.
    """
    try: 
        data = request.get_json()
        app.logger.info(f"📩 Received Data: {json.dumps(data, indent=2)}")

        if not data or 'workflow' not in data:
            return jsonify({"error": "Invalid data"}), 400
        
        workflow = data["workflow"]
        app.logger.info(f"✅ Workflow to be saved: {workflow}")  # Ensure correct workflow received


        response_data = {"WZA_DEMO_GEN": {"Type": "Folder", "ControlmServer": "Sandbox", "OrderMethod": "Manual"}}


        # Job function mapping
        job_function_mapping = {
    "SAP R/3": ("Run SAP R/3 job", "SAP_R3"),
    "SAP S/4 HANA": ("Run SAP S/4 HANA job", "SAP_S4_HANA"),
    "Oracle E-Business Suite": ("Run Oracle E-Business Suite job", "Oracle_E_Business_Suite"),
    "Oracle PeopleSoft": ("Run Oracle PeopleSoft job", "Oracle_PeopleSoft"),
    "IBM DB2": ("Run IBM DB2 job", "IBM_DB2"),
    "Oracle Database": ("Run Oracle Database job", "Oracle_Database"),
    "Microsoft SQL Server": ("Run Microsoft SQL Server job", "Microsoft_SQL_Server"),
    "PostgreSQL": ("Run PostgreSQL job", "PostgreSQL"),
    "Sybase / SAP ASE": ("Run Sybase / SAP ASE job", "Sybase_SAP_ASE"),
    "Java JDBC compliant DB": ("Run Java JDBC compliant DB job", "Java_JDBC_Compliant_DB"),
    "MySQL": ("Run MySQL job", "MySQL"),
    "Teradata": ("Run Teradata job", "Teradata"),
    "SAP HANA": ("Run SAP HANA job", "SAP_HANA"),
    "MongoDB": ("Run MongoDB job", "MongoDB"),
    "FTP FTPS": ("Run FTP FTPS job", "FTP_FTPS"),
    "SFTP": ("Run SFTP job", "SFTP"),
    "AS2": ("Run AS2 job", "AS2"),
    "Amazon S3": ("Run Amazon S3 job", "Amazon_S3"),
    "S3 Comp. Storage": ("Run S3 Comp. Storage job", "S3_Comp_Storage"),
    "Azure Blob Storage": ("Run Azure Blob Storage job", "Azure_Blob_Storage"),
    "Azure Data Lake Storage Gen2": ("Run Azure Data Lake Storage Gen2 job", "Azure_Data_Lake_Storage_Gen2"),
    "Google Cloud Storage": ("Run Google Cloud Storage job", "Google_Cloud_Storage"),
    "OCI Object Storage": ("Run OCI Object Storage job", "OCI_Object_Storage"),
    "AWS Data Pipeline": ("Run AWS Data Pipeline job", "AWS_Data_Pipeline"),
    "AWS Glue": ("Run AWS Glue job", "AWS_Glue"),
    "AWS Glue DataBrew": ("Run AWS Glue DataBrew job", "AWS_Glue_DataBrew"),
    "Azure Data Factory": ("Run Azure Data Factory job", "Azure_Data_Factory"),
    "Microsoft SSIS": ("Run Microsoft SSIS job", "Microsoft_SSIS"),
    "Informatica Cloud Services": ("Run Informatica Cloud Services job", "Informatica_Cloud_Services"),
    "Informatica PowerCenter": ("Run Informatica PowerCenter job", "Informatica_PowerCenter"),
    "SAP Business Warehouse": ("Run SAP Business Warehouse job", "SAP_Business_Warehouse"),
    "Talend Data Management": ("Run Talend Data Management job", "Talend_Data_Management"),
    "Boomi Atmosphere": ("Run Boomi Atmosphere job", "Boomi_Atmosphere"),
    "IBM DataStage": ("Run IBM DataStage job", "IBM_DataStage"),
    "Amazon EMR": ("Run Amazon EMR job", "Amazon_EMR"),
    "Amazon Athena": ("Run Amazon Athena job", "Amazon_Athena"),
    "Azure HDInsight": ("Run Azure HDInsight job", "Azure_HDInsight"),
    "Azure Synapse": ("Run Azure Synapse job", "Azure_Synapse"),
    "Azure Databricks": ("Run Azure Databricks job", "Azure_Databricks"),
    "Google Dataproc": ("Run Google Dataproc job", "Google_Dataproc"),
    "Google Dataflow": ("Run Google Dataflow job", "Google_Dataflow"),
    "Google BigQuery": ("Run Google BigQuery job", "Google_BigQuery"),
    "Snowflake": ("Run Snowflake job", "Snowflake"),
    "Databricks": ("Run Databricks job", "Databricks"),
    "dbt": ("Run dbt job", "dbt"),
    "Apache Hadoop": ("Run Apache Hadoop job", "Apache_Hadoop"),
    "Apache Spark": ("Run Apache Spark job", "Apache_Spark"),
    "Amazon QuickSight": ("Run Amazon QuickSight job", "Amazon_QuickSight"),
    "Microsoft Power BI": ("Run Microsoft Power BI job", "Microsoft_Power_BI"),
    "Qlik Cloud": ("Run Qlik Cloud job", "Qlik_Cloud"),
    "Tableau": ("Run Tableau job", "Tableau"),
    "IBM Cognos": ("Run IBM Cognos job", "IBM_Cognos"),
    "Amazon SageMaker": ("Run Amazon SageMaker job", "Amazon_SageMaker"),
    "Azure Machine Learning": ("Run Azure Machine Learning job", "Azure_Machine_Learning"),
    "Automation Anywhere": ("Run Automation Anywhere job", "Automation_Anywhere"),
    "UiPath": ("Run UiPath job", "UiPath"),
    "AWS Step Functions": ("Run AWS Step Functions job", "AWS_Step_Functions"),
    "Azure LogicApps": ("Run Azure LogicApps job", "Azure_LogicApps"),
    "Apache Airflow": ("Run Apache Airflow job", "Apache_Airflow"),
    "Google Cloud Composer": ("Run Google Cloud Composer job", "Google_Cloud_Composer"),
    "Google Workflows": ("Run Google Workflows job", "Google_Workflows"),
    "AWS Lambda": ("Run AWS Lambda job", "AWS_Lambda"),
    "AWS Batch": ("Run AWS Batch job", "AWS_Batch"),
    "Amazon EC2": ("Run Amazon EC2 job", "Amazon_EC2"),
    "Azure Functions": ("Run Azure Functions job", "Azure_Functions"),
    "Azure Batch": ("Run Azure Batch job", "Azure_Batch"),
    "Google VM": ("Run Google VM job", "Google_VM"),
    "Google Batch": ("Run Google Batch job", "Google_Batch"),
    "Kubernetes": ("Run Kubernetes job", "Kubernetes"),
    "OpenShift": ("Run OpenShift job", "OpenShift"),
    "Azure AKS": ("Run Azure AKS job", "Azure_AKS"),
    "Amazon EKS": ("Run Amazon EKS job", "Amazon_EKS"),
    "AWS CloudFormation": ("Run AWS CloudFormation job", "AWS_CloudFormation"),
    "Azure Resource Manager": ("Run Azure Resource Manager job", "Azure_Resource_Manager"),
    "GCP Deployment Manager": ("Run GCP Deployment Manager job", "GCP_Deployment_Manager"),
    "Communication Suite": ("Run Communication Suite job", "Communication_Suite"),
    "VMware": ("Run VMware job", "VMware"),
    "Web Services SOAP": ("Run Web Services SOAP job", "Web_Services_SOAP"),
    "Web Services REST": ("Run Web Services REST job", "Web_Services_REST"),
    "SAP Data Archiving": ("Run SAP Data Archiving job", "SAP_Data_Archiving"),
}

        # ✅ Remove "Run " prefix from job names
        normalized_workflow = [job.replace("Run ", "").replace(" job", "").strip() for job in workflow]

        # ✅ Check for missing jobs
        missing_jobs = [job for job in normalized_workflow if job not in job_function_mapping]
        
        if missing_jobs:
            app.logger.error(f"❌ Unknown Jobs Found: {missing_jobs}")
            return jsonify({"error": f"Unknown Job Names: {missing_jobs}"}), 400
        

        # Dynamically add jobs to the response data based on the ordered workflow received
        for job_name in normalized_workflow:
          if job_name in job_function_mapping:
            descriptive_key, function_name = job_function_mapping[job_name]
            job_function = getattr(jobs, function_name, None)
            if job_function:
              response_data["WZA_DEMO_GEN"][descriptive_key] = job_function()
            else:
              app.logger.error(f"Function {function_name} not found in jobs.py")
              return jsonify({"error": f"Function {function_name} not found in jobs.py"}), 500


        return jsonify(response_data), 200

    except Exception as e:
        app.logger.error(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/generate-narrative", methods=["POST"])
def generate_narrative():
    """
    Generate a narrative explaining the workflow in detail.
    """
    try: 
        data = request.json
        technologies = data.get("technologies")
        use_case = data.get("use_case")
        ordered_workflow = data.get("optimal_order") or technologies

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400
        
        # Debugging logs
        app.logger.info(f"📝 Generating Narrative with:")
        app.logger.info(f"Technologies: {technologies}")
        app.logger.info(f"Use Case: {use_case}")
        app.logger.info(f"Ordered Workflow: {ordered_workflow}")

        def generate_stream():
            try:

                # Use OpenAI to generate a narrative
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
            "role": "system",
            "content": "You are an AI assistant that generates structured, fluid, and engaging narratives explaining optimized workflows for business use cases. Your response should be professional, insightful, and easy to read, avoiding unnecessary repetition of the provided discovery information."
        },
        {
            "role": "user",
            "content": f"""
            The user has provided the following **discovery information**:

            **Business Challenges:**  
            - Extract the key pain points mentioned in the discovery information.  

            **Positive Business Outcomes:**  
            - Identify the main goals and improvements the business aims to achieve.  

            **Technologies Provided:**  
            {technologies}  

            **Optimized Workflow Order:**  
            {ordered_workflow}  

            **Use Case:**
            {use_case}

            **Generate a structured, fluid narrative following this format:**

            ---
            **Company Type & Industry:**  
            - Extract the relevant details from the **use case** to personalize the response. Clearly state what kind of company it is based on the use case(e.g., financial institution, healthcare provider, e-commerce business, logistics company).  
            
            **Negative Outcomes** 
            (Risks of Not Using Control-M) Describe the potential operational inefficiencies, integration bottlenecks, data inconsistencies, compliance risks, and business disruptions that may arise if the company does not implement Control-M. Emphasize the impact on manual workload, increased errors, missed SLAs, lack of visibility, and higher operational costs. Frame these risks in a way that highlights the urgency of adopting an optimized workflow.

            **Positive Outcomes** 
            (Benefits of Implementing Control-M)Clearly outline the tangible business benefits the company stands to gain by adopting Control-M. Highlight improvements in workflow automation, SLA adherence, error reduction, real-time monitoring, and seamless integration across systems. Explain how this leads to increased efficiency, enhanced customer experience, improved compliance, and reduced operational overhead.

            **Optimized Workflow Recommendation**  
            Transition into explaining the **ideal workflow structure** based on the provided technologies.  

            **Why This Order?**  
            Explain the reasoning behind the sequencing of technologies in a **logical and easy-to-follow manner**. Ensure the explanation aligns with how data flows efficiently, dependencies between systems, and how automation ensures a seamless process.  

            **Technology Contributions and Key Tasks**  
            Break down how **each technology in the workflow contributes**, describing the role it plays and the **key tasks** it handles at that stage. This section should read smoothly and transition logically from one step to the next.  

            **How This Workflow Ensures Efficiency**  
            Conclude by tying everything together—explain how this workflow improves **scalability, reliability, automation, and business efficiency**. Highlight measurable benefits such as **reduced processing time, higher job success rates, improved visibility, and better decision-making**.  

            The response should be **fluid, structured, and easy to read**, avoiding redundancy while ensuring a **clear, insightful explanation** that aligns with business priorities.
            """
        }

                    ], stream = True
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

@app.route("/upload-workflow-json", methods=["POST"])
def upload_workflow_json():
    """
    Extract job names from an uploaded Control-M workflow JSON and return them
    """
    try:
        data = request.get_json()  # Assuming the JSON is sent as raw JSON in the request
        app.logger.info(f"📩 Received JSON: {json.dumps(data, indent=2)}")  # Debug log     

        if not data or "jobs" not in data:
            return jsonify({"error": "Invalid JSON format. Expected a list of jobs."}), 400

         # ✅ Extract only the job name (remove "Run " prefix and " job" suffix)
        extracted_job_names = [
            job.replace("Run ", "").replace(" job", "").strip() for job in data["jobs"]
        ]

        if not extracted_job_names:
            return jsonify({"error": "No valid jobs found in JSON."}), 400

        app.logger.info(f"📋 Extracted Job Names: {extracted_job_names}")  

        return jsonify({"workflow": extracted_job_names}), 200

    except Exception as e:
        app.logger.error(f"Error processing JSON upload: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
