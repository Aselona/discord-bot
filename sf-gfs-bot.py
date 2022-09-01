import discord
from discord.ext import commands
import sqlite3
import urllib.parse
from tabulate import tabulate
import json
from datetime import datetime
from typing import List
import random
import requests

#token = "" #test
token = "" #prod

client = discord.Client()
bot = commands.Bot(command_prefix="-")

@bot.event
async def on_ready():
    print("Bot ready")#сообщение о готовности

@bot.command()
#todo table format
async def info(ctx):
  embed = discord.Embed(color=0x3399FF)
  embed.add_field(name=str("Управление списком баланса:"), value="-rnew name(main) flask stone - Создать баланс для нового игрока. \n-rupd name(main) flask stone - Обновить (добавить к текущим значениям) баланс игрока. \n-rdel name(main) - Удалить баланс игрока. \n\nДля команд -rnew и -rupd допускаются отрицательные значения. Если не вносятся камни или фласки, то указывается 0 значение для соответствующего столбца.", inline=False)
  embed.add_field(name=str("Управление балансом:"), value="-sadd name(main) stone - Добавить камни для игрока. \n-fadd name(main) flask - Добавить фласки для игрока. \n-rt name(main) name(main) - Списать фласки и камни за рт. \n-rtlog log_id - Списать фласки и камни за рт по логам. \n\nДля команд -fadd и -sadd допускаются отрицательные значения.", inline=False)
  embed.add_field(name=str("Просмотр баланса:"), value="-rbal name(main or alt) - Показать баланс конкретного игрока. \n-abal - Показать баланс всех игроков.", inline=False)
  embed.add_field(name=str("Управление списком альтов:"), value="\n-anew name(alt) name(main) - Добавить игрока в таблицу альтов. \n-aupd old_main new_main - Заменить мейна у игрока. \n-adel name(alt) - Удалить конкретную запись с альтом. \n-mdel name(main) - Удалить все записи альтов по нику мейна. \n\nПри выполнении команды -aupd обновление будет произведено для всего списка альтов относящихся к конкретному мейну", inline=False)
  embed.add_field(name=str("Просмотр списка альтов:"), value="-amain - Показать список альтов и мейнов. \n-allraiders log_id - Показать список игроков по логам.", inline=False)
  embed.add_field(name=str("Ролл:"), value="-roll - Рандомное число от 1 до 100. \n-roll number - Рандомное число от 1 до number", inline=False)
  await ctx.send(embed=embed)

@bot.command()
async def roll(ctx, *arg):
  embed = discord.Embed()
  if arg:
    roll = random.randint(1,int(*arg))
    number = ''.join(arg)
    embed.add_field(name=str("Random:"), value=f"{ctx.author.display_name} выбрасывает {roll} (1-{number})")
    await ctx.send(embed=embed)
  else:
    roll = random.randint(1,100)
    embed.add_field(name=str("Random:"), value=f"{ctx.author.display_name} выбрасывает {roll} (1-100)")
    await ctx.send(embed=embed)

#raider
#[0] - id
#[1] - name
#[2] - flask
#[3] - stone
#[4] - upd_date

#raider_alt
#[0] - id
#[1] - alt_name
#[2] - main_name

@bot.command()
async def abal(ctx):
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")
  sqlite_select_query = """SELECT * from raider"""
  cursor.execute(sqlite_select_query)
  records = cursor.fetchall()
  cursor.close() 

  table=[["Ник","Фласки","Камни","Последнее изменение"]]
  for x in records:
    cr_date = datetime.strptime(x[4], '%Y-%m-%d %H:%M:%S.%f')
    cr_date = cr_date.strftime("%d.%m.%Y")
    table.append([x[1],int(x[2]),float(x[3]), cr_date])
  await ctx.send(f'\n{"```" + tabulate(table)+ "```"}')

@bot.command()
async def amain(ctx):
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")
    
  sqlite_select_query = """SELECT * from raider_alt ORDER BY main_name ASC"""
  cursor.execute(sqlite_select_query)
  records = cursor.fetchall()
  cursor.close() 

  table=[["Альт","Мейн"]]
  for x in records:
    table.append([x[1], x[2]])
  await ctx.send(f'\n{"```" + tabulate(table) + "```"}')

