from collections import defaultdict
import math

def select_play_card(my_cards: list, my_id: str, next_id, player_card_counts: dict, num_of_deck: int, before_card: dict, status: dict, order_dic: dict, wild_shuffle_flag: bool, challenge_success: bool, challenged_cnt: dict, num_game: int) -> dict:
    """
    出すカードを選出する

    Args:
        my_cards (list): 自分の手札
        player_card_counts: 他のプレイヤー(自分を除く)のカード枚数
        before_card (dict): 場札のカード
        status: Card_Statusインスタンス
        order_dic: 順番
        wild_shuffle_flag: シャッフルワイルドを持ってるか
        challenge_success: 自分に対してチャレンジ成功されたか
    Return:
        best_card(dict): 最善手
        play_mode(str): どのモードかを表す文字列{"offensive", "deffensive", "uno", "other"}
    """

    cards_valid = [] # 同じ色 または 同じ数字・記号 のカードを格納
    cards_wild = [] # ワイルド・シャッフルワイルド・白いワイルドを格納
    cards_wild4 = [] # ワイルドドロー4を格納

    # 場札と照らし合わせ出せるカードを抽出する
    for card in my_cards:
        card_special = card.get('special')
        card_number = card.get('number')
        before_card_number = before_card.get('number')
        if card_special == 'wild_draw_4': # ワイルドドロー4
            # ワイルドドロー4は場札に関係なく出せる
            cards_wild4.append(card)

        elif card_special in ['wild', 'wild_shuffle', 'white_wild']:
            # ワイルド・シャッフルワイルド・白いワイルドも場札に関係なく出せる
            cards_wild.append(card)

        elif card['color'] == before_card['color']:
            # 場札と同じ色のカード
            cards_valid.append(card)

        elif card_special is not None and card_special == before_card.get('special'):
            # 場札と記号が同じカード
            cards_valid.append(card)

        elif card_number is not None and before_card_number is not None and int(card_number) == int(before_card_number):
            # 場札と数字が同じカード
            cards_valid.append(card)

    """
    出せるカードのリストを結合し、先頭のカードを返却する。
    このプログラムでは優先順位を、「同じ色 または 同じ数字・記号」 > 「ワイルド・シャッフルワイルド・白いワイルド」 > ワイルドドロー4の順番とする。
    ワイルドドロー4は本来、手札に出せるカードが無い時に出していいカードであるため、一番優先順位を低くする。
    ワイルド・シャッフルワイルド・白いワイルドはいつでも出せるので、条件が揃わないと出せない「同じ色 または 同じ数字・記号」のカードより優先度を低くする。
    """
    valid_card_list = cards_valid + cards_wild + cards_wild4

    ######追加#######
    should_play_draw4 = play_draw4_dicision(valid_card_list, before_card, status, my_cards, my_id, next_id, player_card_counts, num_of_deck, challenge_success, challenged_cnt, num_game)
    print('should_play_draw4:', should_play_draw4)

    # UNOプレイヤーがいるとき
    # シャッフルワイルドを持っていて、自分の手札が7枚以上のとき --> シャッフルワイルドを切る
    shuffle_wild = {'color':'white', 'special':'wild_shuffle'}
    if len(my_cards) >= 7 and shuffle_wild in my_cards:
        return (shuffle_wild, "uno")

    if len(valid_card_list) > 0:
        for v in order_dic.values():
            if v["UNO"] == True: #UNO宣言してるやついたら
                tmp_list = card_choice_at_uno(valid_card_list, v["位置"], status)
                return (tmp_list[0], "uno")

        if analyze_situation(my_cards, player_card_counts, wild_shuffle_flag) == "deffensive": #防御モード
            tmp_list = deffesive_mode(valid_card_list, player_card_counts, challenge_success)
            if len(tmp_list) == 0:
                return (None, "deffensive")

            sort_pri_list = sorted(tmp_list, key=lambda x: (x[1][0], -x[1][1]))
            return (sort_pri_list[0][0], "deffensive")

        elif analyze_situation(my_cards, player_card_counts, wild_shuffle_flag) == "offensive": #攻撃モード
            tmp_list = offensive_mode(valid_card_list, my_cards, player_card_counts, challenge_success)
            if len(tmp_list) == 0:
                return (None, "offensive")
            else:
                return (tmp_list[0], "offensive")

    else:
        return (None, "other")


