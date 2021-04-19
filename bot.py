#required packages
import telebot
from telebot import types
import requests
import os
import json
import dns.resolver#Config vars
from pytube import Playlist ,YouTube
import re


with open("config.json") as f:
 token = json.load(f)#initialise bot
 bot = telebot.TeleBot(token["telegramToken"])
 x = bot.get_me()

PORT = int(os.environ.get('PORT','5000'))

async def delete_webhook(self):
    """delete Telegram webhook.
    This method will try to request a deletion of current webhook to make
    new getUpdates request possible and avoid this error : Conflict: can't use getUpdates 
    method while webhook is active; 
    """
    _LOGGER.debug("Sending deleteWebhook request to Telegram")
    async with aiohttp.ClientSession() as session:
        resp = await session.get(self.build_url("deleteWebhook"))

        if resp.status != 200:
            _LOGGER.error("Unable to connect")
            _LOGGER.error("Telegram error %s, %s", resp.status, resp.text)
        else:
            _LOGGER.debug("Telegram webhook deleted")
            json = await resp.json()
            _LOGGER.debug(json)

async def _get_messages(self):
    async with aiohttp.ClientSession() as session:
        data = {}
        if self.latest_update is not None:
            data["offset"] = self.latest_update
        resp = await session.get(self.build_url("getUpdates"),
                                 params=data)
                                 
        #Conflict: can't use getUpdates method while webhook is active
        if resp.status == 409:
            _LOGGER.info("Can't use getUpdates method because previous webhook is still active")
            await self.delete_webhook()
            resp = await session.get(self.build_url("getUpdates"), params=data)
            
        if resp.status != 200:
            _LOGGER.error("Telegram error %s, %s", resp.status, resp.text)
            self.listening = False

        else:
            json = await resp.json()

            await self._parse_message(json)
                
#handling commands - /start
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
 username = message.chat.first_name
 bot.send_message(message.chat.id, "Welcome "+ username+ ", feel free to use this bot")
 
 
@bot.message_handler(commands=["say"])
def send_say(message):
 talk = bot.send_message(message.chat.id, "What do you want to me to say ")
 bot.register_next_step_handler(talk, send_repeat)
 
def send_repeat(message):
 bot.send_message(message.chat.id , message.text)


@bot.message_handler(commands=["dns"])
def send_record(message):
 #target = str(input("Enter domain/ip >> "))
 #markup = types.Reply(selective=False)
 target = bot.send_message(message.chat.id, "Enter domain/ip: ")
 bot.register_next_step_handler(target, send_rec)
#bot.reply_text(message.chat.id, message.text)
#bot.send_message(message.text)
def send_rec(message):
 #bot.send_message(message.chat.id , message.text)

 d = dns.resolver.query(message.text,"A",raise_on_no_answer=False)
 if d.rrset is not None:
   bot.send_message(message.chat.id, d.rrset)


@bot.message_handler(commands=["dplay"])
def send_video(message):   
 video = bot.send_message(message.chat.id, "Enter Playlist url: ")
 bot.register_next_step_handler(video, send_url)
def send_url(message):
 playlist = Playlist(message.text)
 playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
 bot.send_message(message.chat.id, f'Found {len(playlist.video_urls)} Video')
 bot.send_message(message.chat.id, f'Downloading: {playlist.title} Playlist')
 for vid in playlist.video_urls[:]:
  url = YouTube(vid)
  link = url.streams.first()
  if link.filesize >= 52428800:
   bot.send_message(message.chat.id, f'Sorry, This video is bigger than 50MB , {vid}       Here is its link if you want to download it manually')
   continue
  else:
   bot.send_message(message.chat.id, f'Downloading: {url.title}')
   linko = link.download()
   linkoo = open(linko, 'rb')
   bot.send_document(message.chat.id, linkoo )
 
 
 
 #markup = types.ForceReply(selective=False)
 #markup = types.ReplyKeyboardMarkup()
 #itembtna = types.KeyboardButton('a')
 #itembtnv = types.KeyboardButton('v')
 #itembtnc = types.KeyboardButton('c')
 #itembtnd = types.KeyboardButton('d')
 #itembtne = types.KeyboardButton('e')
 #markup.row(itembtna, itembtnv)
 #markup.row(itembtnc, itembtnd, itembtne)
 #bot.send_message(message.chat.id, "Choose one letter:", reply_markup=markup)

#handling commands - /motivate
@bot.message_handler(commands=["motivate"])
def send_quotes(message):
 quote= requests.request(url="https://api.quotable.io/random",method='get')
 bot.reply_to(message, quote.json()["content"]) 



bot.remove_webhook()
print(x)
#pool~start the bot

bot.polling()

