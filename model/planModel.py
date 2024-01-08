import json
from model.homeModel import is_same_day
from model.util import timeFormat
from model.db import mongo
from datetime import datetime, timedelta


def addPlan(plan):
    ##新增時需判斷是否有重複區間
    plan["str_date"] = datetime.fromisoformat(plan["str_date"])
    plan["end_date"] = datetime.fromisoformat(plan["end_date"])
    print(plan["str_date"], plan["end_date"])
    print(checkPlan(plan["str_date"], plan["end_date"], plan["user_id"]))
    if (len(checkPlan(plan["str_date"], plan["end_date"], plan["user_id"]))) <= 0:
        return mongo.db.plan.insert_one(plan)
    else:
        return "無法新增"


def checkPlan(start: datetime, end: datetime, user_id):
    return list(
        mongo.db.plan.find(
            {
                "user_id": user_id,
                "$or": [
                    {
                        "str_date": {"$lte": end},
                        "end_date": {"$gte": start},
                    },
                    {
                        "str_date": {"$lte": start},
                        "end_date": {"$gte": end},
                    },
                ],
            }
        )
    )


def getPlan(user_id):
    return list(
        mongo.db.plan.aggregate(
            [
                {"$match": {"user_id": user_id}},
                {"$unset": ["_id"]},
                {"$sort": {"str_date": 1}},
            ]
        )
    )


# .sort({"str_date":1})


def editPlan(plan, user_id):
    plan["str_date"] = datetime.fromisoformat(plan["str_date"])
    plan["end_date"] = datetime.fromisoformat(plan["end_date"])
    if (len(checkPlan(plan["str_date"], plan["end_date"], user_id))) <= 0:
        return mongo.db.plan.update_one(
            {"id": user_id},
            {"$set": plan},
        )
    else:
        return "無法新增"


def barChart(user_id):
    detail = list(
        mongo.db.Invite_detail.aggregate(
            [
                {
                    "$match": {
                        "user_id": user_id,
                        "accept": 1,
                        "total_score": {"$exists": True},
                    }
                },
                {"$group": {"_id": None, "id": {"$addToSet": "$i_id"}}},
                {"$project": {"_id": 0, "id": 1}},
            ]
        )
    )[0]["id"]

    twelve_months_ago = datetime.now() - timedelta(days=365)

    return list(
        mongo.db.Invite.aggregate(
            [
                {
                    "$match": {
                        "id": {"$in": detail},
                        "time": {"$gte": twelve_months_ago, "$lt": datetime.now()},
                    }
                },
                {
                    "$addFields": {
                        "YwithM": {
                            "$concat": [
                                {"$toString": {"$year": {"$toDate": "$time"}}},
                                "-",
                                {"$toString": {"$month": {"$toDate": "$time"}}},
                            ]
                        },
                        "month": {"$month": {"$toDate": "$time"}},
                    }
                },
                {"$group": {"_id": ["$month", "$YwithM"], "count": {"$sum": 1}}},
                {
                    "$addFields": {
                        "month": {"$first": "$_id"},
                        "YwithM": {"$last": "$_id"},
                    }
                },
                {"$unset": ["_id"]},
                {"$sort":{"YwithM":1}}
            ]
        )
    )


def sportChart(user_id):
    rate = []
    plans = list(
        mongo.db.plan.find(
            {
                "user_id": f"{user_id}",
                "str_date": {"$lte": datetime.now()},
                "end_date": {"$lte": datetime.now()},
            },
            {"_id": 0},
        )
    )

    for plan in plans:
        sportsday = list(
            mongo.db.invite_lsit.find(
                {
                    "time": {"$gte": plan["str_date"], "$lte": plan["end_date"]},
                    "user_id": f"{user_id}",
                }
            )
        )

        weekSport = sum(plan["execute"])
        str_date = plan["str_date"]
        end_date = plan["end_date"]
        firstWeek = 0
        lastWeek = 0
        firstWeekEnd = datetime.now()
        # 第一週目標組數
        for i in range(7):
            # 若已到當週最後一天就離開
            weekday = (str_date + timedelta(days=i)).weekday()
            if weekday == 7:
                firstWeekEnd = str_date + timedelta(days=i + 1)
                break
            else:
                firstWeek += plan["execute"][weekday]
        # 最後一週目標組數
        start_of_week = end_date - timedelta(days=end_date.weekday())
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            lastWeek += plan["execute"][day.weekday()]
            if is_same_day(day, plan["end_date"]):
                break
        num_days = (firstWeekEnd - start_of_week).days
        num_weeks = (num_days - 1) / 7
        target = num_weeks * weekSport + firstWeek + lastWeek
        rate.append((len(sportsday) / target))
    # 看個別運動計畫達成率
    print(rate)
    return sum(rate) / len(rate)


def runChart(user_id):
    return list(
        mongo.db.Invite_detail.aggregate(
            [
                {
                    "$match": {
                        "user_id": user_id,
                        "accept": 1,
                        "total_score": {"$exists": True},
                    }
                },
                {
                    "$lookup": {
                        "from": "Invite",
                        "localField": "i_id",
                        "foreignField": "id",
                        "as": "result",
                    }
                },
                {"$unwind": "$result"},
                {"$addFields": {"time": "$result.time"}},
                {"$project": {"result": 0}},
                {
                    "$project": {
                        "yearMonth": {
                            "$dateToString": {
                                "format": "%Y-%m",
                                "date": {"$toDate": "$time"},
                            }
                        },
                        "total_score": 1,
                        "_id": 0,
                        "id": 1,
                    }
                },
                {
                    "$group": {
                        "_id": "$yearMonth",
                        "count": {"$sum": 1},
                        "score": {"$sum": "$total_score"},
                        "avg": {"$avg": "$total_score"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
    )
