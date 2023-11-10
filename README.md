手順[(参考)](https://qiita.com/yukiya1006/items/4a491df3595662d8f781)

0. ローカルでmainブランチに移動
```bash
$ git checkout main
```

1. 最新のリモートリポジトリをpullする
```bash
git pull origin main
```

2. ローカルのmainブランチから、新しくブランチを作成する
```bash
git switch -c <ブランチ名>
```

3. 新しいブランチでファイルを更新した後、addしてcommitする
```bash
git add .
git commit -m "<メッセージ>"
```
コミットメッセージのフォーマットは、"[コミット種別] 要約"とする。  
コミット種別は以下の四種類を使う
- fix (変更)
- add (追加)
- update (更新)
- remove (削除)


4. リモートにpushする
```bash
git push origin <ブランチ名>
```

5. Githubでpull requestを作成する
