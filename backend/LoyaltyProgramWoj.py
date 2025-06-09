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
folder1 = Folder("zzt-loyalty-program", site_standard="Empty", controlm_server="IN01")


#jobs in zzt-loyalty-program folder

Loyalty_Program_Trigger = JobCommand(f"{prefix}-Loyalty-Program-Trigger",description="This job will start the Loyalty Program flow", command="sleep 15")
folder1.job_list.append(Loyalty_Program_Trigger)

E_Commerce_Data = JobDatabaseMSSQL_SSIS(f"{prefix}-E-Commerce-Data", 
                                        description="Orchestrating e-commerce data using Control-M can streamline various workflows, ensuring efficient and accurate processing of transactions, customer interactions, inventory updates, order fulfillment", 
                                        connection_profile="AZURE_SQL",
                                        package_source="SSIS Catalog",
                                        package_name="E-Channel")

folder1.job_list.append(E_Commerce_Data)

POS_Data = JobDatabaseEmbeddedQuery(f"{prefix}-POS-Data",
                                    query="SELECT \\n    customers.customer_id,\\n    customers.name,\\n    loyalty_points.total_points,\\n    transactions.transaction_id,\\n    transactions.transaction_date,\\n    transactions.points_earned,\\n    transactions.points_redeemed\\nFROM\\n    customers\\nJOIN\\n    loyalty_points ON customers.customer_id = loyalty_points.customer_id\\nJOIN\\n    transactions ON customers.customer_id = transactions.customer_id\\nWHERE\\n    transactions.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)\\nORDER BY \\n    customers.customer_id, transactions.transaction_date)",
                                    connection_profile="ZZZ_ORACLE_DB",
                                    description="Orchestrating POS (Point of Sale) data using Control-M can streamline and automate the processes involved in collecting, processing, and analyzing transactional data from various POS systems.\\nUsing Control-M for orchestrating POS data can significantly improve operational efficiency, provide timely insights, and enhance data-driven decision-making for businesses.")
folder1.job_list.append(POS_Data)

Transaction_Data = JobDatabaseEmbeddedQuery(f"{prefix}-Transaction-Data",
                                            query="-- Extract transaction data and customer details\\nSELECT \\n    transactions.transaction_id,\\n    transactions.transaction_date,\\n    transactions.amount,\\n    transactions.status,\\n    customers.customer_id,\\n    customers.name,\\n    customers.email\\nFROM\\n    transactions\\nJOIN\\n    customers ON transactions.customer_id = customers.customer_id\\nWHERE\\n    transactions.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)\\nORDER BY \\n    transactions.transaction_date DESC;",
                                            connection_profile="ZZZ_ORACLE_DB",
                                            description="Orchestrating transactional data using Control-M can help automate the ingestion, transformation, and processing of data from various sources, ensuring that all transactions are efficiently managed and accurately reported.\\nCollect transactional data from multiple sources, Clean and normalize the raw transactional data")
folder1.job_list.append(Transaction_Data)

Purchase_Data_Validate = JobOCIDataFlow(f"{prefix}-Purchase-Data-Validate",
                                        connection_profile="OCICP",
                                        compartment_ocid="Purchase",
                                        application_ocid="008",
                                        description="Using Control-M for orchestrating purchase data validation can greatly enhance data quality, improve operational efficiency, and provide timely insights for data-driven decision-making.\\nOrchestrating an Oracle data flow using Control-M involves automating the processes required to collect, process, transform, and load data from Oracle databases. This orchestration ensures the efficient and accurate movement of data across various stages of the workflow",
                                        )

folder1.job_list.append(Purchase_Data_Validate)

Transact_Data_Validate_Trigger = JobAwsLambda(f"{prefix}-Transact-Data-Validate-Trigger",
                                              connection_profile="ZZZ_AWS_LAMBDA_STANDARD_CP",
                                              function_name="Transact-Trigger",
                                              parameters="{%4E  \"Version\": \"2024-10-17\",%4E  \"Statement\": [%4E    {%4E      \"Effect\": \"Allow\",%4E      \"Action\": [%4E        \"snowflake:GetItem\",%4E        \"snowflake:Scan\",%4E        \"snowflake:Query\",%4E        \"snowflake:PutItem\",%4E        \"snowflake:UpdateItem\",%4E        \"snowflake:DeleteItem\"%4E      ],%4E      \"Resource\": \"arn:aws:snowflake:REGION:ACCOUNT_ID:table/Transactions\"%4E    },%4E    {%4E      \"Effect\": \"Allow\",%4E      \"Action\": \"logs:*\",%4E      \"Resource\": \"*\"%4E    }%4E  ]",
                                              append_log_to_output="unchecked",
                                              description="Use an AWS Lambda function to trigger on new transactions and process this data. This example assumes that transactions are being recorded in a DB table, and the Lambda function is configured to trigger on new entries in this table.",
                                              )
