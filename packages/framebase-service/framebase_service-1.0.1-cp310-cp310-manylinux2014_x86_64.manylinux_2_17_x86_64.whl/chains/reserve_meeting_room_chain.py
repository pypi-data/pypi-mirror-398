# cython: annotation_typing = False
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableBinding,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    chain as chain_decorator,
)
from community.models.stroutput_parser import ekcStrOutputParser
from langchain.schema.messages import HumanMessage, AIMessage
from datetime import datetime
import copy
import requests

from framebase.models import models
from framebase import config_maps
from framebase.values import RunnableValue
from framebase.notices import RunnableNotice
from framebase.output_parsers import astreaming_parser
from framebase.prompts import chain as prompt, mappings as prompt_mappings
from framebase.retrievers import mappings as VS_POINT_DATA_TYPE
from utils.dbs import redis_hget,get_redis_data,redis_key_exists,hset_redis_data
from utils import exceptions
from utils.logger import logger
from utils.langfuse_tools import langfuse_handler
from utils.langfuse_tools import langfuse_handler,get_langfuse_handler,get_langfuse_trace
from utils.tools import add_time_stamp_start
from .protocol import ReserveMeetingRoomChainInputModel,ReserveMeetingRoomChainOutputModel
from .conversation_chain import reformat_config, chain as conversation_chain


propNames = ["want_subscribe","meeting_start_time", "meeting_end_time", "building", "topic", "send_notify", "attendees"]
propNamesChsMap = {
    "want_subscribe":'是否继续预订会议室',
    "meeting_start_time":'会议开始时间',
    "meeting_end_time":'会议结束时间',
    "building":'办公楼名',
    "topic":'会议主题',
    "send_notify":'是否发送日程通知',
    "attendees":'参会人信息'
}

def get_customItems_field(x, field_name):
    default_user_info = { #hardcoded test user data
        "user_name": "化小易支持",
        "user_email": "v-devsupport@sinochem.com",
        "user_deptmentId": "hrmsubcompany125661",
        "user_token": "1cf72cdf-3fba-4b32-acca-878bb28794ec",
        "user_cityName": "beijing",
        "user_building": ["kaichen"]
    }
    if (x.get('custom_items') is not None) and (x.get('custom_items').get(field_name) is not None):
        return x.get('custom_items').get(field_name)
    return default_user_info[field_name]

inputs = {
    'app_id': lambda x: x.get('app_id'),
    "question": lambda x: x["question"],
    'history': lambda x: x['history'],
    'tags': lambda x: x['tags'],
    'org': lambda x: x['org'],
    'session_id': lambda x: x.get('session_id'),
    'client_id': lambda x: x.get('client_id'),
    'user_name': lambda x: get_customItems_field(x, 'user_name'),
    'user_email': lambda x: get_customItems_field(x, 'user_email'),
    'user_deptmentId': lambda x: get_customItems_field(x, 'user_deptmentId'),
    'user_token': lambda x:  get_customItems_field(x, 'user_token'),
    'user_cityName': lambda x: get_customItems_field(x, 'user_cityName'),
    'user_building': lambda x: get_customItems_field(x, 'user_building'),
}

redis_data=RunnablePassthrough.assign(app_key=lambda x:f"app:{x['app_id']}") | \
    RunnablePassthrough.assign(**{
        'config':lambda x:redis_hget(x['app_key'],'config')
})

def format_chat_history(x):
    history = x["history"]
    question = x["question"]
    chat_history_list = []
    for msg in history:
        if msg.role == "human":
            chat_history_list.append(f"用户：{msg.content}")
        elif msg.role == "ai":
            chat_history_list.append(f"助手：{msg.content}")
        else:
            pass
    chat_history_list.append(f"用户：{question}")
    chat_history = "\n".join(chat_history_list)
    return chat_history

@chain_decorator
def model_binding(x,config):
    # chain_config is from redis
    chain_config=x['configurable']
    # config['configurable'] if from chain's input
    # input > redis, so update chain config by input config
    # if there is lack of any config key, chain will choose them by default
    chain_config.update(config['configurable'])

    return  RunnableBinding(bound=prompt,config={'configurable':chain_config}) | \
                RunnableBinding(bound=models['output_llm'],config={'configurable':chain_config})

