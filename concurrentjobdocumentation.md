# Visual Workflow Editor Documentation

## Overview

This document outlines the implementation of a visual workflow editor that allows users to create concurrent and dependent jobs through intuitive drag-and-drop interactions.

## User Interaction Flow

1. **Initial Job Selection**

   - User selects technologies from the technology list
   - Selected jobs appear as draggable cards in the workflow editor

2. **Job Placement Rules**

   - Jobs placed side by side (horizontally) = Concurrent execution
   - Jobs placed vertically = Potential dependency connection

3. **Dependency Creation**
   - When a job is placed above/below another job:
     - Visual connection line appears
     - Prompt: "Connect these jobs?" with ✔️/❌ options
     - ✔️ = Creates dependency
     - ❌ = No connection

## Frontend Data Structure

```json
{
  "workflow": {
    "name": "workflow_name",
    "jobs": [
      {
        "id": "job1",
        "name": "retrieve-sales-data",
        "type": "JobCommand",
        "position": {
          "x": 100,
          "y": 50
        },
        "dependencies": []
      },
      {
        "id": "job2",
        "name": "retrieve-inventory-data",
        "type": "JobSAPR3BatchInputSession",
        "position": {
          "x": 300,
          "y": 50
        },
        "dependencies": []
      },
      {
        "id": "job3",
        "name": "analyze-data",
        "type": "JobHadoopMapReduce",
        "position": {
          "x": 200,
          "y": 150
        },
        "dependencies": ["job1", "job2"]
      }
    ]
  }
}
```

## Backend Processing

1. **Concurrent Job Detection**

```python
def detect_concurrent_jobs(jobs):
    concurrent_groups = []
    # Group jobs with same y-coordinate
    y_coordinates = {}
    for job in jobs:
        y = job['position']['y']
        if y not in y_coordinates:
            y_coordinates[y] = []
        y_coordinates[y].append(job)

    # Create concurrent groups
    for y, jobs_at_y in y_coordinates.items():
        if len(jobs_at_y) > 1:
            concurrent_groups.append({
                'id': f'group_{y}',
                'jobs': [job['id'] for job in jobs_at_y]
            })

    return concurrent_groups
```

2. **Dependency Processing**

```python
def process_dependencies(jobs):
    for job in jobs:
        if job['dependencies']:
            # Add wait events for dependencies
            wait_events = [Event(event=f"{dep}_COMPLETE")
                         for dep in job['dependencies']]
            job['wait_for_events'] = WaitForEvents(wait_events)
```

## Example Workflow Creation

1. User drags "retrieve-sales-data" and "retrieve-inventory-data" side by side

   - These jobs are automatically marked as concurrent
   - No user prompt needed

2. User drags "analyze-data" below both jobs
   - Visual connection line appears
   - User clicks ✔️ to confirm dependency
   - "analyze-data" now waits for both jobs to complete

## Implementation Steps

1. Create draggable job cards
2. Implement position tracking
3. Add visual connection lines
4. Create dependency confirmation dialog
5. Process concurrent jobs based on x-coordinates
6. Handle dependency creation based on user confirmation
7. Generate workflow JSON for backend

## Testing Considerations

1. Test drag and drop functionality
2. Verify concurrent job detection
3. Check dependency creation
4. Validate visual feedback
5. Test undo/redo functionality
6. Verify workflow generation

## Testing in Postman

### 1. Basic Workflow Creation

**Endpoint**: `POST http://localhost:5000/deploy_personalized_workflow`

**Headers**:

```
Content-Type: application/json
```

**Request Body**:

```json
{
  "workflow": {
    "name": "data-processing-workflow",
    "jobs": [
      {
        "id": "job1",
        "name": "retrieve-sales-data",
        "type": "JobCommand",
        "position": {
          "x": 100,
          "y": 50
        },
        "dependencies": []
      },
      {
        "id": "job2",
        "name": "retrieve-inventory-data",
        "type": "JobSAPR3BatchInputSession",
        "position": {
          "x": 300,
          "y": 50
        },
        "dependencies": []
      },
      {
        "id": "job3",
        "name": "analyze-data",
        "type": "JobHadoopMapReduce",
        "position": {
          "x": 200,
          "y": 150
        },
        "dependencies": ["job1", "job2"]
      }
    ]
  },
  "environment": "saas_dev",
  "user_code": "LBA"
}
```

**Expected Response**:

```json
{
  "message": "Workflow created successfully",
  "workflow_id": "wf_123456",
  "concurrent_groups": [
    {
      "id": "group_50",
      "jobs": ["job1", "job2"]
    }
  ],
  "dependencies": [
    {
      "job": "job3",
      "depends_on": ["job1", "job2"]
    }
  ]
}
```

### 2. Complex Workflow Example

**Request Body**:

```json
{
  "jobs": [
    {
      "id": "job1",
      "name": "Data Collection",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "job2",
      "name": "SAP Inventory",
      "type": "Data_SAP_inventory",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "job3",
      "name": "Market Data",
      "type": "Data_Market_API",
      "position": {
        "x": 500,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "job4",
      "name": "Data Processing",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 300,
        "y": 300
      },
      "dependencies": ["job1", "job2", "job3"]
    },
    {
      "id": "job5",
      "name": "Data Storage",
      "type": "Data_Storage_AWS_S3",
      "position": {
        "x": 500,
        "y": 300
      },
      "dependencies": ["job4"]
    },
    {
      "id": "job6",
      "name": "Data Analysis",
      "type": "AWS_Athena",
      "position": {
        "x": 300,
        "y": 500
      },
      "dependencies": ["job5"]
    },
    {
      "id": "job7",
      "name": "Report Generation",
      "type": "MS_PowerBI",
      "position": {
        "x": 500,
        "y": 500
      },
      "dependencies": ["job6"]
    }
  ],
  "environment": "saas_dev",
  "folder_name": "DEMO_GENERATOR",
  "user_code": "LBA"
}
```

**Expected Response**:

