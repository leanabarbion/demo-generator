#Web Service

def Web_Service_SOAP():
    return {
  "RFASOAP": {
    "Type": "ConnectionProfile:Web Services SOAP",
    "Description": "",
    "Centralized": True,
    "WebServiceAuthenticationBasic": {
      "UsePreemptiveAuth": False,
      "User": "maria.naime",
      "Password": "*****"
    }
  }
}


def Web_Service_REST():
    return {
  "DCO_REST_TEST": {
    "Type": "ConnectionProfile:Web Services REST",
    "Description": "",
    "Centralized": True,
    "WebServiceAuthenticationBasic": {
      "UsePreemptiveAuth": True,
      "User": "BMCDEMO",
      "Password": "*****"
    }
  }
}
 
#SAP

def SAP_R3():
    return {
  "LFI_SAPBWQA": {
    "Type": "ConnectionProfile:SAP",
    "User": "scdemo",
    "Password": "*****",
    "SapClient": "001",
    "Description": "",
    "Centralized": True,
    "ApplicationServerLogon": {
      "SystemNumber": "00",
      "Host": "clm-aus015769"
    }
  }
}
 
 
#Azure

def Azure_blob_storage():
    return {
  "ODD_BLOB_CP": {
    "Type": "ConnectionProfile:FileTransfer:Azure:SharedKey",
    "AzureAccountName": "automateddemos",
    "VerifyDestination": True,
    "AzureAccountAccessKey": "*****",
    "Description": "",
    "Centralized": True
  }
}


def Azure_vm():
    return {
  "OLA_AZURE_VM": {
    "Type": "ConnectionProfile:Azure VM",
    "Tenant ID": "92b796c5-5839-40a6-8dd9-c1fad320c69b",
    "Authentication Method": "PRINCIPAL",
    "Azure Login url": "https://login.microsoftonline.com",
    "Connection timeout": "20",
    "Resource Group": "OLA_RG",
    "Subscription ID": "31681904-0560-470e-a176-edea4d195b22",
    "Client Secret": "*****",
    "Application ID": "e51d5b03-2709-4643-8b8e-9332d9ef96bd",
    "Description": "",
    "Centralized": True
  }
}
 

def Azure_databricks():
    return {
  "ADB_STANDARD_CP": {
    "Type": "ConnectionProfile:Azure Databricks",
    "Tenant ID": "92b796c5-5839-40a6-8dd9-c1fad320c69b",
    "Azure Login url": "https://login.microsoftonline.com",
    "Databricks url": "https://adb-5209843808612711.11.azuredatabricks.net",
    "Connection Timeout": "50",
    "Databricks Resource": "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d",
    "Client Secret": "*****",
    "Application ID": "77142206-7a9e-4c1d-b8e5-31042bcdd38d",
    "Authentication Method": "PRINCIPAL",
    "Description": "",
    "Centralized": True
  }
}
 

def Azure_datafactory():
    return {
  "ADF_STANDARD_CP": {
    "Type": "ConnectionProfile:Azure Data Factory",
    "Tenant ID": "92b796c5-5839-40a6-8dd9-c1fad320c69b",
    "Management url": "management.azure.com",
    "REST Login url": "login.microsoftonline.com",
    "Connection Timeout": "50",
    "Identity Type": "PRINCIPAL",
    "Client Secret": "*****",
    "Subscription ID": "31681904-0560-470e-a176-edea4d195b22",
    "Application ID": "77142206-7a9e-4c1d-b8e5-31042bcdd38d",
    "Description": "",
    "Centralized": True
  }
}


def Azure_devops():
    return {
  "BJA-AZURE-DEV-OPS": {
    "Type": "ConnectionProfile:Azure DevOps",
    "Azure Devops Token": "*****",
    "Azure DevOps URL": "https://dev.azure.com",
    "Organization ID": "bjanjuha",
    "Azure Username": "bjanjuha",
    "Connection Timeout": "60",
    "Description": "Bhups DevOps on Azure",
    "Centralized": True
  }
}
 

#File Transfer

def MFT_S3():
    return {
  "ZZZ_MFT_S3": {
    "Type": "ConnectionProfile:FileTransfer:S3:Amazon",
    "SecretAccessKey": "*****",
    "VerifyDestination": True,
    "Region": "us-west-2",
    "AccessKey": "AKIAVVZZ2EN65EWVECA3",
    "Description": "remote s3 file access to \"us-west-2\"",
    "Centralized": True
  }
}



#Database
def Database_postgre():
    return {
  "MPE_PGSQL": {
    "Type": "ConnectionProfile:Database:PostgreSQL",
    "User": "testUser",
    "DatabaseName": "postgres",
    "Host": "aa871ae6dac4b4f0faf04f73b5e97446-1534552128.us-west-2.elb.amazonaws.com",
    "DatabaseVersion": "Any",
    "Password": "*****",
    "Description": "",
    "Centralized": True
  }
}
 

