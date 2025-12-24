# NextNextPing

- This software is a tool similar to ExPing for pinging multiple devices in Windows.
- You can connect via SSH using a language called TTL(Terawaros Tekitou Language), which is similar to teraterm macro, and ping other servers as stepping stones.


# How to run

## For Linux or Python 
### (1) install

```
$ pip3 install nextnextping
```

### (2) Invoke pyttl

- You can connect via SSH using a language called TTL(Terawaros Tekitou Language), which is similar to teraterm macro, and ping other servers as stepping stones.

```shell
$ pyttl TTL_FILENAME

Example:
$ pyttl ./test/0000_ok_test.ttl
```

### (3) Invoke nextnextping

```shell
$ nextnextping
```

- This software is a tool similar to ExPing for pinging multiple devices in Windows.

<img src="./docs/screen011.png" width="40%">


## For Windows

### (1) Download

- [nextnextping/releases](https://github.com/Tand0/nextnextping/releases)

### (2) Screen image

- [Screen image](./docs/screen.md)

## For Linux and ansible

- [For Ansible](https://galaxy.ansible.com/ui/repo/published/tand0/ttl/)

## Downlad Sourcecode

- [For Github](https://github.com/Tand0/nextnextping)

# For TTL macro

- [The MACRO Language Terawaros Tekitou Language (TTL)](./docs/syntax.md)　
- [TTL command reference](./docs/command.md)


# 基本的な使い方

  - Basic -- sample01/setting.txt に例があります。
      - nextnextpingを起動します。
      - [トップ画面](./docs/screen.md#トップ画面)で適当にipを並べます。
      - メニューバーから、File ⇒ Setting で [設定画面](./docs/screen.md#設定画面) を開いて設定を変更します。
      - Updateボタンをクリックします。
      - Pingボタンをクリックします。
      - しばらくするとpingに成功したものがOK、失敗したものがNGで表示されます。
      - メニューバーから、File ⇒ Save setting で設定の保存ができます。
      - メニューバーから、File ⇒ Save log でログの保存ができます。
      - メニューバーから、File ⇒ Exit で終了できます。
  - Advanced -- sample02/setting.txt に例があります。
      - nextnextpingを起動します。
      - メニューバーから、Tool ⇒ Sheet をクリックします。
      - 設定用CSVファイルを作成します。やり方は２種類あります。
          -  メニューバーから、File ⇒ Load csv で保存した csvをロードします。
          -  Createボタンを押して [設定画新規作成または編集画面面](./docs/tool.md#新規作成または編集画面) を開いて編集します。
          - 行をダブルクリックすると編集ができます。
      - 今後のために File ⇒ Save csv で保存した csvをセーブします。
      - メニューバーから、Go ⇒ Create ttl で ttlを自動生成します。
      - メニューバーから、File ⇒ Closeでツールを終了します。
      - [結果表示画面](./docs/screen.md#結果表示画面) からPingボタンをクリックします。
      - しばらくするとpingに成功したものがOK、失敗したものがNGで表示されます。
      - メニューバーから、File ⇒ Save log でログの保存ができます。
      - メニューバーから、File ⇒ Exit で終了できます。
  - Legend -- sample03/setting.txt に例があります。
      - nextnextpingを起動します。
      - メニューバーから、File ⇒ Setting で [設定画面](./docs/screen.md#設定画面) を開いて設定を変更します。
      - ttlを自作します。
      - [トップ画面](./docs/screen.md#トップ画面)で`[`説明文`]` `(`ttl`)`  `ttlマクロのファイル名` と記述します。
      - Updateボタンをクリックします。
      - Pingボタンをクリックします。
      - しばらくするとpingに成功したものがOK、失敗したものがNGで表示されます。
           - 失敗の条件はエラーが発生したか、または、 `result` が 0 である場合のいずれかです。
      - メニューバーから、File ⇒ Save setting で設定の保存ができます。
      - メニューバーから、File ⇒ Save log でログの保存ができます。
      - メニューバーから、File ⇒ Exit で終了できます。


# 開発者に向けた README

- 動作確認方法
- 以下、カレントフォルダを `.` とする
  - 必要なパッケージが入ってなかったら入れる ※最初のみ
  - 別のPCにインストールしたときはフォルダ名等は見直す ※最初のみ
  - `.pypirc` を持ってきて `.` に置く。※ Python packageを改版する場合
  - `python mybuild.py` の中にある `VERSION=` 情報を変更する。最後が0になるの数値は使わないこと
  - `python mybuild.py` を実行する。※ pyinstaller が動きます
  - `pytest -s` を実行する
      - すべての test にパスすることを確認する
      - 内部で Mock の ssh や scp サーバを起動します
      - Layer4 port 2200 を占有します
  - `wsl` を起動する
      - `wsl` の中で `pytest -s` を実行する
      - すべての test にパスすることを確認する
      - `wsl` の中で `python3 test/test_nextnextping.py` を起動しっぱなにする
          - `wsl` の中で実行しないと後続の `site.yml` が正常動作しません
          - Mock の ssh や scp サーバを起動します
          - Layer4 port 2200 を占有します
  - もう一枚コマンドプロンプトを起動して `wsl` を起動する
      - `cd ../bin` に移動する
      - `nextnextping` を実行して動作に問題ないことを確認する
          - wsl の tkinterで文字化けするのは font が入ってないせい
          - `sudo apt install fonts-noto-cjk` で font を入れること
      - `cd ./forwsl2` に移動する
      - `wsl` の中で `ansible-playbook site.yml` を実行する
      - すべての test にパスすることを確認する
      - `wsl` の中で `ansible-playbook site_pypi.yml` を実行して PyPi にアップロードする 
      - `./dest` 配下に公開に必要なファイル群ができあがる
      - 2つのコマンドプロンプトを `wsl` を `exit` で抜ける
  - ansible-galaxy に登録する
    - [ansible-galaxy](https://galaxy.ansible.com/ui/repo/published/tand0/ttl/)
  - githubに登録する
    - `git add .`
    - `git commit . -m "DOCUMENT"`
    - `git push`
  - エラーが出た時は、指示に従って見直す
    - pyinstall, tkinter, pytest など必要なパッケージが入ってないとエラーになります
    - フォルダ名は環境に合わせて修正が必要です
