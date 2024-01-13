from collections import defaultdict
import math

def select_play_card(my_cards: list, my_id: str, next_id: str, player_card_counts: dict, num_of_deck: int, before_card: dict, game_status: any, games: any) -> dict:
    """
    出すカードを選出する

    Args:
        my_cards (list): 自分の手札
        my_id: 自分のid
        next_id: 次のプレイヤーのid
        player_card_counts: プレイヤーのカード枚数
        num_of_deck: 山札の枚数
        before_card (dict): 場札のカード
        game_status: Statusインスタンス
        games: Gamesインスタンス
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
    wild_shuffle_flag = game_status.wild_shuffle_flag()
    challenge_success = game_status.challenge_success.get(next_id, False)
    should_play_draw4 = play_draw4_dicision(valid_card_list, before_card, my_cards, my_id, next_id, player_card_counts, num_of_deck, challenge_success, game_status, games)
    print('should_play_draw4:', should_play_draw4)

    shuffle_wild = {'color':'black', 'special':'wild_shuffle'}
    # if len(my_cards) >= 7 and shuffle_wild in my_cards:
    #     return (shuffle_wild, "uno")

    play_mode = analyze_situation(my_id, my_cards, player_card_counts, wild_shuffle_flag)
    if len(valid_card_list) > 0:
        # UNOプレイヤーがいるとき
        if play_mode == "uno":
            # シャッフルワイルドを持っていて、自分の手札が7枚以上のとき --> シャッフルワイルドを切る
            if len(my_cards) >= 7 and wild_shuffle_flag:
                game_status.special_logic_flag[1] = True
                return (shuffle_wild, play_mode)

            uno_cnt = uno_player_cnt(game_status.order_dic)
            if uno_cnt == 3: #自分以外の3人がUNO
                tmp_list = card_choice_at_uno_all(valid_card_list, next_id, should_play_draw4, game_status)
                return (tmp_list[0], play_mode)

            elif uno_cnt == 2: #自分以外の2人がUNO
                tmp_list = card_choice_at_uno_two(valid_card_list, should_play_draw4, game_status)
                return (tmp_list[0], play_mode)

            for v in game_status.order_dic.values():
                if v["UNO"]: #UNO宣言してるやついたら
                    tmp_list = card_choice_at_uno(valid_card_list, v["位置"], should_play_draw4, game_status)
                    return (tmp_list[0], play_mode)

        elif play_mode == "deffensive": #防御モード
            tmp_list = deffesive_mode(my_id, valid_card_list, player_card_counts, wild_shuffle_flag, challenge_success, should_play_draw4, game_status)
            if len(tmp_list) == 0:
                return (None, play_mode)
            else:
                return (tmp_list[0], play_mode)

        elif play_mode == "offensive": #攻撃モード
            tmp_list = offensive_mode(valid_card_list, my_cards, challenge_success, game_status)
            if len(tmp_list) == 0:
                return (None, play_mode)
            else:
                return (tmp_list[0], play_mode)

        else:
            print('謎モード:', play_mode)
            return (valid_card_list[0], play_mode)

    else:
        return (None, play_mode)


def card_choice_at_uno_all(valid_card_list: list, next_id: str, should_play_draw4: bool, game_status: any) -> list:
    """
    他のプレイヤー3人全員がウノを出していた場合のカード選択
    ▫ ワイルド> シャッフルワイルド> 白いワイルド>ドロ2 > Skip > reverse > ドロ4 > 直後の人が出せない色・数字大
    ▫ ワイルド系の色選択は防衛モードの優先順位で直後の人を基準にする
    """

    specials_dict = defaultdict(list)
    # nums_dict = defaultdict(dict)
    nums_list = []

    # 有効カード情報を取得
    for card in valid_card_list:
        #スペシャルカードと数字カードを振り分け
        card_special = card.get('special')
        card_number = card.get('number')

        if card_number is None:
            specials_dict[card_special].append(card)
        else:
            nums_list.append(card)
            # card_color = card.get('color')
            # nums_dict[card_color][card_number] = card

    # スペシャルカード(キー)を優先度順に格納したリスト
    if should_play_draw4:
        specials_key_list = ['wild', 'wild_shuffle', 'white_wild', 'draw_2', 'reverse', 'skip', 'wild_draw_4']
    else:
        specials_key_list = ['wild', 'wild_shuffle', 'white_wild', 'draw_2', 'reverse', 'skip']

    # # 返り値の作成
    # rtn_list = []
    # #スペカードを優先度順に並べる
    # for key in specials_key_list:
    #     rtn_list += specials_dict.get(key, [])

    # #数字カードの色優先度を得る
    # color_lis = deffesive_color_order(next_id, game_status)

    # # #色の優先度に基づき数字カードを並べ替える
    # # for color in color_lis:
    # #     #数字カードは現在{色:{数字:{カードの中身(dict)}, 数字:{カードの中身(dict)}.....}}という形で扱われている
    # #     if color in nums_dict:
    # #         tmp_normal_color_lis = nums_dict[color]
    # #         tmp_normal_color_lis = [item[1] for item in sorted(tmp_normal_color_lis.items(), reverse=True)]
    # #         rtn_list += tmp_normal_color_lis

    # color_lis.reverse()
    # nums_list = sorted(nums_list, key=lambda x: (x["number"], color_lis.index(x["color"])), reverse=True)
    # rtn_list += nums_list

    rtn_list = get_two_uno_card_order(specials_dict, nums_list, specials_key_list, next_id, game_status)

    if not should_play_draw4:
        rtn_list += specials_dict.get('wild_draw_4', [])

    return rtn_list


def card_choice_at_uno_two(valid_card_list: list, should_play_draw4: bool, game_status: any) -> list:
    """
    二人がUNO宣言していた場合。
    """

    specials_dict = defaultdict(list)
    nums_dict = defaultdict(dict)
    nums_list = []

    # 有効カード情報を取得
    for card in valid_card_list:
        #スペシャルカードと数字カードを振り分け
        card_special = card.get('special')
        card_number = card.get('number')

        if card_number is None:
            specials_dict[card_special].append(card)
        else:
            nums_list.append(card)
            card_color = card.get('color')
            nums_dict[card_color][card_number] = card

    rtn_list = []

    #直前、対面がUNOってた時
    if get_uno_player_pos(game_status.order_dic) == ["直前","対面"] or get_uno_player_pos(game_status.order_dic) == ["対面","直前"] :
        # スペシャルカード(キー)を優先度順に格納したリスト
        if should_play_draw4:
            specials_key_list = ['wild_shuffle', 'wild', 'white_wild', 'wild_draw_4', 'draw_2', 'reverse', 'skip']
        else:
            specials_key_list = ['wild_shuffle', 'wild', 'white_wild', 'draw_2', 'reverse', 'skip']
        #考慮すべき相手(対面)のidを入手する
        target_id = game_status.get_mid_id()
        rtn_list = get_two_uno_card_order(specials_dict, nums_list, specials_key_list, target_id, game_status)
        if not should_play_draw4:
            rtn_list += specials_dict.get('wild_draw_4', [])

    #直後、対面がUNOってた時
    elif get_uno_player_pos(game_status.order_dic) == ["直後","対面"] or get_uno_player_pos(game_status.order_dic) == ["対面", "直後"]:
        # スペシャルカード(キー)を優先度順に格納したリスト
        if should_play_draw4:
            specials_key_list = ['white_wild', 'wild_shuffle', 'wild', 'wild_draw_4', 'draw_2', 'reverse', 'skip']
        else:
            specials_key_list = ['white_wild', 'wild_shuffle', 'wild', 'draw_2', 'reverse', 'skip']
        #考慮すべき相手(対面)のidを入手する
        target_id = game_status.get_next_id()
        rtn_list = get_two_uno_card_order(specials_dict, nums_list, specials_key_list, target_id, game_status)
        if not should_play_draw4:
            rtn_list += specials_dict.get('wild_draw_4', [])

    #直後,直前がUNOってた時
    elif get_uno_player_pos(game_status.order_dic) == ["直後","直前"] or get_uno_player_pos(game_status.order_dic) == ["直前","直後"]:

        #考慮すべき相手(直後)のidを入手する
        target_id = game_status.get_next_id()
        #もし直後のやつが手札公開していて、その手札公開した札の中でまだ使用していない札があれば
        if len(game_status.other_open_cards[target_id]) > 0: #特殊処理が走る
            # スペシャルカード(キー)を優先度順に格納したリスト
            if should_play_draw4:
                specials_key_list = [ 'wild_shuffle', 'wild', 'draw_2', 'wild_draw_4', 'skip']
            else:
                specials_key_list = [ 'wild_shuffle', 'wild', 'draw_2', 'skip']
            # 返り値の作成
            rtn_list = []
            #スペカードを優先度順に並べる
            for key in specials_key_list:
                rtn_list += specials_dict.get(key, [])

            # #直後の人が持っていない色を認識
            # color_candidate = ["red","blue","green","yellow"]
            # for i in game_status.other_open_cards[target_id]:
            #     if i["color"] in color_candidate:
            #         color_candidate.remove(i["color"])

            # #直後の人が持っていない数字を取得
            # number_candidate = ["0","1","2","3","4","5","6","7","8","9"]
            # for i in game_status.other_open_cards[target_id]:
            #     if i.get("number","-1") in number_candidate:
            #         number_candidate.remove(i["number"])

            # #直後の人が持っていない色＆数字を満たす札をtmp_num_rtn_listに入れる
            # tmp_num_rtn_lis = []
            # for color in color_candidate:
            #     if color in nums_dict:
            #         #直後のやつが持っていない色の札を集める
            #         tmp_normal_color_dic = nums_dict[color]
            #         for num, card in tmp_normal_color_dic.items():
            #             if num in number_candidate:
            #                 tmp_num_rtn_lis.append(card)

            # rtn_list += tmp_num_rtn_lis
            rtn_list += target_dont_have_num_color(game_status.other_open_cards[target_id], nums_dict)

            #白いワイルドを手札に加える
            rtn_list += specials_dict.get('white_wild', [])

            #reverseを手札に加える
            rtn_list += specials_dict.get('reverse', [])

            # #数字大の順に並べて入れる。直後の人が持っていない色＆数字を満たす札と重複しても特に問題ないので強引にやる
            # tmp_num_order_lis = []
            # #数字カードを並べ替える
            # for color in ["blue" ,"green", "red", "yellow"]:
            #     #数字カードは現在{色:{数字:{カードの中身(dict)}, 数字:{カードの中身(dict)}.....}}という形で扱われている
            #     if color in nums_dict:
            #         tmp_normal_color_dic = nums_dict[color]
            #         tmp_normal_color_lis = [sorted(tmp_normal_color_dic.items(), reverse=True)]
            #         tmp_num_order_lis += tmp_normal_color_lis

            # rtn_list += [item[1] for item in sorted(tmp_num_order_lis, reverse=True)]
            rtn_list += get_big_number_order_lis(nums_dict)

        else: #直後のやつに対するヒントが何もなければ
            # スペシャルカード(キー)を優先度順に格納したリスト
            if should_play_draw4:
                specials_key_list = [ 'wild_shuffle', 'wild', 'draw_2', 'wild_draw_4', 'skip', 'white_wild', 'reverse']
            else:
                specials_key_list = [ 'wild_shuffle', 'wild', 'draw_2', 'skip', 'white_wild', 'reverse']
            rtn_list = get_two_uno_card_order(specials_dict, nums_list, specials_key_list, target_id, game_status)

        if not should_play_draw4:
            rtn_list += specials_dict.get('wild_draw_4', [])

    else:
        print("Emergency: Cannot get correct uno situation(two)")
        rtn_list = valid_card_list

    return rtn_list


def card_choice_at_uno(valid_card_list: list, pos: str, should_play_draw4: bool, game_status: any) -> list:
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


    print("pos is ", pos)

    if pos == "直後":
        #考慮すべき相手(直後)のidを入手する
        target_id = game_status.get_next_id()

        rtn_list = []

        #もし直後のやつが手札公開していて、その手札公開した札の中でまだ使用していない札があれば
        if len(game_status.other_open_cards[target_id]) > 0: #特殊処理が走る
            rtn_list += specials_dict.get('draw_2', [])
            rtn_list += specials_dict.get('skip', [])

            #直後のやつが持っていない札を入れる
            rtn_list += target_dont_have_num_color(game_status.other_open_cards[target_id], nums_dict)

            rtn_list += specials_dict.get('wild', [])
            rtn_list += specials_dict.get('white_wild', [])
            rtn_list += specials_dict.get('wild_shuffle', [])
            if should_play_draw4:
                rtn_list += specials_dict.get('wild_draw_4', [])
            rtn_list += specials_dict.get('reverse', [])

            #数字の大きい順に入れる。直後のやつが持っていない札と被るが気にしない
            rtn_list += get_big_number_order_lis(nums_dict)

            if not should_play_draw4:
                rtn_list += specials_dict.get('wild_draw_4', [])

        else:
            # スペシャルカード(キー)を優先度順に格納したリスト
            if should_play_draw4:
                specials_key_list = [ 'draw_2', 'skip', 'white_wild', 'wild_shuffle', 'wild', 'wild_draw_4', 'reverse']
            else:
                specials_key_list = [ 'draw_2', 'skip', 'white_wild', 'wild_shuffle', 'wild', 'reverse']
            rtn_list = get_one_uno_card_order(specials_dict, nums_dict, specials_key_list, target_id, game_status)
            if not should_play_draw4:
                rtn_list += specials_dict.get('wild_draw_4', [])

        return rtn_list

    elif pos == "対面":
        # 考慮すべき相手(対面)のidを入手する
        target_id = game_status.get_mid_id()

        rtn_list = []
        # スペシャルカード(キー)を優先度順に格納したリスト
        if should_play_draw4:
            specials_key_list = [ 'white_wild', 'wild_shuffle', 'wild', 'wild_draw_4', 'reverse', 'draw_2']
        else:
            specials_key_list = [ 'white_wild', 'wild_shuffle', 'wild', 'reverse', 'draw_2']
        rtn_list = get_one_uno_card_order(specials_dict, nums_dict, specials_key_list, target_id, game_status)
        rtn_list += specials_dict.get('skip', [])
        if not should_play_draw4:
            rtn_list += specials_dict.get('wild_draw_4', [])

        return rtn_list

    elif pos == "直前":
        # 考慮すべき相手(直前)のidを入手する
        target_id = game_status.get_before_id()
        rtn_list = []

        #もし直前のやつが手札公開していて、その手札公開した札の中でまだ使用していない札があれば
        if len(game_status.other_open_cards[target_id]) > 0: #特殊処理が走る
            if should_play_draw4:
                specials_key_list = [ 'white_wild', 'wild_shuffle', 'wild', 'wild_draw_4', 'draw_2' ,'skip']
            else:
                specials_key_list = [ 'white_wild', 'wild_shuffle', 'wild', 'draw_2' ,'skip']
            #スペカードを優先度順に並べる
            for key in specials_key_list:
                rtn_list += specials_dict.get(key, [])

            #直前のやつが持っていない札を入れる
            rtn_list += target_dont_have_num_color(game_status.other_open_cards[target_id], nums_dict)

            #数字の大きい順に入れる。直前のやつが持っていない札と被るが気にしない
            rtn_list += get_big_number_order_lis(nums_dict)

            rtn_list += specials_dict.get('reverse', [])

            if not should_play_draw4:
                rtn_list += specials_dict.get('wild_draw_4', [])

        else:
            if should_play_draw4:
                specials_key_list = [ 'wild_shuffle', 'wild', 'wild_draw_4', 'draw_2' ,'skip' ,'white_wild']
            else:
                specials_key_list = [ 'wild_shuffle', 'wild', 'draw_2' ,'skip' ,'white_wild']
            rtn_list = get_one_uno_card_order(specials_dict, nums_dict, specials_key_list, target_id, game_status)
            rtn_list += specials_dict.get('reverse', [])
            if not should_play_draw4:
                rtn_list += specials_dict.get('wild_draw_4', [])

        return rtn_list

    else:
        return valid_card_list



def uno_player_cnt(order_dic: dict):
    uno_cnt = 0
    for i in order_dic.values():
        if i["UNO"]:
            uno_cnt += 1

    return uno_cnt


def get_uno_player_pos(order_dic: dict):
    uno_pos_lis = []
    for i in order_dic.values():
        if i["UNO"]:
            uno_pos_lis.append(i["位置"])

    return uno_pos_lis


def get_one_uno_card_order(specials_dict: dict, nums_dict: dict, specials_pri_list: list, target_id: str, game_status: any) -> list:
    # 返り値の作成
    rtn_list = []
    #スペカードを優先度順に並べる
    for key in specials_pri_list:
        rtn_list += specials_dict.get(key, [])

    #数字カードの色優先度を得る
    color_lis = deffesive_color_order(target_id, game_status)

    #色の優先度に基づき数字カードを並べ替える
    for color in color_lis:
        #数字カードは現在{色:{数字:{カードの中身(dict)}, 数字:{カードの中身(dict)}.....}}という形で扱われている
        if color in nums_dict:
            tmp_normal_color_dic = nums_dict[color]
            tmp_normal_color_lis = [item[1] for item in sorted(tmp_normal_color_dic.items(), reverse=True)]
            rtn_list += tmp_normal_color_lis

    return rtn_list


def get_two_uno_card_order(specials_dict: dict, nums_list: list, specials_pri_list: list, target_id: str, game_status: any) -> list:
    # 返り値の作成
    rtn_list = []
    #スペカードを優先度順に並べる
    for key in specials_pri_list:
        rtn_list += specials_dict.get(key, [])

    #数字カードの色優先度を得る
    color_lis = deffesive_color_order(target_id, game_status)

    color_lis.reverse()
    nums_list = sorted(nums_list, key=lambda x: (x["number"], color_lis.index(x["color"])), reverse=True)
    rtn_list += nums_list

    return rtn_list


def target_dont_have_num_color(open_cards: list, nums_dict: dict):
    #特定のプレイヤーが持っていないはずの色・数字を返す
    #直後の人が持っていない色を認識
    color_candidate = ["red","blue","green","yellow"]
    for i in open_cards:
        if i["color"] in color_candidate:
            color_candidate.remove(i["color"])

    #直後の人が持っていない数字を取得
    number_candidate = ["9","8","7","6","5","4","3","2","1","0"]
    for i in open_cards:
        if i.get("number","-1") in number_candidate:
            number_candidate.remove(i["number"])

    #直後の人が持っていない色＆数字を満たす札をtmp_num_rtn_listに入れる
    tmp_num_rtn_lis = []
    for color in color_candidate:
        if color in nums_dict:
            #直後のやつが持っていない色の札を集める
            tmp_normal_color_dic = nums_dict[color]
            for num, card in tmp_normal_color_dic.items():
                if num in number_candidate:
                    tmp_num_rtn_lis.append(card)

    return tmp_num_rtn_lis


def get_big_number_order_lis(nums_dict):
    tmp_num_order_lis = []
    #数字カードを並べ替える
    for color in ["blue" ,"green", "red", "yellow"]:
        #数字カードは現在{色:{数字:{カードの中身(dict)}, 数字:{カードの中身(dict)}.....}}という形で扱われている
        if color in nums_dict:
            tmp_normal_color_dic = nums_dict[color]
            tmp_normal_color_lis = [sorted(tmp_normal_color_dic.items(), reverse=True)]
            tmp_num_order_lis += tmp_normal_color_lis

    return [item[1] for item in sorted(tmp_num_order_lis, reverse=True)]




def analyze_situation(my_id: str, my_cards: list, player_card_counts: dict, wild_shuffle_flag: bool) -> str:
    """
    全体の手札の状況から戦況判断する関数
    Args:
        my_id: 自分のid
        my_cards(list): 自分の手札
        player_card_counts: プレイヤーのカード枚数
        wild_shuffle_flag: シャッフルワイルド持ってるか

    Returns:
        str: モード
    """

    num_my_cards = len(my_cards) - 1 if wild_shuffle_flag else len(my_cards)
    min_cards_num = min_cards_check(my_id, player_card_counts)

    if min_cards_num == 1:
        return "uno"

    elif num_my_cards < 5: # 自分が4枚以下
        return "offensive"

    elif min_cards_num < 5: # 4枚以下のプレイヤーがいる
        if num_my_cards - min_cards_num < 5: # 最少手札との差が5枚未満
            if min_cards_num == 2: # 2枚のプレイヤーがいる
                return "deffensive"
            else:
                return "offensive"

        else:
            if min_cards_num <= 3: # 3枚以下のプレイヤーがいる
                return "deffensive"
            else:
                if num_my_cards - min_cards_num >= 10: # 最少手札との差が10枚以上
                    return "deffensive"
                else:
                    return "offensive"

    else:
        return "offensive"


    # if min_cards_num < 5 or len(my_cards) < 5:#5枚未満の手札保持者がいる

    #     if len(my_cards) > min_cards_num: #自分が最少手札保持者でない
    #         if min_cards_num <= 2:
    #             return "deffensive"
    #         elif len(my_cards) - min_cards_num >= 4:
    #             return "deffensive"
    #         else:
    #             return "offensive"

    #     elif len(my_cards) <= min_cards_num: #自分と他の最小手札保持者の枚数以下
    #         return "offensive"

    # else: #全員手札が5枚以上の場合
    #     if len(my_cards) >= min_cards_num*2:
    #         return "deffensive"
    #     else:
    #         return "offensive"


def min_cards_check(my_id: str, player_card_counts: dict):
    min_cards_num = 112
    for k, v in player_card_counts.items():
        if k != my_id:
            min_cards_num = min(v, min_cards_num)

    return min_cards_num


def select_change_color(my_cards: list, g_status: any, mode: str="offensive", target_id: str=None) -> str:
    """
    変更する色を選出する

    Args:
        my_cards(list): 自分の手札
        g_status: Statusインスタンス
        mode: モード
        target_id: 基準とするプレイヤー

    Returns:
        str: 選択された色
    """
    print("change_card")
    if mode == "offensive":
        color_list = offensive_color_order(my_cards, g_status.cards_status)
    else:
        if target_id is None:
            target_id = g_status.get_next_id()
        color_list = deffesive_color_order(target_id, g_status)

    select_color = color_list[0]

    # color_dic = {'red':0, 'blue':0, 'green':0, 'yellow':0}
    # select_color = 'red'

    # for card in my_cards:
    #     card_color = card["color"]
    #     if card_color not in ["black","white"]:
    #         color_dic[card_color] += 1
    #         if color_dic[select_color] < color_dic[card_color]:
    #             select_color = card_color

    #         elif color_dic[select_color] == color_dic[card_color]:  # 最も多い色札の枚数が被ったら
    #             if color_counting(select_color, card_status) > color_counting(card_color,card_status):
    #                 select_color = card_color


    # ans = sorted(color_dic.items(), key=lambda x:x[1], reverse=True)
    # print(ans)
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


def offensive_mode(cards: list, my_card: list, challenge_success: bool, g_status: any) -> list:
    """
    攻撃モード
    cards :自分の中で出せるカード
    my_card :自分の手札
    challenge_success :チャレンジを成功された過去があるか否か
    g_status: Statusインスタンス
    """
    shuffle_wild = {'color':'black', 'special':'wild_shuffle'}
    wild_draw_4 = {'color':'black', 'special':'wild_draw_4'}
    ans_list = []
    skip_reverse_lis = []
    draw_2_lis = []
    num_lis = []
    wild_lis = []
    color_order = offensive_color_order(cards, g_status.cards_status)

    for card in cards: #スキップ、リバースを優先的に出す
        card_special = card.get("special")
        if card_special == "skip" or card_special == "reverse":
            skip_reverse_lis.append(card)
    skip_reverse_lis = sorted(skip_reverse_lis, key=lambda x: color_order.index(x["color"]))

    for card in cards: #ドロー2はスキップ、リバースの次に優先的に出す
        card_special = card.get("special")
        if card_special == "draw_2":
            draw_2_lis.append(card)
    draw_2_lis = sorted(draw_2_lis, key=lambda x: color_order.index(x["color"]))

    for card in cards: #3色をキープして戦う = 手札の中で最も多い色から消費する
        # card_color = card["color"]
        #if card_color not in ["black","white"] and card.get("special") not in ["draw_2","skip","reverse"]:
        if card.get("number") is not None:
            num_lis.append(card)
            # num_lis.append((card, color_order.index(card_color), card["number"]))

    num_lis_2 = sorted(num_lis, key=lambda x: color_order.index(x["color"]))
    # num_lis_2 = [item[0] for item in sorted(num_lis, key=lambda x: (x[1], -x[2]))]
    # ans_list += num_lis_2

    wild_order = ["wild", "white_wild", "wild_draw_4", "wild_shuffle"]
    for card in cards: # ワイルド系カードを1枚だけ残して、それで上がれるようにする
        card_special = card.get("special")
        if card_special in wild_order:
            wild_lis.append(card)
            # if card_special == "wild_shuffle" and len(my_card) == 1: # シャッフルワイルドは手札1枚の時にしか出さない
            #     wild_lis.append((card, 4))

            # else:
            #     if card_special != "wild_shuffle": # ワイルド、白いワイルドの方を優先度高く出す
            #         wild_lis.append((card, ["wild", "white_wild", "wild_draw_4"].index(card_special)))

    wild_lis_2 = sorted(wild_lis, key=lambda x: wild_order.index(x["special"]))
    # wild_lis_2 = [item[0] for item in sorted(wild_lis, key=lambda x: x[1])]
    # ans_list += wild_lis_2

    # 答えのリストに追加する
    ans_list += skip_reverse_lis
    ans_list += draw_2_lis
    ans_list += num_lis_2
    ans_list += wild_lis_2

    # ---カードを出すか、ドローするかの処理---
    # カードを出す場合はカードリストを返す
    # カードを出さない場合はNoneを返す
    # 山札を引いて得たカードを出すかどうかは player_v3.pyで記述されている

    # 残り手札が1枚の時は出してゲームをあがる
    if len(my_card) == 1:
        return cards

    # ワイルド系カードを1枚だけ持っていてそれしか出せるカードが無いとき
    if len(wild_lis_2) == 1 and len(cards) == 1:
        # 上記以外の場合はワイルド系カードを使わず山札を引く
        return []

    # ワイルド系カードを複数枚持っていてそれしか出せるカードが無いとき --> 出す
    elif len(wild_lis_2) > 1 and len(cards) == len(wild_lis_2):
        return ans_list

    # ワイルド系カードを持っておらず、出せるカードが無いとき
    elif len(wild_lis_2) == 0 and len(cards) == 0:
        # 山札からカードを引くのでNoneを返す
        return []


    # # 自分が最少手札保持者でシャッフルワイルドを持っており、それ以外に出せるものが無いとき、他プレイヤーとの差が4枚以上であれば、出さずに山札から引く
    # if {'color': 'black', 'special': 'wild_shuffle'} in ans_list:
    #     if len(cards) > 1: #手持ちカードが1枚だけなら無視
    #         if len(cards) < min_cards_check(player_cards_cnt) and min_cards_check(player_cards_cnt) - len(cards) >= 4:
    #             print("wild_shuffleは出しません!!")
    #             ans_list.remove({'color': 'black', 'special': 'wild_shuffle'})

    #シャッフルワイルドとワイルドドロー4を持っているときは先にワイルドドロー4を出し、チャレンジ成功されたら次のターンでシャッフル
    if wild_draw_4 in cards and shuffle_wild in cards and challenge_success:
        return [shuffle_wild]
    else:
        print("出せるのは(offensive)")
        print(ans_list)
        return ans_list


def offensive_color_order(cards: dict, card_status: dict) -> list:
    """
    手札から出すべき色の優先度を吐く
    Args:
        cards: 出せるカード or 自分の手札
        card_status: 場に出ていない札を管理する変数

    Returns:
        list: 色の優先順位
    """
    can_play_colors = set()
    for card in cards:
        card_color = card["color"]
        if card_color not in ["black","white"]:
            can_play_colors.add(card_color)

    color_list = []
    color_dic = {'red':0, 'blue':0, 'green':0, 'yellow':0}
    for k in color_dic.keys():
        color_dic[k] = color_counting(k, card_status)
    color_dic = sorted(color_dic.items(), key=lambda x: x[1])
    for k, v in color_dic:
        if v <= 5 and k in can_play_colors:
            color_list.append(k)

    color_dic = {'red':0, 'blue':0, 'green':0, 'yellow':0}
    for card in cards:
        card_color = card["color"]
        if card_color not in ["black","white"]:
            color_dic[card_color] += 1
    color_dic = sorted(color_dic.items(), key=lambda x:x[1], reverse=True)
    for k, v in color_dic:
        if k not in color_list:
            color_list.append(k)

    # color_dic = {'red':0, 'blue':0, 'green':0, 'yellow':0}
    # for card in cards:
    #     card_color = card["color"]
    #     if card_color not in ["black","white"]:
    #         color_dic[card_color] += 1

    # ans = sorted(color_dic.keys(), key=lambda x:x[1], reverse=True)

    return color_list





def deffesive_mode(my_id: str, cards: list, player_cards_cnt: dict, wild_shuffle_flag: bool, challenge_success: bool, should_play_draw4: bool, g_status: any) -> list:
    """
    防御モード
    cards :自分の中で出せるカード
    player_cards_cnt :他の奴らの手札の枚数
    wild_shuffle_flag: シャッフルワイルド持ってるか
    challenge_success :チャレンジを成功された過去があるか否か
    should_play_draw4: ドロー4出すべきか
    g_status: Statusインスタンス
    """
    print("---防御モード発動---")

    shuffle_wild = {'color':'black', 'special':'wild_shuffle'}
    wild_draw_4 = {'color':'black', 'special':'wild_draw_4'}
    min_cards_num = min_cards_check(my_id, player_cards_cnt)

    ans_list = []
    wild_lis = []
    draw_2_lis = []
    skip_reverse_lis = []
    num_lis = []

    if not wild_shuffle_flag:
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
        if should_play_draw4:
            for card in cards: # ワイルドドロー4を優先的に出す
                card_special = card.get("special")
                if card_special == "wild_draw_4":
                    wild_lis.append(card)
    else:
        if min_cards_num <= 2:
            wild_lis.append(shuffle_wild) # シャッフル最優先で出す

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
            if should_play_draw4:
                for card in cards: # ワイルドドロー4を優先的に出す
                    card_special = card.get("special")
                    if card_special == "wild_draw_4":
                        wild_lis.append(card)

        else:
            for card in cards: # 白いワイルドを優先的に出す
                card_special = card.get("special")
                if card_special == "white_wild":
                    wild_lis.append(card)

            # チャレンジが成功された場合は, ワイルドドロー4の優先順位は最低になる
            # そうでなければこの優先順位でワイルドドロー4を出す
            if not challenge_success:
                for card in cards: # ワイルドドロー4を優先的に出す
                    card_special = card.get("special")
                    if card_special == "wild_draw_4":
                        wild_lis.append(card)

            # 白いワイルド, ワイルドドロー4の次の優先度でシャッフル出す
            wild_lis.append(shuffle_wild)

            for card in cards: # ワイルドを優先的に出す
                card_special = card.get("special")
                if card_special == "wild":
                    wild_lis.append(card)


    # 色優先順位の決定
    # プレイヤーの手札枚数が最も少ないプレイヤーを取得する
    tgt_id = None
    cnt_min = 112
    for k, v in player_cards_cnt.items():
        if k != my_id and v < cnt_min:
            tgt_id = k
            cnt_min = v

    print("最もカード枚数が少ないプレイヤー", tgt_id)

    color_list = deffesive_color_order(tgt_id, g_status)
    # # game_statusインスタンスから, そのプレイヤーの色に関するゲーム記録を取得する
    # # 指定したプレイヤーの色に関する記録があれば参照する
    # if len(g_status.player_color_log[tgt_id]) > 0:

    #     # プレイヤーの苦手な色を取得
    #     last_chose_color, chose_reason = g_status.player_color_log[tgt_id][-1]

    #     # DEBUG
    #     print("---色チェック---", g_status.player_color_log[tgt_id][-1])

    #     # cards_statusを参照して既知なカードのうち、
    #     # 最も場に出されている色順に結果を出力したい
    #     dic = g_status.cards_status.copy()
    #     del dic["white"], dic["black"] # 白、黒は除外する

    #     tmp_lis = sorted(dic.items(), key=lambda x:sum(x[1].values()))
    #     color_list = [item[0] for item in tmp_lis]

    #     # DEBUG
    #     print("last_chose_color & reason:", last_chose_color, chose_reason)
    #     print("color_list:", *color_list)

    #     # 最後に記録された色は除外する
    #     print("除外するか？", last_chose_color in color_list)
    #     if last_chose_color in color_list:
    #         color_list.remove(last_chose_color)

    #     # 返すリストは　[(記録された色), (残りの色のうち、既知な色順)]
    #     color_list = [last_chose_color] + color_list

    # # 記録が無い場合はcards_statusを参照して既知なカードのうち、
    # # 最も場に出されている色順に結果を出力したい
    # else:
    #     dic = g_status.cards_status.copy()
    #     del dic["white"], dic["black"] # 白、黒は除外する
    #     tmp_lis = sorted(dic.items(), key=lambda x:sum(x[1].values()))
    #     print("color_list:", tmp_lis)
    #     color_list = [item[0] for item in tmp_lis]

    # # 色の優先順位を出力
    # print("色の優先順位:", *color_list)

    for card in cards: #ドロー2を優先的に出す
        card_special = card.get("special")
        if card_special == "draw_2":
            draw_2_lis.append(card)

    # ドロー2カードを出すべき色順に並び替える
    draw_2_lis = sorted(draw_2_lis, key=lambda x: color_list.index(x["color"]))

    for card in cards: #スキップ・リバースを優先的に出す
        card_special = card.get("special")
        if card_special in ["skip", "reverse"]:
            skip_reverse_lis.append(card)

    # スキップ・リバースカードを出すべき色順に並び替える
    skip_reverse_lis = sorted(skip_reverse_lis, key=lambda x: color_list.index(x["color"]))

    for card in cards: #数字カードは大きい数を優先的に出す
        if card.get("number") is not None:
            num_lis.append(card)
            # num_lis.append((card, int(card["number"])))

    color_list.reverse()
    num_lis_2 = sorted(num_lis, key=lambda x: (x["number"], color_list.index(x["color"])), reverse=True)
    # num_lis_2 = [item[0] for item in sorted(num_lis, key=lambda x: x[1], reverse=True)]

    # 答えのリストに追加する
    ans_list += wild_lis
    ans_list += draw_2_lis
    ans_list += skip_reverse_lis
    ans_list += num_lis_2

    # チャレンジが成功された場合は, ワイルドドロー4の優先順位は最低になる
    if wild_draw_4 in cards and wild_draw_4 not in ans_list:
        for card in cards: # ワイルドドロー4を出す
            card_special = card.get("special")
            if card_special == "wild_draw_4":
                ans_list.append(card)

    # # カードを出すか、ドローするか
    # # ワイルド系カードを持っていてそれしか出せるカードが無い時
    # if len(wild_lis) > 0 and len(wild_lis) == len(ans_list):
    #     # 残り手札が1枚の時は出してゲームをあがる
    #     if my_card == 1:
    #         return ans_list
    #     # 出せるカードがシャッフルワイルドのみの場合は出さずにカードを引く
    #     if len(wild_lis) == 1 and wild_lis[0].get("special") == "wild_shuffle":
    #         return []
    #     # それ以外の場合は出せるワイルド系カードを出す
    #     return ans_list

    # # ワイルド系カードを持っておらず、出せるカードが無いとき
    # elif len(wild_lis) == 0 and len(cards) == 0:
    #     # 山札からカードを引くのでNoneを返す
    #     return []

    # 上記以外の場合は通常通りにリストを返す
    return ans_list



def deffesive_color_order(player: str, g_status: any) -> list:
    """
    手札から出すべき色の優先度を吐く
    Args:
        player: 基準とするプレイヤー
        g_status: Statusインスタンス

    Returns:
        list: 色の優先順位
    """
    # cards_statusを参照して既知なカードのうち、
    # 最も場に出されている色順に結果を出力したい
    dic = g_status.cards_status.copy()
    del dic["white"], dic["black"] # 白、黒は除外する
    tmp_lis = sorted(dic.items(), key=lambda x:sum(x[1].values()))
    color_list = [item[0] for item in tmp_lis]

    # game_statusインスタンスから, そのプレイヤーの色に関するゲーム記録を取得する
    # 指定したプレイヤーの色に関する記録があれば参照する
    if len(g_status.player_color_log[player]) > 0:
        # プレイヤーの苦手な色を取得
        last_chose_color, chose_reason = g_status.player_color_log[player][-1]

        # DEBUG
        print("---色チェック---", g_status.player_color_log[player][-1])
        print("last_chose_color & reason:", last_chose_color, chose_reason)
        print("color_list:", *color_list)

        # 最後に記録された色は除外する
        print("除外するか？", last_chose_color in color_list)
        if last_chose_color in color_list:
            color_list.remove(last_chose_color)
            if chose_reason == "wild":
                # 返すリストは　[(残りの色のうち、既知な色順), (記録された色)]
                color_list = color_list + [last_chose_color]
            else:
                # 返すリストは　[(記録された色), (残りの色のうち、既知な色順)]
                color_list = [last_chose_color] + color_list

    # 記録が無い場合はcards_statusを参照して既知なカードのうち、
    # 最も場に出されている色順に結果を出力したい
    # else:
    #     dic = g_status.cards_status.copy()
    #     del dic["white"], dic["black"] # 白、黒は除外する
    #     tmp_lis = sorted(dic.items(), key=lambda x:sum(x[1].values()))
    #     print("color_list:", tmp_lis)
    #     color_list = [item[0] for item in tmp_lis]

    # 色の優先順位を出力
    print("色の優先順位:", *color_list)

    return color_list





def challenge_dicision(before_card: dict, my_id: str, before_id: str, player_card_counts: dict, num_of_deck: int, game_status: any, games: any):
    """
    チャレンジの判断関数
    args:
        before_card: dict = wild_draw_4前のカード
        my_id: str = 自分のID
        before_id: str = 直前のプレイヤーのID
        player_card_counts: dict = プレイヤーが持つカードの枚数
        num_of_deck: int = 山札の枚数
        game_status: Statusインスタンス
        games: Gamesインスタンス
    return:
        bool値 = チャレンジするか否か
    """
    # チャレンジ後開示された手札を記憶し、次ワイルドドロー4が出されたときに記憶した手札から場に出されたカードを消したものの中で出せるものがあれば必ずチャレンジ
    if len(game_status.other_open_cards[before_id]) > 0: # カードをオープンしてたら
        card_color = before_card.get("color") #wild_draw_4前のカードの色を取得
        card_number = before_card.get("number")
        card_special = before_card.get("special")
        for card in game_status.other_open_cards[before_id]: # オープンカードを片っ端からチェック
            if card.get("color") == card_color: # 同じ色あったら
                print('記憶したカードでチャレンジ')
                game_status.special_logic_flag[0] = True
                return True
            elif card_number is not None and card_number == card.get("number"):
                print('記憶したカードでチャレンジ')
                game_status.special_logic_flag[0] = True
                return True
            elif card_special is not None and card_special == card.get("spacial"):
                print('記憶したカードでチャレンジ')
                game_status.special_logic_flag[0] = True
                return True
            elif card_color in {'black', 'white'} and card_special != 'wild_draw_4':
                print('記憶したカードでチャレンジ')
                game_status.special_logic_flag[0] = True
                return True


    # 場札と自分の手札から相手が (同じ色を出せる確率) + (同じ数字・記号を出せる確率) + (ワイルド系カードを出せる確率) がp以上であればチャレンジ
    print(before_id)
    print(num_of_deck)

    # 色が何枚残っているか確認
    card_color = before_card.get("color")
    color_num = 0
    for i in game_status.cards_status[card_color].values():
        color_num += i

    print("残っている色の枚数は" + str(color_num))

    # 他プレイヤーが何枚残っているか確認
    other_card_num = 0
    for id, num in player_card_counts.items():
        if id != my_id:
            other_card_num += num


    # 直前のプレイヤーが何枚残っているか確認
    x = player_card_counts[before_id]

    #見えていないワイルドカードの枚数を確認
    wild_num = 0
    for k, i in game_status.cards_status["black"].items():
        if k != "wild_draw_4":
            wild_num += i

    wild_num += game_status.cards_status["white"]["white_wild"]

    print("xの枚数は" + str(x))
    print("x+y+zの枚数は" + str(other_card_num))

    print("ワイルドカードの枚数は" + str(wild_num))

    #確率計算0.48
    p = 1 - (math.comb(num_of_deck + other_card_num - color_num - wild_num, x) / math.comb(num_of_deck + other_card_num, x))

    print("他の出せるカードを"+ before_id +"が持っている確率は :" + str(p))

    # if not 0 <= p <= 1:
    #     exit(print("確率の壁を越えてるよ"))
    if p == 1:
        print('100%持ってる')
        # game_status.special_logic_flag[0] = True
        return True


    # 300戦した後のチャレンジ成功率が30%以下のとき、チャレンジしない
    if games.num_game > 300 and games.challenge_cnt[before_id][0] != 0:
        p_success = games.challenge_cnt[before_id][1] / games.challenge_cnt[before_id][0]
        print(before_id, 'に対するチャレンジ成功率:', p_success)
        print('チャレンジ回数:', games.challenge_cnt[before_id][0], '成功回数:', games.challenge_cnt[before_id][1])
        if p_success <= 0.3:
            return False


    # 相手が6枚以上持っているとき
    if player_card_counts[before_id] >= 6:
        return p >= 0.6 # 相手が出せるカードを持っている確率が60%以上のときチャレンジ
    # 相手が6枚未満の時
    else:
        return p >= 0.9 # 相手が出せるカードを持っている確率が90%以上のときチャレンジ



def play_draw4_dicision(valid_cards: list, before_card: dict, my_cards: list, my_id: str, next_id: str, player_card_counts: dict, num_of_deck: int, challenge_success: bool, game_status: any, games: any):
    """
    ドロ4出すかの判断関数
    args:
        valid_cards: list = 出せるカード
        before_card: dict = 前のカード
        my_cards: list = 自分の手札
        my_id: str = 自分のID
        next_id: str = 直後のプレイヤーのID
        player_card_counts: dict = プレイヤーが持つカードの枚数
        num_of_deck: int = 山札の枚数
        challenge_success: 自分に対してチャレンジ成功されたか
        game_status: Statusインスタンス
        games: Gamesインスタンス
    return:
        bool値 = ドロ4出すべきか否か
    """

    # 他に出せるカードがないとき必ず出す
    for card in valid_cards:
        if card != {"special": "wild_draw_4", "color": "black"}:
            break
    else:
        return True

    # チャレンジ成功されてるときは出さない
    if challenge_success:
        return False

    if games.num_game > 300 and games.challenged_cnt[next_id][0] != 0:
        p_challenge = games.challenged_cnt[next_id][1] / games.challenged_cnt[next_id][0]
        print(next_id, 'のチャレンジ率:', p_challenge)
        print('ドロ4出した回数:', games.challenged_cnt[next_id][0], 'チャレンジ回数:', games.challenged_cnt[next_id][1])
        if p_challenge >= 0.9: # 300戦した後、自分がドロー4出したときの相手のチャレンジ率が90%以上のとき、出さない
            return False
        elif p_challenge <= 0.05: # 300戦した後、自分がドロー4出したときの相手のチャレンジ率が5%以下のとき、出す
            return True

    if games.num_game > 300 and games.challenged_cnt[next_id][1] != 0:
        p_success = games.challenged_cnt[next_id][2] / games.challenged_cnt[next_id][1]
        print(next_id, 'のチャレンジ成功率:', p_success)
        print('チャレンジ回数:', games.challenged_cnt[next_id][1], '成功回数:', games.challenged_cnt[next_id][2])
        if p_success >= 0.8: # 300戦した後の被チャレンジ成功率が 80%以上のとき、出さない
            return False


    print(next_id)
    print(num_of_deck)

    # 色が何枚残っているか確認
    card_color = before_card.get("color")
    color_num = 0
    for i in game_status.cards_status[card_color].values():
        color_num += i


    # 他プレイヤーが何枚残っているか確認
    other_card_num = 0
    for id, num in player_card_counts.items():
        if id != next_id:
            other_card_num += num
        else:
            other_card_num += num // 2


    # 自分が何枚残っているか確認
    w = player_card_counts[my_id]

    # 見えていないワイルドカードの枚数を確認
    wild_num = 0
    for k, i in game_status.cards_status["black"].items():
        if k != "wild_draw_4":
            wild_num += i

    wild_num += game_status.cards_status["white"]["white_wild"]

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
    p = 1 - (math.comb(num_of_deck + other_card_num - color_num - wild_num, w) / math.comb(num_of_deck + other_card_num, w))

    print("他の出せるカードを"+ my_id +"が持っている確率は :" + str(p))

    # 相手が6枚以上持っているとき
    if player_card_counts[my_id] >= 6:
        return p < 0.5 # 自分が出せるカードを持っている確率が50%以上のとき出さない
    # 相手が6枚未満の時
    else:
        return p < 0.8 # 自分が出せるカードを持っている確率が80%以上のとき出さない


def pass_func(err) -> None:
    """
    個別コールバックを指定しないときの代替関数
    """
    return
