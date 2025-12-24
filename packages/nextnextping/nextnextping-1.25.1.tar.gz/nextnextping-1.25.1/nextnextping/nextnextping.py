#!/usr/bin/env python
# -*- coding: utf-8 -*-

# pyinstaller --noconsole --noconfirm nextnextping.py
#
import json
import sys
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import filedialog
import os
import threading
import time
from datetime import datetime
import subprocess
import re
import locale
import csv
from nextnextping.grammer.ttl_parser_worker import TtlPaserWolker
from nextnextping.grammer.version import VERSION
import webbrowser
import platform
import pexpect

SAMPLE_TTL = '''

;INPUT_START

;file_name = "029c1_ok_connect.ttl"
;target_display = "pingを打つ装置"
;target_ip = "127.0.0.1"
;target_type = 1  ; 1=ping, 2=traceroute, 3=show run
;base_display = "SSH接続する装置"
;base_ip = "localhost:2200"
;base_account = "foo" ; アカウント情報
;next_ssh = 2  ; "0=Windows", "1=SSHログイン", "2=SSH踏み台"
;next_display = "SSHからさらに接続する装置"
;next_ip  = "c1"  ; 踏み台SSHのIPアドレス
;next_account = "bar"  ; 踏み台先のIPアドレス

;INPUT_END
ifdefined file_name
if result == 0 then
    file_name = "build/connect_test.ttl"
endif

ifdefined target_display
if result == 0 then
    target_display = "pingを打つ装置"
endif
ifdefined target_ip
if result == 0 then
    target_ip = "127.0.0.1"
endif
ifdefined target_type
if result == 0 then
    target_type = 1  ; 1=ping, 2=traceroute, 3=show run
endif
ifdefined base_display
if result == 0 then
    base_display = "SSH接続する装置"
endif
ifdefined base_ip
if result == 0 then
    base_ip = "localhost:2200"
endif
ifdefined base_account
if result == 0 then
    base_account = "foo"
endif
ifdefined next_ssh
if result == 0 then
    next_ssh = 2
endif
ifdefined next_display
if result == 0 then
    next_display = "SSHからさらに接続する装置"
endif
ifdefined next_ip
if result == 0 then
    next_ip  = "c1"  ; 踏み台SSHのIPアドレス
endif
ifdefined next_account
if result == 0 then
    next_account = "bar"  ; 踏み台先のIPアドレス
endif

; ログファイルを設定する
log_file_name_work = file_name
strreplace log_file_name_work 1 'ttl' ''
strconcat log_file_name_work 'log'  ; 拡張子がttlでないときは replaceでlogできないので追加
; ログファイルを絶対パスに変える
getdir log_file_name
strconcat log_file_name #92
strconcat log_file_name log_file_name_work

; ログを開く
logopen log_file_name 0 0

; すでに接続されていたらエラー
testlink
if result==2  then
    messagebox "already connected" "title"
    call call_ending
    end
endif

;; ベースとなるパスワードを取得する
call call_base_password
base_password = password

; 接続する 'localhost:2200 /ssh /auth=password /user=aaa /passwd=bbb'
command = base_ip
strconcat command " /ssh /auth=password /user="
strconcat command base_account
strconcat command " /passwd="
strconcat command base_password
connect command
if result <> 2 then
    int2str strvar result
    message = "connection failer "
    strconcat message strvar
    messagebox command message
    call call_ending
    end
endif

; ttl本家側で入れないと動かないことがあった
pause 1

;
prompt = '$'
timeout = 150
state_flag = 0  ; call_get_promptのために状態フラグを設定する
command = 'clear'
call call_get_prompt  ; プロンプトを決定する

if next_ssh == 2 then
    state_flag = 1  ; call_get_promptのために状態フラグを設定する
    ; ssh 接続 'ssh account@ip'
    command = "ssh "
    strconcat command next_account
    strconcat command "@"
    strconcat command next_ip
    call call_get_prompt  ; プロンプトを決定する
endif


if server_type == 1 then  ; 1=cisco, 2=linux, 3=qx-s
    ;; cisco のときはこれで -- More -- を出さないようにする
    command = 'terminal length 0'
    call call_one_command
elseif server_type == 3 then  ; 1=cisco, 2=linux, 3=qx-s
    ;; qx-s のときはこれで -- More -- を出さないようにする
    command = 'screen-length disable'
    call call_one_command
    command = 'terminal pager offscreen-length disable'
    call call_one_command
    command = 'set terminal pager disable'
    call call_one_command
endif

; 特殊コマンドを実行する
my_command_flag = 1
ifdefined my_command_int
if result<>1 then
    my_command_flag = 0
endif
ifdefined my_command
if result<>6 then
    my_command_flag = 0
endif

;; 実コマンドの投入
if my_command_flag<>0 then
    for i   0   (my_command_int - 1)
        command = my_command[i]
        strcompare command ""
        if result<>0 then
            call call_check_command
            if result == 1 then
                call call_get_prompt
            elseif result == 2 then
                call call_sudo_command
            else
                call call_one_command
            endif
        endif
    next
elseif target_type = 1 then  ; 1=ping, 2=traceroute, 3=show run
    if server_type == 1 then ; 1=cisco, 2=linux, 3=qx-s
        command = 'ping '
    elseif server_type == 2 then
        command = 'ping -c 1 '
    else
        command = 'ping '
    endif
    strconcat command target_ip
    flushrecv
    sendln command
    wait command
    wait prompt ' 0% packet loss' ' 0.0% packet loss' 'Success rate is 100 percent'
    if result <= 1 then
        call call_ending
        end
    endif
elseif target_type = 2 then
    if server_type == 1 then ; 1=cisco, 2=linux, 3=qx-s
        command = 'traceroute '
        strconcat command target_ip
        call call_one_command
    elseif server_type == 2 then
        strcompare ']' prompt
        if result == 0 then
            ; for vmware
            strscan target_ip ':' ;; for ip v6
            if result == 0 then
                command = 'traceroute '
            else
                command = 'traceroute6 '
            endif
            strconcat command target_ip
            call call_one_command
        else
            strscan target_ip ':' ;; for ip v6
            if result == 0 then
                command = 'tracepath '
            else
                command = 'tracepath6 '
            endif
            strconcat command target_ip
            call call_one_command
        endif
    else
        command = 'traceroute '
        strconcat command target_ip
        call call_one_command
    endif
else
    if server_type == 1 then ; 1=cisco, 2=linux, 3=qx-s
        ; for cisco
        command = 'show running-config'
        call call_one_command
        command = 'show ip interface brief'
        call call_one_command
    elseif server_type == 2 then
        strcompare "]" prompt
        if result == 0 then
            ; for vmware
            command = 'esxcli network nic list'
            call call_one_command
            command = 'esxcli network vswitch standard list'
            call call_one_command
            command = 'esxcli network ip interface list'
            call call_one_command
        else
            ; for linux
            command = 'ifconfig -a'
            call call_one_command
            command = 'ip addr show'
            call call_one_command
            command = 'ip -6 addr show'
            call call_one_command
            command = 'ip link show'
            call call_one_command
            command = 'ip -6 link show'
            call call_one_command
            command = 'ip route show'
            call call_one_command
            command = 'ip -6 route show'
            call call_one_command
            command = 'ss'
            call call_one_command
        endif
    else
        ; for qx-s
        command = 'display current-configuration'
        call call_one_command
    endif
endif

; 終了処理
call call_ending

; 正常終了を通知
error=''
result = 1
end


; SSHでログインするときに使うパスワード
:call_base_password
    key_target = 'normal_'
    strconcat key_target base_account
    key_ip = base_ip
    key_base_display = base_display
    call call_pass_all
return

; SSHからSSHにさらにログインするときのパスワード
:call_base_password_enable
    key_target = 'enable_'
    strconcat key_target base_account
    key_ip = base_ip
    key_base_display = base_display
    call call_pass_all
return

; 特権ユーザのパスワード
:call_next_password
    key_target = 'normal_'
    strconcat key_target next_account
    key_ip = next_ip
    key_base_display = next_display
    call call_pass_all
return

; 特権ユーザのパスワード
:call_next_enable_password
    ; key_target = 'enable_'
    strconcat key_target next_account
    key_ip = next_ip
    key_base_display = next_display
    call call_pass_all
return

; パスワード関連まとめ
:call_pass_all
    key_ip_replace = key_ip
    strreplace key_ip_replace 1 ':' '_' ; ipv6
    strreplace key_ip_replace 1 #92'.' '_'  ; ipv4 正規表現なので単純に.を渡すと全部消える
    getdir key_data
    strconcat key_data #92
    strconcat key_data "pass_" ; パスワード保存用
    strconcat key_data key_ip_replace
    strconcat key_data '.key'
    ispassword key_data key_target  ; パスワードの有無確認
    if result == 0 then  ; 設定されていない
        message = key_target
        strconcat message "("
        strconcat message key_ip
        strconcat message ")"
        passwordbox message base_display
        password = inputstr ; パスワードを入力
        setpassword key_data key_target password  ; パスワードを設定
    else
        getpassword key_data key_target password  ; パスワードを取得
    endif
    return

    :call_ending
    testlink
    if result==2  then
        closett
        ; logclose
    endif
    result = 0
return


:call_check_command
    ; コマンドがプロンプトの変化を要求しているか確認する
    strscan command "sudo "
    if result<>0 then
        result = 2
        return
    endif
    strscan command "clear"
    if result<>0 then
        result = 1
        return
    endif
    strscan command "ssh "
    if result<>0 then
        result = 1
        return
    endif
    strscan command "quit"
    if result<>0 then
        result = 1
        return
    endif
    strscan command "exit"
    if result<>0 then
        result = 1
        return
    endif
    strscan command "system-view"
    if result<>0 then
        result = 1
        return
    endif
return


:call_one_command
    ; １コマンド分の処理
    flushrecv
    sendln command
    wait command
    if result == 0 then
        messagebox 'input command timeout failer' command
        call call_ending
        end
    endif
    ; プロントのチェックを行う
    while 1
        ;
        wait prompt '-- More --'
        if result = 0 then
            messagebox 'command is time up!' command
            call call_ending
            end
        elseif result = 2 then
            flushrecv
            sendln ''
            continue
        endif
        ;
        break
    endwhile
return

:call_get_prompt
    flushrecv
    sendln command
    wait command
    if result == 0 then
        messagebox 'input command timeout failer' command
        call call_ending
        end
    endif
    password_flag = 0
    enable_flag = 0
    while 1
        ; プロンプトチェック
        wait '>' '#' '$' ']' '(yes/no' 'assword:' '-- More --'
        result_type = result
        if result_type == 0 then
            ; タイムアウトのとき
            messagebox 'next prompt check fail!' 'title'
            call call_ending
            end
        elseif result_type == 1 then
            prompt = '>'
            if enable_flag == 0 then
                ; '>'が来たら一度だけenableを打ち、2度来たらqxモードと見なす
                server_type = 1  ; 1=cisco, 2=linux, 3=qx-s
                password_flag = 0
                enable_flag = 1
                command = 'enable'
                flushrecv
                sendln command
                wait command
                continue
            else
                server_type = 3  ; 1=cisco, 2=linux, 3=qx-s
            endif
        elseif result_type == 2 then
            server_type = 1  ; 1=cisco, 2=linux, 3=qx-s
            prompt = '#'
        elseif result_type == 3 then
            server_type = 2  ; 1=cisco, 2=linux, 3=qx-s
            prompt = '$'
        elseif result_type == 4 then
            server_type = 2  ; 1=cisco, 2=linux, 3=qx-s
            prompt = ']'  ; for vmware
        elseif result_type == 5 then
            command = 'yes'
            flushrecv
            sendln command
            wait command
            continue
        elseif result_type == 6 then
            if password_flag <> 0 then
                message = 'passdword ng!'
                messagebox message 'title'
                call call_ending
                end
            endif
            password_flag = 1
            if state_flag == 0 then
                if enable_flag<>0 then
                    call call_base_password_enable  ; 特権モード移行用
                else
                    call call_base_password
                endif
            else
                if enable_flag<>0 then
                    key_target = 'enable_'
                    call call_next_enable_password  ; 特権モード移行用
                else
                    call call_next_password
                endif
            endif
            flushrecv
            sendln password
            continue
        elseif result_type == 7 then
            flushrecv
            sendln ''
            continue
        else
            int2str strvar result_type
            message = "next promot not found("
            strconcat message strvar
            strconcat message ")"
            messagebox message 'title'
            call call_ending
            end
        endif
        ;
        ; while を終わる
        break
    endwhile
return


:call_sudo_command
    flushrecv
    sendln command
    wait command
    if result == 0 then
        messagebox 'input command timeout failer' command
        call call_ending
        end
    endif
    password_flag = 0
    while 1
        ; プロンプトチェック
        wait prompt '[sudo] password for'
        result_type = result
        if result == 0 then
            ; タイムアウトのとき
            messagebox 'next prompt check fail!' 'title'
            call call_ending
            end
        elseif result_type == 1 then
            break
        elseif result_type == 2 then
            if password_flag <> 0 then
                message = 'passdword ng!'
                messagebox message 'title'
                call call_ending
                end
            endif
            wait ':'
            if result == 0 then
                messagebox 'sudo password timeout failer' command
                call call_ending
                end
            endif
            password_flag = 1
            key_target = 'sudo_'
            call call_next_enable_password  ; 特権モード移行用
            flushrecv
            sendln password
            continue
        else
            int2str strvar result_type
            message = "sudo promot not found("
            strconcat message strvar
            strconcat message ")"
            messagebox message 'title'
            call call_ending
            end
        endif
        ;
        ; while を終わる
        break
    endwhile
return

'''


