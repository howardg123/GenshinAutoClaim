import psycopg2
import numpy as np
import os
import heroku3
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def get_heroku_connection(heroku_key, heroku_name):
    heroku_conn = heroku3.from_key(heroku_key)
    app = heroku_conn.apps()[heroku_name]
    proclist = app.process_formation()
    config = app.config()
    return heroku_conn, app, proclist, config

# def compareDatabaseURL(config1, config2):
#     if config1["DATABASE_URL"] != config2["DATABASE_URL"]:
#         config2["DATABASE_URL"] = config1["DATABASE_URL"]
#         print("config is changed")

#Heroku server 1
heroku_conn1, app1, proclist1, config1 = get_heroku_connection(os.environ['HEROKU1_KEY'], 'genshinautoclaim')
#Heroku server 2
heroku_conn2, app2, proclist2, config2 = get_heroku_connection(os.environ['HEROKU2_KEY'], 'genshinautoclaim2')
#compareDatabaseURL(config1, config2)

conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
conn.set_session(autocommit=True)
secret_key=os.environ['SECRET_KEY']
f = Fernet(secret_key.encode("utf-8"))
cursor = conn.cursor()

guildTableName = "guild_table"
userTableName = "user_table"

#Guild
async def createGuildTable():
    sqlCreateGuildTable = "create table if not exists "+guildTableName+" (id bigint NOT NULL PRIMARY KEY);"
    cursor.execute(sqlCreateGuildTable)
    conn.commit()

async def insertDataToGuildTable(guildId):
    try:
        sqlInsertGuildData = "insert into "+guildTableName+"(id) VALUES ("+str(guildId)+")"
        cursor.execute(sqlInsertGuildData)
        conn.commit()
        count = cursor.rowcount
        print(count, "Record inserted successfuly in guild table")
    except (Exception, psycopg2.Error) as error:
        print("Failed to insert in guild table", error)

async def getGuild(guildId):
    try:
        sqlSelectGuildData = "select id from "+guildTableName+" where id = "+str(guildId)
        cursor.execute(sqlSelectGuildData)
        record = cursor.fetchone()
        return record
    except (Exception, psycopg2.Error) as error:
        print("Failed to get data in guild table", error)

async def getAllGuild():
    try:
        sqlSelectGuildData = "select id from "+guildTableName
        cursor.execute(sqlSelectGuildData)
        record = cursor.fetchall()
        arrayRecord = np.array(record).flatten()
        return arrayRecord
    except (Exception, psycopg2.Error) as error:
        print("Failed to get data in guild table", error)

async def removeGuildData(guildId):
    try:
        sqlDeleteGuildData = "delete from "+guildTableName+" where id = " + str(guildId)
        cursor.execute(sqlDeleteGuildData)
        conn.commit()
        count = cursor.rowcount
        print(count, "Record deleted successfuly in guild table")
    except (Exception, psycopg2.Error) as error:
        print("Error in Delete operation", error)

async def removeAllGuildData():
    try:
        sqlDeleteGuildData = "delete from "+guildTableName
        cursor.execute(sqlDeleteGuildData)
        conn.commit()
        count = cursor.rowcount
        print(count, "Record deleted successfuly in guild table")
    except (Exception, psycopg2.Error) as error:
        print("Error in Delete operation", error)
#User
async def createUserTable():
    sqlCreateUserTable = "create table if not exists "+userTableName+" (id bigint NOT NULL PRIMARY KEY, ltoken text NOT NULL, ltuid text NOT NULL, guild bigint NOT NULL);"
    cursor.execute(sqlCreateUserTable)
    conn.commit()

async def insertDataToUserTable(userName, userId, ltoken, ltuid, guildId):
    try:
        sqlInsertUserData = "insert into "+userTableName+"(id, ltoken, ltuid, guild) VALUES (%s,%s,%s,%s)"
        record_to_insert = (userId, str(f.encrypt(ltoken.encode("utf-8")).decode("utf-8")), str(f.encrypt(ltuid.encode("utf-8")).decode("utf-8")), guildId)
        cursor.execute(sqlInsertUserData,record_to_insert)
        conn.commit()
        return str(userName)+"'s data is added successfully. Claim messages will be sent here."
    except (Exception, psycopg2.Error) as error:
        print ("Failed to add "+ str(userName)+ "'s data.", str(error))
        return str(userName)+"'s data is either wrong or already existing."

