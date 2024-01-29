import argparse
import os
import math
import random
import sys
import socketio
import time
from status import Status, Games
from strategy import *

from rich import print




"""
定数
"""
# Socket通信の全イベント名
class SocketConst:
    class EMIT:
        JOIN_ROOM = 'join-room' # 試合参加
        RECEIVER_CARD = 'receiver-card' # カードの配布
        FIRST_PLAYER = 'first-player' # 対戦開始
        COLOR_OF_WILD = 'color-of-wild' # 場札の色を変更する
        UPDATE_COLOR = 'update-color' # 場札の色が変更された
        SHUFFLE_WILD = 'shuffle-wild' # シャッフルしたカードの配布
        NEXT_PLAYER = 'next-player' # 自分の手番
        PLAY_CARD = 'play-card' # カードを出す
        DRAW_CARD = 'draw-card' # カードを山札から引く
        PLAY_DRAW_CARD = 'play-draw-card' # 山札から引いたカードを出す
        CHALLENGE = 'challenge' # チャレンジ
        PUBLIC_CARD = 'public-card' # 手札の公開
        POINTED_NOT_SAY_UNO = 'pointed-not-say-uno' # UNO宣言漏れの指摘
        SPECIAL_LOGIC = 'special-logic' # スペシャルロジック
        FINISH_TURN = 'finish-turn' # 対戦終了
        FINISH_GAME = 'finish-game' # 試合終了
        PENALTY = 'penalty' # ペナルティ


# UNOのカードの色
class Color:
    RED = 'red' # 赤
    YELLOW = 'yellow' # 黄
    GREEN = 'green' # 緑
    BLUE = 'blue' # 青
    BLACK = 'black' # 黒
    WHITE = 'white' # 白


# UNOの記号カード種類
class Special:
    SKIP = 'skip' # スキップ
    REVERSE = 'reverse' # リバース
    DRAW_2 = 'draw_2' # ドロー2
    WILD = 'wild' # ワイルド
    WILD_DRAW_4 = 'wild_draw_4' # ワイルドドロー4
    WILD_SHUFFLE = 'wild_shuffle' # シャッフルワイルド
    WHITE_WILD = 'white_wild' # 白いワイルド


# カードを引く理由
class DrawReason:
    DRAW_2 = 'draw_2' # 直前のプレイヤーがドロー2を出した場合
    WILD_DRAW_4 = 'wild_draw_4' # 直前のプレイヤーがワイルドドロー4を出した場合
    BIND_2 = 'bind_2' # 直前のプレイヤーが白いワイルド（バインド2）を出した場合
    SKIP_BIND_2 = 'skip_bind_2' # 直前のプレイヤーが白いワイルド（スキップバインド2）を出した場合
    NOTHING = 'nothing' # 理由なし


TEST_TOOL_HOST_PORT = '3000' # 開発ガイドラインツールのポート番号
ARR_COLOR = [Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE] # 色変更の選択肢

"""
コマンドラインから受け取った変数等
"""
parser = argparse.ArgumentParser(description='A demo player written in Python')
parser.add_argument('host', action='store', type=str, help='Host to connect')
parser.add_argument('room_name', action='store', type=str, help='Name of the room to join')
parser.add_argument('player', action='store', type=str, help='Player name you join the game as')
parser.add_argument('event_name', action='store', nargs='?', default=None, type=str, help='Event name for test tool') # 追加


args = parser.parse_args(sys.argv[1:])
host = args.host # 接続先（ディーラープログラム or 開発ガイドラインツール）
room_name = args.room_name # ディーラー名
player = args.player # プレイヤー名
event_name = args.event_name # Socket通信イベント名
is_test_tool = TEST_TOOL_HOST_PORT in host # 接続先が開発ガイドラインツールであるかを判定
SPECIAL_LOGIC_TITLE = '◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯◯' # スペシャルロジック名
TIME_DELAY = 10 # 処理停止時間

"""
グローバル変数
"""
games = Games()
game_status = Status()
once_connected = False
id = '' # 自分のID

"""
コマンドライン引数のチェック
"""
if not host:
    # 接続先のhostが指定されていない場合はプロセスを終了する
    print('Host missed')
    os._exit(0)
else:
    print('Host: {}'.format(host))

# ディーラー名とプレイヤー名の指定があることをチェックする
if not room_name or not player:
    print('Arguments invalid')

    if not is_test_tool:
        # 接続先がディーラープログラムの場合はプロセスを終了する
        os._exit(0)
else:
    print('Dealer: {}, Player: {}'.format(room_name, player))


