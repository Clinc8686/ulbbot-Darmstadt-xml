# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from bs4 import BeautifulSoup
import re
from urllib.request import urlopen
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from lxml import etree as ET, html
from lxml.html.soupparser import fromstring
import lxml.html
import requests

API_TOKEN = 'TOKEN'
bot = telebot.TeleBot(API_TOKEN)
call = None

def SearchResult(url, message):
    #List searchresult and selection
    global result
    pageContent = requests.get(url)
    tree = html.fromstring(pageContent.content)
    link = ET.tostring(tree).decode()

    resulthead = tree.xpath('//div[@class="resulthead"]/h3/text()')
    try:
        resulthead[0]
        bot.send_message(message.chat.id, "Bitte gib einen möglichen Suchbegriff ein, der auch keine Sonderzeichen beinhaltet. 🙄")
        return
    except:
        result = re.findall('<div class=\"result recordId\" id=\"recordHEB(.+?)\">', link)
        name = tree.xpath("//div[@class='span-7']/div[@class='resultItemLine1']/a/text()")

        global forward, backward
        handoff = tree.xpath('//a[@title="next page"]/text()')
        leadback = tree.xpath('//a[@title="previous page"]/text()')

        try:
            handoff[0]
            forward = True
        except:
            forward = False
        try:
            leadback[0]
            backward = True
        except:
            backward = False

        if call != None:
            message = call.message

        KeyboardResult(name, message)

##Searchresut & forward/backward button
def KeyboardResult(name, message):
    markup = InlineKeyboardMarkup()
    x = 0
    y = 1
    for i in name:
        i = i.replace("\n","").replace("  ","")
        markup.add(InlineKeyboardButton(str(str(y) + ": " + i), callback_data=result[x]))
        x+=1
        y+=1
    if forward == True:
        markup.add(InlineKeyboardButton("Weiter ⏩ ", callback_data="forward"))
    if backward == True:
        markup.add(InlineKeyboardButton("Zurück ⏪ ", callback_data="backward"))
    bot.send_message(message.chat.id, "Bitte wähle ein Ergebnis aus", reply_markup=markup)

#Edit/filter choosed result 
def ChoosedSearch(link, call, site):
    #Ausgewähltes Ergebis öffnen
    pageContent = requests.get("https://hds.hebis.de/ulbda/Record/HEB" + link)
    tree = html.fromstring(pageContent.content)

    pageContent = requests.get("http://daia.hebis.de/ulb_darmstadt?id=" + link)
    tree2 = html.fromstring(pageContent.content)

    #Filter out informations
    name = tree.xpath("//tr[@class='coreTitle']/td/a/text()")
    author = tree.xpath("//tr[@class='coreMainAuthor']/td/div/div/div/a/text()")
    released = tree.xpath("//tr[@class='corePublished']/td/text()")
    media = tree.xpath("//tr[@valign='top']/td/span/text()")
    signatur = tree2.xpath("//label/text()")
    location = tree2.xpath("//storage/text()")
#    comment = tree2.xpath("//message/text()")

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Zurück zu den Suchergebnissen ↩ ", callback_data="search"))
    markup.add(InlineKeyboardButton("Neue Suche starten 🆕 🔎", callback_data="newsearch"))

    if name[0]:
        info = str("*Vollständiger Name:* " + name[0] + "\n")
        try:
            info = str(info + ("*Medium:* " + media[0]))
            if media[0] == "Buch":
                info = str(info + " 📕" + "\n")
            elif media[0] == "Ebook":
                info = str(info + " 📲" + "\n")
            elif media[0] == "Artikel":
                info = str(info + " 📄" + "\n")
            elif media[0] == "Zeitschrift, Zeitung":
                info = str(info + " 📰" + "\n")
            elif media[0] == "Schriftenreihe, Mehrbändiges Werk":
                info = str(info + " 📚" + "\n")
            elif media[0] == "Noten":
                info = str(info + " 🎶" + "\n")
            elif media[0] == "Karte":
                info = str(info + " 🗺" + "\n")
            else:
                info = str(info + "\n")
        except:
            pass
        try:
            info = str(info + ("📝 *Autor:* " + author[0] + "\n"))
        except:
            pass
        try:
            info = str(info + ("📢 *Veröffentlicht:* " + released[0].replace("  ","").replace("\n"," ") + "\n"))
        except:
            pass
        try:
            info = str(info + ("📍 *Standort:* " + location[0] + "\n"))
        except:
            pass
        try:
            info = str(info + ("🔖 *Signatur:* " + signatur[0] + "\n"))
        except:
            pass
        try:
            if status[0] == "verfügbar":
                info = str(info + ("*Status:* ✔" + status[0] + "\n"))
            elif status[0] == "ausgeliehen":
                 info = str(info + ("*Status:* ❌" + status[0] + "\n"))
            elif status[0] == "nur vor Ort benutzbar":
                 info = str(info + ("*Status:* ☑" + status[0] + "\n"))
        except:
            pass
        bot.send_message(call.message.chat.id, str(info), parse_mode= 'Markdown', reply_markup=markup)

#Start search query on website
def openpage(call, site, searchitem):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "%s Seite wird geöffnet..." % site)
    SearchResult(str("https://hds.hebis.de/ulbda/Search/Results?lookfor=" + searchitem.replace(" ","+")+"&type=allfields&filters=on&view=list&page=") + str(site), call.message)

