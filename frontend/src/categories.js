const categories = [
  {
    name: "ERP",
    technologies: [
      { id: 1, name: "SAP R/3" },
      { id: 2, name: "SAP S/4 HANA" },
      { id: 3, name: "Oracle E-Business Suite" },
      { id: 4, name: "Oracle PeopleSoft" },
    ],
  },
  {
    name: "Databases",
    technologies: [
      { id: 5, name: "IBM DB2" },
      { id: 6, name: "Oracle Database" },
      { id: 7, name: "Microsoft SQL Server" },
      { id: 8, name: "PostgreSQL" },
      { id: 9, name: "Sybase / SAP ASE" },
      { id: 10, name: "Java JDBC compliant DB" },
      { id: 11, name: "MySQL" },
      { id: 12, name: "Teradata" },
      { id: 13, name: "SAP HANA" },
      { id: 14, name: "MongoDB" },
    ],
  },
  {
    name: "File Transfer",
    technologies: [
      { id: 15, name: "FTP FTPS" },
      { id: 16, name: "SFTP" },
      { id: 17, name: "AS2" },
      { id: 18, name: "Amazon S3" },
      { id: 19, name: "S3 Comp. Storage" },
      { id: 20, name: "Azure Blob Storage" },
      { id: 21, name: "Azure Data Lake Storage Gen2" },
      { id: 22, name: "Google Cloud Storage" },
      { id: 23, name: "OCI Object Storage" },
    ],
  },
  {
    name: "Data Integration",
    technologies: [
      { id: 24, name: "AWS Data Pipeline" },
      { id: 25, name: "AWS Glue" },
      { id: 26, name: "AWS Glue DataBrew" },
      { id: 27, name: "Azure Data Factory" },
      { id: 28, name: "Microsoft SSIS" },
      { id: 29, name: "Informatica Cloud Services" },
      { id: 30, name: "Informatica PowerCenter" },
      { id: 31, name: "SAP Business Warehouse" },
      { id: 32, name: "Talend Data Management" },
      { id: 33, name: "Boomi Atmosphere" },
      { id: 34, name: "IBM DataStage" },
    ],
  },
  {
    name: "Data Processing & Analytics",
    technologies: [
      { id: 35, name: "Amazon EMR" },
      { id: 36, name: "Amazon Athena" },
      { id: 37, name: "Azure HDInsight" },
      { id: 38, name: "Azure Synapse" },
      { id: 39, name: "Azure Databricks" },
      { id: 40, name: "Google Dataproc" },
      { id: 41, name: "Google Dataflow" },
      { id: 42, name: "Google BigQuery" },
      { id: 43, name: "Snowflake" },
      { id: 44, name: "Databricks" },
      { id: 45, name: "DBT" },
      { id: 46, name: "Apache Hadoop" },
      { id: 47, name: "Apache Spark" },
    ],
  },
  {
    name: "BI & Analytics",
    technologies: [
      { id: 48, name: "Amazon QuickSight" },
      { id: 49, name: "Microsoft Power BI" },
      { id: 50, name: "Qlik Cloud" },
      { id: 51, name: "Tableau" },
      { id: 52, name: "IBM Cognos" },
    ],
  },
  {
    name: "ML",
    technologies: [
      { id: 53, name: "Amazon SageMaker" },
      { id: 54, name: "Azure Machine Learning" },
    ],
  },
  {
    name: "RPA",
    technologies: [
      { id: 55, name: "Automation Anywhere" },
      { id: 56, name: "UiPath" },
    ],
  },
  {
    name: "Application Workflows",
    technologies: [
      { id: 57, name: "AWS Step Functions" },
      { id: 58, name: "Azure LogicApps" },
      { id: 59, name: "Apache Airflow" },
      { id: 60, name: "Google Cloud Composer" },
      { id: 61, name: "Google Workflows" },
    ],
  },
  {
    name: "Cloud Computing",
    technologies: [
      { id: 62, name: "AWS Lambda" },
      { id: 63, name: "AWS Batch" },
      { id: 64, name: "Amazon EC2" },
      { id: 65, name: "Azure Functions" },
      { id: 66, name: "Azure Batch" },
      { id: 67, name: "Google VM" },
      { id: 68, name: "Google Batch" },
    ],
  },
  {
    name: "Container Orchestration",
    technologies: [
      { id: 69, name: "Kubernetes" },
      { id: 70, name: "OpenShift" },
      { id: 71, name: "Azure AKS" },
      { id: 72, name: "Amazon EKS" },
    ],
  },
  {
    name: "Infrastructure as Code",
    technologies: [
      { id: 73, name: "AWS CloudFormation" },
      { id: 74, name: "Azure Resource Manager" },
      { id: 75, name: "GCP Deployment Manager" },
    ],
  },
  {
    name: "Miscellaneous",
    technologies: [
      { id: 76, name: "Communication Suite" },
      { id: 77, name: "VMware" },
      { id: 78, name: "Web Services SOAP" },
      { id: 79, name: "Web Services REST" },
      { id: 80, name: "SAP Data Archiving" },
    ],
  },
];

export default categories;
