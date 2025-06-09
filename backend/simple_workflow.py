# simple_workflow.py

from ctm_python_client.core.workflow import *
from ctm_python_client.core.comm import *
from ctm_python_client.core.credential import *
from aapi import *
from my_secrets import my_secrets
from ctm_python_client.ext.viz import get_graph

def initialize_workflow():
    my_env = Environment.create_saas(
        endpoint=my_secrets['helix_sandbox_endpoint'],
        api_key=my_secrets['helix_sandbox_api_key']
    )

    defaults = WorkflowDefaults(
        run_as="ctmagent",
        host="zzz-linux-agents",
        application="LBA-DMO-GEN",
        sub_application="LBA-DMO-GEN"
    )

    workflow = Workflow(my_env, defaults=defaults)

    folder_name = "LBA_DEMGEN_VB"
    folder = Folder(folder_name, site_standard="Empty", controlm_server="IN01")
    workflow.add(folder)

    return workflow, folder_name, folder
