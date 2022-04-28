from ibm_watson_machine_learning import APIClient
from dotenv import dotenv_values
import os

config = dotenv_values("../.env") 
apikey=config["API_KEY"]
loc = config["PM-20_LOC"]
space_id = config["SPACE_ID"]

token=os.system("curl -X POST 'https://iam.cloud.ibm.com/oidc/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey="+apikey+"| grep -o '\"access_token\":\"[^\"]*' | grep -o '[^\"]*$'")

wml_credentials = {
   "token": token,
   "instance_id" : "openshift",
   "url": "https://"+loc+".ml.cloud.ibm.com",
   "version": "3.5"
}

client = APIClient(wml_credentials)
client.set.default_space(space_id)

r_shiny_deployment_name='Customer-Attrition-Prediction-Shiny-App'

meta_props = {
    client.shiny.ConfigurationMetaNames.NAME: "Customer Attrition Prediction Shiny Assets",
    client.shiny.ConfigurationMetaNames.DESCRIPTION: 'Store shiny assets in deployment space' # optional
}
app_details = client.shiny.store(meta_props, '/projects/customer-attrition/customer-attrition-prediction-analytics-dashboard.zip')

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


print(wml_credentials["url"]+"/ml/v4/deployments/"+rshiny_deployment['metadata']['id'] + '/r_shiny')

