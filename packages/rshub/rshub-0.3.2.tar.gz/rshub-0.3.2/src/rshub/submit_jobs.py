import requests
import json
import time
import os
from .check_authenticity import return_task_path

def run(data):
    # Step 1: Run models
    url = 'https://rshub.zju.edu.cn/models'
    headers = {'Content-Type': 'application/json'}
    # Convert the data to a JSON string
    json_data = json.dumps(data)
    print(json_data)
    try:
        response = requests.post(url, data=json_data, headers=headers)

        if response.status_code == 200:
            return(response.json())
        else:
            return(f"Request failed with status code {response.status_code}")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return {'error':{http_err}}
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return {'error':{conn_err}}
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return {'error':{timeout_err}}
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
        return {'error':{req_err}}

def check_completion(token, project_name, task_name):
    tmp = return_task_path(token,project_name,task_name)
    # task_path=result['path']
    # task_status=result['task_status']
    # complete_flag=result['result']
    result={}
    result['task_status']=tmp['task_status']
    result['project_name']=project_name
    result['task_name']=task_name

    # print(f"status':{task_status}")
    # print(f"task_path':{task_path}")
    # print(f"complete_flag':{complete_flag}")
    return(result) 
    # if complete_flag:
    #     return {'Jobs are completed'}
    # else:
        
    # try:
    #     if not isinstance(task_path,dict):
    #         url = 'https://rshub.zju.edu.cn/check_state'
    #         headers = {'Content-Type': 'application/json'}
    #         data = {'task_path':task_path}
    #         json_data = json.dumps(data)
    #         response = requests.post(url, data=json_data, headers=headers)
    #         return(response.json())
    #     return task_path['error']
    # except requests.exceptions.HTTPError as http_err:
    #     print(f"HTTP error occurred: {http_err}")
    #     return {'error':{http_err}}
    # except requests.exceptions.ConnectionError as conn_err:
    #     print(f"Connection error occurred: {conn_err}")
    #     return {'error':{conn_err}}
    # except requests.exceptions.Timeout as timeout_err:
    #     print(f"Timeout error occurred: {timeout_err}")
    #     return {'error':{timeout_err}}
    # except requests.exceptions.RequestException as req_err:
    #     print(f"An error occurred: {req_err}")
    #     return {'error':{req_err}}