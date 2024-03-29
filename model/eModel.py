from datetime import datetime, timedelta
import json
from model.util import group,process_date
from model.db import mongo


def getProfile(t_id):
    return list(mongo.db.user.find({"id": t_id}, {"_id": 0}))[0]


def editProfile(t_id, name, sex, birth, phone):
    return mongo.db.user.update_one(
        {"id": t_id},
        {"$set": {"name": name, "sex": sex, "birth": birth, "phone": phone}},
    )


def getEpeople(t_id):
    p_list = list(mongo.db.appointment.find({"t_id": t_id}, {"_id": 0, "p_id": 1}))
    p_ids = []
    for i in p_list:
        p_ids.append(i["p_id"])
    print(p_ids)
    try:
        return list(
            mongo.db.user.aggregate(
                [
                    {
                        "$match": {"id": {"$in": p_ids}},
                    },
                    {
                        "$lookup": {
                            "from": "patient",
                            "localField": "id",
                            "foreignField": "p_id",
                            "as": "result",
                        },
                    },
                    {"$unwind": "$result"},
                    {
                        "$addFields": {
                            "height": "$result.height",
                            "disease": "$result.disease",
                        }
                    },
                    {"$unset": ["_id", "result"]},
                ]
            )
        )
    except:
        return "error"


def getAppoint(t_id):
    table = ["MON", "THE", "WED", "THU", "FRI", "SAT", "SUN"]
    try:
        data = list(
            mongo.db.appointment.aggregate(
                [
                    {"$match": {"t_id": t_id}},
                    {
                        "$group": {
                            "_id": {"start_date": "$start_date", "time": "$time"},
                            "count": {"$count": {}},
                        }
                    },
                    {"$set": {"id": "$_id"}},
                    {"$unset": "_id"},
                    {"$sort":{"id":1}}
                ]
            )
        )
        return process_date(data)
        # res=[]
        for i in data:
            date = i["id"]["start_date"]
            time = i["id"]["time"]

            datetime_object = datetime.strptime(f"{date}", "%Y-%m-%d %H:%M:%S")

            datetime_object += timedelta(days=table.index(time[0:3]))
            i["tf_id"] = {
                "time": f'{int(f"0x{time[3]}",16)+7}:00',
                "start_date": datetime_object,
            }

        return data
    except Exception as e:
        print(e)
        return "model error"


def getAppointDetail(t_id, start_date, time):
    try:
        return list(
            mongo.db.appointment.aggregate(
                [
                    {
                        "$match": {
                            "t_id": t_id,
                            "time": time,
                            "start_date": {"$eq": datetime.fromisoformat(start_date)},
                        }
                    },
                    {
                        "$lookup": {
                            "from": "user",
                            "localField": "p_id",
                            "foreignField": "id",
                            "as": "result",
                        },
                    },
                    {"$unwind": {"path": "$result"}},
                    {"$addFields": {"name": "$result.name"}},
                    {"$unset": ["result", "_id", "t_id", "start_date", "time"]},
                ]
            )
        )
    except Exception as e:
        return f"getAppointmentDetail :{e}"



    