class MyTtlPaserWolker(TtlPaserWolker):
    """ パサーをオーバーライドしてgui周りの処理を行わせる """
    def __init__(self, threading, next_next_ping, log_type_param):
        self.threading = threading
        self.next_next_ping = next_next_ping
        self.log_type_param = log_type_param
        self.log_type_param['stdout'] = ""
        super().__init__()

    def setLog(self, strvar):
        """ オーバライドしてログを設定する """
        self.log_type_param['stdout'] = self.log_type_param['stdout'] + strvar

    def doLogopen(self, filename, binary_flag, append_flag,
                  plain_text_flag, timestamp_flag, hide_dialog_flag,
                  include_screen_buffer_flag, timestamp_type):
        """ open the log """
        if self.next_next_ping.init['ignore_log']:
            return  # ログを開かないようにする
        # 親を呼ぶ
        super().doLogopen(
            filename, binary_flag, append_flag,
            plain_text_flag, timestamp_flag, hide_dialog_flag,
            include_screen_buffer_flag, timestamp_type)

    def commandContext(self, name, line, data_list):
        """ GUI側で処理すべきコマンド群 """
        # print(f"commandContext {name}")
        if "passwordbox" == name:
            p1 = str(self.getData(data_list[0]))
            p2 = str(self.getData(data_list[1]))
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_password_dialog(done_event, p1, p2))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            inputstr = self.next_next_ping.result
            if inputstr is None:
                self.setValue('result', 0)
                self.setValue('inputstr', '')
            else:
                self.setValue('result', 1)
                self.setValue('inputstr', inputstr)
            return
        if "inputbox" == name:
            p1 = str(self.getData(data_list[0]))
            p2 = str(self.getData(data_list[1]))
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_inputdialog(done_event, p1, p2))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            inputstr = self.next_next_ping.result
            if inputstr is None:
                self.setValue('result', 0)
                self.setValue('inputstr', '')
            else:
                self.setValue('result', 1)
                self.setValue('inputstr', inputstr)
            return
        elif "dirnamebox" == name:
            p1 = str(self.getData(data_list[0]))
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_dirdialog(done_event, p1))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            inputstr = self.next_next_ping.result
            if inputstr is None:
                self.setValue('result', 0)
            else:
                self.setValue('result', 1)
                self.setValue('inputstr', inputstr)
            return
        elif "filenamebox" == name:
            p1 = str(self.getData(data_list[0]))
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_filedialog(done_event, p1))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            inputstr = self.next_next_ping.result
            if inputstr is None:
                self.setValue('result', 0)
            else:
                self.setValue('result', 1)
                self.setValue('inputstr', inputstr)
            return
        elif "listbox" == name:
            p1 = str(self.getData(data_list[0]))
            p2 = str(self.getData(data_list[1]))
            p3 = str(self.getKeywordName(data_list[2]))
            i = 0
            list_data = []
            while True:
                target = f"{p3}[{str(i)}]"
                # print(f"target={target}")
                if self.isValue(target):
                    list_data.append(self.getData(target))
                    i = i + 1
                else:
                    break
            if len(list_data) <= 0:
                list_data.append("None")
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_listbox_dialog(done_event, p1, p2, list_data))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            inputstr = self.next_next_ping.result
            if inputstr is None:
                # print("result is None")
                self.setValue('inputstr', -1)
            else:
                # print(f"inputstr is {inputstr}")
                self.setValue('inputstr', inputstr)
            return
        elif "messagebox" == name and not self.next_next_ping.init['ignore_messagebox']:
            p1 = str(self.getData(data_list[0]))
            p2 = str(self.getData(data_list[1]))
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_messagebox_dialog(done_event, p1, p2))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            return
        elif "yesnobox" == name:
            p1 = str(self.getData(data_list[0]))
            p2 = str(self.getData(data_list[1]))
            done_event = threading.Event()
            self.next_next_ping.root.after(
                0, lambda: self.next_next_ping.show_yesnobox_dialog(done_event, p1, p2))
            # 待ち処理
            while not self.end_flag:
                signaled = done_event.wait(timeout=1.0)
                if signaled:
                    break
            inputstr = self.next_next_ping.result
            if inputstr is None:
                self.setValue('result', 0)
            else:
                self.setValue('result', 1)
            return
        #
        #
        # 未実装のコマンド表示
        super().commandContext(name, line, data_list)
        #

    def setValue(self, x, y):
        if self.next_next_ping.init['debug']:
            self.log_type_param['stdout'] = self.log_type_param['stdout'] + f"### x={x} value={y}\r\n"
        super().setValue(x, y)

    def setTitle(self, title: str):
        """ タイトルの設定 """
        # print(f"setTitle {title}")
        self.next_next_ping.root.after(
            0, lambda: self.next_next_ping.setTitle(title))

    def getTitle(self) -> str:
        """ タイトルの取得 """
        title = self.next_next_ping.init['title']
        return title  # self.next_next_ping.title