def get_session_states(session_id):
    name = "session_states:"+session_id
    smap = {}
    if not redis_key_exists(name):
        hset_redis_data(name, "meeting_start_time", "",  ttl=3600)
        hset_redis_data(name, "meeting_end_time", "",  ttl=3600)
        hset_redis_data(name, "building", "",  ttl=3600)
        hset_redis_data(name, "topic", "",  ttl=3600)
        hset_redis_data(name, "send_notify", "",  ttl=3600)
        hset_redis_data(name, "attendees", [],  ttl=3600)
        hset_redis_data(name, "clarifying_fields", [],  ttl=3600) #list of field_names
        hset_redis_data(name, "reserve_json", {},  ttl=3600) #final reserve json, set when all fields clarified
    else:
        smap["meeting_start_time"] = get_redis_data(name, "meeting_start_time")
        smap["meeting_end_time"] = get_redis_data(name, "meeting_end_time")
        smap["building"] = get_redis_data(name, "building")
        smap["topic"] = get_redis_data(name, "topic")
        smap["send_notify"] = get_redis_data(name, "send_notify")
        smap["attendees"] = get_redis_data(name, "attendees")
        smap["clarifying_fields"] = get_redis_data(name, "clarifying_fields")
        smap["reserve_json"] = get_redis_data(name, "reserve_json", {})

    return smap

def get_session_states2(session_id):
    smap = get_session_states(session_id)
    if smap == {}: #new session, call it again to get valid dict value
        smap = get_session_states(session_id)

    return smap

def set_session_state(session_id, key, value):
    name = "session_states:"+session_id
    hset_redis_data(name, key, value, ttl=3600)

def set_session_states(session_id, session_map):
    set_session_state(session_id, "meeting_start_time", session_map['meeting_start_time'])
    set_session_state(session_id, "meeting_end_time", session_map['meeting_end_time'])
    set_session_state(session_id, "building", session_map['building'])
    set_session_state(session_id, "topic", session_map['topic'])
    set_session_state(session_id, "send_notify", session_map['send_notify'])
    set_session_state(session_id, "attendees", session_map['attendees'])
    set_session_state(session_id, "clarifying_fields", session_map['clarifying_fields'])
    set_session_state(session_id, "reserve_json", session_map['reserve_json'])

@chain_decorator
def check_session_stage(input):
    session_id = input.get('session_id')
    smap = get_session_states(session_id)
    if smap == {}:
        return 0 #new session
    if smap["meeting_start_time"] == "":
        return 1
    if smap["meeting_end_time"] == "":
        return 2
    if smap["building"] == "":
        return 3
    if smap["topic"] == "":
        return 4
    if smap["send_notify"] == "":
        return 5
    if smap["attendees"] == []:
        return 6
    return 7 #all known

def call_get_token_api():
    meeting_token_service_endpoint = "https://devtest.sinochem.com/MeetingRoom/api/appLogin"
    token_json = {
	    "appToken": "856737b5-8f25-432c-8a56-e2d760ef9960"
    }
    headers={'Content-Type': 'application/json', 'data-access-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIwODU0ZGQ0Ni1iMTkwLTQ1MGUtOGY5Ni04NTI2MjE1ZGZiN2IiLCJpYXQiOjE3MTY5NDM3MDYsIm5iZiI6MTcxNjk0MzcwNiwiZXhwIjoxNzE3NTQ4NTA2LCJ1c2VyIjp7InVzZXJuYW1lIjoidi1kZXZzdXBwb3J0IiwiYXBwSWQiOiJiMjdlM2NkYi05ZjRjLTQ0OTYtODQ5ZC03NDFhNjg0MTRlODEifX0.P7U5sq8NNEBxsH64Kr4ln9P936SLaMCfbgaG88v37U0'}
    print(f'start MeetingRoom/api/appLogin api, json={token_json}')
    response = requests.post(meeting_token_service_endpoint, json=token_json, headers=headers, timeout=30)
    response.raise_for_status() #throw exception if error
    ret_json = response.json()
    token = ""
    if ret_json["code"] == "0000": #success
        token = ret_json["data"]
    print(f'finish MeetingRoom/api/appLogin api, code={ret_json["code"]},token={token}')
    return token #might be ""