@bot.command()
@commands.has_any_role(526646708709621760)
async def anew(ctx, arg1,
               arg2):  #добавить игрока в таблицу
  embed = discord.Embed(color=0xBDFF7D)
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")

  record = []
  insert_varible_into_table_alt(str(arg1), str(arg2))

  try:
    sql_select_query = """select * from raider_alt where alt_name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record = cursor.fetchall() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (newalt)")
  if record:
    for x in record:
      embed.add_field(name=f'Игрок {arg1} добавлен в таблицу альтов!', value=f'\n Ник альта: {x[1]} \nНик мейна: {x[2]}', inline=False)
  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def aupd(ctx, arg1,
               arg2):  #редактировать таблицу альтов arg1 - текущий ник мейна, arg2 - новый мейн
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")

  old_record = []
  try:
    sql_select_query = """select * from raider_alt where main_name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    old_record = cursor.fetchall() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (updalt1)")
  if old_record:
    for x in old_record:
      update_varible_into_table_alt(int(x[0]), str(arg2))
    
    record = []
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_select_query = """select * from raider_alt where main_name = ?"""
        cursor.execute(sql_select_query, (arg2,))
        record = cursor.fetchone()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (updalt2)")
    if record:
      embed = discord.Embed(color=0xFFBD7D)
      embed.add_field(name=f'Запись игрока {arg1} обновлена в таблице альтов!', value=f'\nСписок альтов обновлен. \nНовый ник мейна: {record[2]}', inline=False)
    
    balance_main = []
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_select_query = """select * from raider where name = ?"""
        cursor.execute(sql_select_query, (arg1,))
        balance_main = cursor.fetchall() 
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (updalt3)")
    if balance_main:
        for x in balance_main:
            update_varible_into_table_bal_changemain(int(x[0]), str(arg2))
            
        new_bal_main = []
        try:
            sqlite_connection = sqlite3.connect('sf-rt.db')
            cursor = sqlite_connection.cursor()
            sql_select_query = """select * from raider where name = ?"""
            cursor.execute(sql_select_query, (arg2,))
            new_bal_main = cursor.fetchone() 
            cursor.close()
        except sqlite3.Error:
            print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (updalt4)")

        if new_bal_main:
          embed.add_field(name=f'Запись игрока {arg1} найдена и обновлена в таблице баланса!', value=f'\nНовый ник мейна: {new_bal_main[1]}', inline=False)
    else: 
        embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице баланса. Возможно, мейн записан под другим именем.')
  else:
    embed.add_field(name=f'Запись отсутствует в таблице альтов:',  value=f'Мейн с ником {arg1} не найден.')

  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def adel(ctx, arg1):  #удалить контретную запись из таблицы по нику альта
  embed = discord.Embed(color=0xFF7D7E)
  record_ck = []
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider_alt where alt_name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record_ck = cursor.fetchone() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (altdel)")
  
  if record_ck:
    delete_sqlite_record_alt(arg1)
    record = []
    try:
      sqlite_connection = sqlite3.connect('sf-rt.db')
      cursor = sqlite_connection.cursor()
      sql_select_query = """select * from raider_alt where alt_name = ?"""
      cursor.execute(sql_select_query, (arg1,))
      record = cursor.fetchone() #формирования списка всех рейдеров
      cursor.close()
    except sqlite3.Error:
          print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (altdel)")
    if not record:
      embed.add_field(name=f'Изменение таблицы альтов:', value=f'Альт {arg1} удален из таблицы!', inline=False)
  else:
    embed.add_field(name=f'Запись отсутствует в таблице альтов:',  value=f'Альт с ником {arg1} не найден.')
  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def mdel(ctx, arg1):  #удалить всех альтов из таблицы по нику мейна
  embed = discord.Embed(color=0xFF7D7E)
  record_ck = []
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider_alt where main_name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record_ck = cursor.fetchone() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (altdel)")

  if record_ck:
    delete_sqlite_record_main(arg1)
    record = []
    try:
      sqlite_connection = sqlite3.connect('sf-rt.db')
      cursor = sqlite_connection.cursor()
      sql_select_query = """select * from raider_alt where main_name = ?"""
      cursor.execute(sql_select_query, (arg1,))
      record = cursor.fetchall() #формирования списка всех рейдеров
      cursor.close()
    except sqlite3.Error:
          print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (maindel)")
    if not record:
      embed.add_field(name=f'Изменение таблицы альтов:', value=f'Все персонажи игрока {arg1} удалены из таблицы!', inline=False)
  else:
     embed.add_field(name=f'Запись отсутствует в таблице альтов:',  value=f'Альты игрока {arg1} не найдены.')
  await ctx.send(embed=embed)

