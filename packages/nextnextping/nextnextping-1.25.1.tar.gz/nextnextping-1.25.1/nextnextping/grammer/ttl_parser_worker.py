# -*- coding: utf-8 -*-
import time
import socket
import re
import subprocess
import os
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
import pathlib
import json
import random
import threading
import base64
import platform
import getpass
from abc import ABC, abstractmethod

IMP_ERR = None
try:
    from cryptography.fernet import Fernet
    from cryptography.fernet import InvalidToken
    import paramiko
    from antlr4.InputStream import InputStream
    from antlr4.CommonTokenStream import CommonTokenStream
    from antlr4.tree.Tree import ParseTreeVisitor
    from antlr4.error.ErrorListener import ErrorListener
    import pexpect
    import uptime
    from .ttl_parser_lexer import TtlParserLexer
    from .ttl_parser_parser import TtlParserParser
    from .version import VERSION
except ImportError as ex:
    class ParseTreeVisitor():
        pass
    IMP_ERR = ex


class MyFindfirst:
    """find first handle class """

    def __init__(self, target):
        target = target.replace(".", "\\.").replace("*", ".*")
        self.my_list = []
        for f in os.listdir(os.getcwd()):
            # print(f"MyFindfirst1 {target} {f}")
            result = re.match(target, f)
            if result:
                # print("hit!")
                self.my_list.append(str(f))

    def close(self):
        """ nothing """
        pass

    def write(self, text):
        """これは呼ばれないので何もしない"""
        pass

    def read(self, length: int):
        """これは呼ばれないので何もしない"""
        pass

    def readline(self) -> str:
        ans = b""
        if 0 < len(self.my_list):
            ans = self.my_list[0]
            self.my_list = self.my_list[1:]
            # print(f"MyFindfirst {str(self.my_list)}")
            ans = ans.encode("utf-8")
        else:
            raise OSError("readline exception")
        return ans


class MyAbstractShell(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def send_ready(self) -> bool:
        pass

    @abstractmethod
    def send(self, message):
        pass

    @abstractmethod
    def recv_ready(self) -> bool:
        pass

    @abstractmethod
    def recv(self, length: int) -> str:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def isActive(self) -> int:
        pass


class MyShell(MyAbstractShell):
    def __init__(self, command=None):
        if command is None:
            command = ['cmd']
        # print("MyShell __init__ start")
        self.data = ""
        self.lock = threading.Lock()
        self.active = 1
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
        )
        thread = MyThread(self, "stdout", self.process.stdout)
        thread.start()
        # print("MyShell __init__ end")

    def send_ready(self) -> bool:
        # print("send_ready")
        if self.active == 0:
            return 0
        return self.process.stdin.writable()

    def send(self, message):
        # print(f"send /{message.strip()}/")
        if self.active == 0:
            return
        self.process.stdin.write(message)
        self.process.stdin.flush()

    def recv_ready(self) -> bool:
        self.process.stdout.flush()
        # self.process.stderr.flush()
        ans = False
        if 0 < len(self.data):
            ans = True
        # print(f"recv_ready {len(self.data)} / {ans}")
        return ans

    def recv(self, length: int) -> str:
        # print(f"recv d=/{self.data.strip()}/")
        if len(self.data) <= 0:
            return
        local_data = ""
        with self.lock:
            local_data = self.data[0]
            self.data = self.data[1:]
        return local_data.encode("utf-8")

    def close(self):
        # print("client close")
        self.active = 0
        self.data = ""
        local_process = self.process
        self.local_process = None
        if local_process is not None:
            try:
                local_process.terminate()
            except Exception:
                # anything delete
                pass

    def isActive(self) -> int:
        return self.active


class MyPexpect(MyAbstractShell):
    def __init__(self):
        shell_name = os.getenv("SHELL", "/bin/sh")
        self.child = pexpect.spawn(shell_name, timeout=0, encoding='utf-8')
        self.result = None

    def send_ready(self) -> bool:
        return True

    def send(self, message):
        child = self.child
        if child is None:
            return
        child.send(message)

    def recv_ready(self) -> bool:
        child = self.child
        if child is None:
            return False
        if self.result is not None:
            return True
        index = child.expect([r".", pexpect.EOF, pexpect.TIMEOUT])
        if index == 0:
            # child.after でマッチした文字列全体を取得
            self.result = child.before + child.after
            if 0 < len(self.result):
                return True
            else:
                return False
        elif index == 1:  # EOF
            self.close()
            return False
        return False  # Timeout

    def recv(self, length: int) -> str:
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
        return work.encode("utf-8")

    def close(self):
        child = self.child.close()
        self.child = None
        try:
            child.close()
        except Exception:
            pass

    def isActive(self) -> int:
        if self.child is not None:
            return 1
        return 0


class MyThread(threading.Thread):
    def __init__(self, myShell: MyShell, name: str, stream):
        # print("MyThread __init__ start")
        super().__init__()
        self.name = name
        self.myShell = myShell
        self.stream = stream
        # print("MyThread __init__ end")

    def run(self):
        """外部プロセスからの読み込み"""
        # print(f"MyThread_run() start f={type(self.myShell)} n={self.name}")
        while self.myShell.isActive() != 0:
            ans = self.stream.read(1)
            # print(f"start n={self.name} a=/{ans}/")
            with self.myShell.lock:
                self.myShell.data = self.myShell.data + ans
        # print(f"MyThread_run() end n={self.name} a=/{ans}/")
        #
        # activeでなくなったので念のため消す
        try:
            self.stream.close()
        except Exception:
            # どんなエラーがでようと必ず殺す
            pass


class Label:
    """ラベル情報の保存地域"""

    def __init__(self, token_list):
        """コンストラクタ"""
        self.token_list = token_list

    def getTokenList(self):
        """トークンの取得"""
        return self.token_list

    def __str__(self):
        return f"{str(self.token_list)}"


class TtlContinueFlagException(Exception):
    """continue 用の例外"""

    def __init__(self, message):
        """コンストラクタ"""
        super().__init__(message)


class TtlBreakFlagException(Exception):
    """break 用の例外"""

    def __init__(self, message):
        """コンストラクタ"""
        super().__init__(message)


class TtlReturnFlagException(Exception):
    """return 用の例外"""

    def __init__(self, message):
        """コンストラクタ"""
        super().__init__(message)


class TtlExitFlagException(Exception):
    """exit 用の例外"""

    def __init__(self, message):
        """コンストラクタ"""
        super().__init__(message)


class TtlResultException(Exception):
    """exit 用の例外"""

    def __init__(self, message):
        """コンストラクタ"""
        super().__init__(message)


class TtlParseTreeVisitor(ParseTreeVisitor):
    def visit(self, tree):
        return tree.accept(self)

    def visitChildren(self, node):
        result = {}
        result["name"] = node.__class__.__name__
        line_number = node.start.line
        result["line"] = line_number
        #
        n = node.getChildCount()
        if n == 0:
            return result
        worker_list = []
        for i in range(n):
            c = node.getChild(i)
            childResult = c.accept(self)
            if childResult is not None:
                worker_list.append(childResult)
        if worker_list != 0:
            result["child"] = worker_list
        return result

    def visitTerminal(self, node):
        type = node.getSymbol().type
        # print(f"visitErrorNode type={type} text={node.getText()}")
        if type < 0:
            return None
        x = TtlParserLexer.ruleNames[type - 1]
        if x == "RN" or x == "WS":
            return None
        return node.getText()

    def visitErrorNode(self, node):
        x = node.getSymbol().type
        x = TtlParserLexer.ruleNames[x - 1]
        y = node.getText()
        line_number = node.getSymbol().line
        raise TypeError(f"### l={str(line_number)} visitErrorNode type={x} text={y}")


class ThrowingErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise TypeError(f"### l={line}:{column} Token recognition error - {msg}")


