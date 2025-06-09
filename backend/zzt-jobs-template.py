# Demo Generator/Loyalty Program Python Script
#
# Project: Demo Generator / Vertical Workflows
# Module: Loyalty Program
# Version: 1.0.0
#
# Author: Wojciech Zaremba <wojciech_zaremba@bmc.com>
# Organization: BMC Control-M VSE
# Created: 2025-05-23
# Last Modified: 2025-05-23 by Wojciech Zaremba
#
# Description:
# This script generates Layalty Program Control-M Workflow.
#
# Features:
# - Feature A: [brief description]
# - Feature B: [brief description]
#
# Known Issues:
# - Issue #1: no issues 
#
# Changelog:
# 1.0.0 (2025-05-23): Initial release.

# Usage:
# Example usage: python script_name.py
#
# Notes:
# Here will be specific notes or warnings for users or developers.
# Banners genereated here https://patorjk.com/software/taag/#p=display&f=ANSI%20Regular&t=GCP


from ctm_python_client.core.workflow import *
from ctm_python_client.core.comm import *
from ctm_python_client.core.credential import *
from aapi import *
from my_secrets import my_secrets

#PROGRAMM DEFAULTS
prefix = "zzt"

#ENV
my_env = Environment.create_saas(endpoint=my_secrets['helix_sandbox_endpoint'],api_key=my_secrets['helix_sandbox_api_key'])
 
#defaults
defaults = WorkflowDefaults(run_as="ctmagent", host="zzz-linux-agents",application="ZZT-Version1-DG", sub_application="ZZT-Version1-DG")
 
#Workflow
workflow = Workflow(my_env, defaults=defaults)
 
#FOLDER
folder1 = Folder("zzt-jobs-template", site_standard="Empty", controlm_server="IN01", description="Folder created by Wojciech Zaremba to test all job types in Python. If you are interested in source code, please contact wzaremba@bmc.com", order_method="Manual")

#  █████  ██     ██ ███████ 
# ██   ██ ██     ██ ██      
# ███████ ██  █  ██ ███████ 
# ██   ██ ██ ███ ██      ██ 
# ██   ██  ███ ███  ███████ 

# AWS AppFlow
AWS_AppFlow = JobAwsAppFlow(f"{prefix}-aws-app-flow",
                            description="AWS AppFlow",
                            connection_profile="ZZZ_AWS_APPFLOW",
                            action="Trigger Flow - Key & Secret Auth",
                            flow_name="testflow1",
                            trigger_flow_with_idempotency_token="checked",
                            client_token="Token_Control-1_for_AppFlow%%ORDERID",
                            )
folder1.job_list.append(AWS_AppFlow)

# AWS App Runner
AWS_AppRunner = JobAwsAppRunner(f"{prefix}-aws-app-runner",
                                connection_profile="ZZZ_AWS_APP_RUNNER",
                                action="Deploy",
                                service_arn="arn:aws:apprunner:us-east-1:xxxxxxxxxx:service/Hello_World/xxxxxxx",
                                output_job_logs="unchecked"
                                )
folder1.job_list.append(AWS_AppRunner)

# AWS Athena
AWS_Athena = JobAwsAthena(f"{prefix}-aws-athena",
                          description="AWS Athena", 
                          connection_profile="ZZZ_AWS_ATHENA",
                          output_location="s3://s3bucket}",
                          db_catalog_name="DB_Catalog_Athena",
                          database_name="DB_Athena",
                          query="Select * from Athena_Table",
                          workgroup="Primary"
                          )
folder1.job_list.append(AWS_Athena)

# AWS Backup
AWS_Backup = JobAwsBackup(f"{prefix}-aws-backup",
                          connection_profile="ZZZ_AWS_BACKUP",
                          action="Backup",
                          windows_vss="Disabled",
                          backup_vault_name="Test1",
                          role_arn="arn:aws:iam::12234888888:role/service-role/AWSBackupDefaultServiceRole1",
                          idempotency_token="token12345",
                          )
folder1.job_list.append(AWS_Backup)

# AWS Batch
AWS_Batch = JobAwsBatch(f"{prefix}-aws-batch",
                        connection_profile="ZZZ_AWS_BATCH",
                        job_name="job_name",
                        job_definition_and_revision="zzz-batch-job-definition:1",
                        job_queue="zzz-batch-job-queue",
                        job_attempts="2",
                        use_advanced_json_format="unchecked",
                        container_overrides_command="[\"echo\", \"hello from control-m\"]",
                        )
folder1.job_list.append(AWS_Batch)

# AWS CloudFormation
AWS_CloudFormation = JobAwsCloudFormation(f"{prefix}-aws-cloudformation",
                                          connection_profile="ZZZ_AWS_CLOUDFORMATION",
                                          action="Update Stack",
                                          stack_name="Demo",
                                          stack_parameters="Template URL",
                                          template_url="https://ayatest.s3.amazonaws.com/dynamodbDemo.yml",
                                          template_body="",
                                          role_arn="arn:aws:iam::122343283363:role/AWS-QuickSetup-StackSet-Local-AdministrationRole",
                                          capabilities_type="CAPABILITY_NAMED_IAM",
                                          enable_termination_protection="unchecked",
                                          on_failure="DELETE",
                                          failure_tolerance="2"
                                          )
