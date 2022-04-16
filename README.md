# GenshinAutoClaim
## Install libraries
pip install -r requirements.txt
## Config vars
DATABASE_URL - Database url of heroku's add-on postgres
DISCORD_TOKEN - Discord bot token
HEROKU1_KEY - 1st heroku key
HEROKU2_KEY - 2nd heroku key (To switch server every 15th day of the month)
SECRET_KEY - SECRET for encryption
## Create table for your database
use the function createGuildTable(), and createUserTable() of create_database.py
## Run main
