# Samidare DAQ WebUI

SAM_DAQ を Web API から制御するための FastAPI ベースの WebUI / backend です。

基本構造はSPADIの[FEE Control Software](https://github.com/spadi-alliance/FEE-Control-Software)を元にしています。

このリポジトリは、SAMDAQ の CLI を直接操作する代わりに、HTTP API 経由で DAQ の状態取得、接続、電源制御、トリガー設定、DAQ 開始・停止などを実行するためのラッパーを提供します。

内部的には、起動済みの SAMDAQ CLI に対して `tmux send-keys` でコマンドを送り、実行結果をログから取得します。

- DAQ の基本操作
  - status
  - connect / disconnect
  - power on / off
  - trigger type / threshold 設定
  - polarity / gain / samples / pretrigger 設定
  - external clock 設定
  - start / stop
  - output directory / filename 設定
- TOML 設定ファイルによる backend / script / API path の切り替え

## ディレクトリ構造

```text
.
├── config
│   ├── asagi.toml
│   └── samidare.toml
├── pyproject.toml
├── README.md
├── src
│   └── samidaq_webui
│       ├── agasa
│       ├── legacy
│       ├── samidare
│       │   ├── Backend
│       │   │   ├── config
│       │   │   ├── helpers
│       │   │   └── main.py
│       │   ├── Frontend
│       │   └── Scripts
│       │       └── send_samdaq_tmux.sh
│       └── test
└── uv.lock
````

## インストール方法

```bash
git clone https://github.com/FumiHubCNS/samidaq_webui.git
cd samidaq_webui
uv sync
```

ただし以下が必要です。

* Python `>=3.14`
* uv
* tmux
* SAMDAQ executable
* SAMDAQ が動作する環境


## 始め方

テストページの起動コマンドは`src/samidaq_webui/samidare/dev_server.py`にあり、以下のコマンドで実行可能です。

```zsh
uv run webui-dev
```

あとは`http://127.0.0.1:8080`でUIを確認できます。

また、`SAM_DAQ`も同時に起動したい場合は以下のコマンドで起動できます。

```zsh
uv run webui-dev -s
```

## 詳細設定

SAMIDARE 用の設定は以下です。

```text
config/samidare.toml
```

主な設定項目:

```toml
[defaults]
save_dir = "log/samidare_configs"
config = "src/samidaq_webui/samidare/Backend/config/general/default.json"

[device]
script = "src/samidaq_webui/samidare/Scripts/send_samdaq_tmux.sh"
session = "samdaq:0.0"
log_file = "log/samdaq_tmux.log"
wait_timeout = 2
poll_sec = 0.05

[functions]
get_status = "samidaq_webui.samidare.Backend.helpers.backEndHelpers:get_status"
set_gain = "samidaq_webui.samidare.Backend.helpers.backEndHelpers:set_gain"
start_daq = "samidaq_webui.samidare.Backend.helpers.backEndHelpers:start_daq"
stop_daq = "samidaq_webui.samidare.Backend.helpers.backEndHelpers:stop_daq"

[api]
prefix = "/api/samidare"
run_route = "/run"
```

### device.session

SAMDAQ が起動している tmux pane を指定します。

例:

```toml
session = "samdaq:0.0"
```

これは tmux session `samdaq` の window 0 / pane 0 を意味します。

### device.script

SAMDAQ CLI にコマンドを送るスクリプトです。

```toml
script = "src/samidaq_webui/samidare/Scripts/send_samdaq_tmux.sh"
```

このスクリプトは `tmux send-keys` で SAMDAQ CLI にコマンドを送り、`tmux pipe-pane` で出力ログを取得します。


### SAMIDARE バックエンド関数の使い方

SAMIDARE WebUI のバックエンドでは、`config/samidare.toml` の `[functions]` セクションで、API から呼び出せる関数を指定しています。

つまり実行したい関数をバックエンドに書いたのちにこの`toml`に関数のパスと名前を渡せば使えるようになります。

### SAM_DAQの起動

`src/samidaq_webui/samidare/Scripts/start_samdaq.sh`にSAM_DAQのパスとtmuxでの起動方法が書かれています。

正しくSAM_DAQをインストールできていれば実行可能なはずです。