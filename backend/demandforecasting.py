#%%
from ctm_python_client.core.workflow import *
from ctm_python_client.core.comm import *
from ctm_python_client.core.credential import *
from aapi import *
from my_secrets import my_secrets


#ENV
my_env = Environment.create_saas(endpoint=my_secrets['helix_sandbox_endpoint'],api_key=my_secrets['helix_sandbox_api_key'])
 
#defaults
defaults = WorkflowDefaults(run_as="ctmagent", host="zzz-linux-agents",application="ZZT-Version1-DG", sub_application="ZZT-Version1-DG")
 
#Workflow
workflow = Workflow(my_env, defaults=defaults)
 
#FOLDER
folder1 = Folder("zzt-demand-forecasting", site_standard="Empty", controlm_server="IN01")

#TEST AREA
workflow.add(folder1)
zztDataSourcesandCollection = SubFolder("zzt-Data-Sources-and-Collection",)
zztDataProcessingandConsumption = SubFolder("zzt-Data-Processing-and-Consumption")
folder1.sub_folder_list.append(zztDataSourcesandCollection)
folder1.sub_folder_list.append(zztDataProcessingandConsumption)

workflow.connect("zzt-Data-Sources-and-Collection", "zzt-Data-Processing-and-Consumption", inpath="zzt-demand-forecasting")
#END OF TEST AREA

exit()

#Subfolders
zztDataSourcesandCollection = SubFolder("zzt-Data-Sources-and-Collection",)
zztDataSourcesandCollection_addEventsList = AddEvents([Event(event="zzt-Data-Sources-and-Collection_OK",date=Event.Date.OrderDate)])
zztDataSourcesandCollection.events_to_add.append(zztDataSourcesandCollection_addEventsList)
folder1.sub_folder_list.append(zztDataSourcesandCollection)

zztDataProcessingandConsumption = SubFolder("zzt-Data-Processing-and-Consumption")
zztDataProcessingandConsumption_WaitEventsList = WaitForEvents([Event(event="zzt-Data-Sources-and-Collection_OK",date=Event.Date.OrderDate)])
zztDataProcessingandConsumption.wait_for_events.append(zztDataProcessingandConsumption_WaitEventsList)
zztDataProcessingandConsumption_DeleteEventsList = DeleteEvents([Event(event="zzt-Data-Sources-and-Collection_OK",date=Event.Date.OrderDate)])
zztDataProcessingandConsumption.delete_events_list.append(zztDataProcessingandConsumption_DeleteEventsList)
#connection to SLA
zztDataProcessingandConsumption_addEventsList = AddEvents([Event(event="zztDataProcessingandConsumption_OK",date=Event.Date.OrderDate)])
zztDataProcessingandConsumption.events_to_add.append(zztDataProcessingandConsumption_addEventsList)
#END OF connection to SLA
folder1.sub_folder_list.append(zztDataProcessingandConsumption)


#jobs in zzt-Data-Sources-and-Collection folder

Data_SAP_inventory = JobSAPR3BatchInputSession("zzt-Data-SAP-inventory", description="JOB 2: retrieve_inventory_data SAP ERP", connection_profile="SAPCP", target="SAP_SERVER", session=JobSAPR3BatchInputSession.Session("Stock_Session"))
zztDataSourcesandCollection.job_list.append(Data_SAP_inventory)

Data_SFDC = JobCommand("zzt-Data-SFDC",description="JOB 1: retrieve_sales_data SalesForce CRM", command = "curl \"https://data.nasdaq.com/api/v3/datatables/EVEST/MDFIRM?api_key=EQ7KseM9AiJk9Xye7KAK\"")
zztDataSourcesandCollection.job_list.append(Data_SFDC)

Data_Market_API = JobCommand("zzt-Market-Data-API",description="JOB 3: Retrieve market data from external APIs (e.g. Neilsen, IRI)", command = "curl \"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo\"")
zztDataSourcesandCollection.job_list.append(Data_Market_API)

Data_Weather_API = JobCommand("zzt-Weather-Data-API",description="JOB 4: Retrieve weather data from external APIs (e.g. OpenWeatherMap)", command = "wget \"https://api.openweathermap.org/data/2.5/weather?zip=%%zipcode,us&appid=%%appid&units=imperial\" -O $HOME/output.json")
zztDataSourcesandCollection.job_list.append(Data_Weather_API)

