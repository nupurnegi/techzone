import pandas as pd
import datetime
from ibm_watson_machine_learning import APIClient
import json, os
from dotenv import dotenv_values
import dotenv
import string
import random

config = dotenv_values("../.env") 
apikey=config["API_KEY"]
loc = config["PM-20_LOC"]
space_id = config["SPACE_ID"]
deployment_id = config["DEPLOYMENT_ID"]

wml_credentials = {
    "apikey": apikey,
    "url": "https://"+loc+".ml.cloud.ibm.com",
    }
client = APIClient(wml_credentials)

client.set.default_space(space_id)

# we will use the prep script for getting the raw data into the format required for scoring
# we also need the prep metadata that was saved as json during the prep for training - this ensures that the user inputs specified for prepping the data for training are the same used for scoring
# we need to add these files into the deployment space


asset_details_json = client.data_assets.create('training_user_inputs_and_prepped_column_names.json', file_path='/projects/customer-attrition/training_user_inputs_and_prepped_column_names.json')
asset_details_script = client.data_assets.create('attrition_prep.py', file_path='/projects/customer-attrition/attrition_prep.py')      
asset_details_dataset = client.data_assets.create('customer_history.csv', file_path='/projects/customer-attrition/customer_history.csv')

client.data_assets.list()

# get the assets that were stored in the space - in this version of the package we need to manually assign the id
metadata_id = asset_details_json['metadata']['guid']
prep_id = asset_details_script['metadata']['guid']
dataset_id = asset_details_dataset['metadata']['guid']

assets_dict = {'dataset_asset_id' : dataset_id, 'metadata_asset_id' : metadata_id, 'prep_script_asset_id' : prep_id, 'dataset_name' : 'customer_history.csv'}

# wml_credentials["instance_id"] = "openshift"  (Model deployment failed credentials error)

ai_parms = {'wml_credentials' : wml_credentials,'space_id' : space_id, 'assets' : assets_dict, 'model_deployment_id' : deployment_id}

# Scoring Pipeline Function
# The function below takes new customers to be scored as a payload. 
# It preps the customer raw data, loads the model, executes the model scoring and generates the predictions for attrition. 
def scoring_pipeline(parms=ai_parms):
    
    import pandas as pd
    import requests
    import os
    import json
    
    from ibm_watson_machine_learning import APIClient

    client = APIClient(parms['wml_credentials'])
    client.set.default_space(parms['space_id'])
     
    
    # call the function to download the stored dataset asset and return the path
    dataset_path = client.data_assets.download(parms['assets']['dataset_asset_id'], parms['assets']['dataset_name'])
    df_raw = pd.read_csv(dataset_path, infer_datetime_format=True, 
                             parse_dates=['CUSTOMER_RELATIONSHIP_START_DATE', 
                                              'CUSTOMER_SUMMARY_END_DATE','CUSTOMER_SUMMARY_START_DATE'])

    # call the function to download the prep script and return the path
    prep_script_path = client.data_assets.download(parms['assets']['prep_script_asset_id'], 'prep_data_script.py')
    # remove the rest of path and .py at end of file name to get the name of the script for importing
    script_name = os.path.basename(prep_script_path).replace('.py', '')
    
    # call the function to download the prep metadata and return the path
    metadata_path = client.data_assets.download(parms['assets']['metadata_asset_id'], 'user_inputs.json')
    
    def prep(cust_id, sc_end_date):
        
        import requests
        import os
        # import the prep script that we downloaded into the deployment space
        prep_data_script = __import__(script_name)
        
        with open(metadata_path, 'r') as f:
            user_inputs_dict = json.load(f)
        
        globals().update(user_inputs_dict)
                  
        input_df = df_raw[df_raw[granularity_key] == cust_id]
        
        scoring_prep = prep_data_script.AttritionPrep('score', effective_date=sc_end_date, feature_attributes=feature_attributes,
                             derive_column_list=derive_column_list,
                             granularity_key=granularity_key, target_attribute=target_attribute,
                             status_attribute=status_attribute,
                             funds_attribute=funds_attribute, date_customer_joined=date_customer_joined,
                             customer_end_date=customer_end_date, customer_start_date=customer_start_date,
                             period_attribute=period_attribute, status_flag_attrition=status_flag_attrition,
                             AUM_reduction_threshold=AUM_reduction_threshold,
                             forecast_horizon=forecast_horizon, observation_window=observation_window,
                             sum_list=sum_list, cat_threshold=cat_threshold)
        
        prepped_data = scoring_prep.prep_data(input_df, 'score')
        
        if prepped_data is None:
            print("Data prep filtered out customer data. Unable to score.", file=sys.stderr)
            return None
    
        # handle empty data
        if prepped_data.shape[0] == 0:
            print("Data prep filtered out customer data. Unable to score.", file=sys.stderr)
            return None

        to_drop_corr = ['CUSTOMER_SUMMARY_FUNDS_UNDER_MANAGEMENT_mean', 'CUSTOMER_SUMMARY_FUNDS_UNDER_MANAGEMENT_min',
                            'CUSTOMER_SUMMARY_FUNDS_UNDER_MANAGEMENT_max', 'CUSTOMER_SUMMARY_TOTAL_AMOUNT_OF_DEPOSITS_min',
                            'CUSTOMER_SUMMARY_TOTAL_AMOUNT_OF_DEPOSITS_max', 'CUSTOMER_SUMMARY_TOTAL_AMOUNT_OF_DEPOSITS_sum',
                            'CUSTOMER_ANNUAL_INCOME', 'CUSTOMER_NUMBER_OF_DEPENDENT_CHILDREN',
                            'NUM_ACCOUNTS_WITH_RISK_TOLERANCE_MODERATE', 'NUM_ACCOUNTS_WITH_RISK_TOLERANCE_HIGH',
                            'NUM_ACCOUNTS_WITH_RISK_TOLERANCE_VERY_LOW', 'NUM_ACCOUNTS_WITH_RISK_TOLERANCE_LOW', 
                            'CUSTOMER_TENURE', 'NUM_ACCOUNTS_WITH_INVESTMENT_OBJECTIVE_PLANNING',
                            'NUM_ACCOUNTS_WITH_INVESTMENT_OBJECTIVE_SECURITY','CUSTOMER_SUMMARY_TOTAL_AMOUNT_OF_DEPOSITS_max_min_ratio',
                            'CUSTOMER_SUMMARY_TOTAL_AMOUNT_OF_DEPOSITS_current_vs_6_months_ago']
        
        # don't need to include target variable for scoring
        cols_used_for_training.remove(target_attribute)

        # if a column does not exist in scoring but is in training, add the column to scoring dataset
        for col in cols_used_for_training:
            if col not in list(prepped_data.columns):
                prepped_data[col] = 0

        # if a column exists in scoring but not in training, delete it from scoring dataset
        for col in list(prepped_data.columns):
            if col not in cols_used_for_training:
                prepped_data.drop(col, axis=1, inplace=True)

        # make sure order of scoring columns is same as training dataset
        prepped_data = prepped_data[cols_used_for_training]
        
        prepped_data = prepped_data.drop(to_drop_corr, axis=1)
        
        return prepped_data
        
    def score(payload):
        
        import json
        try:
            sc_end_date = payload['input_data'][0]['values'][0][1]
        except:
            sc_end_date="2018-09-30"
            
        cust_id = payload['input_data'][0]['values'][0][0]
        
        prepped_data = prep(cust_id, sc_end_date)
        
        if prepped_data is None:
            return {"predictions" : [{'values' : 'Data prep filtered out customer data. Unable to score.'}]}
        else:

            scoring_payload = {"input_data":  [{ "values" : prepped_data.values.tolist()}]}
            
            response_scoring = client.deployments.score(parms['model_deployment_id'], scoring_payload)
            result=  response_scoring
            print(result['predictions'][0]['values'][0][1][1])
            result["Probability_of_Attrition"]=str(round(result['predictions'][0]['values'][0][1][1]*100,2))+"%"
            return {"predictions" : [{'values' : result}]}

    return score