def call_get_token_api_wrapper(x):
    try:
        result = call_get_token_api()
    except Exception as ex:
        # Handles all exceptions
        print("An unhandled exception occured when calling MeetingRoom/api/appLogin.")
        print(type(ex).__name__, ex)
        result = ""
    if result == "": result = get_customItems_field(x, 'user_token')
    return result

def call_available_meetingroom_api(input, state_map):
    print('enter call_available_meetingroom_api')
    available_meetingroom_service_endpoint = "https://devtest.sinochem.com/MeetingRoom/api/tMeetingRoomInfo/ajaxListFuseStatus"
    cityName = input["user_cityName"]
    building = state_map["building"]
    startTime = datetime.strptime(state_map['meeting_start_time'], '%Y年%m月%d日%H时%M分').strftime("%Y-%m-%d %H:%M:%S")
    endTime = datetime.strptime(state_map['meeting_end_time'], '%Y年%m月%d日%H时%M分').strftime("%Y-%m-%d %H:%M:%S")
    attendeesNum = len(state_map["attendees"])
    buildingCode = [cityName, building]
    room_json = {"cityName": cityName, "building": building, "buildingCode": buildingCode,
                 "startTime": startTime, "endTime": endTime, "choose": True
                }
    headers={'Content-Type': 'application/json', 'token': input["user_token"]}
    print(f'start call_available_meetingroom_api, token={input["user_token"]}, json={room_json}')
    response = requests.post(available_meetingroom_service_endpoint, json=room_json, headers=headers, timeout=30)
    response.raise_for_status() #throw exception if error
    ret_json = response.json()
    roomsList = []
    roomId = None
    roomName = ""
    if ret_json["code"] == "0000": #success  #Daoming TODO: check code with SinoChem
        roomDatas = ret_json['data']
        for rd in roomDatas:
            roomsList.append((rd["id"],rd["capacity"],f"{rd['cityName']}-{rd['building']}-{rd['floorNumber']}层-{rd['displayName']}-容量:{rd['capacity']}"))
        roomsList.sort(key=lambda x:x[1])
        for r in roomsList:
            if r[1]-attendeesNum>=-5 and r[1]-attendeesNum<=5:
                roomId = r[0]
                roomName = r[2]
                break
        if roomId is None and roomsList:
            roomId = roomsList[0][0]
            roomName = roomsList[0][2]
    print(f'finish call_available_meetingroom_api, code={ret_json["code"]},roomId={roomId},roomName={roomName}')
    return roomId,roomName  #roomId, might be None
 
def call_available_meetingroom_api_wrapper(input, state_map):
    try:
        result,name = call_available_meetingroom_api(input, state_map)
    except Exception as ex:
        # Handles all exceptions
        print("An unhandled exception occured when calling call_available_meetingroom_api.")
        print(type(ex).__name__, ex)
        result = None
        name = ''
    return result,name

def call_contacts_api(input, user_name_or_email):
    print('enter call_contacts_api')
    contacts_service_endpoint = "https://devtest.sinochem.com/MeetingRoom/api/oaContact/getPersonsAndSubordinateList"
    departmentId = input["user_deptmentId"]
    name = user_name_or_email
    contact_json={"departmentId": departmentId, "name": name, "subordinate": True, "pageSize": 20, "pageIndex":1}
    headers={'Content-Type': 'application/json', 'token': input["user_token"]}
    print(f'start call_contacts_api, token={input["user_token"]}, json={contact_json}')
    response = requests.post(contacts_service_endpoint, json=contact_json, headers=headers, timeout=30)
    response.raise_for_status() #throw exception if error
    ret_json = response.json()
    contacts = []
    if ret_json["code"] == "0000": #success
        contactDatas = ret_json['data']["records"]
        for ct in contactDatas:
            contacts.append({"name":ct["name"], "email":ct["email"], "company":ct["company"], "department":ct["department"]})
    print(f'finish call_contacts_api, code={ret_json["code"]},contacts={contacts}')
    return contacts #might be []

