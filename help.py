#!/usr/bin/env python
import PySimpleGUI as sg
import io, os
import codecs
from uuid import getnode as get_mac
import pyautogui
import configparser
import psutil
import tkinter as tk
import platform
import base64
from peewee import *
import qrcode
import math
import time
import requests
import hashlib
from netifaces import interfaces, ifaddresses, AF_INET

db = SqliteDatabase('clx.db')
class Ticket(Model):
  tid = IntegerField(unique=True)
  body = TextField(default='')
  ack = TextField(default='')
  is_fixed = BooleanField(default=False)
  is_confirmed = BooleanField(default=False)
  at = CharField(default='')
  rat = CharField(default='')
  class Meta:
    database = db 

db.connect()
db.create_tables([Ticket])

root = tk.Tk()
max_width = root.winfo_screenwidth() - 200
root.destroy()
del root

config = configparser.ConfigParser()
try:
  config.read('config.ini')
  host = 'http://' + config['MAIN']['local_server']
except Exception as e:
  sg.popup('配置文件有误！')
  exit(1)

def Launcher():
  sg.theme('DarkAmber')
  contact = ''
  cell = ''
  layout = [  [sg.Text('信息科', size=(6,1), justification='center', auto_size_text=True, text_color='white'),
            sg.Button('报修', key='-HELP-', focus=False, size=(4,1))] ]
  window = sg.Window('泗泾医院报修系统', layout,
                     location=(max_width,100),
                     no_titlebar=True,
                     grab_anywhere=True,
                     keep_on_top=True,
                     element_padding=(0, 0),
                     margins=(0, 0))
  win2_active=False
  counter = 0
  while True:
    event, values = window.read(timeout=500)
    counter += 1

    to_be_fixed = (Ticket.select()
                      .where(Ticket.is_fixed == False)
                      .count())
    # if to_be_fixed > 0 and counter % 10 == 0:
      # try:
      #   # r = requests.get(host+'/poll/'+str(get_mac()), timeout=0.5).json()
      #   # for x in r:
      #   #   Ticket.update(is_fixed=True, ack= x['ack'], rat=x['rat']).where(Ticket.tid == x['_id']).execute()
      # except Exception as e:
      #   pass

    to_be_confirmed = (Ticket.select()
                      .where((Ticket.is_confirmed == False) & (Ticket.is_fixed == True))
                      .count())

    if to_be_confirmed > 0:
      if (counter % 2 == 0):
        window['-HELP-'].update(button_color=(sg.theme_text_color(),sg.theme_element_background_color()))
      else:
        window['-HELP-'].update(button_color=('black','orange'))

    if event is None:
      break
    if event == '-HELP-' and not win2_active:
      try:
        scope = ''
        scopes = ['电脑','打印机','电话']
        layoutScopes = []
        for i in range( math.ceil(len(scopes)/4) ):
          rows = []
          for j in range(4):
            idx = i*4 + j
            if (idx < len(scopes)):
              s = scopes[idx]
              rows.append(sg.Radio(s, "SCP",size=(8,1),auto_size_text=True,enable_events=True,key='scp_'+str(idx)))

          layoutScopes += [rows]
          

        win2_active = True

        if to_be_confirmed > 0:
          row = Ticket.get(Ticket.is_confirmed == False, Ticket.is_fixed == True)
          layout_ask = [[sg.Text(row.body, text_color='white', pad=(5,10))],
                        [sg.Text('时间：'+row.at, text_color='silver')]]
          layout_ack = [[sg.Text(row.ack, text_color='white', pad=(5,10))],
                        [sg.Text('时间：'+row.rat, text_color='silver')]]
          layout2 = [[sg.Frame('报修问题', layout_ask)],
                     [sg.Frame('回复内容', layout_ack)],
                     [sg.Button('确认', bind_return_key=True, font=('Verdana', 16))]]
          win2 = sg.Window('回复确认', layout2)
          while True:
            ev2, vals2 = win2.Read()
            if ev2 is None or ev2 == '确认':
              Ticket.update(is_confirmed= True).where(Ticket.tid == row.tid).execute()
              win2.close()
              win2_active = False
              break

        else:
          # img = pyautogui.screenshot()
          # img_bytes = io.BytesIO()
          # try:
          #   img.save(img_bytes, format='PNG')
          #   base64_data = codecs.encode(img_bytes.getvalue(), 'base64')
          #   base64_text = codecs.decode(base64_data, 'ascii')
          # except Exception as e:
          #   base64_text = ''
          
          layout2= [[sg.Text('报修电话...', auto_size_text=False, justification='center', text_color='black', background_color='white', key='-CALL-')],
                    [sg.Text('问题简述（电话通不通，都麻烦填一下）')],
                    [sg.In(key='-ASK-')],
                    [sg.Text('联系人姓名', text_color='white')], 
                    [sg.In(contact, key='-CONTACT-')],
                    [sg.Checkbox('自动截屏', key='-SCRN-', default=True)],
                    [sg.Button('提交', bind_return_key=True)]]
          layout2 = layoutScopes + layout2
          win2 = sg.Window('报修内容', layout2, font=('Verdana', 16))
          while True:
            ev2, vals2 = win2.Read()
            if ev2 is None:
              win2.close()
              win2_active = False
              break
            if ev2.startswith('scp_'):
              idx = int(ev2.split('_')[1])
              win2['-CALL-'](value=''.join('报修电话：1307'))
              scope = scopes[idx]

            if ev2 == '提交':
              ask = vals2['-ASK-'].strip()
              if scope == '':
                sg.popup('请选择报修范围')
                continue
              if len(ask) == 0:
                sg.popup('问题不能为空')
              elif len(ask) > 100:
                sg.popup('问题不需太长')
              else:          
                contact = vals2['-CONTACT-'].strip()
                if  vals2['-SCRN-'] is False:
                  base64_text = ''

                ip = extractIp()

                # payload = {'ip': ' '.join(ip), 'img': base64_text, 'scope': scope, 'ask': ask, 'mac': get_mac(), 'contact': contact, 'workflow_id':1, 'suggestion':'请协助提供更多信息', 'transition_id': 1}
                payload = {'title': (ip +'-' + contact + '-' + ask), 'ip': ip, 'scope': scope, 'ask': ask, 'mac': get_mac(), 'contact': contact, 'workflow_id':1, 'suggestion':'请协助提供更多信息', 'transition_id': 3}

                try:
                  timestamp = str(time.time())[:10]
                  ori_str = timestamp + 'a9964a84-680a-11ee-915f-202b20a7956c'
                  signature = hashlib.md5(ori_str.encode(encoding='utf-8')).hexdigest()

                  headers = dict(signature=signature, timestamp=timestamp, appname='client', username='root')

                  # # get
                  # get_data = dict(per_page=20, category='all')
                  # r = requests.get('http://127.0.0.1:8000/workflows/1/init_state', headers=headers, params=get_data)
                  # result = r.json()

                  # post

                  print(payload)
                  r = requests.post(host + '/api/v1.0/tickets', headers=headers, json=payload).json()

                  if (r['code']==0):
                    Ticket.create(tid=r['data']['ticket_id'], body=ask, at=r['data']['ticket_id'])

                    sg.popup_auto_close('报修成功!')

                  else:
                    sg.popup('报修失败！原因为'+r['msg'])

                  win2.close()
                  win2_active = False
                except Exception as e:
                  print(e)
                  sg.popup('服务不可用，请稍后再试！') 
        
      except Exception as e:
        print(e)
        sg.popup('服务不可用，请稍后再试！')

         
  window.close()


def extractIp():
  ip = [];
  for ifaceName in interfaces():
    addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': 'No IP addr'}])]

    print(' '.join(addresses))

    for address in addresses:
      if address.startswith("192.168"):
        ip.append(address);

  return ip[0]


if __name__ == '__main__':
  Launcher()