folder1.job_list.append(AWS_CloudFormation)

# AWS Data Pipeline
AWS_DataPipeline = JobAwsDataPipeline(f"{prefix}-aws-datapipeline",
                                      connection_profile="ZZZ_AWS_DATAPIPELINE",
                                      trigger_created_pipeline="Trigger Pipeline",
                                      pipeline_id="df-020488024DNBVFN1S2U",
                                      pipeline_name="demo-pipeline",
                                      pipeline_unique_id="235136145",
                                      )
folder1.job_list.append(AWS_DataPipeline)

# AWS Datasync
AWS_DataSync = JobAwsDataSync(f"{prefix}-aws-datasync",
                              connection_profile="ZZZ_AWS_DATASYNC",
                              action="Execute Task",
                              variables=[{"UCM-TASKARNSECRET": "arn:aws:datasync:us-east-1:122343283363:task/task-0752fa45494724f46"}],
                              output_logs="checked"
                              )
folder1.job_list.append(AWS_DataSync)

# AWS DynamoDB
AWS_DynamoDB = JobAwsDynamoDB(f"{prefix}-aws-dynamodb",
                              connection_profile="ZZZ_AWS_DYNAMODB",
                              action="Execute Statement",
                              run_statement_with_parameter="checked",
                              statement="Select * From IFteam  where Id=? OR Name=?",
                              statement_parameters="\[\{\"N\": \"20\"\},\{\"S\":\"Stas30\"\}\]",
                              )
folder1.job_list.append(AWS_DynamoDB)

# AWS EC2
AWS_EC2 = JobAwsEC2(f"{prefix}-aws-ec2",
                    description="AWS EC2", 
                    connection_profile="ZZZ_AWS_EC2",
                    operations="Create",
                    placement_availability_zone="us-west-2c",
                    instance_type="m1.small",
                    subnet_id="subnet-00aa899a7db25494d",
                    key_name="ksu-aws-ec2-key-pair",
                    get_instances_logs="unchecked",
                    )

folder1.job_list.append(AWS_EC2)

# AWS ECS
AWS_ECS = JobAwsECS(f"{prefix}-aws-ecs",
                    connection_profile="ZZZ_AWS_ECS",
                    action="Preset Json",
                    ecs_cluster_name="ECSIntegrationCluster",
                    ecs_task_definition="ECSIntegrationTask",
                    assign_public_ip="True",
                    network_security_groups="\"sg-01e4a5bfac4189d10\"",
                    network_subnets="\"subnet-045ddaf41d4852fd7\", \"subnet-0b574cca721d462dc\", \"subnet-0e108b6ba4fc0c4d7\"",
                    override_container="IntegrationURI",
                    override_command="\"/bin/sh -c 'whoami'\"",
                    environment_variables="\{\"name\": \"var1\", \"value\": \"1\"\}",
                    get_logs="Get Logs"

                    )
folder1.job_list.append(AWS_ECS)

# AWS EMR
AWS_EMR = JobAwsEMR(f"{prefix}-aws-emr",
                    connection_profile="ZZZ_AWS_EMR",
                    cluster_id="j-21PO60WBW77GX",
                    notebook_id="e-DJJ0HFJKU71I9DWX8GJAOH734",
                    relative_path="ShowWaitingAndRunningClusters.ipynb",
                    notebook_execution_name="TestExec",
                    service_role="EMR_Notebooks_DefaultRole",
                    use_advanced_json_format="unchecked"
                    )
folder1.job_list.append(AWS_EMR)

# AWS Glue
AWS_Glue = JobAwsGlue(f"{prefix}-aws-glue",
                      connection_profile="ZZZ_AWS_GLUE",
                      glue_job_name="ZZZ_GLUE_JOB",
                      glue_job_arguments="checked",
                      arguments="{\"--source\": \"https://jsonplaceholder.typicode.com/todos/1\", \"--destination\": \"ncu-datapipe\"}",
                      )
folder1.job_list.append(AWS_Glue)

# AWS Glue DataBrew
AWS_GlueDataBrew = JobAwsGlueDataBrew(f"{prefix}-aws-glue-databrew",
                                      description="AWS Glue Databrew",
                                      connection_profile="ZZZ_AWS_GLUE_DATABREW",
                                      job_name="databrew-job",
                                      )
folder1.job_list.append(AWS_GlueDataBrew)

# AWS Lambda
AWS_Lambda = JobAwsLambda(f"{prefix}-aws-lambda",
                          connection_profile="ZZZ_AWS_LAMBDA",
                          function_name="MyTestFunction",
                          parameters="{%4E   \"param1\": 60,%4E   \"param2\": 60%4E}",
                          append_log_to_output="checked"
                          )
folder1.job_list.append(AWS_Lambda)

