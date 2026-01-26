# Samidare DAQ webui (demo)

Samdare CLIコマンドのWeb制御用UI

## Quick start 

```zsh
uv run webui
```

## ディレクトリ構造

```
.
├── pyproject.toml
├── README.md
├── src
│   ├── certs
│   │   ├── cert.pem
│   │   └── key.pem
│   ├── data
│   │   ├── clock_type.dat
│   │   ├── comment.dat
│   │   ├── current_output_path.dat
│   │   ├── file_name.dat
│   │   ├── gain.dat
│   │   ├── num_sample.dat
│   │   ├── output_dir.dat
│   │   ├── polarity.dat
│   │   ├── pre_sample.dat
│   │   ├── run_name.dat
│   │   ├── run_number.dat
│   │   ├── samdaq.pgid
│   │   ├── trig_type.dat
│   │   └── trig_value.dat
│   ├── samidaq_webui
│   │   ├── templates
│   │   │   └── index.html
│   │   └── webctl.py
│   └── scripts
│       ├── run.sh
│       ├── send.sh
│       ├── status.txt
│       ├── stop.sh
│       └── wait.sh
└── uv.lock
```