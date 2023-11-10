import * as chai from 'chai';
import * as webdriver from 'selenium-webdriver';
import * as chrome from 'selenium-webdriver/chrome';
import * as BlueBird from 'bluebird';
import * as path from 'path';
import * as fs from 'fs';
import sanitize = require('sanitize-filename');
import Consts from '../helpers/consts';

import APP_CONFIG from '../../src/configs/app.config';
import { AppConst } from '../../src/commons/consts/app.const';

const dealerList = `http://localhost:${APP_CONFIG.ENV.APP.PORT}/${AppConst.API_PREFIX}/${AppConst.API_VERSION}/admin/web`;
const gameLog = `http://localhost:${APP_CONFIG.ENV.APP.PORT}/${AppConst.API_PREFIX}/${AppConst.API_VERSION}/admin/web/log`;

// ディーラー新規追加
describe('Add dealers to management tools', function () {
  let driver: webdriver.WebDriver;
  before(function () {
    driver = new webdriver.Builder().forBrowser("chrome").build();
  });
  
  // ディーラー名 境界値(null) - 失敗
  it(`s04-A-TC001: Dealer name (null) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();
    
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // ディーラー名 境界値(空白) - 失敗
  it(`s04-A-TC002: Dealer name (blank) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_NAME_BLANK);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // ディーラー名 境界値(最小) - 成功
  it(`s04-A-TC003: Dealer name (min) - successfully`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_NAME_MIN);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });
  
  // ディーラー名 境界値(最長) - 成功
  it(`s04-A-TC004: Dealer name (max) - successfully`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_NAME_MAX);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });

  // ディーラー名 境界値(最長) - 失敗
  it(`s04-A-TC005: Dealer name (over) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_NAME_OVER);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // ディーラー名 同名 - 成功
  it(`s04-A-TC006: Dealer name (same name) - successfully`, async () => {
    await driver.get(dealerList);

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });
  
  // 対戦数 境界値(null) - 失敗
  it(`s04-A-TC007: Number of matches (null) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // 対戦数 境界値(空白) - 失敗
  it(`s04-A-TC008: Number of matches (blank) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN_BLANK);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // 対戦数 境界値(正) - 成功
  it(`s04-A-TC009: Number of matches (plus) - successfully`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });
  
  // 対戦数 境界値(負) - 失敗
  it(`s04-A-TC010: Number of matches (minus) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN_MINUS);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // 対戦数 境界値(ゼロ) - 失敗
  it(`s04-A-TC011: Number of matches (zero) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN_ZERO);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // 対戦数 境界値(小数) - 失敗
  it(`s04-A-TC012: Number of matches (decimal) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN_DECIMAL);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // 対戦数 境界値(最大値) - 成功
  it(`s04-A-TC013: Number of matches (max) - successfully`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN_MAX);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });
  
  // 対戦数 境界値(最大値) - 失敗
  it(`s04-A-TC014: Number of matches (over) - failed`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN_OVER);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });
  
  // 白いワイルド 選択(スキップバインド2) - 成功
  it(`s04-A-TC015: White wild selection (Skip bind 2) - successfully`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });
  
  // 白いワイルド 選択(バインド2) - 成功
  it(`s04-A-TC016: White wild selection (Bind 2) - successfully`, async () => {
    await driver.get(dealerList);

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });

  after(function () {
    driver && driver.quit();
  });
});