def card_choice_at_uno(valid_card_list: list, pos: str, status: dict) -> list:
    """
    UNO状態のプレイヤーがいるときに、どのカードを選択するか決める関数(失点を減らすように)
    カードの出し方は次を参照： https://github.com/sbmtrntr/ALGORI_MML/issues/11#issuecomment-1855121547
    Args:
        valid_card_list(list): 出すことのできるカードを格納するリスト
        pos(str): {"直前", "対面", "直後"}のいずれか

    Returns:
        rtn_list(list): 失点を減らすようにvalid_card_listをソートしたリスト
    """

    specials_dict = defaultdict(list)
    nums_dict = defaultdict(dict)

    print("pos is ", pos)

    if pos == "直後":
        # 有効カード情報を取得
        for card in valid_card_list:
            #スペシャルカードと数字カードを振り分け
            card_special = card.get('special')
            card_number = card.get('number')

            if card_number is None:
                specials_dict[card_special].append(card)
            else:
                card_color = card.get('color')
                nums_dict[card_color][card_number] = card

        print("特別カード")
        print(specials_dict)
        print("数字カード")
        print(nums_dict)

        # スペシャルカード(キー)を優先度順に格納したリスト
        specials_key_list = ['wild_shuffle', 'draw_2', 'wild', 'white_wild', 'reverse', 'skip', 'wild_draw_4']

        # 場に見えている色順を得る
        cnt_by_color = defaultdict(int)
        for color in ['red', 'blue', 'green', 'yellow']:
            cnt_by_color[color] = color_counting(color, status)
        sorted_color = [item[0] for item in sorted(cnt_by_color.items(), key=lambda x: x[1])]
        print("多く出されている色の順は", sorted_color)

        # 色ごとに、場に見えている数字カードの数が大きい順に、手持ちの数字カードをソートする
        tmp_num_list = []
        for color in sorted_color:
            sorted_by_cnt = [item[0] for item in sorted(status[color].items(), key=lambda x: x[1])]
            print("sorted_by_cnt")
            print(sorted_by_cnt)
            for key in sorted_by_cnt:
                if key not in ['draw_2', 'reverse', 'skip']:
                    key = int(key)
                    if key in nums_dict[color]:
                        tmp_num_list.append(nums_dict[color][key])
        print("tmp_num_list")
        print(tmp_num_list)

        # 返り値の作成
        rtn_list = []
        for key in specials_key_list:
            rtn_list += specials_dict.get(key, [])
        rtn_list += tmp_num_list

        # Remove (DEBUG)
        print('---出す順---')
        for card in rtn_list:
            card_number = card.get('number')
            if card_number:
                card_color = card.get('color')
                print(f'{card_color}の{card_number}', end=' ')
            else:
                card_special = card.get('special')
                print(card_special, end=' ')
        print(rtn_list)

        return rtn_list

    elif pos == "対面":
        # 有効カード情報を取得
        for card in valid_card_list:
            card_special = card.get('special')
            card_number = card.get('number')

            if card_number is None:
                specials_dict[card_special].append(card)
            else:
                nums_dict[card_number] = card

        # 数字カードの値が大きい順に数字カードをソートする
        tmp_num_list = [item[1] for item in sorted(nums_dict.items(), key=lambda x:int(x[0]), reverse=True)]
        print("tmp_num_list")
        print(tmp_num_list)

        # スペシャルカード(キー)を優先度順に格納したリスト
        specials_key_list = ['wild_shuffle', 'white_wild', 'wild', 'wild_draw_4', 'draw_2', 'reverse', 'skip']

        # 返り値の作成
        rtn_list = []
        for key in specials_key_list:
            # if specials_dict.get(key,False) != False:
            rtn_list += specials_dict.get(key, [])
        print("rtn_list_1 :")
        print(rtn_list)
        rtn_list += tmp_num_list

        # Remove (DEBUG)
        print('---出す順---')
        for card in rtn_list:
            card_number = card.get('number')
            if card_number is None:
                card_color = card.get('color')
                print(f'{card_color}の{card_number}', end=' ')
            else:
                card_special = card.get('special')
                print(card_special, end=' ')
        print(rtn_list)

        return rtn_list

    elif pos == "直前":
        # 有効カード情報を取得
        for card in valid_card_list:
            card_special = card.get('special')
            card_number = card.get('number')

            if card_number is None:
                specials_dict[card_special].append(card)
            else:
                nums_dict[card_number] = card

        # スペシャルカード(キー)を優先度順に格納したリスト　※Reverseはあとで別途で追加する
        specials_key_list = ['wild_shuffle', 'wild', 'wild_draw_4', 'draw_2', 'white_wild', 'skip']

        # 数字カードの値が大きい順に数字カードをソートする
        tmp_num_list = [item[1] for item in sorted(nums_dict.items(), key=lambda x:int(x[0]), reverse=True)]
        print("tmp_num_list")
        print(tmp_num_list)

        # 返り値の作成
        rtn_list = []
        for key in specials_key_list:
            # if specials_dict.get(key,False) != False:
            rtn_list += specials_dict.get(key, [])

        print("rtn_list_1 :")
        print(rtn_list)
        rtn_list += tmp_num_list
        print("rtn_list_2 :")
        print(rtn_list)
        rtn_list += specials_dict.get('reverse', [])

        # Remove (DEBUG)
        print('---出す順---')
        for card in rtn_list:
            card_number = card.get('number')
            if card_number:
                card_color = card.get('color')
                print(f'{card_color}の{card_number}', end=' ')
            else:
                card_special = card.get('special')
                print(card_special, end=' ')
        print(rtn_list)

        return rtn_list

    else:
        return valid_card_list


