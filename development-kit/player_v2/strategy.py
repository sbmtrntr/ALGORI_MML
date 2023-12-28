from collections import defaultdict
import math


def select_play_card(my_cards: list, player_card_counts: dict, before_card: dict, status: dict, order_dic: dict, wild_shuffle_flag: bool, challenge_sucess: bool) -> dict:
    """
    出すカードを選出する

    Args:
        my_cards (list): 自分の手札
        player_card_counts: 他のプレイヤー(自分を除く)のカード枚数 
        before_card (dict): 場札のカード
        status: Card_Statusインスタンス
        order_dic: 順番
        wild_shuffle_flag: シャッフルワイルドを持ってるか
        challenge_sucess: 自分に対してチャレンジされたか否か
    Return:
        best_card(dict): 最善手
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

        # elif (
        #     (card_special and str(card_special) == str(before_card.get('special'))) or
        #     ((card_number is not None or (card_number is not None and int(card_number) == 0)) and (before_card.get('number') and int(card_number) == int(before_card.get('number'))))
        # ):
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
    if len(valid_card_list) > 0:
        for v in order_dic.values():
            if v["UNO"] == True: #UNO宣言してるやついたら
                tmp_list = defensive_card_choice(valid_card_list, v["位置"], status)
                return tmp_list[0]

        if analyze_situation(my_cards, player_card_counts, wild_shuffle_flag) == "deffensive": #防御モード
            tmp_list = deffesive_mode(valid_card_list, player_card_counts, challenge_sucess)
            if len(tmp_list) == 0:
                return None
            
            sort_pri_list = sorted(tmp_list, key=lambda x: (x[1][0], -x[1][1]))
            return sort_pri_list[0][0]

        elif analyze_situation(my_cards, player_card_counts, wild_shuffle_flag) == "offensive": #攻撃モード
            tmp_list = offensive_mode(valid_card_list, my_cards, player_card_counts, challenge_sucess)
            if len(tmp_list) == 0:
                return None
            else:
                return tmp_list[0]

    else:
        return None



def defensive_card_choice(valid_card_list: list, pos: str, status: dict) -> list:
    """
    負けそうな時に、失点を減らすことを優先するカードの出し方を選択する関数
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
        sorted_color = [item[0] for item in sorted(cnt_by_color.items(), key=lambda x: x[1])]  ##########
        print("多く出されている色の順は", sorted_color)

        # 色ごとに、場に見えている数字カードの数が大きい順に、手持ちの数字カードをソートする
        tmp_num_list = []
        for color in sorted_color:
            sorted_by_cnt = [item[0] for item in sorted(status[color].items(), key=lambda x: x[1])]  ###########
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


def offensive_mode(cards: list, my_card: list, player_cards_cnt: dict, challenge_sucess: bool) -> list:
    """
    攻撃モード
    cards :自分の中で出せるカード
    my_card :自分の手札の枚数
    player_cards_cnt :他の奴らの手札の枚数
    challenge_success :チャレンジを成功された過去があるか否か
    
    """
    ans_list = []
    for card in cards:#スキップ、リバースを優先的に出す
        card_special = card.get("special")
        if card_special == "skip" or card_special == "reverse":
            ans_list.append(card)
    
    for card in cards:#ドロー2はスキップ、リバースの次に優先的に出す
        card_special = card.get("special")
        if card_special == "draw_2":
            ans_list.append(card)
    
    num_lis = []
    color_order = my_color_cnt(cards)
    for card in cards: #3色をキープして戦う = 手札の中で最も多い色から消費する
        card_color = card["color"]
        #if card_color not in ["black","white"] and card.get("special") not in ["draw_2","skip","reverse"]:
        if card.get("number", False) != False:
            num_lis.append((card, color_order.index(card_color), card["number"]))
    
    num_lis_2 = [item[0] for item in sorted(num_lis, key=lambda x: (x[1], -x[2]))]
    ans_list += num_lis_2

    spe_lis = []

    for card in cards:# ワイルド系カードを1枚だけ残して、それで上がれるようにする
        if card.get("special") in ["wild", "white_wild", "wild_draw_4", "wild_shuffle"]:
            if card.get("special") == "wild_shuffle" and len(my_card) == 1: # シャッフルワイルドは手札1枚の時にしか出さない
                spe_lis.append((card, 4))
            
            else:
                if card.get("special") != "wild_shuffle": # ワイルド、白いワイルドの方を優先度高く出す
                    spe_lis.append((card, ["wild", "white_wild", "wild_draw_4"].index(card.get("special"))))
    
    spe_lis_2 = [item[0] for item in sorted(spe_lis, key=lambda x: x[1])]
    ans_list += spe_lis_2

    # 自分が最少手札保持者でシャッフルワイルドを持っており、それ以外に出せるものが無いとき、他プレイヤーとの差が4枚以上であれば、出さずに山札から引く
    if {'color': 'black', 'special': 'wild_shuffle'} in ans_list:
        if len(cards) > 1: #手持ちカードが1枚だけなら無視
            if len(cards) < min_cards_check(player_cards_cnt) and min_cards_check(player_cards_cnt) - len(cards) >= 4:
                print("wild_shuffleは出しません!!")
                ans_list.remove({'color': 'black', 'special': 'wild_shuffle'})
    
    #シャッフルワイルドとワイルドドロー4を持っているときは先にワイルドドロー4を出し、チャレンジ成功されたら次のターンでシャッフル
    if {'color': 'black', 'special': 'wild_draw_4'} in cards and {'color': 'black', 'special': 'wild_shuffle'} in cards and challenge_sucess == True:
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