```json
{
  "workflow": {
    "name": "LBA_DEMO_GENERATOR",
    "jobs": [
      {
        "id": "job1",
        "name": "Data Collection",
        "type": "Data_SFDC",
        "object_name": "zzt-Data Collection"
      },
      {
        "id": "job2",
        "name": "SAP Inventory",
        "type": "Data_SAP_inventory",
        "object_name": "zzt-SAP Inventory"
      },
      {
        "id": "job3",
        "name": "Market Data",
        "type": "Data_Market_API",
        "object_name": "zzt-Market Data"
      },
      {
        "id": "job4",
        "name": "Data Processing",
        "type": "JobHadoopMapReduce",
        "object_name": "zzt-Data Processing"
      },
      {
        "id": "job5",
        "name": "Data Storage",
        "type": "Data_Storage_AWS_S3",
        "object_name": "zzt-Data Storage"
      },
      {
        "id": "job6",
        "name": "Data Analysis",
        "type": "AWS_Athena",
        "object_name": "zzt-Data Analysis"
      },
      {
        "id": "job7",
        "name": "Report Generation",
        "type": "MS_PowerBI",
        "object_name": "zzt-Report Generation"
      }
    ],
    "concurrent_groups": [
      {
        "id": "group_100",
        "jobs": ["job1", "job2", "job3"]
      },
      {
        "id": "group_300",
        "jobs": ["job4", "job5"]
      },
      {
        "id": "group_500",
        "jobs": ["job6", "job7"]
      }
    ],
    "dependencies": [
      {
        "job": "job4",
        "depends_on": ["job1", "job2", "job3"]
      },
      {
        "job": "job5",
        "depends_on": ["job4"]
      },
      {
        "job": "job6",
        "depends_on": ["job5"]
      },
      {
        "job": "job7",
        "depends_on": ["job6"]
      }
    ]
  },
  "deployment": {
    "success": true,
    "message": "Workflow successfully built and deployed",
    "build_output": "...",
    "deploy_output": "..."
  },
  "raw_json": "..."
}
```

This example demonstrates:

1. Three concurrent data collection jobs (Data_SFDC, Data_SAP_inventory, Data_Market_API)
2. Parallel data processing and storage jobs (JobHadoopMapReduce, Data_Storage_AWS_S3)
3. Parallel analysis and reporting jobs (AWS_Athena, MS_PowerBI)
4. Complex dependency chain ensuring proper data flow

### 3. Error Handling Examples

**Missing Required Field**:

```json
{
  "workflow": {
    "name": "error-workflow",
    "jobs": [
      {
        "id": "job1",
        "name": "test-job",
        "type": "JobCommand",
        "position": {
          "x": 100,
          "y": 50
        }
        // Missing dependencies field
      }
    ]
  }
}
```

**Response**:

```json
{
  "error": "Missing required field: dependencies",
  "status": 400
}
```

**Invalid Job Type**:

```json
{
  "workflow": {
    "name": "error-workflow",
    "jobs": [
      {
        "id": "job1",
        "name": "test-job",
        "type": "InvalidJobType",
        "position": {
          "x": 100,
          "y": 50
        },
        "dependencies": []
      }
    ]
  }
}
```

**Response**:

```json
{
  "error": "Invalid job type: InvalidJobType",
  "status": 400
}
```

### 4. Testing Tips

1. **Start Simple**: Begin with a basic workflow (2-3 jobs) to verify the endpoint works
2. **Check Concurrent Groups**: Verify that jobs at the same y-coordinate are grouped correctly
3. **Test Dependencies**: Ensure dependencies are properly created and validated
4. **Error Cases**: Test various error scenarios to ensure proper error handling
5. **Environment**: Make sure to specify the correct environment in the request

### 5. Common Issues

1. **Position Conflicts**: Jobs with the same position might cause issues
2. **Circular Dependencies**: The system should prevent circular dependencies
3. **Invalid Job Types**: Only supported job types should be accepted
4. **Missing Fields**: All required fields must be present
5. **Environment Access**: Ensure the specified environment is accessible

## Testing generate_workflow Endpoint

### 1. Basic Concurrent Workflow

**Endpoint**: `POST http://localhost:5000/generate_workflow`

**Headers**:

```
Content-Type: application/json
```

**Request Body**:

```json
{
  "jobs": [
    {
      "id": "job1",
      "name": "retrieve-sales-data",
      "type": "JobCommand",
      "position": {
        "x": 100,
        "y": 50
      },
      "dependencies": []
    },
    {
      "id": "job2",
      "name": "retrieve-inventory-data",
      "type": "JobSAPR3BatchInputSession",
      "position": {
        "x": 300,
        "y": 50
      },
      "dependencies": []
    },
    {
      "id": "job3",
      "name": "analyze-data",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 200,
        "y": 150
      },
      "dependencies": ["job1", "job2"]
    }
  ],
  "environment": "saas_dev",
  "folder_name": "DEMGEN_VB",
  "user_code": "LBA"
}
```

**Expected Response**:

```json
{
  "workflow": {
    "name": "LBA_DEMGEN_VB",
    "jobs": [
      {
        "id": "job1",
        "name": "retrieve-sales-data",
        "type": "JobCommand",
        "object_name": "zzt-retrieve-sales-data"
      },
      {
        "id": "job2",
        "name": "retrieve-inventory-data",
        "type": "JobSAPR3BatchInputSession",
        "object_name": "zzt-retrieve-inventory-data"
      },
      {
        "id": "job3",
        "name": "analyze-data",
        "type": "JobHadoopMapReduce",
        "object_name": "zzt-analyze-data"
      }
    ],
    "concurrent_groups": [
      {
        "id": "group_50",
        "jobs": ["job1", "job2"]
      }
    ],
    "dependencies": [
      {
        "job": "job3",
        "depends_on": ["job1", "job2"]
      }
    ]
  },
  "raw_json": "...",
  "build_errors": null,
  "deploy_errors": null
}
```

### 2. Complex Workflow Example

**Request Body**:

```json
{
  "jobs": [
    {
      "id": "sfdc_job",
      "name": "Data-SFDC",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "sap_job",
      "name": "Data-SAP-inventory",
      "type": "Data_SAP_inventory",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "market_api_job",
      "name": "Market-Data-API",
      "type": "Data_Market_API",
      "position": {
        "x": 500,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "transfer_job",
      "name": "Transfer-to-Centralized-Repo",
      "type": "JobFileTransfer",
      "position": {
        "x": 300,
        "y": 300
      },
      "dependencies": ["sfdc_job", "sap_job"],
      "subfolder": "Data-Transfer"
    },
    {
      "id": "storage_job",
      "name": "Data-Storage-AWS-S3",
      "type": "Data_Storage_AWS_S3",
      "position": {
        "x": 500,
        "y": 300
      },
      "dependencies": ["market_api_job"],
      "subfolder": "Data-Transfer"
    },
    {
      "id": "hadoop_job",
      "name": "Analyse-Data-Hadoop",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 300,
        "y": 500
      },
      "dependencies": ["transfer_job", "storage_job"],
      "subfolder": "Data-Processing"
    },
    {
      "id": "spark_job",
      "name": "Cleansing-Transformation-Spark",
      "type": "AWS_EMR",
      "position": {
        "x": 500,
        "y": 500
      },
      "dependencies": ["transfer_job", "storage_job"],
      "subfolder": "Data-Processing"
    },
    {
      "id": "powerbi_job",
      "name": "Summary-Power-BI",
      "type": "MS_PowerBI",
      "position": {
        "x": 300,
        "y": 700
      },
      "dependencies": ["hadoop_job", "spark_job"],
      "subfolder": "Reporting"
    },
    {
      "id": "tableau_job",
      "name": "Summary-Reports-Tableau",
      "type": "Tableau",
      "position": {
        "x": 500,
        "y": 700
      },
      "dependencies": ["hadoop_job", "spark_job"],
      "subfolder": "Reporting"
    }
  ],
  "subfolders": [
    {
      "name": "Data-Collection",
      "description": "Data collection from various sources",
      "events": {
        "add": ["Data-Collection_OK"],
        "wait": [],
        "delete": []
      }
    },
    {
      "name": "Data-Transfer",
      "description": "Data transfer and storage operations",
      "events": {
        "add": ["Data-Transfer_OK"],
        "wait": ["Data-Collection_OK"],
        "delete": ["Data-Collection_OK"]
      }
    },
    {
      "name": "Data-Processing",
      "description": "Data processing and transformation",
      "events": {
        "add": ["Data-Processing_OK"],
        "wait": ["Data-Transfer_OK"],
        "delete": ["Data-Transfer_OK"]
      }
    },
    {
      "name": "Reporting",
      "description": "Report generation and visualization",
      "events": {
        "add": ["Reporting_OK"],
        "wait": ["Data-Processing_OK"],
        "delete": ["Data-Processing_OK"]
      }
    }
  ],
  "environment": "saas_dev",
  "folder_name": "data-pipeline",
  "user_code": "LBA"
}
```

