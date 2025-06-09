
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response, make_response
import json
from flask_cors import CORS

from simple_workflow import initialize_workflow
from ctm_python_client.core.workflow import JobCommand

from ctm_python_client.core.workflow import *
from ctm_python_client.core.comm import *
from ctm_python_client.core.credential import *
from aapi import *
from my_secrets import my_secrets



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

JOB_LIBRARY = {
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
    "Data_Oracle": lambda: JobDatabaseSQLScript(
        "zzt-Oracle-Data",
        connection_profile="ZZT-ORACLE-SALES",
        sql_script="export_store_sales.sql",
        output_sql_output="Y",
        description="JOB 5: Retrieve data from Oracle database"
    ),
    "Transfer_to_Centralized_Repo": lambda: JobFileTransfer(
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
    "Analyse_Data_Hadoop": lambda: JobHadoopMapReduce(
        "zzt-Analyse-Data-Hadoop",
        connection_profile="CP",
        description="JOB 8: Aggregate and analyse data using Hadoop",
        program_jar="/home/user1/hadoop-jobs/hadoop-mapreduce-examples.jar",
        main_class="com.mycomp.mainClassName",
        arguments=["arg1", "arg2"]
    ),
    "Cleansing_Transformation_Spark": lambda: JobAwsEMR(
        "zzt-Cleansing-Transformation-Spark",
        connection_profile="ZZT-AWS-EMR",
        description="JOB 7: Cleansing and transformation of data using Apache Spark"
    ),
    "Data_Insights_AWSGlue": lambda: JobAwsGlue(
        "zzt-Data-Insights-AWS-Glue",
        connection_profile="ZZT-AWS-GLUe",
        description="JOB 9: Additional data processing using AWS Glue for refined insights"
    ),
    "Summary_Power_BI": lambda: JobMicrosoftPowerBI(
        "zzt-Summary-Power-BI",
        connection_profile="ZZT-AZURE-POWERBI",
        description="JOB 11: Publish reports to Power BI"
    ),
    "Summary_Reports_Tableau": lambda: JobTableau(
        "zzt-Summary-Reports-Tableau",
        connection_profile="ZZT-AWS-TABLEAU",
        description="JOB 11: Publish reports to Tableau",
        action="Refresh Datasource",
        datasource_name="demand_forecasting"
    ),
    "Demand_Forecasting_Process_SLA": lambda: JobSLAManagement(
        "zzt-Demand-Forecasting-Process-SLA",
        service_name="Demand Forecasting Service",
        job_runs_deviations_tolerance="3"
    )
}


@app.route('/job_types', methods=['GET'])
def list_job_types():
    return jsonify(list(JOB_LIBRARY.keys()))

#Inject metadata per object
def apply_metadata(obj):
    obj.host = "zzz-linux-agents"
    obj.application = "ZZT-Version1-DG"
    obj.run_as = "ctmagent"
    obj.sub_application = "ZZT-Version1-DG"
    return obj


@app.route('/generate_workflow', methods=['POST'])
def generate_workflow():
    data = request.get_json()

    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' list in request."}), 400

    jobs_input = data['jobs']
    connect_jobs = data.get('connect', True)
    add_sla = data.get('add_sla', False)
    events = data.get('events', [])

    if not isinstance(jobs_input, list) or len(jobs_input) < 1:
        return jsonify({"error": "'jobs' must be a non-empty list."}), 400

    # Initialize workflow and folder
    workflow, folder_name, folder = initialize_workflow()

    subfolder_map = {}
    job_refs = []

    for job_def in jobs_input:
        job_name = job_def.get("name")
        subfolder_name = job_def.get("subfolder")

        if not job_name or job_name not in JOB_LIBRARY:
            return jsonify({"error": f"Unknown or missing job name: {job_name}"}), 400

        job = apply_metadata(JOB_LIBRARY[job_name]())

        if subfolder_name:
            if subfolder_name not in subfolder_map:
                sf = SubFolder(subfolder_name)
                apply_metadata(sf)
                subfolder_map[subfolder_name] = sf
                folder.sub_folder_list.append(sf)
            subfolder_map[subfolder_name].job_list.append(job)
            job_refs.append(f"{folder_name}/{subfolder_name}/{job.object_name}")
        else:
            folder.job_list.append(job)
            job_refs.append(f"{folder_name}/{job.object_name}")

    # Event logic
    for e in events:
        e_type = e.get("type")
        event_name = e.get("event")
        date = Event.Date.OrderDate

        if e_type == "add":
            job_name = e.get("job")
            for sf in subfolder_map.values():
                for job in sf.job_list:
                    if job.object_name == job_name:
                        sf.events_to_add.append(AddEvents([Event(event=event_name, date=date)]))
        elif e_type in ["wait", "delete"]:
            subfolder_name = e.get("subfolder")
            if subfolder_name in subfolder_map:
                event_obj = Event(event=event_name, date=date)
                if e_type == "wait":
                    subfolder_map[subfolder_name].wait_for_events.append(WaitForEvents([event_obj]))
                elif e_type == "delete":
                    subfolder_map[subfolder_name].delete_events_list.append(DeleteEvents([event_obj]))

    # Fix 4: Add chaining events manually
    def add_chain_events(job_a, job_b):
        event_name = f"{job_a.object_name}-TO-{job_b.object_name}"
        job_a.events_to_add.append(AddEvents([Event(event=event_name)]))
        job_b.wait_for_events.append(WaitForEvents([Event(event=event_name)]))
        job_b.delete_events_list.append(DeleteEvents([Event(event=event_name)]))

    if connect_jobs:
        for i in range(len(job_refs) - 1):
            ref_a, ref_b = job_refs[i], job_refs[i + 1]
            add_chain_events(ref_a, ref_b)

            parts_a = ref_a.split("/")
            parts_b = ref_b.split("/")

            if len(parts_a) == 3:
                _, subfolder_a, obj_a = parts_a
                job_a = next(j for j in subfolder_map[subfolder_a].job_list if j.object_name == obj_a)
            else:
                _, obj_a = parts_a
                job_a = next(j for j in folder.job_list if j.object_name == obj_a)

            if len(parts_b) == 3:
                _, subfolder_b, obj_b = parts_b
                job_b = next(j for j in subfolder_map[subfolder_b].job_list if j.object_name == obj_b)
            else:
                _, obj_b = parts_b
                job_b = next(j for j in folder.job_list if j.object_name == obj_b)

            add_chain_events(ref_a, ref_b)

    # SLA injection
    if add_sla:
        sla_job = apply_metadata(JobSLAManagement(
            "zzt-Demand-Forecasting-Process-SLA",
            service_name="Demand Forecasting Service",
            job_runs_deviations_tolerance="3"
        ))
        sla_job.wait_for_events.append(WaitForEvents([
            Event(event="zztDataProcessingandConsumption_OK", date=Event.Date.OrderDate)
        ]))
        sla_job.delete_events_list.append(DeleteEvents([
            Event(event="zztDataProcessingandConsumption_OK", date=Event.Date.OrderDate)
        ]))
        folder.job_list.append(sla_job)

     
    raw_json = workflow.dumps_json()
    print(raw_json)

    return Response(raw_json, mimetype='application/json')

    # workflow_json = json.dumps(workflow.dumps_json())
    # return jsonify(workflow_json)



if __name__ == "__main__":
    app.run(debug=True)