// デモプレイヤー追加/試合開始、ログ
describe('Add demo player and start dealer and logging to management tools', function () {
  let driver: webdriver.WebDriver;
  const downloadDir = path.join(__dirname, 'downloads');

  before(function () {
    // ダウンロードディレクトリを設定  
    if (!fs.existsSync(downloadDir)) {
      fs.mkdirSync(downloadDir);
    }
    // Chromeのオプションを設定
    let options = new chrome.Options();
    options.setUserPreferences({ 'download.default_directory': downloadDir });

    driver = new webdriver.Builder().forBrowser("chrome").setChromeOptions(options).build();
  });

  // 1〜4回のデモプレイヤー追加
  it(`s04-B-TC001: Add demo player (1 - 4)`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const beforeText = await driver.findElement(webdriver.By.className("panel")).getText();

    for (let i = 0; i < 4; i++) {
      await driver.findElement(webdriver.By.className("add-btn")).click();
      await BlueBird.delay(50 * Consts.TIME_DELAY);
      await driver.navigate().refresh();
    }

    await driver.navigate().refresh();

    const afterText = await driver.findElement(webdriver.By.className("panel")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });

  // リロード
  it(`s04-B-TC002: Reload`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const beforeText = await driver.findElement(webdriver.By.tagName("Body")).getText();

    // デモプレイヤーを1つ追加
    await driver.findElement(webdriver.By.className("add-btn")).click();
    await BlueBird.delay(50 * Consts.TIME_DELAY);
    await driver.navigate().refresh();

    // リロード
    await driver.findElement(webdriver.By.className("reload")).click();

    const afterText = await driver.findElement(webdriver.By.tagName("Body")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });

  // 試合開始
  it(`s04-B-TC003: Start dealer`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    const beforeText = await driver.findElement(webdriver.By.tagName("Body")).getText();

    // デモプレイヤーを4つ追加して試合開始
    for (let i = 0; i < 4; i++) {
      await driver.findElement(webdriver.By.className("add-btn")).click();
      await BlueBird.delay(50 * Consts.TIME_DELAY);
      await driver.navigate().refresh();
    }

    await driver.navigate().refresh();

    await driver.findElement(webdriver.By.className("start-btn")).click();
    await BlueBird.delay(500 * Consts.TIME_DELAY);
    await driver.navigate().refresh();

    const afterText = await driver.findElement(webdriver.By.tagName("Body")).getText();
    chai.expect(beforeText).to.equal(afterText);
  });

  // ログのダウンロード
  it(`s04-B-TC004: Download a log`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_2_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    // デモプレイヤーを4つ追加して試合開始
    for (let i = 0; i < 4; i++) {
      await driver.findElement(webdriver.By.className("add-btn")).click();
      await BlueBird.delay(50 * Consts.TIME_DELAY);
      await driver.navigate().refresh();
    }

    await driver.navigate().refresh();

    await driver.findElement(webdriver.By.className("start-btn")).click();
    await BlueBird.delay(500 * Consts.TIME_DELAY);
    await driver.navigate().refresh();

    await driver.findElement(webdriver.By.className("download-btn")).click();

    // ダウンロードされたファイルの存在を確認
    const game_name = sanitize(await driver.findElement(webdriver.By.className("dealer-id")).getText(), { replacement: '_' }).replace(/\s/g, '_');
    const filePath = path.join(downloadDir, `${game_name}-${await driver.findElement(webdriver.By.className("dealer-name")).getText()}.log`);

    driver.wait(() => fs.existsSync(filePath), 5000)
      .then(() => chai.expect(fs.existsSync(filePath)).to.be.true)
      .catch(() => chai.expect.fail('File did not download within specified time'));
  });

  after(function () {
    driver && driver.quit();
  });
});

// ページング
describe('Paging', function () {
  let driver: webdriver.WebDriver;
  before(function () {
    driver = new webdriver.Builder().forBrowser("chrome").build();
  });

  // ディーラー一覧のページング
  it(`s04-C-TC001: Paging the dealer list page`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    for (let i = 0; i < 40; i++) {
      await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_1_NAME);
      await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
      await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
      await driver.findElement(webdriver.By.id("create-btn")).click();
    }

    const beforeText = await driver.findElement(webdriver.By.id("game-list")).getText();

    await driver.navigate().to(`${dealerList}?order=desc&page=2`);

    const afterText = await driver.findElement(webdriver.By.id("game-list")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });

  // ゲームログのページング
  it(`s04-C-TC002: Paging the game log`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_3_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    // デモプレイヤーを4つ追加して試合開始
    for (let i = 0; i < 4; i++) {
      await driver.findElement(webdriver.By.className("add-btn")).click();
      await BlueBird.delay(50 * Consts.TIME_DELAY);
      await driver.navigate().refresh();
    }

    await driver.navigate().refresh();

    await driver.findElement(webdriver.By.className("start-btn")).click();
    await BlueBird.delay(500 * Consts.TIME_DELAY);
    await driver.navigate().refresh();

    // 要素取得してディーラーIDを判定
    const dealerId = await driver.findElement(webdriver.By.className("dealer-id")).getText();
    
    await driver.get(`${gameLog}/${dealerId}?turn=1`);

    const beforeText = await driver.findElement(webdriver.By.tagName("Body")).getText();

    await driver.navigate().to(`${gameLog}/${dealerId}?turn=2`);

    const afterText = await driver.findElement(webdriver.By.tagName("Body")).getText();
    chai.expect(beforeText).to.not.equal(afterText);
  });

  after(function () {
    driver && driver.quit();
  });
});

