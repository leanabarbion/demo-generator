import os
from openai import OpenAI
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
import json
from flask_cors import CORS
import jobs

# Load environment variables from .env file
load_dotenv()

# Access the OpenAI API key from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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

if __name__ == "__main__":
    app.run(debug=True)
