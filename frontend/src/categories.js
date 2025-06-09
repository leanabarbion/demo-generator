const categories = [
  {
    name: "Extra",
    technologies: [
      { id: 81, name: "Data_Market_API" },
      { id: 82, name: "Data_SFDC" },
      { id: 83, name: "Data_SAP_inventory" },
      { id: 84, name: "Data_Weather_API" },
      { id: 85, name: "JobDatabaseSQLScript" },
      { id: 86, name: "JobFileTransfer" },
      { id: 87, name: "Data_Oracle_Cloud" },
      { id: 88, name: "Data_Storage_AWS_S3" },
      { id: 89, name: "JobHadoopMapReduce" },
      { id: 90, name: "JobAwsEMR" },
      { id: 91, name: "JobSLAManagement" },
    ],
  },
  {
    name: "App Integration",
    technologies: [
      { id: 1, name: "AWS_AppFlow" },
      { id: 2, name: "AWS_AppRunner" },
      { id: 11, name: "AWS_ECS" },
      { id: 12, name: "AWS_EMR" },
      { id: 16, name: "AWS_MainframeModernization" },
      { id: 17, name: "AWS_MWAA" },
      { id: 100, name: "AZURE_HDInsight" },
      { id: 105, name: "AZURE_LogicApps" },
      { id: 211, name: "GCP_CloudRun" },
      { id: 301, name: "OCI_DataIntegration" },
    ],
  },
  {
    name: "Backup",
    technologies: [
      { id: 4, name: "AWS_Backup" },
      { id: 109, name: "AZURE_Backup" },
    ],
  },
  {
    name: "Compute",
    technologies: [
      { id: 10, name: "AWS_EC2" },
      { id: 106, name: "AZURE_VM" },
      { id: 203, name: "GCP_VM" },
      { id: 300, name: "OCI_VM" },
    ],
  },
  {
    name: "Data Processing",
    technologies: [
      { id: 13, name: "AWS_Glue" },
      { id: 14, name: "AWS_GlueDataBrew" },
      { id: 20, name: "AWS_SageMaker" },
      { id: 102, name: "AZURE_Databricks" },
      { id: 108, name: "AZURE_Machine_Learning" },
      { id: 200, name: "GCP_Dataflow" },
      { id: 201, name: "GCP_Dataproc" },
      { id: 205, name: "GCP_Dataprep" },
      { id: 210, name: "GCP_Data_Fusion" },
      { id: 302, name: "OCI_DataFlow" },
      { id: 303, name: "OCI_DataScience" },
      { id: 402, name: "DBT" },
      { id: 403, name: "MS_PowerBI" },
      { id: 406, name: "Tableau" },
    ],
  },
  {
    name: "Database",
    technologies: [
      { id: 3, name: "AWS_Athena" },
      { id: 9, name: "AWS_DynamoDB" },
      { id: 18, name: "AWS_QuickSight" },
      { id: 19, name: "AWS_Redshift" },
      { id: 107, name: "AZURE_Synapse" },
      { id: 204, name: "GCP_BigQuery" },
    ],
  },
  {
    name: "DevOps",
    technologies: [{ id: 111, name: "AZURE_DevOps" }],
  },
  {
    name: "File Transfer",
    technologies: [
      { id: 7, name: "AWS_DataPipeline" },
      { id: 8, name: "AWS_DataSync" },
      { id: 103, name: "AZURE_DataFactory" },
    ],
  },
  {
    name: "Messaging",
    technologies: [
      { id: 21, name: "AWS_SNS" },
      { id: 22, name: "AWS_SQS" },
      { id: 112, name: "AZURE_Service_Bus" },
    ],
  },
  {
    name: "Orchestration",
    technologies: [
      { id: 23, name: "AWS_StepFunctions" },
      { id: 209, name: "GCP_Workflows" },
      { id: 212, name: "GCP_Composer" },
      { id: 400, name: "Ansible_AWS" },
      { id: 401, name: "Automation_Anywhere" },
      { id: 404, name: "Terraform" },
      { id: 405, name: "UI_Path" },
      { id: 407, name: "Jenkins" },
      { id: 408, name: "Apache_NiFi" },
      { id: 409, name: "Apache_Airflow" },
    ],
  },
  {
    name: "Provisioning",
    technologies: [
      { id: 6, name: "AWS_CloudFormation" },
      { id: 110, name: "AZURE_Resource_Manager" },
      { id: 207, name: "GCP_DeploymentManager" },
    ],
  },
  {
    name: "Serverless",
    technologies: [
      { id: 15, name: "AWS_Lambda" },
      { id: 104, name: "AZURE_Functions" },
      { id: 202, name: "GCP_Functions" },
    ],
  },
  {
    name: "Other",
    technologies: [
      { id: 5, name: "AWS_Batch" },
      { id: 101, name: "AZURE_Batch" },
      { id: 206, name: "GCP_Dataplex" },
      { id: 208, name: "GCP_Batch" },
    ],
  },
];

export default categories;