def call_contacts_api_wrapper(input, user_name_or_email):
    try:
        result = call_contacts_api(input, user_name_or_email)
    except Exception as ex:
        # Handles all exceptions
        print("An unhandled exception occured when calling call_contacts_api.")
        print(type(ex).__name__, ex)
        result = []
    return result

def try_reserve_meetingroom_api(input, state_map):
    print('enter try_reserve_meetingroom_api')
    reserve_json = {}
    sendEmail = (state_map["send_notify"]=='是')
    startTime = datetime.strptime(state_map['meeting_start_time'], '%Y年%m月%d日%H时%M分').strftime("%Y-%m-%d %H:%M")
    endTime = datetime.strptime(state_map['meeting_end_time'], '%Y年%m月%d日%H时%M分').strftime("%Y-%m-%d %H:%M")
    subject = state_map["topic"]
    reservation_email = input['user_email']
    roomId,roomName = call_available_meetingroom_api_wrapper(input, state_map)
    if roomId is None: #no available room
        print('finish try_reserve_meetingroom_api: no available room')
        reserve_json["code"] = 1 #no room
        reserve_json["data"] = {}
        reserve_json["response"] = "对不起，没能找到可用的会议室"
        return  reserve_json
    attendees = []
    notifiers = []
    user_emails = state_map["attendees"]
    for ue in user_emails:
        cts = call_contacts_api_wrapper(input, ue)
        if cts:
            attendees.append({"name": cts[0]["name"], "accountId": ue.split("@")[0], "email":ue})
            notifiers.append({"accountId": ue.split("@")[0], "email":ue})
    meeting_json = {"confType": "0", "confSource": "2", "sendEmail": sendEmail,
                    "sendNotify":True, "mediaTypes":"Video", "startTime":startTime, "endTime":endTime,
                    "attendees":attendees, "subject": subject, "roomId": roomId, "leaders": "N", "eventAttendeeList": [],
                    "reservationEmail":reservation_email, "notifyRemind":[15], "notifyStaff":notifiers
                    }
    reserve_json["code"] = 0
    reserve_json["data"] = meeting_json
    reserve_json["response"] = f"""你将预订的会议室信息如下：
    时间: {startTime} 至 {endTime}
    地点: {roomName}
    请确认你是否要预订此会议室?
    """
    print(f'finish try_reserve_meetingroom_api, reserve_json={reserve_json}')
    return reserve_json

def call_reserve_meetingroom_api(input, state_map):
    print('enter call_reserve_meetingroom_api')
    reserve_meetingroom_service_endpoint = "http://dev.mp.sinochem.com/cangqiong-gateway/hxy-meeting-fusion/v2/meeting/create"
    reserve_result = {}
    meeting_json = state_map["reserve_json"]["data"]
    headers={'Content-Type': 'application/json', 'token': input["user_token"], 'data-access-token':'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIwODU0ZGQ0Ni1iMTkwLTQ1MGUtOGY5Ni04NTI2MjE1ZGZiN2IiLCJpYXQiOjE3MTY5NDM3MDYsIm5iZiI6MTcxNjk0MzcwNiwiZXhwIjoxNzE3NTQ4NTA2LCJ1c2VyIjp7InVzZXJuYW1lIjoidi1kZXZzdXBwb3J0IiwiYXBwSWQiOiJiMjdlM2NkYi05ZjRjLTQ0OTYtODQ5ZC03NDFhNjg0MTRlODEifX0.P7U5sq8NNEBxsH64Kr4ln9P936SLaMCfbgaG88v37U0'}
    print(f'start call_reserve_meetingroom_api, token={input["user_token"]}, json={meeting_json}')
    response = requests.post(reserve_meetingroom_service_endpoint, json=meeting_json, headers=headers, timeout=30)
    response.raise_for_status() #throw exception if error
    ret_json =  response.json()
    if ret_json["code"] == 2000: #success
        onsiteData = ret_json["body"]["onSite"]
        reserve_result["code"] = 0 #success
        reserve_result["subject"] = onsiteData["subject"]
        reserve_result["singleStartTime"] = onsiteData["singleStartTime"]
        reserve_result["singleEndTime"] = onsiteData["singleEndTime"]
        reserve_result["roomName"] = onsiteData["roomName"]
        reserve_result["meetingAddress"] = onsiteData["meetingAddress"]
    else:
        reserve_result["code"] = 2 #error
    print(f'finish call_reserve_meetingroom_api, code={ret_json["code"]}, reserve_result={reserve_result}')
    return reserve_result  #we need to handle API exception

