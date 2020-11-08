#please excuse the messy code, this is our first hackathon and we were rushed :)

#to use this bot, all you need to do is replace the bot token at the bottom of this script
#the script will automatically create two database files and one json file

import discord
from discord.ext import commands
import sqlite3
from sqlite3 import Error
import os
import json

client = commands.Bot(command_prefix = '!')
react_msgs = []

#-------------~~HELP~~-------------

client.remove_command("help")

@client.command(name = "help")
async def _help(ctx, mod = None):
    e = discord.Embed(title = "Commands", color = 0x0c85d6, inline = False)
    e.add_field(name = "`help [optional: mod]`", value = "Does this. Putting any text for the `mod` argument will also display mod commands.")
    e.add_field(name = "`create [Team Name], [optional: @Member], [optional: @Member]`", value = "Creates a new team. Optionally add up to 3 members. Put commas in between the team name and each member.")
    e.add_field(name = "`delete`", value = "Deletes your team (you have to be the owner to do this).")
    e.add_field(name = "`add [@Member]`", value = "Adds a member to your team.")
    e.add_field(name = "`leave`", value = "Leaves the team you're on")
    e.add_field(name = "`view`", value = "See your team's info (name, owner, members).")
    if mod:
        e.add_field(name = "`purge [optional: amount]`", value = "Deletes the amount specified of messages before the sent message. If not specified, deletes the message before it.")
        e.add_field(name = "`kick [@Member]`", value = "Kicks the member off the server.")
        e.add_field(name = "`ban [@Member]`", value = "Bans a member from the server.")
    await ctx.send(embed = e)

#-------------~~DATABASE~~-------------

class Database():
    def __init__(self, path):
        connection = None
        try:
            connection = sqlite3.connect(path)
            print("Connection to SQLite DB successful")
        except sqlite3.Error as e:
            print(f"The error '{e}' occurred")
        self.connection = connection

    def execute_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"The error '{e}' occurred")

    def execute_read_query(self, query):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except sqlite3.Error as e:
            print(f"The error '{e}' occurred")

if not os.path.exists("teams.db"):
    with open("teams.db", "w+") as f:
        pass

    tdb = Database("./teams.db")

    tdb.execute_query("""
    CREATE TABLE teams (
        owner   INTEGER PRIMARY KEY,
        name STRING,
        members STRING
    );
    """)
else:
    tdb = Database("./teams.db")

def owns_team(member_id):
    return len(tdb.execute_read_query(f'SELECT * from teams WHERE owner={member_id};')) != 0

def new_team(name, owner_id):
    tdb.execute_query(f'INSERT INTO teams VALUES ({owner_id}, "{name}", "");')

def delete_team(owner_id):
    tdb.execute_query(f"DELETE FROM teams WHERE owner={owner_id}")

def get_team_data(owner_id):
    return tdb.execute_read_query(f'SELECT * from teams WHERE owner={owner_id};')

def add_member(owner_id, member_id):
    tdb.execute_query(f'UPDATE teams SET members = "{str(member_id) if (s := str(get_team_data(owner_id)[0][2])) == "" else s + ", " + str(member_id)}" WHERE owner = {owner_id};')

def delete_member(owner_id, member_id):
    l = get_team_data(owner_id)[0][2].split(", ")
    l.remove(str(member_id))
    tdb.execute_query(f'UPDATE teams SET members = {", ".join(l)}')

if not os.path.exists("all_members.db"):
    with open("all_members.db", "w+") as f:
        pass

    adb = Database("./all_members.db")

    adb.execute_query("""
    CREATE TABLE all_members (
        member   INTEGER PRIMARY KEY,
        owner INTEGER
    );
    """)
else:
    adb = Database("./all_members.db")

def add_all_member(member_id, owner_id):
    adb.execute_query(f'INSERT INTO all_members VALUES ({member_id},  {owner_id});')