# 開発ガイドラインツールSTEP1で送信するサンプルデータ
TEST_TOOL_EVENT_DATA = {
    SocketConst.EMIT.JOIN_ROOM: {
        'player': player,
        'room_name': room_name,
    },
    SocketConst.EMIT.COLOR_OF_WILD: {
        'color_of_wild': 'red',
    },
    SocketConst.EMIT.PLAY_CARD: {
        'card_play': { 'color': 'black', 'special': 'wild' },
        'yell_uno': False,
        'color_of_wild': 'blue',
    },
    SocketConst.EMIT.DRAW_CARD: {},
    SocketConst.EMIT.PLAY_DRAW_CARD: {
        'is_play_card': True,
        'yell_uno': True,
        'color_of_wild': 'blue',
    },
    SocketConst.EMIT.CHALLENGE: {
        'is_challenge': True,
    },
    SocketConst.EMIT.POINTED_NOT_SAY_UNO: {
        'target': 'Player 1',
    },
    SocketConst.EMIT.SPECIAL_LOGIC: {
        'title': SPECIAL_LOGIC_TITLE,
    },
}


# Socketクライアント
sio = socketio.Client()


def random_by_number(num):
    """
    乱数取得

    Args:
        num (int):

    Returns:
        int:
    """
    return math.floor(random.random() * num)


def determine_if_execute_pointed_not_say_uno(number_card_of_player:dict) -> None:
    """
    他のプレイヤーのUNO宣言漏れをチェックする

    Args:
        number_card_of_player(dict): {キー:プレイヤーID, 値:手札の枚数}
    Returns:
        None
    """
    global id, game_status

    target = None
    # 手札の枚数が1枚だけのプレイヤーを抽出する
    # 2枚以上所持しているプレイヤーはUNO宣言の状態をリセットする
    for k, v in number_card_of_player.items():
        if k == id:
            # 自分のIDは処理しない
            continue
        elif v == 1:
            # 1枚だけ所持しているプレイヤー
            target = k
            break
        elif k in game_status.uno_declared:
            # 2枚以上所持しているプレイヤーはUNO宣言の状態をリセットする
            del game_status.uno_declared[k]

    if target == None:
        # 1枚だけ所持しているプレイヤーがいない場合、処理を中断する
        return

    # 抽出したプレイヤーがUNO宣言を行っていない場合宣言漏れを指摘する
    if target not in game_status.uno_declared.keys():
        send_event(SocketConst.EMIT.POINTED_NOT_SAY_UNO, { 'target': target })
        time.sleep(TIME_DELAY / 1000)


def send_event(event, data, callback = pass_func):
    """
    送信イベント共通処理

    Args:
        event (str): Socket通信イベント名
        data (Any): 送信するデータ
        callback (func): 個別処理
    """
    # print('Send {} event.'.format(event))
    # print('req_data: ', data)

    def after_func(err, res):
        if err:
            # print('{} event failed!'.format(event))
            # print(err)
            return

        # print('Send {} event.'.format(event))
        # print('res_data: ', res)
        callback(res)

    sio.emit(event, data, callback=after_func)


def receive_event(event, data, callback = pass_func):
    """
    受信イベント共通処理

    Args:
        event (str): Socket通信イベント名
        data (Any): 送信するデータ
        callback (func): 個別処理
    """
    # print('Receive {} event.'.format(event))
    # print('res_data: ', data)

    callback(data)


"""
Socket通信の確立
"""
@sio.on('connect')
def on_connect():
    print('Client connect successfully!')

    if not once_connected:
        if is_test_tool:
            # テストツールに接続
            if not event_name:
                # イベント名の指定がない（開発ガイドラインSTEP2の受信のテストを行う時）
                print('Not found event name')
            elif not event_name in TEST_TOOL_EVENT_DATA:
                # イベント名の指定があり、テストデータが定義されていない場合はエラー
                print('Undefined test data. eventName: ', event_name)
            else:
                # イベント名の指定があり、テストデータが定義されている場合は送信する(開発ガイドラインSTEP1の送信のテストを行う時)
                send_event(event_name, TEST_TOOL_EVENT_DATA[event_name])
        else:
            # ディーラープログラムに接続
            data = {
                'room_name': room_name,
                'player': player,
            }

            def join_room_callback(*args):
                global once_connected, id
                print('Client join room successfully!')
                once_connected = True
                id = args[0].get('your_id')
                print('My id is {}'.format(id))

            send_event(SocketConst.EMIT.JOIN_ROOM, data, join_room_callback)


"""
Socket通信を切断
"""
@sio.on('disconnect')
def on_disconnect():
    print('Client disconnect.')
    os._exit(0)


"""
Socket通信受信
"""
# プレイヤーがゲームに参加
@sio.on(SocketConst.EMIT.JOIN_ROOM)
def on_join_room(data_res):
    receive_event(SocketConst.EMIT.JOIN_ROOM, data_res)


# カードが手札に追加された
@sio.on(SocketConst.EMIT.RECEIVER_CARD)
def on_reciever_card(data_res):
    global game_status
    cards_receive = data_res["cards_receive"]
    game_status.my_cards += cards_receive
    if len(cards_receive) == 5 and {"special": "wild_draw_4", "color": "black"} in cards_receive:
        cards_receive.remove({"special": "wild_draw_4", "color": "black"})
    game_status.update_cards_status(cards_receive)
    # print("私の手札は")
    # print(game_status.my_cards)
    receive_event(SocketConst.EMIT.RECEIVER_CARD, data_res)