def call_reserve_meetingroom_api_wrapper(input, state_map):
    try:
        reserve_result = call_reserve_meetingroom_api(input, state_map)
    except Exception as ex:
        # Handles all exceptions
        print("An unhandled exception occured when calling call_reserve_meetingroom_api.")
        print(type(ex).__name__, ex)
        reserve_result = {}
        reserve_result["code"] = 2 #success
    return reserve_result

def map_from_buildingName_to_dbName(buildingName):
    if buildingName == '凯晨世贸中心' or buildingName == '凯晨大厦' or buildingName == '凯晨' or buildingName == '凯晨中心':
        return 'kaichen'
    elif buildingName == '中化' or buildingName == '中化大厦':
        return 'zhonghua'
    return ''

def check_field_value_is_valid(input,field_name, valueStr):
    if valueStr == '':
        if field_name != 'attendees': return False, '', f'{propNamesChsMap[field_name]}字段为空，请输入它的值'
        else: return False, [], f'{propNamesChsMap[field_name]}字段为空，请输入它的值'
    if field_name == 'meeting_start_time' or field_name == 'meeting_end_time' \
        or field_name == 'topic' or field_name == 'send_notify':
        return True, valueStr, ''
    if field_name == 'building':
        user_buildings = input['user_building']
        buildingDbName = map_from_buildingName_to_dbName(valueStr)
        if buildingDbName == '': #invalid name
            return False, '', f'{valueStr}是不正确的办公楼名，可用的楼名为中化大厦或凯晨大厦，请输入正确的办公楼名。'
        if not buildingDbName in user_buildings:
            return False, '', f'你没有权限预订{valueStr}的会议室，请输入你有权限的办公楼名。'
        return True, buildingDbName, ''
    if field_name == 'attendees':
        attendees = valueStr.split(" ") #emails
        validValues = []
        invalidValues = []
        for at in attendees:
            cts = call_contacts_api_wrapper(input, at)
            if cts == []:
                invalidValues.append(at)
            else:
                validValues.append(at)
        if invalidValues == []:
            return True, validValues, ''
        else:
            if validValues == []:
                errMsg = '参会人邮箱地址均不正确，请准确输入参会人信息。'
            else:
                errMsg = '参会人邮箱地址有些是不正确的，请准确输入参会人信息。正确的邮箱地址有:'+";".join(validValues)+"。而不正确的邮箱地址有:"+";".join(validValues)
            return False, [], errMsg

def fix_new_state_map(input, new_state_map, new_state_map_unfixed, fields, emptyAllowed):
    response = ""
    invalid_fields = []
    for k in fields: #init
        if k != "attendees": new_state_map[k] = ""
        else: new_state_map[k] = []
    for k in fields:
        if new_state_map_unfixed[k] == "" and emptyAllowed: continue
        isValid, updated_field_value, errMsg = check_field_value_is_valid(input, k, new_state_map_unfixed[k])
        new_state_map[k] = updated_field_value
        if not isValid:
            response += errMsg + "\n"
            invalid_fields.append(k)
    return invalid_fields, response