def delete_all_members(member_id):
    adb.execute_query(f"DELETE FROM all_members WHERE member={member_id}")

def get_all_data(member_id):
    return adb.execute_read_query(f'SELECT * from all_members WHERE member={member_id};')

#-------------~~TEAMS~~-------------

async def ask_join(ctx, member_ids, message_id):
    while True:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout = 120.0, check = lambda reaction, user: str(reaction.emoji) == "✅" and user.id in member_ids)
        except:
            return
        member_ids.remove(user.id)
        add_member(ctx.author.id, user.id)
        add_all_member(user.id, ctx.author.id)
        #await channel.edit(overwrites = {user: discord.PermissionOverwrite(read_messages=True)}.update(channel.overwrites))
        await ctx.send(f"{user.mention}, you have joined {ctx.author.mention}'s team.")
        if len(member_ids) == 0:
            return

@client.command(name = "create")
async def create(ctx, *, info):
    if owns_team(ctx.author.id):
        await ctx.send("You already own a team! To create a new one, delete the old one using the !delete command.")
        return
    if len(get_all_data(ctx.author.id)) != 0:
        await ctx.send("You are already on a team!")
        return
    if "," in info:
        name = info[:info.find(",")]
    else:
        name = info
    if not name.replace(" ", "").isalpha():
        await ctx.send("The team name must only be letters and spaces.")
        return
    name = name.strip()
    info = info[info.find(",") + 1:]
    ms = info.split(",")
    m1 = ms[0]
    try:
        m2 = ms[1]
    except IndexError:
        m2 = ""
    try:
        m3 = ms[2]
    except IndexError:
        m3 = ""
    try:
        m1 = await client.fetch_user(int("".join([l for l in m1 if l.isnumeric()])))
    except (ValueError, discord.errors.HTTPException):
        pass
    try:
        m2 = await client.fetch_user(int("".join([l for l in m2 if l.isnumeric()])))
    except (ValueError, discord.errors.HTTPException):
        pass
    try:
        m3 = await client.fetch_user(int("".join([l for l in m3 if l.isnumeric()])))
    except (ValueError, discord.errors.HTTPException):
        pass
    l = [m.id for m in [m1, m2, m3] if isinstance(m, discord.User)]
    g = ctx.guild
    overw = {
        g.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }
    c = await g.create_text_channel(name, overwrites = overw)
    new_team(name, ctx.author.id)
    if len(l) > 0:
        m = await ctx.send(f"{', '.join([m.mention for m in [m1, m2, m3] if isinstance(m, discord.User)])}, react to this message with a ✅ to join {name}.")
        await m.add_reaction("✅")
        await ask_join(ctx, l, m.id)

@client.command(name = "delete")
async def delete(ctx):
    i = get_team_data(ctx.author.id)
    if len(i) == 0:
        await ctx.send("You don't own a team.")
        return
    l = str(i[0][2]).split(", ")
    for m in l:
        delete_all_members(m)
    delete_team(ctx.author.id)
    await ctx.send(embed = discord.Embed(title = "Deleted your team.", color = 0xfa0b0b))

@client.command(name = "leave")
async def leave(ctx):
    i = get_all_data(ctx.author.id)
    if len(i) == 0:
        await ctx.send("You are not a member of a team. If you are an owner and wish to delete your team, use the `delete` command.")
        return
    o = i[0][1]
    delete_member(o, ctx.author.id)
    delete_all_members(ctx.author.id)
    await ctx.send(f"You left the team {get_team_data(i[0][1])[0][1]}.")

@client.command(name = "add")
async def add(ctx, member: discord.Member):
    m = await ctx.send(f"{member.mention}, react to this message with a ✅ to join {ctx.author.mention}'s team.")
    await m.add_reaction("✅")
    await ask_join(ctx, [member.id], m.id)