Expected Response:

```json
{
  "workflow": {
    "name": "LBA-data-pipeline",
    "jobs": [
      {
        "id": "sfdc_job",
        "name": "Data-SFDC",
        "type": "Data_SFDC",
        "object_name": "LBA-Data-SFDC",
        "subfolder": "Data-Collection"
      },
      {
        "id": "sap_job",
        "name": "Data-SAP-inventory",
        "type": "Data_SAP_inventory",
        "object_name": "zzt-Data-SAP-inventory",
        "subfolder": "Data-Collection"
      },
      {
        "id": "market_api_job",
        "name": "Market-Data-API",
        "type": "Data_Market_API",
        "object_name": "zzt-Market-Data-API",
        "subfolder": "Data-Collection"
      },
      {
        "id": "transfer_job",
        "name": "Transfer-to-Centralized-Repo",
        "type": "JobFileTransfer",
        "object_name": "zzt-Transfer-to-Centralized-Repo",
        "subfolder": "Data-Transfer"
      },
      {
        "id": "storage_job",
        "name": "Data-Storage-AWS-S3",
        "type": "Data_Storage_AWS_S3",
        "object_name": "zzt-Data-Storage-AWS-S3",
        "subfolder": "Data-Transfer"
      },
      {
        "id": "hadoop_job",
        "name": "Analyse-Data-Hadoop",
        "type": "JobHadoopMapReduce",
        "object_name": "zzt-Analyse-Data-Hadoop",
        "subfolder": "Data-Processing"
      },
      {
        "id": "spark_job",
        "name": "Cleansing-Transformation-Spark",
        "type": "AWS_EMR",
        "object_name": "zzt-Cleansing-Transformation-Spark",
        "subfolder": "Data-Processing"
      },
      {
        "id": "powerbi_job",
        "name": "Summary-Power-BI",
        "type": "MS_PowerBI",
        "object_name": "zzt-Summary-Power-BI",
        "subfolder": "Reporting"
      },
      {
        "id": "tableau_job",
        "name": "Summary-Reports-Tableau",
        "type": "Tableau",
        "object_name": "zzt-Summary-Reports-Tableau",
        "subfolder": "Reporting"
      }
    ],
    "subfolders": [
      {
        "name": "Data-Collection",
        "description": "Data collection from various sources",
        "events": {
          "add": ["Data-Collection_OK"],
          "wait": [],
          "delete": []
        }
      },
      {
        "name": "Data-Transfer",
        "description": "Data transfer and storage operations",
        "events": {
          "add": ["Data-Transfer_OK"],
          "wait": ["Data-Collection_OK"],
          "delete": ["Data-Collection_OK"]
        }
      },
      {
        "name": "Data-Processing",
        "description": "Data processing and transformation",
        "events": {
          "add": ["Data-Processing_OK"],
          "wait": ["Data-Transfer_OK"],
          "delete": ["Data-Transfer_OK"]
        }
      },
      {
        "name": "Reporting",
        "description": "Report generation and visualization",
        "events": {
          "add": ["Reporting_OK"],
          "wait": ["Data-Processing_OK"],
          "delete": ["Data-Processing_OK"]
        }
      }
    ],
    "concurrent_groups": [
      {
        "id": "group_100",
        "jobs": ["sfdc_job", "sap_job", "market_api_job"]
      },
      {
        "id": "group_300",
        "jobs": ["transfer_job", "storage_job"]
      },
      {
        "id": "group_500",
        "jobs": ["hadoop_job", "spark_job"]
      },
      {
        "id": "group_700",
        "jobs": ["powerbi_job", "tableau_job"]
      }
    ],
    "dependencies": [
      {
        "job": "transfer_job",
        "depends_on": ["sfdc_job", "sap_job"]
      },
      {
        "job": "storage_job",
        "depends_on": ["market_api_job"]
      },
      {
        "job": "hadoop_job",
        "depends_on": ["transfer_job", "storage_job"]
      },
      {
        "job": "spark_job",
        "depends_on": ["transfer_job", "storage_job"]
      },
      {
        "job": "powerbi_job",
        "depends_on": ["hadoop_job", "spark_job"]
      },
      {
        "job": "tableau_job",
        "depends_on": ["hadoop_job", "spark_job"]
      }
    ]
  },
  "deployment": {
    "success": true,
    "message": "Workflow successfully built and deployed",
    "build_output": "...",
    "deploy_output": "..."
  },
  "raw_json": "..."
}
```

This example demonstrates:

1. **Proper Path Structure**:

   - Jobs are organized in subfolders (Data-Collection, Data-Transfer, Data-Processing, Reporting)
   - Each job has a full path that includes the folder and subfolder
   - Job names are consistently formatted with the user code prefix

2. **Subfolder Organization**:

   - Data Collection jobs run in parallel in the Data-Collection subfolder
   - Data Transfer jobs run in parallel in the Data-Transfer subfolder
   - Data Processing jobs run in parallel in the Data-Processing subfolder
   - Reporting jobs run in parallel in the Reporting subfolder

3. **Event Handling**:

   - Each subfolder has its own events (add, wait, delete)
   - Events are used to manage dependencies between subfolders
   - Event names follow a consistent pattern (subfolder_name_OK)

4. **Dependency Management**:

   - Jobs within the same subfolder can have dependencies
   - Jobs can depend on jobs in other subfolders
   - Dependencies are properly tracked using full job paths

5. **Concurrent Execution**:
   - Jobs at the same y-coordinate run in parallel
   - Concurrent groups are properly identified and managed
   - Dependencies between concurrent groups are maintained

## Future Enhancements

1. Zoom in/out functionality
2. Grid snapping
3. Job grouping
4. Workflow templates
5. Undo/redo support
6. Workflow validation
7. Performance optimization