# AWS Mainframe modernization
AWS_MainframeModernization = JobAwsMainframeModernization("{prefix}-aws-mainframe-modernization",
                                                          connection_profile="ZZZ_AWS_MAINFRAME",
                                                          application_name="Demo",
                                                          action="Start Batch Job",
                                                          jcl_name="DEMO.JCL",
                                                          retrieve_cloud_watch_logs="checked",
                                                          application_action="Start Application"
                                                        )
folder1.job_list.append(AWS_MainframeModernization)

# AWS MWAA
AWS_MWAA = JobAwsMWAA(f"{prefix}-aws-mwaa",
                      connection_profile="ZZZ_AWS_MWAA",
                      action="Run DAG",
                      m_w_a_a_environment_name="MyAirflowEnvironment",
                      d_a_g_name="example_dag_basic",
                      parameters="{}"
                      )
folder1.job_list.append(AWS_MWAA)

# AWS QuickSight
AWS_QuickSight = JobAwsQuickSight(f"{prefix}-aws-quicksight",
                                  description="AWS QuickSight",
                                  connection_profile="ZZZ_AWS_QUICKSIGHT",
                                  aws_dataset_id="d351ce9e-1500-4494-b0e1-43b2d6f48861",
                                  refresh_type="Full Refresh",
                                  )
folder1.job_list.append(AWS_QuickSight)

# AWS Redshift
AWS_Redshift = JobAwsRedshift(f"{prefix}-aws-redshift",
                              connection_profile="ZZZ_AWS_REDSHIFT",
                              load_redshift_sql_statement="select * from Redshift_table",
                              actions="Redshift SQL Statement",
                              workgroup_name="Workgroup_Name",
                              secret_manager_arn="Secret_Manager_ARN",
                              database="Database_Redshift"
                              )
folder1.job_list.append(AWS_Redshift)

# AWS SageMaker
AWS_SageMaker = JobAwsSageMaker(f"{prefix}-aws-sagemaker",
                                description="AWS SageMaker",
                                connection_profile="ZZZ_AWS_SAGEMAKER",
                                pipeline_name="SageMaker_Pipeline",
                                add_parameters="unchecked",
                                retry_pipeline_execution="unchecked",
                                )
folder1.job_list.append(AWS_SageMaker)

# AWS SNS
AWS_SNS = JobAwsSNS(f"{prefix}-aws-sns",
                    connection_profile="ZZZ_AWS_SNS",
                    message_type="Message To A Topic",
                    topic_type="Standard",
                    target_arn="Target ARN",
                    json_message_structure="unchecked",
                    subject="Subject",
                    message="Message",
                    attributes="checked",
                    attribute1_name="Attribute1",
                    attribute1_value="Value1",
                    sms_attributes="checked",
                    sender_identifier="Sender ID",
                    sender_id="BMC",
                    max_price="1.0",
                    sms_type="Transactional",
                    )
folder1.job_list.append(AWS_SNS)

# AWS SQS
AWS_SQS = JobAwsSQS(f"{prefix}-aws-sqs",
                    connection_profile="ZZZ_AWS_SQS",
                    queue_type="Standard Queue",
                    queue_url="https://sqs.eu-west-2.amazonaws.com/122343283363/TestingQueue",
                    message_body="Test Message Body",
                    delay_seconds="0",
                    message_attributes="checked",
                    attribute1_name="Attribute.1",
                    attribute1_data_type="String",
                    attribute1_value="CustomValue1",
                    )
folder1.job_list.append(AWS_SQS)

# AWS Step Functions
AWS_StepFunctions = JobAwsStepFunctions(f"{prefix}-aws-stepfunctions",
                                        connection_profile="ZZZ_AWS_STEP_FUNCTIONS",
                                        execution_name="Step Functions Exec",
                                        state_machine_arn="arn:aws:states:us-east-1:155535555553:stateMachine:MyStateMachine",
                                        parameters="{\"parameter1\":\"value1\"\}",
                                        show_execution_logs="checked"
                                        )

folder1.job_list.append(AWS_StepFunctions)



#  █████  ███████ ██    ██ ██████  ███████ 
# ██   ██    ███  ██    ██ ██   ██ ██      
# ███████   ███   ██    ██ ██████  █████   
# ██   ██  ███    ██    ██ ██   ██ ██      
# ██   ██ ███████  ██████  ██   ██ ███████ 


# Azure HDInsight
AZURE_HDInsight = JobAzureHDInsight(f"{prefix}-azure-hd-insight",
                                    connection_profile="ZZZ_AZURE_HD_INSIGHT",
                                    parameters= "\{%4E\"file\" : \"wasb://asafcluster2-2022-06-06t07-39-08-081z@asafcluster2hdistorage.blob.core.windows.net/example/jars/hadoop-mapreduce-examples.jar\", %4E\"jars\" : \[\"wasb://asafcluster2-2022-06-06t07-39-08-081z@asafcluster2hdistorage.blob.core.windows.net/example/jars/hadoop-mapreduce-examples.jar\"\],%4E\"driverMemory\" : \"5G\",  %4E\"driverCores\" : 3,  %4E\"executorMemory\" : \"5G\",  %4E\"executorCores\" : 3,  %4E\"numExecutors\" : 1  %4E\}",
                                    bring_job_logs_to_output="checked",
                                    )
