
def azure_data_factory():
    return {
        "Type": "Job:Azure Data Factory",
        "ConnectionProfile": "BSJAZUREADF",
        "Resource Group Name": "wza",
        "Data Factory Name": "datafactorynamegoeshere",
        "Pipeline Name": "pipelinename1",
        "Parameters": "{\"param1\":\"value1\"}",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "BSJAZUREADF",
        "Application": "WZA",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToWaitFor": {
            "Type": "WaitForEvents",
            "Events": [{"Event": "Transfer_files_to_Azure-TO-Process_customer_data"}]
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Process_customer_data-TO-Reports_on_customers"}]
        },
        "eventsToDelete": {
            "Type": "DeleteEvents",
            "Events": [{"Event": "Transfer_files_to_Azure-TO-Process_customer_data"}]
        }
    }


def database():
    return {
        "Type": "Job:Database:EmbeddedQuery",
        "Query": "select * from customers;",
        "ConnectionProfile": "WZA_PGSQL",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-gcp-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "WZA_PGSQL",
        "Application": "WZA",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_data_from_Customers_Database-TO-Transfer_files_to_Azure"}]
        }
    }


def file_transfer():
    return {
      "Type" : "Job:FileTransfer",
      "ConnectionProfileSrc" : "ZZM_AZURE",
      "ConnectionProfileDest" : "wza_local_ux",
      "AzureContainerNameSrc" : "zzm-cloud-credit",
      "SubApplication" : "DEMOGEN",
      "Host" : "zzz-aws-windows-2.bmcdemo.com",
      "CreatedBy" : "wzaremba",
      "RunAs" : "ZZM_AZURE+wza_local_ux",
      "Application" : "WZA",
      "Variables" : [ {
        "FTP-LOSTYPE" : "Unix"
      }, {
        "FTP-CONNTYPE1" : "Azure"
      }, {
        "FTP-ROSTYPE" : "Unix"
      }, {
        "FTP-CONNTYPE2" : "File System"
      }, {
        "FTP-RHOST" : "<Agent Host>"
      }, {
        "FTP-RUSER" : "controlm"
      }, {
        "FTP-CM_VER" : "9.0.00"
      }, {
        "FTP-COMPRESSION11" : "0"
      }, {
        "FTP-COMPRESSION21" : "0"
      }, {
        "FTP-OVERRIDE_WATCH_INTERVAL1" : "0"
      }, {
        "FTP-POSTCMD_ON_FAILURE1" : "0"
      }, {
        "FTP-SYNC_DIR_NO_DEL1" : "0"
      } ],
      "FileTransfers" : [ {
        "TransferType" : "Binary",
        "TransferOption" : "DestToSrc",
        "Src" : "/export",
        "Dest" : "/export/all_files.*",
        "ABSTIME" : "0",
        "TIMELIMIT" : "0",
        "UNIQUE" : "0",
        "SRCOPT" : "0",
        "IF_EXIST" : "0",
        "DSTOPT" : "0",
        "ContinueOnFailure" : False,
        "DeleteFileOnDestIfFails" : False,
        "FailJobOnDestActionFailure" : False,
        "FailJobOnSourceCommandFailure" : False,
        "FailJobOnDestCommandFailure" : False,
        "RECURSIVE" : "0",
        "EXCLUDE_WILDCARD" : "0",
        "TRIM" : "1",
        "NULLFLDS" : "0",
        "VERNUM" : "0",
        "CASEIFS" : "0",
        "FileWatcherOptions" : {
          "MinDetectedSizeInBytes" : "0",
          "UnitsOfTimeLimit" : "Minutes",
          "SkipToNextFileIfCriteriaNotMatch" : False
        },
        "IncrementalTransfer" : {
          "IncrementalTransferEnabled" : False,
          "MaxModificationAgeForFirstRunEnabled" : False,
          "MaxModificationAgeForFirstRunInHours" : "0"
        },
        "SimultaneousTransfer" : {
          "TransferMultipleFilesSimultaneously" : False
        }
      } ],
      "When" : {
        "WeekDays" : [ "NONE" ],
        "MonthDays" : [ "ALL" ],
        "DaysRelation" : "OR"
      },
      "eventsToWaitFor" : {
        "Type" : "WaitForEvents",
        "Events" : [ {
          "Event" : "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"
        }, {
          "Event" : "Export_data_from_Customers_Database-TO-Transfer_files_to_Azure"
        } ]
      },
      "eventsToAdd" : {
        "Type" : "AddEvents",
        "Events" : [ {
          "Event" : "Transfer_files_to_Azure-TO-Process_customer_data"
        } ]
      },
      "eventsToDelete" : {
        "Type" : "DeleteEvents",
        "Events" : [ {
          "Event" : "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"
        }, {
          "Event" : "Export_data_from_Customers_Database-TO-Transfer_files_to_Azure"
        } ]
      }
    }