### Demand Forecasting Workflow Example

```json
{
  "jobs": [
    {
      "id": "sfdc_job",
      "name": "Data-SFDC",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "sap_job",
      "name": "Data-SAP-inventory",
      "type": "Data_SAP_inventory",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "market_api_job",
      "name": "Market-Data-API",
      "type": "Data_Market_API",
      "position": {
        "x": 500,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "weather_api_job",
      "name": "Weather-Data-API",
      "type": "Data_Weather_API",
      "position": {
        "x": 700,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "oracle_job",
      "name": "Oracle-Data",
      "type": "JobDatabaseSQLScript",
      "position": {
        "x": 900,
        "y": 100
      },
      "dependencies": []
    },
    {
      "id": "transfer_job",
      "name": "Transfer-to-Centralized-Repo",
      "type": "JobFileTransfer",
      "position": {
        "x": 300,
        "y": 300
      },
      "dependencies": ["sfdc_job", "sap_job"]
    },
    {
      "id": "storage_job",
      "name": "Data-Storage-AWS-S3",
      "type": "Data_Storage_AWS_S3",
      "position": {
        "x": 500,
        "y": 300
      },
      "dependencies": ["market_api_job", "weather_api_job", "oracle_job"]
    },
    {
      "id": "hadoop_job",
      "name": "Analyse-Data-Hadoop",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 300,
        "y": 500
      },
      "dependencies": ["transfer_job", "storage_job"]
    },
    {
      "id": "spark_job",
      "name": "Cleansing-Transformation-Spark",
      "type": "AWS_EMR",
      "position": {
        "x": 500,
        "y": 500
      },
      "dependencies": ["transfer_job", "storage_job"]
    },
    {
      "id": "glue_job",
      "name": "Data-Insights-AWS-Glue",
      "type": "AWS_Glue",
      "position": {
        "x": 700,
        "y": 500
      },
      "dependencies": ["transfer_job", "storage_job"]
    },
    {
      "id": "powerbi_job",
      "name": "Summary-Power-BI",
      "type": "MS_PowerBI",
      "position": {
        "x": 300,
        "y": 700
      },
      "dependencies": ["hadoop_job", "spark_job", "glue_job"]
    },
    {
      "id": "tableau_job",
      "name": "Summary-Reports-Tableau",
      "type": "Tableau",
      "position": {
        "x": 500,
        "y": 700
      },
      "dependencies": ["hadoop_job", "spark_job", "glue_job"]
    },
    {
      "id": "sla_job",
      "name": "Demand-Forecasting-Process-SLA",
      "type": "JobSLAManagement",
      "position": {
        "x": 700,
        "y": 700
      },
      "dependencies": ["powerbi_job", "tableau_job"]
    }
  ],
  "environment": "saas_dev",
  "folder_name": "demand-forecasting",
  "user_code": "zzt"
}
```

This workflow represents the complete demand forecasting process with:

1. **Data Collection Layer** (y=100):

   - Salesforce CRM data
   - SAP inventory data
   - Market data API
   - Weather data API
   - Oracle database data

2. **Data Transfer Layer** (y=300):

   - Centralized repository transfer
   - AWS S3 storage

3. **Data Processing Layer** (y=500):

   - Hadoop analysis
   - Spark transformation
   - AWS Glue processing

4. **Reporting Layer** (y=700):
   - Power BI reports
   - Tableau dashboards
   - SLA monitoring

The workflow demonstrates:

- Parallel data collection from multiple sources
- Data consolidation and storage
- Parallel processing using different technologies
- Multiple reporting options
- End-to-end SLA monitoring

Expected Response:

```json
{
  "workflow": {
    "name": "zzt_demand-forecasting",
    "jobs": [
      // ... job details ...
    ],
    "concurrent_groups": [
      {
        "id": "group_100",
        "jobs": [
          "sfdc_job",
          "sap_job",
          "market_api_job",
          "weather_api_job",
          "oracle_job"
        ]
      },
      {
        "id": "group_300",
        "jobs": ["transfer_job", "storage_job"]
      },
      {
        "id": "group_500",
        "jobs": ["hadoop_job", "spark_job", "glue_job"]
      },
      {
        "id": "group_700",
        "jobs": ["powerbi_job", "tableau_job", "sla_job"]
      }
    ],
    "dependencies": [
      {
        "job": "transfer_job",
        "depends_on": ["sfdc_job", "sap_job"]
      },
      {
        "job": "storage_job",
        "depends_on": ["market_api_job", "weather_api_job", "oracle_job"]
      },
      {
        "job": "hadoop_job",
        "depends_on": ["transfer_job", "storage_job"]
      },
      {
        "job": "spark_job",
        "depends_on": ["transfer_job", "storage_job"]
      },
      {
        "job": "glue_job",
        "depends_on": ["transfer_job", "storage_job"]
      },
      {
        "job": "powerbi_job",
        "depends_on": ["hadoop_job", "spark_job", "glue_job"]
      },
      {
        "job": "tableau_job",
        "depends_on": ["hadoop_job", "spark_job", "glue_job"]
      },
      {
        "job": "sla_job",
        "depends_on": ["powerbi_job", "tableau_job"]
      }
    ]
  },
  "deployment": {
    "success": true,
    "message": "Workflow successfully built and deployed",
    "build_output": "...",
    "deploy_output": "..."
  },
  "raw_json": "..."
}
```

### Handling Subfolders in Workflows

To support subfolders in workflows, the following modifications are needed:

1. **Workflow Data Structure**:

```json
{
  "jobs": [
    {
      "id": "sfdc_job",
      "name": "Data-SFDC",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Sources-and-Collection" // Add subfolder field
    }
  ],
  "subfolders": [
    // Add subfolders array
    {
      "name": "Data-Sources-and-Collection",
      "description": "Data collection and ingestion jobs",
      "events": {
        "add": ["Data-Sources-and-Collection_OK"],
        "wait": [],
        "delete": []
      }
    },
    {
      "name": "Data-Processing-and-Consumption",
      "description": "Data processing and analysis jobs",
      "events": {
        "add": ["Data-Processing-and-Consumption_OK"],
        "wait": ["Data-Sources-and-Collection_OK"],
        "delete": ["Data-Sources-and-Collection_OK"]
      }
    }
  ],
  "environment": "saas_dev",
  "folder_name": "demand-forecasting",
  "user_code": "zzt"
}
```

2. **Backend Modifications**:

