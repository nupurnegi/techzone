from ibm_watson_machine_learning import APIClient
import json, os
from dotenv import dotenv_values
import dotenv
from ibm_watson_machine_learning.deployment import WebService
import string
import random

config = dotenv_values("../.env") 
deployment_space_name = config["DEPLOYMENT_SPACE_NAME"]
function_name = config["FUNCTION_NAME"]
space_id = config["SPACE_ID"]
url = config["CP4DURL"]
username = config["CP4DUSER"]
password = config["CP4DPASSWORD"]

function_file_location = config["FUNCTION_FILE_LOCATION"]

wml_credentials = {
   "instance_id" : "openshift",
   "url": url,
   "version": "3.5",
   "username"    : username,
   "password"    : password,
}
client = APIClient(wml_credentials)

client.set.default_space(space_id)

asset_details_json = client.data_assets.create('training_user_inputs_and_prepped_column_names.json', file_path='/projects/customer-attrition/dataset/training_user_inputs_and_prepped_column_names.json')
asset_details_script = client.data_assets.create('attrition_prep.py', file_path='/projects/customer-attrition/notebooks/attrition_prep.py')      
asset_details_dataset = client.data_assets.create('customer_history.csv', file_path='/projects/customer-attrition/dataset/customer_history.csv')

client.data_assets.list()
i=0

client.import_assets.start(space_id=space_id,
                           file_path=function_file_location)


details = client.import_assets.get_details(space_id=space_id)
print("Waiting for import to finish...")
while details["resources"][0]["entity"]["status"]["state"] != "completed" and details["resources"][0]["entity"]["status"]["state"] != "failed":
    details = client.import_assets.get_details(space_id=space_id)

asset_details = client.repository.get_details()
# print(asset_details)

for resource in asset_details["functions"]["resources"] :
    if(resource["metadata"]["name"] == function_name):
        function_id = resource["metadata"]["id"]
        print("Deployment Space with ID " + space_id + " and name "+ deployment_space_name +" containing function " + function_name +" is created successfully.")
    else:
        print("Funtion Import Failed!!!.")

function_deployment_name = 'Customer-Attrition-Prediction-Scoring-Function-Deployment'

meta_props = {
    client.deployments.ConfigurationMetaNames.NAME: function_deployment_name,
    client.deployments.ConfigurationMetaNames.TAGS : ['attrition_scoring_pipeline_function_deployment_tag'],
    client.deployments.ConfigurationMetaNames.DESCRIPTION:"Customer Attrition Scoring Function which will take raw data for scoring, prep it into the format required for the model and score it to return attrition probability of the customer.",
    client.deployments.ConfigurationMetaNames.ONLINE: {}
}

function_deployment_details = client.deployments.create(artifact_uid=function_id, meta_props=meta_props)
scoring_deployment_id = client.deployments.get_uid(function_deployment_details)
client.deployments.get_details(scoring_deployment_id)