# 対戦の開始
@sio.on(SocketConst.EMIT.FIRST_PLAYER)
def on_first_player(data_res):
    # global id, game_status, num_game, first_player, challenge_success_cnt
    global id, game_status, games

    if games.num_game < 300:
        if games.scores[0] < -1300 and games.scores[0] < games.scores[1]:
            game_status.version = 'v3'
        else:
            game_status.version = 'v2'
    elif games.num_game < 500:
        if games.scores[0] < -200:
            if games.num_game < 400 and games.scores[1] > -500:
                game_status.version = 'v3'
            elif games.scores[1] > -300:
                game_status.version = 'v3'
            elif games.scores[0] < -1000 and games.scores[0] < games.scores[1]:
                game_status.version = 'v3'
            else:
                game_status.version = 'v2'
        else:
            game_status.version = 'v2'
    else:
        if games.scores[0] < games.scores[1]:
            game_status.version = 'v3'
        else:
            game_status.version = 'v2'
    print('Game', games.num_game + 1)
    print(f'game_scores: v2 = {games.scores[0]}, v3 = {games.scores[1]}')
    print(f'version: {game_status.version}')


    # チャレンジ成功数を記録するための辞書
    if games.num_game == 0:
        for player_id in data_res['play_order']:
            if player_id != id:
                games.challenge_cnt[player_id] = [0, 0] # [トータル数, 成功数]
                games.challenged_cnt[player_id] = [0, 0, 0] # [ドロ4出した回数, チャレンジ回数, 成功数]

    games.num_game += 1
    game_status.set_play_order(data_res['play_order'], id)

    first_card = data_res['first_card']
    if "special" in first_card.keys():
        if first_card["special"] == "reverse":
                game_status.reverse_order()

    first_player = data_res['first_player']

    # 最後にターンをプレイしたプレイヤーを初期化する
    game_status.who_played_last = first_player

    # プレイヤー全員の手札枚数を初期化する
    game_status.init_player_card_counts(data_res['play_order'])
    game_status.field_cards.append(data_res['first_card'])
    game_status.update_cards_status(data_res['first_card'])

    receive_event(SocketConst.EMIT.FIRST_PLAYER, data_res)


# 場札の色指定を要求
@sio.on(SocketConst.EMIT.COLOR_OF_WILD)
def on_color_of_wild(data_res):
    def color_of_wild_callback(data_res):
        global game_status
        color = select_change_color(game_status.my_cards, game_status)
        data = {
            'color_of_wild': color,
        }

        # 色変更を実行する
        send_event(SocketConst.EMIT.COLOR_OF_WILD, data)

    receive_event(SocketConst.EMIT.COLOR_OF_WILD, data_res, color_of_wild_callback)


# 場札の色が変わった
@sio.on(SocketConst.EMIT.UPDATE_COLOR)
def on_update_color(data_res):
    def on_update_color_callback(data_res):
        global game_status

        # どの色に変更されたか記録する
        chosen_color = data_res.get("color")
        game_status.player_color_log[game_status.who_played_last].append([chosen_color, "wild", True])

        # 場に出されたカードのログにおいて、カード色を black --> chosen_color に変更する
        game_status.field_cards[-1]["color"] = chosen_color
        # DEBUG
        # print(f"---場カードログの色を黒から{chosen_color}へ変更---")
        # print("場に出されたカード:", game_status.field_cards[-1])

    receive_event(SocketConst.EMIT.UPDATE_COLOR, data_res, on_update_color_callback)


# シャッフルワイルドにより手札状況が変更
@sio.on(SocketConst.EMIT.SHUFFLE_WILD)
def on_shuffle_wild(data_res):
    global game_status

    def shuffle_wild_callback(data_res):
        global id, game_status
        game_status.uno_declared = {}

        #シャッフルワイルドで公開手札をリセットする
        game_status.init_open_cards()
        game_status.init_my_open_cards()

        for k, v in data_res.get('number_card_of_player').items():
            if v == 1:
                # シャッフル後に1枚になったプレイヤーはUNO宣言を行ったこととする
                game_status.uno_declared[k] = True
                if id != k:
                    game_status.set_uno_player(k)
                else:
                    game_status.my_uno_flag = True
                #break

            elif k in game_status.uno_declared:
                # シャッフル後に2枚以上のカードが配られたプレイヤーはUNO宣言の状態をリセットする
                if id != k:
                    game_status.undo_uno_player(k)
                else:
                    game_status.my_uno_flag = False

                del game_status.uno_declared[k]

        # shuffle wildにより各プレイヤーの手札枚数がリセット
        # 最新状態に更新しておく
        for k, v in data_res['number_card_of_player'].items():
            game_status.check_player_card_counts(k, v)

        # print("---シャッフルワイルド発動---")
        game_status.return_my_cards()
        game_status.update_cards_status(data_res.get("cards_receive"))
        game_status.set_my_cards(data_res.get("cards_receive"))

    receive_event(SocketConst.EMIT.SHUFFLE_WILD, data_res, shuffle_wild_callback)