```python
# Create main folder
folder = Folder(formatted_folder_name, site_standard="Empty", controlm_server=controlm_server)
workflow.add(folder)

# Create subfolders
for subfolder_data in data['subfolders']:
    subfolder = SubFolder(f"zzt-{subfolder_data['name']}")

    # Add events
    if subfolder_data['events']['add']:
        add_events = [Event(event=event, date=Event.Date.OrderDate)
                     for event in subfolder_data['events']['add']]
        subfolder.events_to_add.append(AddEvents(add_events))

    # Add wait events
    if subfolder_data['events']['wait']:
        wait_events = [Event(event=event, date=Event.Date.OrderDate)
                      for event in subfolder_data['events']['wait']]
        subfolder.wait_for_events.append(WaitForEvents(wait_events))

    # Add delete events
    if subfolder_data['events']['delete']:
        delete_events = [Event(event=event, date=Event.Date.OrderDate)
                        for event in subfolder_data['events']['delete']]
        subfolder.delete_events_list.append(DeleteEvents(delete_events))

    folder.sub_folder_list.append(subfolder)

# Process jobs with subfolder assignment
for job_data in jobs_data:
    job = JOB_LIBRARY[job_data['type']]()
    job.object_name = f"zzt-{job_data['name']}"

    # Add job to appropriate subfolder
    if 'subfolder' in job_data:
        subfolder_path = f"{formatted_folder_name}/zzt-{job_data['subfolder']}"
        workflow.add(job, inpath=subfolder_path)
    else:
        workflow.add(job, inpath=formatted_folder_name)
```

3. **Example Subfolder Structure** (based on DemandForecastingWoj):

```json
{
  "jobs": [
    {
      "id": "sfdc_job",
      "name": "Data-SFDC",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Sources-and-Collection"
    },
    {
      "id": "sap_job",
      "name": "Data-SAP-inventory",
      "type": "Data_SAP_inventory",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Sources-and-Collection"
    },
    {
      "id": "hadoop_job",
      "name": "Analyse-Data-Hadoop",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 300,
        "y": 500
      },
      "dependencies": ["transfer_job", "storage_job"],
      "subfolder": "Data-Processing-and-Consumption"
    }
  ],
  "subfolders": [
    {
      "name": "Data-Sources-and-Collection",
      "description": "Data collection and ingestion jobs",
      "events": {
        "add": ["Data-Sources-and-Collection_OK"],
        "wait": [],
        "delete": []
      }
    },
    {
      "name": "Data-Processing-and-Consumption",
      "description": "Data processing and analysis jobs",
      "events": {
        "add": ["Data-Processing-and-Consumption_OK"],
        "wait": ["Data-Sources-and-Collection_OK"],
        "delete": ["Data-Sources-and-Collection_OK"]
      }
    }
  ],
  "environment": "saas_dev",
  "folder_name": "demand-forecasting",
  "user_code": "zzt"
}
```

4. **Subfolder Event Handling**:

- Each subfolder can have its own events:
  - `add`: Events to add when the subfolder completes
  - `wait`: Events to wait for before starting the subfolder
  - `delete`: Events to delete after subfolder completion
- Events are used to manage dependencies between subfolders
- Events follow the format: `subfolder_name_OK`

5. **Best Practices**:

- Use subfolders to organize related jobs
- Implement proper event handling between subfolders
- Keep subfolder names consistent with job naming conventions
- Use events to manage subfolder dependencies
- Document subfolder purposes and relationships

6. **Testing Considerations**:

- Verify subfolder creation
- Test event propagation between subfolders
- Validate job placement in correct subfolders
- Check subfolder dependencies
- Monitor event handling

### Complex Workflow Example with Subfolders

```json
{
  "jobs": [
    {
      "id": "data_collection_1",
      "name": "Salesforce-Data",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_collection_2",
      "name": "SAP-Inventory",
      "type": "Data_SAP_inventory",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_collection_3",
      "name": "Market-Data",
      "type": "Data_Market_API",
      "position": {
        "x": 500,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_transfer_1",
      "name": "Transfer-to-Repo",
      "type": "JobFileTransfer",
      "position": {
        "x": 100,
        "y": 300
      },
      "dependencies": ["data_collection_1", "data_collection_2"],
      "subfolder": "Data-Transfer"
    },
    {
      "id": "data_transfer_2",
      "name": "Store-in-S3",
      "type": "Data_Storage_AWS_S3",
      "position": {
        "x": 300,
        "y": 300
      },
      "dependencies": ["data_collection_3"],
      "subfolder": "Data-Transfer"
    },
    {
      "id": "data_processing_1",
      "name": "Hadoop-Processing",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 100,
        "y": 500
      },
      "dependencies": ["data_transfer_1"],
      "subfolder": "Data-Processing"
    },
    {
      "id": "data_processing_2",
      "name": "Spark-Processing",
      "type": "AWS_EMR",
      "position": {
        "x": 300,
        "y": 500
      },
      "dependencies": ["data_transfer_2"],
      "subfolder": "Data-Processing"
    },
    {
      "id": "data_processing_3",
      "name": "Glue-Processing",
      "type": "AWS_Glue",
      "position": {
        "x": 500,
        "y": 500
      },
      "dependencies": ["data_transfer_1", "data_transfer_2"],
      "subfolder": "Data-Processing"
    },
    {
      "id": "reporting_1",
      "name": "PowerBI-Report",
      "type": "MS_PowerBI",
      "position": {
        "x": 100,
        "y": 700
      },
      "dependencies": ["data_processing_1", "data_processing_3"],
      "subfolder": "Reporting"
    },
    {
      "id": "reporting_2",
      "name": "Tableau-Report",
      "type": "Tableau",
      "position": {
        "x": 300,
        "y": 700
      },
      "dependencies": ["data_processing_2", "data_processing_3"],
      "subfolder": "Reporting"
    },
    {
      "id": "monitoring",
      "name": "Process-SLA",
      "type": "JobSLAManagement",
      "position": {
        "x": 500,
        "y": 700
      },
      "dependencies": ["reporting_1", "reporting_2"],
      "subfolder": "Monitoring"
    }
  ],
  "subfolders": [
    {
      "name": "Data-Collection",
      "description": "Data collection from various sources",
      "events": {
        "add": ["Data-Collection_OK"],
        "wait": [],
        "delete": []
      }
    },
    {
      "name": "Data-Transfer",
      "description": "Data transfer and storage operations",
      "events": {
        "add": ["Data-Transfer_OK"],
        "wait": ["Data-Collection_OK"],
        "delete": ["Data-Collection_OK"]
      }
    },
    {
      "name": "Data-Processing",
      "description": "Data processing and transformation",
      "events": {
        "add": ["Data-Processing_OK"],
        "wait": ["Data-Transfer_OK"],
        "delete": ["Data-Transfer_OK"]
      }
    },
    {
      "name": "Reporting",
      "description": "Report generation and visualization",
      "events": {
        "add": ["Reporting_OK"],
        "wait": ["Data-Processing_OK"],
        "delete": ["Data-Processing_OK"]
      }
    },
    {
      "name": "Monitoring",
      "description": "Process monitoring and SLA tracking",
      "events": {
        "add": ["Monitoring_OK"],
        "wait": ["Reporting_OK"],
        "delete": ["Reporting_OK"]
      }
    }
  ],
  "environment": "saas_dev",
  "folder_name": "data-pipeline",
  "user_code": "LBA"
}
```