def Database_azure_sql():
    return {
  "MHP_AZURESQL": {
    "Type": "ConnectionProfile:Database:MSSQL",
    "UseJDBC": True,
    "User": "hashadmin",
    "Port": "1433",
    "DatabaseName": "sqldatabase",
    "Host": "mhpsqlserver.database.windows.net",
    "Password": "*****",
    "DatabaseVersion": "2022",
    "Description": "",
    "Centralized": True
  }
}

#AWS


def AWS_SQS():
    return {
  "FMO-AWS-SQS": {
    "Type": "ConnectionProfile:AWS SQS",
    "Connection Timeout": "30",
    "AWS Region": "ap-southeast-2",
    "AWS Secret": "*****",
    "AWS Access Key": "AKIAVVZZ2EN64N4CCYXR",
    "Authentication Method": "Secret",
    "AWS SQS URL": "https://sqs.ap-southeast-2.amazonaws.com",
    "Description": "",
    "Centralized": True
  }
}
 

def AWS_Quicksight():
    return {
  "STUDENT_QUICKSIGHT": {
    "Type": "ConnectionProfile:AWS QuickSight",
    "Connection Timeout": "30",
    "AWS Region": "us-east-1",
    "AWS Secret": "*****",
    "AWS Access Key": "AKIAVVZZ2EN65EWVECA3",
    "AWS Account ID": "390426403709",
    "Authentication Method": "Secret",
    "AWS QuickSight URL": "https://quicksight.us-east-1.amazonaws.com",
    "Description": "",
    "Centralized": True
  }
}
 

def AWS_EC2():
    return {
  "ZZZ_AWS_EC2": {
    "Type": "ConnectionProfile:AWS EC2",
    "AWS Access key ID": "AKIAVVZZ2EN65WDTFHMC",
    "Authentication": "SECRET",
    "AWS Secret": "*****",
    "EC2 Region": "us-east-2",
    "Connection timeout": "20",
    "Description": "us-east-2",
    "Centralized": True
  }
}


def AWS_athena():
    return {
  "STUDENT_ATHENA": {
    "Type": "ConnectionProfile:AWS Athena",
    "AWS Secret Key": "*****",
    "Authentication": "SECRET",
    "AWS Region": "us-east-1",
    "AWS Access Key": "AKIAVVZZ2EN65EWVECA3",
    "Connection Timeout": "20",
    "AWS Base URL": "https://athena.us-east-1.amazonaws.com",
    "Description": "",
    "Centralized": True
  }
}


def AWS_S3():
    return {
  "ZZZ_AWS_EU": {
    "Type": "ConnectionProfile:AWS",
    "SecretAccessKey": "*****",
    "Region": "eu-central-1",
    "AccessKey": "AKIAVVZZ2EN6UHXZ2DZD",
    "Description": "eu-central-1",
    "Centralized": True
  }
}



def AWS_Glue():
    return {
  "AWS-GLUE-BENCH": {
    "Type": "ConnectionProfile:AWS Glue",
    "AWS Access key ID": "AKIAZCKNG7JUBMFTC7NC",
    "AWS Secret": "*****",
    "Authentication": "SECRET",
    "AWS Region": "us-west-2",
    "Glue url": "glue.us-west-2.amazonaws.com",
    "Connection Timeout": "40",
    "Description": "",
    "Centralized": True
  }
}

#Others

def Communication_suite():
    return {
  "MHA_COMMSUITE": {
    "Type": "ConnectionProfile:Communication Suite",
    "Connection Timeout": "30",
    "Telegram URL": "https://api.telegram.org/bot",
    "WhatsApp URL": "https://graph.facebook.com/{{Version}}/{{PhoneNumberId}}/messages",
    "Slack Webhook URL": "https://hooks.slack.com/services/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",
    "Version": "v15.0",
    "Description": "MHA_COMMSUITE",
    "Centralized": True
  }
}
 

def DBT():
    return {
  "DAV_DBT_TEST_DEMO": {
    "Type": "ConnectionProfile:DBT",
    "Account ID": "243868",
    "DBT Token": "*****",
    "DBT URL": "https://cloud.getdbt.com",
    "Connection Timeout": "60",
    "Description": "",
    "Centralized": True
  }
}



def Informatica():
    return {
  "ZZZ_INFORMATICA": {
    "Type": "ConnectionProfile:Informatica",
    "Repository": "BMC_Dev_10_4",
    "User": "Administrator",
    "ConnectionType": "HTTP",
    "PowerCenterDomain": "Domain_ControlM_10_4",
    "Port": "7333",
    "Host": "vw-tlv-ctm-dvp5.adprod.bmc.com",
    "IntegrationService": "IntBmc",
    "SecurityDomain": "Native",
    "MaxConcurrentConnections": "100",
    "Password": "*****",
    "Description": "",
    "Centralized": True
  }
}
 


