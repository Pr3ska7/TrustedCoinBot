import discord
from discord.ext import commands
import json
import random
import os

# 🔁 Replace these with your actual Discord channel/role IDs
GAMBLE_CHANNEL_ID = 1378311139904983070
BALANCE_CHANNEL_ID = 1378311068417265797
LEADERBOARD_CHANNEL_ID = 1378310946753089607

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

data_file = "user_data.json"

def load_data():
    if not os.path.exists(data_file):
        with open(data_file, "w") as f:
            json.dump({}, f)
    with open(data_file, "r") as f:
        return json.load(f)

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()
    user_id = str(message.author.id)

    if user_id not in data:
        data[user_id] = {"messages": 0, "trusted_coins": 0}

    data[user_id]["messages"] += 1

    if data[user_id]["messages"] >= 100:
        data[user_id]["trusted_coins"] += 1
        data[user_id]["messages"] = 0
        await message.channel.send(f"{message.author.mention} earned 1 Trusted Coin! 🎉")

    save_data(data)

    if data[user_id]["trusted_coins"] >= 50:
        role = discord.utils.get(message.guild.roles, name="CanRedeem")
        if role and role not in message.author.roles:
            await message.author.add_roles(role)
            await message.channel.send(f"{message.author.mention} has 50+ coins and got the `CanRedeem` role!")

    await bot.process_commands(message)

@bot.command()
async def balance(ctx):
    if ctx.channel.id != BALANCE_CHANNEL_ID:
        await ctx.send("❌ Use this in the #check-balance channel.")
        return

    data = load_data()
    user_id = str(ctx.author.id)
    coins = data.get(user_id, {}).get("trusted_coins", 0)
    await ctx.send(f"{ctx.author.mention}, you have {coins} Trusted Coins.")

@bot.command()
async def gamble(ctx, amount: int):
    if ctx.channel.id != GAMBLE_CHANNEL_ID:
        await ctx.send("❌ Use this in the #trusted-gamble channel.")
        return

    data = load_data()
    user_id = str(ctx.author.id)

    if user_id not in data or data[user_id]["trusted_coins"] < amount:
        await ctx.send("❌ You don't have enough Trusted Coins.")
        return

    result = random.choice(["win", "lose"])

    if result == "win":
        data[user_id]["trusted_coins"] += amount
        await ctx.send(f"🎉 You won! Now you have {data[user_id]['trusted_coins']} Trusted Coins.")
    else:
        data[user_id]["trusted_coins"] -= amount
        await ctx.send(f"💀 You lost! Now you have {data[user_id]['trusted_coins']} Trusted Coins.")

    save_data(data)

@bot.command()
async def addcoins(ctx, member: discord.Member, amount: int):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("❌ Only the server owner can use this.")
        return

    data = load_data()
    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = {"messages": 0, "trusted_coins": 0}

    data[user_id]["trusted_coins"] += amount
    save_data(data)

    await ctx.send(f"✅ Added {amount} Trusted Coins to {member.mention}.")

@bot.command()
async def leaderboard(ctx):
    if ctx.channel.id != LEADERBOARD_CHANNEL_ID:
        await ctx.send("❌ Use this in the #leaderboard channel.")
        return

    data = load_data()
    top = sorted(data.items(), key=lambda x: x[1]["trusted_coins"], reverse=True)[:10]
    msg = "**🏆 Trusted Coin Leaderboard 🏆**\n"
    for i, (uid, stats) in enumerate(top, 1):
        member = ctx.guild.get_member(int(uid))
        if member:
            msg += f"{i}. {member.display_name}: {stats['trusted_coins']} coins\n"
    await ctx.send(msg)

# 🟢 Start the bot using your secret token from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
