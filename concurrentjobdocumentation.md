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

### 3. Error Handling Examples

**Invalid Job Type**:

```json
{
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
  ],
  "environment": "saas_dev",
  "folder_name": "DEMGEN_VB",
  "user_code": "LBA"
}
```

**Response**:

```json
{
  "error": "Unknown job type: InvalidJobType",
  "status": 400
}
```

**Missing Required Fields**:

```json
{
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
  ],
  "environment": "saas_dev",
  "folder_name": "DEMGEN_VB",
  "user_code": "LBA"
}
```

**Response**:

```json
{
  "error": "Missing required field: dependencies",
  "status": 400
}
```

### 4. Testing Tips

1. **Job Types**: Ensure you're using valid job types from the JOB_LIBRARY
2. **Positioning**:
   - Jobs at the same y-coordinate will be concurrent
   - Jobs at different y-coordinates can have dependencies
3. **Dependencies**:
   - Dependencies must reference valid job IDs
   - Avoid circular dependencies
4. **Environment**:
   - Use valid environment values (saas_dev, saas_preprod, etc.)
   - Ensure environment credentials are configured

### 5. Common Issues

1. **Position Conflicts**:
   - Jobs with the same position might cause issues
   - Use different x-coordinates for concurrent jobs
2. **Invalid Dependencies**:
   - Dependencies must reference existing job IDs
   - Check for typos in job IDs
3. **Environment Access**:
   - Verify environment credentials
   - Check environment availability
4. **Job Type Support**:
   - Only use supported job types
   - Check JOB_LIBRARY for available types

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
