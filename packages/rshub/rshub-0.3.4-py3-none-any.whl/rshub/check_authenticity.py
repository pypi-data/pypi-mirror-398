import json 
import requests   
def return_task_path(token,project_name,task_name):
    check_url = 'https://rshub.zju.edu.cn/request_download'
    headers = {'Content-Type': 'application/json'}
    params={'token':token,
            'project_name':project_name,
            'task_name':task_name}
    # print(params)
    json_data = json.dumps(params)
    try:
        response = requests.post(check_url,data=json_data,headers=headers)
        # print(response.text)
        result = response.json()
        return result
    
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