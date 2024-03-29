from create_database import *
import discord
from datetime import datetime, timezone
from dateutil import tz
import genshinstats as gs
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def checkGuildExist(message):
  if await getGuild(message.channel.id) is None:
    await insertDataToGuildTable(message.channel.id)

async def sendEmbed(message):
  embed = discord.Embed(title="Daily Rewards", description=message, color=0x3CA45C)
  embed.set_thumbnail(url=img)
  embed.set_footer(text=str(datetime.now().replace(tzinfo=timezone.utc).astimezone(tz.gettz('Asia/Hong_Kong')).strftime('%d/%m/%Y at %X')), icon_url='https://theclick.gg/wp-content/uploads/2022/02/hoyoverse-new-brand-genshin.jpg')
  return embed

async def notifyUser():
  ...

async def claim(client, userId, ltoken, ltuid, guildId):
  try:
    #verify
    verified = 0
    user = await getUsersFromGuild(guildId)
    for i in range(len(user)):
      if userId == user[i]['name']:
        verified = 1
    if verified == 1:
      userName = await client.fetch_user(userId)
      gs.set_cookie(ltuid=int(f.decrypt(str(ltuid).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(ltoken).encode("utf-8")).decode("utf-8")))
      reward = gs.claim_daily_reward()
      global img
      img = min(enumerate(gs.get_claimed_rewards()))[1]['img']
      if reward is not None:
        try:
          currResin = gs.get_notes(f.decrypt(str(await getUID(userId)).encode("utf-8")).decode("utf-8"))['resin']
          return (f"{currResin}/160 Resin | %s - {reward['cnt']}x {reward['name']}" % userName)
        except:
          return (f"%s - {reward['cnt']}x {reward['name']}" % userName)
      else:
        try:
          currResin = gs.get_notes(f.decrypt(str(await getUID(userId)).encode("utf-8")).decode("utf-8"))['resin']
          return (f"{currResin}/160 Resin | Already claimed %s" % userName)
        except:
          return (f"Already claimed %s" % userName)
    else:
      return "No existing user"
  except (Exception, psycopg2.Error) as error:
    print(error)
    return ("Error for %s" % userName)

async def claim_all(client):
  try:
    #loop through all guilds
    channels = await getAllGuild()
    for currChannel in channels:
      channel = client.get_channel(id=int(currChannel))
      #get all users from guild
      user = await getUsersFromGuild(currChannel)
      message = ""
      try:
        for x in range(len(user)):
          message = message + await claim(client, user[x]['name'],user[x]['ltoken'],user[x]['ltuid'], currChannel) + "\n"
        if len(message) > 0:
          await channel.send(embed=await sendEmbed(message))
        else:
          #remove channel in database if empty
          await removeGuildData(currChannel)
      except Exception as e:
        print(e)
        print("error in claim_all loop user")
        await asyncio.sleep(15)
  except Exception as e:
    print("error in claim_all looping through guild")
    print(e)
    await asyncio.sleep(15)

async def autoClaimAll(client):
  try:
    await client.wait_until_ready()
    # sleep until 10:00PM
    now = datetime.now()
    t_now = int(now.replace(tzinfo=timezone.utc).astimezone(tz.gettz('Asia/Hong_Kong')).strftime('%H'))
    diff = 22 - t_now
    if t_now != 0:
      await asyncio.sleep(diff*3600)
    while not client.is_closed():
      now = datetime.now()
      t_now = int(now.replace(tzinfo=timezone.utc).astimezone(tz.gettz('Asia/Hong_Kong')).strftime('%H'))
      #If time is 12:00 AM
      if t_now == 0:
        #loop through all guilds
        channels = await getAllGuild()
        for currChannel in channels:
          channel = client.get_channel(id=int(currChannel))
          #get all users from guild
          user = await getUsersFromGuild(currChannel)
          message = ""
          for x in range(len(user)):
            message = message + await claim(client, user[x]['name'],user[x]['ltoken'],user[x]['ltuid'], currChannel) + "\n"
          if len(message) > 0:
            await channel.send(embed=await sendEmbed(message))
          else:
            #remove channel in database if empty
            await removeGuildData(currChannel)
        await asyncio.sleep(3600)
        #Restart dyno if 1:00AM
        
      await asyncio.sleep(30)
  except Exception as e:
    print("Error in autoClaimAll")
    print(e)
    # channel = client.get_channel(id=int(os.environ['CHANNEL_ID']))
    # myID = '<@528802955831410690>'
    # await channel.send('%s, please restart the server' % myID)
    await asyncio.sleep(15)

async def autoNotifyAll(client):
    await client.wait_until_ready()
    notifiedList = []
    messageIDList = []
    while not client.is_closed():
      try:
        #loop through all guilds
        channels = await getAllGuild()
        for currChannel in channels:
          channel = client.get_channel(id=int(currChannel))
          #get all users from guild
          user = await getUsersFromGuild(currChannel)
          for x in range(len(user)):
            if user[x]['notify'] != None:
              gs.set_cookie(ltuid=int(f.decrypt(str(user[x]['ltuid']).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(user[x]['ltoken']).encode("utf-8")).decode("utf-8")))
              currResin = gs.get_notes(f.decrypt(str(await getUID(user[x]['name'])).encode("utf-8")).decode("utf-8"))['resin']
              if user[x]['notify'] == 'TRUE' and user[x]['name'] not in notifiedList and int(currResin) >= int(user[x]['notifyResin']):
                notifiedList.append(user[x]['name'])
                messageID = await channel.send("<@"+str(user[x]['name'])+"> Your resin is at "+ str(currResin) + "/160")
                messageIDList.append({'user': user[x]['name'], 'messageID': messageID.id})
              elif user[x]['notify'] == 'TRUE' and user[x]['name'] in notifiedList and int(currResin) < int(user[x]['notifyResin']):
                notifiedList.remove(user[x]['name'])
                messageIDList[:] = [d for d in messageIDList if d.get('user') != user[x]['name']]
              elif user[x]['notify'] == 'TRUE' and user[x]['name'] in notifiedList and int(currResin) > int(user[x]['notifyResin']):
                for userObject in messageIDList:
                  if userObject['user'] == user[x]['name']:
                    message = await channel.fetch_message(userObject['messageID'])
                    await message.edit(content="<@"+str(user[x]['name'])+"> Your resin is at "+ str(currResin) + "/160")
        await asyncio.sleep(60)
      except Exception as e:
        print("Error in autonotifyAll")
        print(e)
    await asyncio.sleep(15)