# 自分の番
@sio.on(SocketConst.EMIT.NEXT_PLAYER)
def on_next_player(data_res):
    global game_status

    # print("私は"+ id + "です")

    def next_player_callback(data_res):
        # global game_status, challenge_success, id, num_game, first_player, challenge_success_cnt
        global id, game_status, games

        before_player = data_res.get('before_player')
        before_card = data_res.get('card_before')
        cards = data_res.get('card_of_player')
        num_card_of_player = data_res.get('number_card_of_player')

        next_player = game_status.get_next_id()
        mid_player = game_status.get_mid_id()
        # challenge_success = game_status.challenge_success.get(next_player, False)
        num_of_deck = game_status.calculate_num_of_deck(id, num_card_of_player)

        # if game_status.turn_right != data_res.get('turn_right'):
            # print('順番が違うよ')
            # print(data_res.get('before_player'))
            # print(game_status.get_before_id())

        game_status.check_uno_player(id, num_card_of_player)

        determine_if_execute_pointed_not_say_uno(num_card_of_player)

        # 各プレイヤーの手札枚数を最新状態に更新しておく
        for k, v in num_card_of_player.items():
            game_status.check_player_card_counts(k, v)

        # 自分の手札を更新しておく
        game_status.set_my_cards(cards)
        game_status.my_uno_flag = len(cards) == 1

        # print(f'デバッグプリント {games.num_game}対戦目')
        # print(game_status.order_dic)
        # print(game_status.my_cards)
        # game_status.debug_print()

        if data_res.get('draw_reason') == DrawReason.WILD_DRAW_4:
            # カードを引く理由がワイルドドロー4の時、チャレンジを行うことができる。

            # print("チャレンジする？")
            # print(game_status.cards_status)

            cnt = 1
            while game_status.field_cards[-1*cnt - 1].get('color', None) == "white" or game_status.field_cards[-1*cnt - 1].get('color', None) is None: #直前の色が白以外になるまで探索
                cnt += 1
            field_card = game_status.field_cards[-1*cnt - 1] #wild_draw_4の直前に出されたカード

            # print("wild前は")
            # print(field_card)

            # print('直前があってるか', before_player == game_status.get_before_id())
            is_challenge = challenge_dicision(field_card, id, before_player, num_card_of_player, num_of_deck, game_status, games)
            if game_status.special_logic_flag[0]:
                game_status.special_logic_flag[0] = False
                title = "千里眼ッ!!!!!"
                send_event(SocketConst.EMIT.SPECIAL_LOGIC, { 'title': title })
            send_event(SocketConst.EMIT.CHALLENGE, { 'is_challenge': is_challenge } )
            if is_challenge:
                return


        if data_res.get('must_call_draw_card'):
            # カードを引かないと行けない時
            game_status.my_uno_flag = False
            send_event(SocketConst.EMIT.DRAW_CARD, {})
            return

        # 自分の手札から、出せるカードのリストとプレイモードを取得する
        play_card, play_mode = select_play_card(cards, id, next_player, num_card_of_player, num_of_deck, before_card, game_status, games)
        # DEBUG print

        # print("プレイモード:", play_mode)

        # 選出したカードがある時
        if play_card:
            # # print('selected card: {} {}'.format(play_card.get('color'), play_card.get('number') or play_card.get('special')))
            game_status.my_uno_flag = len(cards) == 2
            data = {
                'card_play': play_card,
                'yell_uno': game_status.my_uno_flag  # 残り手札数を考慮してUNOコールを宣言する
            }

            if play_card.get('special') == Special.WILD or play_card.get('special') == Special.WILD_DRAW_4:
                #UNOplayer3人の時は
                if uno_player_cnt(game_status.order_dic) == 3:
                    # print("uno-3-deffensive-color-choice")
                    color_lis = deffesive_color_order(next_player, game_status)
                    color = color_lis[0]

                elif uno_player_cnt(game_status.order_dic) == 2:
                    if get_uno_player_pos(game_status.order_dic) == ["直前","対面"] or get_uno_player_pos(game_status.order_dic) == ["対面","直前"]:
                        # print("uno-2-next-mid-deffensive-color-choice")
                        color_lis = deffesive_color_order(mid_player, game_status)
                        color = color_lis[0]

                    elif get_uno_player_pos(game_status.order_dic) == ["直後","対面"] or get_uno_player_pos(game_status.order_dic) == ["対面", "直後"]:
                        # print("uno-2-before-mid-deffensive-color-choice")
                        color_lis = deffesive_color_order(next_player, game_status)
                        color = color_lis[0]

                    elif get_uno_player_pos(game_status.order_dic) == ["直後","直前"] or get_uno_player_pos(game_status.order_dic) == ["直前","直後"]:
                        # print("uno-2-before-next-deffensive-color-choice")
                        color_lis = deffesive_color_order(next_player, game_status)
                        color = color_lis[0]

                    else:
                        # print("Emergency: player_v3 uno_player 2 Error")
                        color = select_change_color(game_status.my_cards, game_status, play_mode)

                elif uno_player_cnt(game_status.order_dic) == 1:
                    if get_uno_player_pos(game_status.order_dic) == ["直後"]:

                        # print("uno-2-next-deffensive-color-choice")
                        if len(game_status.other_open_cards[next_player]) > 0: #特殊処理が走る
                            #直後の人が持っていない色を認識
                            my_colors = offensive_color_order(cards, game_status.cards_status)
                            open_card = game_status.other_open_cards[next_player][0]
                            open_card_coler = open_card["color"]

                            if open_card_coler in {"black", "white"}:
                                color = my_colors[0]
                            else:
                                for my_coler in my_colors:
                                    if my_coler != open_card_coler:
                                        color = my_coler
                                        break

                        else:
                            color_lis = deffesive_color_order(next_player, game_status)
                            color = color_lis[0]

                    elif get_uno_player_pos(game_status.order_dic) == ["対面"]:
                        # print("uno-2-mid-deffensive-color-choice")
                        color_lis = deffesive_color_order(mid_player, game_status)
                        color = color_lis[0]

                    elif get_uno_player_pos(game_status.order_dic) == ["直前"]:

                        # print("uno-2-before-deffensive-color-choice")
                        if len(game_status.other_open_cards[before_player]) > 0: #特殊処理が走る
                            #直後の人が持っていない色を認識
                            my_colors = offensive_color_order(cards, game_status.cards_status)
                            open_card = game_status.other_open_cards[before_player][0]
                            open_card_coler = open_card["color"]

                            if open_card_coler in {"black", "white"}:
                                color = my_colors[0]
                            else:
                                for my_coler in my_colors:
                                    if my_coler != open_card_coler:
                                        color = my_coler
                                        break

                        else:
                            color_lis = deffesive_color_order(before_player, game_status)
                            color = color_lis[0]

                    else:
                        # print("Emergency: player_v3 uno_player 1 Error")
                        color = select_change_color(game_status.my_cards, game_status, play_mode)

                else:
                    target_id = None
                    if play_mode == "deffensive":
                        # プレイヤーの手札枚数が最も少ないプレイヤーを取得する
                        cnt_min = 112
                        for k, v in num_card_of_player.items():
                            if k != id and v < cnt_min:
                                target_id = k
                                cnt_min = v
                    color = select_change_color(game_status.my_cards, game_status, play_mode, target_id)

                data['color_of_wild'] = color

            if play_card.get('special') == Special.WILD_DRAW_4:
                games.challenged_cnt[next_player][0] += 1

            if game_status.special_logic_flag[1]:
                game_status.special_logic_flag[1] = False
                title = "もう絶望する必要なんて，ない！"
                send_event(SocketConst.EMIT.SPECIAL_LOGIC, { 'title': title })

            send_event(SocketConst.EMIT.PLAY_CARD, data)

        else:
            # 引いたカードを出すイベントを実行
            def draw_card_callback(res):
                global id, game_status, games

                # 引いたカードが場に出せない場合、処理を終了
                if not res.get('can_play_draw_card'):
                    game_status.my_uno_flag = False
                    # print('引いたカードが出せない')
                    return

                # 引いたカード情報の取得
                draw_card = res.get('draw_card')[0]

                # プレイモードに応じて処理を変える
                # 攻撃モードの場合
                if play_mode == "offensive":
                    # 引いてきたカードがシャッフルワイルドの場合、出さずに処理を終了
                    if draw_card.get("special") == "wild_shuffle" and not (len(cards) >= 4 and min_cards_check(id, num_card_of_player) <= 2):
                        game_status.my_uno_flag = False
                        # print('引いたカード出せるけど出さない')
                        data = {
                            'is_play_card': False,
                            'yell_uno': game_status.my_uno_flag  # 残り手札数を考慮してUNOコールを宣言する
                        }
                        send_event(SocketConst.EMIT.PLAY_DRAW_CARD, data)
                        return
                    elif not game_status.wild_shuffle_flag() and draw_card.get("special")  == "white_wild":
                        game_status.my_uno_flag = False
                        # print('引いたカード出せるけど出さない')
                        data = {
                            'is_play_card': False,
                            'yell_uno': game_status.my_uno_flag  # 残り手札数を考慮してUNOコールを宣言する
                        }
                        send_event(SocketConst.EMIT.PLAY_DRAW_CARD, data)
                        return

                # 直後がUNOであり、自分もUNOでワイルドカードが引いたとき
                if get_uno_player_pos(game_status.order_dic) == ["直後"] and game_status.my_uno_flag and draw_card.get("special") in ["wild", "wild_shuffle", "white_wild"]:
                    #直後が手札公開をしていて,その手札から読める絶対に出せない色＝場の色である場合出さない
                    if len(game_status.other_open_cards[next_player]) > 0: #特殊処理が走る
                        #直後の人が持っていない色を認識
                        open_card = game_status.other_open_cards[next_player][0]
                        open_card_coler = open_card["color"]
                        open_card_number = open_card.get("number")
                        open_card_special = open_card.get("special")

                        if open_card_coler not in {"black", "white"} and before_card["color"] != open_card_coler:
                            if open_card_number is not None and open_card_number != before_card.get("number"):
                                #出さない
                                game_status.my_uno_flag = False
                                data = {
                                    'is_play_card': False,
                                    'yell_uno': game_status.my_uno_flag  # 残り手札数を考慮してUNOコールを宣言する
                                }
                                send_event(SocketConst.EMIT.PLAY_DRAW_CARD, data)
                                return
                            elif open_card_special is not None and open_card_special != before_card.get("special"):
                                #出さない
                                game_status.my_uno_flag = False
                                data = {
                                    'is_play_card': False,
                                    'yell_uno': game_status.my_uno_flag  # 残り手札数を考慮してUNOコールを宣言する
                                }
                                send_event(SocketConst.EMIT.PLAY_DRAW_CARD, data)
                                return


                # 以後、引いたカードが場に出せるときの処理
                game_status.my_uno_flag = len(cards) == 1
                data = {
                    'is_play_card': True,
                    'yell_uno': game_status.my_uno_flag  # 残り手札数を考慮してUNOコールを宣言する
                }

                play_card = res.get('draw_card')[0]
                if play_card.get('special') == Special.WILD or play_card.get('special') == Special.WILD_DRAW_4:
                    #UNOplayer3人の時は
                    if uno_player_cnt(game_status.order_dic) == 3:
                        # print("uno-3-deffensive-color-choice")
                        color_lis = deffesive_color_order(next_player, game_status)
                        color = color_lis[0]

                    elif uno_player_cnt(game_status.order_dic) == 2:
                        if get_uno_player_pos(game_status.order_dic) == ["直前","対面"] or get_uno_player_pos(game_status.order_dic) == ["対面","直前"]:
                            # print("uno-2-next-mid-deffensive-color-choice")
                            color_lis = deffesive_color_order(mid_player, game_status)
                            color = color_lis[0]

                        elif get_uno_player_pos(game_status.order_dic) == ["直後","対面"] or get_uno_player_pos(game_status.order_dic) == ["対面", "直後"]:
                            # print("uno-2-before-mid-deffensive-color-choice")
                            color_lis = deffesive_color_order(next_player, game_status)
                            color = color_lis[0]

                        elif get_uno_player_pos(game_status.order_dic) == ["直後","直前"] or get_uno_player_pos(game_status.order_dic) == ["直前","直後"]:
                            # print("uno-2-before-next-deffensive-color-choice")
                            color_lis = deffesive_color_order(next_player, game_status)
                            color = color_lis[0]

                        else:
                            # print("Emergency: player_v3 uno_player 2(Draw) Error")
                            color = select_change_color(game_status.my_cards, game_status, play_mode)

                    elif uno_player_cnt(game_status.order_dic) == 1:
                        if get_uno_player_pos(game_status.order_dic) == ["直後"]:
                            # print("draw-and-uno-1-next-deffensive-color-choice")
                            if len(game_status.other_open_cards[next_player]) > 0: #特殊処理が走る
                                #直後の人が持っていない色を認識
                                my_colors = offensive_color_order(cards, game_status.cards_status)
                                open_card = game_status.other_open_cards[next_player][0]
                                open_card_coler = open_card["color"]

                                if open_card_coler in {"black", "white"}:
                                    color = my_colors[0]
                                else:
                                    for my_coler in my_colors:
                                        if my_coler != open_card_coler:
                                            color = my_coler
                                            break
                            else:
                                color_lis = deffesive_color_order(next_player, game_status)
                                color = color_lis[0]

                        elif get_uno_player_pos(game_status.order_dic) == ["対面"]:
                            # print("draw-and-uno-1-mid-deffensive-color-choice")
                            color_lis = deffesive_color_order(mid_player, game_status)
                            color = color_lis[0]

                        elif get_uno_player_pos(game_status.order_dic) == ["直前"]:
                            # print("draw-and-uno-1-before-deffensive-color-choice")
                            if len(game_status.other_open_cards[before_player]) > 0: #特殊処理が走る
                                #直後の人が持っていない色を認識
                                my_colors = offensive_color_order(cards, game_status.cards_status)
                                open_card = game_status.other_open_cards[before_player][0]
                                open_card_coler = open_card["color"]

                                if open_card_coler in {"black", "white"}:
                                    color = my_colors[0]
                                else:
                                    for my_coler in my_colors:
                                        if my_coler != open_card_coler:
                                            color = my_coler
                                            break
                            else:
                                color_lis = deffesive_color_order(before_player, game_status)
                                color = color_lis[0]

                        else:
                            # print("Emergency: player_v3 uno_player 1(Draw) Error")
                            color = select_change_color(game_status.my_cards, game_status, play_mode)

                    else:
                        target_id = None
                        if play_mode == "deffensive":
                            # プレイヤーの手札枚数が最も少ないプレイヤーを取得する
                            cnt_min = 112
                            for k, v in num_card_of_player.items():
                                if k != id and v < cnt_min:
                                    target_id = k
                                    cnt_min = v
                        color = select_change_color(game_status.my_cards, game_status, play_mode, target_id)

                    data['color_of_wild'] = color

                if play_card.get('special') == Special.WILD_DRAW_4:
                    games.challenged_cnt[next_player][0] += 1

                # 引いたカードを出すイベントを実行
                # print('引いたカードを出す')
                send_event(SocketConst.EMIT.PLAY_DRAW_CARD, data)
                return

            # カードを引くイベントを実行
            send_event(SocketConst.EMIT.DRAW_CARD, {}, draw_card_callback)

    receive_event(SocketConst.EMIT.NEXT_PLAYER, data_res, next_player_callback)


