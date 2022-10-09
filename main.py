from posixpath import split
from create_database import *
from utilities.functions import *
from datetime import datetime, timezone
from dateutil import tz
import genshinstats as gs
import discord
from dotenv import load_dotenv
import os

client = discord.Client()

load_dotenv()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.wait_until_ready()
    await checkDate(client)

@client.event
async def on_message(message):
    split_message = message.content.split(' ')
    if message.author == client.user:
        return
    #instruction
    if split_message[0] == '!help':
      if len(split_message) == 1:
        await message.channel.send(
          "!add <ltoken> <ltuid> or !add <discordID> <ltoken> <ltuid> - Add your data to the database to claim daily reward.\n"+
          "!update <ltoken> <ltuid> - Update your data in the database.\n"+
          "!claim - Claim your own daily reward.\n"+
          "!claimAll - Claim everyone's daily reward in all servers.\n"+
          "!delete - Delete your data in the database.\n"+
          "!updateUID <UID> - Add your UID to the database to check resin.\n"+
          "!checkResin - Checks your resin only if you have UID.\n"+
          "!notify <number of resin> - Notify if your resin has reached the number. Default is 150.")
    #!claim
    if split_message[0] == '!claim':
      if len(split_message) == 1:
        userData = await getUser(message.author.id)
        try:
          desc = await claim(client, userData[0],userData[1],userData[2], userData[3])
          await message.channel.send(embed=await sendEmbed(desc))
        except (Exception, psycopg2.Error) as error:
          print(error)
          await message.channel.send("User does not exist.")
    #claim all
    if split_message[0] == '!claimAll':
      if len(split_message) == 1:
        await claim_all(client)
    #!add <ltoken> <ltuid>
    if split_message[0] == '!add':
      if len(split_message) == 3:
        try:
          gs.set_cookie(ltoken=split_message[1], ltuid=split_message[2])
          gs.claim_daily_reward() #verify
          await checkGuildExist(message)
          await message.channel.send(await insertDataToUserTable(message.author, message.author.id, split_message[1], split_message[2], message.channel.id))
        except:
          await message.channel.send("Either ltoken or ltuid is incorrect.")
      elif len(split_message) == 4:
        try:
          gs.set_cookie(ltoken=split_message[2], ltuid=split_message[3])
          gs.claim_daily_reward() #verify
          await checkGuildExist(message)
          await message.channel.send(await insertDataToUserTable(await client.fetch_user(split_message[1]), split_message[1], split_message[2], split_message[3], message.channel.id))
        except (Exception, psycopg2.Error) as error:
          print(error)
          await message.channel.send("Either ltoken or ltuid is incorrect.")
    #update <ltoken> <ltuid>
    if split_message[0] == '!update':
      if len(split_message) > 2:
        try:
          gs.set_cookie(ltoken=split_message[1], ltuid=split_message[2])
          gs.claim_daily_reward() #verify
          await message.channel.send(await updateUserData(message.author, message.author.id, split_message[1], split_message[2], message.channel.id))
        except:
          await message.channel.send("Either ltoken or ltuid is incorrect.")
    #delete
    if split_message[0] == '!delete':
      if len(split_message) == 1:
        await message.channel.send(await removeUserData(message.author, message.author.id))
    #!updateUID <UID>
    if split_message[0] == '!updateUID':
      if len(split_message) == 2:
        try:
          userData = await getUser(message.author.id)
          gs.set_cookie(ltuid=int(f.decrypt(str(userData[2]).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(userData[1]).encode("utf-8")).decode("utf-8"))) #verify
          gs.get_notes(split_message[1])
          await message.channel.send(await setUID(split_message[1], message.author.id))
        except Exception as e:
          await message.channel.send("UID is invalid or hoyolab account is privated.")
          print(e)
    #!checkResin
    if split_message[0] == '!checkResin':
      if len(split_message) == 1:
        try:
          userData = await getUser(message.author.id)
          gs.set_cookie(ltuid=int(f.decrypt(str(userData[2]).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(userData[1]).encode("utf-8")).decode("utf-8"))) #verify
          currResin = gs.get_notes(f.decrypt(str(await getUID(message.author.id)).encode("utf-8")).decode("utf-8"))['resin']
          await message.channel.send(f"{await client.fetch_user(message.author.id)} - {currResin}/160 Resin")
        except Exception as e:
          print(e)
          await message.channel.send("Either no UID or UID is invalid. Please update your UID using !updateUID <UID>")
    #!notify <number of resin>
    if split_message[0] == '!notify':
      if len(split_message) >= 1:
        try:
          userData = await getUser(message.author.id)
          if len(split_message) == 1:
            resinCap = 150
          else:
            resinCap = split_message[1]
          if int(resinCap) >= 0 and int(resinCap) <= 160:
            gs.set_cookie(ltuid=int(f.decrypt(str(userData[2]).encode("utf-8")).decode("utf-8")), ltoken=str(f.decrypt(str(userData[1]).encode("utf-8")).decode("utf-8"))) #verify
            await message.channel.send(await updateNotify(resinCap, str(userData[0])))
          else:
            await message.channel.send("Please enter a valid number from 0 to 160")
        except Exception as e:
          print(e)
          await message.channel.send("No user exist")
    if split_message[0] == '!restart':
      if len(split_message) == 1:
        try:
          if message.author.id == 528802955831410690:
            app1.restart()
            app2.restart()
            await message.channel.send("Bot restarted.")
          else:
            await message.channel.send("You are not authorized.")
        except Exception as e:
          print(e)
client.loop.create_task(autoClaimAll(client))
client.loop.create_task(autoNotifyAll(client))
client.run(os.environ['DISCORD_TOKEN'])