folder1.job_list.append(AZURE_HDInsight)

# Azure Batch
AZURE_Batch = JobAzureBatchAccounts(f"{prefix}-azure-batch-accounts",
                                    connection_profile="ZZZ_AZURE_BATCH_ACCOUNTS",
                                    batch_job_id="zzz-jobid",
                                    task_command_line="cmd /c echo hello from Control-M",
                                    max_wall_clock_time="Unlimited",
                                    max_wall_time_unit="Minutes",
                                    max_task_retry_count="None",
                                    retention_time="Custom",
                                    retention_time_digits="4",
                                    retention_time_unit="Days",
                                    append_log_to_output="checked",
                                    )
folder1.job_list.append(AZURE_Batch)

# Azure Databricks
AZURE_Databricks = JobAzureDatabricks(f"{prefix}-azure-databricks",
                                      connection_profile="ZZZ_AZURE_DATABRICKS",
                                      databricks_job_id="168477649492161",
                                      parameters="\"notebook_params\":\{\"param1\":\"val1\", \"param2\":\"val2\"\}",
                                      )
folder1.job_list.append(AZURE_Databricks)

# Azure Data Factory
AZURE_DataFactory = JobAzureDataFactory(f"{prefix}-azure-datafactory",
                                        connection_profile="ZZZ_AZURE_DATAFACTORY",
                                        resource_group_name="ZZZ_Group",
                                        data_factory_name="zzz-test",
                                        pipeline_name="test123",
                                        parameters="{}",
                                        )
folder1.job_list.append(AZURE_DataFactory) 

# Azure Functions
AZURE_Functions = JobAzureFunctions(f"{prefix}-azure-function",
                                   connection_profile="ZZZ_AZURE_FUNCTIONS",
                                   function_app="new-function",
                                   function_name="Hello",
                                   optional_input_parameters="{\"param1\":\"val1\", \"param2\":\"val2\"}\"",
                                   function_type="activity"
                                   )
folder1.job_list.append(AZURE_Functions)                         

# Azure LogicApps
AZURE_LogicApps = JobAzureLogicApps(f"{prefix}-azure-logicapps",
                                    connection_profile="ZZZ_AZURE_LOGICAPPS",
                                    workflow="zzz-logic",
                                    parameters="{\"bodyinfo\":\"hello from CM\"}",
                                    get_logs="unchecked",
                                    )
folder1.job_list.append(AZURE_LogicApps)

# Azure VM
AZURE_VM = JobAzureVM(f"{prefix}-azure-vm",
                      connection_profile="ZZZ_AZURE_VM",
                      operation="Create\\Update",
                      verification_poll_interval="10",
                      vm_name="zzz-vm1",
                      input_parameters="{\"key\": \"val\"}",
                      delete_vm_os_disk="unchecked",
                      )
folder1.job_list.append(AZURE_VM)

# Azure Synapse
AZURE_Synapse = JobAzureSynapse(f"{prefix}-azure-synapse",
                                connection_profile="ZZZ_AZURE_SYNAPSE",
                                pipeline_name="zzz_synapse_pipeline",
                                parameters="{\"periodinseconds\":\"40\"}",
                                )
folder1.job_list.append(AZURE_Synapse)

# Azure Machine Learning
AZURE_Machine_Learning = JobAzureMachineLearning(f"{prefix}-azure-machine-learning",
                                                 connection_profile="ZZZ_AZURE_MACHINELEARNING",
                                                 resource_group_name="ZZZ_Resource_Group",
                                                 workspace_name="ZZZ_ML",
                                                 action="Trigger Endpoint Pipeline",
                                                 pipeline_endpoint_id="353c4707-fd23-40f6-91e2-83bf7cba764c",
                                                 parameters="{\"ExperimentName\": \"test\",\"DisplayName\":\"test1123\"}",
                                                 )
folder1.job_list.append(AZURE_Machine_Learning)

# Azure Backup
AZURE_Backup = JobAzureBackup(f"{prefix}-azure-backup",
                              connection_profile="ZZZ_AZURE_BACKUP",
                              action="Backup",
                              vault_resource_group="zzz-if",
                              vault_name="Test",
                              vm_resource_group="zzz-if",
                              vm_name="zzz-if-squid-proxy",
                              include_or_exclude_disks="Include",
                              restore_to_latest_recovery_point="checked",
                              recovery_point_name="142062693017419",
                              storage_account_name="stasaccount",
                              restore_region="UK South",
                              )
folder1.job_list.append(AZURE_Backup)

# Azure Resource Manager
AZURE_Resource_Manager = JobAzureResourceManager(f"{prefix}-azure-resource-manager",
                                                 connection_profile="ZZZ_AZURE_RESOURCE_MANAGER",
                                                 action="Create Deployment",
                                                 resource_group_name="ZZZ_Resource_Group",
                                                 deployment_name="demo",
                                                 deployment_properties="{\"properties\": {\"templateLink\": {\"uri\": \"https://123.blob.core.windows.net/test123/123.json?sp=r&st=2023-05-23T08:39:09Z&se=2023-06-10T16:39:09Z&sv=2022-11-02&sr=b&sig=RqrATxi4Sic2UwQKFu%2FlwaQS7fg5uPZyJCQiWX2D%2FCc%3D\",\"queryString\": \"sp=r&st=2023-05-23T08:39:09Z&se=2023-06-10T16:39:09Z&sv=2022-11-02&sr=b&sig=RqrATxi4Sic2UwQKFu%2FlwaQS7fg5uPZyJCQiWX2D%1234\"}",
                                                )                                                                                                 