Data_Oracle = JobDatabaseSQLScript("zzt-Oracle-Data", connection_profile="ZZT-ORACLE-SALES", sql_script="export_store_sales.sql", output_sql_output="Y",description="JOB 5: Retrieve data from Oracle database")
zztDataSourcesandCollection.job_list.append(Data_Oracle)

Transfer_to_Centralized_Repo = JobFileTransfer("zzt-Transfer-to-Centralized-Repo", connection_profile_src="ZZM_SFTP_AGT1", connection_profile_dest="ZZM_FS_LOCAL",description="Job 5: Collect and aggregate all retrieve data into a centralized repository unising CTM MFT", file_transfers=[{
            "ABSTIME": "0",
            "VERNUM": "0",
            "Dest": "/opt/controlm/ctm/DemandForecast/",
            "ContinueOnFailure": False,
            "SRC_PATTERN": "Wildcard",
            "SRCOPT": "0",
            "DeleteFileOnDestIfFails": False,
            "TransferType": "Binary",
            "CASEIFS": "0",
            "DSTOPT": "0",
            "RECURSIVE": "0",
            "TransferOption": "SrcToDest",
            "Src": "/",
            "TIMELIMIT": "0",
            "FailJobOnDestCommandFailure": False,
            "EXCLUDE_WILDCARD": "0",
            "NULLFLDS": "0",
            "FailJobOnDestActionFailure": False,
            "TRIM": "1",
            "IF_EXIST": "0",
            "FailJobOnSourceCommandFailure": False,
            "UNIQUE": "0",
            "FileWatcherOptions": {
              "UnitsOfTimeLimit": "Minutes",
              "SkipToNextFileIfCriteriaNotMatch": False,
              "MinDetectedSizeInBytes": "0"
            },
            "SimultaneousTransfer": {
              "TransferMultipleFilesSimultaneously": False
            },
            "IncrementalTransfer": {
              "IncrementalTransferEnabled": False,
              "MaxModificationAgeForFirstRunEnabled": False,
              "MaxModificationAgeForFirstRunInHours": "1"
            }
          }])
zztDataSourcesandCollection.job_list.append(Transfer_to_Centralized_Repo)

Data_Storage_AWS_S3 = JobFileTransfer("zzt-Data-Storage-AWS-S3", connection_profile_src="ZZM_SFTP_AGT1", connection_profile_dest="ZZM_FS_LOCAL",description="Job 5: Collect and aggregate all retrieve data into a centralized repository unising CTM MFT", file_transfers=[{
            "ABSTIME": "0",
            "VERNUM": "0",
            "Dest": "/opt/controlm/ctm/DemandForecast/",
            "ContinueOnFailure": False,
            "SRC_PATTERN": "Wildcard",
            "SRCOPT": "0",
            "DeleteFileOnDestIfFails": False,
            "TransferType": "Binary",
            "CASEIFS": "0",
            "DSTOPT": "0",
            "RECURSIVE": "0",
            "TransferOption": "SrcToDest",
            "Src": "/",
            "TIMELIMIT": "0",
            "FailJobOnDestCommandFailure": False,
            "EXCLUDE_WILDCARD": "0",
            "NULLFLDS": "0",
            "FailJobOnDestActionFailure": False,
            "TRIM": "1",
            "IF_EXIST": "0",
            "FailJobOnSourceCommandFailure": False,
            "UNIQUE": "0",
            "FileWatcherOptions": {
              "UnitsOfTimeLimit": "Minutes",
              "SkipToNextFileIfCriteriaNotMatch": False,
              "MinDetectedSizeInBytes": "0"
            },
            "SimultaneousTransfer": {
              "TransferMultipleFilesSimultaneously": False
            },
            "IncrementalTransfer": {
              "IncrementalTransferEnabled": False,
              "MaxModificationAgeForFirstRunEnabled": False,
              "MaxModificationAgeForFirstRunInHours": "1"
            }
          }])
zztDataSourcesandCollection.job_list.append(Data_Storage_AWS_S3)