# store the function and deploy it 
function_name = 'Customer Attrition Prediction Scoring Function'
function_deployment_name = 'Customer-Attrition-Prediction-Scoring-Function-Deployment'

software_spec_id = client.software_specifications.get_id_by_name("runtime-22.1-py3.9")


# add the metadata for the function and deployment    
meta_data = {
    client.repository.FunctionMetaNames.NAME : function_name,
    client.repository.FunctionMetaNames.TAGS : ['attrition_scoring_pipeline_function_tag'],
    client.repository.FunctionMetaNames.INPUT_DATA_SCHEMAS:[{'id': '1','type': 'struct','fields': [{'name': 'CUSTOMER ID', 'type': 'int'},{'name': 'sc_end_date', 'type': 'date'}]}],
    client.repository.FunctionMetaNames.OUTPUT_DATA_SCHEMAS: [{'id': '1','type': 'struct','fields': [{'name': 'Probability_of_Attrition','type': 'double'}]}],
    client.repository.FunctionMetaNames.SOFTWARE_SPEC_UID: software_spec_id,
    client.repository.FunctionMetaNames.TYPE: "python"
}

function_details = client.repository.store_function(meta_props=meta_data, function=scoring_pipeline)

function_id = function_details["metadata"]["id"]

meta_props = {
    client.deployments.ConfigurationMetaNames.NAME: function_deployment_name,
    client.deployments.ConfigurationMetaNames.TAGS : ['attrition_scoring_pipeline_function_deployment_tag'],
    client.deployments.ConfigurationMetaNames.DESCRIPTION:"Customer Attrition Scoring Function which will take raw data for scoring, prep it into the format required for the model and score it to return attrition probability of the customer.",
    client.deployments.ConfigurationMetaNames.ONLINE: {}
}

# deploy the function
function_deployment_details = client.deployments.create(artifact_uid=function_id, meta_props=meta_props)
scoring_deployment_id = client.deployments.get_uid(function_deployment_details)
client.deployments.get_details(scoring_deployment_id)