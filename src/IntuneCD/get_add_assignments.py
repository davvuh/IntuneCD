"""
This module is used to get and add assignments for configurations.

Parameters get_assignments
----------
endpoint : str
    Microsoft Graph endpoint for assignments
object : dict
    The object to look for assignments on
objectID : str
    ID of the object in Intune to get assignments for
extra_endpoint : str
    Used if endpoint differs from assignment endpoint

Parameters add_assignments
----------
endpoint : str
    Microsoft Graph endpoint for assignments
object : dict
    The object to add assignments on
objectID : str
    ID of the object in Intune to add assignments on
extra_endpoint : str
    Used if endpoint differs from assignment endpoint
extra_url : str
    Used if additional content is needed in the endpoint
wap : bool
    Set to True if updating assignment for Windows Autopilot
script : bool
    Set to True if updating assignment for Device Management scripts
extra_endpoint : str
    Used if endpoint differs from assignment endpoint
"""

import json
from .graph_request import makeapirequest,makeapirequestPost

## Set MS Graph endpoint
group_endpoint = "https://graph.microsoft.com/beta/groups"

def get_assignments(endpoint,get_object,objectID,token,extra_endpoint=None):
    remove_keys = {'id','createdDateTime','version','lastModifiedDateTime','sourceId'}
    current_assignments = []
    if extra_endpoint == None:
        assignments = makeapirequest(endpoint + "/" + objectID + "/assignments", token)
    else:
        assignments = makeapirequest(extra_endpoint + "/" + objectID + "/assignments", token)
    if assignments['value']:
        for assignment in assignments['value']:
            for k in remove_keys:
                assignment.pop(k, None)
            if "groupId" in assignment['target']:
                q_param = {"$select":"displayName"}
                group_name = makeapirequest(group_endpoint + "/" + assignment['target']['groupId'],token,q_param)
                if group_name:
                    assignment['target'].pop('groupId', None)
                    assignment['target']['groupName'] = group_name['displayName']
            current_assignments.append(assignment)
            get_object['assignments'] = current_assignments
            return current_assignments

def add_assignment(endpoint,add_object,objectID,token,status_code=200,extra_url=None,wap=False,script=False,extra_endpoint=None):
    ## Add assignment if assignments key exists
    if "assignments" in add_object:
        repo_assignments = add_object['assignments']
        ## If groupName, search for group
        request_data = {}
        assign = []
        ## Check if object has assignments assigned
        if extra_endpoint == None:
            curr_assignment = get_assignments(endpoint,add_object,objectID,token)
        else:
            curr_assignment = get_assignments(endpoint,add_object,objectID,token,extra_endpoint)
        ## Get details of current assignment
        if curr_assignment:
            curr_assignment_list = [value for elem in curr_assignment
                      for value in elem['target'].values()]
            for assignment in repo_assignments:
                if "groupName" in assignment['target']:
                    if assignment['target']['groupName'] not in curr_assignment_list:
                        group_q_param = {"$filter":"displayName eq " + "'" + assignment['target']['groupName'] + "'"}
                        group_data = makeapirequest(group_endpoint,token,group_q_param)
                        if group_data['value']:
                            assignment['target'].pop('groupName')
                            assignment['target']['groupId'] = group_data['value'][0]['id']
                            assign.append(assignment)
                elif assignment['target']['@odata.type'] not in curr_assignment_list:
                    assign.append(assignment)
                ## If missing assignments, add them
                if assign:
                    print("Updating assignment for: " + objectID + " with assignment(s):")
                    print(assign, sep='\n')
                    
                    if ((extra_url == None) and (wap == False) and (script == False)):
                        request_data['assignments'] = assign
                        request_json = json.dumps(request_data)
                        makeapirequestPost(endpoint + "/" + objectID + "/assign",token,q_param=None,jdata=request_json,status_code=status_code)
                    elif wap == True:
                        for target in assign:
                            request_data['target'] = target['target']
                            request_json = json.dumps(request_data)
                            makeapirequestPost(endpoint + "/" + objectID + "/assignments",token,q_param=None,jdata=request_json,status_code=status_code)
                    elif script == True:
                            request_data['deviceManagementScriptAssignments'] = assign
                            request_json = json.dumps(request_data)
                            print(request_json)
                            makeapirequestPost(endpoint + "/" + objectID + "/assign",token,q_param=None,jdata=request_json)
                    else:
                        request_data['assignments'] = assign
                        request_json = json.dumps(request_data)
                        makeapirequestPost(endpoint + "/" + objectID + extra_url + "/assign",token,q_param=None,jdata=request_json,status_code=status_code)

        ## If current assignment is none, add assignments        
        else:
            ## Get group id for each group if key = groupName
            for assignment in add_object['assignments']:
                if "groupName" in assignment['target']:
                    group_q_param = {"$filter":"displayName eq " + "'" + assignment['target']['groupName'] + "'"}
                    group_data = makeapirequest(group_endpoint,token,group_q_param)
                    if group_data['value']:
                        assignment['target'].pop('groupName')
                        assignment['target']['groupId'] = group_data['value'][0]['id']
                        assign.append(assignment)
                ## If assignment = all devices/users add it
                else:
                    assign.append(assignment)

            if assign:
                print("No assignment found for: " + objectID + " adding assignment(s):")
                print(assign, sep='\n')

                if ((extra_url == None) and (wap == False) and (script == False)):
                    request_data['assignments'] = assign
                    request_json = json.dumps(request_data)
                    makeapirequestPost(endpoint + "/" + objectID + "/assign",token,q_param=None,jdata=request_json,status_code=status_code)
                elif wap == True:
                    for target in assign:
                        request_data['target'] = target['target']
                        request_json = json.dumps(request_data)
                        makeapirequestPost(endpoint + "/" + objectID + "/assignments",token,q_param=None,jdata=request_json,status_code=status_code)
                elif script == True:
                        request_data['deviceManagementScriptAssignments'] = assign
                        request_json = json.dumps(request_data)
                        makeapirequestPost(endpoint + "/" + objectID + "/assign",token,q_param=None,jdata=request_json)
                else:
                    request_data['assignments'] = assign
                    request_json = json.dumps(request_data)
                    makeapirequestPost(endpoint + "/" + objectID + extra_url + "/assign",token,q_param=None,jdata=request_json,status_code=status_code)
            else:
                print("Unable to update assignment, group cannot be found")