def analyze_situation(my_cards: list, player_card_counts: dict, wild_shuffle_flag: bool) -> str:
    """全体の手札の状況から戦況判断する関数"""

    min_cards_num = min_cards_check(player_card_counts)

    if min_cards_num < 5 or len(my_cards) < 5:#5枚未満の手札保持者がいる

        if len(my_cards) > min_cards_num: #自分が最少手札保持者でない
            if min_cards_num <= 2:
                return "deffensive"
            elif len(my_cards) - min_cards_num >= 4:
                return "deffensive"
            else:
                return "offensive"

        elif len(my_cards) <= min_cards_num: #自分と他の最小手札保持者の枚数以下
            return "offensive"

    else: #全員手札が5枚以上の場合
        if len(my_cards) >= min_cards_num*2:
            return "deffensive"
        else:
            return "offensive"


def min_cards_check(player_card_counts: dict):
    min_cards_num = 100
    for v in player_card_counts.values():
        min_cards_num = min(v, min_cards_num)

    return min_cards_num


def select_change_color(my_cards: list, card_status: dict) -> str:
    """
    変更する色を選出する

    Args:
        my_cards(list): 自分の手札
        card_status(dict): 場に出ていない札の数の状況

    Returns:
        str: 選択された色
    """
    print("change_card")
    color_dic = {'red':0, 'blue':0, 'green':0, 'yellow':0}
    select_color = 'red'

    for card in my_cards:
        card_color = card["color"]
        if card_color not in ["black","white"]:
            color_dic[card_color] += 1
            if color_dic[select_color] < color_dic[card_color]:
                select_color = card_color

            elif color_dic[select_color] == color_dic[card_color]:  # 最も多い色札の枚数が被ったら
                if color_counting(select_color, card_status) > color_counting(card_color,card_status):
                    select_color = card_color


    ans = sorted(color_dic.items(), key=lambda x:x[1], reverse=True)
    print(ans)
    return select_color


def color_counting(color: str, card_status: dict) -> int:
    """
    色を指定し、その色の場に出ていない札が何枚残っているか返す関数

    Args:
        color(str): 指定した色
        card_status(dict): 場に出ていない札を管理する変数

    Returns:
        int:何枚残っているか

    """
    card_nums = card_status[color]
    color_num = 0
    for v in card_nums.values():
        color_num += v

    return color_num


