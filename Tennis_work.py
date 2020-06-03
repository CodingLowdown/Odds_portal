#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 13:59:00 2020

@author: nicholaslowe
"""
from bs4 import BeautifulSoup as bs
import pandas as pd
import requests
from binascii import unhexlify
import json
import re
from datetime import datetime
import time
import os
import glob
from os import path
import csv

base_domain="https://www.oddsportal.com"
input_results='/results/#tennis'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS,
        # and places our data files in a folder relative to that temp
        # folder named as specified in the datas tuple in the spec file
        base_path = sys._MEIPASS
    except Exception:
        # sys._MEIPASS is not defined, so use the original path
        base_path = '/Users/nicholaslowe/Desktop/code/Tennis'

    return os.path.join(base_path, relative_path)

filename=resource_path('Tennis_work.py')
filepath=os.path.dirname(filename)




def session_creation():
    s= requests.session()
    headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0',
          'Accept': '*/*',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate, br',
          'x-li-lang': 'en_US',
          'x-restli-protocol-version': '2.0.0',
          'Connection': 'keep-alive',
          'Referer': 'https://www.oddsportal.com',
          'TE': 'Trailers',
          'Pragma': 'no-cache',
          'Cache-Control': 'no-cache'
                }
    
    cookies=s.cookies
    return s,headers,cookies

sessionnums=session_creation()
s=sessionnums[0]
headers=sessionnums[1]
cookies=sessionnums[2]

def get_BookMaker_Table(s,headers,cookies,base_domain,filespath):

    res6=s.get(base_domain+'/bookmakers/'
          ,headers=headers
          ,cookies=cookies)

    soup6=bs(res6.text)
    TablesMakers=soup6.find('table')
    
    BookMakers=[]
    BookMakersLinks=[]
    for tr in TablesMakers.findAll("tr"):
        trs = tr.findAll("td")
        for each in trs:
            try:
                link = each.find('a').find('span')['class'][1]
                BookMakers.append(link)
                link = each.find('a')['href']
                BookMakersLinks.append(link)
            except:
                pass
    
    
    BookMakersMap=pd.DataFrame({
            "BookMakers" : BookMakers,
            "BookMakersLinks" : BookMakersLinks
            })
    
    BookMakersMap=BookMakersMap[BookMakersMap['BookMakersLinks']!='/register/']
    BookMakersMap['Key']=BookMakersMap['BookMakers'].str.replace('l','')
    BookMakersMap['Name']=BookMakersMap['BookMakersLinks'].str.replace('/bookmaker/','').str.replace('/','')
    BookMakersMap = BookMakersMap.reset_index(drop=True)
    row = ["l16", "", '16',"bet365"]
    BookMakersMap.loc[len(BookMakersMap)] = row
    BookMakersMap.to_csv(filespath+'/BookMakersKey.csv')
    return BookMakersMap






def get_competition_links(s,headers,cookies,base_domain,input_results):
    
    res=s.get(base_domain+input_results
              ,headers=headers
              ,cookies=cookies
              )
    
    soup=bs(res.text, 'html.parser')
    
    tables=soup.find_all('table')
    ResultantTable=tables[0]
    
    
    links = []
    for tr in ResultantTable.findAll("tr"):
        trs = tr.findAll("td")
        for each in trs:
            try:
                link = each.find('a')['href']
                links.append(link)
            except:
                pass
    
    matching = [s for s in links if "tennis" in s]
    return matching
    




def get_all_tourney_years(s,headers,cookies,base_domain,url):
    testurl=base_domain+url
    res01=s.get(testurl
          ,headers=headers
          ,cookies=cookies)
    soup=bs(res01.text)
    soupYearList=soup.find_all('ul',{"class": "main-filter"})[1:]
    all_hrefs=[]
    all_years=[]
    for counts in soupYearList:
        lists=counts.find_all('a')
        for countlits in lists:
            all_hrefs.append(countlits['href'])
            all_years.append(countlits.text)
        
    YearsDF=pd.DataFrame({
            "all_hrefs" : all_hrefs,
            "all_years" : all_years
            })
    return YearsDF


def get_firstTourneyPage(s,headers,cookies,base_domain,urllink):
    
    
    res=s.get(base_domain+urllink
    ,headers=headers
          ,cookies=cookies)
    soup=bs(res.text, 'html.parser')
    try:
        TourneySurface=soup.find('body').find_all('a',{"href":urllink.replace('results/','')})[0].text.split('(')[1].split(')')[0]
    except:
        TourneySurface=''
    try:
        PrizeMoney=soup.find('body').find_all('div',{"class":"prizemoney"})[0].text.split(':')[1].replace(' ','')
    except:
        PrizeMoney=''
    
    scripts=soup.find('body').find_all('script')
    for counts in scripts:
        if 'id":' in counts.string:
            
            inputajax=counts.string.replace('\n','').replace('\t','').split('id":"')[1].split('",')[0]

    page=1         
    gamelink=s.get('https://fb.oddsportal.com/ajax-sport-country-tournament-archive/3/'+inputajax+'/X0/1/0/'+str(page)+'/'
                   ,headers=headers
              ,cookies=cookies
                   )
    
    soup2=bs(gamelink.text.replace('[^\\{]*','').replace('\\)$', '').replace('\"', "").replace('\\', "").replace(');', "").split('{s:1,d:{html:')[1].replace('},refresh:20}', ""))
      
    try:    
        pageslen=len(soup2.find('div').find_all('a'))-1
        pages=soup2.find('div').find_all('a')
        pagenum=pages[pageslen]['x-page']
    except:
        pagenum=1

    tablepull=soup2.find('table').find_all('tr')
    
    return tablepull,pagenum,inputajax,TourneySurface,PrizeMoney


def get_fullTourneyDF(s,headers,cookies,tablepull,pagenum,inputajax):
    listofgames=[]
    linktogames=[]
    tabpulllen=3
    while tabpulllen <len(tablepull):
        try:
            listofgames.append(tablepull[tabpulllen].find('a').text)
            linktogames.append(tablepull[tabpulllen].find('a').get('href'))
        except:
            tabpulllen+=1
            continue
        tabpulllen+=1
    
        
    
    testtable=pd.DataFrame({
            "listofgames" : listofgames,
            "linktogames" : linktogames
            })
    
    appendedDataframe=[]
    appendedDataframe.append(testtable)
    for panum in list(range(2,int(pagenum)+1)):
        gamelink=s.get('https://fb.oddsportal.com/ajax-sport-country-tournament-archive/3/'+inputajax+'/X0/1/0/'+str(panum)+'/'
                   ,headers=headers
              ,cookies=cookies
                   )
        
        soup2=bs(gamelink.text.replace('[^\\{]*','').replace('\\)$', '').replace('\"', "").replace('\\', "").replace(');', "").split('{s:1,d:{html:')[1].replace('},refresh:20}', ""))
        tablepull=soup2.find('table').find_all('tr')
        listofgames=[]
        linktogames=[]
        tabpulllen=3
        while tabpulllen <len(tablepull):
            try:
                listofgames.append(tablepull[tabpulllen].find('a').text)
                linktogames.append(tablepull[tabpulllen].find('a').get('href'))
            except:
                tabpulllen+=1
                continue
            tabpulllen+=1
        appendedDataframe.append(pd.DataFrame({
            "listofgames" : listofgames,
            "linktogames" : linktogames
            }))
    
    FInalTourneyGameList = pd.concat(appendedDataframe)
    NumTourneyGames=len(FInalTourneyGameList)
    FInalTourneyGameList=FInalTourneyGameList.reset_index(drop=True)
    return FInalTourneyGameList,NumTourneyGames

def get_odds_data(s,headers,cookies,base_domain,FInalTourneyGameList,TourneyGameNum):
    GameLink=FInalTourneyGameList['linktogames'].to_list()
    
    res=s.get(base_domain+GameLink[TourneyGameNum]
    ,headers=headers
              ,cookies=cookies
    )
    soup3= bs(res.text)
    regex = re.compile('.*date.*')
    try:
        datenum=soup3.find('body').find('div',{"id":"col-content"}).find('p',{"class": regex})['class'][2].split('t')[1].split('-')[0]
        MatchDate=datetime.fromtimestamp(
        int(datenum)
    ).strftime('%Y-%m-%d')
        StartDate=datetime.fromtimestamp(
        int(datenum)
    ).strftime('%H:%M:%S')
    except:
        MatchDate=''
        StartDate=''
    
    scripts=soup3.find('body').find_all('script')
    for counts in scripts:
        if 'id":' in counts.string:
            inputajax=counts.string.replace('\n','').replace('\t','').split('id":"')[1].split('",')[0]
            xhash=counts.string.replace('\n','').replace('\t','').split('xhash":"')[1].split('",')[0].split('%')
    
    xhash.remove('')


    unhash=''
    for counts in xhash:
        unhash+=str(unhexlify(counts).decode('UTF-8'))
    res4=s.get('https://fb.oddsportal.com/feed/postmatchscore/2-'+inputajax+'-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    
    GameResult= json.loads(res4.text.split("globals.jsonpCallback(\'/feed/postmatchscore/2-"+inputajax+"-"+unhash+".dat\', ")[1].replace(");", ""))
    
    
    res5=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-3-2-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res6=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-3-12-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res7=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-3-13-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res8=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-3-14-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res9=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-5-2-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res10=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-5-12-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res11=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-5-13-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res12=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-2-2-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res13=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-2-12-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res14=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-2-13-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res15=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-2-14-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res16=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-8-2-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res17=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-8-12-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res18=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-8-13-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res19=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-10-2-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res20=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-10-12-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res21=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-10-13-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    res22=s.get('https://fb.oddsportal.com/feed/match/1-2-'+inputajax+'-10-14-'+unhash+'.dat?_=1587233249604'
              ,headers=headers
              ,cookies=cookies)
    
    FullHomeAwayOdds=json.loads(res5.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-3-2-"+unhash+".dat\', ")[1].replace(");", ""))
    Set1HomeAwayOdds=json.loads(res6.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-3-12-"+unhash+".dat\', ")[1].replace(");", ""))
    Set2HomeAwayOdds=json.loads(res7.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-3-13-"+unhash+".dat\', ")[1].replace(");", ""))
    Set3HomeAwayOdds=json.loads(res8.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-3-14-"+unhash+".dat\', ")[1].replace(");", ""))
    
    FullAsianOdds=json.loads(res9.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-5-2-"+unhash+".dat\', ")[1].replace(");", ""))
    Set1AsianOdds=json.loads(res10.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-5-12-"+unhash+".dat\', ")[1].replace(");", ""))
    Set2AsianOdds=json.loads(res11.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-5-13-"+unhash+".dat\', ")[1].replace(");", ""))
    
    FullOverUnder=json.loads(res12.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-2-2-"+unhash+".dat\', ")[1].replace(");", ""))
    Set1OverUnder=json.loads(res13.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-2-12-"+unhash+".dat\', ")[1].replace(");", ""))
    Set2OverUnder=json.loads(res14.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-2-13-"+unhash+".dat\', ")[1].replace(");", ""))
    Set3OverUnder=json.loads(res15.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-2-14-"+unhash+".dat\', ")[1].replace(");", ""))
    
    FullCorrectScore=json.loads(res16.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-8-2-"+unhash+".dat\', ")[1].replace(");", ""))
    Set1CorrectScore=json.loads(res17.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-8-12-"+unhash+".dat\', ")[1].replace(");", ""))
    Set2CorrectScore=json.loads(res18.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-8-13-"+unhash+".dat\', ")[1].replace(");", ""))
    
    FullOddsEven=json.loads(res19.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-10-2-"+unhash+".dat\', ")[1].replace(");", ""))
    Set1OddsEven=json.loads(res20.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-10-12-"+unhash+".dat\', ")[1].replace(");", ""))
    Set2OddsEven=json.loads(res21.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-10-13-"+unhash+".dat\', ")[1].replace(");", ""))
    Set3OddsEven=json.loads(res22.text.split("globals.jsonpCallback(\'/feed/match/1-2-"+inputajax+"-10-14-"+unhash+".dat\', ")[1].replace(");", ""))
    
    return GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate


def odds_dataframecreation(BookMakersTable,FullHomeAwayOdds,FUll_SetNUM):
    dfappend=[]
    for numbetlines in FullHomeAwayOdds['d']['oddsdata']['back']:
        for BKmaker in FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['odds']:
            try:
                BKNAME=BookMakersTable[BookMakersTable['Key']==int(BKmaker)]['Name'].values[0]
            except:
                BKNAME=BKmaker
            try:
                ClosingFullHomeOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker][0]
            except:
                try:
                    ClosingFullHomeOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker]['1']
                except:
                    ClosingFullHomeOdds=''
            try:
                ClosingFullAwayOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker][1]
            except:
                try:
                    ClosingFullAwayOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker]['0']
                except:
                    ClosingFullAwayOdds=''
            try:
                ClosingOutcomeTiming=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    ClosingOutcomeTiming=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    ClosingOutcomeTiming=''
            try:
                OpeningFullHomeOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker][0]
            except:
                try:
                    OpeningFullHomeOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker]['1']
                except:
                    OpeningFullHomeOdds=''
            try:
                OpeningFullAwayOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker][1]
            except:
                try:
                    OpeningFullAwayOdds=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker]['0']
                except:
                    OpeningFullAwayOdds=''
            try:
                OpeningOutcomeTiming=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['opening_change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    OpeningOutcomeTiming=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['opening_change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    OpeningOutcomeTiming=''
            try:
                HomeVolume=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker][0]
            except:
                try:
                    HomeVolume=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker]['1']
                except:
                    HomeVolume=''
            try:
                AwayVolume=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker][1]
            except:
                try:
                    AwayVolume=FullHomeAwayOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker]['0']
                except:
                    AwayVolume=''
            try:
                HomeLayClosingOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker][0]
            except:
                try:
                    HomeLayClosingOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker]['1']
                except:
                    HomeLayClosingOdds=''
            try:
                AwayLayClosingOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker][1]
            except:
                try:
                    AwayLayClosingOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker]['0']
                except:
                    AwayLayClosingOdds=''
            try:
                HomeLayOpeningOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker][0]
            except:
                try:
                    HomeLayOpeningOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker]['1']
                except:
                    HomeLayOpeningOdds=''
            try:
                AwayLayOpeningOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker][1]
            except:
                try:
                    AwayLayOpeningOdds=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker]['0']
                except:
                    AwayLayOpeningOdds=''
            try:
                LayClosingTime=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    LayClosingTime=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    LayClosingTime=''
            try:
                LayOpenClosingTime=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['opening_change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    LayOpenClosingTime=datetime.fromtimestamp(int(FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['opening_change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    LayOpenClosingTime=''
            try:
                LayHomeVolume=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker][0]
            except:
                try:
                    LayHomeVolume=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker]['1']
                except:
                    LayHomeVolume=''
            try:
                LayAwayVolume=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker][1]
            except:
                try:
                    LayAwayVolume=FullHomeAwayOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker]['0']
                except:
                    LayAwayVolume=''
            
            if FUll_SetNUM=='F':
                Prepend='Full'
            elif FUll_SetNUM=='S1':
                Prepend='Set1'
            elif FUll_SetNUM=='S2':
                Prepend='Set2'
            elif FUll_SetNUM=='S3':
                Prepend='Set3'
            else:
                Prepend='Full'
            miniDF=pd.DataFrame({
                    "BKNAME" : [BKNAME],
                    Prepend+"ClosingFullHomeOdds" : [ClosingFullHomeOdds],
                    Prepend+"ClosingFullAwayOdds" : [ClosingFullAwayOdds],
                    Prepend+"ClosingOutcomeTiming" : [ClosingOutcomeTiming],
                    Prepend+"OpeningFullHomeOdds" : [OpeningFullHomeOdds],
                    Prepend+"OpeningFullAwayOdds" : [OpeningFullAwayOdds],
                    Prepend+"OpeningOutcomeTiming" : [OpeningOutcomeTiming],
                    Prepend+"HomeVolume" : [HomeVolume],
                    Prepend+"AwayVolume" : [AwayVolume],
                    Prepend+"HomeLayClosingOdds" : [HomeLayClosingOdds],
                    Prepend+"AwayLayClosingOdds" : [AwayLayClosingOdds],
                    Prepend+"HomeLayOpeningOdds" : [HomeLayOpeningOdds],
                    Prepend+"AwayLayOpeningOdds" : [AwayLayOpeningOdds],
                    Prepend+"LayClosingTime" : [LayClosingTime],
                    Prepend+"LayOpenClosingTime" : [LayOpenClosingTime],
                    Prepend+"LayHomeVolume" : [LayHomeVolume],
                    Prepend+"LayAwayVolume" : [LayAwayVolume],
                    })
            dfappend.append(miniDF)
        MiniDF=pd.concat(dfappend)
        return MiniDF

def Asian_dataframecreation(BookMakersTable,FullAsianOdds,FUll_SetNUM):
    dfappend=[]
    for numbetlines in FullAsianOdds['d']['oddsdata']['back']:
        for BKmaker in FullAsianOdds['d']['oddsdata']['back'][numbetlines]['odds']:
            try:
                BKNAME=BookMakersTable[BookMakersTable['Key']==int(BKmaker)]['Name'].values[0]
            except:
                BKNAME=BKmaker
            try:
                ClosingFullHomeAsianOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker][0]
            except:
                try:
                    ClosingFullHomeAsianOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker]['1']
                except:
                    ClosingFullHomeAsianOdds=''
            try:
                ClosingFullAwayAsianOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker][1]
            except:
                try:
                    ClosingFullAwayAsianOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['odds'][BKmaker]['0']
                except:
                    ClosingFullAwayAsianOdds=''
            try:
                ClosingOutcomeTiming=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['back'][numbetlines]['change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    ClosingOutcomeTiming=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['back'][numbetlines]['change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    ClosingOutcomeTiming=''
            try:
                OpeningFullAsianHomeOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker][0]
            except:
                try:
                    OpeningFullAsianHomeOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker]['1']
                except:
                    OpeningFullAsianHomeOdds=''
            try:
                OpeningFullAsianAwayOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker][1]
            except:
                try:
                    OpeningFullAsianAwayOdds=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['opening_odds'][BKmaker]['0']
                except:
                    OpeningFullAsianAwayOdds=''
            try:
                OpeningOutcomeTiming=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['back'][numbetlines]['opening_change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    OpeningOutcomeTiming=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['back'][numbetlines]['opening_change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    OpeningOutcomeTiming=''
            try:
                AsianHomeVolume=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker][0]
            except:
                try:
                    AsianHomeVolume=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker]['1']
                except:
                    AsianHomeVolume=''
            try:
                AsianAwayVolume=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker][1]
            except:
                try:
                    AsianAwayVolume=FullAsianOdds['d']['oddsdata']['back'][numbetlines]['volume'][BKmaker]['0']
                except:
                    AsianAwayVolume=''
            try:
                AsianHomeLayClosingOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker][0]
            except:
                try:
                    AsianHomeLayClosingOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker]['1']
                except:
                    AsianHomeLayClosingOdds=''
            try:
                AsianAwayLayClosingOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker][1]
            except:
                try:
                    AsianAwayLayClosingOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['odds'][BKmaker]['0']
                except:
                    AsianAwayLayClosingOdds=''
            try:
                AsianHomeLayOpeningOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker][0]
            except:
                try:
                    AsianHomeLayOpeningOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker]['1']
                except:
                    AsianHomeLayOpeningOdds=''
            try:
                AsianAwayLayOpeningOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker][1]
            except:
                try:
                    AsianAwayLayOpeningOdds=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['opening_odds'][BKmaker]['0']
                except:
                    AsianAwayLayOpeningOdds=''
            try:
                LayClosingTime=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    LayClosingTime=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    LayClosingTime=''
            try:
                LayOpenClosingTime=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['opening_change_time'][BKmaker][0])).strftime('%Y-%m-%d %H:%M:%S')
            except:
                try:
                    LayOpenClosingTime=datetime.fromtimestamp(int(FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['opening_change_time'][BKmaker]['1'])).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    LayOpenClosingTime=''
            try:
                LayAsianHomeVolume=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker][0]
            except:
                try:
                    LayAsianHomeVolume=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker]['1']
                except:
                    LayAsianHomeVolume=''
            try:
                LayAsianAwayVolume=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker][1]
            except:
                try:
                    LayAsianAwayVolume=FullAsianOdds['d']['oddsdata']['lay'][numbetlines]['volume'][BKmaker]['0']
                except:
                    LayAsianAwayVolume=''
            
            if FUll_SetNUM=='F':
                Prepend='Full'
            elif FUll_SetNUM=='S1':
                Prepend='Set1'
            elif FUll_SetNUM=='S2':
                Prepend='Set2'
            elif FUll_SetNUM=='S3':
                Prepend='Set3'
            else:
                Prepend='Full'
            miniDF=pd.DataFrame({
                    "BKNAME" : [BKNAME],
                    "numbetlines" : [numbetlines],
                    Prepend+"ClosingFullHomeAsianOdds" : [ClosingFullHomeAsianOdds],
                    Prepend+"ClosingFullAwayAsianOdds" : [ClosingFullAwayAsianOdds],
                    Prepend+"ClosingOutcomeTiming" : [ClosingOutcomeTiming],
                    Prepend+"OpeningFullAsianHomeOdds" : [OpeningFullAsianHomeOdds],
                    Prepend+"OpeningFullAsianAwayOdds" : [OpeningFullAsianAwayOdds],
                    Prepend+"OpeningOutcomeTiming" : [OpeningOutcomeTiming],
                    Prepend+"AsianHomeVolume" : [AsianHomeVolume],
                    Prepend+"AsianAwayVolume" : [AsianAwayVolume],
                    Prepend+"AsianHomeLayClosingOdds" : [AsianHomeLayClosingOdds],
                    Prepend+"AsianAwayLayClosingOdds" : [AsianAwayLayClosingOdds],
                    Prepend+"AsianHomeLayOpeningOdds" : [AsianHomeLayOpeningOdds],
                    Prepend+"AsianAwayLayOpeningOdds" : [AsianAwayLayOpeningOdds],
                    Prepend+"LayClosingTime" : [LayClosingTime],
                    Prepend+"LayOpenClosingTime" : [LayOpenClosingTime],
                    Prepend+"LayAsianHomeVolume" : [LayAsianHomeVolume],
                    Prepend+"LayAsianAwayVolume" : [LayAsianAwayVolume],
                    })
            dfappend.append(miniDF)
    MiniDF=pd.concat(dfappend)
    return MiniDF

def TourneyYearData(tourneyYears,lentorunery):
    urllink=tourneyYears.iloc[[lentorunery]]['all_hrefs'][lentorunery]
    TournYear=tourneyYears.iloc[[lentorunery]]['all_years'][lentorunery]
    tablepull,pagenum,inputajax,TourneySurface,PrizeMoney=get_firstTourneyPage(s,headers,cookies,base_domain,urllink)
    FInalTourneyGameList,TourneyGameNum=get_fullTourneyDF(s,headers,cookies,tablepull,pagenum,inputajax)
    if 'double' in urllink.split('/')[3]:
        Doubles='Y'
    else:
        Doubles='N'
    
    return Doubles,FInalTourneyGameList,TourneyGameNum,TourneySurface,PrizeMoney,TournYear,urllink

def Game_Odds_DataPulling_tries(s,headers,cookies,base_domain,FInalTourneyGameList,countGames):
    Game_worked='Y'
    try:
        GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate=get_odds_data(s,headers,cookies,base_domain,FInalTourneyGameList,countGames)
    except:
        try:
           time.sleep(3)
           GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate=get_odds_data(s,headers,cookies,base_domain,FInalTourneyGameList,countGames)
           print('Try1 ' + str(FInalTourneyGameList.iloc[[countGames]]['linktogames'][countGames]))
        except:
            try:
                time.sleep(10)
                GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate=get_odds_data(s,headers,cookies,base_domain,FInalTourneyGameList,countGames)
                print('Try2 ' + str(FInalTourneyGameList.iloc[[countGames]]['linktogames'][countGames]))
            except:
                print('MISSING GAME ' + str(FInalTourneyGameList.iloc[[countGames]]['linktogames'][countGames]))
                GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate = '','','','','','',''
                Game_worked='N'
    return GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate,Game_worked


def create_Game_Data(FInalTourneyGameList,GameResult,countGames,urllink,TournYear,TourneySurface,Doubles,PrizeMoney,MatchDate,StartDate):
    try:
        Players=FInalTourneyGameList.iloc[[countGames]]['listofgames'][countGames].split(' - ')
    except:
        Players=['','']
    try:
        ReportResult=bs(GameResult['d']['result']).find('strong').text
    except:
        ReportResult=''
    try:
        Result=bs(GameResult['d']['result']).find('strong').text.split(':')
    except:
        Result=['']
    try:
        if Result[0]>Result[1]:
            Winner=Players[0]
        else:
            Winner=Players[1]
    except:
        if Players[0] in Result[0]:
            Winner=Players[1]
        else:
            Winner=Players[0]
    try:
        Score=bs(GameResult['d']['result']).text.split('(')[1].split(')')[0]
    except:
        Score=''
    
    DF_OUT_Game=pd.DataFrame({
            "Country" : [urllink.split('/')[2]],
            "Tournament" : [urllink.split('/')[3]],
            "Year of Tournament" : [TournYear],
            "Tournament Surface" : [TourneySurface],
            "Doubles" : [Doubles],
            "Prize Money" :[PrizeMoney],
            "Match Day" :[MatchDate],
            "Start Time" :[StartDate],
            "Player Name 1" :[Players[0]],
            "Player Name 2" :[Players[1]],
            "Winner" : [Winner],
            "Sets" : [ReportResult],
            "Score" : [Score]
            
            })
    return DF_OUT_Game

def run_Tourneys(s,headers,cookies,base_domain,TournURL,BookMakersTable,savedFileFolder):
    print('STARTING '+TournURL)
    tourneyYears=get_all_tourney_years(s,headers,cookies,base_domain,TournURL)
    print('Got ALL YEARS '+tourneyYears)
    all_files = glob.glob(savedFileFolder + "/results/*.csv")
    for filename in all_files:
        numoffilesin=-1
        TourneyFile=filename.split('.csv')[0][:-4].split('results/')[1]
        for ind,links in enumerate(tourneyYears['all_hrefs'].to_list()):
            if TourneyFile == links.split('/')[3]:
                print('Dropping FROM RUN '+TourneyFile)
                tourneyYears=tourneyYears.drop(tourneyYears.index[ind])
    tourneyYears=tourneyYears.reset_index(drop=True)        
    for lentorunery in list(range(0,len(tourneyYears))):
        Doubles,FInalTourneyGameList,TourneyGameNum,TourneySurface,PrizeMoney,TournYear,urllink =TourneyYearData(tourneyYears,lentorunery)
        gamesDF=[]
        gamesDFAsian=[]
        gamesDFOver=[]
        gamesDFCS=[]
        gamesDFEven=[]
        #countGames=0
        #countGames=151
        for countGames in list(range(0,TourneyGameNum)):
            
            GameResult,FullHomeAwayOdds,Set1HomeAwayOdds,Set2HomeAwayOdds,Set3HomeAwayOdds,FullAsianOdds,Set1AsianOdds,Set2AsianOdds,FullOverUnder,Set1OverUnder,Set2OverUnder,Set3OverUnder,FullCorrectScore,Set1CorrectScore,Set2CorrectScore,FullOddsEven,Set1OddsEven,Set2OddsEven,Set3OddsEven,MatchDate,StartDate,Game_worked=Game_Odds_DataPulling_tries(s,headers,cookies,base_domain,FInalTourneyGameList,countGames)
            if Game_worked=='N':
                print('Failed')
                break
            
            
            DF_OUT_Game=create_Game_Data(FInalTourneyGameList,GameResult,countGames,urllink,TournYear,TourneySurface,Doubles,PrizeMoney,MatchDate,StartDate)
            print('Starting GAME ' + FInalTourneyGameList.iloc[[countGames]]['linktogames'][countGames])
            
            
            MiniDF=odds_dataframecreation(BookMakersTable,FullHomeAwayOdds,"F")
            try:
                MiniDF1=odds_dataframecreation(BookMakersTable,Set1HomeAwayOdds,"S1")
            except:
                MiniDF1=None
            try:
                MiniDF2=odds_dataframecreation(BookMakersTable,Set2HomeAwayOdds,"S2")
            except:
                MiniDF2=None
            try:
                MiniDF3=odds_dataframecreation(BookMakersTable,Set3HomeAwayOdds,"S3")
            except:
                MiniDF3=None
            if MiniDF1 is None:
                s1=MiniDF
            else:
                s1 = pd.merge(MiniDF, MiniDF1, how='left', on=['BKNAME'])
            if MiniDF2 is None:
                s2=s1
            else:
                s2 = pd.merge(s1, MiniDF2, how='left', on=['BKNAME'])  
            if MiniDF3 is None:
                MiniDFOut=s2
            else:
                MiniDFOut = pd.merge(s2, MiniDF3, how='left', on=['BKNAME'])
            
            MiniDFOut = MiniDFOut.reset_index(drop=True)
            df_repeated = pd.concat([DF_OUT_Game]*len(MiniDFOut), ignore_index=True)
            df_repeated=df_repeated.reset_index(drop=True)
            gamesDF.append(pd.concat([df_repeated,MiniDFOut], axis=1))
            
            try:
                MiniDF=Asian_dataframecreation(BookMakersTable,FullAsianOdds,"F")
            except:
                MiniDF=None
            try:
                MiniDF1=Asian_dataframecreation(BookMakersTable,Set1AsianOdds,"S1")
            except:
                MiniDF1=None
            try:
                MiniDF2=Asian_dataframecreation(BookMakersTable,Set2AsianOdds,"S2")
            except:
                MiniDF2=None
            try:
                MiniDF3=Asian_dataframecreation(BookMakersTable,Set3AsianOdds,"S3")
            except:
                MiniDF3=None
            if MiniDF1 is None:
                s1=MiniDF
            else:
                s1 = pd.merge(MiniDF, MiniDF1, how='left', on=['BKNAME','numbetlines'])
            if MiniDF2 is None:
                s2=s1
            else:
                s2 = pd.merge(s1, MiniDF2, how='left', on=['BKNAME','numbetlines'])  
            if MiniDF3 is None:
                AsianMiniDFOut=s2
            else:
                AsianMiniDFOut = pd.merge(s2, MiniDF3, how='left', on=['BKNAME','numbetlines'])
            
            try:
                
                AsianMiniDFOut = AsianMiniDFOut.reset_index(drop=True)
                
                df_repeated2 = pd.concat([DF_OUT_Game]*len(AsianMiniDFOut), ignore_index=True)
                df_repeated2=df_repeated2.reset_index(drop=True)
                gamesDFAsian.append(pd.concat([df_repeated2,AsianMiniDFOut], axis=1))
            except:
                print('MissingDataAsian')
            try:    
                MiniDF=Asian_dataframecreation(BookMakersTable,FullOverUnder,"F")
            except:
                MiniDF=None
            try:
                MiniDF1=Asian_dataframecreation(BookMakersTable,Set1OverUnder,"S1")
            except:
                MiniDF1=None
            try:
                MiniDF2=Asian_dataframecreation(BookMakersTable,Set2OverUnder,"S2")
            except:
                MiniDF2=None
            try:
                MiniDF3=Asian_dataframecreation(BookMakersTable,Set3OverUnder,"S3")
            except:
                MiniDF3=None
            if MiniDF1 is None:
                s1=MiniDF
            else:
                s1 = pd.merge(MiniDF, MiniDF1, how='left', on=['BKNAME','numbetlines'])
            if MiniDF2 is None:
                s2=s1
            else:
                s2 = pd.merge(s1, MiniDF2, how='left', on=['BKNAME','numbetlines'])  
            if MiniDF3 is None:
                OverMiniDFOut=s2
            else:
                OverMiniDFOut = pd.merge(s2, MiniDF3, how='left', on=['BKNAME','numbetlines'])
            
            try:
                
                OverMiniDFOut = OverMiniDFOut.reset_index(drop=True)
                
                df_repeated3 = pd.concat([DF_OUT_Game]*len(OverMiniDFOut), ignore_index=True)
                df_repeated3=df_repeated3.reset_index(drop=True)
                gamesDFOver.append(pd.concat([df_repeated3,OverMiniDFOut], axis=1))
            except:
                print('MissingDataOver')
            
            try:
                MiniDF=Asian_dataframecreation(BookMakersTable,FullCorrectScore,"F")
            except:
                MiniDF=None
            try:
                MiniDF1=Asian_dataframecreation(BookMakersTable,Set1CorrectScore,"S1")
            except:
                MiniDF1=None
            try:
                MiniDF2=Asian_dataframecreation(BookMakersTable,Set2CorrectScore,"S2")
            except:
                MiniDF2=None
            try:
                MiniDF3=Asian_dataframecreation(BookMakersTable,Set2CorrectScore,"S3")
            except:
                MiniDF3=None
            if MiniDF1 is None:
                s1=MiniDF
            else:
                s1 = pd.merge(MiniDF, MiniDF1, how='left', on=['BKNAME','numbetlines'])
            if MiniDF2 is None:
                s2=s1
            else:
                s2 = pd.merge(s1, MiniDF2, how='left', on=['BKNAME','numbetlines'])  
            if MiniDF3 is None:
                CSMiniDFOut=s2
            else:
                CSMiniDFOut = pd.merge(s2, MiniDF3, how='left', on=['BKNAME','numbetlines'])
            
            try:
                CSMiniDFOut = CSMiniDFOut.reset_index(drop=True)
            
                df_repeated4 = pd.concat([DF_OUT_Game]*len(CSMiniDFOut), ignore_index=True)
                df_repeated4=df_repeated4.reset_index(drop=True)
                gamesDFCS.append(pd.concat([df_repeated4,CSMiniDFOut], axis=1))
            except:
                print('MissingDataCS')
            
            try:
                MiniDF=Asian_dataframecreation(BookMakersTable,FullOddsEven,"F")
            except:
                MiniDF=None
            try:
                MiniDF1=Asian_dataframecreation(BookMakersTable,Set1OddsEven,"S1")
            except:
                MiniDF1=None
            try:
                MiniDF2=Asian_dataframecreation(BookMakersTable,Set2OddsEven,"S2")
            except:
                MiniDF2=None
            try:
                MiniDF3=Asian_dataframecreation(BookMakersTable,Set3OddsEven,"S3")
            except:
                MiniDF3=None
            if MiniDF1 is None:
                s1=MiniDF
            else:
                s1 = pd.merge(MiniDF, MiniDF1, how='left', on=['BKNAME','numbetlines'])
            if MiniDF2 is None:
                s2=s1
            else:
                s2 = pd.merge(s1, MiniDF2, how='left', on=['BKNAME','numbetlines'])  
            if MiniDF3 is None:
                EvenMiniDFOut=s2
            else:
                EvenMiniDFOut = pd.merge(s2, MiniDF3, how='left', on=['BKNAME','numbetlines'])
            
            try:
                EvenMiniDFOut = EvenMiniDFOut.reset_index(drop=True)
            
                df_repeated5 = pd.concat([DF_OUT_Game]*len(EvenMiniDFOut), ignore_index=True)
                df_repeated5=df_repeated5.reset_index(drop=True)
                gamesDFEven.append(pd.concat([df_repeated5,EvenMiniDFOut], axis=1))
            except:
                 print('MissingDataEven')
            
            
        folderpath=os.getcwd()+ "/results/"
        if not os.path.exists(folderpath):
            os.makedirs(folderpath)
        try:
            OutputGames=pd.concat(gamesDF)
            longCols=len(gamesDF[0].columns)
            ind=0
            for CountLongestCols in list(range(1,len(gamesDF))):
                if len(gamesDF[CountLongestCols].columns)>longCols:
                    ind=CountLongestCols
                    longCols=len(gamesDF[CountLongestCols].columns)
            OutputGames=OutputGames[gamesDF[ind].columns]
            OutputGames=OutputGames.reset_index(drop=True)
            OutputGames.to_csv(folderpath+OutputGames.iloc[[0]]['Tournament'][0]+OutputGames.iloc[[0]]['Year of Tournament'][0]+".csv") 
        except:
            print('HomeAwayOddsFailure')
            
            
            
            
            
        try: 
            OutputGamesAsian=pd.concat(gamesDFAsian)
            longCols=len(gamesDFAsian[0].columns)
            ind=0
            for CountLongestCols in list(range(1,len(gamesDFAsian))):
                if len(gamesDFAsian[CountLongestCols].columns)>longCols:
                    ind=CountLongestCols
                    longCols=len(gamesDFAsian[CountLongestCols].columns)
            OutputGamesAsian=OutputGamesAsian[gamesDFAsian[ind].columns]
            OutputGamesAsian=OutputGamesAsian.reset_index(drop=True)
            OutputGamesAsian.to_csv(folderpath+'Asian'+OutputGamesAsian.iloc[[0]]['Tournament'][0]+OutputGamesAsian.iloc[[0]]['Year of Tournament'][0]+".csv")  

        except:
            print('AsianFailure')
            
            
            
            
            
            
        try:   
            OutputGamesOver=pd.concat(gamesDFOver)
            longCols=len(gamesDFOver[0].columns)
            ind=0
            for CountLongestCols in list(range(1,len(gamesDFOver))):
                if len(gamesDFOver[CountLongestCols].columns)>longCols:
                    ind=CountLongestCols
                    longCols=len(gamesDFOver[CountLongestCols].columns)
            OutputGamesOver=OutputGamesOver[gamesDFOver[ind].columns]
            OutputGamesOver=OutputGamesOver.reset_index(drop=True)
            OutputGamesOver.to_csv(folderpath+'Over'+OutputGamesOver.iloc[[0]]['Tournament'][0]+OutputGamesOver.iloc[[0]]['Year of Tournament'][0]+".csv") 
          
        except:
            print('OverFailure')
            
        try:
            OutputGamesCS=pd.concat(gamesDFCS)
            longCols=len(gamesDFCS[0].columns)
            ind=0
            for CountLongestCols in list(range(1,len(gamesDFCS))):
                if len(gamesDFCS[CountLongestCols].columns)>longCols:
                    ind=CountLongestCols
                    longCols=len(gamesDFCS[CountLongestCols].columns)
            OutputGamesCS=OutputGamesCS[gamesDFCS[ind].columns]
            OutputGamesCS=OutputGamesCS.reset_index(drop=True)
            OutputGamesCS.to_csv(folderpath+'CS'+OutputGamesCS.iloc[[0]]['Tournament'][0]+OutputGamesCS.iloc[[0]]['Year of Tournament'][0]+".csv") 
        
        except:
            print('CSFailure')
            
        try:
            OutputGamesEven=pd.concat(gamesDFEven)
            longCols=len(gamesDFEven[0].columns)
            ind=0
            for CountLongestCols in list(range(1,len(gamesDFEven))):
                if len(gamesDFEven[CountLongestCols].columns)>longCols:
                    ind=CountLongestCols
                    longCols=len(gamesDFEven[CountLongestCols].columns)
            OutputGamesEven=OutputGamesEven[gamesDFEven[ind].columns]
            OutputGamesEven=OutputGamesEven.reset_index(drop=True)
            OutputGamesEven.to_csv(folderpath+'Even'+OutputGamesEven.iloc[[0]]['Tournament'][0]+OutputGamesEven.iloc[[0]]['Year of Tournament'][0]+".csv")
        except:
            print('EvenFailure')
            continue
        
        
        


def run_all_master_output(s,headers,cookies,base_domain,input_results,savedFileFolder):
    BookMakersTable=get_BookMaker_Table(s,headers,cookies,base_domain,savedFileFolder)
    CompLinks=get_competition_links(s,headers,cookies,base_domain,input_results)
    all_files = glob.glob(savedFileFolder + "/results/*.csv")
    CompLinksReduced=get_competition_links(s,headers,cookies,base_domain,input_results)
    #li2 = []
    for filename in all_files:
        numoffilesin=-1
        TourneyFile=filename.split('.csv')[0][:-4].split('results/')[1]
        for ind,links in enumerate(CompLinksReduced):
            if TourneyFile in links:
                numoffilesin=ind
                CompLinksReduced.remove(links)
    compcount =0    
    while compcount < len(CompLinksReduced):
        TournURL=CompLinksReduced[compcount]
        try:
            run_Tourneys(s,headers,cookies,base_domain,TournURL,BookMakersTable,savedFileFolder)
        except:
            time.sleep(8)
            try:
                run_Tourneys(s,headers,cookies,base_domain,TournURL,BookMakersTable,savedFileFolder)
            except:
                time.sleep(10)
                continue
        compcount+=1
                
#OutputGames=pd.concat(gamesDF)      
#OutputGames.to_csv('Wimb_final_test.csv')


# import tkinter module 
from tkinter import * 
from tkinter.ttk import *
import tkinter.messagebox
#inputsDFUpdate=pd.read_csv(filepath+'/InputsSave.csv')
# creating main tkinter window/toplevel 
master = Tk() 
#master.geometry("1000x1000")  
master.title("GUI")
# this wil create a label widget 
l1 = Label(master, text = "Sport URL") 
l2 = Label(master, text = "Tournament URLS") 
#l3 = Label(master, text = "Linkedin User Name")
#l4 = Label(master, text = "Linkedin Password") 
l0 = Label(master, text = "SAVED_FILE_LOCATION") 
# grid method to arrange labels in respective 
# rows and columns as specified 
l1.grid(row = 1, column = 0, sticky = W, pady = 2) 
l2.grid(row = 1, column = 1, sticky = W, pady = 2) 
#l3.grid(row = 1, column = 2, sticky = W, pady = 2) 
#l4.grid(row = 1, column = 3, sticky = W, pady = 2) 
l0.grid(row = 0, column = 0, sticky = W, pady = 2) 
# entry widgets, used to take entry from user

v0 = StringVar(master, value=os.getcwd())
v1 = StringVar(master, value=input_results)
v2 = StringVar(master, value="/tennis/united-kingdom/atp-wimbledon/results/")
#v3 = StringVar(master, value=inputsDFUpdate['input3'].iloc[[0]][0])
#v4 = StringVar(master, value=inputsDFUpdate['input4'].iloc[[0]][0])

e0 = Entry(master,textvariable=v0) 

e1 = Entry(master,textvariable=v1) 
e2 = Entry(master,textvariable=v2) 
#e3 = Entry(master,textvariable=v3) 
#e4 = Entry(master,textvariable=v4, show="*")


# this will arrange entry widgets 
e0.grid(row = 0, column = 1, pady = 2) 
e1.grid(row = 2, column = 0, pady = 2) 
e2.grid(row = 2, column = 1, pady = 2) 
#e3.grid(row = 2, column = 2, pady = 2) 
#e4.grid(row = 2, column = 3, pady = 2)

def setwd():
    os.chdir(e0.get())

def runFullOutput():
    setwd()
    s,headers,cookies=session_creation()
    savedFileFolder=e0.get()
    run_all_master_output(s,headers,cookies,base_domain,e1.get(),savedFileFolder)
    #tkinter.messagebox.showinfo("Done!","G Sheet Updated for "+str(e2.get()))
def BookmakersRun():
    setwd()
    s,headers,cookies=session_creation()
    get_BookMaker_Table(s,headers,cookies,base_domain,e0.get())
    #tkinter.messagebox.showinfo("Done!","G Sheet Updated for "+str(e2.get()))
def TourneyURLS():
    setwd()
    s,headers,cookies=session_creation()
    CompLinks=get_competition_links(s,headers,cookies,base_domain,e1.get())
    pd.DataFrame({
            "CompLinks" : CompLinks
            }).to_csv(e0.get()+'/'+e1.get().split('/')[-1]+'Complinks.csv')
    #tkinter.messagebox.showinfo("Done!","G Sheet Updated for "+str(e2.get()))
def TourneyRun():
    setwd()
    s,headers,cookies=session_creation()
    TournURL=e2.get()
    savedFileFolder=e0.get()
    if path.exists(e0.get()+'/BookMakersKey.csv'):
        BookMakersTable=pd.read_csv(e0.get()+'/BookMakersKey.csv')
        run_Tourneys(s,headers,cookies,base_domain,TournURL,BookMakersTable,savedFileFolder)
    else:
        BookmakersRun()
        BookMakersTable=pd.read_csv(e0.get()+'/BookMakersKey.csv')
        run_Tourneys(s,headers,cookies,base_domain,TournURL,BookMakersTable,savedFileFolder)
    #tkinter.messagebox.showinfo("Done!","G Sheet Updated for "+str(e2.get()))

def store_new_defaults():
    setwd()
    inputsDF=pd.DataFrame({
            "input0" : [e0.get()],
             "input1" : [e1.get()],
              "input2" : [e2.get()],
               
    })
    inputsDF.to_csv('InputsSave.csv')




btn1 = Button(master,text = "BookMakers Numbering", command= BookmakersRun).grid(row = 2, column = 6, pady = 2) #'fg or foreground' is for coloring the contents (buttons)
btn2 = Button(master,text = "Get Full List Of Tourney URLS", command= TourneyURLS).grid(row = 5, column = 6, pady = 2) #'fg or foreground' is for coloring the contents (buttons)
btn3 = Button(master,text = "Run Tournament URL All Years", command= TourneyRun).grid(row = 10, column = 6, pady = 2) #'fg or foreground' is for coloring the contents (buttons)
btn4 = Button(master,text = "Run Full Output (CAN TAKE WEEKS)", command= runFullOutput).grid(row = 15, column = 6, pady = 2) #'fg or foreground' is for coloring the contents (buttons)
# infinite loop which can be terminated by keyboard 
# or mouse interrupt 
mainloop() 




