def power_bi():
    return {
        "Type": "Job:Microsoft Power BI",
        "ConnectionProfile": "POWERBI",
        "Dataset Refresh/ Pipeline Deployment": "Dataset Refresh",
        "Workspace Name": "Customers",
        "Workspace ID": "1234557890",
        "Dataset ID": "9887654321",
        "Parameters": "{}",
        "SubApplication": "DEMOGEN",
        "CreatedBy": "wzaremba",
        "RunAs": "POWERBI",
        "Application": "WZA",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToWaitFor": {
            "Type": "WaitForEvents",
            "Events": [{"Event": "Process_customer_data-TO-Reports_on_customers"}]
        },
        "eventsToDelete": {
            "Type": "DeleteEvents",
            "Events": [{"Event": "Process_customer_data-TO-Reports_on_customers"}]
        }
    }


def command():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }


def SAP_R3():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def SAP_S4_HANA():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Oracle_E_Business_Suite():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Oracle_PeopleSoft():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def IBM_DB2():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Oracle_Database():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Microsoft_SQL_Server():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def PostgreSQL():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Sybase_SAP_ASE():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Java_JDBC_Compliant_DB():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def MySQL():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }
def Teradata():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def SAP_HANA():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def MongoDB():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def FTP_FTPS():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def SFTP():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def AS2():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Amazon_S3():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def S3_Comp_Storage():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Azure_Blob_Storage():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }
def Azure_Data_Lake_Storage_Gen2():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Google_Cloud_Storage():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def OCI_Object_Storage():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def AWS_Data_Pipeline():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def AWS_Glue():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def AWS_Glue_DataBrew():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Azure_Data_Factory():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Microsoft_SSIS():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Informatica_Cloud_Services():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Informatica_PowerCenter():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def SAP_Business_Warehouse():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }
def Talend_Data_Management():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Boomi_Atmosphere():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def IBM_DataStage():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Amazon_EMR():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Amazon_Athena():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Azure_HDInsight():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Azure_Synapse():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Azure_Databricks():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Google_Dataproc():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Google_Dataflow():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Google_BigQuery():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def CommandLine():
    return {
        "Type": "Job:Command",
        "SubApplication": "DEMOGEN",
        "Host": "zzz-aws-linux-1.bmcdemo.com",
        "CreatedBy": "wzaremba",
        "RunAs": "controlmsand",
        "Application": "WZA",
        "Command": "/opt/app_location/bin/run_export.sh",
        "When": {
            "WeekDays": ["NONE"],
            "MonthDays": ["ALL"],
            "DaysRelation": "OR"
        },
        "eventsToAdd": {
            "Type": "AddEvents",
            "Events": [{"Event": "Export_customer_data_from_marketing_application-TO-Transfer_files_to_Azure"}]
        }
    }

def Snowflake():
    return CommandLine()

def Databricks():
    return CommandLine()

def dbt():
    return CommandLine()

def Apache_Hadoop():
    return CommandLine()

def Apache_Spark():
    return CommandLine()

def Amazon_QuickSight():
    return CommandLine()

def Microsoft_Power_BI():
    return CommandLine()

def Qlik_Cloud():
    return CommandLine()

def Tableau():
    return CommandLine()

def IBM_Cognos():
    return CommandLine()

def Amazon_SageMaker():
    return CommandLine()

def Azure_Machine_Learning():
    return CommandLine()

def Automation_Anywhere():
    return CommandLine()

def UiPath():
    return CommandLine()

def AWS_Step_Functions():
    return CommandLine()

def Azure_LogicApps():
    return CommandLine()

def Apache_Airflow():
    return CommandLine()

def Google_Cloud_Composer():
    return CommandLine()

def Google_Workflows():
    return CommandLine()

def AWS_Lambda():
    return CommandLine()

def AWS_Batch():
    return CommandLine()

def Amazon_EC2():
    return CommandLine()

def Azure_Functions():
    return CommandLine()

def Azure_Batch():
    return CommandLine()

def Google_VM():
    return CommandLine()

def Google_Batch():
    return CommandLine()

def Kubernetes():
    return CommandLine()

def OpenShift():
    return CommandLine()

def Azure_AKS():
    return CommandLine()

def Amazon_EKS():
    return CommandLine()

def AWS_CloudFormation():
    return CommandLine()

def Azure_Resource_Manager():
    return CommandLine()

def GCP_Deployment_Manager():
    return CommandLine()

def Communication_Suite():
    return CommandLine()

def VMware():
    return CommandLine()

def Web_Services_SOAP():
    return CommandLine()

def Web_Services_REST():
    return CommandLine()

def SAP_Data_Archiving():
    return CommandLine()