folder1.job_list.append(AZURE_Resource_Manager)

# Azure DevOps
AZURE_DevOps = JobAzureDevOps(f"{prefix}-azure-devops",
                              connection_profile="ZZZ_AZURE_DEVOPS",
                              project_name="TestProject",
                              actions="Run Pipeline with More Options",
                              pipeline_id="1",
                              show_build_logs="checked",
                              stages_to_skip="\"Test\",\"Deploy\"",
                              )
folder1.job_list.append(AZURE_DevOps)

# Azure Service Bus
AZURE_Service_Bus = JobAzureServiceBus(f"{prefix}-azure-service-bus",
                                       connection_profile="ZZZ_AZURE_SERVICEBUS",
                                       message_body="\{\"key1\":\"value1\"\}",
                                       service_bus_namespace="test",
                                       queue_topic_name="testname",
                                       message_format="application/json"
                                       )
folder1.job_list.append(AZURE_Service_Bus)

###########################################################################################################################################################

#  ██████   ██████ ██████  
# ██       ██      ██   ██ 
# ██   ███ ██      ██████  
# ██    ██ ██      ██      
#  ██████   ██████ ██     

###########################################################################################################################################################

# GCP Dataflow
GCP_Dataflow = JobGCPDataflow(f"{prefix}-gcp-dataflow",
                              connection_profile="ZZZ_GCP_DATAFLOW",
                              project_id="applied-lattice-11111",
                              region="us-central1",
                              template_type="Classic Template",
                              template_location_gs_="gs://dataflow-templates-us-central1/latest/Word_Count",
                              parameters__json_format="{\"jobName\": \"wordcount11\"}",
                              log_level="INFO",
                              )
folder1.job_list.append(GCP_Dataflow)

# GCP DataProc
GCP_Dataproc = JobGCPDataproc(f"{prefix}-gcp-dataproc",
                              connection_profile="ZZZ_GCP_DATAPROC",
                              project_id="applied-lattice-333108",
                              account_region="us-central1",
                              dataproc_task_type="Workflow Template",
                              workflow_template="<TemplateID>",
                              )
folder1.job_list.append(GCP_Dataproc)

# GCP Functions
GCP_Functions = JobGCPFunctions(f"{prefix}-gcp-functions",
                                connection_profile="ZZZ_GCP_FUNCTIONS",
                                function_parameters="Body",
                                body="{\\\"message\\\":\\\"controlm-body-%%ORDERID\\\"}",
                                failure_tolerance="2",
                                get_logs="unchecked",
                                location="us-central1",
                                function_name="ZZZ_function",
                                project_id="<Project ID>",
                                )
folder1.job_list.append(GCP_Functions)

# GCP VM
GCP_VM = JobGCPVM(f"{prefix}-gcp-vm",
                  connection_profile="ZZZ_GCP_VM",
                  project_id="applied-lattice",
                  zone="us-central1-f",
                  operation="Stop",
                  instance_name="cluster-us-cen1-f-m",
                  )
folder1.job_list.append(GCP_VM)

# GCP BigQuery
GCP_BigQuery = JobGCPBigQuery(f"{prefix}-gcp-bigquery",
                              connection_profile="ZZZ_GCP_BIGQUERY",
                              action="Query",
                              run_select_query_and_copy_to_table="checked",
                              project_name="applied-lattice-333108",
                              dataset_name="Test",
                              sql_statement="select * from IFteam",
                              )
folder1.job_list.append(GCP_BigQuery)

# GCP Dataprep
GCP_Dataprep = JobGCPDataprep(f"{prefix}-gcp-dataprep",
                              connection_profile="ZZZ_GCP_DATAPREP",
                              flow_name="data_manipulation",
                              parameters="{\"schemaDriftOptions\":{\"schemaValidation\": \"true\",\"stopJobOnErrorsFound\": \"true\"                             }}",
                              execute_job_with_idempotency_token="checked",
                              idempotency_token="Control-M-Token-%%ORDERID",
                              )
folder1.job_list.append(GCP_Dataprep)

# GCP Dataplex
GCP_Dataplex = JobGCPDataplex(f"{prefix}-gcp-dataplex",
                              connection_profile="ZZZ_GCP_DATAPLEX",
                              project_id="applied-lattice-333108",
                              location="europe-west2",
                              action="Data Profiling Scan",
                              lake_name="Demo_Lake",
                              task_name="Demo_Task",
                              scan_name="Demo",
                              )
folder1.job_list.append(GCP_Dataplex)

