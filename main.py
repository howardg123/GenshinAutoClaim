# bot.py
from create_database import *
from datetime import datetime, timezone
from dateutil import tz
import genshinstats as gs
import discord
import asyncio

client = discord.Client()

async def sendEmbed(message):
  embed = discord.Embed(title="Daily Rewards", description=message, color=0x3CA45C)
  embed.set_thumbnail(url=img)
  now = datetime.now()
  t_now = str(now.replace(tzinfo=timezone.utc).astimezone(tz.gettz('Asia/Hong_Kong')).strftime('%d/%m/%Y at %X'))
  embed.set_footer(text=t_now, icon_url='https://theclick.gg/wp-content/uploads/2022/02/hoyoverse-new-brand-genshin.jpg')
  return embed

async def claim(userId, ltoken, ltuid, guildId):
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

async def claim_all():
  try:
    #loop through all guilds
    channels = await getAllGuild()
    for currChannel in channels:
      channel = client.get_channel(id=currChannel)
      #get all users from guild
      user = await getUsersFromGuild(currChannel)
      message = ""
      try:
        for x in range(len(user)):
          message = message + await claim(user[x]['name'],user[x]['ltoken'],user[x]['ltuid'], currChannel) + "\n"
        if len(message) > 0:
          await channel.send(embed=await sendEmbed(message))
        else:
          #remove channel in database if empty
          await removeGuildData(currChannel)
      except:
        print("error in claim_all loop user")
        await asyncio.sleep(15)
  except Exception as e:
    print("error in claim_all looping through guild")
    print(e)
    await asyncio.sleep(15)


async def autoClaimAll():
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
          channel = client.get_channel(id=currChannel)
          #get all users from guild
          user = await getUsersFromGuild(currChannel)
          message = ""
          for x in range(len(user)):
            message = message + await claim(user[x]['name'],user[x]['ltoken'],user[x]['ltuid'], currChannel) + "\n"
          if len(message) > 0:
            await channel.send(embed=await sendEmbed(message))
          else:
            #remove channel in database if empty
            await removeGuildData(currChannel)
        await asyncio.sleep(3600)
        #Restart dyno if 1:00AM
        if proclist1['worker'].quantity == 1:
          app1.restart()
        elif proclist2['worker'].quantity == 1:
          app2.restart()
      await asyncio.sleep(30)
  except Exception as e:
    print("Error in autoClaimAll")
    print(e)
    channel = client.get_channel(id=911650646653034504)
    myID = '<@528802955831410690>'
    await channel.send('%s, please restart the server' % myID)
    await asyncio.sleep(15)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.wait_until_ready()
    #schedule
    now = datetime.now()
    day = now.replace(tzinfo=timezone.utc).astimezone(tz.gettz('Asia/Hong_Kong')).strftime('%d')
    switched = 0
    if int(day) == 15 and proclist1['worker'].quantity == 1:
        #open server 2 close server 1
        await channel.send('Switching to server 2.')
        app2.process_formation()['worker'].scale(1)
        app1.process_formation()['worker'].scale(0)
        switched = 1
    elif int(day) == 1 and proclist2['worker'].quantity == 1:
        #open server 1 close server 2
        print("@@@")
        print(channel)
        await channel.send('Switching to server 1.')
        app1.process_formation()['worker'].scale(1)
        app2.process_formation()['worker'].scale(0)
        switched = 1
    if proclist1['worker'].quantity == 1 and int(day) == 1 and switched == 0:
      await channel.send('Server 1 is up.')
    elif proclist2['worker'].quantity == 1 and int(day) == 15 and switched == 0:
      await channel.send('Server 2 is up.')