# カードが場に出た
@sio.on(SocketConst.EMIT.PLAY_CARD)
def on_play_card(data_res):
    global id, game_status
    def play_card_callback(data_res):
        global id, game_status
        player = data_res.get('player')
        card_play = data_res.get('card_play')

        # UNO宣言を行った場合は記録する
        if data_res.get('yell_uno'):
            game_status.uno_declared[player] = data_res.get('yell_uno')
            if id != player:
                game_status.set_uno_player(player)

        # カードを場に出した(game_status側処理)
        game_status.play_card(card_play, player)
        game_status.num_of_field += 1

        if id != player:
            # 自分の出したカードでなければ cards_statusを更新する
            # print("私以外だよ")
            game_status.update_cards_status(card_play)
            # 公開されていた手札に含まれていた場合は消去する
            game_status.remove_other_player_cards(player, card_play)
        else:
            # print("私だよ")
            game_status.remove_my_open_cards(card_play)
            # if card_play != {'color': 'black', 'special': 'wild_shuffle'}:
            if card_play in game_status.my_cards:
                game_status.my_cards.remove(card_play)

        # play_content = data_res['card_play']
        if "special" in card_play.keys():
            if card_play["special"] == "reverse":
                game_status.reverse_order()

        # game_status.player_color_log[player][-1][2] = False
        # 最後にカードをプレイしたプレイヤーを更新
        game_status.who_played_last = player

        # ホワイトワイルドの効果が切れてるのを確認
        if game_status.is_white_activate[player] > 0:
            game_status.is_white_activate[player] = 0

    receive_event(SocketConst.EMIT.PLAY_CARD, data_res, play_card_callback)