# GCP Deployment Manager
GCP_DeploymentManager = JobGCPDeploymentManager(f"{prefix}-gcp-deployment-manager",
                                                connection_profile="ZZZ_GCP_DEPLOYMENT_MANAGER",
                                                project_id="applied-lattice-333111",
                                                action="Create Deployment",
                                                deployment_name="demo_deployment",
                                                yaml_config_content="\{resources: \[\{type: compute.v1.instance, name: quickstart-deployment-vm, properties: \{zone: us-central1-f, machineType: 'https://www.googleapis.com/compute/v1/projects/applied-lattice-333108/zones/us-central1-f/machineTypes/e2-micro', disks: \[\{deviceName: boot, type: PERSISTENT, boot: true, autoDelete: true, initializeParams: \{sourceImage: 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-11'\}\}\], networkInterfaces: \[\{network: 'https://www.googleapis.com/compute/v1/projects/applied-lattice-333108/global/networks/default', accessConfigs: \[\{name: External NAT, type: ONE_TO_ONE_NAT\}\]\}\]\}\}\]\}",
                                                )
folder1.job_list.append(GCP_DeploymentManager)

# GCP Batch
GCP_Batch = JobGCPBatch(f"{prefix}-gcp-batch",
                        connection_profile="ZZZ_GCP_BATCH",
                        project_id="applied-lattice-333111",
                        override_region="Yes",
                        job_name="test",
                        runnable_type="Script",
                        task_script_text="echo hello",
                        override_commands="No",
                        instance_policy="Machine Type",
                        provisioning_model="Standard",
                        log_policy="Cloud Logging",
                        use_advanced_json_format="unchecked",
                        allowed_locations="[\"regions us-east1\",\"zones us-east1-b\"]",
                        service_account__email_format="example@example.com",
                        )
folder1.job_list.append(GCP_Batch)

# GCP Eventarc
# NOT EXISTING IN PYTHON?

# GCP Workflows
GCP_Workflows = JobGCPWorkflows(f"{prefix}-gcp-workflows",
                                connection_profile="ZZZ_GCP_WORKFLOWS",
                                show_workflow_results="checked",
                                project_id="12345id",
                                location="us-central1",
                                workflow_name="workflow-1",
                                parameters_json_input="\{%4E    \"argument\": \"\{\}\"%4E\}",
                                )
folder1.job_list.append(GCP_Workflows)

# GCP Data Fusion
GCP_Data_Fusion = JobGCPDataFusion(f"{prefix}-gcp-datafusion",
                                   connection_profile="ZZZ_GCP_DATAFUSION",
                                   region="us-west1",
                                   project_name=" Project-Name ",
                                   instance_name=" Instance-Name ",
                                   pipeline_name="TestBatchPipeLine",
                                   runtime_parameters="{ \"Parameter1\":\"Value1}",
                                   get_logs="checked",
                                   )
folder1.job_list.append(GCP_Data_Fusion)

# GCP Cloud Run
GCP_CloudRun = JobGCPCloudRun(f"{prefix}-gcp-cloudrun",
                              connection_profile="ZZZ_GCP_CLOUDRUN",
                              project_id="applied-lattice-333108",
                              location="us-central1",
                              job_name="testjob",
                              overrides_specification="\{\}",
                              )
folder1.job_list.append(GCP_CloudRun)

# GCP Composer
GCP_Composer = JobGCPComposer(f"{prefix}-gcp-composer",
                              connection_profile="ZZZ_GCP_COMPOSER",
                              action="Run DAG",
                              d_a_g_name="example_dag_basic",
                              parameters="{}",
                              )
folder1.job_list.append(GCP_Composer)


#  ██████  ██████   █████   ██████ ██      ███████ 
# ██    ██ ██   ██ ██   ██ ██      ██      ██      
# ██    ██ ██████  ███████ ██      ██      █████   
# ██    ██ ██   ██ ██   ██ ██      ██      ██      
#  ██████  ██   ██ ██   ██  ██████ ███████ ███████ 
                                                 
# OCI_VM
OCI_VM = JobOCIVM(f"{prefix}-oci-vm",
                  connection_profile="ZZZ_OCI_VM",
                  action= "Start",
                  parameters="\{\"compartmentId\": \"ocid1.tenancy.oc1..\",     \"displayName\": \"Team_Demo\",    \"shape\": \"VM.Standard.E2.1.Micro\",                                \"subnetId\": \"ocid1.subnet.oc1.il-jerusalem-1.*\",     \"imageId\": \"ocid1.image.oc1.il-jerusalem-1.*\",     \"availabilityDomain\": \"TVqI:IL-JERUSALEM-1-AD-1\",\"metadata\": \{                                \"ssh_authorized_keys\": \"ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDGOXTtnyZ03mOfKq9zX4GzaC00k0VJOU1Oh68IqyB6onkNoTg+q5tHGuNCBkFPP6J6yYDB8Km8PVV7ajGqkX8wQbUghrxdn2IeFYsCaNEz1JBvhONsFl0k6hbm1aipL/tyhkHBkaHQoUaN+cy0Lg5WoMVrZvuI/1fatCbl3bdrPqfe11lJ3sX7IW0JJz5W+d/26JEzcW3+vSwBGNgGwXB19LcR*\"                                \},\"extendedMetadata\": \{                                \"freeformTags\": \{           \"my_tag_key\": \"my_tag_value\"                                \},\"definedTags\": \{                                \"my_defined_tag_namespace\": \{                                \"my_defined_tag_key\": \"my_defined_tag_value\"                                \}                                \}                                \},                                \"freeformOptions\": \{                                \"isAlwaysFree\": true                                \}                                \}",
                  )
