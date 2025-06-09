// This is a simplified version of the job library for frontend display purposes
export const JOB_LIBRARY = {
  job1: { description: "Basic job 1" },
  job2: { description: "Basic job 2" },
  Data_SFDC: { description: "JOB 1: retrieve_sales_data SalesForce CRM" },
  Data_SAP_inventory: { description: "JOB 2: retrieve_inventory_data SAP ERP" },
  Data_Market_API: {
    description:
      "JOB 3: Retrieve market data from external APIs (e.g. Alpha Vantage)",
  },
  Data_Weather_API: {
    description:
      "JOB 4: Retrieve weather data from external APIs (e.g. OpenWeatherMap)",
  },
  JobDatabaseSQLScript: {
    description: "JOB 5: Retrieve data from Oracle database",
  },
  JobFileTransfer: {
    description:
      "Job 5: Collect and aggregate data into a centralized repository using CTM MFT",
  },
  Data_Storage_AWS_S3: {
    description: "Job 5: Store aggregated data in AWS S3 using CTM MFT",
  },
  JobHadoopMapReduce: {
    description: "JOB 8: Aggregate and analyse data using Hadoop",
  },
  JobSLAManagement: {
    description: "JOB 9: Manage SLA for Demand Forecasting Process",
  },
  AWS_AppFlow: { description: "AWS AppFlow integration" },
  AWS_AppRunner: { description: "AWS AppRunner deployment" },
  AWS_Athena: { description: "AWS Athena query execution" },
  AWS_Backup: { description: "AWS Backup operations" },
  AWS_Batch: { description: "AWS Batch job execution" },
  AWS_CloudFormation: { description: "AWS CloudFormation stack management" },
  AWS_DataPipeline: { description: "AWS DataPipeline operations" },
  AWS_DataSync: { description: "AWS DataSync task execution" },
  AWS_DynamoDB: { description: "AWS DynamoDB operations" },
  AWS_EC2: { description: "AWS EC2 instance management" },
  AWS_ECS: { description: "AWS ECS task execution" },
  AWS_EMR: { description: "AWS EMR cluster operations" },
  AWS_Glue: { description: "AWS Glue job execution" },
  AWS_GlueDataBrew: { description: "AWS Glue DataBrew operations" },
  AWS_Lambda: { description: "AWS Lambda function execution" },
  AWS_MainframeModernization: {
    description: "AWS Mainframe Modernization operations",
  },
  AWS_MWAA: { description: "AWS MWAA workflow execution" },
};