def offensive_mode(cards: list, my_card: list, player_cards_cnt: dict, challenge_success: bool) -> list:
    """
    攻撃モード
    cards :自分の中で出せるカード
    my_card :自分の手札の枚数
    player_cards_cnt :他の奴らの手札の枚数
    challenge_success :チャレンジを成功された過去があるか否か
    """
    ans_list = []
    for card in cards: #スキップ、リバースを優先的に出す
        card_special = card.get("special")
        if card_special == "skip" or card_special == "reverse":
            ans_list.append(card)

    for card in cards: #ドロー2はスキップ、リバースの次に優先的に出す
        card_special = card.get("special")
        if card_special == "draw_2":
            ans_list.append(card)

    num_lis = []
    color_order = my_color_cnt(cards)
    for card in cards: #3色をキープして戦う = 手札の中で最も多い色から消費する
        card_color = card["color"]
        #if card_color not in ["black","white"] and card.get("special") not in ["draw_2","skip","reverse"]:
        if card.get("number") is not None:
            num_lis.append((card, color_order.index(card_color), card["number"]))

    num_lis_2 = [item[0] for item in sorted(num_lis, key=lambda x: (x[1], -x[2]))]
    ans_list += num_lis_2

    spe_lis = []

    for card in cards: # ワイルド系カードを1枚だけ残して、それで上がれるようにする
        if card.get("special") in ["wild", "white_wild", "wild_draw_4", "wild_shuffle"]:
            if card.get("special") == "wild_shuffle" and len(my_card) == 1: # シャッフルワイルドは手札1枚の時にしか出さない
                spe_lis.append((card, 4))

            else:
                if card.get("special") != "wild_shuffle": # ワイルド、白いワイルドの方を優先度高く出す
                    spe_lis.append((card, ["wild", "white_wild", "wild_draw_4"].index(card.get("special"))))

    spe_lis_2 = [item[0] for item in sorted(spe_lis, key=lambda x: x[1])]
    ans_list += spe_lis_2

    # ---カードを出すか、ドローするかの処理---
    # カードを出す場合はカードリストを返す
    # カードを出さない場合はNoneを返す
    # 山札を引いて得たカードを出すかどうかは player_v3.pyで記述されている

    # ワイルド系カードを1枚だけ持っていてそれしか出せるカードが無いとき
    if len(spe_lis_2) == 1 and len(cards) == 1:
        # 残り手札が1枚の時は出してゲームをあがる
        if my_card == 1:
            return ans_list
        # 上記以外の場合はワイルド系カードを使わず山札を引く
        return []

    # ワイルド系カードを複数枚持っていてそれしか出せるカードが無いとき --> 出す
    elif len(spe_lis_2) > 1 and len(cards) == len(spe_lis_2):
        return ans_list

    # ワイルド系カードを持っておらず、出せるカードが無いとき
    elif len(spe_lis_2) == 0 and len(cards) == 0:
        # 山札からカードを引くのでNoneを返す
        return []


    # # 自分が最少手札保持者でシャッフルワイルドを持っており、それ以外に出せるものが無いとき、他プレイヤーとの差が4枚以上であれば、出さずに山札から引く
    # if {'color': 'black', 'special': 'wild_shuffle'} in ans_list:
    #     if len(cards) > 1: #手持ちカードが1枚だけなら無視
    #         if len(cards) < min_cards_check(player_cards_cnt) and min_cards_check(player_cards_cnt) - len(cards) >= 4:
    #             print("wild_shuffleは出しません!!")
    #             ans_list.remove({'color': 'black', 'special': 'wild_shuffle'})

    #シャッフルワイルドとワイルドドロー4を持っているときは先にワイルドドロー4を出し、チャレンジ成功されたら次のターンでシャッフル
    if {'color': 'black', 'special': 'wild_draw_4'} in cards and {'color': 'black', 'special': 'wild_shuffle'} in cards and challenge_success == True:
        return [{'color': 'black', 'special': 'wild_shuffle'}]
    else:
        print("出せるのは(offensive)")
        print(ans_list)
        return ans_list


