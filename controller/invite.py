from flask import Blueprint, request
from model import inviteModel
from .util import checkParm, ret, quickRet
from model.db import mongo

inviteAPI = Blueprint("invite", __name__, url_prefix="/invite")

#新增邀約
@inviteAPI.route("/<m_id>/add", methods=["POST"]) 
def addinvite(m_id):
    cond = ["id", "name", "friend","time","remark"]
    result = {"success": False, "mes": ""}
    check = checkParm(cond, request.json)

    if(isinstance(check, dict)):
        if type(check) == dict:
            id = check["id"]
            name = check["name"]
            friend = check["friend"]
            time = check["time"]
            remark = check["remark"]
            inviteModel.addinvite(
                id,name,m_id,friend,time,remark
            )
            friend = []
            for i in check["friend"]:
                friend.append(i)
            if(friend != []): #加try 查看看mongo有沒有transaction
                try:
                    for i in range(0,len(friend)):
                        inviteModel.addinvitedetail(id,friend[i])
                    result["mes"] = "新增邀約成功"
                    result["success"] = True
                    return ret(result) 
                except:
                    result["mes"] = "好友邀約失敗"
                    return ret(result)
            else:
                result["mes"] = "新增邀約成功，您暫無邀請任何好友"
                result["success"] = True
                return ret(result) 
    else : 
        result["mes"] = "新增邀約異常"
        return ret(result)    


#修改邀約
@inviteAPI.route("/<m_id>/<id>/edit", methods=["POST"]) 
def editinvite(m_id,id):
    cond = ["name", "friend","time","remark"]
    check = checkParm(cond, request.json)
    print(check)
    result = {"success": False, "mes": ""}
    name=check["name"]
    friend=check["friend"]
    time=check["time"]
    remark=check["remark"]
    if(isinstance(check, dict)):
        if type(check) == dict:
            data = inviteModel.editinvite(id, name, m_id, friend, time, remark)
            print((data))
            result["mes"] = "編輯成功"
            result["success"] = True
            return ret(result)
    else:
        result["mes"] = "修改失敗"
        return ret(result)  

#查看邀約列表
@inviteAPI.route("/list/<m_id>/<int:mode>", methods=["GET"])
def getinviteList(m_id,mode):
    match(mode):
        #接受、跟他主辦的
        case 1:
            try:
                data = getaccept(m_id)
                return quickRet(data) 
            except : 
                result = {"success": False, "mes": "查無資料"}
                return ret(result)
        #不接受
        case 2:
            try:
                data = getreject(m_id)
                return quickRet(data) 
            except:
                result = {"success": False, "mes": "查無資料"}
                return ret(result)
        #未回覆
        case 3:
            try:
                data = getunreply(m_id)
                return quickRet(data) 
            except:
                result = {"success": False, "mes": "查無資料"}
                return ret(result)
        #全部
        case _:
            accept = getaccept(m_id)
            reject = getreject(m_id)
            unreply = getunreply(m_id)
            data={"accept":accept,"reject":reject,"unreply":unreply}
            return quickRet(data)

def getaccept(m_id):
    acceptID=inviteModel.getacceptID(m_id)
    accept_ids = []
    for i in acceptID:
        accept_ids.append(i["id"])
    if(accept_ids !=[]):
        data = inviteModel.getacceptList(m_id,accept_ids)
        print(data)
        return data
    
def getreject(m_id):
    rejectID = inviteModel.getrejectID(m_id)
    reject_ids = []
    for i in rejectID:
        reject_ids.append(i["id"])
    if(reject_ids !=[]):
        data = inviteModel.getrejectList(reject_ids)
        print(data)
        return data
    
def getunreply(m_id):
    unreplyID = inviteModel.getunreplyID(m_id)
    unreply_ids = []
    for i in unreplyID:
        unreply_ids.append(i["id"])
    if(unreply_ids !=[]):
        data = inviteModel.getunreplyList(unreply_ids)
        return data

#查看邀約內容
@inviteAPI.route("/<m_id>/<id>", methods=["GET"]) 
def getinviteDetail(m_id,id):
    try:
        data = inviteModel.getinviteDetail(m_id,int(id))
        return quickRet(data)
    except: 
        result = {"success": False, "mes": "查無資料"}
        return ret(result)
    
    
#使用者回復邀約
@inviteAPI.route("/<m_id>/<id>", methods=["POST"]) 
def replyinvite(m_id,id):
    cond = ["accept"]
    check = checkParm(cond, request.json)
    result = {"success": False, "mes": ""}
    if(isinstance(check, dict)):
        if type(check) == dict:
            try:
                accept=check["accept"]
                inviteModel.replyinvite(m_id, int(id), accept)
                if(accept):
                    result["mes"] = "已接受邀約"
                else:
                    result["mes"] = "已拒絕邀約"
                result["success"] = True
                return ret(result)
            except:
                return ret(result)
    else:
        result["mes"] = "資料傳遞錯誤"
        return ret(result)
