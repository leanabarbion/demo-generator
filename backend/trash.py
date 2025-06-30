
# @app.route('/generate_workflow', methods=['POST'])
def generate_workflow():
    data = request.get_json()
    
    if not data or 'jobs' not in data:
        return jsonify({"error": "Missing 'jobs' in request."}), 400

    jobs_data = data['jobs']
    subfolders_data = data.get('subfolders', [])
    environment = data.get('environment', 'saas_dev')
    folder_name = data.get('folder_name', 'LBA_demo-genai')
    user_code = data.get('user_code', 'LBA')

    # Validate environment
    valid_environments = ['saas_dev', 'saas_preprod', 'saas_prod', 'vse_dev', 'vse_qa', 'vse_prod']
    if environment not in valid_environments:
        return jsonify({"error": f"Invalid environment. Must be one of: {valid_environments}"}), 400

    # Set Control-M server based on environment
    if environment.startswith('saas'):
        controlm_server = "IN01"
    elif environment == 'vse_dev':
        controlm_server = "DEV"
    elif environment == 'vse_qa':
        controlm_server = "QA"
    elif environment == 'vse_prod':
        controlm_server = "PROD"
    else:
        return jsonify({"error": "Invalid environment configuration"}), 400

    # Format folder and application names with user code
    formatted_folder_name = sanitize_name(folder_name, user_code)
    formatted_application = f"{user_code}-demo-genai"
    formatted_sub_application = f"{user_code}-demo-genai"

    try:
        # Create environment connection
        app.logger.info(f"🔧 Creating environment connection for {environment}")
        my_env = Environment.create_saas(
            endpoint=my_secrets[f'{environment}_endpoint'],
            api_key=my_secrets[f'{environment}_api_key']
        )

        # Create workflow defaults
        defaults = WorkflowDefaults(
            run_as="ctmagent",
            host="zzz-linux-agents",
            application=formatted_application,
            sub_application=formatted_sub_application
        )

        # Create workflow
        app.logger.info("🔨 Creating workflow object")
        workflow = Workflow(my_env, defaults=defaults)
        
        # Create main folder
        folder = Folder(formatted_folder_name, site_standard="lba_DemoGen AI", controlm_server=controlm_server)
        workflow.add(folder)

        # Create subfolders
        subfolder_map = {}
        for subfolder_data in subfolders_data:
            subfolder_name = sanitize_name(subfolder_data['name'], user_code)
            subfolder = SubFolder(subfolder_name)
            
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
            subfolder_map[subfolder_data['name']] = subfolder

        # Group jobs by concurrent groups within subfolders
        concurrent_groups = {}
        for job_data in jobs_data:
            subfolder_name = job_data.get('subfolder', '')
            concurrent_group = job_data.get('concurrent_group', 'default')
            
            if subfolder_name not in concurrent_groups:
                concurrent_groups[subfolder_name] = {}
            if concurrent_group not in concurrent_groups[subfolder_name]:
                concurrent_groups[subfolder_name][concurrent_group] = []
            
            concurrent_groups[subfolder_name][concurrent_group].append(job_data['id'])

        # Process jobs and create dependencies
        job_instances = {}
        job_paths = {}  # Store full paths for each job

        for job_data in jobs_data:
            job_id = job_data['id']
            job_type = job_data['type']
            
            if job_type not in JOB_LIBRARY:
                return jsonify({"error": f"Unknown job type: {job_type}"}), 400

            # Create job instance
            job = JOB_LIBRARY[job_type]()
            job.object_name = sanitize_name(job_data['name'], user_code)
            
            # Add job to appropriate subfolder or main folder
            if 'subfolder' in job_data and job_data['subfolder'] in subfolder_map:
                subfolder_name = sanitize_name(job_data['subfolder'], user_code)
                subfolder_path = f"{formatted_folder_name}/{subfolder_name}"
                workflow.add(job, inpath=subfolder_path)
                job_paths[job_id] = f"{subfolder_path}/{job.object_name}"
            else:
                workflow.add(job, inpath=formatted_folder_name)
                job_paths[job_id] = f"{formatted_folder_name}/{job.object_name}"
                
            job_instances[job_id] = job

        # Add completion events for concurrent groups
        for subfolder_name, groups in concurrent_groups.items():
            for group_name, job_ids in groups.items():
                if len(job_ids) > 1:  # Only create events for actual concurrent groups
                    completion_event = f"{subfolder_name}_{group_name}_COMPLETE"
                    for job_id in job_ids:
                        if job_id in job_instances:
                            job_instances[job_id].events_to_add.append(AddEvents([Event(event=completion_event)]))

        # Create logical dependencies between subfolders using events
        # This is handled through the subfolder events (wait/add/delete) defined in the AI response

        # Generate JSON
        raw_json = workflow.dumps_json()

        # Save JSON to output.json
        output_file = "output.json"
        with open(output_file, "w") as f:
            f.write(raw_json)

        # Build the workflow using Python client
        app.logger.info("🔨 Building workflow")
        build_result = workflow.build()
        if build_result.errors:
            app.logger.error(f"❌ Build errors: {build_result.errors}")
            deployment_status = {
                "success": False,
                "message": "Workflow build failed",
                "errors": build_result.errors
            }
        else:
            # Deploy the workflow using Python client
            app.logger.info("🚀 Deploying workflow")
            deploy_result = workflow.deploy()
            if deploy_result.errors:
                app.logger.error(f"❌ Deploy errors: {deploy_result.errors}")
                deployment_status = {
                    "success": False,
                    "message": "Workflow deployment failed",
                    "errors": deploy_result.errors
                }
            else:
                deployment_status = {
                    "success": True,
                    "message": "Workflow successfully built and deployed",
                    "build_result": str(build_result),
                    "deploy_result": str(deploy_result)
                }

        # Prepare response
        response = {
            "workflow": {
                "name": formatted_folder_name,
                "jobs": [
                    {
                        "id": job_id,
                        "name": job_data['name'],
                        "type": job_data['type'],
                        "object_name": job_instances[job_id].object_name,
                        "subfolder": job_data.get('subfolder', None)
                    }
                    for job_id, job_data in zip(job_instances.keys(), jobs_data)
                ],
                "folder_name": "industry-specific-job-name",
                        "subfolders": [
                    {
                        "name": subfolder_data['name'],
                        "description": subfolder_data.get('description', ''),
                        "events": subfolder_data['events']
                    }
                    for subfolder_data in subfolders_data
                ],
                "concurrent_groups": concurrent_groups,
            },
            "deployment": deployment_status,
            "raw_json": raw_json
        }

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"❌ Error during workflow generation: {str(e)}")
        return jsonify({
            "error": "Workflow generation failed",
            "details": str(e)
        }), 500