@client.command(name = "view")
async def view(ctx):
    i = get_team_data(ctx.author.id)
    if len(i) == 0:
        i = get_all_data(ctx.author.id)
        if len(i) == 0:
            await ctx.send("You are not on a team!")
            return
        i = get_team_data(i[0][1])
    i = i[0]
    e = discord.Embed(title = i[1], color = (o := (await client.fetch_user(i[0]))).color).add_field(name = "Owner", value = o.display_name)
    if len((l := [(await client.fetch_user(i)).display_name for i in [int(num) for num in str(i[2]).split(', ') if num.isnumeric()]])) > 0:
        e.add_field(name = "Member" if len(l) == 1 else "Members", value = ", ".join(l))
    await ctx.send(embed = e)

#-------------~~EVENTS~~-------------

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        return
    if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        await ctx.send("You're missing a required argument.")
        return
    if isinstance(error, discord.ext.commands.errors.MemberNotFound):
        await ctx.send("Make sure you @ a valid member.")
        return
    if isinstance(error, discord.ext.commands.errors.MissingPermissions):
        await ctx.send("You don't have discord permissions to use this command.")
        return
    raise error

@client.event
async def on_ready():
    await client.change_presence(status = discord.Status.online, activity = discord.Game("!help for a list of commands."))
    print('Bot Ready')

@client.event
async def welcome(member):
    print(f'{member} has joined the server!')

@client.event
async def on_raw_reaction_add(payload):
    if payload.message_id == 774683512509956136 and payload.emoji.id == 713477730007515211 and payload.member.top_role.id == 774666371933405184:
        await payload.member.add_roles(payload.member.guild.get_role(ROLE_ID))

#-------------~~COMMANDS~~-------------

@client.command(name = "purge")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount = 1):
    if round(amount) >= 1:
        await ctx.channel.purge(limit = amount + 1,)
    else:
        await ctx.channel.purge(limit = 1)
    await ctx.send("Deleted " + str(amount) + " messages!")

@client.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason = None):
    await member.send(f"You have been kicked!\nReason: {reason}")
    await member.kick(reason=reason)
    await ctx.send(f'Kicked {member.mention}')

@client.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member : discord.Member, *, reason = None):
    await member.send(f"You have been banned!\nReason: {reason}")
    await member.ban(reason = reason)
    await ctx.send(f'Banned {member.mention}')



#LAST MINUTE STUFF




if not os.path.exists("users.json"):
    with open("users.json", "w+") as f:
        json.dump({}, f)

@client.event
async def on_member_join(member):
    with open('users.json', 'r') as f:
        users = json.load(f)

    await update_data(users, member)

    with open('users.json', 'w') as f:
        json.dump(users, f)
    await client.get_channel(774666371933405187).send(f'Welcome to the official discord server for hackPHS Hackathon {member.mention}!\n\nHead over to <#774666371933405187> to claim your roles.')


@client.event
async def on_message(message):
    await client.process_commands(message)
    with open('users.json', 'r') as f:
        users = json.load(f)

    await update_data(users, message.author)
    await add_experience(users, message.author, 10)
    await level_up(users, message.author, message.channel)

    with open('users.json', 'w') as f:
        json.dump(users, f)

async def update_data(users, user):
    if not user.id in users:
        users[user.id] = {}
        users[user.id]['experience'] = 0
        users[user.id]['level'] = 1

async def add_experience(users, user, exp):
    users[user.id]['experience'] += exp

async def level_up(user, users, channel):
    experience = users[user.id]['experience']
    lvl_start = users[user.id]['level']
    lvl_end = int(experience ** (1/4))

    if lvl_start < lvl_end:
        await client.send_message(channel, '{} has leveled up to level {}'.format(user.mention, lvl_end))
        users[user.id]['level'] = lvl_end

#-------------~~SCHEDULE~~-------------

client.run("Nzc1MDIyMDMzNzAzNTM0NjE0.X6gRhA.AOHjvci9I5-hsFlbdMDw65F3PSA")