def my_color_cnt(cards: dict) -> list:
    """
    手札から出すべき色の優先度を吐く。先頭に最も多い色が来る
    """

    color_dic = {'red':0, 'blue':0, 'green':0, 'yellow':0}
    for card in cards:
        card_color = card["color"]
        if card_color not in ["black","white"]:
            color_dic[card_color] += 1

    ans = sorted(color_dic.keys(), key=lambda x:x[1], reverse=True)
    return ans


def deffesive_mode(cards: list, my_card: int, player_cards_cnt: dict, challenge_sucess: bool, g_status:any) -> list:
    """
    防御モード
    cards :自分の中で出せるカード
    my_card :自分の手札の枚数
    player_cards_cnt :他の奴らの手札の枚数
    challenge_success :チャレンジを成功された過去があるか否か
    """
    print("---防御モード発動---")

    ans_list = []
    wild_lis = []
    non_wild_lis = []
    num_lis = []

    for card in cards: # ワイルドを優先的に出す
        card_special = card.get("special")
        if card_special == "wild":
            wild_lis.append(card)

    for card in cards: # 白いワイルドを優先的に出す
        card_special = card.get("special")
        if card_special == "white_wild":
            wild_lis.append(card)

    # チャレンジが成功された場合は, ワイルドドロー4の優先順位は最低になる
    # そうでなければこの優先順位でワイルドドロー4を出す
    if not challenge_sucess:
        for card in cards: # ワイルドドロー4を優先的に出す
            card_special = card.get("special")
            if card_special == "wild_draw_4":
                wild_lis.append(card)

    # 色優先順位の決定
    # プレイヤーの手札枚数が最も少ないプレイヤーを取得する
    # 同枚数のプレイヤーがいたらどうするのか？
    tgt_id = None
    cnt_min = 112
    for k, v in player_cards_cnt.items():
        if v < cnt_min:
            tgt_id = k
            cnt_min = v

    print("最もカード枚数が少ないプレイヤー", tgt_id)

    # game_statusインスタンスから, そのプレイヤーの色に関するゲーム記録を取得する
    # 指定したプレイヤーの色に関する記録があれば参照する
    if g_status.player_card_log[tgt_id]:
        last_chose_color = g_status.player_card_log[tgt_id][-1]

    # 記録が無い場合はcards_statusを参照して既知なカードのうち、
    # 最も場に出されている色順に結果を出力したい
    else:
        # TODO
        pass


    for card in cards: #ドロー2を優先的に出す
        card_special = card.get("special")
        if card_special == "draw_2":
            non_wild_lis.append(card)

    for card in cards: #スキップ・リバースを優先的に出す
        card_special = card.get("special")
        if card_special in ["skip", "reverse"]:
            non_wild_lis.append(card)

    # color_order = my_color_cnt(cards)
    for card in cards: #数字カードは大きい数を優先的に出す
        if card.get("number") is not None:
            num_lis.append((card, int(card["number"])))

    num_lis_2 = [item[0] for item in sorted(num_lis, key=lambda x: x[1], reverse=True)]

    # 答えのリストに追加する
    ans_list += wild_lis
    ans_list += non_wild_lis
    ans_list += num_lis_2

    # チャレンジが成功された場合は, ワイルドドロー4の優先順位は最低になる
    if challenge_sucess:
        for card in cards: # ワイルドドロー4を優先的に出す
            card_special = card.get("special")
            if card_special == "wild_draw_4":
                ans_list.append(card)

    # カードを出すか、ドローするか
    # ワイルド系カードを持っていてそれしか出せるカードが無い時
    if len(wild_lis) > 0 and len(wild_lis) == len(ans_list):
        # 残り手札が1枚の時は出してゲームをあがる
        if my_card == 1:
            return ans_list
        # 出せるカードがシャッフルワイルドのみの場合は出さずにカードを引く
        if len(wild_lis) == 1 and wild_lis[0].get("special") == "wild_shuffle":
            return []
        # それ以外の場合は出せるワイルド系カードを出す
        return ans_list
    
    # ワイルド系カードを持っておらず、出せるカードが無いとき
    elif len(wild_lis) == 0 and len(cards) == 0:
        # 山札からカードを引くのでNoneを返す
        return []

    # 上記以外の場合は通常通りにリストを返す
    return ans_list


