#!/bin/bash
if [ $# -ne 4 ]; then
  echo "実行するには3個の引数(バージョン ディーラー名 プレイヤー名)が必要です。" 1>&2
  echo "例) bash player.sh v0 Dealer Player1" 1>&2
  exit 1
fi
cd development-kit/player_$1
docker build -t player_$1 ./
docker run player_$1 http://localhost:8080 "$2" "$3"
