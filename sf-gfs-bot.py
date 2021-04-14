import discord
from discord.ext import commands
import pymongo
from pymongo import MongoClient
import urllib.parse
import dns
from tabulate import tabulate
import json
from datetime import datetime
from typing import List

token = "ODMxNDk2ODY2NjYyMzE4MDgw.YHWFzQ.lDYSnfQGIthH2r-ny0wytpUajKA"
url = "mongodb+srv://root-user:rootuser123@test.lwhri.mongodb.net/test"

client = discord.Client()
bot = commands.Bot(command_prefix="-")

try:
    cluster = MongoClient(url)
    print("DB Connected successfully")
except:
    print("Could not connect to MongoDB")

db = cluster['sf']
collection = db['raider']

@bot.event
async def on_ready():
    print("Bot ready")#сообщение о готовности

@bot.command()
#todo table format
async def info(ctx):
  embed = discord.Embed()
  embed.add_field(name=str("Commands:"), value="- newadd name flask stone - Создать баланс для нового игрока. Первый аргумент - количесво фласок, второй аргумент - количество камней. Если не вносятся камни или фласки, то указывается 0 значение для соответствующего столбца. \n-sadd name stone - Добавить камни для игрока. \n-fadd name flask - Добавить фласки для игрока. \nДля команд -fadd и -sadd доступны отрицательные значения. \n-abal - Показать общий баланс. \n-rbal name - Показать баланс игрока. \n-rt name name name... - Списать фласки и камни за рт.")
  await ctx.send(embed=embed)


@bot.command()
async def abal(ctx):
  table=[["Ник","Фласки","Камни","Последнее изменение"]]
  for x in collection.find():
    table.append([x["name"],int(x["flask"]),float(x["stone"]),x["upd_date"].strftime("%m/%d/%Y")])      
  await ctx.send(f'>\n{tabulate(table)}')

@bot.command()
async def rbal(ctx, arg1):
  embed = discord.Embed()
  raider_list = []
  for x in collection.find():
    raider_list.append(x["name"]) #формирования списка всех рейдеров
  if (arg1 in raider_list):
    raider_info = collection.find_one({"name" : arg1})
    embed.add_field(name=f'**{raider_info["name"]}**', value=f'> Фласки: {raider_info["flask"]}\n> Камни: {raider_info["stone"]}\n> Дата обновления: {raider_info["upd_date"].strftime("%m/%d/%Y")}', inline=False)
    await ctx.send(embed=embed)
  else: 
    await ctx.send(f'Игрок с ником {arg1} не найден.')


@bot.command()
@commands.has_any_role(526646708709621760)
async def newadd(ctx, arg1,
               arg2, arg3):  #добавление камней на счет arg1- ник arg2 - колво фласок arg3 - колво камней
  row = {"name": arg1, "stone": int(arg2), "flask": int(arg3), "upd_date": datetime.now()}
  collection.insert_one(row)
  await ctx.send(f'Новый игрок {arg1} добавлен в таблицу! Текущий баланс: {arg2} фласок и {arg3} камней.')


@bot.command()
@commands.has_any_role(526646708709621760)
async def fadd(ctx, arg1,
               arg2):  #добавление фласок на счет arg1- ник arg2 - колво
      raider_list = []
      for x in collection.find():
        raider_list.append(x["name"]) #формирования списка всех рейдеров
      
      if (arg1 in raider_list): #если введеный ник есть в списке - обновляем, иначе - добавляем
        x = collection.find_one({"name" : arg1})
        flask = int(x["flask"]) + int(arg2)
        old_row = {"flask": x["flask"], "upd_date": x["upd_date"]}
        new_row = {"$set": {"flask": flask, "upd_date": datetime.now()}}
        collection.update_one(old_row, new_row)
        await ctx.send(f'Баланс игрока {arg1} обновлен! Счет изменен на {arg2} фласок. Текущий баланс игрока: {flask}')
      else:
        row = {"name": arg1, "flask": int(arg2), "stone" : 0, "upd_date": datetime.now()}
        collection.insert_one(row)
        await ctx.send(f'Игрок с ником {arg1} не найден, добавлена новая запись. Текущий баланс игрока: {arg2} фласок.')


@bot.command()
@commands.has_any_role(526646708709621760)
async def sadd(ctx, arg1,
               arg2):  #добавление камней на счет arg1- ник arg2 - колво
    raider_list = []
    for x in collection.find():
      raider_list.append(x["name"]) #формирования списка всех рейдеров

    if (arg1 in raider_list): #если введеный ник есть в списке - обновляем, иначе - добавляем
        x = collection.find_one({"name" : arg1})
        stone = int(x["stone"]) + int(arg2)
        old_row = {"stone": x["stone"], "upd_date": x["upd_date"]}
        new_row = {"$set": {"stone": stone, "upd_date": datetime.now()}}
        collection.update_one(old_row, new_row)
        await ctx.send(f'Баланс игрока {arg1} обновлен! Счет изменен на {arg2} камней. Текущий баланс игрока: {stone}')
    else:
        row = {"name": arg1, "flask": 0, "stone": int(arg2), "upd_date": datetime.now()}
        collection.insert_one(row)
        await ctx.send(f'Игрок с ником {arg1} не найден, добавлена новая запись. Текущий баланс игрока: {arg2} камней.')
    

@bot.command()
@commands.has_any_role(526646708709621760)
async def rt(ctx, *, arg): #списание
  rt_list = arg.split(' ') #список игроков присутствующих на рт

  raider_list = [] #список всех игроков на балансе
  for x in collection.find():
    raider_list.append(x["name"])

  bd_list=list(set(rt_list) & set(raider_list))  #список игроков которые есть в бд и были на рт
  rt_list=list(set(rt_list) - set(raider_list)) #были на рт, но отсутствуют в бд

  if bd_list:
    update_raider_list = []
    for raider in bd_list:
      x = collection.find_one({"name" : raider})
      stone = float(x["stone"]) - float(0.25)
      flask = int(x["flask"]) - 1
      old_row = {"stone": x["stone"], "flask" : x["flask"], "upd_date" : x["upd_date"]}
      new_row = {"$set": {"flask": flask, "stone": stone, "upd_date": datetime.now()}}
      collection.update_one(old_row, new_row)
      update_raider_list.append(raider)
    await ctx.send(f'Баланс игроков {update_raider_list} обновлен.')

  if rt_list:
    add_raider_list = []
    for raider in rt_list:
      row = {"name": raider, "flask": -1, "stone": -0.25, "upd_date": datetime.now()}
      collection.insert_one(row)
      add_raider_list.append(raider)
    await ctx.send(f'{add_raider_list} отсутствуют в таблице баланса. Записи добавлены с отрицательными значениями.')  


bot.run(token)
