import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
import json
from flask_cors import CORS
import jobs
import base64
import requests
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Access the OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# GitHub Config (store token securely in .env)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "leanabarbion"
REPO_NAME = "workflow-repo"  # Replace with your repo name
BRANCH = "main"
BASE_FOLDER_PATH = "jobs"# Folder where files will be uploaded

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

        if not workflow_json or not narrative_text:
            return jsonify({"error": "Missing workflow or narrative"}), 400

        # Generate a unique folder name (Timestamp format: YYYY-MM-DD_HH-MM-SS)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{BASE_FOLDER_PATH}/workflow_{timestamp}"  # e.g., jobs/workflow_2025-02-11_13-45-30

        # Define file paths inside this unique folder
        workflow_file = f"{folder_name}/workflow.json"
        narrative_file = f"{folder_name}/narrative.txt"
        metadata_file = f"{folder_name}/metadata.txt"  # Optional metadata file

        # Upload both files
        upload_workflow = upload_to_github(workflow_file, workflow_json, "Added workflow JSON")
        upload_narrative = upload_to_github(narrative_file, narrative_text, "Added workflow narrative")

        # Optional: Upload metadata (user info, timestamp, etc.)
        metadata_content = f"Upload Time: {timestamp}\nUser Info: {data.get('user_info', 'N/A')}"
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
        ordered_workflow = extract_json_from_response(response_content)

        if ordered_workflow:
          response = {"optimal_order": ordered_workflow.get("workflow_order") or ordered_workflow.get("workflow")}
          app.logger.info(f"Optimal Workflow Order: {json.dumps(response, indent=2)}")
          return jsonify(response), 200

        else:
            return jsonify({"error": "Failed to extract ordered workflow", "raw_response": response_content}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-workflow', methods=['POST'])
def save_workflow():
    """
    Save a workflow based on selected technologies.
    """
    try: 
        data = request.get_json()
        app.logger.info(f"Received Data: {data}")  # Log the received data

        if not data or 'workflow' not in data:
            return jsonify({"error": "Invalid data"}), 400

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

        # Dynamically add jobs to the response data based on the ordered workflow received
        for job_name in data['workflow']:
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
        ordered_workflow = data.get("optimal_order")

        if not technologies or not use_case or not ordered_workflow:
            return jsonify({"error": "Technologies, use case, and workflow order are required."}), 400

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

            ]
        )

        narrative_response = completion.choices[0].message.content.strip()

        return jsonify({"narrative": narrative_response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