folder1.job_list.append(Transact_Data_Validate_Trigger)

Ingest_Transform = JobSnowflake(f"{prefix}-Ingest-Transform",
                                connection_profile="SNOWCP",
                                database="LoyaltyDB",
                                schema="Program-Ingest",
                                action="SQL Statement",
                                add_condition="unchecked",
                                activity_options="Copy From External Datasource",
                                overwrite="Yes",
                                start_or_pause_snowpipe="Pause Snowpipe",
                                statement_timeout="2",
                                show_more_options="unchecked",
                                show_output="unchecked",
                                snowflake_sql_statement="-- SQL Script to clean and transform data in Snowflake%4EUSE DATABASE my_snowflake_db;%4EUSE SCHEMA public;%4E%4E-- Step 1: Clean and normalize data%4ECREATE OR REPLACE TABLE staging_cleaned AS%4ESELECT %4E    ORDER_ID,%4E    CUSTOMER_ID,%4E    ORDER_DATE,%4E    ROUND(TOTAL_AMOUNT, 2) AS TOTAL_AMOUNT_CLEANED%4EFROM%4E    staging_raw%4EWHERE%4E    TOTAL_AMOUNT IS NOT NULL;%4E%4E-- Step 2: Apply business rules and additional transformations%4ECREATE OR REPLACE TABLE staging_transformed AS%4ESELECT%4E    ORDER_ID,%4E    CUSTOMER_ID,%4E    ORDER_DATE,%4E    TOTAL_AMOUNT_CLEANED,%4E    CASE %4E        WHEN TOTAL_AMOUNT_CLEANED > 100 THEN 'HIGH'%4E        ELSE 'LOW'%4E    END AS ORDER_CATEGORY%4EFROM%4E    staging_cleaned;"
                                )
folder1.job_list.append(Ingest_Transform)

Campaign_Update = JobEmbeddedScript(f"{prefix}-Campaign-Update",
                                    script="Job: Update_Email_Marketing\\nType: API\\nAPIEndpoint: \"https://email.marketing.provider/api/update_campaign\"\\nHTTPMethod: POST\\nHeaders:\\n  - \"Authorization: Bearer YOUR_ACCESS_TOKEN\"\\n  - \"Content-Type: application/json\"\\nRequestBody: |\\n  {\\n    \"campaign_id\": \"12345\",\\n    \"new_details\": {\\n        \"subject\": \"Updated Campaign Subject\",\\n        \"content\": \"Updated campaign content goes here\",\\n        \"send_date\": \"2023-04-15T12:00:00Z\"\\n    }\\n  }\\nSchedule:\\n  Frequency: Daily\\n  After: Validate_Campaign_Data\\nOutput:",
                                    description="Orchestrating campaign updates using Control-M involves automating the tasks necessary to manage, update, and distribute marketing campaign data across various channels. This provides a streamlined and efficient approach to managing marketing campaigns, ensuring timely and accurate updates.",
                                    file_name="campaign.yaml",
                                    )
folder1.job_list.append(Campaign_Update)


Member_Profile_Send = JobFileTransfer(f"{prefix}-Member-Profile-Send",
                                      connection_profile_src="ZZM_SFTP_AGT1", 
                                      connection_profile_dest="ZZM_SFTP_AGT1",
                                      description="Orchestrating member profile management using Control-M involves automating the processes that collect, process, update, and store member profile information. Efficiently managing member profiles is crucial for maintaining accurate and up-to-date information, which can be used for personalized services, marketing, and analytics", 
                                      file_transfers=[ {
                                                    "ABSTIME" : "0",
                                                    "VERNUM" : "0",
                                                    "Dest" : "Member_Profile_%%DATE.csv",
                                                    "ContinueOnFailure" : False,
                                                    "SRC_PATTERN" : "Wildcard",
                                                    "SRCOPT" : "0",
                                                    "DeleteFileOnDestIfFails" : False,
                                                    "TransferType" : "Binary",
                                                    "CASEIFS" : "0",
                                                    "DSTOPT" : "0",
                                                    "RECURSIVE" : "0",
                                                    "TransferOption" : "SrcToDest",
                                                    "Src" : "Member_Profile.csv",
                                                    "TIMELIMIT" : "0",
                                                    "FailJobOnDestCommandFailure" : False,
                                                    "EXCLUDE_WILDCARD" : "0",
                                                    "NULLFLDS" : "0",
                                                    "FailJobOnDestActionFailure" : False,
                                                    "TRIM" : "1",
                                                    "IF_EXIST" : "0",
                                                    "FailJobOnSourceCommandFailure" : False,
                                                    "UNIQUE" : "0",
                                                    "FileWatcherOptions" : {
                                                    "UnitsOfTimeLimit" : "Minutes",
                                                    "SkipToNextFileIfCriteriaNotMatch" : False,
                                                    "MinDetectedSizeInBytes" : "0"
                                                    },
                                                    "SimultaneousTransfer" : {
                                                    "TransferMultipleFilesSimultaneously" : False
                                                    },
                                                    "IncrementalTransfer" : {
                                                    "IncrementalTransferEnabled" : False,
                                                    "MaxModificationAgeForFirstRunEnabled" : False,
                                                    "MaxModificationAgeForFirstRunInHours" : "0"
                                                    }
                                                } ],
                                        )