def get_clarifying_fields_and_response(state_map):
    response = ""
    clarifying_fields = []
    if state_map['meeting_start_time'] == "":
        clarifying_fields.append('meeting_start_time')
        if state_map["meeting_end_time"] == "":
            clarifying_fields.append('meeting_end_time')
            response = "你想要什么时间开始会议，要开多长时间?"
        elif state_map["building"] == "":
            clarifying_fields.append('building')
            response = "你想要什么时间开始会议，在哪个办公楼开?"
        elif state_map["topic"] == "":
            clarifying_fields.append('topic')
            response = "你想要什么时间开始会议，会议主题是什么?"
        else:
            response = "你想要什么时间开始会议?"
    elif state_map['meeting_end_time'] == "":
        clarifying_fields.append('meeting_end_time')
        if state_map["building"] == "":
            clarifying_fields.append('building')
            response = "你想要什么时间结束会议，在哪个办公楼开?"
        elif state_map["topic"] == "":
            clarifying_fields.append('topic')
            response = "你想要什么时间结束会议，会议主题是什么?"
        else:
            response = "你想要什么时间结束会议?"
    elif state_map['building'] == "":
        clarifying_fields.append('building')
        if state_map["topic"] == "":
            clarifying_fields.append('topic')
            response = "你想在哪个办公楼开会，会议主题是什么?"
        else:
            response = "你想在哪个办公楼开会?"
    elif state_map['topic'] == "":
        clarifying_fields.append('topic')
        response = "会议主题是什么?"
    elif state_map['send_notify'] == "":
        clarifying_fields.append('send_notify')
        if state_map["attendees"] == []:
            clarifying_fields.append('attendees')
            response = "是否需要向参会人发送邮件通知，还有参会人包括哪些人? 请输入参会人的邮箱地址，并以分号隔开。"
        else:
            response = "是否需要向参会人发送邮件通知?"
    elif state_map["attendees"] == []:
        clarifying_fields.append('attendees')
        response = "参会人包括哪些人? 请输入参会人的邮箱地址，并以分号隔开。"
    return clarifying_fields, response

def get_response_from_state_info(input, cur_state_no, cur_state_map, new_state_map_unfixed):
    new_state_map = copy.deepcopy(cur_state_map)
    clarifying_fields = cur_state_map["clarifying_fields"]
    if cur_state_no == 0: #new session
        invalid_fields, response = fix_new_state_map(input, new_state_map, new_state_map_unfixed, fields=propNames[1:], emptyAllowed=True)
        if invalid_fields != []:
            new_state_map['clarifying_fields'] = clarifying_fields = invalid_fields
            set_session_states(input['session_id'],new_state_map)
            return response
    elif clarifying_fields != []:
        invalid_fields, response = fix_new_state_map(input, new_state_map, new_state_map_unfixed, fields = clarifying_fields, emptyAllowed=False)
        other_fields = list(filter(lambda x: x not in clarifying_fields, propNames[1:]))
        invalid_fields2, response2 = fix_new_state_map(input, new_state_map, new_state_map_unfixed, fields = other_fields, emptyAllowed=True)
        if invalid_fields != []:
            new_state_map['clarifying_fields'] = clarifying_fields = invalid_fields
            set_session_states(input['session_id'],new_state_map)
            return response
        elif invalid_fields2 != []:
            new_state_map['clarifying_fields'] = clarifying_fields = invalid_fields2
            set_session_states(input['session_id'],new_state_map)
            return response2
    clarifying_fields, response = get_clarifying_fields_and_response(new_state_map)
    new_state_map['clarifying_fields'] = clarifying_fields
    set_session_states(input['session_id'],new_state_map)
    if clarifying_fields != []:
        return response
    #all fields clarified
    reserve_json = try_reserve_meetingroom_api(input, new_state_map)
    new_state_map['reserve_json'] = reserve_json
    set_session_states(input['session_id'],new_state_map)
    response = reserve_json["response"]

    return response

def get_session_state_response(x):
    cur_state = x["cur_state"]
    cur_state_map = x["cur_state_map"]
    new_input_states = x["new_input_states"]
    msg = AIMessage(content="")
    if new_input_states["want_subscribe"] == 'N': #user don't want to subscribe
        msg.content = "不好意思，没能帮到你，有需要再联系我。"
        return msg
    new_state_map = copy.deepcopy(cur_state_map)
    for k in propNames[1:]:
        new_state_map[k] = new_input_states[k]
    msg.content = get_response_from_state_info(x, cur_state, cur_state_map, new_state_map)
    return msg

