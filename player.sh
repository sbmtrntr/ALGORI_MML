#!/bin/bash
if [ $# -ne 4 ]; then
  echo "実行するには4個の引数(バージョン, ディーラーのIPアドレス, ディーラー名, プレイヤー名)が必要です。" 1>&2
  echo "例) bash player.sh v0 xx.xx.xx.xx Dealer Player1" 1>&2
  exit 1
fi
cd development-kit/player_$1
docker build -t $1 ./
docker run player_$1 http://$2:8080 "$3" "$4"
