from ibm_watson_machine_learning import APIClient
import json, os
from dotenv import dotenv_values
import dotenv
from ibm_watson_machine_learning.deployment import WebService
import string
import random
  

# deployment_space_name = ''.join(random.choices(string.ascii_uppercase +
#                              string.digits, k = 15))
# f = open("../key_file", "r")
# obj=json.loads(f.read())
# apikey=obj["apikey"]

# #add the apikey to .env file
# dotenv.set_key("../.env","API_KEY",apikey)

# dotenv.set_key("../.env","DEPLOYMENT_SPACE_NAME",deployment_space_name)

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
        dotenv.set_key("../.env","FUNCTION_ID",resource["metadata"]["id"])
        print("Deployment Space with ID " + space_id + " and name "+ deployment_space_name +" containing function " + function_name + " is created successfully.")
    else:
        print("Funtion Import Failed!!!.")

function_deployment_name = 'Customer-Attrition-Prediction-Scoring-Function-Deployment'

meta_props = {
    client.deployments.ConfigurationMetaNames.NAME: function_deployment_name,
    client.deployments.ConfigurationMetaNames.TAGS : ['attrition_scoring_pipeline_function_deployment_tag'],
    client.deployments.ConfigurationMetaNames.DESCRIPTION:"Customer Attrition Scoring Function which will take raw data for scoring, prep it into the format required for the model and score it to return attrition probability of the customer.",
    client.deployments.ConfigurationMetaNames.ONLINE: {}
}
function_id = config["FUNCTION_ID"]
# deploy the function
function_deployment_details = client.deployments.create(artifact_uid=function_id, meta_props=meta_props)
scoring_deployment_id = client.deployments.get_uid(function_deployment_details)
client.deployments.get_details(scoring_deployment_id)