def challenge_dicision(before_card: dict, card_status: dict, my_id: str, before_id: str, other_cards: dict, cards_num: int, open_cards: dict, challenge_cnt: dict, num_game: int):
    """
    チャレンジの判断関数
    args:
        before_card: dict = wild_draw_4前のカード
        card_status: dict = 見えてないカードの山の内容
        my_id: str = 自分のID
        before_id: str = 直前のプレイヤーのID
        other_cards: dict = プレイヤーが持つカードの枚数
        cards_num: int = 山札の枚数
        open_cards: dict = オープンされている手札のdict
        challenge_cnt: dict = チャレンジ成功率の管理
        num_game: int = 何試合目か
    return:
        bool値 = チャレンジするか否か
    """


    # チャレンジ後開示された手札を記憶し、次ワイルドドロー4が出されたときに記憶した手札から場に出されたカードを消したものの中で出せるものがあれば必ずチャレンジ
    if len(open_cards[before_id]) > 0: # カードをオープンしてたら
        card_color = before_card.get("color") #wild_draw_4前のカードの色を取得
        card_number = before_card.get("number")
        card_special = before_card.get("special")
        for card in open_cards[before_id]: # オープンカードを片っ端からチェック
            if card.get("color") == card_color: # 同じ色あったら
                print('記憶したカードでチャレンジ')
                return True
            elif card_number is not None and card_number == card.get("number"):
                print('記憶したカードでチャレンジ')
                return True
            elif card_special is not None and card_special == card.get("spacial"):
                print('記憶したカードでチャレンジ')
                return True
            elif card_color in {'black', 'white'} and card_special != 'wild_draw_4':
                print('記憶したカードでチャレンジ')
                return True


    # 200戦した後のチャレンジ成功率が30%以下のとき、チャレンジしない
    if num_game > 200 and challenge_cnt[before_id][0] != 0:
        p_success = challenge_cnt[before_id][1] / challenge_cnt[before_id][0]
        print(before_id, 'に対するチャレンジ成功率:', p_success)
        print('チャレンジ回数:', challenge_cnt[before_id][0], '成功回数:', challenge_cnt[before_id][1])
        if p_success <= 0.3:
            return False

    # 場札と自分の手札から相手が (同じ色を出せる確率) + (同じ数字・記号を出せる確率) + (ワイルド系カードを出せる確率) がp以上であればチャレンジ
    print(before_id)
    print(cards_num)

    # 色が何枚残っているか確認
    card_color = before_card.get("color")
    color_num = 0
    for i in card_status[card_color].values():
        color_num += i

    print("残っている色の枚数は" + str(color_num))

    # 他プレイヤーが何枚残っているか確認
    other_card_num = 0
    for id, num in other_cards.items():
        if id != my_id:
            other_card_num += num


    # 直前のプレイヤーが何枚残っているか確認
    x = other_cards[before_id]

    #見えていないワイルドカードの枚数を確認
    wild_num = 0
    for k, i in card_status["black"].items():
        if k != "wild_draw_4":
            wild_num += i

    wild_num += card_status["white"]["white_wild"]

    print("xの枚数は" + str(x))
    print("x+y+zの枚数は" + str(other_card_num))

    print("ワイルドカードの枚数は" + str(wild_num))

    #確率計算0.48
    p = 1 - (math.comb(cards_num + other_card_num - color_num - wild_num, x) / math.comb(cards_num + other_card_num, x))

    print("他の出せるカードを"+ before_id +"が持っている確率は :" + str(p))

    if not 0 <= p <= 1:
        exit(print("確率の壁を越えてるよ"))

    # 相手が6枚以上持っているとき
    if other_cards[before_id] >= 6:
        return p >= 0.5 # 相手が出せるカードを持っている確率が50%以上のときチャレンジ
    # 相手が6枚未満の時
    else:
        return p >= 0.8 # 相手が出せるカードを持っている確率が80%以上のときチャレンジ