# 山札からカードを引いた
@sio.on(SocketConst.EMIT.DRAW_CARD)
def on_draw_card(data_res):
    global id, game_status
    def draw_card_callback(data_res):
        global id, game_status
        player = data_res.get('player')
        # カードが増えているのでUNO宣言の状態をリセットする
        if player in game_status.uno_declared:
            if id != player:
                game_status.undo_uno_player(player)
            del game_status.uno_declared[player]

        # 山札からカードが引かれた(game_status側処理)
        game_status.draw_card(player)

    receive_event(SocketConst.EMIT.DRAW_CARD, data_res, draw_card_callback)


# 山札から引いたカードが場に出た
@sio.on(SocketConst.EMIT.PLAY_DRAW_CARD)
def on_play_draw_card(data_res):
    global id, game_status
    def play_draw_card_callback(data_res):
        global id, game_status

        player = data_res.get('player')
        card_play = data_res.get('card_play')
        if data_res.get('is_play_card'):
            if data_res.get('yell_uno'):
            # UNO宣言を行った場合は記録する
                game_status.uno_declared[player] = data_res.get('yell_uno')
                if id != player:
                    game_status.set_uno_player(player)

            # カードを場に出した(game_status側処理)
            game_status.play_card(card_play, player)
            game_status.num_of_field += 1

            if id != player:
                # 自分の出したカードでなければ cards_statusを更新する
                game_status.update_cards_status(card_play)
            else:
                # print("私だよ！")
                # if card_play != {'color': 'black', 'special': 'wild_shuffle'}:
                if card_play in game_status.my_cards:
                    game_status.my_cards.remove(card_play)

            # play_content = data_res['card_play']
            if "special" in card_play.keys():
                if card_play["special"] == "reverse":
                    game_status.reverse_order()

            # 最後にカードをプレイしたプレイヤーを更新
            game_status.who_played_last = player

    receive_event(SocketConst.EMIT.PLAY_DRAW_CARD, data_res, play_draw_card_callback)