#connections
workflow.chain(
    [
        Data_Market_API, Data_Oracle, Data_Storage_AWS_S3
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Sources-and-Collection'
)
workflow.chain(
    [
        Data_Weather_API, Data_Oracle, Data_Storage_AWS_S3
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Sources-and-Collection'
)
workflow.chain(
    [
        Data_SAP_inventory, Transfer_to_Centralized_Repo, Data_Storage_AWS_S3
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Sources-and-Collection'
)
workflow.chain(
    [
        Data_SFDC, Transfer_to_Centralized_Repo, Data_Storage_AWS_S3
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Sources-and-Collection'
)

# jobs in zzt-Data-Processing-and-Consumption folder 

Analyse_Data_Hadoop = JobHadoopMapReduce("zzt-Analyse-Data-Hadoop", connection_profile="CP",description="JOB 8:  Aggregate and analyse data using Hadoop", program_jar='/home/user1/hadoop-jobs/hadoop-mapreduce-examples.jar',main_class='com.mycomp.mainClassName',arguments=['arg1','arg2'])
zztDataProcessingandConsumption.job_list.append(Analyse_Data_Hadoop)

Cleansing_Transformation_Spark = JobAwsEMR("zzt-Cleansing-Transformation-Spark", connection_profile="ZZT-AWS-EMR",description="JOB 7:  Cleansing and transformation of data using Apache Spark")
zztDataProcessingandConsumption.job_list.append(Cleansing_Transformation_Spark)

Data_Insights_AWSGlue = JobAwsGlue("zzt-Data-Insights-AWS-Glue", connection_profile="ZZT-AWS-GLUe",description="JOB 9: Additional data processing using AWS Glue for refined insights")
zztDataProcessingandConsumption.job_list.append(Data_Insights_AWSGlue)

Summary_Power_BI = JobMicrosoftPowerBI("zzt-Summary-Power-BI", connection_profile="ZZT-AZURE-POWERBI",description="JOB 11:  Publish reports to BI tools like Tableau and Power BI")
zztDataProcessingandConsumption.job_list.append(Summary_Power_BI)

Summary_Reports_Tableau = JobTableau("zzt-Summary-Reports-Tableau", connection_profile="ZZT-AWS-TABLEAU" ,description="JOB 11:  Publish reports to BI tools like Tableau and Power BI",action="Refresh Datasource", datasource_name="demand_forecasting")
zztDataProcessingandConsumption.job_list.append(Summary_Reports_Tableau)

#SLA JOB
Demand_Forecasting_Process_SLA = JobSLAManagement("zzt-Demand-Forecasting-Process-SLA", service_name= "Demand Forecasting Service", job_runs_deviations_tolerance="3")
#Events
Demand_Forecasting_Process_SLA_WaitEventsList = WaitForEvents([Event(event="zztDataProcessingandConsumption_OK",date=Event.Date.OrderDate)])
Demand_Forecasting_Process_SLA.wait_for_events.append(Demand_Forecasting_Process_SLA_WaitEventsList)
Demand_Forecasting_Process_SLA_DeleteEventsList = DeleteEvents([Event(event="zztDataProcessingandConsumption_OK",date=Event.Date.OrderDate)])
Demand_Forecasting_Process_SLA.delete_events_list.append(Demand_Forecasting_Process_SLA_DeleteEventsList)


folder1.job_list.append(Demand_Forecasting_Process_SLA)

#connections
workflow.chain(
    [
        Analyse_Data_Hadoop, Summary_Power_BI
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Processing-and-Consumption'
)
workflow.chain(
    [
        Analyse_Data_Hadoop, Summary_Reports_Tableau
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Processing-and-Consumption'
)

workflow.chain(
    [
        Cleansing_Transformation_Spark, Summary_Power_BI
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Processing-and-Consumption'
)
workflow.chain(
    [
        Cleansing_Transformation_Spark, Summary_Reports_Tableau
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Processing-and-Consumption'
)

workflow.chain(
    [
        Data_Insights_AWSGlue, Summary_Power_BI
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Processing-and-Consumption'
)
workflow.chain(
    [
        Data_Insights_AWSGlue, Summary_Reports_Tableau
    ],
    inpath='zzt-demand-forecasting/zzt-Data-Processing-and-Consumption'
)

workflow.add(folder1)
 
print(workflow.dumps_json())
 
 
print(workflow.build().errors)
# print(workflow.deploy().errors)
# %%