This workflow demonstrates:

1. **Data Collection Layer** (y=100):

   - Three concurrent data collection jobs
   - Each job collects data from different sources
   - All jobs run in parallel in the Data-Collection subfolder

2. **Data Transfer Layer** (y=300):

   - Two concurrent transfer jobs
   - First job depends on Salesforce and SAP data
   - Second job depends on Market data
   - Jobs run in the Data-Transfer subfolder

3. **Data Processing Layer** (y=500):

   - Three concurrent processing jobs
   - Hadoop job processes transferred data
   - Spark job processes S3 data
   - Glue job processes all data
   - All jobs run in the Data-Processing subfolder

4. **Reporting Layer** (y=700):

   - Two concurrent reporting jobs
   - PowerBI report depends on Hadoop and Glue processing
   - Tableau report depends on Spark and Glue processing
   - Jobs run in the Reporting subfolder

5. **Monitoring Layer** (y=700):
   - SLA monitoring job
   - Depends on both reporting jobs
   - Runs in the Monitoring subfolder

**Subfolder Dependencies**:

- Data-Transfer waits for Data-Collection_OK
- Data-Processing waits for Data-Transfer_OK
- Reporting waits for Data-Processing_OK
- Monitoring waits for Reporting_OK

**Concurrent Groups**:

- Data collection jobs (y=100)
- Data transfer jobs (y=300)
- Data processing jobs (y=500)
- Reporting jobs (y=700)

Expected Response:

```json
{
  "workflow": {
    "name": "LBA-data-pipeline",
    "jobs": [
      // ... job details with subfolder information ...
    ],
    "subfolders": [
      {
        "name": "Data-Collection",
        "description": "Data collection from various sources",
        "events": {
          "add": ["Data-Collection_OK"],
          "wait": [],
          "delete": []
        }
      }
      // ... other subfolder details ...
    ],
    "concurrent_groups": [
      {
        "id": "group_100",
        "jobs": ["data_collection_1", "data_collection_2", "data_collection_3"]
      },
      {
        "id": "group_300",
        "jobs": ["data_transfer_1", "data_transfer_2"]
      },
      {
        "id": "group_500",
        "jobs": ["data_processing_1", "data_processing_2", "data_processing_3"]
      },
      {
        "id": "group_700",
        "jobs": ["reporting_1", "reporting_2", "monitoring"]
      }
    ],
    "dependencies": [
      {
        "job": "data_transfer_1",
        "depends_on": ["data_collection_1", "data_collection_2"]
      },
      {
        "job": "data_processing_3",
        "depends_on": ["data_collection_3"]
      }
    ]
  },
  "deployment": {
    "success": true,
    "message": "Workflow successfully built and deployed",
    "build_output": "...",
    "deploy_output": "..."
  },
  "raw_json": "..."
}
```

### Example: Concurrent Jobs in Subfolders with Subfolder Connections

This example demonstrates a workflow with two subfolders, each containing concurrent jobs that are connected to a single job within their subfolder. The subfolders themselves are connected through events.

```json
{
  "jobs": [
    {
      "id": "data_collection_1",
      "name": "Collect-Sales-Data",
      "type": "Data_SFDC",
      "position": {
        "x": 100,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_collection_2",
      "name": "Collect-Inventory-Data",
      "type": "Data_SAP_inventory",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_collection_3",
      "name": "Collect-Market-Data",
      "type": "Data_Market_API",
      "position": {
        "x": 500,
        "y": 100
      },
      "dependencies": [],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_collection_consolidator",
      "name": "Consolidate-Collection-Data",
      "type": "JobFileTransfer",
      "position": {
        "x": 300,
        "y": 200
      },
      "dependencies": [
        "data_collection_1",
        "data_collection_2",
        "data_collection_3"
      ],
      "subfolder": "Data-Collection"
    },
    {
      "id": "data_processing_1",
      "name": "Process-Sales-Data",
      "type": "JobHadoopMapReduce",
      "position": {
        "x": 100,
        "y": 400
      },
      "dependencies": [],
      "subfolder": "Data-Processing"
    },
    {
      "id": "data_processing_2",
      "name": "Process-Inventory-Data",
      "type": "AWS_EMR",
      "position": {
        "x": 300,
        "y": 400
      },
      "dependencies": [],
      "subfolder": "Data-Processing"
    },
    {
      "id": "data_processing_3",
      "name": "Process-Market-Data",
      "type": "AWS_Glue",
      "position": {
        "x": 500,
        "y": 400
      },
      "dependencies": [],
      "subfolder": "Data-Processing"
    },
    {
      "id": "data_processing_consolidator",
      "name": "Consolidate-Processing-Results",
      "type": "AWS_Athena",
      "position": {
        "x": 300,
        "y": 500
      },
      "dependencies": [
        "data_processing_1",
        "data_processing_2",
        "data_processing_3"
      ],
      "subfolder": "Data-Processing"
    }
  ],
  "subfolders": [
    {
      "name": "Data-Collection",
      "description": "Data collection and consolidation",
      "events": {
        "add": ["Data-Collection_OK"],
        "wait": [],
        "delete": []
      }
    },
    {
      "name": "Data-Processing",
      "description": "Data processing and analysis",
      "events": {
        "add": ["Data-Processing_OK"],
        "wait": ["Data-Collection_OK"],
        "delete": ["Data-Collection_OK"]
      }
    }
  ],
  "environment": "saas_dev",
  "folder_name": "data-pipeline",
  "user_code": "LBA"
}
```

Expected Response:

```json
{
  "workflow": {
    "name": "LBA-data-pipeline",
    "jobs": [
      {
        "id": "data_collection_1",
        "name": "Collect-Sales-Data",
        "type": "Data_SFDC",
        "object_name": "LBA-Collect-Sales-Data",
        "subfolder": "Data-Collection"
      },
      {
        "id": "data_collection_2",
        "name": "Collect-Inventory-Data",
        "type": "Data_SAP_inventory",
        "object_name": "LBA-Collect-Inventory-Data",
        "subfolder": "Data-Collection"
      },
      {
        "id": "data_collection_3",
        "name": "Collect-Market-Data",
        "type": "Data_Market_API",
        "object_name": "LBA-Collect-Market-Data",
        "subfolder": "Data-Collection"
      },
      {
        "id": "data_collection_consolidator",
        "name": "Consolidate-Collection-Data",
        "type": "JobFileTransfer",
        "object_name": "LBA-Consolidate-Collection-Data",
        "subfolder": "Data-Collection"
      },
      {
        "id": "data_processing_1",
        "name": "Process-Sales-Data",
        "type": "JobHadoopMapReduce",
        "object_name": "LBA-Process-Sales-Data",
        "subfolder": "Data-Processing"
      },
      {
        "id": "data_processing_2",
        "name": "Process-Inventory-Data",
        "type": "AWS_EMR",
        "object_name": "LBA-Process-Inventory-Data",
        "subfolder": "Data-Processing"
      },
      {
        "id": "data_processing_3",
        "name": "Process-Market-Data",
        "type": "AWS_Glue",
        "object_name": "LBA-Process-Market-Data",
        "subfolder": "Data-Processing"
      },
      {
        "id": "data_processing_consolidator",
        "name": "Consolidate-Processing-Results",
        "type": "AWS_Athena",
        "object_name": "LBA-Consolidate-Processing-Results",
        "subfolder": "Data-Processing"
      }
    ],
    "subfolders": [
      {
        "name": "Data-Collection",
        "description": "Data collection and consolidation",
        "events": {
          "add": ["Data-Collection_OK"],
          "wait": [],
          "delete": []
        }
      },
      {
        "name": "Data-Processing",
        "description": "Data processing and analysis",
        "events": {
          "add": ["Data-Processing_OK"],
          "wait": ["Data-Collection_OK"],
          "delete": ["Data-Collection_OK"]
        }
      }
    ],
    "concurrent_groups": [
      {
        "id": "group_100",
        "jobs": ["data_collection_1", "data_collection_2", "data_collection_3"]
      },
      {
        "id": "group_400",
        "jobs": ["data_processing_1", "data_processing_2", "data_processing_3"]
      }
    ],
    "dependencies": [
      {
        "job": "data_collection_consolidator",
        "depends_on": [
          "data_collection_1",
          "data_collection_2",
          "data_collection_3"
        ]
      },
      {
        "job": "data_processing_consolidator",
        "depends_on": [
          "data_processing_1",
          "data_processing_2",
          "data_processing_3"
        ]
      }
    ]
  },
  "deployment": {
    "success": true,
    "message": "Workflow successfully built and deployed",
    "build_output": "...",
    "deploy_output": "..."
  },
  "raw_json": "..."
}
```

This example demonstrates:

1. **Data Collection Subfolder**:

   - Three concurrent jobs collecting different types of data
   - All three jobs run in parallel at y=100
   - A consolidator job that depends on all three collection jobs
   - The consolidator triggers the "Data-Collection_OK" event when complete

2. **Data Processing Subfolder**:

   - Three concurrent jobs processing different types of data
   - All three jobs run in parallel at y=400
   - A consolidator job that depends on all three processing jobs
   - The consolidator triggers the "Data-Processing_OK" event when complete

3. **Subfolder Connection**:

   - The Data-Processing subfolder waits for the "Data-Collection_OK" event
   - This ensures all data collection is complete before processing begins
   - The Data-Collection_OK event is deleted after processing starts

4. **Job Dependencies**:

   - Jobs within each subfolder are connected to their respective consolidator
   - No direct connections between jobs in different subfolders
   - Subfolder-level connection through events

5. **Concurrent Execution**:
   - Three concurrent jobs in each subfolder
   - Consolidator jobs run after their respective concurrent groups
   - Subfolders run sequentially through event-based dependencies

## Simple Functional Frontend Implementation

Here's a simple React-based frontend implementation to interact with the `generate_workflow` endpoint. This example demonstrates how to create a basic UI for workflow generation with concurrent jobs and subfolders.

### 1. Basic Component Structure

```jsx
// WorkflowGenerator.jsx
import React, { useState } from "react";
import "./WorkflowGenerator.css";

const WorkflowGenerator = () => {
  const [workflow, setWorkflow] = useState({
    jobs: [],
    subfolders: [],
    environment: "saas_dev",
    folder_name: "data-pipeline",
    user_code: "LBA",
  });

  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("http://localhost:5000/generate_workflow", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(workflow),
      });
      const data = await response.json();
      setResponse(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="workflow-generator">
      <h2>Workflow Generator</h2>
      <form onSubmit={handleSubmit}>{/* Form components will go here */}</form>
      {error && <div className="error">{error}</div>}
      {response && (
        <div className="response">
          <h3>Generated Workflow</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default WorkflowGenerator;
```

### 2. Job Management Components

```jsx
// JobForm.jsx
const JobForm = ({ onAddJob }) => {
  const [job, setJob] = useState({
    id: "",
    name: "",
    type: "",
    position: { x: 0, y: 0 },
    dependencies: [],
    subfolder: "",
    isPlaceholder: false,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    // Only add non-placeholder jobs
    if (!job.isPlaceholder) {
      onAddJob(job);
    }
    setJob({
      id: "",
      name: "",
      type: "",
      position: { x: 0, y: 0 },
      dependencies: [],
      subfolder: "",
      isPlaceholder: false,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="job-form">
      <div className="position-inputs">
        <input
          type="number"
          placeholder="X Position"
          value={job.position.x}
          onChange={(e) =>
            setJob({
              ...job,
              position: { ...job.position, x: parseInt(e.target.value) },
            })
          }
        />
        <input
          type="number"
          placeholder="Y Position"
          value={job.position.y}
          onChange={(e) =>
            setJob({
              ...job,
              position: { ...job.position, y: parseInt(e.target.value) },
            })
          }
        />
      </div>

      <div className="job-type-selection">
        <select
          value={job.type}
          onChange={(e) => {
            const selectedType = e.target.value;
            setJob({
              ...job,
              type: selectedType,
              // Auto-generate name based on type and position
              name: selectedType
                ? `${selectedType}_${job.position.x}_${job.position.y}`
                : "",
              isPlaceholder: !selectedType,
            });
          }}
        >
          <option value="">Select Technology</option>
          <option value="AWS">AWS</option>
          <option value="Azure">Azure</option>
          <option value="GCP">GCP</option>
          <option value="SAP">SAP</option>
          <option value="Oracle">Oracle</option>
          <option value="Salesforce">Salesforce</option>
          {/* Add more technology options */}
        </select>
      </div>

      <div className="subfolder-selection">
        <select
          value={job.subfolder}
          onChange={(e) => setJob({ ...job, subfolder: e.target.value })}
        >
          <option value="">Select Subfolder</option>
          {/* Subfolders will be populated dynamically */}
        </select>
      </div>

      <button type="submit">Add Job</button>
    </form>
  );
};
```

### 3. Subfolder Management

```jsx
// SubfolderForm.jsx
const SubfolderForm = ({ onAddSubfolder }) => {
  const [subfolder, setSubfolder] = useState({
    name: "",
    description: "",
    events: {
      add: [],
      wait: [],
      delete: [],
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (subfolder.name) {
      onAddSubfolder(subfolder);
      setSubfolder({
        name: "",
        description: "",
        events: {
          add: [],
          wait: [],
          delete: [],
        },
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="subfolder-form">
      <input
        type="text"
        placeholder="Subfolder Name"
        value={subfolder.name}
        onChange={(e) => setSubfolder({ ...subfolder, name: e.target.value })}
      />
      <input
        type="text"
        placeholder="Description"
        value={subfolder.description}
        onChange={(e) =>
          setSubfolder({ ...subfolder, description: e.target.value })
        }
      />
      <button type="submit">Add Subfolder</button>
    </form>
  );
};
```