# チャレンジの結果
@sio.on(SocketConst.EMIT.CHALLENGE)
def on_challenge(data_res):
    # global game_status, id, challenge_success, challenge_success_cnt
    global id, game_status, games

    # レスポンス取得
    challenger = data_res.get("challenger")
    target = data_res.get("target")
    is_challenge = data_res.get("is_challenge")
    is_challenge_success = data_res.get("is_challenge_success")

    # if target == id and is_challenge_success: # 自分にチャレンジされて成功されたら
    #     game_status.challenge_success[challenger] = True
    # else:
    #     game_status.challenge_success[challenger] = False

    # チャレンジした場合
    if is_challenge:
        if challenger == id:
            games.challenge_cnt[target][0] += 1
        if target == id:
            games.challenged_cnt[challenger][1] += 1
            game_status.my_open_cards[challenger] = game_status.my_cards.copy()
            # print('チャレンジされた！')
            # print(game_status.my_open_cards)

        # チャレンジが成功した場合は
        if is_challenge_success:
            # ターゲットがペナルティとして山札から4枚引く
            game_status.draw_card(target)

            # 場に出されていたwild_draw_4を手札に戻す
            wild_draw_4 = game_status.field_cards.pop() # wild_draw_4が取り出される
            game_status.num_of_field -= 1 # 場のカードが1枚減る
            game_status.player_card_counts[target] += 1 # プレイヤーの手札の枚数が+1される
            if target != id: # wild_draw_4を出したプレイヤーが自分でない場合
                # 自分からwild_draw_4が見えなくなるので cards_statusを元に戻す
                game_status.cards_status["black"]["wild_draw_4"] += 1
            else:
                game_status.challenge_success = True
                games.challenged_cnt[challenger][2] += 1
                game_status.my_open_cards[challenger].append({"special": "wild_draw_4", "color": "black"})

            # チャレンジ成功数をインクリメント
            if challenger == id:
                games.challenge_cnt[target][1] += 1

        # チャレンジが失敗した場合は
        else:
            # チャレンジャーが wild_draw_4の効果を受けて4枚ドロー
            game_status.draw_card(challenger)

            # 追加でペナルティとして山札から2枚引く
            game_status.draw_card(challenger, penalty_draw=2)

    # チャレンジしない場合
    else:
        # wild_draw_4の効果を受けて4枚ドロー
        game_status.draw_card(challenger)

    receive_event(SocketConst.EMIT.CHALLENGE, data_res)