def deffesive_mode(cards: list, player_cards_cnt: dict, challenge_sucess: bool) -> list:
    """
    防御モードの手札選択

    Args:
        card_dict(dict): 自分の手札のカードを格納した辞書型
    Returns:
        ans_list(list): 2次元配列(list in list), 要素 = [cardオブジェクト, (優先順位, cardの数字)]
    """
    ans_list = []
    for card in cards:
        if "special" in card.keys():
            card_special = card.get("special")
            if card_special == "wild_shuffle":
                #シャッフルワイルドを持っているときは3枚以下のプレイヤーが出たときに使う
                if min_cards_check(player_cards_cnt) <= 3: 
                    ans_list.append([card, (0, 1)])
                    # 自分が最少手札保持者でシャッフルワイルドを持っており、それ以外に出せるものが無いとき、他プレイヤーとの差が4枚以上であれば、出さずに山札から引く
                    # if len(cards) <  min_cards_check(player_cards_cnt) and min_cards_check(player_cards_cnt) - len(cards) >= 4:
                    #     continue
                    # else:
                    #     ans_list.append([card, (0, 1)])

            elif card_special == "white_wild":
                ans_list.append([card, (2, 1)])

            elif card_special == "wild_draw_4":
                if challenge_sucess == False: #直前のチャレンジ成功がなかったら
                    ans_list.append([card, (3, 1)])
                else: #あったら
                    ans_list.append([card, (9, 1)])

            elif card_special == "wild":
                ans_list.append([card, (1, 1)])

            elif card_special == "draw_2":
                ans_list.append([card, (4, 1)])

            elif card_special == "skip" or card_special == "reverse":
                ans_list.append([card, (5, 1)])

        elif "number" in card.keys():
            ans_list.append([card, (6, card.get("number"))])

    return ans_list


def challenge_dicision(card_before: dict, card_status: dict, my_id: int, before_id: int, other_cards: dict, cards_num: int, open_cards: dict):
    """
    チャレンジの判断関数
    args:
        before_card: dict = wild_draw_4前のカード
        card_status: dict = 見えてないカードの山の内容
        my_id: int = 自分のID
        before_id: int = 直前のプレイヤーのID
        other_cards: dict = 直前のプレイヤーが持つカードの枚数
        cards_num: int = 山札の枚数
        open_cards: dict = オープンされている手札のdict
    return:
        bool値 = チャレンジするか否か
    """

    # 相手が15枚以上持っているときは必ずチャレンジ
    if other_cards[before_id] >= 15: 
        return True
    
    # チャレンジ後開示された手札を記憶し、次ワイルドドロー4が出されたときに記憶した手札から場に出されたカードを消したものの中で出せるものがあれば必ずチャレンジ
    if len(open_cards[before_id]) > 0: # カードをオープンしてたら
        card_color = card_before.get("color") #wild_draw_4前のカードの色を取得
        for i in open_cards[before_id]: # オープンカードを片っ端からチェック
            if i.get("color") == card_color: # 同じ色あったら
                return True

    # 場札と自分の手札から相手が (同じ色を出せる確率) + (同じ数字・記号を出せる確率) + (ワイルド系カードを出せる確率) がp以上であればチャレンジ
    # 色が何枚残っているか確認
    card_color = card_before.get("color") 
    color_num = 0
    for i in card_status[card_color].values():
        color_num += i

    print("残っている色の枚数は" + str(color_num))
    
    # 他プレイヤーが何枚残っているか確認
    other_card_num = 0
    for id,num in other_cards.items():
        if id != my_id:
            other_card_num += num

    
    # 直前のプレイヤーが何枚残っているか確認
    other_card_num_2 = other_card_num - other_cards[before_id]

    print("x+y+zの枚数は" + str(other_card_num))
    print("y+zの枚数は" + str(color_num))

    #確率計算0.48
    p1 = 1 - (math.comb(cards_num + other_card_num_2, color_num) / math.comb(cards_num + other_card_num, color_num))

    wild_num = 0
    for k,i in card_status["black"].items():
        if k != "wild_draw_4":
            wild_num += i
    
    wild_num += card_status["white"]["white_wild"]

    print("ワイルドカードの枚数は" + str(wild_num))

    p2 = 1 - (math.comb(cards_num + other_card_num_2, wild_num) / math.comb(cards_num + other_card_num, wild_num))

    p = p1 + p2
    print(card_color +"を"+ before_id +"が持っている確率は :" + str(p))

    if p >= 0.75:
        return True
    else:
        return False



def pass_func(err)->None:
    """
    個別コールバックを指定しないときの代替関数
    """
    return