def Dataflow():
    return {
  "DAV_DATAFLOW_GCP": {
    "Type": "ConnectionProfile:GCP Dataflow",
    "Identity Type": "service_account",
    "DataFlow URL": "https://dataflow.googleapis.com",
    "Service Account Key": "*****",
    "Description": "",
    "Centralized": True
  }
}
 

def BigQuery():
    return

def Airflow():
    return {
  "DAV_AIRFLOW": {
    "Type": "ConnectionProfile:Airflow:GoogleComposer2",
    "BaseURL": "https://2b384a483d4049428b2415fff40484ca-dot-us-central1.composer.googleusercontent.com",
    "ServiceAccountKey": "*****",
    "ServiceAccountKeyFilename": "sso-gcp-presale-dba-pub-c20570-fbf9c944cd91.json",
    "Description": "",
    "Centralized": True
  }
}


def K8s():
    return {
  "BJA-K8-AWS-CP": {
    "Type": "ConnectionProfile:Kubernetes",
    "Service Token File": "/var/run/secrets/kubernetes.io/serviceaccount/token",
    "Connection Timeout": "50",
    "Kubernetes Cluster URL": "https://kubernetes.default.svc",
    "Namespace": "bsj",
    "Description": "",
    "Centralized": True
  }
}
 



def Snowflake():
    return {"BHUPS_SNOWFLAKE_CP": {
    "Type": "ConnectionProfile:Snowflake",
    "Refresh Token": "ver:1-hint:149984559395054-ETMsDgAAAZUds04NABRBRVMvQ0JDL1BLQ1M1UGFkZGluZwEAABAAEChwl3Q2Xn1QT2NfOGvqFAUAAABgdKLV7BwibPv4b69xOK+Agcb/LHjChYU4ntNTLWtKbLo11dGIJ2mguOYXrYk52zKtDMbabccIE9834LMXZpfZwqIuP/uXnpfrIDiyIoYuBRMCqn471KTBw1tAMSTcaKBTABRJn84RgxrcAABJY5jDcw56fuc2xQ==",
    "Client ID": "eYFkx+WJdvUpSFi/YBYaeOLyJAg=",
    "Account Identifier": "bmcpartner",
    "Client Secret": "*****",
    "Redirect URL": "https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fbrowser-callback",
    "Description": "https://bmcpartner.snowflakecomputing.com/oauth/authorize?client_id=6yufEbjYGicssJK7kj9%2FaafeQtk%3D&response_type=code&redirect_uri=https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fbrowser-callback\\\n",
    "Centralized": True
  }}

def Snowflake_IDP_wout_region():
    return  { "BHUPS_SNF_V2_CP": {
    "Type": "ConnectionProfile:Snowflake v2",
    "Refresh Token": "ver%3A2-hint%3A149984553963762-did%3A1003-ETMsDgAAAZU4QwyFABRBRVMvQ0JDL1BLQ1M1UGFkZGluZwEAABAAEKDvI%2FkxohZ4M2usMREhEWoAAAEA1rY2sc1sa5Ujw1PEiBqXvkmxrudyWXElGx0SeKGlV2F3%2Fzod46wK3HrNfsSBGtSTT6D%2BJ5m%2FDb1Pr%2BBsVVOAdH50giQJM5uI4kC4gqJs6vF5ESxoJeUROJX4QRNo8qogL5egS5HUTYyPxCzCTBLKPKKxduliWaFfZgUFm8yjzar10bsn%2FcYWqYWMImKUB1ec%2Fv4TkYy2LqgcEHdtsWYR%2BaCn6A%2BRnZrq49Rub9SnKxEOztWK4SvkHPxiCANXcLytkcfOvpWy%2BiGaoUzI386zG8c%2FvjR0ci0ipKS2MrpovHpEz0WyArYzhF4%2FUPqi06XbYbaTUgmF8Q7EuoGRRvnn6wAUkKr8lVI%2BwcvRpS1b1bDKGHqx%2Blk%3D",
    "Client ID": "eYFkx+WJdvUpSFi/YBYaeOLyJAg=",
    "Account Identifier": "bmcpartner",
    "Client Secret": "*****",
    "Redirect URL": "https%3A%2F%2Foauth.pstmn.io%2Fv1%2Fbrowser-callback",
    "Description": "Bhups Snowflake Driver - minus region",
    "Centralized": True
  }}

def Default_Connection_Profile():
    return {
        "noconnectionprofile": {
            "Type": "ConnectionProfile:Generic",
            "Description": "Fallback profile",
            "Centralized": True
        }
    }