class TtlPaserWolker(ABC):
    """tera tekitou lang の実装部分(GUI除く)"""

    def __init__(self):
        """ init """
        if IMP_ERR:
            raise ImportError(IMP_ERR)
        self.value_list = {}
        self.result_file_json = {}
        self.end_flag = False
        self.client = None
        self.shell = None
        self.stdout = ""
        self.file_handle_list = {}
        self.title = "dummy"
        self.title = self.getTitle()  # オーバーライドされたときにタイトルを差し替える
        self.log_file_handle = None
        self.log_start = True
        self.log_timestamp_type = -1
        self.log_login_time = time.time()
        self.log_connect_time = None
        # カレントフォルダを取得する
        self.current_dir = pathlib.Path.cwd()
        #
        self.encrypt_file = {}
        self.exitcode = None

    def stop(self, error=None):
        """強制停止処理"""
        if error is not None:
            self.setValue("error", error)
            self.setValue("result", 0)
        self.end_flag = True
        #
        # SSH接続していたら止める
        self.closeClient()
        #
        # ファイルハンドルがいたら止める
        for k in list(self.file_handle_list.keys()):
            self.doFileclose(k)
        #
        # ログファイルハンドルがいたら止める
        self.doLogclose()
        #
        # カレントフォルダを戻す
        os.chdir(self.current_dir)

    def closeClient(self):
        """close client"""
        # print("closeClient()")
        self.stdout = ""
        self.log_connect_time = None
        #
        client = self.client
        self.client = None
        if client is not None:
            try:
                client.close()
            except Exception:
                # どんなエラーがでようと必ず殺す
                pass
                client = self.client
        shell = self.shell
        self.shell = None
        if shell is not None:
            try:
                shell.close()
            except Exception:
                # どんなエラーがでようと必ず殺す
                pass

    def set_default_value(self, param_list: list):
        #
        self.setValue("error", "")
        self.setValue("result", 1)
        #
        # print(f" data={json.dumps(param_list, indent=2)}")
        for i in range(10):
            self.setValue("param" + str(i + 1), "")
            self.setValue("param[" + str(i + 1) + "]", "")
        #
        for i, param in enumerate(param_list):
            self.setValue("param" + str(i + 1), param)
            self.setValue("param[" + str(i + 1) + "]", param)

    def execute(self, filename: str, param_list: list, data=None, ignore_result=False):
        try:
            self.set_default_value(param_list)
            #
            # 一発目のinclude
            self.include(filename, data)
            #
            if self.exitcode is not None:
                self.setValue("result", self.exitcode)
            if not ignore_result:
                result = int(self.getValue('result'))
                error_data = self.getValue('error')
                if result == 0:
                    raise TtlResultException(f"Exceptiont (result==0) f={filename} e=/{error_data}/")
            #
        finally:
            # なにがあろうとセッションは必ず殺す
            self.closeClient()

    def include_only(self, filename: str, data=None):
        """読み込みここから"""
        try:
            #
            # print(f"filename={filename} param={self.result_file_json}")
            if filename not in self.result_file_json:
                if data is None:
                    with open(filename, "r", encoding="utf-8") as f:
                        data = f.read()
                result_json = self.include_data(data)
                #
                # for call command
                self.result_file_json[filename] = result_json
                #
                # ラベル設定
                self.correctLabel()
                #
        except Exception as e:
            self.setLogInner(f"### except read file exception! f={str(e)}")
            self.stop(f"{type(e).__name__} f={filename} e={str(e)} error!")
            raise  # そのまま上流へ送る

    def include(self, filename: str, data=None):
        if self.end_flag:
            return
        #
        # 読み込みここから
        self.include_only(filename, data)
        #
        if self.end_flag:
            return
        #
        # 実処理ここから
        try:
            #
            self.execute_result(self.result_file_json[filename]["child"])
            #
        except TtlExitFlagException:
            # exitコマンドが呼び出されときは正常終了です
            pass
        except Exception as e:
            self.setLogInner(f"### except execute_result f={str(e)}")
            self.stop(f"{type(e).__name__} f={filename} e={str(e)} error!")
            raise  # そのまま上流へ送る

    def include_data(self, data: str):
        """Jsonで結果を得る"""
        if self.end_flag:
            return
        #
        input_stream = InputStream(data + "\n")
        lexer = TtlParserLexer(input_stream)
        lexer.removeErrorListeners()
        lexer.addErrorListener(ThrowingErrorListener())
        token_stream = CommonTokenStream(lexer)
        parser = TtlParserParser(token_stream)
        #
        # パーサが失敗していたら止める
        # parser._errHandler = BailErrorStrategy()
        #
        tree = parser.statement()
        visitor = TtlParseTreeVisitor()
        return tree.accept(visitor)

    def setValue(self, strvar: str, data):
        """変数を設定する"""
        # print(f"setValue={strvar} data={data}")
        if self.isValue(strvar):  # this is label
            if isinstance(self.getValue(strvar), Label):
                raise TypeError(f"Label already set exception. v={strvar}")
        self.value_list[strvar] = data

    def setValueLabel(self, strvar: str, data: Label):
        """変数を設定する"""
        # print(f"01ラベルを設定した {strvar} /{data.getTokenList()}/")
        self.value_list[strvar] = data

    def isValue(self, strvar: str) -> bool:
        """変数がいるかチェックする"""
        return strvar in self.value_list

    def getValue(self, strvar: str, error_stop=True):
        """変数を取得する"""
        if strvar not in self.value_list:
            for k in self.value_list:
                # print(k)
                if strvar + "[" in k:
                    return "ARRAY"  # 配列指定がある
            if error_stop:
                raise TypeError(f"Value not found err v={strvar}")
            return None
        # print(f"02ラベルを取得した {strvar} // {self.value_list[strvar]}")
        return self.value_list[strvar]

    def execute_result(self, x_list, ifFlag=1):
        """execute_result"""
        # print("execute_result")
        if self.end_flag:
            return
        for x in x_list:
            name = x["name"]
            line = x["line"]
            #
            # よくわからんがsleep入れないと不明なエラーが出る？
            # time.sleep(0.01)
            #
            if "CommandlineContext" == name:
                if ifFlag != 0:
                    self.commandlineContext(x["child"])
            elif "ElseifContext" == name:
                if ifFlag == 0:
                    first = self.getDataInt(x["child"][1])
                    if first != 0:
                        self.execute_result(x["child"][3:])
                        ifFlag = 1
            elif "ElseContext" == name:
                if ifFlag == 0:
                    self.execute_result(x["child"][1:])
            else:
                self.stop(error=f"### l={line} execute_result Unkown name={name} x={x}")
            if self.end_flag:
                break

    def normpath(self, filename: str) -> str:
        filename = os.path.normpath(filename.replace("\\", "/"))
        if platform.system().lower() == "linux":
            result = re.search("^([a-zA-Z]):(.*)$", filename)
            if result:
                filename = f"/mnt/{result.group(1)}/{result.group(2)}"
        return filename

    def commandlineContext(self, token_list):
        for x in token_list:
            # print(f"commandlineContext data={json.dumps(x, indent=2)}")
            name = x["name"]
            line = x["line"]
            if "InputContext" == name:
                strvar = self.getKeywordName(x["child"][0])
                data = x["child"][2]
                data = self.getData(data)
                self.setValue(strvar, data)
            elif "CommandContext" == name:
                command_name = x["child"][0]
                if "assert" == command_name:
                    self.doAssert(command_name, line, x["child"][1:])
                elif "break" == command_name:
                    raise TtlBreakFlagException(command_name)
                elif "continue" == command_name:
                    raise TtlContinueFlagException(command_name)
                elif "end" == command_name:
                    self.end_flag = True
                elif "exit" == command_name:
                    raise TtlExitFlagException(command_name)
                elif "return" == command_name:
                    raise TtlReturnFlagException(command_name)
                elif "include" == command_name:
                    p1 = self.getData(x["child"][1])
                    self.include(p1)
                elif "call" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    # print(f"call label={p1}")
                    self.callContext(line, p1)
                elif "bplusrecv" == command_name:
                    self.doBplusrecv(command_name, line)
                elif "bplussend" == command_name:
                    p1 = self.getData(x["child"][1])
                    self.doBplussend(command_name, line, p1)
                elif "callmenu" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doCallmenu(command_name, line, p1)
                elif command_name in ["setdir", "changedir"]:
                    p1 = self.getData(x["child"][1])
                    self.doChangedir(p1)
                elif "clearscreen" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doClearscreen(command_name, line, p1)
                elif command_name in ["closett", "disconnect", "unlink"]:
                    self.closeClient()
                elif "connect" == command_name:
                    self.doConnect(self.getData(x["child"][1]), line)
                elif "dispstr" == command_name:
                    self.doDispstr(x["child"][1:])
                elif "flushrecv" == command_name:
                    self.doFlushrecv()
                elif "enablekeyb" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doEnablekeyb(command_name, line, p1)
                elif "getmodemstatus" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    self.doGetmodemstatus(command_name, line, p1)
                elif "gethostname" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    self.doGethostname(p1)
                elif "gettitle" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p1_val = self.getTitle()
                    self.setValue(p1, p1_val)
                elif "logautoclosemode" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doLogautoclosemode(command_name, line, p1)
                elif "logclose" == command_name:
                    self.doLogclose()
                elif "loginfo" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    self.doLoginfo(command_name, line, p1)
                elif "logopen" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = self.getDataInt(x["child"][2])
                    p3 = self.getDataInt(x["child"][3])
                    p_len = len(x["child"])
                    p4 = 0
                    if 5 < p_len:
                        p4 = self.getDataInt(x["child"][4])
                    p5 = 0
                    if 6 <= p_len:
                        p5 = self.getDataInt(x["child"][5])
                    p6 = 0
                    if 7 <= p_len:
                        p6 = self.getDataInt(x["child"][6])
                    p7 = 0
                    if 8 <= p_len:
                        p7 = self.getDataInt(x["child"][7])
                    p8 = 0
                    if 9 <= p_len:
                        p8 = self.getDataInt(x["child"][8])
                    self.doLogopen(p1, p2, p3, p4, p5, p6, p7, p8)
                elif "logpause" == command_name:
                    self.doLogpause()
                elif "logrotate" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p_len = len(self.getData(x["child"]))
                    p2 = None
                    if 3 < p_len:
                        p2 = self.getDataInt(x["child"][2])
                    self.doLogrotate(command_name, line, p1, p2)
                elif "logstart" == command_name:
                    self.doLogstart()
                elif "logwrite" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.doLogwrite(p1)
                elif "recvln" == command_name:
                    self.doRecvln()
                elif "scprecv" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = p1
                    if 3 <= len(x["child"]):
                        p2 = str(self.getData(x["child"][2]))
                    self.doScprecv(p1, p2)
                elif "scpsend" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = p1
                    if 3 <= len(x["child"]):
                        p2 = str(self.getData(x["child"][2]))
                    self.doScpsend(p1, p2)
                elif command_name in ["send", "sendbinary", "sendtext"]:
                    self.doSend(x["child"][1:])
                elif "sendbreak" == command_name:
                    self.doSendbreak()
                elif "sendln" == command_name:
                    self.doSendln(x["child"][1:])
                elif "settitle" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.setTitle(p1)
                elif "testlink" == command_name:
                    self.doTestlink()
                elif command_name in ["wait", "wait4all"]:
                    self.doWait(x["child"][1:])
                elif "waitln" == command_name:
                    self.doWaitln(x["child"][1:])
                elif "execcmnd" == command_name:
                    p1 = self.getData(x["child"][1])
                    result_json = self.include_data(p1)
                    self.execute_result(result_json["child"])
                elif "mpause" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doPause(p1 / 1000)
                elif "pause" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doPause(p1)
                elif "code2str" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = x["child"][2]
                    p2 = self.getData(p2)
                    if p2 == 0:
                        self.setValue(p1, "")
                    else:
                        p2 = self.getChrSharp(p2)
                        self.setValue(p1, p2)
                elif "expandenv" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = ""
                    if 3 <= len(x["child"]):
                        p2 = self.getData(x["child"][2])
                    else:
                        p2 = self.getData(p1)
                    self.doExpandenv(p1, p2)
                elif "int2str" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    self.setValue(p1, p2)
                elif "sprintf" == command_name:
                    self.doSprintf("inputstr", x["child"][1:])
                elif "sprintf2" == command_name:
                    p1 = x["child"][1]
                    p1 = self.getKeywordName(p1)
                    self.doSprintf(p1, x["child"][2:])
                elif "str2code" == command_name:
                    # print("str2code")
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = x["child"][2]
                    # print(f"p2A={p2}")
                    p2 = self.getData(p2)
                    # print(f"p2B={p2}")
                    p2 = self.getSharpChr(p2)
                    # print(f"p2C={p2}")
                    self.setValue(p1, p2)
                elif "str2int" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getDataInt(x["child"][2])
                    self.setValue(p1, p2)
                elif "strcompare" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    result = 0
                    if p1 == p2:
                        result = 0
                    elif p1 < p2:
                        result = -1
                    else:
                        result = 1
                    self.setValue("result", result)
                elif "strconcat" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p1_str = self.getValue(p1)
                    p2_str = x["child"][2]
                    p1_str = p1_str + self.getData(p2_str)
                    self.setValue(p1, p1_str)
                elif "strcopy" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = self.getDataInt(x["child"][2]) - 1  # 1オリジン
                    p3 = self.getDataInt(x["child"][3])
                    p4 = self.getKeywordName(x["child"][4])
                    if p2 < 0:
                        p2 = 0
                    p1 = p1[p2: p2 + p3]
                    self.setValue(p4, p1)
                elif "strinsert" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getDataInt(x["child"][2]) - 1  # 1オリジン
                    p3 = str(self.getData(x["child"][3]))
                    p1_val = self.getData(p1)
                    # print(f"### l={line} {command_name} {p1} {p2} {p3} {p1_val}")
                    p1_val = p1_val[:p2] + p3 + p1_val[p2:]
                    self.setValue(p1, p1_val)
                elif "strjoin" == command_name:
                    # print(f"### l={line} {command_name}")
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p3 = 9
                    # print(f"len {len(x['child'])}")
                    if 4 <= len(x["child"]):
                        p3 = self.getDataInt(x["child"][3])
                    p1_val = ""
                    for i in range(p3):
                        if i != 0:
                            p1_val = p1_val + p2
                        p1_val = p1_val + self.getValue("groupmatchstr" + str(i + 1))
                    self.setValue(p1, p1_val)
                elif "strlen" == command_name:
                    p1 = len(self.getData(x["child"][1]))
                    self.setValue("result", p1)
                elif "strmatch" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    self.doStrmatch(p1, p2)
                elif "strremove" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getDataInt(x["child"][2]) - 1  # 1オリジン
                    p3 = self.getDataInt(x["child"][3])
                    p1_val = self.getData(p1)
                    # print(f"### l={line} {command_name} {p1} {p2} {p3} {p1_val}")
                    p1_val = p1_val[:p2] + p1_val[p2 + p3:]
                    self.setValue(p1, p1_val)
                elif "strreplace" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p1_val = self.getData(p1)
                    p2 = self.getDataInt(x["child"][2]) - 1  # 1オリジン
                    p3 = str(self.getData(x["child"][3]))
                    p4 = str(self.getData(x["child"][4]))
                    self.doStrreplace(p1, p1_val, p2, p3, p4)
                elif "strscan" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    index = p1.find(p2)
                    if index < 0:
                        index = 0
                    else:
                        index = index + 1
                    # print(f"strscan {index}")
                    self.setValue("result", index)
                elif "strspecial" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p1_val = self.getData(p1)
                    if 3 <= len(x["child"]):
                        p1_val = str(self.getData(x["child"][2]))
                    p1_val = p1_val.encode().decode("unicode_escape")
                    self.setValue(p1, p1_val)
                elif "strsplit" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p1_val = self.getData(p1)
                    p2 = str(self.getData(x["child"][2]))
                    p3 = 10
                    if 4 <= len(x["child"]):
                        p3 = self.getDataInt(x["child"][3])
                    for i in range(9):
                        self.setValue("groupmatchstr" + str(i + 1), "")
                    i = 0
                    while i < p3 - 1:
                        index = p1_val.find(p2)
                        if 0 <= index:
                            # print(f"aa i{i + 1} {p3} /{p1_val[0:index]}/ /{p1_val[index + len(p2):]}/")
                            self.setValue("groupmatchstr" + str(i + 1), p1_val[0:index])
                            p1_val = p1_val[index + len(p2):]
                        else:
                            break
                        i = i + 1
                    if 0 < len(p1_val):
                        # print(f"bb i{i + 1} {p3} /{p1_val}/")
                        self.setValue("groupmatchstr" + str(i + 1), p1_val)
                    i = i + 1
                    # print(f"i={i}")
                    self.setValue("result", i)
                elif "strtrim" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p1_var = self.getData(p1)
                    p2 = self.getData(x["child"][2])
                    p1_var = self.doStrtrim(p1_var, p2)
                    self.setValue(p1, p1_var)
                elif "tolower" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p2 = p2.lower()
                    self.setValue(p1, p2)
                elif "toupper" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p2 = p2.upper()
                    self.setValue(p1, p2)
                elif "basename" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p2 = self.normpath(p2)
                    p2 = os.path.basename(p2)
                    self.setValue(p1, str(p2))
                elif "dirname" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p2 = self.normpath(p2)
                    # print(f"p2a={p2}")
                    p2 = re.sub(r"[\/]$", "", p2)
                    p2 = pathlib.Path(p2)
                    # print(f"p2b={p2}")
                    p2 = str(p2.parent)
                    # print(f"p2c={p2}")
                    self.setValue(p1, str(p2))
                elif command_name in ["fileclose", "findclose"]:
                    p1 = self.getKeywordName(x["child"][1])
                    self.doFileclose(p1)
                elif "fileconcat" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    self.doFileconcat(p1, p2)
                elif "filecopy" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    self.doFilecopy(p1, p2)
                elif "filecreate" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doFileopen(p1, p2, 0, 0)
                elif "filedelete" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.doFiledelete(p1)
                elif "fileopen" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    p3 = self.getDataInt(x["child"][3])
                    p4 = 0
                    if 5 <= len(x["child"]):
                        p4 = self.getData(x["child"][4])
                    self.doFileopen(p1, p2, p3, p4)
                elif "filereadln" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    p2 = str(self.getKeywordName(x["child"][2]))
                    self.doFilereadln(line, p1, p2)
                elif "fileread" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getDataInt(x["child"][2])
                    p3 = self.getKeywordName(x["child"][3])
                    self.doFileread(line, p1, p2, p3)
                elif "filerename" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    self.doFilerename(p1, p2)
                elif "filesearch" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.doFilesearch(p1)
                elif "filestat" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getKeywordName(x["child"][2]))
                    p3 = None
                    if 4 <= len(x["child"]):
                        p3 = str(self.getKeywordName(x["child"][3]))
                    p4 = None
                    if 4 <= len(x["child"]):
                        p4 = str(self.getKeywordName(x["child"][4]))
                    self.doFilestat(p1, p2, p3, p4)
                elif "filetruncate" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = self.getDataInt(x["child"][2])
                    self.doFiletruncate(p1, p2)
                elif "filewrite" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doFilewrite(line, p1, p2)
                elif "filewriteln" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2]) + "\n"
                    self.doFilewrite(line, p1, p2)
                elif "findfirst" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p3 = self.getKeywordName(x["child"][3])
                    self.doFindfirst(line, p1, p2, p3)
                elif "findnext" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    p2 = str(self.getKeywordName(x["child"][2]))
                    self.doFindnext(line, p1, p2)
                elif "foldercreate" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.doFoldercreate(p1)
                elif "folderdelete" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.doFolderdelete(p1)
                elif "foldersearch" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    self.doFoldersearch(p1)
                elif "getdir" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    path = pathlib.Path.cwd()
                    self.setValue(p1, str(path))
                elif "makepath" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = str(self.getData(x["child"][2]))
                    p3 = str(self.getData(x["child"][3]))
                    self.doMakepath(p1, p2, p3)
                elif command_name in ["setpassword", "setpassword2"]:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    p3 = str(self.getData(x["child"][3]))
                    p4 = "anonymouse"
                    if 5 <= len(x["child"]):
                        p4 = str(self.getData(x["child"][4]))
                    self.doSetpassword(p1, p2, p3, p4)
                elif command_name in ["getpassword", "getpassword2"]:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    p3 = str(self.getKeywordName(x["child"][3]))
                    p4 = "anonymouse"
                    if 5 <= len(x["child"]):
                        p4 = str(self.getData(x["child"][4]))
                    self.doGetpassword(p1, p2, p3, p4)
                elif command_name in ["ispassword", "ispassword2"]:
                    p1 = self.getData(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doIspassword(p1, p2)
                elif command_name in ["delpassword", "delpassword2"]:
                    p1 = self.getData(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doDelpassword(p1, p2)
                elif "checksum8" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doChecksum8(p1, p2)
                elif "checksum8file" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doChecksum8file(p1, p2)
                elif "checksum16" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doChecksum16(p1, p2)
                elif "checksum16file" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doChecksum16file(p1, p2)
                elif "checksum32" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doChecksum32(p1, p2)
                elif "checksum32file" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doChecksum32file(p1, p2)
                elif "crc16" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doCrc16(p1, p2)
                elif "crc16file" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doCrc16file(p1, p2)
                elif "crc32" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doCrc32(p1, p2)
                elif "crc32file" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    p2 = self.getData(x["child"][2])
                    self.doCrc32file(p1, p2)
                elif "exec" == command_name:
                    self.doExec(line, x["child"][1:])
                elif "getdate" == command_name:
                    self.doGetdate(x["child"][1:])
                elif "getenv" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = self.getKeywordName(x["child"][2])
                    # print(f"getenv1 c=({command_name}) l={p1} r={p2}")
                    p1 = os.getenv(p1)
                    if p1 is None:
                        p1 = ""
                    # print(f"getenv2 c=({command_name}) l={p1} r={p2}")
                    self.setValue(p2, p1)
                elif "getipv4addr" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    p2 = str(self.getKeywordName(x["child"][2]))
                    self.doGetipv4addr(p1, p2)
                elif "getipv6addr" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    p2 = str(self.getKeywordName(x["child"][2]))
                    self.doGetipv6addr(p1, p2)
                elif "gettime" == command_name:
                    self.doGetdate(x["child"][1:], format="%H:%M:%S")
                elif "getttdir" == command_name:
                    p1 = self.getKeywordName(x["child"][1])
                    self.setValue(p1, self.current_dir)
                elif "getver" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    p2 = None
                    if 3 <= len(x["child"]):
                        p2 = float(self.getData(x["child"][2]))
                    self.doGetver(p1, p2)
                elif "ifdefined" == command_name:
                    p1 = str(x["child"][1])
                    self.doIfdefined(p1)
                elif "intdim" == command_name:
                    p1 = x["child"][1]
                    p2 = self.getDataInt(x["child"][2])
                    for i in range(p2):
                        self.setValue(p1 + "[" + str(i) + "]", 0)
                elif "random" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    p2 = self.getDataInt(x["child"][2])
                    p1_val = random.randint(0, p2)
                    self.setValue(p1, p1_val)
                elif "setenv" == command_name:
                    p1 = str(self.getData(x["child"][1]))
                    p2 = str(self.getData(x["child"][2]))
                    os.environ[p1] = p2
                    # print(f"setenv2 c=({command_name}) l={p1} r={p2}")
                elif "setexitcode" == command_name:
                    p1 = self.getDataInt(x["child"][1])
                    self.doSetexitcode(p1)
                elif "strdim" == command_name:
                    p1 = x["child"][1]
                    p2 = self.getDataInt(x["child"][2])
                    for i in range(p2):
                        self.setValue(p1 + "[" + str(i) + "]", "")
                elif "uptime" == command_name:
                    p1 = str(self.getKeywordName(x["child"][1]))
                    self.setValue(p1, int(uptime.uptime() * 1000))
                else:
                    # print(f"### l={line} コマンドが分からない{name}")
                    self.commandContext(command_name, line, x["child"][1:])
            elif "ForNextContext" == name:
                self.forNextContext(x["child"])
            elif "WhileEndwhileContext" == name:
                self.whileEndwhileContext(x["child"])
            elif "UntilEnduntilContext" == name:
                self.untilEnduntilContext(x["child"])
            elif "DoLoopContext" == name:
                self.doLoopContext(x["child"])
            elif "If1Context" == name:
                self.if1Context(x["child"])
            elif "If2Context" == name:
                self.if2Context(x["child"])
            elif "LabelContext" != name:
                pass
            else:
                self.stop(error=f"### l={line} Unkown name={name}")
            if self.end_flag:
                break

    def commandContext(self, name, line, data_list):
        """(GUI系を)オーバーライドさせて使う"""
        # GUIでしかできないのでダニーを入れておく
        if name in ["passwordbox", "inputbox", "listbox"]:
            # print(f"super.commandContext {name} start")
            self.printCommand(name, line, data_list)
            self.setValue("inputstr", "aaa")
            # print(f"super.commandContext {name} end")
        elif name in [
            "bringupbox",
            "closesbox",
            "messagebox",
            "statusbox",
            "setdlgpos",
        ]:
            self.printCommand(name, line, data_list)
        elif "dirnamebox" == name:
            self.printCommand(name, line, data_list)
            self.setValue("result", 1)
            self.setValue("inputstr", str(os.getcwd()))
        elif "filenamebox" == name:
            self.printCommand(name, line, data_list)
            self.setValue("result", 0)
            self.setValue("inputstr", "tmp.txt")
        elif name in ["yesnobox"]:
            self.printCommand(name, line, data_list)
            self.setValue("result", 1)
        elif name in ["showtt"]:
            self.printCommand(name, line, data_list)
            self.setValue(self.getKeywordName(data_list[0]), 0)
        elif name in ["setdlgpos", "show", "callmenu", "enablekeyb"]:
            pass
        else:
            self.printCommand(name, line, data_list)
            raise TypeError(f"### l={line} Unsupport command={name}")

    def printCommand(self, name: str, line: int, data_list) -> str:
        message = f"### l={line} c={name}"
        for data in data_list:
            keywordName = None
            try:
                keywordName = self.getKeywordName(data)
            except TypeError:
                # print(f"type error {e}")
                pass
            result = self.getData(data)
            if isinstance(result, int):
                result = str(result)
            elif isinstance(result, Label):
                result = "LABEL"
            if keywordName is None:
                message = message + f" p({result})"
            else:
                message = message + f" p({keywordName}/{result})"
        self.setLog(message + "\n")
        return message

    def correctLabel(self):
        """ラベルを収集する"""
        self.correctLabelAll(self.result_file_json.values())

    def correctLabelAll(self, token_list_list: list):
        """ラベルを収集する"""
        i = -1
        for token_dict in token_list_list:
            i = i + 1
            name = token_dict["name"]  # StatementContext
            # print(f"correctLabelAll i={i} {name}")
            if "StatementContext" == name:
                # print("hit")
                self.correctLabelAll(token_dict["child"])  # StatementContext
            elif "CommandlineContext" == name:
                # print("hit2")
                j = -1
                next_list = token_dict["child"]
                for next in next_list:
                    j = j + 1
                    if "LabelContext" == next["name"]:
                        # print(f"hot3 {next['child']}")
                        label_name = next["child"][1]
                        # print("hit4")
                        label = Label(token_list_list[i + 1:])
                        # print(f"xxx data={label_name} // {label.getTokenList()}")
                        self.setValueLabel(label_name, label)
            #
            if self.end_flag:
                break

    def callContext(self, line, label):
        #
        try:
            # print("callContest")
            label = self.getValue(label, error_stop=False)
            if label is None:
                raise TypeError(f"### l={line} No hit label error none label={label}")
            if not isinstance(label, Label):
                raise TypeError(f"### l={line} No hit label error label={label}")
            for token in label.getTokenList():
                # print(f"hit x {token}")
                self.execute_result([token])
                if self.end_flag:
                    break
        except TtlReturnFlagException:
            # print("TtlReturnFlagException")
            pass
        #

    def forNextContext(self, data_list):
        intvar = self.getKeywordName(data_list[1])
        first = self.getDataInt(data_list[2])
        self.setValue(intvar, first)
        last = self.getDataInt(data_list[3])
        # print(f"for intvar={intvar} first={first} last={last}")
        add = -1
        if first < last:
            add = 1
        while True:
            #
            try:
                self.execute_result(data_list[4:-1])
                #
                if self.end_flag:
                    break
                #
                self.setValue(intvar, self.getValue(intvar) + add)
                if 0 < add:
                    if last < self.getValue(intvar):
                        break
                else:
                    if self.getValue(intvar) < last:
                        break
            except TtlContinueFlagException:
                pass
            except TtlBreakFlagException:
                break

    def whileEndwhileContext(self, data_list):
        while self.getDataInt(data_list[1]) != 0:
            try:
                #
                self.execute_result(data_list[2:-1])
                #
                if self.end_flag:
                    break
            except TtlContinueFlagException:
                pass
            except TtlBreakFlagException:
                break

    def untilEnduntilContext(self, data_list):
        while self.getDataInt(data_list[1]) == 0:
            try:
                #
                self.execute_result(data_list[2:-1])
                #
                if self.end_flag:
                    break
            except TtlContinueFlagException:
                pass
            except TtlBreakFlagException:
                break

    def doLoopContext(self, data_list):
        while True:
            try:
                for data in data_list:
                    if isinstance(data, str):
                        # do/loop
                        # print(f"do/loop={data}")
                        pass
                    elif "CommandlineContext" == data["name"]:
                        # print(f"LineContext={data}")
                        self.execute_result([data])
                    else:
                        # print(f"data={data['name']}")
                        value = self.getDataInt(data)
                        # print(f"value ={value}")
                        if value == 0:
                            # print(f"data ok={data}")
                            raise TtlBreakFlagException("doLoopContext")
            except TtlContinueFlagException:
                pass
            except TtlBreakFlagException:
                break

    def if1Context(self, data_list):
        first = self.getDataInt(data_list[1])
        # print(f"if1 first={first}")
        if 0 != first:
            self.execute_result(data_list[2:])

    def if2Context(self, data_list):
        first = self.getDataInt(data_list[1])
        # print(f"if2 first={first}")
        self.execute_result(data_list[3:-1], first)

    def getDataInt(self, data) -> int:
        try:
            result = self.getData(data)
            result = int(result)
        except (TypeError, ValueError) as e:
            if isinstance(data, dict):
                if "line" in data:
                    raise TypeError(f"### l={data['line']} {type(e).__name__} e={e}")
            raise  # そのまま上流へ送る
        return result

    def getData(self, data):
        """構文解析からデータを抽出する"""
        result = ""
        if isinstance(data, str):
            result = self.getValue(data)
        elif "name" not in data:
            raise TypeError(f"unkown name data={str(data)}")
        elif "P11ExpressionContext" == data["name"]:
            result = self.p11ExpressionContext(data["child"])
        elif "P10ExpressionContext" == data["name"]:
            result = self.p10ExpressionContext(data["child"])
        elif "P9ExpressionContext" == data["name"]:
            result = self.p9ExpressionContext(data["child"])
        elif "P8ExpressionContext" == data["name"]:
            result = self.p8ExpressionContext(data["child"])
        elif "P7ExpressionContext" == data["name"]:
            result = self.p7ExpressionContext(data["child"])
        elif "P6ExpressionContext" == data["name"]:
            result = self.p6ExpressionContext(data["child"])
        elif "P5ExpressionContext" == data["name"]:
            result = self.p5ExpressionContext(data["child"])
        elif "P4ExpressionContext" == data["name"]:
            result = self.p4ExpressionContext(data["child"])
        elif "P3ExpressionContext" == data["name"]:
            result = self.p3ExpressionContext(data["child"])
        elif "P2ExpressionContext" == data["name"]:
            result = self.p2ExpressionContext(data["child"])
        elif "P1ExpressionContext" == data["name"]:
            result = self.p1ExpressionContext(data["child"])
        elif "IntExpressionContext" == data["name"]:
            result = self.intExpressionContext(data["child"])
        elif "StrExpressionContext" == data["name"]:
            result = self.strExpressionContext(data["child"])
        elif "IntContextContext" == data["name"]:
            result = self.intContext(data["child"])
        elif "StrContextContext" == data["name"]:
            result = self.strContext(data["child"])
        elif "KeywordContext" == data["name"]:
            result = self.keywordContext(data)
        else:
            raise TypeError(f"unkown keyword n={data['name']}")
        return result

    def p11ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        val2 = self.getDataInt(data[2])
        result = val1 or val2
        # print(f"p11 {val1:x}/{val2:x}/{result:x}")
        return result

    def p10ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        val2 = self.getDataInt(data[2])
        result = val1 and val2
        # print(f"p10 {val1:x}/{val2:x}/{result:x}")
        return result

    def p9ExpressionContext(self, data: list):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        # print(f"p9ExpressionContext count={count} data={data[0]['name']} child={data[0]['child'][0]} ")
        # print(f"xxx {data[0]}")
        val1 = self.getDataInt(data[0])
        # print("xxx 2")
        oper = data[1]
        # print(f"p9ExpressionContext count={1} data={oper}")
        # print(f"p9ExpressionContext count={2} data={data[2]['name']} child={data[2]['child']} ")
        val2 = self.getDataInt(data[2])
        result = 0
        if "==" == oper or "=" == oper:
            result = val1 == val2
        else:  # <> or !=
            result = val1 != val2
        if result:
            return 1
        return 0

    def p8ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        oper = data[1]
        val2 = self.getDataInt(data[2])
        result = 0
        if "<" == oper:
            result = val1 < val2
        elif "<=" == oper:
            result = val1 <= val2
        elif ">" == oper:
            result = val1 > val2
        else:  # '>='
            result = val1 >= val2
        if result:
            return 1
        return 0

    def p7ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        # oper = data[1]
        val2 = self.getDataInt(data[2])
        result = val1 | val2
        # print(f"p7 oper={oper}")
        return result

    def p6ExpressionContext(self, data):
        # print(f"p6 d={data}")
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        # oper = data[1]
        val2 = self.getDataInt(data[2])
        result = val1 ^ val2
        # print(f"p6 oper={oper} {val1:x}/{val2:x}/{result:x}")
        return result

    def p5ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        val2 = self.getDataInt(data[2])
        result = val1 & val2
        # print(f"p5 {val1:x}/{val2:x}/{result:x}")
        return result

    def p4ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        oper = data[1]
        val2 = self.getDataInt(data[2])
        result = 0
        if ">>>" == oper:
            result = val1 >> val2
        elif ">>" == oper:
            result = val1 >> val2
        elif "<<" == oper:
            result = val1 << val2
        return result

    def p3ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        oper = data[1]
        val2 = self.getDataInt(data[2])
        result = 0
        if "+" == oper:
            result = val1 + val2
        elif "-" == oper:
            result = val1 - val2
        return result

    def p2ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[0])
        oper = data[1]
        val2 = self.getDataInt(data[2])
        result = 0
        if "*" == oper:
            result = val1 * val2
        elif "/" == oper:
            try:
                result = val1 // val2
            except ZeroDivisionError as e:
                raise TypeError(f"ZeroDivisionError e={str(e)}")
        elif "%" == oper:
            try:
                result = val1 % val2
            except ZeroDivisionError as e:
                raise TypeError(f"ZeroDivisionError e={str(e)}")
        return result

    def p1ExpressionContext(self, data):
        count = len(data)
        if count == 1:
            return self.getData(data[0])
        val1 = self.getDataInt(data[1])
        if 0 == val1:
            return 1
        return 0

    def intExpressionContext(self, data_list):
        count = len(data_list)
        if count == 1:
            return self.getData(data_list[0])
        else:
            # ()表現=data_list[0]には'('が入っている
            return self.getData(data_list[1])

    def strExpressionContext(self, data_list):
        return self.getData(data_list[0])

    def strContext(self, data_list):
        # print(f"str={data_list}")
        result = ""
        for data in data_list:
            state = 0
            old = ""
            for i in range(len(data)):
                hit_flag = False
                ch0 = data[i]
                # print(f"\tch0={ch0}")
                if state == 0:
                    if ch0 == "'":
                        state = 1
                        hit_flag = True
                    elif ch0 == '"':
                        state = 2
                        hit_flag = True
                    elif ch0 == "#":
                        hit_flag = True
                    else:
                        old = old + ch0
                    if hit_flag:
                        result = result + self.getChrSharp_str(old)
                        old = ""  # clear
                        if ch0 == "#":
                            old = ch0
                elif state == 1:
                    if ch0 == "'":
                        state = 0
                    else:
                        result = result + ch0
                elif state == 2:
                    if ch0 == '"':
                        state = 0
                    else:
                        result = result + ch0
            result = result + self.getChrSharp_str(old)
        # print(f"result={result}")
        return result

    def getChrSharp_str(self, base) -> str:
        if len(base) <= 0:
            return ""
        #
        # print(f"\tbaseB={base}")
        if "#" == base[0]:
            # print(f"\tbaseC={base} data={base[1:]}")
            base = self.getChrSharp(self.getAsciiNum(base[1:]))
            # print(f"\tbaseD={base} data={base[1:]}")
        elif "$" == base[0]:
            base = self.getAsciiNum(base)
        return base

    def getChrSharp(self, data: int) -> str:
        if data <= 0:
            return chr(data & 0xFF)
        result = ""
        while 0 < data:
            result = chr(data & 0xFF) + result
            data = data >> 8
        return result

    def getSharpChr(self, data: str) -> int:
        # print(f"getSharpChr {data}")
        if len(data) <= 0:
            return ""
        result = 0
        while "" != data:
            result = (result * 256) + ord(data[0])
            data = data[1:]
        return result

    def intContext(self, data_list) -> int:
        result = 0
        data = data_list[0]
        # print(f"intContext={data}")
        if 0 < len(data) and data[0] == "$":
            result = self.getAsciiNum(data)
        else:
            result = int(data)
        return result

    def getAsciiNum(self, data: str) -> int:
        # print(f"getAsciiNum={data} len={len(data)} data[0]={data[0]}")
        if (0 < len(data)) and ("$" == data[0]):
            ans = int(data[1:], 16)
            # print(f"data[1:]={data[1:]} ans={ans}")
            return ans
        return int(data)

    def getKeywordName(self, data):
        """構文内のキーワード名を取得する"""
        # print(f"keywordName {data}")
        if "name" not in data:
            if isinstance(data, str):
                return data
            elif isinstance(data, list):
                return data[0]
            raise TypeError("keywordName name not in data")
        #
        # this is dict
        if "StrExpressionContext" == data["name"]:
            return self.getKeywordName(data["child"][0])
        elif "KeywordContext" != data["name"]:
            raise TypeError(
                f"### l={data['line']} keywordName name is not KeywordContext {data}"
            )
        #
        data = data["child"]
        # print(f"data={data} len={len(data)}")
        if len(data) == 1:
            # 単純指定
            return data[0]
        else:
            # 配列対策
            index = data[2]
            index = self.getData(index)
            return data[0] + "[" + str(int(index)) + "]"

    def keywordContext(self, data):
        """構文内のキーワードから値を抽出する"""
        # print(f"keywordContext data={data}")
        return self.getValue(self.getKeywordName(data))

    def doAssert(self, command_name: str, line: int, data_list) -> str:
        """assert 処理用"""
        message = self.printCommand(command_name, line, data_list)
        p1 = self.getData(data_list[0])
        if p1 == 0:
            raise TypeError(message)

    def doBplusrecv(self, command_name: str, line: int):
        """bplusrecv 処理用"""
        self.printCommand(command_name, line, [])

    def doBplussend(self, command_name: str, line: int, p1):
        """bplussend 処理用"""
        self.printCommand(command_name, line, [p1])

    def doCallmenu(self, command_name: str, line: int, p1):
        """callmenu 処理用"""
        self.printCommand(command_name, line, [p1])

    def doChangedir(self, p1):
        """changedir 処理用"""
        p1 = pathlib.Path(p1)
        if p1.is_absolute():
            # print(f"pathA={p1}")
            os.chdir(p1)
        else:
            # print(f"pathB={p1}")
            p1 = pathlib.Path.cwd() / p1
            os.chdir(p1)

    def doClearscreen(self, command_name: str, line: int, p1):
        """clearscreen 処理用"""
        self.printCommand(command_name, line, [p1])

    def doConnect(self, data: str, line):
        """接続する"""
        # print(f"do connect data={data}")
        if self.client is not None:
            self.setValue("error", "Already connected")
            self.setValue("result", 0)
            return
        param_list = re.split(r"[ \t]+", data)
        server = "localhost"
        user = None
        passwd = None
        keyfile = None
        port_number = 22
        param_cmd = False
        for param in param_list:
            if len(param) <= 0:
                continue
            if param[0] != "/":
                server = param.split(":")
                if len(server) == 1:
                    server = server[0]
                elif len(server) == 2:
                    port_number = int(server[1])
                    server = server[0]
                else:
                    self.setValue("error", "Invalid server name")
                    self.setValue("result", 0)
                    return
            else:
                user_string = "user="
                passwd_string = "passwd="
                keyfile_string = "keyfile="
                param = param[1:]
                # print(f"\tparam={param}")
                if "ssh" == param:
                    pass
                elif "1" == param:
                    self.setValue("error", "SSH1 not support")
                    self.setValue("result", 0)
                    return
                elif "2" == param:
                    pass  # SSH2
                elif "cmd" == param:
                    param_cmd = True
                elif "ask4passwd" == param:
                    self.setValue("error", "Not Support ask4passwd error!")
                    self.setValue("result", 0)
                    return
                elif "auth=password" == param:
                    pass  # わからん
                elif "auth=publickey" == param:
                    pass  # わからん
                elif "auth=challenge" == param:
                    pass  # わからん
                elif re.search("^" + user_string, param):
                    user = param[len(user_string):]
                elif re.search("^" + passwd_string, param):
                    passwd = param[len(passwd_string):]
                elif re.search("^" + keyfile_string, param):
                    keyfile = param[len(keyfile_string):]
                    keyfile = self.normpath(keyfile)
                else:
                    # 知らないパラメータが来たら停止する
                    self.setValue("error", f"unkown paramater={param}")
                    self.setValue("result", 0)
                    return
        #
        # 前の接続は削除
        self.closeClient()
        #
        # ここから接続処理
        if not param_cmd:
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                #
                # print(f"p1 {server}, port={port_number}, username={user}, password={passwd}, key_filename={keyfile}")
                self.client.connect(
                    server,
                    port=port_number,
                    username=user,
                    password=passwd,
                    key_filename=keyfile,
                )
                # print(f"p2 {server}, port={port_number}, username={user}, password={passwd}, key_filename={keyfile}")
                #
                self.shell = self.client.invoke_shell()
                if self.shell is None:
                    raise paramiko.SSHException("shell is None")
                # print(f"p3 {server}, port={port_number}, username={user}, password={passwd}, key_filename={keyfile}")
                #
                # 接続成功
                #
                self.setValue("result", 2)
                self.log_connect_time = time.time()
                # print("connect OK !")
                #
            except (
                socket.gaierror,
                paramiko.ssh_exception.NoValidConnectionsError,
                paramiko.AuthenticationException,
                paramiko.SSHException,
            ) as e:
                self.setValue("error", f"### l={line} {type(e).__name__} e={e}")
                self.setValue("result", 0)
                self.closeClient()
        else:
            if platform.system().lower() == "linux":
                # ここから expect 起動
                self.shell = MyPexpect()
            else:
                # ここから cmd 起動
                self.shell = MyShell()
            #
            # 接続成功
            self.setValue("result", 2)

    def doDispstr(self, data_list):
        for data in data_list:
            result = self.getData(data)
            if isinstance(result, int):
                result = chr(data & 0xFF)
            self.setLogInner(result)

    def doEnablekeyb(self, command_name: str, line: int, p1):
        """enablekeyb 処理用"""
        pass

    def doGetmodemstatus(self, command_name: str, line: int, p1):
        """getmodemstatus 処理用"""
        # print(f"{p1}")
        self.setValue(p1, 0)
        self.setValue("result", 1)  # 必ず失敗

    def doGethostname(self, p1):
        """ホスト名の取得"""
        if self.client is not None and self.shell is not None and self.shell.active:
            # 外部と接続しているとき
            ip_address = self.client.get_transport().getpeername()[0]
            self.setValue(p1, ip_address)
        else:
            #
            # 何もリンクしていない、または cmdと接続しているとき
            hostname = socket.gethostname()
            self.setValue(p1, hostname)

    def doTestlink(self):
        if self.shell is None or not self.shell.active:
            self.setValue("result", 0)
        else:
            self.setValue("result", 2)

    def doSend(self, data_list):
        # print(f"doSend() d={data_list}")
        for data in data_list:
            result = self.getData(data)
            self.doSendAll(result)

    def doSendln(self, data_list):
        # print(f"doSendln() d={data_list}")
        if len(data_list) <= 0:
            self.doSendAll("\n")
        else:
            for data in data_list:
                message = self.getData(data)
                self.doSendAll(message + "\n")

    def doSendbreak(self):
        # print(f"doSendbreak() d={data_list}")
        self.doSendAll("\x03")

    def doSendAll(self, message):
        # print(f"doSendAll d={message}")
        while not self.end_flag:
            local_shell = self.shell
            if local_shell is None:
                # print("doSendAll shell None")
                break
            elif local_shell.send_ready():
                # print(f"send! f=/{message}/")
                local_shell.send(message)
                break
            else:
                time.sleep(0.1)

    def doWait(self, data_list):
        result_list = []
        for data in data_list:
            result = self.getData(data)
            result_list.append(result)
        self.doWaitAll(result_list)

    def doWaitln(self, data_list):
        result_list = []
        for data in data_list:
            result = self.getData(data) + "\n"
            result_list.append(result)
        self.doWaitAll(result_list)

    def doRecvln(self):
        result_list = ["\n"]
        self.doWaitAll(result_list)

    def doFlushrecv(self):
        """do flush"""
        # すでに読んだものを空にする
        self.stdout = ""
        #
        # まだ読めてないものを空にする
        while not self.end_flag:
            #
            local_ssh = self.shell
            if local_ssh is None:
                break
            #
            if not local_ssh.recv_ready():
                break
            #
            output = local_ssh.recv(1024).decode("utf-8")
            if output is None:
                break
            self.setLogInner(output)

    def doWaitAll(self, result_list):
        # print(f"doWaitAll x=/{result_list}/")
        m_timeout = self.getTimer()
        now_time = time.time()
        result = 0
        hit_flag = False
        self.setValue("result", 0)
        while not self.end_flag and not hit_flag:
            #
            if m_timeout != 0:
                r_time = (now_time + m_timeout) - time.time()
                # print(f"\ndoWaitAll {r_time} / {m_timeout}")
                if r_time < 0:
                    result = 0  # timeout
                    # print(f"hit1! {r_time}")
                    break
            #
            # 生成したものでヒットするか確認
            result = 1
            max = None
            result_len = ""
            #
            # 全件チェックする
            for i, reslut_text in enumerate(result_list):
                index = self.stdout.find(reslut_text)
                if 0 <= index:
                    hit_flag = True
                    if max is None or index < max:
                        # 最初にヒットしたか、より最初にヒットする方を選ぶ
                        max = index
                        result_len = len(reslut_text)
                        result = i + 1
            #
            if hit_flag:
                # 見つかった地点まで切り飛ばす
                # print(f"remain1=/{self.stdout}/ cutlen={max + result_len}")
                self.stdout = self.stdout[max + result_len:]
                # print(f"remain2=/{self.stdout.strip()}/")
                self.setValue("result", result)
                # ヒットしていたら終了
                break
            #
            local_ssh = self.shell
            if local_ssh is None:
                break
            #
            # m_timeout は 0 の時無限待ちになる
            if local_ssh.recv_ready():
                now_time = time.time()  # 最後の時間更新
                # print("recv start! ============")
                output = local_ssh.recv(1024).decode("utf-8")
                # print(f"recv! end {output} ============")
                if output is None:
                    break
                self.setLogInner(output)
                self.stdout = self.stdout + output
                #
            else:
                # print("sleep")
                time.sleep(0.1)

    def getTimer(self) -> float:
        m_timeout = 0.0
        x = self.getValue("timeout", error_stop=False)
        if x is not None:
            m_timeout = int(x)
        x = self.getValue("mtimeout", error_stop=False)
        if x is not None:
            m_timeout = m_timeout + (int(x) / 1000)
        return m_timeout

    def doLogautoclosemode(self, name, line, p1):
        self.commandContext(name, line, (p1))

    def doLogclose(self):
        log_file_handle = self.log_file_handle
        self.log_file_handle = None
        if log_file_handle is not None:
            try:
                log_file_handle.close()
            except Exception:
                pass
        #
        # 他も初期化する
        self.log_start = True
        self.log_timestamp_type = -1
        self.log_connect_time = None

    def doLoginfo(self, name, line, p1):
        self.commandContext(name, line, (p1))

    def doLogopen(
        self,
        filename,
        binary_flag,
        append_flag,
        plain_text_flag,
        timestamp_flag,
        hide_dialog_flag,
        include_screen_buffer_flag,
        timestamp_type,
    ):
        """open the log"""
        # 開いているものがあったらクローズする
        self.doLogclose()
        #
        filename = self.normpath(filename)
        #
        option = 'wb'
        # print(f"append_flag={append_flag}")
        if append_flag != 0:
            option = 'ab'
        if binary_flag != 0:
            # plain_text_flag = 0
            timestamp_flag = 0
        if timestamp_flag == 0:
            timestamp_type = -1
        #
        # タイムスタンプの変数を入れる
        self.log_timestamp_type = timestamp_type
        #
        self.log_file_handle = open(filename, option)
        #
        # タイムスタンプありなら最初に書き込む
        if self.log_timestamp_type != -1:
            self.log_file_handle.write(self.getTimestamp().encode("utf-8"))

    def doLogpause(self):
        self.log_start = False

    def doLogrotate(self, name, line, p1, p2):
        """必要ならオーバーライドしてください"""
        self.commandContext(name, line, (p1, p2))

    def doLogstart(self):
        self.log_start = True

    def doLogwrite(self, strvar: str):
        """無条件で書き込む"""
        if self.log_file_handle is None:
            # ログが開かれていない
            return
        #
        if self.log_timestamp_type == -1:
            # タイムスタンプは不要
            if isinstance(strvar, str):
                strvar = strvar.encode("utf-8")
            self.log_file_handle.write(strvar)
        else:
            # タイムスタンプを付ける必要がある
            while True:
                if strvar == "":
                    break
                index = strvar.find("\n")
                if index < 0:
                    if isinstance(strvar, str):
                        strvar = strvar.encode("utf-8")
                    self.log_file_handle.write(strvar)
                    break
                target = strvar[: index + 1]
                if isinstance(target, str):
                    target = target.encode("utf-8")
                self.log_file_handle.write(target)
                self.log_file_handle.write(self.getTimestamp().encode("utf-8"))
                strvar = strvar[index + 1:]

    def getTimestamp(self) -> str:
        """タイムスタンプを入れる"""
        if self.log_timestamp_type == 0:
            # ローカルタイム
            return "[" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "]"
        elif self.log_timestamp_type == 1:
            # UTC
            return "[" + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + "]"
        elif self.log_timestamp_type == 2:
            # 経過時間 (Logging)
            return self.getTimestampElapsed(self.log_login_time)
        else:
            # 経過時間 (Connection)
            return self.getTimestampElapsed(self.log_connect_time)

    def getTimestampElapsed(self, start) -> str:
        """経過時間を文字に変換する"""
        total_seconds = 0
        if start is not None:
            total_seconds = int(start - time.time())
        day = total_seconds // (60 * 60 * 24)
        hours = (total_seconds // (60 * 60)) % 24
        minutes = (total_seconds // 60) % 3600
        seconds = total_seconds % 60
        return f"[{day} {hours:02}:{minutes:02}:{seconds:02}]"

    def setLogInner(self, strvar: str):
        """ログファイル書き込みが必要ならこちらを使います"""
        #
        # ログ出力/オーバーライドする方に渡す
        self.setLog(strvar)
        #
        # ログ出力処理
        if self.log_start:
            self.doLogwrite(strvar)

    @abstractmethod
    def setLog(self, strvar: str):
        """ Please Override! """
        pass

    def doChecksum8(self, p1: str, p2: str):
        p2_byte = p2.encode("utf-8")
        self.getChecksum(p1, p2_byte, 0x0F)

    def doChecksum8file(self, p1: str, p2: str):
        self.setValue(p1, 0)  # default value
        try:
            with open(p2, "rb") as f:
                p2_byte = f.read()
                self.getChecksum(p1, p2_byte, 0x0F)
                self.setValue("result", 0)
        except Exception:
            self.setValue("result", -1)

    def doChecksum16(self, p1: str, p2: str):
        p2_byte = p2.encode("utf-8")
        self.getChecksum(p1, p2_byte, 0xFF)

    def doChecksum16file(self, p1: str, p2: str):
        self.setValue(p1, 0)  # default value
        try:
            with open(p2, "rb") as f:
                p2_byte = f.read()
                self.getChecksum(p1, p2_byte, 0xFF)
                self.setValue("result", 0)
        except Exception:
            self.setValue("result", -1)

    def doChecksum32(self, p1: str, p2: str):
        p2_byte = p2.encode("utf-8")
        self.getChecksum(p1, p2_byte, 0xFFFF)

    def doChecksum32file(self, p1: str, p2: str):
        self.setValue(p1, 0)  # default value
        try:
            with open(p2, "rb") as f:
                p2_byte = f.read()
                self.getChecksum(p1, p2_byte, 0xFFFF)
                self.setValue("result", 0)
        except Exception:
            self.setValue("result", -1)

    def getChecksum(self, p1: str, p2_byte, mask: int):
        sum = 0
        for b in p2_byte:
            # print(f"b={int(b):#02x}")
            sum = (sum + int(b)) & mask
        self.setValue(p1, sum)

    def doCrc16(self, p1: str, p2: str):
        p2_byte = p2.encode("utf-8")
        self.crc16_IBM_SDLC(p1, p2_byte)

    def doCrc16file(self, p1: str, p2: str):
        self.setValue(p1, 0)  # default value
        try:
            with open(p2, "rb") as f:
                p2_byte = f.read()
                self.crc16_IBM_SDLC(p1, p2_byte)
                self.setValue("result", 0)
        except Exception:
            self.setValue("result", -1)

    def crc16_IBM_SDLC(self, p1: str, data: bytes):
        r = 0xFFFF
        for byte in data:
            r = r ^ byte
            for ignore in range(8):
                if r & 0x1 == 1:
                    r = (r >> 1) ^ 0x8408
                else:
                    r = r >> 1
        r = r ^ 0xFFFF
        self.setValue(p1, r)

    def doCrc32(self, p1: str, p2: str):
        p2_byte = p2.encode("utf-8")
        self.crc32_IBM_SDLC(p1, p2_byte)

    def doCrc32file(self, p1: str, p2: str):
        self.setValue(p1, 0)  # default value
        try:
            with open(p2, "rb") as f:
                p2_byte = f.read()
                self.crc32_IBM_SDLC(p1, p2_byte)
                self.setValue("result", 0)
        except Exception:
            self.setValue("result", -1)

    def crc32_IBM_SDLC(self, p1: str, data: bytes):
        r = 0xFFFFFFFF
        for byte in data:
            r = r ^ byte
            for ignore in range(8):
                if r & 0x1 == 1:
                    r = (r >> 1) ^ 0xEDB88320
                else:
                    r = r >> 1
        r = r ^ 0xFFFFFFFF
        self.setValue(p1, r)

    def doExec(self, line, data_line):
        # print(f"### l={line} doExec() ")
        data_len = len(data_line)
        command = self.getData(data_line[0])
        command_list = re.split(r"[ \t]+", command)
        show = 1  # SW_SHOWNORMAL
        if 2 <= (data_len):
            show = self.getData(data_line[1]).lower()
            if "show" == show:
                pass
            elif "minimize" == show:
                show = 6  # SW_MINIMIZE
            elif "maximize" == show:
                show = 3  # SW_MAXIMIZE
            elif "hide" == show:
                show = 0  # SW_HIDE
            else:
                raise TypeError(f"### l={line} doExec type error")
        wait = 0
        if 3 <= (data_len):
            wait = self.getDataInt(data_line[2])
        base_directory = "."
        if 4 <= (data_len):
            base_directory = self.getData(data_line[3])
            if not os.path.isdir(base_directory):
                base_directory = "."
        # print(f"\tcommand_list={command_list}")
        # print(f"\tshow={show}")
        # print(f"\twait={wait}")
        # print(f"\tbase_directory={base_directory}")
        #
        si = None
        if platform.system().lower() != "linux":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0  # SW_HIDE
        p = subprocess.Popen(
            command_list, startupinfo=si, cwd=base_directory, shell=True
        )
        if wait != 0:
            p.wait()  # プロセスが終了するまで待機
            self.setValue("result", p.returncode)

    def doGetdate(self, data_line, format="%Y-%m-%d"):
        date = self.getKeywordName(data_line[0])
        data_len = len(data_line)
        if 2 <= data_len:
            format = self.getData(data_line[1])
        #
        local_timezone = None
        # print(f"timezone={local_timezone}")
        if 3 <= data_len:
            local_timezone = self.getData(data_line[2])
        date_str = ""
        if local_timezone is None:
            local_now = datetime.now()
        else:
            local_now = datetime.now(ZoneInfo(local_timezone))
        date_str = local_now.strftime(format)
        self.setValue(date, date_str)

    def doExpandenv(self, p1, p2):
        if platform.system().lower() != "linux":
            p2 = os.path.expandvars(p2)
        else:
            pattern = r"%(.*?)%"
            p2 = re.sub(pattern, lambda match: f"%{match.group(1).lower()}%", p2)
            p2 = p2.replace("%windir%", "c:\\windows")
            p2 = p2.replace("%systemroot%", "/root")
            p2 = p2.replace("%programfiles%", "/usr/local")
            p2 = p2.replace("%programfiles(x86)%", "/usr/local")
            p2 = p2.replace("%userprofile%", os.environ.get("HOME"))
            p2 = p2.replace("%appdata%", "/usr/local")
            p2 = p2.replace("%localappdata%", "/usr/local")
            p2 = p2.replace("%temp%", "/tmp")
            p2 = p2.replace("%tmp%", "/tmp")
            p2 = p2.replace("%computerprogramfiles%", "/usr/local")
            p2 = p2.replace("%public%", os.environ.get("HOME"))
            p2 = p2.replace("%computername%", socket.gethostname())
            p2 = p2.replace("%username%", getpass.getuser())
            p2 = p2.replace("%path%", os.environ.get("PATH"))
        #
        self.setValue(p1, p2)

    def doSprintf(self, inputstr, data_line):
        format = self.getData(data_line[0])
        data_new = []
        for data in data_line[1:]:
            data_new.append(self.getData(data))
        # print(f"format={format}")
        # print(f"data_new={tuple(data_new)}")
        strvar = format % tuple(data_new)
        # print(f"strvar={strvar}")
        self.setValue(inputstr, strvar)
        self.setValue("result", 0)

    def doPause(self, p1):
        """指定された秒数待つ"""
        # print(f"pause {p1}")
        if self.end_flag:
            return

        # 1秒未満の待ち
        mtime = p1 - int(p1)
        if 0 < mtime:
            time.sleep(mtime)

        # 1秒以上の待ちは1秒づつ end_flagが立っていないか見る
        for ignore in range(int(p1)):
            if self.end_flag:
                break
            time.sleep(1)

    def doStrtrim(self, p1_var: str, p2: str) -> str:
        # エスケープを変換する
        p2 = p2.encode().decode("unicode_escape")

        # 前方方向
        while 0 < len(p1_var):
            ch = p1_var[0]
            if ch not in p2:
                break
            p1_var = p1_var[1:]

        # 後方方向
        while 0 < len(p1_var):
            ch = p1_var[-1]
            if ch not in p2:
                break
            p1_var = p1_var[:-1]
        return p1_var

    def doSetpassword(
        self, filename: str, password_name: str, password: str, encrypt_str: str
    ):
        worker = {}
        filename = self.normpath(filename)
        worker = self.get_encrypt_file(filename)
        encrypt_byte = encrypt_str.encode("utf-8")
        encrypt_byte = encrypt_byte.ljust(32, b"\0")  # 32byte以下なら増やす
        encrypt_byte = encrypt_byte[:32]  # 32byte以上を無視する
        encrypt_byte = base64.urlsafe_b64encode(encrypt_byte)
        cipher = Fernet(encrypt_byte)
        #
        target_0 = password.encode("utf-8")  # 文字をセット
        target_1 = f"{password}_{encrypt_str}".encode("utf-8")
        # print(f"d {password_name} {password} 0={target_0}")
        target_0 = cipher.encrypt(target_0)  # byte列に変更して暗号化
        target_1 = cipher.encrypt(target_1)
        target_0 = base64.b64encode(target_0).decode()  # base64に変更して文字にする
        target_1 = base64.b64encode(target_1).decode()
        worker[password_name] = [target_0, target_1]
        # print(f"c {password_name} {password}  0={target_0}")
        result = self.set_encrypt_file(filename, worker)
        # print(f"doSetpassword2 str={filename} p={password_name} p={password} w={worker}")
        self.setValue("result", result)
        # print(f"doSetpassword3 str={filename} p={password_name} p={password} w={worker}")

    def doGetpassword(
        self, filename: str, password_name: str, p3: str, encrypt_str: str
    ):
        # print(f"doGetpassword p3={p3}")
        filename = self.normpath(filename)
        worker = self.get_encrypt_file(filename)
        # print(f"doGetpassword worker={worker}")
        if password_name in worker and 2 <= len(worker[password_name]):
            encrypt_byte = encrypt_str.encode("utf-8")
            encrypt_byte = encrypt_byte.ljust(32, b"\0")  # 32byte以下なら増やす
            encrypt_byte = encrypt_byte[:32]  # 32byte以上を無視する
            encrypt_byte = base64.urlsafe_b64encode(encrypt_byte)
            cipher = Fernet(encrypt_byte)
            #
            # print(f"d {password_name} 0={worker[password_name][0]}")
            target_0 = base64.b64decode(worker[password_name][0].encode())
            target_1 = base64.b64decode(worker[password_name][1].encode())
            try:
                target_0 = cipher.decrypt(target_0).decode("utf-8")
                target_1 = cipher.decrypt(target_1).decode("utf-8")
            except InvalidToken:
                self.setValue("result", 0)
                return
            # print(f"e {password_name} 0={target_0}")
            # print(f"e {password_name} 0={target_1}")
            #
            if f"{target_0}_{encrypt_str}" == target_1:
                self.setValue(p3, target_0)
                self.setValue("result", 1)
            else:
                # encriptが一致しなかった
                self.setValue("result", 0)
        else:
            self.setValue("result", 0)

    def doIspassword(self, filename: str, password_name: str):
        # print(f"doGetpassword p3={p3}")
        filename = self.normpath(filename)
        worker = self.get_encrypt_file(filename)
        # print(f"doGetpassword worker={worker}")
        if password_name in worker:
            self.setValue("result", 1)
        else:
            self.setValue("result", 0)

    def doDelpassword(self, filename: str, password_name: str):
        # print(f"doGetpassword p3={p3}")
        filename = self.normpath(filename)
        worker = self.get_encrypt_file(filename)
        # print(f"doGetpassword worker={worker}")
        if password_name in worker:
            del worker[password_name]
        self.set_encrypt_file(filename, worker)

    def set_encrypt_file(self, filename, worker: dict) -> int:
        """暗号化のファイル書き込み後、学習しておく"""
        # エンコードしたい元の文字列
        original_text = json.dumps(worker)
        filename = self.normpath(filename)
        filename = str(pathlib.Path(filename).resolve())
        self.encrypt_file[filename] = worker
        #
        # ファイルへの書き込み
        try:
            with open(filename, "wt") as f:
                f.write(original_text)
        except (FileNotFoundError, IOError):
            return 0
        return 1

    def get_encrypt_file(self, filename):
        """暗号化のファイル読み込みを１回で終わらせる"""
        #
        # すでに読み込んでいるなら、それを使う
        filename = self.normpath(filename)
        filename = str(pathlib.Path(filename).resolve())
        if filename in self.encrypt_file:
            return self.encrypt_file[filename]
        #
        # データがないのでファイルからロードする
        worker = {}
        try:
            with open(filename, "rt") as f:
                worker = json.loads(f.read())
                self.encrypt_file[filename] = worker
        except (FileNotFoundError, IOError, json.decoder.JSONDecodeError):
            worker = {}
        return worker

    def doFileopen(
        self, file_handle, filename: str, append_flag: int, readonly_flag: int
    ):
        """ファイルハンドルを作る"""
        if file_handle in self.file_handle_list:
            self.doFileClose(file_handle)
        filename = self.normpath(filename)
        self.file_handle_list[file_handle] = {}
        self.file_handle_list[file_handle]["file_handle"] = None
        self.file_handle_list[file_handle]["filename"] = filename
        self.file_handle_list[file_handle]["append_flag"] = append_flag
        self.file_handle_list[file_handle]["readonly_flag"] = readonly_flag
        self.getValue("result", 0)

    def doFindfirst(self, line, file_handle, file_name: str, strvar: str):
        """ファイルハンドルを作る"""
        if file_handle in self.file_handle_list:
            self.doFileClose(file_handle)
        self.file_handle_list[file_handle] = {}
        self.file_handle_list[file_handle]["file_handle"] = MyFindfirst(file_name)
        self.file_handle_list[file_handle]["filename"] = file_name
        self.file_handle_list[file_handle]["append_flag"] = False
        self.file_handle_list[file_handle]["readonly_flag"] = True
        self.doFindnext(line, file_handle, strvar)

    def doFindnext(self, line, file_handle, strvar: str):
        """次のファイルを取得する"""
        self.doFilereadln(line, file_handle, strvar)
        if self.getValue("result") == 0:
            self.setValue("result", 1)
        else:
            self.setValue("result", 0)

    def doFileclose(self, file_handle):
        """ファイルハンドルがいたら消す"""
        if file_handle not in self.file_handle_list:
            return
        file_handle_base = self.file_handle_list[file_handle]
        #
        self.file_handle_list[file_handle] = None
        del self.file_handle_list[file_handle]
        #
        file_handle_file = file_handle_base["file_handle"]
        if file_handle_file is None:
            return
        try:
            self.file_handle.close()
        except Exception:
            pass

    def doFilewrite(self, line, file_handle, data):
        if file_handle not in self.file_handle_list:
            raise TypeError(f"### l={line} file_handle not found f={file_handle}")
        file_handle_base = self.file_handle_list[file_handle]
        file_handle_file = file_handle_base["file_handle"]
        if file_handle_file is None:
            option = 'wb'
            if file_handle_base["append_flag"] != 0:
                option = 'ab'
            file_handle_file = open(file_handle_base["filename"], option)
            file_handle_base["file_handle"] = file_handle_file
        file_handle_file.write(data.encode("utf-8"))

    def openHandle(self, line, file_handle):
        if file_handle not in self.file_handle_list:
            raise TypeError(f"### l={line} file_handle not found f={file_handle}")
        file_handle_base = self.file_handle_list[file_handle]
        file_handle_file = file_handle_base["file_handle"]
        if file_handle_file is None:
            file_handle_file = open(file_handle_base["filename"], "rb")
            file_handle_base["file_handle"] = file_handle_file
        return file_handle_file

    def doFileread(self, line, file_handle, read_byte, strvar):
        file_handle_file = self.openHandle(line, file_handle)
        #
        text = file_handle_file.read(read_byte)
        if text is not None:
            self.setValue(strvar, text.decode())
            self.setValue("result", 1)
        else:
            self.setValue(strvar, "")
            self.setValue("result", 0)

    def doFilereadln(self, line, file_handle, strvar):
        file_handle_file = self.openHandle(line, file_handle)
        #
        try:
            text = file_handle_file.readline()
            self.setValue(strvar, text.decode())
            self.setValue("result", 0)
        except OSError:
            self.setValue(strvar, "")
            self.setValue("result", 1)

    def doFileconcat(self, p1, p2):
        p1 = self.normpath(p1)
        p2 = self.normpath(p2)
        if p1 == p2:
            self.setValue("result", 0)
            return
        try:
            with open(p1, "ab") as f1:
                with open(p2, "rb") as f2:
                    f1.write(f2.read())
            self.setValue("result", 1)
        except OSError:
            self.setValue("result", 0)

    def doFilecopy(self, p1, p2):
        p1 = self.normpath(p1)
        p2 = self.normpath(p2)
        if p1 == p2:
            self.setValue("result", 0)
            return
        try:
            with open(p1, "rb") as f1:
                with open(p2, "wb") as f2:
                    f2.write(f1.read())
            self.setValue("result", 1)
        except OSError:
            self.setValue("result", 0)

    def doFiledelete(self, filename):
        filename = self.normpath(filename)
        if not os.path.exists(filename):
            self.setValue("result", 0)
            return
        try:
            os.remove(filename)
            self.setValue("result", 1)
        except OSError:
            self.setValue("result", 0)

    def doFilerename(self, p1, p2):
        p1 = self.normpath(p1)
        p2 = self.normpath(p2)
        # print(f"doFilerename0 {p1} {p2}")
        if p1 == p2:
            # print(f"doFilerename1 {p1} {p2}")
            self.setValue("result", 1)
            return
        if not os.path.exists(p1):
            # print(f"doFilerename2 {p1} {p2}")
            self.setValue("result", 1)
            return
        self.doFiledelete(p2)
        try:
            os.rename(p1, p2)
            self.setValue("result", 0)
        except OSError:
            self.setValue("result", 1)

    def doStrreplace(self, strvar, strvar_val, index, regex, newstr):
        strvar_pre = strvar_val[0:index]
        strvar_val = strvar_val[index:]
        strvar_val = strvar_pre + re.sub(regex, newstr, strvar_val)
        try:
            self.setValue(strvar, strvar_val)
            self.setValue("result", 1)
        except (re.error, TypeError, ValueError):
            self.setValue("result", 0)

    def doStrmatch(self, target_string, string_with_regular_expressio):
        # print(f"strmatch {target_string} {string_with_regular_expressio}")
        match = re.search(string_with_regular_expressio, target_string)
        if match:
            # print(f"hit strmatch {target_string} {string_with_regular_expressio}")
            self.setValue("result", match.start() + 1)
            i = 0
            for grp in match.groups():
                self.setValue("groupmatchstr" + str(i + 1), grp)
                i = i + 1
                if 10 <= i:
                    break
        else:
            self.setValue("result", 0)

    def doFilesearch(self, filename):
        filename = self.normpath(filename)
        if os.path.exists(filename):
            self.setValue("result", 1)
        else:
            self.setValue("result", 0)

    def doFilestat(self, filename, size, mtime, drive):
        try:
            filename = self.normpath(filename)
            size_val = os.path.getsize(filename)
            self.setValue(size, size_val)
            if mtime is not None:
                timestamp = os.path.getmtime(filename)
                dt = datetime.fromtimestamp(timestamp)
                self.setValue(mtime, dt)
            if drive is not None:
                drive_val, xx = os.path.splitdrive(filename)
                self.setValue(drive, drive_val)
            self.setValue("result", 0)
        except FileNotFoundError:
            self.setValue(size, 0)
            if mtime is not None:
                self.setValue(mtime, "")
            if drive is not None:
                self.setValue(drive, "")
            self.setValue("result", -1)

    def doFiletruncate(self, filename: str, size: int):
        size_val = 0
        try:
            filename = self.normpath(filename)
            size_val = os.path.getsize(filename)
        except FileNotFoundError:
            self.setValue(size, 0)
            size_val = 0
        if size_val == size:
            return
        try:
            if size < size_val:
                # 切り詰めが必要
                with open(filename, "r+b") as f:
                    fd = f.fileno()
                    os.truncate(fd, size)
            else:
                # ゼロバイト加算
                with open(filename, "ab") as f:
                    f.write(bytes(size - size_val))
        except OSError:
            self.setValue("result", -1)

    def doFoldercreate(self, folder_name):
        try:
            folder_name = self.normpath(folder_name)
            os.mkdir(folder_name)
            self.setValue("result", 1)
        except FileNotFoundError:
            self.setValue("result", 0)

    def doFolderdelete(self, folder_path):
        folder_path = self.normpath(folder_path)
        if not os.path.isdir(folder_path):
            self.setValue("result", 0)
            return
        try:
            os.rmdir(folder_path)
            self.setValue("result", 1)
        except OSError:
            self.setValue("result", 0)

    def doFoldersearch(self, folder_path):
        folder_path = self.normpath(folder_path)
        if os.path.isdir(folder_path):
            self.setValue("result", 1)
        else:
            self.setValue("result", 0)

    def doMakepath(self, strvar, dir, name):
        dir = self.normpath(dir)
        result = os.path.abspath(dir)
        result = os.path.join(result, name)
        self.setValue(strvar, result)

    def doGetipv4addr(self, string_array, intvar):
        ip = socket.gethostbyname(socket.gethostname())
        if ip is None:
            self.setValue(intvar, 0)
            return
        self.setValue(string_array + "[0]", ip)
        self.setValue(intvar, 1)

    def doGetipv6addr(self, string_array, intvar):
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6)
        i = 0
        if infos is None:
            self.setValue(intvar, 0)
            self.setValue("result", 0)
            return
        for info in infos:
            ipv6 = info[4][0]
            # print("IPv6アドレス:", ipv6)
            self.setValue(f"{string_array}[{str(i)}]", ipv6)
            i = i + 1
        self.setValue(intvar, i)
        if 0 < i:
            self.setValue("result", 1)
        else:
            self.setValue("result", 0)

    def doGetver(self, strvar: str, target_version: float):
        """バージョン情報 オーバーライドして使ってください"""
        # print("doGetver")
        now_version = float(VERSION)
        self.setValue(strvar, str(now_version))
        if target_version is not None:
            if now_version == target_version:
                self.setValue("result", 0)
            elif now_version < target_version:
                self.setValue("result", -1)
            else:
                self.setValue("result", 1)
        # print("doGetver end")

    def setTitle(self, title: str):
        """タイトルの設定 オーバーライドして使ってください"""
        self.title = title

    def getTitle(self) -> str:
        """タイトルの取得 オーバーライドして使ってください"""
        return self.title

    def doIfdefined(self, strvar: str):
        result = 0
        if strvar in self.value_list:
            # print(f"doIfdefined /{strvar}/")
            result = self.getValue(strvar)
            if isinstance(result, Label):
                result = 4
            elif isinstance(result, int):
                result = 1
            else:
                result = 3
        else:
            for value in self.value_list:
                # print(f"hit2 {value}/{strvar}")
                if strvar + "[" in value:
                    if isinstance(self.getValue(value), int):
                        result = 5
                    else:
                        result = 6
                    break
            self.setValue("result", 0)
        # print(f"doIfdefined v={strvar} d={result}")
        self.setValue("result", result)

    def doScprecv(self, p1, p2):
        """SCP 受信"""
        if self.client is None:
            return
        sftp_connection = self.client.open_sftp()
        sftp_connection.get(p1, p2)
        sftp_connection.close()

    def doScpsend(self, p1, p2):
        """SCP 転送"""
        if self.client is None:
            return
        sftp_connection = self.client.open_sftp()
        sftp_connection.put(p1, p2)
        sftp_connection.close()

    def doSetexitcode(self, p1):
        self.exitcode = int(p1)


#