async def getUser(userId):
    try:
        sqlSelectUsersfromGuild = "select id, ltoken, ltuid, guild from "+userTableName+" where id = " + str(userId)
        cursor.execute(sqlSelectUsersfromGuild)
        record = cursor.fetchone()
        return record
    except (Exception, psycopg2.Error) as error:
        print("Failed to get data in user table", error)
    
async def getUsersFromGuild(guildId):
    try:
        sqlSelectUsersfromGuild = "select id, ltoken, ltuid, notify, notifyResin from "+userTableName+" where guild = " + str(guildId)
        cursor.execute(sqlSelectUsersfromGuild)
        records = cursor.fetchall()
        arrayObject = []
        for record in records:
            userid, ltoken, ltuid, notify, notifyResin = record
            userObject = {
                'name': userid,
                'ltoken': ltoken,
                'ltuid': ltuid,
                'notify': notify,
                'notifyResin': notifyResin,
            }
            arrayObject.append(userObject)
        return arrayObject
    except (Exception, psycopg2.Error) as error:
        print("Failed to get data in user table", error)

async def removeUserData(userName, userId):
    try:
        sqlDeleteUserData = "delete from "+userTableName+" where id = " + str(userId)
        cursor.execute(sqlDeleteUserData)
        conn.commit()
        return str(userName)+"'s data is removed successfully."
    except (Exception, psycopg2.Error) as error:
        return str(userName) + "'s data does not exist."

async def removeAllUserData():
    try:
        sqlDeleteUserData = "delete from "+userTableName
        cursor.execute(sqlDeleteUserData)
        conn.commit()
        count = cursor.rowcount
        print(count, "Record deleted successfuly in user table")
    except (Exception, psycopg2.Error) as error:
        print("Error in Delete operation", error)

async def updateUserData(userName, userId, ltoken, ltuid, guildId):
    try:
        #ltoken
        sqlUpdateUserLtoken = "update user_table set ltoken = %s where id = %s"
        cursor.execute(sqlUpdateUserLtoken, (str(f.encrypt(str(ltoken).encode("utf-8")).decode("utf-8")), userId))
        conn.commit()
        #ltuid
        sqlUpdateUserLtoken = "update user_table set ltuid = %s where id = %s"
        cursor.execute(sqlUpdateUserLtoken, (str(f.encrypt(str(ltuid).encode("utf-8")).decode("utf-8")), userId))
        conn.commit()
        #guildId
        sqlUpdateUserLtoken = "update user_table set guild = %s where id = %s"
        cursor.execute(sqlUpdateUserLtoken, (guildId, userId))
        conn.commit()
        return str(userName)+"'s data is successfully updated. Claim messages will be sent here."
    except (Exception, psycopg2.Error) as error:
        print(error)
        return str(userName)+"'s data failed to update."

async def setUID(uid, userId):
    try:
        #ltoken
        sqlUpdateUID = "update user_table set uid = %s where id = %s"
        cursor.execute(sqlUpdateUID, (str(f.encrypt(str(uid).encode("utf-8")).decode("utf-8")), userId))
        conn.commit()
        return str(uid)+"'s data is successfully added."
    except (Exception, psycopg2.Error) as error:
        print(error)
        return "UID is incorrect."

async def getUID(userId):
    try:
        sqlSelectUIDfromUser = "select uid from "+userTableName+" where id = " + str(userId)
        cursor.execute(sqlSelectUIDfromUser)
        record = cursor.fetchone()
        return record
    except (Exception, psycopg2.Error) as error:
        print("Failed to get data in user table", error)

async def updateNotify(notifyResin, userId):
    try:
        #guildId
        sqlUpdateUserLtoken = "update "+userTableName+" set notify = %s where id = %s"
        cursor.execute(sqlUpdateUserLtoken, ('TRUE', userId))
        conn.commit()
        sqlUpdateUserLtoken = "update "+userTableName+" set notifyResin = %s where id = %s"
        cursor.execute(sqlUpdateUserLtoken, (notifyResin, userId))
        conn.commit()
        return "Will notify user <@"+str(userId)+"> if resin is at "+ str(notifyResin)
    except (Exception, psycopg2.Error) as error:
        print(error)
        return "<@"+str(userId)+">"+"'s data failed to update."