def do_reserve_meeting_room(x):
    msg = AIMessage(content="")
    result = call_reserve_meetingroom_api_wrapper(x, x['cur_state_map'])
    if result["code"]==0:#success
        msg.content = f"预订会议室成功。 会议主题:{result['subject']},时间:{result['singleStartTime']}至{result['singleEndTime']},地点:{result['meetingAddress']}-{result['roomName']}"
    elif result["code"]==1: #no available room
        msg.content = f"预订会议室失败。错误原因:没有可用的会议室。"
    else:
        msg.content = f"预订会议室失败。错误原因:调用中化API失败。"
    return msg

def get_cur_time_info(x):
    t = datetime.now()
    t_weekdays = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日']
    cur_time = f'{t.year}年{t.month}月{t.day}日{t.hour}时{t.minute}分,{t_weekdays[t.weekday()]}'
    return cur_time

parse_input_state_chain0 = RunnablePassthrough.assign(chat_history = lambda x: format_chat_history(x)) | \
    RunnablePassthrough.assign(current_time_info = lambda x: get_cur_time_info(x)) | \
    RunnablePassthrough.assign(template_name=RunnableValue(value='reserve_meeting_room_state_clarify_template')) | \
    model_binding | \
    ekcStrOutputParser()

@chain_decorator
def parse_meeting_room_state_clarify_output(input):
    """
    员工是否要订会议室: 是
    会议开始时间: 2024年5月11日10时0分
    会议结束时间: 2024年5月11日12时0分
    会议室所在写字楼: 凯晨世贸中心
    会议主题: 项目沟通会
    发送邮件通知: 是
    参会人信息: x1@sinochem.com y1@sinochem.com
    """
    llm_result_lines = input["llm_result"].strip().split("\n")
    propPrefixs = ["员工是否要订会议室:", "会议开始时间:", "会议结束时间:", "会议室所在写字楼:", "会议主题:", "发送邮件通知:", "参会人信息:"]
    propStrs = ["" for _ in propPrefixs]
    new_states = {p:""  for p in propNames}
    for i, result_line in enumerate(llm_result_lines):
        result_line = result_line.strip()[len(propPrefixs[i]):].strip()
        if i==0:
            propStrs[i] = 'Y' if result_line.startswith('是') else 'N'
            new_states[propNames[i]] = propStrs[i]
        elif not result_line.startswith("无"):
            propStrs[i] = result_line
            new_states[propNames[i]] = propStrs[i]

    return new_states

@chain_decorator
def parse_confirm_reserve_output(input):
    llm_result_lines = input["llm_result"].strip()
    return True if llm_result_lines.startswith('是') else False

parse_input_state_chain = RunnablePassthrough.assign(llm_result = parse_input_state_chain0) |\
    parse_meeting_room_state_clarify_output

parse_confirm_reserve_chain0 = RunnablePassthrough.assign(chat_history = lambda x: format_chat_history(x)) | \
    RunnablePassthrough.assign(current_time_info = lambda x: get_cur_time_info(x)) | \
    RunnablePassthrough.assign(template_name=RunnableValue(value='reserve_meeting_room_confirm_template')) | \
    model_binding | \
    ekcStrOutputParser()

parse_confirm_reserve_chain = RunnablePassthrough.assign(llm_result = parse_confirm_reserve_chain0) |\
    parse_confirm_reserve_output

session_state_output = {
    'response_variables' : lambda x: {
        "response_type": ['LLM'],
        "feedback": [],
        "confidence":0,
        "relevance":0,
        "sources_documents": [],
        "LLM": [x.get('configurable').get('output_llm') or x.get('output_llm')],
        "external_service": {}
    },
    'model_output' : RunnableLambda(get_session_state_response)
}