@client.event
async def on_message(message):
    split_message = message.content.split(' ')
    if message.author == client.user:
        return
    #instruction
    if split_message[0] == '!help':
      if len(split_message) == 1:
        instruction = "!add <ltoken> <ltuid> - Add your data to the database to claim daily reward.\n!update <ltoken> <ltuid> - Update your data in the database.\n!claim - Claim your own daily reward.\n!claimAll - Claim everyone's daily reward in all servers.\n!delete - Delete your data in the database.\n!updateUID <UID> - Add your UID to the database to check resin.\n!checkResin - Checks your resin only if you have UID."
        await message.channel.send(instruction)
    #!claim <user>
    if split_message[0] == '!claim':
      if len(split_message) == 1:
        userId = message.author.id
        userData = await getUser(userId)
        try:
          desc = await claim(userData[0],userData[1],userData[2], userData[3])
          await message.channel.send(embed=await sendEmbed(desc))
        except (Exception, psycopg2.Error) as error:
          print(error)
          await message.channel.send("User does not exist.")
    #claim all
    if split_message[0] == '!claimAll':
      if len(split_message) == 1:
        userId = message.author.id
        userData = await getUser(userId)
        await claim_all()
    #!add <ltoken> <ltuid>
    if split_message[0] == '!add':
      if len(split_message) == 3:
        userId = message.author.id
        guildId = message.channel.id
        userName = message.author
        #verify
        try:
          gs.set_cookie(ltoken=split_message[1], ltuid=split_message[2])
          gs.claim_daily_reward()
          #if new guild
          if await getGuild(guildId) is None:
            await insertDataToGuildTable(guildId)
          await message.channel.send(await insertDataToUserTable(userName, userId, split_message[1], split_message[2], guildId))
        except:
          await message.channel.send("Either ltoken or ltuid is incorrect.")
      elif len(split_message) == 4:
        userId = split_message[1]
        ltoken = split_message[2]
        ltuid = split_message[3]
        userName = await client.fetch_user(userId)
        guildId = message.channel.id
        #verify
        try:
          gs.set_cookie(ltoken=ltoken, ltuid=ltuid)
          gs.claim_daily_reward()
          #if new guild
          if await getGuild(guildId) is None:
            await insertDataToGuildTable(guildId)
          await message.channel.send(await insertDataToUserTable(userName, userId, ltoken, ltuid, guildId))
        except (Exception, psycopg2.Error) as error:
          print(error)
          await message.channel.send("Either ltoken or ltuid is incorrect.")
        
    #update <ltoken> <ltuid>
    if split_message[0] == '!update':
      if len(split_message) > 2:
        userId = message.author.id
        guildId = message.channel.id
        userName = message.author
        #verify
        try:
          gs.set_cookie(ltoken=split_message[1], ltuid=split_message[2])
          gs.claim_daily_reward()
          await message.channel.send(await updateUserData(userName, userId, split_message[1], split_message[2], guildId))
        except:
          await message.channel.send("Either ltoken or ltuid is incorrect.")
    #delete
    if split_message[0] == '!delete':
      if len(split_message) == 1:
        userId = message.author.id
        userName = message.author
        await message.channel.send(await removeUserData(userName, userId))
    #!updateUID <UID>
    if split_message[0] == '!updateUID':
      if len(split_message) == 2:
        userId = message.author.id
        #verify
        try:
          userData = await getUser(userId)
          gs.set_cookie(ltuid=int(f.decrypt(str(userData[2]).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(userData[1]).encode("utf-8")).decode("utf-8")))
          gs.get_notes(split_message[1])
          await message.channel.send(await setUID(split_message[1], userId))
        except Exception as e:
          await message.channel.send("UID is invalid.")
          print(e)
    #!checkResin
    if split_message[0] == '!checkResin':
      if len(split_message) == 1:
        userId = message.author.id
        #verify
        try:
          userData = await getUser(userId)
          userName = await client.fetch_user(userId)
          gs.set_cookie(ltuid=int(f.decrypt(str(userData[2]).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(userData[1]).encode("utf-8")).decode("utf-8")))
          currResin = gs.get_notes(f.decrypt(str(await getUID(userId)).encode("utf-8")).decode("utf-8"))['resin']
          await message.channel.send(f"{userName} - {currResin}/160 Resin")
        except Exception as e:
          print(e)
          await message.channel.send("Either no UID or UID is invalid.")
client.loop.create_task(autoClaimAll())
client.run(os.environ['DISCORD_TOKEN'])