folder1.job_list.append(OCI_VM)

# OCI DATA INTGEGRATION
OCI_DataIntegration = JobOCIDataIntegration(f"{prefix}-oci-data-integrations",
                                             connection_profile="ZZZ_OCI_DATAINTEGRATIONS",
                                             actions="Run Task",
                                             application_key="0dab7145-1e2b-4d2b-844e-d784cadc28be",
                                             task_key="b5636bc5-d672-9ca0-84a0-9b20c17d0bda",
                                             workspace_ocid="ocid1.disworkspace.oc1.phx.anyhqljr2ow634yaho5mitq5jxqcreq4kt3ycpoltpakb57flphqowx3eeia",
                                             task_run_name="Task1",
                                             task_run_input_parameters="\"PARAMETER\": \{%4E        \"simpleValue\": \"Hello\"%4E      \},%4E      \"PARAMETER2\": \{%4E        \"simpleValue\": \"Hello222\"%4E      \}",
                                             )
folder1.job_list.append(OCI_DataIntegration)

# OCI Functions
# NOT EXISTING IN PYTHON? It exists in AAPI. 


# OCI Data Flow
OCI_DataFlow = JobOCIDataFlow(f"{prefix}-oci-data-flow",
                              connection_profile="ZZZ_OCI_DATAFLOW",
#"Run Name": "CM test run",
                              compartment_ocid="ocid1.compartment.oc1..aaaaaaaahjoxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                              application_ocid="ocid1.dataflowapplication.oc1.phx.anyhqljrtxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                                        )
folder1.job_list.append(OCI_DataFlow)

# OCI Data Science
OCI_DataScience = JobOCIDataScience(f"{prefix}-oci-data-science",
                                    connection_profile="ZZZ_OCI_DATASCIENCE",
                                    action="Start Job Run",
                                    parameters="\{\"projectId\":\"ocid1.datascienceproject.oc1.phx.amaaaaaatdg3y3qa3spw62ticili6ovduagkr6es4j5txq2ehjqq12341234\",\"compartmentId\":\"ocid1.compartment.oc1..aaaaaaaahjo7g63l5dhmgepb7xfszhpgikuby4rdybd4wywxuz5a23451234\",\"jobId\":\"ocid1.datasciencejob.oc1.phx.amaaaaaatdg3y3qaax2vzve2s4xpskeildkq36kfshixr65muj123423412\",\"definedTags\":\{\},\"displayName\":\"test\",\"freeformTags\":\{\},\"jobConfigurationOverrideDetails\":\{\"jobType\":\"DEFAULT\"\},\"jobLogConfigurationOverrideDetails\":\{\"enableAutoLogCreation\":true,\"enableLogging\":true,\"logGroupId\":\"ocid1.loggroup.oc1.phx.amaaaaaatdg3y3qacy5u3klrnav737vitndpltgdmabrps3sbxl3rw1234123\"\}\}",
                                    )
folder1.job_list.append(OCI_DataScience)

# OCI Big Data Service
#Not in Helix and not in AAPI

                                        

#  ██████  ████████ ██   ██ ███████ ██████  ███████ 
# ██    ██    ██    ██   ██ ██      ██   ██ ██      
# ██    ██    ██    ███████ █████   ██████  ███████ 
# ██    ██    ██    ██   ██ ██      ██   ██      ██ 
#  ██████     ██    ██   ██ ███████ ██   ██ ███████ 
                                                



# Ansible AWX
Ansible_AWS = JobAnsibleAWX(f"{prefix}-ansible-awx",
                            connection_profile="ZZZ_ANIBLE_AWX",
                            action="Launch Job Template",
                            job_template_name="Demo Job Template",
                            inventory="Demo Inventory",
                            parameters="\{\"tempo\": \"30\"\}",
                            output_logs= "checked",
                            )
folder1.job_list.append(Ansible_AWS)

# Automation Anywhere
Automation_Anywhere = JobAutomationAnywhere(f"{prefix}-automation-anywhere",
                                            connection_profile="ZZZ_AUTOMATION_ANYWHERE",
                                            automation_type="Bot",
                                            bot_input_parameters="\{%4E\t\"One\": \{%4E\t\t\"type\": \"STRING\", %4E\t\t\     \"string\": \"Hello world, go be great.\"%4E\t\}, %4E\t\      \"Num\": \{%4E\t\t\"type\": \"NUMBER\", %4E\t\t\"number\": 11%4E\t\} %4E\}",
                                            )
folder1.job_list.append(Ansible_AWS)

# DBT
DBT = JobDBT(f"{prefix}-dbt",
             connection_profile="ZZZ_DBT",
             override_job_commands="checked",
             dbt_job_id="12345",
             run_comment="A text description",
             )