def play_draw4_dicision(valid_card_list: list, before_card: dict, card_status: dict, my_cards: list, my_id: str, next_id: str, other_cards: dict, cards_num: int, challenge_success: bool, challenged_cnt: dict, num_game: int):
    """
    チャレンジの判断関数
    args:
        valid_card_list: list = 出せるカード
        before_card: dict = 前のカード
        card_status: dict = 見えてないカードの山の内容
        my_cards: list = 自分の手札
        my_id: str = 自分のID
        next_id: str = 直後のプレイヤーのID
        other_cards: dict = プレイヤーが持つカードの枚数
        cards_num: int = 山札の枚数
        challenge_success: 自分に対してチャレンジ成功されたか
        challenged_cnt: dict = チャレンジ成功数
    return:
        bool値 = チャレンジするか否か
    """

    # 他に出せるカードがないとき必ず出す
    for card in valid_card_list:
        if card != {"special": "wild_draw_4", "color": "black"}:
            break
    else:
        return True

    if challenge_success:
        return False

    if num_game > 200 and challenged_cnt[next_id][0] != 0:
        p_challenge = challenged_cnt[next_id][1] / challenged_cnt[next_id][0]
        print(next_id, 'のチャレンジ率:', p_challenge)
        print('ドロ4出した回数:', challenged_cnt[next_id][0], 'チャレンジ回数:', challenged_cnt[next_id][1])
        if p_challenge >= 0.9: # 200戦した後、自分がドロー4出したときの相手のチャレンジ率が90%以上のとき、出さない
            return False
        elif p_challenge <= 0.05: # 200戦した後、自分がドロー4出したときの相手のチャレンジ率が5%以下のとき、出す
            return True

    if num_game > 200 and challenged_cnt[next_id][1] != 0:
        p_success = challenged_cnt[next_id][2] / challenged_cnt[next_id][1]
        print(next_id, 'のチャレンジ成功率:', p_success)
        print('チャレンジ回数:', challenged_cnt[next_id][1], '成功回数:', challenged_cnt[next_id][2])
        if p_success >= 0.8: # 200戦した後の被チャレンジ成功率が 80%以上のとき、出さない
            return False



    print(next_id)
    print(cards_num)

    # 色が何枚残っているか確認
    card_color = before_card.get("color")
    color_num = 0
    for i in card_status[card_color].values():
        color_num += i


    # 他プレイヤーが何枚残っているか確認
    other_card_num = 0
    for id, num in other_cards.items():
        if id != next_id:
            other_card_num += num
        else:
            other_card_num += num // 2


    # 自分が何枚残っているか確認
    w = other_cards[my_id]

    # 見えていないワイルドカードの枚数を確認
    wild_num = 0
    for k, i in card_status["black"].items():
        if k != "wild_draw_4":
            wild_num += i

    wild_num += card_status["white"]["white_wild"]

    for card in my_cards:
        if card.get("color") == card_color:
            color_num += 1
        elif card.get("color") in {"black", "white"} and card.get("special") != "wild_draw_4":
            wild_num += 1


    print("wの枚数は" + str(w))
    print("x+y+wの枚数は" + str(other_card_num))

    print("残っている色の枚数は" + str(color_num))
    print("ワイルドカードの枚数は" + str(wild_num))

    #確率計算
    p = 1 - (math.comb(cards_num + other_card_num - color_num - wild_num, w) / math.comb(cards_num + other_card_num, w))

    print("他の出せるカードを"+ my_id +"が持っている確率は :" + str(p))

    # 相手が6枚以上持っているとき
    if other_cards[my_id] >= 6:
        return p < 0.5 # 自分が出せるカードを持っている確率が50%以上のとき出さない
    # 相手が6枚未満の時
    else:
        return p < 0.8 # 自分が出せるカードを持っている確率が80%以上のとき出さない



def pass_func(err)->None:
    """
    個別コールバックを指定しないときの代替関数
    """
    return