session_reserve_output = {
    'response_variables' : lambda x: {
        "response_type": ['LLM'],
        "feedback": [],
        "confidence":0,
        "relevance":0,
        "sources_documents": [],
        "LLM": [x.get('configurable').get('output_llm') or x.get('output_llm')],
        "external_service": {}
    },
    'model_output' : RunnableLambda(do_reserve_meeting_room)
}

session_noreserve_output = {
    'response_variables' : lambda x: {
        "response_type": ['LLM'],
        "feedback": [],
        "confidence":0,
        "relevance":0,
        "sources_documents": [],
        "LLM": [x.get('configurable').get('output_llm') or x.get('output_llm')],
        "external_service": {}
    },
    'model_output' : lambda x: AIMessage(content='对不起，这次没帮到你，一天好心情...')
}

def get_clarified_status(x):
    st = x['cur_state_map']
    if st.get("reserve_json") is None or st.get("reserve_json") == {}:
        return 0 #not clarified
    if st["reserve_json"]["code"] != 0:
        return 1 #clarified but no room
    return 2 #all clarified with available room

confirm_reserve_dispatcher = RunnableBranch(
    (lambda x: x['confirmed'], session_reserve_output | astreaming_parser),
    session_noreserve_output | astreaming_parser
)

session_state_dispatcher = RunnablePassthrough.assign(cur_state = check_session_stage) |\
    RunnablePassthrough.assign(cur_state_map=lambda x: get_session_states2(x['session_id'])) |\
    RunnableBranch(
        (lambda x: get_clarified_status(x) ==2, RunnablePassthrough.assign(confirmed = parse_confirm_reserve_chain)  |\
            confirm_reserve_dispatcher),
        (lambda x: get_clarified_status(x) ==1, session_noreserve_output | astreaming_parser),
        RunnablePassthrough.assign(new_input_states = parse_input_state_chain)  |\
            session_state_output | astreaming_parser
    )

parameter_incorrect_output = {
    'response_variables' : lambda x: {
            "response_type": ['LLM'],
            "feedback": [],
            "confidence":0,
            "relevance":0,
            "sources_documents": [],
            "LLM": [x.get('configurable').get('output_llm') or x.get('output_llm')],
            "external_service": {}
        },
    'model_output' : lambda x: AIMessage(content="请检查你的应用设置和输入参数，这个应用需要设置session_id,client_id,user_name等参数。")
}

parameter_check_dispatcher=RunnableBranch(
    # has correct input
    (lambda x:x.get('app_id') and x.get('session_id') and x.get('client_id') and x.get('user_name') and x.get('user_email') and x.get('user_deptmentId') and x.get('user_token') and x.get('user_cityName') and x.get('user_building'),
        redis_data | reformat_config | session_state_dispatcher),
    # no app_id or session_id or client_id, not supported
    RunnablePassthrough(lambda x: logger.error(f"reserve meeting room chain: incorrect input. app_id={x.get('app_id')}, session_id={x.get('session_id')}, client_id={x.get('client_id')}")) |\
        parameter_incorrect_output | astreaming_parser
)

@chain_decorator
async def throw_exception(inputs):
    exception=inputs['exception']
    try:
        hasattr(exception,'status_code')
        hasattr(exception,'error_code')
        hasattr(exception,'message')
    except:
        exception=exceptions.ApplicationError(str(exception))
    return RunnableNotice(error=exception)

exception_handler=throw_exception|astreaming_parser

chain = add_time_stamp_start | RunnablePassthrough.assign(**inputs,**config_maps) |\
        RunnablePassthrough.assign(user_token=lambda x: call_get_token_api_wrapper(x)) |\
        RunnablePassthrough(lambda x: logger.debug("Input for reserve_meeting_room chain is: "+str(x))) |\
        parameter_check_dispatcher
chain = chain.with_fallbacks([exception_handler],exceptions_to_handle=exceptions.errors,exception_key='exception')

if langfuse_handler:
    chain = chain.with_config(config={"callbacks":[langfuse_handler]})
chain = chain.with_types(input_type=ReserveMeetingRoomChainInputModel,output_type=ReserveMeetingRoomChainOutputModel)
