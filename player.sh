#!/bin/bash
if [ $# -ne 4 ]; then
  echo "指定された引数は$#個です。" 1>&2
  echo "実行するには4個の引数(image名, ディーラーのIPアドレス, ディーラー名, プレイヤー名)が必要です。" 1>&2
  exit 1
fi
cd development-kit/demo-player_python
docker build -t $1 ./
docker run $1 http://$2:8080 "$3" "$4"
