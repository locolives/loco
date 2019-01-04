import discord
import json

from config import config

client = discord.Client()


try:
    users = json.load(open("usersave.json"))
except:
    print("COULDNT LOAD USERSAVE.JSON!!!\n"*10)
    users = {}


try:
    showStock = json.load(open("showStock.json"))
else:
    showStock = {
        "Loco": 0
        }

def createusers():
    for member in client.get_all_members():
        if not member.id in users:
            users[member.id] = {
                "points": 0,
                "statistics": {
                    "lives": {
                        "Loco": 0
                        },
                    "commands": 0,
                    "payments": {
                        "payments": 0,
                        "points": 0
                        }
                    }
                }


def saveusers():
    json.dump(users, open("usersave.json", "w+"))
    

@client.event
async def on_ready():
    print("Connected as "+client.user.name)
    createusers()


@client.event
async def on_message():
    msg = message.content[1:].split()
    channel = message.channel
    author = message.author

    isAdmin = author.id in ("453245427542786058", "257606762998267905")

    if message.content.startswith(config["botPrefix"]):

        user = users[author.id]
        botchannel = client.get_channel("506967406703542283")
        lifebot = botchannel.server.get_member("447716887225171988")

        if msg[0] == "loco":
            user["statistics"]["commands"] += 1
            if len(msg) < 2:
                await client.send_message(channel, "Usage: ``%s%s referral1 referral2 <amount>``")
                return
            
            if user["points"] <= 0:
                await client.send_message(channel, "Sorry, you have no points left!")

            if msg[-1].isdigit():
                amount = int(msg[-1])
                referrals = msg[1:-1]
            else:
                amount = 1
                referrals = msg[1:]

            pointsneeded = len(referrals)*amount
            if user["points"]-pointsneeded < 0:
                await client.send_message(channel, "Sorry, you don't have enough points!")
                return

            user["points"] -= pointsneeded
            generatingmsg = await client.send_message(channel, "Generating %s lives for %s..."%(amount, ", ".join(referrals)))
            commandmsg = await client.send_message(botchannel, "+loco %s %s"%(amount, ", ".join(referrals)))

            botresponse = await client.wait_for_message(channel=botchannel, author=lifebot)
            while True:
                await asyncio.sleep(1)
                botresponse = await client.get_message(botchannel, botresponse.id)
                if "doesn't exist" in botresponse.content:
                    user["points"] += pointsneeded
                    await client.edit_message(generatingmsg, botresponse.content)
                    break

                elif "Generated" in botresponse.content:
                    await client.edit_message(generatingmsg, "Generated %s lives for %s!"%(amount, ", ".join(referrals)))
                    break

            saveusers()


        elif msg[0] == "setstock" and isAdmin:
            msg[1] = msg[1].lower()
            if msg[1] == "loco":
                showStock["Loco"] = int(msg[2])
                await client.send_message(channel, "Changed!")
                json.dump(showStock, open("showStock.json", "w+"))



        elif msg[0] in ("buy", "purchase", "pay"):
            await client.send_message(author, "Hello %s,\nthank you for using this command!\nHow much points would you like to purchase?"%ctx.message.author.name)
            await client.say("**Okay, I sent you a DM {}!**".format(author.mention))

            amount = None
            while not amount:
                message = await client.wait_for_message(author=ctx.message.author)
                content = message.content.lower()
                if content.startswith(".buy"):
                    return

                if message.channel == channel:
                    if content.isdigit() and int(content):
                        amount = int(content)
                        price = amount*3

                        await client.send_message(userName, "The price will be ₹%s. Is that okay?"%price)
                        message = await client.wait_for_message(author=ctx.message.author)
                        content = message.content.lower()
                        if content.startswith(".buy"):
                            return

                        if message.channel == channel:
                            if not "y" in content:
                                amount = None
                                await client.send_message(userName, "Okay, how much points do you need?")
                    else:
                        await client.send_message(userName, "This is not a valid amount of points! How much points do you want?")


            await client.send_message(userName, "To confirm your payment, I need to know your PayTM phone number that I know it's you. Please type in your PayTM phone number. For example:\n1234567890\nor\n12XXXX7890")

            phonenumber = None
            while not phonenumber:
                message = await client.wait_for_message(author=ctx.message.author)
                content = message.content.lower()
                if content.startswith(".buy"):
                    return

                if message.channel == channel:
                    if content.startswith("+91"):
                        content = content[3:]
                    num = content[:2]+content[6:]
                    if num.isdigit() and len(num) > 4:
                        phonenumber = content
                    else:
                        await client.send_message(userName, "This is not a valid phone number! Please type it again!")

            waitmessage = await client.send_message(userName, "Creating your payment...")

            
            payment = requests.post(
                "http://188.68.36.239:52050/paytm/create",
                json={
                    "amount": price,
                    "number": phonenumber
                    },
                headers={"authorization": "453245427542786058|datriviagoooiithatplaysloco9832hfn"}
                ).json()

            with open('points.json', 'r') as f:
                users = json.load(f)
                
            if "paymentId" in payment:
                users[userName.id]["payment"] = {
                    "amount": amount,
                    "toPay": price,
                    "number": phonenumber,
                    "created": time.time(),
                    "paymentId": payment["paymentId"]
                    }

            else:
                await client.edit_message(
                    waitmessage,
                    "Oh no, something went wrong!"
                    )
                return

            await client.edit_message(
                waitmessage,
                "**Please send ₹%s using the following QR code:**\n%s"%(
                    price,
                    payment["QRCode"]
                    )
                )

            await client.send_message(
                client.get_channel("512307725003390987"),
                "Created payment for <@%s> (%s#%s, %s): %s"%(
                    userName.id,
                    userName.name,
                    userName.discriminator,
                    userName.id,
                    users[userName.id]["payment"]
                    )
                )