folder1.job_list.append(DBT)

# Microsoft PowerBI
MS_PowerBI = JobMicrosoftPowerBI(f"{prefix}-ms-power-bi",
                                 connection_profile="ZZZ_MS_POWERBI",
                                 dataset_refresh_pipeline_deployment="Dataset Refresh",
                                 workspace_name="Demo",
                                 workspace_id="a7979345-8cfe-44e7-851f-81560e67973d",
                                 dataset_id="a7979345-8c",
                                 parameters="\{\"type\":\"Full\",\"commitMode\":\"transactional\",\"maxParallelism\":20,\"retryCount\":2\}",
                                 )
folder1.job_list.append(MS_PowerBI)


# Terraform
Terraform = JobTerraform(f"{prefix}-terraform",
                         connection_profile="ZZZ_TERRAFORM",
                         action="Run Workspace",
                         workspace_name="AWS-terraform",
                         workspace_params="\{\"key\": \"ec2_status\",\"value\": \"\"running\"\"\}",
                         )
folder1.job_list.append(Terraform)

# UI Path
UI_Path = JobUIPath(f"{prefix}-ui-path",
                    connection_profile="ZZZ_UI_PATH",
                    folder_name="Default",
                    folder_id="374915",
                    process_name="control-m-demo-process",
#      "packagekey": "209c433e-1704-4bea-b618-c9acbea6c5a2",
                    robot_name="zzz-ctm-bot",
                    robot_id="153158",
                    )
folder1.job_list.append(UI_Path)

# Tableau
Tableau = JobTableau(f"{prefix}-tableau",
                     connection_profile="ZZZ_TABLEAU",
                     action="Refresh Datasource",
                     datasource_name="BQ_Dataset",
                     )
folder1.job_list.append(Tableau)

# Jenkins
Jenkins = JobJenkins(f"{prefix}-jenkins",
                     connection_profile="ZZZ_JENKINS",
                     pipeline_name="Demo",
                     add_parameters="checked",
                     add_branch_name="checked",
                     branch_name="Development",
                     )
folder1.job_list.append(Jenkins)

# Apache NiFi
Apache_NiFi = JobApacheNiFi(f"{prefix}-apache-nifi",
                            connection_profile="ZZZ_APACHE_NIFI",
                            processor_group_id="2b315548-a11b-1ff4-c672-770c0ba49da3",
                            processor_id="2b315c50-a11b-1ff4-99f2-690aa6f35952v",
                            action="Run Processor",
                            disconnected_node_ack="unchecked",
                            )
folder1.job_list.append(Apache_NiFi)

# Apache Airflow
Apache_Airflow = JobApacheAirflow(f"{prefix}-apache-airflow",
                                  connection_profile="ZZZ_APACHE_AIRFLOW",
                                  action="Run DAG",
                                  d_a_g_name="Example_DAG",
                                  d_a_g_run_id="RunID-1",
                                  parameters="\{\"variable\": \"Value\"\}",
                                  )
folder1.job_list.append(Apache_Airflow)


# Snowflake
# Boomi Atomsphere
# Communication Suite
# Circle CI
# Databricks
# Datadog
# Informatica CS
# Quik Cloud
# Talend Data Management
# Talend OAuth
# Web Service REST
# Web Service SOAP
# Airbyte
# Pager Duty
# Astronomer
# Rabbit MQ
# VmWare
# Apache Hadoop and all job types like Spark, pig etc. 
# IBM Datastage
# Matillion
# Veritas NetBackup
# Fivetran
# Veeam Backup




# ███    ███ ███████ ████████ 
# ████  ████ ██         ██    
# ██ ████ ██ █████      ██    
# ██  ██  ██ ██         ██    
# ██      ██ ██         ██    
                           
# Azure Blob Storage
# Azure Data Lake Storage Gen2
# AWS S3
# AS2
# Sharepoint

#  ██████  ██████  ███    ██ ████████  █████  ██ ███    ██ ███████ ██████  ███████ 
# ██      ██    ██ ████   ██    ██    ██   ██ ██ ████   ██ ██      ██   ██ ██      
# ██      ██    ██ ██ ██  ██    ██    ███████ ██ ██ ██  ██ █████   ██████  ███████ 
# ██      ██    ██ ██  ██ ██    ██    ██   ██ ██ ██  ██ ██ ██      ██   ██      ██ 
#  ██████  ██████  ██   ████    ██    ██   ██ ██ ██   ████ ███████ ██   ██ ███████

# Azure AKS


# Azure Container Instances
# AZURE_Container_Instances = container
#  "Azure Container Instances_Job_2": \{
#     "Type": "Job:Azure Container Instances",
#     "ConnectionProfile": "ACI",
#     "Resource Group Name": "Keren_Resource_Group",
#     "Container Group Name": "ksu-batch-job-word-counter-in-novel",
#     "Append Log to Output": "checked",
#     "Container Name": "ksu-batch-job-word-counter-in-novel",

workflow.add(folder1)
 
print(workflow.dumps_json())
 
 
print(workflow.build().errors)
print(workflow.deploy().errors)