folder1.job_list.append(Member_Profile_Send)

Reward_Processing = JobEmbeddedScript(f"{prefix}-Reward-Processing",
                                      script="python\\n#!/usr/bin/env python3\\nimport pandas as pd\\n\\n# Define the paths to the input and output files\\ntransaction_data_path = '/path/to/temp_storage/transaction_data.csv'\\nreward_data_path = '/path/to/temp_storage/reward_data.csv'\\nlog_path = '/path/to/logs/reward_calculation_log.txt'\\n\\n# Read the transaction data into a DataFrame\\ndf = pd.read_csv(transaction_data_path)\\n\\n# Initialize a list to store calculated rewards\\nreward_data = []\\n\\n# Define the reward calculation logic (e.g., 1 point for every $10 spent)\\nfor index, row in df.iterrows():\\n    customer_id = row['customer_id']\\n    amount_spent = row['amount']\\n    reward_points = int(amount_spent // 10)\\n    \\n    # Append the calculated reward data to the list\\n    reward_data.append({\\n        'customer_id': customer_id,\\n        'reward_points': reward_points\\n    })\\n\\n# Convert the reward data list to a DataFrame\\nreward_df = pd.DataFrame(reward_data)\\n\\n# Save the calculated rewards to a CSV file\\nreward_df.to_csv(reward_data_path, index=False)\\n\\n# Log the reward calculation process\\nwith open(log_path, 'w') as log_file:\\n    log_file.write(\"Reward calculation completed successfully.\\n\")",
                                      file_name="Reward.py",
                                      description= "Orchestrating reward processing using Control-M involves automating tasks related to the management, calculation, and distribution of rewards to customers or members. This helps ensure timely and accurate processing of rewards, enhancing customer satisfaction and engagement.",
                                      )
folder1.job_list.append(Reward_Processing)

Loyalty_Analytics = JobTableau(f"{prefix}-Loyalty-Analytics",
                              connection_profile="ZZT-TABCP",
                              action="Refresh Datasource",
                              datasource_name="Loyalty_data",
)
folder1.job_list.append(Loyalty_Analytics)

Loyalty_Program_SLA = JobSLAManagement(f"{prefix}-Loyalty-Program-SLA", 
                                       service_name=f"{prefix}-Loyalty-Program-Service",
                                       job_runs_deviations_tolerance="3",
                                       )
folder1.job_list.append(Loyalty_Program_SLA)


#connections
workflow.chain(
    [
        Loyalty_Program_Trigger, E_Commerce_Data, Purchase_Data_Validate, Ingest_Transform, Campaign_Update, Loyalty_Analytics, Loyalty_Program_SLA
    ],
    inpath='zzt-loyalty-program'
)
workflow.chain(
    [
        Loyalty_Program_Trigger, POS_Data, Purchase_Data_Validate
    ],
    inpath='zzt-loyalty-program'
)
workflow.chain(
    [
        Loyalty_Program_Trigger, POS_Data,  Transact_Data_Validate_Trigger, Ingest_Transform, Member_Profile_Send, Loyalty_Analytics
    ],
    inpath='zzt-loyalty-program'
)
workflow.chain(
    [
         Loyalty_Program_Trigger, Transaction_Data, Transact_Data_Validate_Trigger
    ],
    inpath='zzt-loyalty-program'
)
workflow.chain(
    [
         Ingest_Transform, Reward_Processing, Loyalty_Analytics
    ],
    inpath='zzt-loyalty-program'
)




workflow.add(folder1)
 
print(workflow.dumps_json())
 
 
print(workflow.build().errors)
print(workflow.deploy().errors)