### 4. Main Workflow Generator Component

```jsx
// WorkflowGenerator.jsx (continued)
const WorkflowGenerator = () => {
  // ... previous state declarations ...

  const handleAddJob = (newJob) => {
    setWorkflow((prev) => ({
      ...prev,
      jobs: [...prev.jobs, newJob],
    }));
  };

  const handleAddSubfolder = (newSubfolder) => {
    setWorkflow((prev) => ({
      ...prev,
      subfolders: [...prev.subfolders, newSubfolder],
    }));
  };

  return (
    <div className="workflow-generator">
      <h2>Workflow Generator</h2>

      <div className="workflow-sections">
        <section className="jobs-section">
          <h3>Jobs</h3>
          <JobForm onAddJob={handleAddJob} />
          <div className="jobs-list">
            {workflow.jobs.map((job) => (
              <div key={job.id} className="job-item">
                <span>{job.name}</span>
                <span>{job.type}</span>
                <span>{job.subfolder}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="subfolders-section">
          <h3>Subfolders</h3>
          <SubfolderForm onAddSubfolder={handleAddSubfolder} />
          <div className="subfolders-list">
            {workflow.subfolders.map((subfolder) => (
              <div key={subfolder.name} className="subfolder-item">
                <span>{subfolder.name}</span>
                <span>{subfolder.description}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <form onSubmit={handleSubmit} className="workflow-form">
        <div className="form-group">
          <label>Environment:</label>
          <select
            value={workflow.environment}
            onChange={(e) =>
              setWorkflow((prev) => ({ ...prev, environment: e.target.value }))
            }
          >
            <option value="saas_dev">SaaS Dev</option>
            <option value="saas_preprod">SaaS Preprod</option>
            <option value="saas_prod">SaaS Prod</option>
          </select>
        </div>

        <div className="form-group">
          <label>Folder Name:</label>
          <input
            type="text"
            value={workflow.folder_name}
            onChange={(e) =>
              setWorkflow((prev) => ({ ...prev, folder_name: e.target.value }))
            }
          />
        </div>

        <div className="form-group">
          <label>User Code:</label>
          <input
            type="text"
            value={workflow.user_code}
            onChange={(e) =>
              setWorkflow((prev) => ({ ...prev, user_code: e.target.value }))
            }
          />
        </div>

        <button type="submit">Generate Workflow</button>
      </form>

      {error && <div className="error">{error}</div>}
      {response && (
        <div className="response">
          <h3>Generated Workflow</h3>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

### 5. Basic Styling

```css
/* WorkflowGenerator.css */
.workflow-generator {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.workflow-sections {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.job-form,
.subfolder-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.jobs-list,
.subfolders-list {
  border: 1px solid #ccc;
  padding: 10px;
  min-height: 200px;
}

.job-item,
.subfolder-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.workflow-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-width: 400px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.error {
  color: red;
  padding: 10px;
  border: 1px solid red;
  margin-top: 20px;
}

.response {
  margin-top: 20px;
  padding: 10px;
  border: 1px solid #ccc;
}

.response pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
```

### 6. Usage Example

```jsx
// App.jsx
import React from "react";
import WorkflowGenerator from "./WorkflowGenerator";

function App() {
  return (
    <div className="app">
      <header>
        <h1>Workflow Generator</h1>
      </header>
      <main>
        <WorkflowGenerator />
      </main>
    </div>
  );
}

export default App;
```

This frontend implementation provides:

1. **Job Management:**

   - Add jobs with properties (ID, name, type, position, subfolder)
   - View list of added jobs
   - Select job types from predefined options

2. **Subfolder Management:**

   - Create subfolders with names and descriptions
   - Configure subfolder events
   - View list of created subfolders

3. **Workflow Configuration:**

   - Set environment, folder name, and user code
   - Generate workflow with all configured components
   - View response or error messages

4. **Visual Feedback:**
   - Clear display of added jobs and subfolders
   - Error handling and display
   - Formatted JSON response display

To use this frontend:

1. Install dependencies:

```bash
npm install react react-dom
```

2. Set up the project structure:

```
src/
  components/
    WorkflowGenerator.jsx
    JobForm.jsx
    SubfolderForm.jsx
  styles/
    WorkflowGenerator.css
  App.jsx
```

3. Start the development server:

```bash
npm start
```

This provides a simple but functional interface for generating workflows with concurrent jobs and subfolders. You can enhance it by adding:

1. Drag-and-drop job positioning
2. Visual workflow diagram
3. Job dependency visualization
4. More sophisticated error handling
5. Job template management
6. Workflow validation
7. Save/load workflow configurations

### 7. Implementation Challenges and Solutions

When implementing this frontend with the existing backend, you may encounter several challenges:

1. **Job Type Selection**
   **Issues:**

   - Need to handle dynamic job types based on selected technology
   - Placeholder positions need to be managed
   - Job names should be auto-generated based on type and position

   **Solution:**

   ```javascript
   // Technology to job type mapping
   const TECHNOLOGY_JOBS = {
     AWS: ["AWS_AppFlow", "AWS_Batch", "AWS_DataPipeline"],
     Azure: ["AZURE_HDInsight", "AZURE_Batch", "AZURE_DataFactory"],
     GCP: ["GCP_Dataflow", "GCP_Dataproc", "GCP_Functions"],
     // Add more mappings
   };

   // Enhanced job form with technology selection
   const handleTechnologyChange = (technology) => {
     const availableJobs = TECHNOLOGY_JOBS[technology] || [];
     setJob((prev) => ({
       ...prev,
       type: "",
       availableJobs,
       isPlaceholder: !technology,
     }));
   };
   ```

2. **Position Management**
   **Issues:**

   - Need to maintain grid layout
   - Handle empty positions
   - Ensure proper job alignment

   **Solution:**

   ```javascript
   // Grid management
   const GRID_SIZE = { x: 10, y: 10 };
   const POSITION_STEP = 100; // pixels

   const calculatePosition = (x, y) => ({
     x: x * POSITION_STEP,
     y: y * POSITION_STEP,
   });

   // Validate position
   const isValidPosition = (x, y) => {
     return x >= 0 && x < GRID_SIZE.x && y >= 0 && y < GRID_SIZE.y;
   };
   ```

3. **Subfolder Management**
   **Issues:**

   - Dynamic subfolder creation
   - Job assignment to subfolders
   - Event handling between subfolders

   **Solution:**

   ```javascript
   // Subfolder management
   const handleSubfolderCreation = (name, description) => {
     const subfolder = {
       name,
       description,
       events: {
         add: [`${name}_OK`],
         wait: [],
         delete: [],
       },
     };
     return subfolder;
   };
   ```

These solutions focus on the core functionality needed for the workflow generator, without unnecessary complexity for production environments or user feedback systems.
