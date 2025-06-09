from flask import Flask, request, jsonify, Response
from ctm_python_client.core.workflow import *
from ctm_python_client.core.credential import *
from ctm_python_client.core.comm import *
from aapi import *
from my_secrets import my_secrets

    
# Somewhere global in your module
JOB_LIBRARY = {
        "job1": lambda: JobCommand("job1", command="echo JOB1"),
        "job2": lambda: JobCommand("job2", command="echo JOB2"),
        "Data_SFDC": lambda: JobCommand(
            "zzt-Data-SFDC",
            description="JOB 1: retrieve_sales_data SalesForce CRM",
            command='curl "https://data.nasdaq.com/api/v3/datatables/EVEST/MDFIRM?api_key=EQ7KseM9AiJk9Xye7KAK"'
        ), 
    "Data_SAP_inventory": lambda: JobSAPR3BatchInputSession(
        "zzt-Data-SAP-inventory",
        description="JOB 2: retrieve_inventory_data SAP ERP",
        connection_profile="SAPCP",
        target="SAP_SERVER",
        session=JobSAPR3BatchInputSession.Session("Stock_Session")
    ),
    "Data_Market_API": lambda: JobCommand(
        "zzt-Market-Data-API",
        description="JOB 3: Retrieve market data from external APIs (e.g. Alpha Vantage)",
        command='curl "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=%%apikey"'
    ),
    "Data_Weather_API": lambda: JobCommand(
        "zzt-Weather-Data-API",
        description="JOB 4: Retrieve weather data from external APIs (e.g. OpenWeatherMap)",
        command='wget "https://api.openweathermap.org/data/2.5/weather?zip=%%zipcode,us&appid=%%appid&units=imperial" -O $HOME/output.json'
    ),
    "JobDatabaseSQLScript": lambda: JobDatabaseSQLScript(
        "zzt-Oracle-Data",
        connection_profile="ZZT-ORACLE-SALES",
        sql_script="export_store_sales.sql",
        output_sql_output="Y",
        description="JOB 5: Retrieve data from Oracle database"
    ),
    "JobFileTransfer": lambda: JobFileTransfer(
        "zzt-Transfer-to-Centralized-Repo",
        connection_profile_src="ZZM_SFTP_AGT1",
        connection_profile_dest="ZZM_FS_LOCAL",
        description="Job 5: Collect and aggregate data into a centralized repository using CTM MFT",
        file_transfers=[{
            "ABSTIME": "0", "VERNUM": "0", "Dest": "/opt/controlm/ctm/DemandForecast/",
            "ContinueOnFailure": False, "SRC_PATTERN": "Wildcard", "SRCOPT": "0",
            "DeleteFileOnDestIfFails": False, "TransferType": "Binary", "CASEIFS": "0",
            "DSTOPT": "0", "RECURSIVE": "0", "TransferOption": "SrcToDest", "Src": "/",
            "TIMELIMIT": "0", "FailJobOnDestCommandFailure": False, "EXCLUDE_WILDCARD": "0",
            "NULLFLDS": "0", "FailJobOnDestActionFailure": False, "TRIM": "1", "IF_EXIST": "0",
            "FailJobOnSourceCommandFailure": False, "UNIQUE": "0",
            "FileWatcherOptions": {
                "UnitsOfTimeLimit": "Minutes", "SkipToNextFileIfCriteriaNotMatch": False,
                "MinDetectedSizeInBytes": "0"
            },
            "SimultaneousTransfer": {"TransferMultipleFilesSimultaneously": False},
            "IncrementalTransfer": {
                "IncrementalTransferEnabled": False,
                "MaxModificationAgeForFirstRunEnabled": False,
                "MaxModificationAgeForFirstRunInHours": "1"
            }
        }]
    ),
    "Data_Storage_AWS_S3": lambda: JobFileTransfer(
        "zzt-Data-Storage-AWS-S3",
        connection_profile_src="ZZM_SFTP_AGT1",
        connection_profile_dest="ZZM_FS_LOCAL",
        description="Job 5: Store aggregated data in AWS S3 using CTM MFT",
        file_transfers=[{
            "ABSTIME": "0", "VERNUM": "0", "Dest": "/opt/controlm/ctm/DemandForecast/",
            "ContinueOnFailure": False, "SRC_PATTERN": "Wildcard", "SRCOPT": "0",
            "DeleteFileOnDestIfFails": False, "TransferType": "Binary", "CASEIFS": "0",
            "DSTOPT": "0", "RECURSIVE": "0", "TransferOption": "SrcToDest", "Src": "/",
            "TIMELIMIT": "0", "FailJobOnDestCommandFailure": False, "EXCLUDE_WILDCARD": "0",
            "NULLFLDS": "0", "FailJobOnDestActionFailure": False, "TRIM": "1", "IF_EXIST": "0",
            "FailJobOnSourceCommandFailure": False, "UNIQUE": "0",
            "FileWatcherOptions": {
                "UnitsOfTimeLimit": "Minutes", "SkipToNextFileIfCriteriaNotMatch": False,
                "MinDetectedSizeInBytes": "0"
            },
            "SimultaneousTransfer": {"TransferMultipleFilesSimultaneously": False},
            "IncrementalTransfer": {
                "IncrementalTransferEnabled": False,
                "MaxModificationAgeForFirstRunEnabled": False,
                "MaxModificationAgeForFirstRunInHours": "1"
            }
        }]
    ),
    "JobHadoopMapReduce": lambda: JobHadoopMapReduce(
        "zzt-Analyse-Data-Hadoop",
        connection_profile="CP",
        description="JOB 8: Aggregate and analyse data using Hadoop",
        program_jar="/home/user1/hadoop-jobs/hadoop-mapreduce-examples.jar",
        main_class="com.mycomp.mainClassName",
        arguments=["arg1", "arg2"]
    ),
    "JobSLAManagement": lambda: JobSLAManagement(
        "zzt-Demand-Forecasting-Process-SLA",
        service_name="Demand Forecasting Service",
        job_runs_deviations_tolerance="3"
    ),"AWS_AppFlow": lambda: JobAwsAppFlow(
        "zzt-aws-app-flow",
        description="AWS AppFlow",
        connection_profile="ZZZ_AWS_APPFLOW",
        action="Trigger Flow - Key & Secret Auth",
        flow_name="testflow1",
        trigger_flow_with_idempotency_token="checked",
        client_token="Token_Control-1_for_AppFlow%%ORDERID"
    ),
    "AWS_AppRunner": lambda: JobAwsAppRunner(
        "zzt-aws-app-runner",
        connection_profile="ZZZ_AWS_APP_RUNNER",
        action="Deploy",
        service_arn="arn:aws:apprunner:us-east-1:xxxxxxxxxx:service/Hello_World/xxxxxxx",
        output_job_logs="unchecked"
    ),
    "AWS_Athena": lambda: JobAwsAthena(
        "zzt-aws-athena",
        description="AWS Athena",
        connection_profile="ZZZ_AWS_ATHENA",
        output_location="s3://s3bucket}",
        db_catalog_name="DB_Catalog_Athena",
        database_name="DB_Athena",
        query="Select * from Athena_Table",
        workgroup="Primary"
    ),
    "AWS_Backup": lambda: JobAwsBackup(
        "zzt-aws-backup",
        connection_profile="ZZZ_AWS_BACKUP",
        action="Backup",
        windows_vss="Disabled",
        backup_vault_name="Test1",
        role_arn="arn:aws:iam::12234888888:role/service-role/AWSBackupDefaultServiceRole1",
        idempotency_token="token12345"
    ),
    "AWS_Batch": lambda: JobAwsBatch(
        "zzt-aws-batch",
        connection_profile="ZZZ_AWS_BATCH",
        job_name="job_name",
        job_definition_and_revision="zzz-batch-job-definition:1",
        job_queue="zzz-batch-job-queue",
        job_attempts="2",
        use_advanced_json_format="unchecked",
        container_overrides_command='["echo", "hello from control-m"]'
    ),
    "AWS_CloudFormation": lambda: JobAwsCloudFormation(
        "zzt-aws-cloudformation",
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
    ),
    "AWS_DataPipeline": lambda: JobAwsDataPipeline(
        "zzt-aws-datapipeline",
        connection_profile="ZZZ_AWS_DATAPIPELINE",
        trigger_created_pipeline="Trigger Pipeline",
        pipeline_id="df-020488024DNBVFN1S2U",
        pipeline_name="demo-pipeline",
        pipeline_unique_id="235136145"
    ),
    "AWS_DataSync": lambda: JobAwsDataSync(
        "zzt-aws-datasync",
        connection_profile="ZZZ_AWS_DATASYNC",
        action="Execute Task",
        variables=[{"UCM-TASKARNSECRET": "arn:aws:datasync:us-east-1:122343283363:task/task-0752fa45494724f46"}],
        output_logs="checked"
    ),
    "AWS_DynamoDB": lambda: JobAwsDynamoDB(
        "zzt-aws-dynamodb",
        connection_profile="ZZZ_AWS_DYNAMODB",
        action="Execute Statement",
        run_statement_with_parameter="checked",
        statement="Select * From IFteam  where Id=? OR Name=?",
        statement_parameters='[{"N": "20"},{"S":"Stas30"}]'
    ),
    "AWS_EC2": lambda: JobAwsEC2(
        "zzt-aws-ec2",
        description="AWS EC2",
        connection_profile="ZZZ_AWS_EC2",
        operations="Create",
        placement_availability_zone="us-west-2c",
        instance_type="m1.small",
        subnet_id="subnet-00aa899a7db25494d",
        key_name="ksu-aws-ec2-key-pair",
        get_instances_logs="unchecked"
    ),
    "AWS_ECS": lambda: JobAwsECS(
        "zzt-aws-ecs",
        connection_profile="ZZZ_AWS_ECS",
        action="Preset Json",
        ecs_cluster_name="ECSIntegrationCluster",
        ecs_task_definition="ECSIntegrationTask",
        assign_public_ip="True",
        network_security_groups="\"sg-01e4a5bfac4189d10\"",
        network_subnets="\"subnet-045ddaf41d4852fd7\", \"subnet-0b574cca721d462dc\", \"subnet-0e108b6ba4fc0c4d7\"",
        override_container="IntegrationURI",
        override_command="\"/bin/sh -c 'whoami'\"",
        environment_variables='{"name": "var1", "value": "1"}',
        get_logs="Get Logs"
    ),
    "AWS_EMR": lambda: JobAwsEMR(
        "zzt-aws-emr",
        connection_profile="ZZZ_AWS_EMR",
        cluster_id="j-21PO60WBW77GX",
        notebook_id="e-DJJ0HFJKU71I9DWX8GJAOH734",
        relative_path="ShowWaitingAndRunningClusters.ipynb",
        notebook_execution_name="TestExec",
        service_role="EMR_Notebooks_DefaultRole",
        use_advanced_json_format="unchecked"
    ),
    "AWS_Glue": lambda: JobAwsGlue(
        "zzt-aws-glue",
        connection_profile="ZZZ_AWS_GLUE",
        glue_job_name="ZZZ_GLUE_JOB",
        glue_job_arguments="checked",
        arguments='{"--source": "https://jsonplaceholder.typicode.com/todos/1", "--destination": "ncu-datapipe"}'
    ),
    "AWS_GlueDataBrew": lambda: JobAwsGlueDataBrew(
        "zzt-aws-glue-databrew",
        description="AWS Glue Databrew",
        connection_profile="ZZZ_AWS_GLUE_DATABREW",
        job_name="databrew-job"
    ),
    "AWS_Lambda": lambda: JobAwsLambda(
        "zzt-aws-lambda",
        connection_profile="ZZZ_AWS_LAMBDA",
        function_name="MyTestFunction",
        parameters='{"param1": 60, "param2": 60}',
        append_log_to_output="checked"
    ),
    "AWS_MainframeModernization": lambda: JobAwsMainframeModernization(
        "zzt-aws-mainframe-modernization",
        connection_profile="ZZZ_AWS_MAINFRAME",
        application_name="Demo",
        action="Start Batch Job",
        jcl_name="DEMO.JCL",
        retrieve_cloud_watch_logs="checked",
        application_action="Start Application"
    ),
    "AWS_MWAA": lambda: JobAwsMWAA(
        "zzt-aws-mwaa",
        connection_profile="ZZZ_AWS_MWAA",
        action="Run DAG",
        m_w_a_a_environment_name="MyAirflowEnvironment",
        d_a_g_name="example_dag_basic",
        parameters="{}"
    ),
    "AWS_QuickSight": lambda: JobAwsQuickSight(
        "zzt-aws-quicksight",
        description="AWS QuickSight",
        connection_profile="ZZZ_AWS_QUICKSIGHT",
        aws_dataset_id="d351ce9e-1500-4494-b0e1-43b2d6f48861",
        refresh_type="Full Refresh"
    ),
    "AWS_Redshift": lambda: JobAwsRedshift(
        "zzt-aws-redshift",
        connection_profile="ZZZ_AWS_REDSHIFT",
        load_redshift_sql_statement="select * from Redshift_table",
        actions="Redshift SQL Statement",
        workgroup_name="Workgroup_Name",
        secret_manager_arn="Secret_Manager_ARN",
        database="Database_Redshift"
    ),
    "AWS_SageMaker": lambda: JobAwsSageMaker(
        "zzt-aws-sagemaker",
        description="AWS SageMaker",
        connection_profile="ZZZ_AWS_SAGEMAKER",
        pipeline_name="SageMaker_Pipeline",
        add_parameters="unchecked",
        retry_pipeline_execution="unchecked"
    ),
    "AWS_SNS": lambda: JobAwsSNS(
        "zzt-aws-sns",
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
        sms_type="Transactional"
    ),
    "AWS_SQS": lambda: JobAwsSQS(
        "zzt-aws-sqs",
        connection_profile="ZZZ_AWS_SQS",
        queue_type="Standard Queue",
        queue_url="https://sqs.eu-west-2.amazonaws.com/122343283363/TestingQueue",
        message_body="Test Message Body",
        delay_seconds="0",
        message_attributes="checked",
        attribute1_name="Attribute.1",
        attribute1_data_type="String",
        attribute1_value="CustomValue1"
    ),
    "AWS_StepFunctions": lambda: JobAwsStepFunctions(
        "zzt-aws-stepfunctions",
        connection_profile="ZZZ_AWS_STEP_FUNCTIONS",
        execution_name="Step Functions Exec",
        state_machine_arn="arn:aws:states:us-east-1:155535555553:stateMachine:MyStateMachine",
        parameters='{"parameter1":"value1"}',
        show_execution_logs="checked"
    ),
    "AZURE_HDInsight": lambda: JobAzureHDInsight(
        "zzt-azure-hd-insight",
        connection_profile="ZZZ_AZURE_HD_INSIGHT",
        parameters=('{'
                    '"file": "wasb://asafcluster2-2022-06-06t07-39-08-081z@asafcluster2hdistorage.blob.core.windows.net/example/jars/hadoop-mapreduce-examples.jar",'
                    '"jars": ["wasb://asafcluster2-2022-06-06t07-39-08-081z@asafcluster2hdistorage.blob.core.windows.net/example/jars/hadoop-mapreduce-examples.jar"],'
                    '"driverMemory": "5G", "driverCores": 3, "executorMemory": "5G", "executorCores": 3, "numExecutors": 1'
                    '}'),
        bring_job_logs_to_output="checked"
    ),
    "AZURE_Batch": lambda: JobAzureBatchAccounts(
        "zzt-azure-batch-accounts",
        connection_profile="ZZZ_AZURE_BATCH_ACCOUNTS",
        batch_job_id="zzz-jobid",
        task_command_line="cmd /c echo hello from Control-M",
        max_wall_clock_time="Unlimited",
        max_wall_time_unit="Minutes",
        max_task_retry_count="None",
        retention_time="Custom",
        retention_time_digits="4",
        retention_time_unit="Days",
        append_log_to_output="checked"
    ),
    "AZURE_Databricks": lambda: JobAzureDatabricks(
        "zzt-azure-databricks",
        connection_profile="ZZZ_AZURE_DATABRICKS",
        databricks_job_id="168477649492161",
        parameters='"notebook_params":{"param1":"val1", "param2":"val2"}'
    ),
    "AZURE_DataFactory": lambda: JobAzureDataFactory(
        "zzt-azure-datafactory",
        connection_profile="ZZZ_AZURE_DATAFACTORY",
        resource_group_name="ZZZ_Group",
        data_factory_name="zzz-test",
        pipeline_name="test123",
        parameters="{}"
    ),
    "AZURE_Functions": lambda: JobAzureFunctions(
        "zzt-azure-function",
        connection_profile="ZZZ_AZURE_FUNCTIONS",
        function_app="new-function",
        function_name="Hello",
        optional_input_parameters='{"param1":"val1", "param2":"val2"}',
        function_type="activity"
    ),
    "AZURE_LogicApps": lambda: JobAzureLogicApps(
        "zzt-azure-logicapps",
        connection_profile="ZZZ_AZURE_LOGICAPPS",
        workflow="zzz-logic",
        parameters='{"bodyinfo":"hello from CM"}',
        get_logs="unchecked"
    ),
    "AZURE_VM": lambda: JobAzureVM(
        "zzt-azure-vm",
        connection_profile="ZZZ_AZURE_VM",
        operation="Create\\Update",
        verification_poll_interval="10",
        vm_name="zzz-vm1",
        input_parameters='{"key": "val"}',
        delete_vm_os_disk="unchecked"
    ),
    "AZURE_Synapse": lambda: JobAzureSynapse(
        "zzt-azure-synapse",
        connection_profile="ZZZ_AZURE_SYNAPSE",
        pipeline_name="zzz_synapse_pipeline",
        parameters='{"periodinseconds":"40"}'
    ),
    "AZURE_Machine_Learning": lambda: JobAzureMachineLearning(
        "zzt-azure-machine-learning",
        connection_profile="ZZZ_AZURE_MACHINELEARNING",
        resource_group_name="ZZZ_Resource_Group",
        workspace_name="ZZZ_ML",
        action="Trigger Endpoint Pipeline",
        pipeline_endpoint_id="353c4707-fd23-40f6-91e2-83bf7cba764c",
        parameters='{"ExperimentName": "test", "DisplayName":"test1123"}'
    ),
    "AZURE_Backup": lambda: JobAzureBackup(
        "zzt-azure-backup",
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
        restore_region="UK South"
    ),
    "AZURE_Resource_Manager": lambda: JobAzureResourceManager(
        "zzt-azure-resource-manager",
        connection_profile="ZZZ_AZURE_RESOURCE_MANAGER",
        action="Create Deployment",
        resource_group_name="ZZZ_Resource_Group",
        deployment_name="demo",
        deployment_properties=(
            '{"properties": {"templateLink": {"uri": '
            '"https://123.blob.core.windows.net/test123/123.json?sp=r&st=2023-05-23T08:39:09Z&se=2023-06-10T16:39:09Z'
            '&sv=2022-11-02&sr=b&sig=RqrATxi4Sic2UwQKFu%2FlwaQS7fg5uPZyJCQiWX2D%2FCc%3D"}}}'
        )
    ),
    "AZURE_DevOps": lambda: JobAzureDevOps(
        "zzt-azure-devops",
        connection_profile="ZZZ_AZURE_DEVOPS",
        project_name="TestProject",
        actions="Run Pipeline with More Options",
        pipeline_id="1",
        show_build_logs="checked",
        stages_to_skip='"Test","Deploy"'
    ),
    "AZURE_Service_Bus": lambda: JobAzureServiceBus(
        "zzt-azure-service-bus",
        connection_profile="ZZZ_AZURE_SERVICEBUS",
        message_body='{"key1":"value1"}',
        service_bus_namespace="test",
        queue_topic_name="testname",
        message_format="application/json"
    ),

    "GCP_Dataflow": lambda: JobGCPDataflow(
        "zzt-gcp-dataflow",
        connection_profile="ZZZ_GCP_DATAFLOW",
        project_id="applied-lattice-11111",
        region="us-central1",
        template_type="Classic Template",
        template_location_gs_="gs://dataflow-templates-us-central1/latest/Word_Count",
        parameters__json_format='{"jobName": "wordcount11"}',
        log_level="INFO"
    ),
    "GCP_Dataproc": lambda: JobGCPDataproc(
        "zzt-gcp-dataproc",
        connection_profile="ZZZ_GCP_DATAPROC",
        project_id="applied-lattice-333108",
        account_region="us-central1",
        dataproc_task_type="Workflow Template",
        workflow_template="<TemplateID>"
    ),
    "GCP_Functions": lambda: JobGCPFunctions(
        "zzt-gcp-functions",
        connection_profile="ZZZ_GCP_FUNCTIONS",
        function_parameters="Body",
        body='{"message":"controlm-body-%%ORDERID"}',
        failure_tolerance="2",
        get_logs="unchecked",
        location="us-central1",
        function_name="ZZZ_function",
        project_id="<Project ID>"
    ),
    "GCP_VM": lambda: JobGCPVM(
        "zzt-gcp-vm",
        connection_profile="ZZZ_GCP_VM",
        project_id="applied-lattice",
        zone="us-central1-f",
        operation="Stop",
        instance_name="cluster-us-cen1-f-m"
    ),
    "GCP_BigQuery": lambda: JobGCPBigQuery(
        "zzt-gcp-bigquery",
        connection_profile="ZZZ_GCP_BIGQUERY",
        action="Query",
        run_select_query_and_copy_to_table="checked",
        project_name="applied-lattice-333108",
        dataset_name="Test",
        sql_statement="select * from IFteam"
    ),
    "GCP_Dataprep": lambda: JobGCPDataprep(
        "zzt-gcp-dataprep",
        connection_profile="ZZZ_GCP_DATAPREP",
        flow_name="data_manipulation",
        parameters='{"schemaDriftOptions":{"schemaValidation": "true","stopJobOnErrorsFound": "true"}}',
        execute_job_with_idempotency_token="checked",
        idempotency_token="Control-M-Token-%%ORDERID"
    ),
    "GCP_Dataplex": lambda: JobGCPDataplex(
        "zzt-gcp-dataplex",
        connection_profile="ZZZ_GCP_DATAPLEX",
        project_id="applied-lattice-333108",
        location="europe-west2",
        action="Data Profiling Scan",
        lake_name="Demo_Lake",
        task_name="Demo_Task",
        scan_name="Demo"
    ),
    "GCP_DeploymentManager": lambda: JobGCPDeploymentManager(
        "zzt-gcp-deployment-manager",
        connection_profile="ZZZ_GCP_DEPLOYMENT_MANAGER",
        project_id="applied-lattice-333111",
        action="Create Deployment",
        deployment_name="demo_deployment",
        yaml_config_content="{resources: [{type: compute.v1.instance, name: quickstart-deployment-vm, properties: {zone: us-central1-f, machineType: 'https://www.googleapis.com/compute/v1/projects/applied-lattice-333108/zones/us-central1-f/machineTypes/e2-micro', disks: [{deviceName: boot, type: PERSISTENT, boot: true, autoDelete: true, initializeParams: {sourceImage: 'https://www.googleapis.com/compute/v1/projects/debian-cloud/global/images/family/debian-11'}}], networkInterfaces: [{network: 'https://www.googleapis.com/compute/v1/projects/applied-lattice-333108/global/networks/default', accessConfigs: [{name: External NAT, type: ONE_TO_ONE_NAT}]}]}}]}"
    ),
    "GCP_Batch": lambda: JobGCPBatch(
        "zzt-gcp-batch",
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
        allowed_locations='["regions us-east1","zones us-east1-b"]',
        service_account__email_format="example@example.com"
    ),
    "GCP_Workflows": lambda: JobGCPWorkflows(
        "zzt-gcp-workflows",
        connection_profile="ZZZ_GCP_WORKFLOWS",
        show_workflow_results="checked",
        project_id="12345id",
        location="us-central1",
        workflow_name="workflow-1",
        parameters_json_input='{"argument": "{}"}'
    ),
    "GCP_Data_Fusion": lambda: JobGCPDataFusion(
        "zzt-gcp-datafusion",
        connection_profile="ZZZ_GCP_DATAFUSION",
        region="us-west1",
        project_name=" Project-Name ",
        instance_name=" Instance-Name ",
        pipeline_name="TestBatchPipeLine",
        runtime_parameters='{ "Parameter1":"Value1"}',
        get_logs="checked"
    ),
    "GCP_CloudRun": lambda: JobGCPCloudRun(
        "zzt-gcp-cloudrun",
        connection_profile="ZZZ_GCP_CLOUDRUN",
        project_id="applied-lattice-333108",
        location="us-central1",
        job_name="testjob",
        overrides_specification="{}"
    ),
    "GCP_Composer": lambda: JobGCPComposer(
        "zzt-gcp-composer",
        connection_profile="ZZZ_GCP_COMPOSER",
        action="Run DAG",
        d_a_g_name="example_dag_basic",
        parameters="{}"
    ),

    "OCI_VM": lambda: JobOCIVM(
        "zzt-oci-vm",
        connection_profile="ZZZ_OCI_VM",
        action="Start",
        parameters='{...}'  # Consider storing the full JSON in a separate variable or file for readability
    ),
    "OCI_DataIntegration": lambda: JobOCIDataIntegration(
        "zzt-oci-data-integrations",
        connection_profile="ZZZ_OCI_DATAINTEGRATIONS",
        actions="Run Task",
        application_key="0dab7145-1e2b-4d2b-844e-d784cadc28be",
        task_key="b5636bc5-d672-9ca0-84a0-9b20c17d0bda",
        workspace_ocid="ocid1.disworkspace.oc1.phx.anyhqljr2ow634yaho5mitq5jxqcreq4kt3ycpoltpakb57flphqowx3eeia",
        task_run_name="Task1",
        task_run_input_parameters='"PARAMETER": {"simpleValue": "Hello"}, "PARAMETER2": {"simpleValue": "Hello222"}'
    ),
    "OCI_DataFlow": lambda: JobOCIDataFlow(
        "zzt-oci-data-flow",
        connection_profile="ZZZ_OCI_DATAFLOW",
        compartment_ocid="ocid1.compartment.oc1..aaaaaaaahjoxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        application_ocid="ocid1.dataflowapplication.oc1.phx.anyhqljrtxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ),
    "OCI_DataScience": lambda: JobOCIDataScience(
        "zzt-oci-data-science",
        connection_profile="ZZZ_OCI_DATASCIENCE",
        action="Start Job Run",
        parameters='{...}'  # same as above: long JSON string can be offloaded
    ),
    "Ansible_AWX": lambda: JobAnsibleAWX(
        "zzt-ansible-awx",
        connection_profile="ZZZ_ANIBLE_AWX",
        action="Launch Job Template",
        job_template_name="Demo Job Template",
        inventory="Demo Inventory",
        parameters='{"tempo": "30"}',
        output_logs="checked"
    ),
    "Automation_Anywhere": lambda: JobAutomationAnywhere(
        "zzt-automation-anywhere",
        connection_profile="ZZZ_AUTOMATION_ANYWHERE",
        automation_type="Bot",
        bot_input_parameters='{"One": {"type": "STRING", "string": "Hello world, go be great."}, "Num": {"type": "NUMBER", "number": 11}}'
    ),
    "DBT": lambda: JobDBT(
        "zzt-dbt",
        connection_profile="ZZZ_DBT",
        override_job_commands="checked",
        dbt_job_id="12345",
        run_comment="A text description"
    ),
    "MS_PowerBI": lambda: JobMicrosoftPowerBI(
        "zzt-ms-power-bi",
        connection_profile="ZZZ_MS_POWERBI",
        dataset_refresh_pipeline_deployment="Dataset Refresh",
        workspace_name="Demo",
        workspace_id="a7979345-8cfe-44e7-851f-81560e67973d",
        dataset_id="a7979345-8c",
        parameters='{"type":"Full","commitMode":"transactional","maxParallelism":20,"retryCount":2}'
    ),
    "Terraform": lambda: JobTerraform(
        "zzt-terraform",
        connection_profile="ZZZ_TERRAFORM",
        action="Run Workspace",
        workspace_name="AWS-terraform",
        workspace_params='{"key": "ec2_status", "value": "running"}'
    ),
    "UI_Path": lambda: JobUIPath(
        "zzt-ui-path",
        connection_profile="ZZZ_UI_PATH",
        folder_name="Default",
        folder_id="374915",
        process_name="control-m-demo-process",
        robot_name="zzz-ctm-bot",
        robot_id="153158"
    ),
    "Tableau": lambda: JobTableau(
        "zzt-tableau",
        connection_profile="ZZZ_TABLEAU",
        action="Refresh Datasource",
        datasource_name="BQ_Dataset"
    ),
    "Jenkins": lambda: JobJenkins(
        "zzt-jenkins",
        connection_profile="ZZZ_JENKINS",
        pipeline_name="Demo",
        add_parameters="checked",
        add_branch_name="checked",
        branch_name="Development"
    ),
    "Apache_NiFi": lambda: JobApacheNiFi(
        "zzt-apache-nifi",
        connection_profile="ZZZ_APACHE_NIFI",
        processor_group_id="2b315548-a11b-1ff4-c672-770c0ba49da3",
        processor_id="2b315c50-a11b-1ff4-99f2-690aa6f35952v",
        action="Run Processor",
        disconnected_node_ack="unchecked"
    ),
    "Apache_Airflow": lambda: JobApacheAirflow(
        "zzt-apache-airflow",
        connection_profile="ZZZ_APACHE_AIRFLOW",
        action="Run DAG",
        d_a_g_name="Example_DAG",
        d_a_g_run_id="RunID-1",
        parameters='{"variable": "Value"}'
    )
            }