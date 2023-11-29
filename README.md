# ALGORI_MML


<details><summary>
GitHubの使い方
</summary><div>

1. ローカルでmainブランチに移動
```bash
$ git checkout main
```

2. 最新のリモートリポジトリをpullする
```bash
git pull origin main
```

3. ローカルのmainブランチから、新しくブランチを作成する
```bash
git switch -c <ブランチ名>
```

4. 新しいブランチでファイルを更新した後、addしてcommitする
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


5. リモートにpushする
```bash
git push origin <ブランチ名>
```

6. Githubでpull requestを作成する

</div></details>