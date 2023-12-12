class Card_Select:
    def __init__(self) -> None:
        self.shuffle_wild_flag = False


    def check_wild_shuffle(self, flag:bool) -> None:
        self.shuffle_wild_flag = flag


    def select_play_card(self, my_cards:list, before_card:dict) -> dict:    
        """
        出すカードを選出する

        Args:
            my_cards (list): 自分の手札
            before_card (dict): 場札のカード
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
            tmp_list = self.decision_priority(valid_card_list)
            sort_pri_list = sorted(tmp_list, key=lambda x: (x[1][0], -x[1][1]))
        else:
            sort_pri_list = valid_card_list

        #################
        if len(sort_pri_list) > 0:
            return sort_pri_list[0][0]
        else:
            return None
        

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
                    if self.color_counting(select_color,card_status) > self.color_counting(card_color,card_status):
                        select_color = card_color


        ans = sorted(color_dic.items(), key=lambda x:x[1], reverse=True)
        print(ans)
        return select_color


    def color_counting(self,color:str,card_status:dict) -> int:
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


    def decision_priority(self, cards:list) -> list:
        """
        手札の優先度を決める関数

        Args:
            card_dict(dict): 自分の手札のカードを格納した辞書型
        Returns:
            ans_lis(list): 2次元配列(list in list), 要素=[cardオブジェクト, (優先順位, cardの数)]
        """
        ans_lis = []
        if self.shuffle_wild_flag == False:
            for card in cards:
                if "special" in card.keys():
                    if card.get("special") == "white_wild":
                        ans_lis.append([card,(1,1)])
                    elif card.get("special") == "wild_shuffle":
                        ans_lis.append([card,(2,1)])
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
        else:
            for card in cards:
                if "special" in card.keys():
                    if card.get("special") == "white_wild":
                        ans_lis.append([card,(6,1)])
                    elif card.get("special") == "wild_shuffle":
                        ans_lis.append([card,(7,1)])
                    elif card.get("special") == "wild_draw_4":
                        ans_lis.append([card,(1,1)])
                    elif card.get("special") == "wild":
                        ans_lis.append([card,(5,1)])
                    elif card.get("special") == "draw_2":
                        ans_lis.append([card,(4,1)])
                    elif card.get("special") == "skip" or card.get("special") == "reverse":
                        ans_lis.append([card,(3,1)])
                elif "number" in card.keys():
                    ans_lis.append([card,(2,card.get("number"))])

        return ans_lis
    

# def is_challenge()->bool:
    
#     return True


def pass_func(err)->None:
    """
    個別コールバックを指定しないときの代替関数
    """
    return