class MyWindowsProcess():
    def __init__(self, command_next_list: str):
        self.default_locale = locale.getencoding()
        self.process = subprocess.Popen(command_next_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        #
        # 英語にしないと日本語で表示され、OK/NGが分からなくなる
        subprocess.Popen(['chcp.com', '65001'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()

    def readable(self) -> bool:
        return self.process.stdout.readable()

    def read(self, length: int) -> str:
        self.process.stdout.flush
        return self.process.stdout.read(1)

    def close(self):
        # localeをもとに戻す
        subprocess.Popen(['chcp.com', self.default_locale], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
        #
        process = self.process
        self.process = None
        if process is not None:
            try:
                process.stdout.close()
            except Exception:
                pass
            try:
                process.stderr.close()
            except Exception:
                pass
            try:
                process.terminate()
            except Exception:
                pass


class MyLinuxProcess():
    def __init__(self, shell_name: str):
        self.child = pexpect.spawn(shell_name, timeout=0, encoding='utf-8')
        self.result = None

    def readable(self) -> bool:
        child = self.child
        if child is None:
            return False
        if self.result is not None:
            return True
        index = child.expect([r".", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            self.result = child.before + child.after
            if 0 < len(self.result):
                return True
            else:
                return False
        elif index == 1:  # EOF
            self.close()
            return False
        return False  # Timeout

    def read(self, length: int) -> str:
        if self.child is None:
            return None
        work = ''
        if self.result is not None:
            if len(self.result) <= length:
                work = self.result
                self.result = None
            else:
                work = self.result[:self.result]
                self.result = self.result[self.result + 1:]
        elif self.recv_ready():
            work = self.recv(length)
        if self.child is None:
            return None
        return work

    def close(self):
        child = self.child.close()
        self.child = None
        try:
            child.close()
        except Exception:
            pass


class MyThread():
    def __init__(self):
        self.non_stop_flag = True
        self.next_next_ping = None
        self.threading = None
        self.values_values = []
        self.myTtlPaserWolker = None

    def set_therad(self, next_next_ping, threading, values_values):
        self.next_next_ping = next_next_ping
        self.threading = threading
        self.values_values = values_values

    def start(self):
        while self.non_stop_flag:
            for values in self.values_values:
                (result, date, display_name, type, command) = values
                #
                flag = False
                if type not in self.next_next_ping.log:
                    self.next_next_ping.log[type] = {}
                if command not in self.next_next_ping.log[type]:
                    self.next_next_ping.log[type][command] = {}
                self.next_next_ping.log[type][command]['stdout'] = 'unkown'
                for command_dict in self.next_next_ping.init['data']:
                    if type in command_dict['name']:
                        # hit
                        if command_dict['ttl']:
                            flag = self.ttl_result(type, command)
                            # print(f"flag={flag}")
                        else:
                            flag = self.subprocess_result(type, command_dict, command)
                        #
                        break
                #
                if flag:
                    result = "OK"
                    date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                else:
                    if result != "NG":
                        # NGになった時間を入力し、２回目NGは時間更新しない
                        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    result = "NG"
                if type not in self.next_next_ping.log:
                    self.next_next_ping.log[type] = {}
                if command not in self.next_next_ping.log[type]:
                    self.next_next_ping.log[type][command] = {}
                self.next_next_ping.log[type][command]['result'] = result
                self.next_next_ping.log[type][command]['date'] = date
                #
                self.next_next_ping.root.after(
                    0, lambda: self.next_next_ping.command_ping_threading(result, date, type, command))
                self.command_status_threading(f"{result} {display_name} ({type}) {command}")
                #
                if not self.non_stop_flag:
                    break
                # print(f"wait_time={self.next_next_ping.init['wait_time']}")
                time.sleep(self.next_next_ping.init['wait_time'])
                if not self.non_stop_flag:
                    break
            #
            # loopフラグが落ちていたら終了する
            if self.next_next_ping.init["loop"] is False:
                self.stop()
                messagebox.showinfo("Info", "ping end!")
                break

    def ttl_result(self, type, param):
        param_list = param.split(',')
        filename = param_list[0]
        param_list_next = []
        for param_list_next_list in param_list:
            param_list_next.append(param_list_next_list.strip())
        try:
            self.myTtlPaserWolker = MyTtlPaserWolker(self.threading, self.next_next_ping, self.next_next_ping.log[type][param])
        except Exception as e:
            self.myTtlPaserWolker.setLog(f"Exception create {str(e)}")
            return 0  # this is NG!
        try:
            if not os.path.isabs(filename):
                # 相対パスなので絶対パスに変換する
                base_dir = self.next_next_ping.init["setting"]
                base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
                base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
                os.chdir(base_dir)  # 起動フォルダを相対後に変更する
                filename = os.path.join(base_dir, filename)  # ファイル名を決定
            #
            self.myTtlPaserWolker.execute(filename, param_list_next)
        except Exception as e:
            self.myTtlPaserWolker.setLog(f"Exception execute {str(e)}")
            return 0  # this is NG!
        finally:
            # なにがあろうとworkerは絶対に殺す
            if self.myTtlPaserWolker is not None:
                self.myTtlPaserWolker.stop()
        return int(self.myTtlPaserWolker.getValue('result')) != 0

    def subprocess_result(self, type, command_dict, command):
        flag = False
        command_next = None
        if platform.system().lower() == "linux":
            if 'command_linux' in command_dict:
                command_next = command_dict['command_linux']
        else:
            if 'command_windo' in command_dict:
                command_next = command_dict['command_windo']
        if command_next is None:
            for data_one in NextNextPing.INIT_DATA['data']:
                if data_one['name'] == type:
                    if platform.system().lower() == "linux":
                        command_next = data_one['command_linux']
                    else:
                        command_next = data_one['command_windo']
                    break

        command_list = command.split(',')
        if type not in self.next_next_ping.log:
            self.next_next_ping.log[type] = {}
        if command not in self.next_next_ping.log[type]:
            self.next_next_ping.log[type][command] = {}
        #
        # 出力先を保持
        log_type_coomand = self.next_next_ping.log[type][command]
        #
        # print(f"T1={type} C=/{command}/")
        log_type_coomand['stdout'] = ''
        for i, command_data in enumerate(command_list):
            key = '%' + str(i + 1)
            value = command_data.strip()
            command_next = command_next.replace(key, value)
        command_next_list = command_next.split(' ')
        process = None
        try:
            #
            if platform.system().lower() != "linux":
                process = MyWindowsProcess(command_next_list)
            else:
                process = MyLinuxProcess(command_next)
            #
            seconds = command_dict['timeout'] + time.time()
            while self.non_stop_flag and time.time() < seconds:
                # print(f"T4={type} C=/{command}/")
                if process.readable():
                    buffer = process.read(1)
                    if buffer is None:
                        break
                    if buffer == '':
                        continue
                    print(f"{buffer}", end='')
                    x = log_type_coomand['stdout']
                    log_type_coomand['stdout'] = x + buffer
                else:
                    time.sleep(0.1)
            # print(f"T3={type} C=/{command}/")
            #
            if 'ok' in command_dict:
                if isinstance(command_dict['ok'], str):
                    command_dict['ok'] = [command_dict['ok']]
                if 0 == len(command_dict['ok']):
                    flag = True
                else:
                    for ok in command_dict['ok']:
                        if ok in log_type_coomand['stdout']:
                            flag = True
                            break
        except Exception as e:
            log_type_coomand['stdout'] = log_type_coomand['stdout'] + f"## Exception {str(e)}"
            flag = False
        finally:
            if process is not None:
                try:
                    process.close()
                except Exception:
                    pass
        return flag

    def stop(self):
        if self.myTtlPaserWolker is not None:
            self.myTtlPaserWolker.stop()
        self.non_stop_flag = False

    def command_status_threading(self, message: str):
        self.next_next_ping.root.after(
            0, lambda: self.next_next_ping.command_status_threading(message))


class NextNextPing():
    # ログファイル
    LOG_JSON = 'log.json'

    # 初期ファイル
    INIT_JSON = 'init.json'

    def __init__(self):
        self.log = {}
        self.init = {}
        self.setting_text = ""
        self.log_text = ""
        self.tree = ""
        self.tool_tree = None
        self.my_thread = None
        self.root = None
        self.status_var = None
        self.result = None
        self.notebook = None
        self.current_dir = os.getcwd()

    def next_json_load(self, file_name: str):
        # print(f"file={file_name}")
        data = {}
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            data = {}
        return data

    def next_json_save(self, file_name: str, data):
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def next_text_load(self, file_name: str):
        data = ''
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = f.read()
        except FileNotFoundError:
            data = ''
        return data

    def next_text_save(self, file_name: str, data):
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(data)

    def save_log(self):
        """ logを保存 """
        self.stop()
        base_dir = self.init["setting"]
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("json files", "*.json"), ("All json", "*.*")],
            initialdir=base_dir,
            initialfile=NextNextPing.LOG_JSON,
            title="Save log"
        )
        if file_path:
            self.next_json_save(file_path, self.log)

    def load_log(self):
        """ logを保存 """
        self.stop()
        base_dir = self.init["setting"]
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        full_path = os.path.join(base_dir, NextNextPing.LOG_JSON)  # ファイル名を決定
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("json files", "*.json"), ("All files", "*.*")],
            initialdir=base_dir,
            initialfile=NextNextPing.LOG_JSON,
            title="Load log"
        )
        if file_path:
            self.log = self.next_json_load(full_path)
            #
            # アップデートまで実行する
            self.update_setting()

    def save_setting(self, file_path=None):
        """ setting と init を保存 """
        if file_path is None:
            base_dir = self.init["setting"]
            base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
            base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                initialdir=base_dir,
                filetypes=[("txt files", "*.txt"), ("All files", "*.*")],
                initialfile="setting.txt",
                title="Save setting"
            )
        setting = self.setting_text.get("1.0", tk.END)
        if not file_path:
            return  # キャンセルされた
        #
        # initにファイルを指定
        self.init['setting'] = file_path
        #
        # 設定ファイルを保存
        self.next_text_save(file_path, setting)
        #
        # initを保存
        self.next_json_save(NextNextPing.INIT_JSON, self.init)

    def load_setting(self, file_path=None):
        if file_path is None:
            base_dir = self.init["setting"]
            base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
            base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
            file_path = filedialog.askopenfilename(
                defaultextension=".txt",
                filetypes=[("txt files", "*.txt"), ("All files", "*.*")],
                initialdir=base_dir,
                initialfile="setting.txt",
                title="Load setting"
            )
        if not file_path:
            return  # キャンセルされた
        #
        # initにファイルを指定
        self.init['setting'] = file_path
        #
        # ログをクリアする
        self.log = {}
        #
        setting = self.next_text_load(file_path)  # ファイルをロード
        self.setting_text.delete('1.0', 'end')  # 既存のテキストを削除
        self.setting_text.insert(1.0, setting)  # テキストを差し替える
        #
        # アップデートまで実行する
        self.update_setting()
        #
        # ステータスバーを更新する
        self.command_status_threading(f"load f={file_path}")
        #
        # タイトルをファイル名にする
        self.setTitle(file_path)

    def system_exit(self):
        self.stop()
        sys.exit()

    def update_setting(self):
        #
        # pingを打っていたら止める
        self.stop()
        #
        # アイテムIDをすべて削除
        children = self.tree.get_children()
        for child in children:
            self.tree.delete(child)
        #
        # すべてのipを追加
        setting = self.setting_text.get("1.0", tk.END)
        lines = setting.splitlines()
        for line in lines:
            line = line.strip()
            for target in ['#', '\'', '\"', ';']:
                index = line.find(target)
                if 0 <= index:
                    line = line[:index]
            line = line.strip()
            if line == '':
                continue
            type = 'ping'
            display_name = type
            result = re.match(r"^\s*(\[[^\]]*\])?\s*(\([^\)]*\))?\s*(\S+)\s*", line)
            if result:
                display_name = result.group(1)
                type = result.group(2)
                line = result.group(3)
                if type is None:
                    type = 'ping'
                else:
                    # print(f"line1 p1={type} p2={display_name} p3={line}")
                    type = type.strip().lower()
                    if 2 <= len(type):
                        type = type[1:-1]  # 前後の()を消す
                    if "trace" in type:
                        type = "trace"
                    if "show" in type:
                        type = "show"
                    else:
                        a_flag = False
                        for data_list in self.init['data']:
                            # print(f"{data_list['name']}")
                            if data_list['name'] == type:
                                a_flag = True
                        if not a_flag:
                            type = "ping"
                    # print(f"line2 p1={type} p2={display_name} p3={line}")
                #
                if display_name is None or '' == display_name:
                    display_name = type + ':' + line
                elif 2 <= len(display_name):
                    display_name = display_name[1:-1]  # 前後の[]を消す
                    display_name = display_name.strip()
                #
                if line is None:
                    continue
                line = line.strip()
            #
            date = '--'
            result = '--'
            if type in self.log:
                if line in self.log[type]:
                    if 'result' in self.log[type][line]:
                        result = self.log[type][line]['result']
                    if 'date' in self.log[type][line]:
                        date = self.log[type][line]['date']
            values = (result, date, display_name, type, line)
            self.tree.insert("", "end", values=values)
        #
        # 画面を切り替える
        self.notebook.select(1)

    def command_ping(self):
        #
        # logをクリアする
        self.log = {}
        #
        if self.my_thread is None or not self.my_thread.non_stop_flag:
            #
            message = "Ping start!"
            self.command_status_threading(message)
            messagebox.showinfo("Info", message)
            #
            children = self.tree.get_children()
            values_values = []
            for child in children:
                values_values.append(list(self.tree.item(child, 'values')))
            #
            self.my_thread = MyThread()
            thread = threading.Thread(target=self.my_thread.start, daemon=True)
            self.my_thread.set_therad(self, thread, values_values)
            thread.start()
        else:
            message = "Ping already start! (Stop)"
            self.command_status_threading(message)
            messagebox.showinfo("Info", message)
            self.stop()

    def command_stop(self):
        if self.my_thread is not None:
            # スレッド側で終わったダイアログをだすので、こちらは不要
            self.stop()
            return
        message = "Ping already stop!"
        self.command_status_threading(message)
        messagebox.showinfo("Info", message)

    def command_delete(self):
        #
        # 処理止めないと消えたものを実行しようとする
        self.stop()
        #
        selected_items = self.tree.selection()
        for item_id in selected_items:
            self.tree.delete(item_id)

    def stop(self):
        my_thread = self.my_thread
        self.my_thread = None
        if my_thread is not None:
            my_thread.stop()

    def command_ping_threading(self, result, date, type, command):
        """ 戻り処理 """
        children = self.tree.get_children()
        for child in children:
            values = list(self.tree.item(child, 'values'))
            # print(f"xx {values} // {type} // {command}")
            if (values[3] == type) and (values[4] == command):
                values[0] = result
                values[1] = date
            self.tree.item(child, values=values)

    def command_status_threading(self, data: str):
        """ 戻り処理 """
        message = ''
        if self.init['debug']:
            message = "D(True) "
        else:
            message = "D(False) "
        if self.init['loop']:
            message = message + 'L(True) '
        else:
            message = message + 'L(False) '
        if isinstance(data, str):
            message = message + data
        elif isinstance(data, list) or isinstance(data, tuple):
            for d in data:
                message = message + str(d)
        self.status_var.set(message)

    def on_select_double(self, _):

        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        display_name = values[2]
        type = values[3]
        command = values[4]
        string = "empty"
        self.command_status_threading(f"touch n={display_name} t={type} c=/{command}/")
        if type not in self.log:
            self.log[type] = {}
        if command not in self.log[type]:
            self.log[type][command] = {}
        result = "--"
        if 'result' in self.log[type][command]:
            result = self.log[type][command]['result']
        date = "--"
        if 'date' in self.log[type][command]:
            date = self.log[type][command]['date']
        stdout = "--"
        if 'stdout' in self.log[type][command]:
            stdout = self.log[type][command]['stdout']
        string = f"n={display_name} t={type} c={command}\r\n"
        string = string + f"result={result}\r\n"
        string = string + f"date={date}\r\n"
        string = string + "stdout=\r\n"
        string = string + stdout
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(1.0, string)
        #
        self.notebook.select(2)

    INIT_DATA = {
        'setting': 'setting.txt',  # 設定ファイル
        'title': 'nextnextping',
        'wait_time': 1,
        'loop': False,
        'debug': False,
        'data': [
            {
                'name': 'ttl',
                'ttl': True
            },
            {
                'name': 'ping',
                'ttl': False,
                'command_linux': 'ping -c 1 %1',
                'command_windo': 'ping -n 1 %1',
                'ok': ['(0%', ' 0% packet loss'],
                'timeout': 10
            },
            {
                'name': 'trace',
                'ttl': False,
                'command_linux': 'traceroute %1',
                'command_windo': 'tracert %1',
                'ok': ['Trace complete.'],
                'timeout': 10
            },
            {
                'name': 'show',
                'ttl': False,
                'command_linux': 'ip address',
                'command_windo': 'ipconfig /all',
                'ok': [],
                'timeout': 30
            }
        ]
    }

    def next_next_ping(self):
        # 初期値をロードする
        self.init = self.next_json_load(NextNextPing.INIT_JSON)
        # 初期値が入ってなかったら入れる
        for target in NextNextPing.INIT_DATA:
            if target not in self.init:
                self.init[target] = NextNextPing.INIT_DATA[target]
        # 初期値が入ってなかったら入れる
        for target in NextNextPing.SETTING_PARAM:
            if '' == target[2]:
                continue
            if target[2] not in self.init:
                self.init[target[2]] = target[3]
        #
        #
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.system_exit)
        self.root.title(self.init['title'])
        self.root.geometry("800x400")
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        # ファイルメニュー
        file_menu = tk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save setting", command=self.save_setting)
        file_menu.add_command(label="Load setting", command=self.load_setting)
        file_menu.add_command(label="Save log", command=self.save_log)
        file_menu.add_command(label="Load log", command=self.load_log)
        file_menu.add_command(label="Setting", command=self.command_settings)
        file_menu.add_command(label="Exit", command=self.system_exit)
        #
        # ツールメニュー
        tool_menu = tk.Menu(menu_bar, tearoff=False)
        menu_bar.add_cascade(label="Tool", menu=tool_menu)
        tool_menu.add_command(label="Sheet", command=self.tool_sheet)
        #
        # Help メニュー
        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(label="Help", command=self.help_brows)
        help_menu.add_command(label="About", command=self.help_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        #
        self.notebook = ttk.Notebook(self.root)
        #
        # tab1
        #
        tab1 = tk.Frame(self.notebook)
        self.notebook.add(tab1, text="setting")
        top_frame = tk.Frame(tab1)
        top_frame.pack(side=tk.TOP)
        top_button = tk.Button(top_frame, text="Update", command=self.update_setting)
        top_button.pack(side=tk.LEFT)
        main_frame = ttk.Frame(tab1)
        self.setting_text = tk.Text(main_frame)
        self.setting_text.insert(1.0, '; Enter the IP address to ping')
        self.setting_text.pack(pady=2, padx=2, fill=tk.BOTH, expand=True)
        # スクロールバーの設定
        vsb = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.setting_text.yview)
        self.setting_text.configure(yscrollcommand=vsb.set)
        self.setting_text.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.pack(fill=tk.BOTH, expand=True)
        #
        # tab2
        #
        tab2 = tk.Frame(self.notebook)
        self.notebook.add(tab2, text="result")
        column = [
            ['OK/NG', tk.CENTER, 60, False],
            ['Date', tk.W, 120, False],
            ['Display', tk.W, 20, True],
            ['Type', tk.CENTER, 20, True],
            ['IP', tk.W, 20, True]]
        tree_colum = []
        for var in column:
            tree_colum.append(var[0])
        #
        # フレームで Treeview と Scrollbar をまとめる
        top_frame = tk.Frame(tab2)
        top_frame.pack(side=tk.TOP)
        tk.Button(top_frame, text="Ping", command=self.command_ping).pack(side=tk.LEFT)
        tk.Button(top_frame, text="Stop", command=self.command_stop).pack(side=tk.LEFT)
        tk.Button(top_frame, text="Delete", command=self.command_delete).pack(side=tk.LEFT)
        main_frame = ttk.Frame(tab2)
        self.tree = ttk.Treeview(main_frame, columns=tree_colum)
        self.tree.column('#0', width=0, stretch='no')
        for var in column:
            self.tree.column(var[0], anchor=var[1], width=var[2], minwidth=var[2], stretch=var[3])
            self.tree.heading(var[0], text=var[0])
        self.tree.pack(pady=2, padx=2, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-Button-1>", self.on_select_double)
        # スクロールバーの設定
        vsb = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.pack(fill=tk.BOTH, expand=True)
        #
        # tab3
        #
        tab3 = tk.Frame(self.notebook)
        self.notebook.add(tab3, text="log")
        #
        main_frame = ttk.Frame(tab3)
        self.log_text = tk.Text(main_frame)
        self.log_text.insert(1.0, "Please attache table for result tag.")
        self.log_text.pack(pady=2, padx=2, fill=tk.BOTH, expand=True)
        # スクロールバーの設定
        vsb = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=vsb.set)
        self.log_text.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.pack(fill=tk.BOTH, expand=True)
        #
        # ステータスバー（Label）を下部に配置
        #
        self.status_var = tk.StringVar()
        self.command_status_threading("This is status bar")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        #
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        #
        # 画面をトップ画面に切り替える
        self.notebook.select(0)
        #
        self.root.mainloop()
        #

    def setTitle(self, title: str):
        """ タイトルの設定 """
        self.init['title'] = title
        self.root.title(title)

    def show_password_dialog(self, event, p1, p2):
        # print(f"show_password_dialog {p1} / {p2}")
        dialog = PasswordDialog(self.root, message=p1, title=p2)
        self.result = None
        if dialog.result:
            # 成功した！
            self.result = dialog.result
        #
        # イベントを進ませる
        event.set()

    def show_inputdialog(self, event, p1, p2):
        user_input = simpledialog.askstring(p2, p1)
        self.result = None
        if user_input:
            # 成功した！
            self.result = user_input
        #
        # イベントを進ませる
        event.set()

    def show_dirdialog(self, event, p1):
        base_dir = self.init["setting"]
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        dialog_path = filedialog.askdirectory(
            title=p1,
            initialdir=base_dir
        )
        self.result = None
        if dialog_path:
            # 成功した！
            self.result = dialog_path
        #
        # イベントを進ませる
        event.set()

    def show_filedialog(self, event, p1):
        base_dir = self.init["setting"]
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        dialog_path = filedialog.askopenfilename(
            title=p1,
            initialdir=base_dir
        )
        if dialog_path:
            # 成功した！
            self.result = dialog_path
        #
        # イベントを進ませる
        event.set()

    def show_listbox_dialog(self, event, message, title, options):
        dialog = ListboxDialog(self.root, title, options, message=message)
        self.result = None
        if dialog.selection:
            # 成功した！
            self.result = dialog.selection
            # print(f"ListboxDialog {str(self.result)}")
        #
        # イベントを進ませる
        event.set()

    def show_messagebox_dialog(self, event, message, title):
        messagebox.showinfo(title, message)
        event.set()

    def show_yesnobox_dialog(self, event, message, title):
        answer = messagebox.askyesno(title=title, message=message)
        self.result = None
        # 入力結果の処理
        if answer:
            self.result = "OK"
        #
        # イベントを進ませる
        event.set()

    def tool_sheet(self):
        # モーダルダイアログ
        dialog = tk.Toplevel(self.root)
        dialog.title("tool_sheet")
        dialog.geometry("1024x400")
        #
        menu_bar = tk.Menu(dialog)
        dialog.config(menu=menu_bar)
        # ファイルメニュー
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Save csv", command=self.save_csv)
        file_menu.add_command(label="Load csv", command=self.load_csv)
        file_menu.add_command(label="Close", command=dialog.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)
        # goメニュー
        go_menu = tk.Menu(menu_bar, tearoff=False)
        go_menu.add_command(label="Create ttl", command=self.create_ttl)
        menu_bar.add_cascade(label="Go", menu=go_menu)
        #
        top_frame = tk.Frame(dialog)
        top_frame.pack(side=tk.TOP)
        top_button = tk.Button(top_frame, text="Create", command=self.create_tool)
        top_button.pack(side=tk.LEFT)
        top_button = tk.Button(top_frame, text="Delete", command=self.delete_tool)
        top_button.pack(side=tk.LEFT)
        #
        column = []
        for target in NextNextPing.TARGET_PARAM:
            var = target[0]
            column.append(var)
        # フレームでTreeviewとScrollbarをまとめる
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True)
        # 表を作成
        self.tool_tree = ttk.Treeview(frame, columns=column)
        self.tool_tree.column('#0', width=0, stretch='no')
        for var in column:
            self.tool_tree.column(var, anchor=tk.W, width=20)
            self.tool_tree.heading(var, text=var)
        self.tool_tree.bind("<Double-Button-1>", self.modify_tool)
        self.tool_tree.pack(pady=2, padx=2, fill=tk.BOTH, expand=True)
        # スクロールバーの設定
        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tool_tree.yview)
        self.tool_tree.configure(yscrollcommand=vsb.set)
        self.tool_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # ダイアログが閉じられるまで待つ
        dialog.grab_set()
        self.root.wait_window(dialog)

    def create_tool(self):
        values = []
        selected = self.tool_tree.selection()
        if selected:
            item_id = selected[0]
            values = self.tool_tree.item(item_id)["values"]
        else:
            for x in NextNextPing.TARGET_PARAM:
                values.append(str(x[2]))
        item_id = self.tool_tree.insert("", "end", values=values)
        self.update_tool(item_id, values)

    def modify_tool(self, _):
        selected = self.tool_tree.selection()
        if not selected:
            return
        item_id = selected[0]
        values = self.tool_tree.item(item_id)["values"]
        # print(f"values {values}")
        self.update_tool(item_id, values)

    TARGET_PARAM = [
        ["file_name", "ファイル名", "dummy.ttl", ()],
        ["target_display", "pingを打つ装置の表示名", "target_display", ()],
        ["target_ip", "pingを打つIP", "127.0.0.1", ()],
        ["target_type", "設定する種別", 1, ("1=ping", "2=traceroute", "3=show run")],
        ["next_ssh", "踏台先有無", 0, ("0=Windows", "1=SSH login", "2=SSH->SSH login")],
        ["base_type", "SSH先の種別", 2, ("1=cisco", "2=linux", "3=qx-s")],
        ["base_display", "SSH接続する表示名", "base_display", ()],
        ["base_ip", "SSH接続するIP", "localhost:2200", ()],
        ["base_account", "SSH接続するアカウント", "admin", ()],
        ["next_type", "踏み台先種別", 1, ("1=cisco", "2=linux", "3=qx-s")],
        ["next_display", "SSHからさらに接続する装置", "next_display", ()],
        ["next_ip", "踏み台SSHのIPアドレス", "dummy", ()],
        ["next_account", "踏み台先のアカウント", "admin", ()]]

    def get_japanese_flag(self) -> bool:
        current_locale = locale.getlocale()
        # 戻り値のタプルの最初の要素（言語コード）を取得
        lang_code = current_locale[0]
        # 日本語かどうかを判定
        if lang_code:
            lang_code = lang_code.lower()
            # print(f"get_japanese_flag {lang_code}")
            return lang_code.startswith('ja') or lang_code.startswith('japanese')
        return False

    def get_target_filename(self, row_index: int, values: list) -> str:
        """ ファイル名を取得する """
        row_index = str(1000 + row_index)
        #
        ans = ''
        #
        target_ip = values[2]
        target_type = int(values[3])
        next_ssh = int(values[4])
        base_ip = values[7]
        next_ip = values[11]
        action_name = self.get_target_type_to_action_name(target_type, target_ip)
        if next_ssh == 0:  # 0=Windows , 1=SSH login , 2=SSH->SSH login
            return "None"  # not required ttl name
        elif next_ssh == 1:  # 0=Windows , 1=SSH login , 2=SSH->SSH login
            ans = f"{row_index}_ok_{base_ip}_{action_name}"
        elif next_ssh == 2:  # 0=Windows , 1=SSH login , 2=SSH->SSH login
            ans = f"{row_index}_ok_{next_ip}_{action_name}"
        else:
            ans = "unkown_next_ssh"
        #
        for replace_target in [
                '.',  # ipv4
                ':',  # ipv6
                '[',  # ipv6
                ']',  # ipv6
                '%',  # ipv6
                '/',  # folder
                '@']:  # account
            ans = ans.replace(replace_target, '-')
        for replace_target in [
                ',', '\'', '\'', '<', '>', '(', ')', '[', ']', ';', ' ', "\r", "\n", "\t"]:
            ans = ans.replace(replace_target, '')
        return ans + '.ttl'

    def update_tool(self, item_id, values: list) -> list:
        # モーダルダイアログ
        dialog = tk.Toplevel(self.root)
        dialog.title('tool_sheet_line')
        dialog.geometry('400x450')
        #
        # 不正対策
        while len(values) < len(NextNextPing.TARGET_PARAM):
            values.append('')
        #
        japanese_flag = self.get_japanese_flag()
        #
        name_var_list = []
        widget = []

        def on_combo_select(event):
            """ コンボ選択処理 """
            target_type = int(name_var_list[3].get()[0])
            if target_type == 3:  # 1=ping , 2=traceroute , 3=show run
                widget[2].config(state='disabled')
            else:
                widget[2].config(state='normal')
            #
            next_ssh = int(name_var_list[4].get()[0])
            if next_ssh == 0:  # ('0=Windows', '1=SSH login', '2=sSSH step')
                for entry in widget[5:]:
                    entry.config(state='disabled')
            elif next_ssh == 1:
                for entry in widget[5:]:
                    entry.config(state='normal')
                for entry in widget[9:]:
                    entry.config(state='disabled')
            else:
                for entry in widget[5:]:
                    entry.config(state='normal')
        #
        for i, target_param in enumerate(NextNextPing.TARGET_PARAM):
            label_text = target_param[0]
            if japanese_flag:
                label_text = target_param[1]
            tk.Label(dialog, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky='e')
            if 0 < len(target_param[3]):
                combo_list = target_param[3]  # target_type
                selected_value = tk.StringVar()
                selected_value.set(values[i])
                name_var_list.append(selected_value)
                combo = ttk.Combobox(dialog, textvariable=selected_value)
                widget.append(combo)
                combo['values'] = combo_list
                if i == 3 or i == 4:  # target_type, ssh_type
                    combo.bind('<<ComboboxSelected>>', on_combo_select)
                value_item = 0
                j = 0
                for combo_str in combo_list:
                    if str(values[i]) == combo_str[0]:  # 最初の一文字がマッチするか？
                        # print(f"hit! {j}")
                        value_item = j
                        break
                    j = j + 1
                combo.current(value_item)  # 初期選択（インデックス）
                combo.grid(row=i, column=1, padx=10, pady=5)
            else:
                name_var = tk.StringVar()
                name_var.set(values[i])
                name_var_list.append(name_var)
                entry = tk.Entry(dialog, textvariable=name_var)
                widget.append(entry)
                entry.grid(row=i, column=1, padx=10, pady=5)
                if i == 0:
                    entry.config(state='disabled')
            #
        #
        # コンボ選択の反映
        on_combo_select(None)

        def submit():
            """ 入力値を取得する関数 """
            values = []
            for i, name_var in enumerate(name_var_list):
                val = name_var.get()
                if NextNextPing.TARGET_PARAM[i][0] in ["target_type", "next_ssh", "base_type", "next_type"]:
                    if 0 < len(val):
                        val = val[0]  # 先頭一文字を抽出する
                    else:
                        val = str(NextNextPing.TARGET_PARAM[i][2])  # 初期値を入れる
                values.append(val)
            #
            # 表の行数を得る
            row_index = self.tool_tree.get_children().index(item_id)
            #
            values[0] = self.get_target_filename(row_index, values)
            #
            self.tool_tree.item(item_id, values=values)
            #
            self.command_status_threading(f"Update index{row_index}")
            #
            dialog.destroy()

        bottom_frame = tk.Frame(dialog)
        bottom_frame.grid(row=len(NextNextPing.TARGET_PARAM), column=0, columnspan=2, pady=10)
        # 送信ボタン
        tk.Button(bottom_frame, text="Update", command=submit).pack(side=tk.LEFT)

        # ダイアログが閉じられるまで待つ
        dialog.grab_set()
        self.root.wait_window(dialog)

        return values

    def help_about(self):
        # モーダルダイアログ
        dialog = tk.Toplevel(self.root)
        dialog.title('About nextnextping')
        dialog.geometry('400x200')
        #
        label_text_list = []
        label_text_list.append(f"nextnextping Version {str(VERSION)} (C)2025 Toshikazu Ando")
        label_text_list.append("")
        label_text_list.append("Powerd by:")
        label_text_list.append("  ANTLR 4.13.2")
        label_text_list.append(f"  Python {sys.version}")
        label_text_list.append("")
        label_text_list.append("Author: https://github.com/Tand0/nextnextping")
        #
        for i, label_text in enumerate(label_text_list):
            tk.Label(dialog, text=label_text, wraplength=380).grid(row=i, column=0, padx=10, pady=1, sticky=tk.W)

        # ダイアログが閉じられるまで待つ
        dialog.grab_set()
        self.root.wait_window(dialog)

    def delete_tool(self):
        selected_items = self.tool_tree.selection()
        for item in selected_items:
            self.tool_tree.delete(item)

    def load_csv(self):
        """ 読み込みダイアログを表示 """
        base_dir = self.init["setting"]
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        file_path = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=base_dir,  # 設定ファイルが配置されているフォルダをベースにする
            initialfile="setting.csv",
            title="Load csv"
        )
        if not file_path:
            return  # ファイルが指定されなかった
        #
        file_path = os.path.abspath(file_path)  # 絶対パスに変換
        self.init["setting"] = os.path.splitext(file_path)[0] + ".txt"  # 設定ファイルを指定
        #
        current_encoding = ''
        if self.get_japanese_flag():
            current_encoding = 'cp932'
        else:
            current_encoding = locale.getpreferredencoding(False)
        #
        # ロード
        values = []
        try:
            with open(file_path, newline='', encoding=current_encoding) as f:
                reader = csv.reader(f)
                values = [row for row in reader]
        except UnicodeDecodeError:
            if current_encoding.lower() == 'utf-8':
                current_encoding = 'cp932'
            else:
                current_encoding = 'utf-8'
            with open(file_path, newline='', encoding=current_encoding) as f:
                reader = csv.reader(f)
                values = [row for row in reader]
        #
        # 表を一度クリア
        for item in self.tool_tree.get_children():
            self.tool_tree.delete(item)
        #
        for i, value in enumerate(values):
            # 表への詰み込み
            while len(value) < len(NextNextPing.TARGET_PARAM):
                value.append('')
            if value[0].strip() == '':  # 先頭が空行なら無視する
                continue
            target_values = []
            for value_one in value:
                target_values.append(str(value_one))  # int避け
            target_values[0] = self.get_target_filename(i, target_values)
            self.tool_tree.insert("", "end", values=target_values)
        #
        messagebox.showinfo("Info", "load_csv is ok")
        self.tool_tree.focus_set()

    def save_csv(self):
        """ 保存ダイアログを表示 """
        base_dir = self.init["setting"]
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=base_dir,  # 設定ファイルが配置されているフォルダをベースにする
            initialfile="setting.csv",
            title="Save csv"
        )
        if not file_path:
            return  # ファイルが指定されなかった
        #
        all_items = self.tool_tree.get_children()
        values_list = []
        for item_id in all_items:
            values = self.tool_tree.item(item_id)["values"]
            values_list.append(values)
        #
        file_path = os.path.abspath(file_path)  # 絶対パスに変換
        self.init["setting"] = os.path.splitext(file_path)[0] + ".txt"  # 設定ファイルを指定
        #
        current_encoding = ""
        if self.get_japanese_flag():
            current_encoding = "cp932"
        else:
            current_encoding = locale.getpreferredencoding(False)
        #
        with open(file_path, "w", encoding=current_encoding) as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerows(values_list)
        #
        messagebox.showinfo("Info", "save_csv is ok")
        self.tool_tree.focus_set()

    def get_target_type_to_action_name(self, target_type: int, target_ip: str) -> str:
        """ target_type を 1=ping , 2=trace , 3=show に変える """
        if target_type == 1:
            return f"ping_{target_ip}"
        elif target_type == 2:
            return f"trace_{target_ip}"
        elif target_type == 3:
            return "show"  # showの時はtarget_typeはいらない
        #
        return str(target_type)

    def create_ttl(self):
        """ リストを抽出してttlを作る """
        # ベースフォルダを確定させる
        base_dir = self.init["setting"]  # 設定ファイルを読み込み
        base_dir = os.path.abspath(base_dir)  # 絶対パスに変換
        base_dir = os.path.dirname(base_dir)  # フォルダのみ抽出
        #
        new_text = ''
        all_items = self.tool_tree.get_children()
        for item_id in all_items:
            values = self.tool_tree.item(item_id)["values"]
            #
            file_name = values[0]
            target_display = values[1]
            target_ip = values[2]
            target_type = int(values[3])
            next_ssh = int(values[4])
            base_ip = values[7]
            base_display = values[6]
            next_display = values[10]
            next_ip = values[11]
            #
            file_head_data = ''
            action_name = self.get_target_type_to_action_name(target_type, f"{target_display}({target_ip})")
            if next_ssh == 0:  # 0=Windows , 1=SSH login , 2=SSH->SSH login
                file_head_data = f"; {action_name}\n"
            elif next_ssh == 1:  # 0=Windows , 1=SSH login , 2=SSH->SSH login
                file_head_data = f"; {base_display}({base_ip}) {action_name} \n"
            elif next_ssh == 2:  # 0=Windows , 1=SSH login , 2=SSH->SSH login
                file_head_data = f"; {base_display}({base_ip})->{next_display}({next_ip}) {action_name}\n"
            else:
                file_head_data = "; \n"
            #
            display_name = target_display
            for replace_target in ['@', ':', ',', '\'', '\'', '<', '>', '(', ')', '[', ']', ';', '#', ' ', "\r", "\n", "\t"]:
                display_name = display_name.replace(replace_target, '')
            new_text = new_text + file_head_data
            new_text = new_text + '[' + display_name + ']'
            #
            if next_ssh == 0:
                # windowsから打つ場合はttlいらな
                if target_type == 1:  # '1=ping', '2=traceroute', '3=show run'
                    new_text = new_text + target_ip + "\n"
                elif target_type == 2:
                    new_text = new_text + '(traceroute)' + target_ip + "\n"
                else:
                    new_text = new_text + '(show) None\n'
                new_text = new_text + "\n"
            else:
                # sshが必要なのでttlを出力する
                new_text = new_text + "(ttl)" + file_name + "\n"
                new_text = new_text + "\n"
                #
                file_head_data = ';\n' + file_head_data + ";\n\n"
                #
                # ファイルを書き込む
                for i, value in enumerate(values):
                    if i == 0:
                        file_head_data = file_head_data + "basename file_name param1\n"
                        continue
                    file_head_data = file_head_data + NextNextPing.TARGET_PARAM[i][0]
                    file_head_data = file_head_data + " = "
                    if isinstance(NextNextPing.TARGET_PARAM[i][2], int):
                        file_head_data = file_head_data + str(value)
                    else:
                        file_head_data = file_head_data + f"\"{str(value)}\""
                    if 0 < len(NextNextPing.TARGET_PARAM[i][3]):
                        file_head_data = file_head_data + "  ; "
                        flag = False
                        for data in NextNextPing.TARGET_PARAM[i][3]:
                            if flag:
                                file_head_data = file_head_data + " , "
                            else:
                                flag = True
                            file_head_data = file_head_data + data
                        #
                    file_head_data = file_head_data + "\n"
                base_file = 'base.ttl'
                file_head_data = file_head_data + "\n\n"
                file_head_data = file_head_data + f"include \"{base_file}\""
                file_head_data = file_head_data + "\n\n"
                #
                # baseファイルの作成
                full_path = os.path.join(base_dir, base_file)
                if not os.path.exists(full_path):  # ベースファイルが存在しなければ作る
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(SAMPLE_TTL)
                #
                # 実際のフォルダを指定する
                full_path = os.path.join(base_dir, file_name)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_head_data)
                #
        # 設定シートを書き換える
        self.setting_text.delete('1.0', 'end')  # 既存のテキストを削除
        self.setting_text.insert('1.0', new_text)  # 新しいテキストを挿入
        #
        # 設定シートを保存する
        self.save_setting(self.init["setting"])
        #
        # resultシートを更新する
        self.update_setting()
        #
        messagebox.showinfo("Info", "ttl is ok")
        self.tool_tree.focus_set()

    SETTING_PARAM = [
        ['Debug flag', 'debugするか？', 'debug', True],
        ['Loop flag', 'ループするか？', 'loop', True],
        ['wait_time', 'コマンド終了時待ち時間', 'wait_time', 0],
        ['', '', '', ''],
        ['TTL macro', 'TTL macro', '', ''],
        ['TTL ignore messagebox', 'messageboxを表示しない', 'ignore_messagebox', True],
        ['TTL ignore log', 'logを出力しない', 'ignore_log', True]]

    def command_settings(self):
        """ 設定用ダイアログを開く """
        # モーダルダイアログ
        dialog = tk.Toplevel(self.root)
        dialog.title("tool_sheet_line")
        dialog.geometry("400x300")
        japanese_flag = self.get_japanese_flag()
        #
        name_var_list = []
        for i, target_param in enumerate(NextNextPing.SETTING_PARAM):
            label_text = target_param[0]
            if japanese_flag:
                label_text = target_param[1]
            #
            ans = ''
            if target_param[2] in self.init:
                ans = self.init[target_param[2]]
            #
            type = target_param[3]
            tk.Label(dialog, text=label_text).grid(row=i, column=0, padx=10, pady=5, sticky="e")
            name_var = tk.StringVar()
            name_var_list.append(name_var)
            if '' == target_param[2]:  # コメント行のとき
                pass
            elif isinstance(type, bool):
                # print(f"i={i} bool name={target_param[2]} ans={str(ans)}")
                combo_list = ('False', 'True')
                name_var.set(str(ans))
                combo = ttk.Combobox(dialog, textvariable=name_var)
                combo["values"] = combo_list
                if ans:
                    combo.current(1)
                else:
                    combo.current(0)
                combo.grid(row=i, column=1, padx=10, pady=5, sticky='ew')
            elif isinstance(type, int):
                # print(f"i={i} int  name={target_param[2]} ans={str(ans)}")
                name_var.set(str(ans))
                entry = tk.Entry(dialog, textvariable=name_var)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky='ew')

        def submit():
            """ 入力値を取得する関数 """
            for j, target_param2 in enumerate(NextNextPing.SETTING_PARAM):
                if target_param2[2] not in self.init:
                    continue
                #
                val = name_var_list[j].get()
                name = target_param2[2]
                type = target_param2[3]
                if isinstance(type, bool):
                    # print(f"i={j} bool type={type} name={name} str={str(val)}")
                    val = str(val)
                    if 't' == val[0].lower():
                        self.init[name] = True
                    else:
                        self.init[name] = False
                elif isinstance(type, int):
                    # print(f"i={j} int  type={type} name={name} str={str(val)}")
                    val = int(val)
                    self.init[name] = val
            #
            self.command_status_threading('Setting update!')
            #
            self.update_setting()
            dialog.destroy()

        bottom_frame = tk.Frame(dialog)
        bottom_frame.grid(row=len(NextNextPing.SETTING_PARAM), column=0, columnspan=2, pady=10)
        # 送信ボタン
        tk.Button(bottom_frame, text="Update", command=submit).pack(side=tk.LEFT)

        # ダイアログが閉じられるまで待つ
        dialog.grab_set()
        self.root.wait_window(dialog)

    def help_brows(self):
        base_file = "_internal/README.html"
        full_path = os.path.join(self.current_dir, base_file)
        path = os.path.abspath(full_path)
        webbrowser.open(path)


class PasswordDialog(simpledialog.Dialog):
    def __init__(self, parent, title="PasswordDialog", message="Enter Password"):
        self.message = message
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text=self.message).grid(row=0, column=0, padx=10, pady=10)
        self.entry = tk.Entry(master, show="*")
        self.entry.grid(row=1, column=0, padx=10)
        return self.entry  # 初期フォーカス

    def apply(self):
        self.result = self.entry.get()


class ListboxDialog(simpledialog.Dialog):
    def __init__(self, parent, title, options, message="Plrease select"):
        self.options = options
        self.selection = None
        self.message = message
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text=self.message).pack(padx=10, pady=5)
        self.listbox = tk.Listbox(master, selectmode=tk.SINGLE)
        for item in self.options:
            self.listbox.insert(tk.END, item)
        self.listbox.pack(padx=10, pady=5)
        return self.listbox

    def apply(self):
        selected = self.listbox.curselection()
        # print("apply")
        if selected:
            self.selection = self.listbox.get(selected[0])
            # print(f"選択されている {self.selection}")


def main():
    next_next_ping = NextNextPing()
    next_next_ping.next_next_ping()


if __name__ == "__main__":
    main()

#
