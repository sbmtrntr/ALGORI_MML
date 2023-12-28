from collections import defaultdict

class Card_Select:

    def __init__(self) -> None:
        self.shuffle_wild_flag = False
        self.order_dic = defaultdict(dict)


    def check_wild_shuffle(self, flag:bool) -> None:
        self.shuffle_wild_flag = flag


    def select_play_card(self, my_cards:list, player_card_counts:dict, before_card:dict, status:dict) -> dict:    
        """
        出すカードを選出する

        Args:
            my_cards (list): 自分の手札
            before_card (dict): 場札のカード
            status: Card_Statusインスタンス
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
            if card_special == 'wild_draw_4': # ワイルドドロー4
                # ワイルドドロー4は場札に関係なく出せる
                cards_wild4.append(card)

            elif card_special in ['wild', 'wild_shuffle', 'white_wild']:
                # ワイルド・シャッフルワイルド・白いワイルドも場札に関係なく出せる
                cards_wild.append(card)

            elif card['color'] == before_card['color']:
                # 場札と同じ色のカード
                cards_valid.append(card)

            elif (
                (card_special and str(card_special) == str(before_card.get('special'))) or
                ((card_number is not None or (card_number is not None and int(card_number) == 0)) and (before_card.get('number') and int(card_number) == int(before_card.get('number'))))
            ):
                # 場札と数字または記号が同じカード
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
            for i,v in self.order_dic.items():
                if v["Unoか"] == True:
                    tmp_list = self.defensive_card_choice(valid_card_list, v["位置"], status)
                    return tmp_list[0]

            if self.analyze_situ(my_cards, player_card_counts) == "akan":
                tmp_list = self.decision_priority_0(valid_card_list)    
                sort_pri_list = sorted(tmp_list, key=lambda x: (x[1][0], -x[1][1]))
                return sort_pri_list[0][0]

            else:
                return valid_card_list[0]

        else:
            return None


    def defensive_card_choice(self, valid_card_list:list, pos:str, status:dict) -> list:
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
                cnt_by_color[color] = self.color_counting(color, status)
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
                # if specials_dict.get(key):
                rtn_list += specials_dict.get(key,[])
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
            specials_key_list = ['wild_shuffle', 'white_wild', 'wild_draw_4', 'draw_2', 'wild', 'reverse', 'skip']

            # 返り値の作成
            rtn_list = []
            for key in specials_key_list:
                if specials_dict.get(key,False) != False:
                    rtn_list += specials_dict.get(key)
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
            specials_key_list = ['wild_shuffle', 'wild_draw_4', 'draw_2', 'wild', 'white_wild', 'skip']

            # 数字カードの値が大きい順に数字カードをソートする
            tmp_num_list = [item[1] for item in sorted(nums_dict.items(), key=lambda x:int(x[0]), reverse=True)]
            print("tmp_num_list")
            print(tmp_num_list)

            # 返り値の作成
            rtn_list = []
            for key in specials_key_list:
                if specials_dict.get(key,False) != False:
                    rtn_list += specials_dict.get(key)

            print("rtn_list_1 :")
            print(rtn_list)
            rtn_list += tmp_num_list
            print("rtn_list_2 :")
            print(rtn_list)
            rtn_list += specials_dict.get('reverse',[])

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


    def analyze_situ(self, my_cards:dict, player_card_counts:dict) -> str:
        """全体の手札の状況から戦況判断する関数"""
        
        min_cards_num = 100
        for v in player_card_counts.values():
            min_cards_num = min(v, min_cards_num)

        if self.shuffle_wild_flag:
            n = 4
        else:
            n = 1
        
        if len(my_cards) - min_cards_num >= n:
            return "akan"
        else:
            return "normal"


    def select_change_color(self, my_cards:list, card_status: dict)->str:
        """
        変更する色を選出する
        
        Args:
            my_cards(list):自分の手札
            card_status(dict):場に出ていない札の数の状況

        Returns:
            str: ランダムに選択された色
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

                elif color_dic[select_color] == color_dic[card_color]: #最も多い色札の枚数が被ったら
                    if self.color_counting(select_color, card_status) > self.color_counting(card_color,card_status):
                        select_color = card_color


        ans = sorted(color_dic.items(), key=lambda x:x[1], reverse=True)
        print(ans)
        return select_color


    def color_counting(self, color:str, card_status:dict) -> int:
        """
        色を指定し、その色の場に出ていない札が何枚残っているか返す関数

        Args:
            color(str):指定した色
            card_status(dict):場に出ていない札を管理する変数

        Returns:
            int:何枚残っているか

        """

        card_nums = card_status[color]
        color_num = 0
        for v in card_nums.values():
            color_num += v
        
        return color_num


    def decision_priority_0(self, cards:list) -> list:
        """
        手札の優先度を決める関数

        Args:
            card_dict(dict): 自分の手札のカードを格納した辞書型
        Returns:
            ans_lis(list): 2次元配列(list in list), 要素=[cardオブジェクト, (優先順位, cardの数)]
        """
        ans_lis = []
        #if self.shuffle_wild_flag == False:
        for card in cards:
            if "special" in card.keys():
                if card.get("special") == "white_wild":
                    ans_lis.append([card,(2,1)])
                elif card.get("special") == "wild_shuffle":
                    ans_lis.append([card,(1,1)])
                elif card.get("special") == "wild_draw_4":
                    ans_lis.append([card,(3,1)])
                elif card.get("special") == "wild":
                    ans_lis.append([card,(4,1)])
                elif card.get("special") == "draw_2":
                    ans_lis.append([card,(5,1)])
                elif card.get("special") == "skip" or card.get("special") == "reverse":
                    ans_lis.append([card,(6,1)])
            elif "number" in card.keys():
                ans_lis.append([card,(7,card.get("number"))])
        # else:
        #     for card in cards:
        #         if "special" in card.keys():
        #             if card.get("special") == "white_wild":
        #                 ans_lis.append([card,(6,1)])
        #             elif card.get("special") == "wild_shuffle":
        #                 ans_lis.append([card,(7,1)])
        #             elif card.get("special") == "wild_draw_4":
        #                 ans_lis.append([card,(1,1)])
        #             elif card.get("special") == "wild":
        #                 ans_lis.append([card,(5,1)])
        #             elif card.get("special") == "draw_2":
        #                 ans_lis.append([card,(4,1)])
        #             elif card.get("special") == "skip" or card.get("special") == "reverse":
        #                 ans_lis.append([card,(3,1)])
        #         elif "number" in card.keys():
        #             ans_lis.append([card,(2,card.get("number"))])

        return ans_lis
    

    def set_play_order(self, order:list, my_id:str) -> None:
        """順番を記憶させる関数"""

        my_pos = order.index(my_id)
        self.order_dic[order[(my_pos+1)%4]] = {"位置":"直後", "Unoか":False}
        self.order_dic[order[(my_pos+2)%4]] = {"位置":"対面", "Unoか":False}
        self.order_dic[order[(my_pos+3)%4]] = {"位置":"直前", "Unoか":False}


    def reverse_order(self) -> None:
        """順番逆転に対応させる関数"""

        print("反転発動")
        print(self.order_dic)
        for i, v in self.order_dic.items():
            if v["位置"] == "直前":
                self.order_dic[i]["位置"] = "直後"
            elif v["位置"] == "直後":
                self.order_dic[i]["位置"] = "直前"

    
    def set_uno_player(self, player_id:str) -> None:
        """UNO宣言したやつの記憶"""

        print(player_id + "がUNOしました" )
        self.order_dic[player_id]["Unoか"] = True

    
    def undo_uno_player(self, player_id:str) -> None:
        """UNO宣言解除したやつの記憶"""

        print(player_id + "がUNO解除しました" )
        self.order_dic[player_id]["Unoか"] = False


def pass_func(err)->None:
    """
    個別コールバックを指定しないときの代替関数
    """
    return