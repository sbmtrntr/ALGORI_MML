from collections import defaultdict, deque


class Card_Status:
    def __init__(self) -> None:
        self.cards_status = self.init_cards_status()
        self.my_cards = []
        self.player_card_counts = defaultdict(lambda: 7)
        self.player_card_log = defaultdict(lambda: deque(maxlen=None))


    def init_cards_status(self) -> dict:
        """
        カードカウンティング用変数(cards_status)と自分の手札(my_cards)の初期化
        """
        cards_status = {
            "blue"  :{"0":1,"1":2,"2":2,"3":2,"4":2,"5":2,"6":2,"7":2,"8":2,"9":2,"draw_2":2,"skip":2,"reverse":2},
            "green" :{"0":1,"1":2,"2":2,"3":2,"4":2,"5":2,"6":2,"7":2,"8":2,"9":2,"draw_2":2,"skip":2,"reverse":2},
            "red"   :{"0":1,"1":2,"2":2,"3":2,"4":2,"5":2,"6":2,"7":2,"8":2,"9":2,"draw_2":2,"skip":2,"reverse":2},
            "yellow":{"0":1,"1":2,"2":2,"3":2,"4":2,"5":2,"6":2,"7":2,"8":2,"9":2,"draw_2":2,"skip":2,"reverse":2},
            "black" :{"wild":4,"wild_draw_4":4,"wild_shuffle":1},
            "white" :{"white_wild":3},
        }
        
        return cards_status


    def set_my_cards(self, cards:list) -> None:
        """
        自分の手札(my_cards)の更新
        """
        self.my_cards = cards
   

    def update_cards_status(self, cards:any) -> None:
        """
        場に出たカードを減らす

        Args:
            cards (dict|list): 場に出たカードor手札に来たカード
        Returns:
            None
        """

        if isinstance(cards, dict):
            cards = [cards]

        for card in cards:
            card_color = card["color"]

            #draw4とwildカード系は使用時に変更先の色として使われるので特殊処理する
            if "special" in card and card["special"] in ["wild", "wild_draw_4"]:
                card_color = "black"
                card_type = card["special"]

            elif card_color in ["black", "white"]:
                card_type = card["special"]

            else:
                if "number" in card:
                    card_type = str(card["number"])
                else:
                    card_type = card["special"]
            
            self.cards_status[card_color][card_type] -= 1

    
    def return_my_cards(self) -> None:
        """
        シャッフルによって場に戻った手札の分cards_statusを更新する
        """

        for card in self.my_cards:
            card_color = card["color"]
            if "number" in card:
                card_type = str(card["number"])
            elif "special" in card:
                card_type = card["special"]
                if card_type == "wild_draw_4":
                    card_color = "black"
            self.cards_status[card_color][card_type] += 1


    def wild_shuffle_flag(self) -> bool:
        for card in self.my_cards:
            if card.get("special") == "wild_shuffle":
                return True
            
        return False
    
    def update_player_card_counts(self, player:str, card_num:int) -> None:
        """
        適宜イベント時に呼び出して、
        引数で指定したプレイヤーのカードを更新させる関数

        Args: 
            player(str): カードを出した or 引いたプレイヤー名
            draw_num(int): カードを受け取る枚数, 負の整数も可能
        Returns: 
            None
        """
        self.player_card_counts[player] = card_num

        # Debug用プリント処理
        # if self.player_card_counts[player] < 0:
        #     print(f"{player}のカード枚数は0以上でなれければならない。")


    def update_player_card_log(self, player:str, card:any) -> None:
        """
        プレイヤーごとに
        - どのようなカードを場に出したか
        - そのときの、カードを出した後のの残り枚数
        を時系列で記録する関数

        Args: 
            player(str): プレイヤー名
            card(any): 場に出したカード
            
        Returns: 
            None
        """
        tmp_dict = {
            "card_counts":self.player_card_counts[player]-1,
            "card": card,
        }
        self.player_card_log[player].append(tmp_dict)
        if len(self.player_card_log[player]) >= 2:
            print("今のは" + str(self.player_card_log[player][-1]))
            print("その前は" + str(self.player_card_log[player][-2]))



