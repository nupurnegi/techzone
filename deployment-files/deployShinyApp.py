from ibm_watson_machine_learning import APIClient
from dotenv import dotenv_values
import os

config = dotenv_values("../.env") 
space_id = config["SPACE_ID"]
url = config["CP4DURL"]
username = config["CP4DUSER"]
password = config["CP4DPASSWORD"]

wml_credentials = {
   "instance_id" : "openshift",
   "url": url,
   "version": "3.5",
   "username"    : username,
   "password"    : password,
}

client = APIClient(wml_credentials)
client.set.default_space(space_id)

r_shiny_deployment_name='Customer-Attrition-Prediction-Shiny-App'

meta_props = {
    client.shiny.ConfigurationMetaNames.NAME: "Customer Attrition Prediction Shiny Assets",
    client.shiny.ConfigurationMetaNames.DESCRIPTION: 'Store shiny assets in deployment space' # optional
}
app_details = client.shiny.store(meta_props, '/projects/customer-attrition/zipFolders/customer-attrition-prediction-analytics-dashboard-fixed.zip')

# Deployment metadata.
deployment_meta_props = {
    client.deployments.ConfigurationMetaNames.NAME: r_shiny_deployment_name,
    client.deployments.ConfigurationMetaNames.DESCRIPTION: 'Deploy Customer Attrition Prediction dashboard',
    client.deployments.ConfigurationMetaNames.R_SHINY: { 'authentication': 'anyone_with_url' },
    client.deployments.ConfigurationMetaNames.HARDWARE_SPEC: { 'name': 'S', 'num_nodes': 1}
}

# Create the deployment.
app_uid = client.shiny.get_uid(app_details)
rshiny_deployment = client.deployments.create(app_uid, deployment_meta_props)


print("\n###################################Your R Shiny Dashboard URL###################################\n")
print(wml_credentials["url"]+"/ml/v4/deployments/"+rshiny_deployment['metadata']['id'] + '/r_shiny')
print("\n#################################################################################################\n")