// 検索
describe('Search', function () {
  let driver: webdriver.WebDriver;
  before(function () {
    driver = new webdriver.Builder().forBrowser("chrome").build();
  });

  // ゲームログの検索
  it(`s04-F-TC001: Search the game log`, async () => {
    await driver.get(dealerList);

    // ディーラー追加
    await driver.findElement(webdriver.By.id("new-dealer-name")).sendKeys(Consts.DEALER_4_NAME);
    await driver.findElement(webdriver.By.id("total-turn")).sendKeys(Consts.TOTAL_TURN);
    await driver.findElement(webdriver.By.id("white-wild")).sendKeys(Consts.WHITE_WILD.SKIP_BIND_2);
    await driver.findElement(webdriver.By.id("create-btn")).click();

    // デモプレイヤーを4つ追加して試合開始
    for (let i = 0; i < 4; i++) {
      await driver.findElement(webdriver.By.className("add-btn")).click();
      await BlueBird.delay(50 * Consts.TIME_DELAY);
      await driver.navigate().refresh();
    }

    await driver.navigate().refresh();

    await driver.findElement(webdriver.By.className("start-btn")).click();
    await BlueBird.delay(500 * Consts.TIME_DELAY);
    await driver.navigate().refresh();

    // 要素取得してディーラーIDを判定
    const dealerId = await driver.findElement(webdriver.By.className("dealer-id")).getText();

    await driver.get(`${gameLog}/${dealerId}?turn=1`);

    const checkboxes = Object.values(Consts.SOCKET.EVENT);
    let error = false;

    // Test all combinations
    Object.keys(checkboxes).forEach(async function (i) {
      // 全てのチェックを外す
      Object.keys(checkboxes).forEach(async function (j) {
        if (await driver.findElement(webdriver.By.id(`event-${checkboxes[j]}`)).isSelected()) {
          await driver.findElement(webdriver.By.id(`event-${checkboxes[j]}`)).click();
        }
      });
      const beforeText = await driver.findElement(webdriver.By.className("search-result-condition")).getText();

      // 1つだけチェックを入れる
      await driver.findElement(webdriver.By.id(`event-${checkboxes[i]}`)).click();
      await driver.findElement(webdriver.By.id("search-btn")).click();
      const afterText = await driver.findElement(webdriver.By.className("search-result-condition")).getText();

      if (beforeText === afterText) {
        error = true;
      }
    });

    // 全てのチェックを外す
    Object.keys(checkboxes).forEach(async function (i) {
      if (await driver.findElement(webdriver.By.id(`event-${checkboxes[i]}`)).isSelected()) {
        await driver.findElement(webdriver.By.id(`event-${checkboxes[i]}`)).click();
      }
    });

    // 2のn乗のパターンを試す
    const numPatterns = Math.pow(2, checkboxes.length);

    for (let i = 0; i < numPatterns; i++) {
      const beforeText = await driver.findElement(webdriver.By.className("search-result-condition")).getText();
      for (let j = 0; j < checkboxes.length; j++) {
        const checkbox = driver.findElement(webdriver.By.id(`event-${checkboxes[j]}`));
        const isSelected = await checkbox.isSelected();
        // もしパターンと現在の状態が異なれば、クリックして状態を変更
        if ((i & (1 << j)) !== 0 !== isSelected) {
            await checkbox.click();
        }
      }
      // 検索
      await driver.findElement(webdriver.By.id("search-btn")).click();
      const afterText = await driver.findElement(webdriver.By.className("search-result-condition")).getText();
      
      if (beforeText === afterText) {
        error = true;
      }
    }

    chai.expect(error).to.be.false;
  });

  after(function () {
    driver && driver.quit();
  });
});