# チャレンジによる手札の公開
@sio.on(SocketConst.EMIT.PUBLIC_CARD)
def on_public_card(data_res):
    global game_status
    # print("チャレンジによる手札の公開", data_res)
    game_status.set_other_player_cards(data_res.get("card_of_player"), data_res.get("cards"))

    receive_event(SocketConst.EMIT.PUBLIC_CARD, data_res)


# UNOコールを忘れていることを指摘
@sio.on(SocketConst.EMIT.POINTED_NOT_SAY_UNO)
def on_pointed_not_say_uno(data_res):
    receive_event(SocketConst.EMIT.POINTED_NOT_SAY_UNO, data_res)


# 対戦が終了
@sio.on(SocketConst.EMIT.FINISH_TURN)
def on_finish_turn(data_res):
    global id, game_status
    def finish_turn_callback(data_res):
        global id, game_status
        score = data_res.get("score")[id]
        if game_status.version == 'v2':
            games.scores[0] += score
        else:
            games.scores[1] += score
        game_status = Status()

    receive_event(SocketConst.EMIT.FINISH_TURN, data_res, finish_turn_callback)


# 試合が終了
@sio.on(SocketConst.EMIT.FINISH_GAME)
def on_finish_game(data_res):
    receive_event(SocketConst.EMIT.FINISH_GAME, data_res)


# ペナルティ発生
@sio.on(SocketConst.EMIT.PENALTY)
def on_penalty(data_res):
    global game_status
    def penalty_callback(data_res):
        global game_status

        # ペナルティによりカードを2枚引く
        game_status.draw_card(data_res.get('player'), penalty_draw=2)

        # print("ペナルティ発生", data_res)
        # カードが増えているのでUNO宣言の状態をリセットする
        if data_res.get('player') in game_status.uno_declared:
            del game_status.uno_declared[data_res.get('player')]

    receive_event(SocketConst.EMIT.PENALTY, data_res, penalty_callback)


def main():
    sio.connect(
        host,
        transports=['websocket'],
    )
    sio.wait()


if __name__ == '__main__':
    main()