@bot.command()
async def rbal(ctx, arg1):
  embed = discord.Embed(color=0x3399FF)
  raider = []
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider_alt where alt_name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    raider = cursor.fetchone() #поиск ника в списке альтов
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (rbal)")
  if raider:
    record = []
    sql_select_query = """select * from raider where name = ?"""
    cursor.execute(sql_select_query, (raider[2],))
    record = cursor.fetchall() 
    if record:
      for x in record:
        upd_date = datetime.strptime(x[4], '%Y-%m-%d %H:%M:%S.%f')
        upd_date = upd_date.strftime("%d.%m.%Y")
        if arg1 == x[1]:
          embed.add_field(name=f'**{x[1]}**', value=f'> Фласки: {x[2]}\n> Камни: {x[3]}\n> Дата обновления: {upd_date}', inline=False)
        else:
          embed.add_field(name=f'**{arg1} (мейн: {raider[2]})**', value=f'> Фласки: {x[2]}\n> Камни: {x[3]}\n> Дата обновления: {upd_date}', inline=False)
    else:
      embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице. Возможно, мейн записан под другим именем.')
  else:
    embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице.')
  await ctx.send(embed=embed)
  cursor.close()

@bot.command()
@commands.has_any_role(526646708709621760)
async def rnew(ctx, arg1,
               arg2, arg3):  #добавить игрока в таблицу
  embed = discord.Embed(color=0xBDFF7D)
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")
  record = []
  add_date = datetime.now()
  insert_varible_into_table(str(arg1), int(arg2), float(arg3), add_date)

  try:
    sql_select_query = """select * from raider where name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record = cursor.fetchall() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (newr)")
  if record:
    for x in record:
      embed.add_field(name=f'Мейн {arg1} добавлен в таблицу баланса!', value=f'\n Баланс фласок: {x[2]} \nБаланс камней: {x[3]}', inline=False)
  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def rupd(ctx, arg1,
               arg2, arg3):  #обновить баланс игрока
  embed = discord.Embed(color=0xFFBD7D)
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider where name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record = cursor.fetchall() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (fadd)")
  if record:
    for x in record:
      if arg1 == x[1]:
        add_date = datetime.now()
        flask = int(x[2]) + int(arg2)
        stone = float(x[3]) + float(arg3)
        update_sqlite_table_flask(str(arg1), flask, add_date)
        update_sqlite_table_stone(str(arg1), stone, add_date)

      new_record = []
      try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_select_query = """select * from raider where name = ?"""
        cursor.execute(sql_select_query, (arg1,))
        new_record = cursor.fetchall() #формирования списка всех рейдеров
        cursor.close()
      except sqlite3.Error:
            print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (newr)")
      if new_record:
        for x in new_record:
          embed.add_field(name=f'Общий баланс мейна {arg1} обновлен!', value=f'\n Баланс фласок: {x[2]} \nБаланс камней: {x[3]}', inline=False)
  else:
    embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице.')
  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def rdel(ctx, arg1):  #удалить игрока из таблицы
  embed = discord.Embed(color=0xFF7D7E)
  record_ck = []
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider where name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record_ck = cursor.fetchone() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (rdel)")

  if record_ck:
    delete_sqlite_record(arg1)
    record = []
    try:
      sqlite_connection = sqlite3.connect('sf-rt.db')
      cursor = sqlite_connection.cursor()
      sql_select_query = """select * from raider where name = ?"""
      cursor.execute(sql_select_query, (arg1,))
      record = cursor.fetchall() #формирования списка всех рейдеров
      cursor.close()
    except sqlite3.Error:
          print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (rdel)")
    if not record:
      embed.add_field(name=f'Изменение таблицы баланса:', value=f'Мейн {arg1} удален!', inline=False)
  else:
    embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице.')
  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def fadd(ctx, arg1,
               arg2):  #добавление фласок на счет arg1- ник arg2 - колво
  embed = discord.Embed(color=0xFFBD7D)
  record = []
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider where name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record = cursor.fetchall() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (fadd)")
  if record:
    for x in record:
      if arg1 == x[1]:
        add_date = datetime.now()
        flask = int(x[2]) + int(arg2)
        update_sqlite_table_flask(str(arg1), flask, add_date)

      new_record = []
      try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_select_query = """select * from raider where name = ?"""
        cursor.execute(sql_select_query, (arg1,))
        new_record = cursor.fetchall() #формирования списка всех рейдеров
        cursor.close()
      except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (fadd 2)")
      for a in new_record:
        new_date = datetime.strptime(a[4], '%Y-%m-%d %H:%M:%S.%f')
        new_date = new_date.strftime("%d.%m.%Y")
        embed.add_field(name=f'**Баланс фласок мейна {a[1]}**', value=f'> Было: {x[2]}\n> Стало: {a[2]}\n> Дата обновления: {new_date}', inline=False)
  else:
    embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице.')
  await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(526646708709621760)
async def sadd(ctx, arg1,
               arg2):  #добавление камней на счет arg1- ник arg2 - колво
  embed = discord.Embed(color=0xFFBD7D)
  record = []
  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sql_select_query = """select * from raider where name = ?"""
    cursor.execute(sql_select_query, (arg1,))
    record = cursor.fetchall() #формирования списка всех рейдеров
    cursor.close()
  except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (sadd)")
  if record:
    for x in record:
      if arg1 == x[1]:
        add_date = datetime.now()
        stone = float(x[3]) + float(arg2)
        update_sqlite_table_stone(str(arg1), stone, add_date)

      new_record = []
      try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_select_query = """select * from raider where name = ?"""
        cursor.execute(sql_select_query, (arg1,))
        new_record = cursor.fetchall() #формирования списка всех рейдеров
        cursor.close()
      except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (sadd 2)")
      for a in new_record:
        new_date = datetime.strptime(a[4], '%Y-%m-%d %H:%M:%S.%f')
        new_date = new_date.strftime("%d.%m.%Y")
        embed.add_field(name=f'**Баланс камней мейна {a[1]}**', value=f'> Было: {x[3]}\n> Стало: {a[3]}\n> Дата обновления: {new_date}', inline=False)
  else:
    embed.add_field(name=f'Запись отсутствует в таблице баланса:', value=f'Мейн с ником {arg1} не найден в таблице.')
  await ctx.send(embed=embed)   

@bot.command()
@commands.has_any_role(526646708709621760)
async def rt(ctx, *, arg): #списание

  rt_list = arg.split(' ') #список игроков присутствующих на рт
  raider_list = []
  raider_list_name = []
  bd_list = []
  alt_list = []
  main_name_list = []
  altc_list = []
  rtc_list = []

  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")

  alt_name = []
  sqlite_select_query = """SELECT alt_name from raider_alt"""
  cursor.execute(sqlite_select_query)
  alt_name = cursor.fetchall() #список игроков присутствующих в списке альтов
  for raiders in alt_name:
    alt_list.append(raiders)
  alt_list = list(sum(alt_list, ()))
  
  for wl_name in rt_list:
    sqlite_select_query = """SELECT main_name from raider_alt where alt_name = ?"""
    cursor.execute(sqlite_select_query, (wl_name,))
    raider_list.append(cursor.fetchone())
    sqlite_connection.commit()
  cursor.close()

  main_name_list = list(filter(None, raider_list))
  main_name_list = list(sum(main_name_list, ())) #список игроков присутствующихна рт
  main_name_list = list(set(main_name_list)) #удаляются дубли

  altc_list = list(set(rt_list) - set(alt_list)) #были на рт, но отсутствуют в списке альтов

  if altc_list:
    alt_raider_list = []
    for raider in altc_list:
      alt_raider_list.append(raider)
    await ctx.send(f'{alt_raider_list} отсутствуют в таблице альтов. Добавьте игроков в таблицу с помощью -anew и повторите попопытку.')
  else:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sqlite_select_query = """SELECT * from raider"""
    cursor.execute(sqlite_select_query)
    raider_list = cursor.fetchall() #список игроков присутствующих в списке баланса
    for raiders in raider_list:
      raider_list_name.append(raiders[1])
    cursor.close()
  
    bd_list=list(set(main_name_list) & set(raider_list_name)) #были на рт и присутствуют в бд
    rtc_list=list(set(main_name_list) - set(raider_list_name)) #были на рт, но отсутствуют в бд
  
  if rtc_list:
    add_raider_list = []
    for raider in rtc_list:
      add_raider_list.append(raider)
    await ctx.send(f'{add_raider_list} отсутствуют в таблице баланса. Добавьте игроков в таблицу с помощью -rnew и повторите попопытку.')
  else:
    update_raider_list = []
    update_raider_name = []
    for raider in bd_list:
      try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_select_query = """select * from raider where name = ?"""
        cursor.execute(sql_select_query, (raider,))
        update_raider_list = cursor.fetchall() #формирования списка всех рейдеров
        cursor.close()
      except sqlite3.Error:
        print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (rt)")

      for a in update_raider_list:
        flask = int(a[2]) - 1
        stone = float(a[3]) - 0.25
        upd_date = datetime.now()

        update_sqlite_table_rt(str(a[1]), flask, stone, upd_date)
        update_raider_name.append(raider)
    if update_raider_name:
      await ctx.send(f'Баланс игроков {update_raider_name} обновлен.')

@bot.command()
@commands.has_any_role(526646708709621760)
async def rtlog(ctx, arg): #списание по id логу

  url = f'https://www.warcraftlogs.com/v1/report/fights/{arg}?api_key=ad4e11b6ead6b252930b4992f94c862f'
  response = requests.get(url)

  bd_list = []
  rt_list = []
  raider_list = []
  main_name_list = []
  raider_list_name = []
  alt_list = []
  altc_list = []
  rtc_list = []

  rt_logs_raider = response.json()['friendlies']
  for logs_raider in rt_logs_raider:
    if (logs_raider['type'] != 'NPC' and logs_raider['type'] != 'Pet'):
      rt_list.append(logs_raider['name']) #список игроков присутствующих на рт, включая возможных альтов

  try:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
  except:
    print("Could not connect to DB")

  alt_name = []
  sqlite_select_query = """SELECT alt_name from raider_alt"""
  cursor.execute(sqlite_select_query)
  alt_name = cursor.fetchall() #список игроков присутствующих в списке альтов
  for raiders in alt_name:
    alt_list.append(raiders)
  alt_list = list(sum(alt_list, ()))
  
  for wl_name in rt_list:
    sqlite_select_query = """SELECT main_name from raider_alt where alt_name = ?"""
    cursor.execute(sqlite_select_query, (wl_name,))
    raider_list.append(cursor.fetchone())
    sqlite_connection.commit()
  cursor.close()

  main_name_list = list(filter(None, raider_list))
  main_name_list = list(sum(main_name_list, ())) #список игроков присутствующихна рт
  main_name_list = list(set(main_name_list)) #удаляются дубли

  altc_list = list(set(rt_list) - set(alt_list)) #были на рт, но отсутствуют в списке альтов

  if altc_list:
    alt_raider_list = []
    for raider in altc_list:
      alt_raider_list.append(raider)
    await ctx.send(f'{alt_raider_list} отсутствуют в таблице альтов. Добавьте игроков в таблицу с помощью -anew и повторите попопытку.')
  else:
    sqlite_connection = sqlite3.connect('sf-rt.db')
    cursor = sqlite_connection.cursor()
    sqlite_select_query = """SELECT * from raider"""
    cursor.execute(sqlite_select_query)
    raider_list = cursor.fetchall() #список игроков присутствующих в списке баланса
    for raiders in raider_list:
      raider_list_name.append(raiders[1])
    cursor.close()
  
    bd_list=list(set(main_name_list) & set(raider_list_name)) #были на рт и присутствуют в бд
    rtc_list=list(set(main_name_list) - set(raider_list_name)) #были на рт, но отсутствуют в бд

    if rtc_list:
      add_raider_list = []
      for raider in rtc_list:
        add_raider_list.append(raider)
      await ctx.send(f'{add_raider_list} отсутствуют в таблице баланса. Добавьте игроков в таблицу с помощью -rnew и повторите попопытку.')
    else:
      update_raider_list = []
      update_raider_name = []
      for raider in bd_list:
        try:
          sqlite_connection = sqlite3.connect('sf-rt.db')
          cursor = sqlite_connection.cursor()
          sql_select_query = """select * from raider where name = ?"""
          cursor.execute(sql_select_query, (raider,))
          update_raider_list = cursor.fetchall() #формирования списка всех рейдеров
          cursor.close()
        except sqlite3.Error:
          print("Ошибка при работе с SQLite, поиск отсутствующих в БД значений (rt)")
        for a in update_raider_list:
          flask = int(a[2]) - 1
          stone = float(a[3]) - 0.25
          upd_date = datetime.now()

          update_sqlite_table_rt(str(a[1]), flask, stone, upd_date)
          update_raider_name.append(raider)
      if update_raider_name:
        await ctx.send(f'Баланс игроков {update_raider_name} обновлен.')

@bot.command()
async def allraiders(ctx, arg): #список игроков присутствующих на рт, включая возможных альтов

  url = f'https://www.warcraftlogs.com/v1/report/fights/{arg}?api_key=ad4e11b6ead6b252930b4992f94c862f'
  response = requests.get(url)
  rt_list = []
  rt_logs_raider = response.json()['friendlies']
  for logs_raider in rt_logs_raider:
    if (logs_raider['type'] != 'NPC' and logs_raider['type'] != 'Pet'):
      rt_list.append(logs_raider['name']) #список игроков присутствующих на рт, включая возможных альтов
  await ctx.send(f'Игроки принявшие участие в рейде: {" ".join(rt_list)}.')

# all function
def insert_varible_into_table(name, flask, stone, upd_date):
    try:
      sqlite_connection = sqlite3.connect('sf-rt.db')
      cursor = sqlite_connection.cursor()
      sqlite_insert_with_param = """INSERT INTO raider
                                (name, flask, stone, upd_date)
                                VALUES (?, ?, ?, ?);"""
      data_tuple = (name, flask, stone, upd_date)
      cursor.execute(sqlite_insert_with_param, data_tuple)
      sqlite_connection.commit()
      cursor.close()  
    except sqlite3.Error:
          print("Ошибка при работе с SQLite, добавление новой записи в БД (ins-bal)")

def insert_varible_into_table_alt(alt_name, main_name):
    try:
      sqlite_connection = sqlite3.connect('sf-rt.db')
      cursor = sqlite_connection.cursor()
      sqlite_insert_with_param = """INSERT INTO raider_alt
                                (alt_name, main_name)
                                VALUES (?, ?);"""
      data_tuple = (alt_name, main_name)
      cursor.execute(sqlite_insert_with_param, data_tuple)
      sqlite_connection.commit()
      cursor.close()  
    except sqlite3.Error:
          print("Ошибка при работе с SQLite, добавление новой записи в БД (ins-alt)")

def delete_sqlite_record_alt(alt_name):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """DELETE from raider_alt where alt_name = ?"""
        cursor.execute(sql_update_query, (alt_name, ))
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, удаление записи из БД (alt_name)")

def delete_sqlite_record_main(main_name):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """DELETE from raider_alt where main_name = ?"""
        cursor.execute(sql_update_query, (main_name, ))
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, удаление записи из БД (main_name)")

def delete_sqlite_record(name):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """DELETE from raider where name = ?"""
        cursor.execute(sql_update_query, (name, ))
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, удаление записи из БД (rdel)")

def update_varible_into_table_alt(row_id, new_main):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """Update raider_alt set main_name = ? where id = ?"""
        data = (new_main, row_id)
        cursor.execute(sql_update_query, data)
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, обновление записи (updalt)")
        
def update_varible_into_table_bal_changemain(row_id, new_main):
  try:
      sqlite_connection = sqlite3.connect('sf-rt.db')
      cursor = sqlite_connection.cursor()
      sql_update_query = """Update raider set name = ? where id = ?"""
      data = (new_main, row_id)
      cursor.execute(sql_update_query, data)
      sqlite_connection.commit()
      cursor.close()
  except sqlite3.Error:
      print("Ошибка при работе с SQLite, обновление записи (updbalmain)")

def update_sqlite_table_flask(name, flask, upd_date):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """Update raider set flask = ?, upd_date = ? where name = ?"""
        data = (flask, upd_date, name)
        cursor.execute(sql_update_query, data)
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, обновление записи (fadd)")

def update_sqlite_table_stone(name, stone, upd_date):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """Update raider set stone = ?, upd_date = ? where name = ?"""
        data = (stone, upd_date, name)
        cursor.execute(sql_update_query, data)
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, обновление записи (sadd)")

def update_sqlite_table_rt(name, flask, stone, upd_date):
    try:
        sqlite_connection = sqlite3.connect('sf-rt.db')
        cursor = sqlite_connection.cursor()
        sql_update_query = """Update raider set flask = ?, stone = ?, upd_date = ? where name = ?"""
        data = (flask, stone, upd_date, name)
        cursor.execute(sql_update_query, data)
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error:
        print("Ошибка при работе с SQLite, обновление записи (rt)")


bot.run(token)
