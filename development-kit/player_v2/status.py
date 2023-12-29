from collections import defaultdict, deque
from typing import Union

NUM_OF_ALL_CARDS = 112

class Status:
    def __init__(self) -> None:
        self.cards_status = self.init_cards_status()
        self.my_cards = []
        self.order_dic = {}
        self.uno_declared = {}
        self.my_uno_flag = False
        self.num_of_deck = NUM_OF_ALL_CARDS-4*7-1 # 山札の枚数
        self.num_of_field = 1 # 場にあるカードの枚数

        # プレイヤーごとに手札の枚数を記録しておくディクショナリ
        self.player_card_counts = defaultdict(int)

        # 「誰が」「どのカードを」出したかを記録するディクショナリ
        self.player_card_log = defaultdict(lambda: deque(maxlen=None))

        # 場に出されたカードを記録する配列
        self.feild_cards = deque(maxlen=None)

        # 誰がどの手札を公開したか記録するdict(list(card))
        self.other_open_cards = defaultdict(list)


    def init_cards_status(self) -> dict:
        """
        カードカウンティング用変数(cards_status)と自分の手札(my_cards)の初期化
        """
        cards_status = {
            "blue"  : {"0": 1, "1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 2, "8": 2, "9": 2, "draw_2": 2, "skip": 2, "reverse": 2},
            "green" : {"0": 1, "1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 2, "8": 2, "9": 2, "draw_2": 2, "skip": 2, "reverse": 2},
            "red"   : {"0": 1, "1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 2, "8": 2, "9": 2, "draw_2": 2, "skip": 2, "reverse": 2},
            "yellow": {"0": 1, "1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 2, "8": 2, "9": 2, "draw_2": 2, "skip": 2, "reverse": 2},
            "black" : {"wild": 4, "wild_draw_4": 4, "wild_shuffle": 1},
            "white" : {"white_wild": 3},
        }
        return cards_status
    

    def init_player_card_counts(self, player_id_list: list) -> None:
        """
        プレイヤーのカード枚数カウントを初期化するメソッド
        Args:
            player_id_list(list): 全員分のplayer_idを格納したリスト
        """
        for player_id in player_id_list:
            self.player_card_counts[player_id] = 7


    def set_my_cards(self, cards:list) -> None:
        """自分の手札(my_cards)の更新"""
        self.my_cards = cards


    def update_cards_status(self, cards: Union[dict, list]) -> None:
        """
        場に出たカード、手札に来たカードからcards_statusを更新するメソッド
        Args:
            cards (dict|list): 場に出たカード or 手札に来たカード
        """
        if isinstance(cards, dict):
            # 場に出されたカードの場合は記録しておく
            cards = [cards]

        for card in cards:
            card_color, card_type = self.get_keys_for_card_status(card)
            self.cards_status[card_color][card_type] -= 1

        print("場札または手札にないのは")
        print("カードステータス:", self.cards_status)

    
    def return_my_cards(self) -> None:
        """
        シャッフルによって場に戻った手札の分cards_statusを更新する
        """
        for card in self.my_cards:
            card_color, card_type = self.get_keys_for_card_status(card)
            self.cards_status[card_color][card_type] += 1


    def wild_shuffle_flag(self) -> bool:
        for card in self.my_cards:
            if card.get("special") == 'wild_shuffle':
                return True
        return False


    def check_player_card_counts(self, player: str, card_num: int) -> None:
        """
        「自分のターン時に」呼び出して、
        引数で指定したプレイヤーのカードを更新させる関数
        カード枚数を照合する役割を果たす
        ※ペナルティなどのイベントで枚数計算がうまくいかない場合がある
        ※毎ターン提示される各プレイヤーの枚数情報を用いて正しい枚数に修正する

        Args:
            player(str): カードを出した or 引いたプレイヤー名
            draw_num(int): カードの枚数
        """

        # Debug用プリント処理
        print("---枚数照合---")
        print("誰？：", player)
        print("dealerから送られてきたカード枚数:", card_num)
        print("game_statusで記録していたカード枚数:", self.player_card_counts[player])
        print("正しいか:", self.player_card_counts[player]==card_num)

        # 更新
        if self.player_card_counts[player] != card_num:
            print("正しい枚数に更新する")
            self.player_card_counts[player] = card_num


    def update_player_card_log(self, player:str, card:any) -> None:
        """
        プレイヤーごとに
        - どのようなカードを場に出したか
        - そのときの、カードを出した後の残り枚数
        を時系列で記録する関数

        Args:
            player(str): プレイヤー名
            card(any): 場に出したカード
        """

        tmp_dict = {
            "card_counts":self.player_card_counts[player],
            "card": card,
        }

        # プレイヤーごとにカードログを記録
        self.player_card_log[player].append(tmp_dict)

        # DEBUG用
        if len(self.player_card_log[player]) >= 2:
            print("今のは" + str(self.player_card_log[player][-1]))
            print("その前は" + str(self.player_card_log[player][-2]))


    def set_play_order(self, order: list, my_id: str) -> None:
        """順番を記憶させる関数"""
        my_pos = order.index(my_id)
        self.order_dic[order[(my_pos + 1) % 4]] = {"位置": "直後", "UNO": False}
        self.order_dic[order[(my_pos + 2) % 4]] = {"位置": "対面", "UNO": False}
        self.order_dic[order[(my_pos + 3) % 4]] = {"位置": "直前", "UNO": False}


    def reverse_order(self) -> None:
        """順番逆転に対応させる関数"""
        print("反転発動")
        print(self.order_dic)
        for i, v in self.order_dic.items():
            if v["位置"] == "直前":
                self.order_dic[i]["位置"] = "直後"
            elif v["位置"] == "直後":
                self.order_dic[i]["位置"] = "直前"


    def get_before_id(self) -> str:
        """直前のプレイヤーのidを入手する関数(ごめん)"""
        for i, v in self.order_dic.items():
            if v["位置"] == "直前":
                return i
            
        return ""    


    def set_uno_player(self, player_id: str) -> None:
        """UNO宣言したやつの記憶"""
        print(player_id + "がUNOしました" )
        self.order_dic[player_id]["UNO"] = True


    def undo_uno_player(self, player_id: str) -> None:
        """UNO宣言解除したやつの記憶"""
        print(player_id + "がUNO解除しました" )
        self.order_dic[player_id]["UNO"] = False


    def deck_empty(self) -> None:
        """山札が0になった場合にcard_statusをリセットするメソッド"""
        print("山札が切れました")
        # card_statusのリセット
        self.cards_status = self.init_cards_status()

        # 最後に場に出されたカードは山札に戻らないのでcard_statusから除外する
        card_color, card_type = self.get_keys_for_card_status(self.feild_cards[-1])
        self.cards_status[card_color][card_type] -= 1

        # 自分の手札カードも山札に戻らないのでcard_statusから除外する
        for card in self.my_cards:
            card_color, card_type = self.get_keys_for_card_status(card)
            self.cards_status[card_color][card_type] -= 1

        # 山札枚数を再計算する
        # 最後の1枚を除いて山札に戻す、山札がマイナス(借金状態)な時も考慮する
        self.num_of_deck = self.num_of_field - 1 + self.num_of_deck 
        self.num_of_field = 1 # 場のカードは1枚にする

        # debug print
        print("---山札のリセットがうまくできているか---")
        self.debug_print()
    

    def get_keys_for_card_status(self, card) -> tuple:
        """
        card_status用のkeyを取得するメソッド
        
        Args:
            card(any):カード
        Returns
            tuple: (color, type)
        """

        # カードの色を取得
        card_color = card["color"]

        # draw4とwildカード系は使用時に変更先の色として使われるので特殊処理する
        if "special" in card and card["special"] in ["wild_draw_4", "wild"]:
            card_color = "black"
            card_type = card["special"]

        elif card_color in ["black", "white"]:
            card_type = card["special"]

        else:
            if "number" in card:
                card_type = str(card["number"])
            else:
                card_type = card["special"]

        return (card_color, card_type)
    

    def draw_card(self, player:str, penalty_draw:int=0) -> None:
        """
        カードが山札から引かれた時に実行されるメソッド
        ※このメソッドでは「cards_status」を操作しない
        
        Args:
            player(str): カードを引くプレイヤー
            penalty_draw(bool): ペナルティ時に何枚引くかを指定する ※0枚の時はペナルティ無しと扱う  
        """
        # 自分がカードを引いた際、そのターンにどのカードを引いたのか判定できない
        # 自分のターンが回ってきたときに増加分のカードのcards_statusを更新する

        print(f"---{player}がカードを引きます---")

        # 手持ちが25枚より大きい状態になることを許容するか
        is_ok_over_25 = True

        # 最後に出されたカードを取得する
        top_card = self.feild_cards[-1]

        # ペナルティの場合は指定した回数分だけ引く
        if penalty_draw:
            num_of_draw = penalty_draw
            is_ok_over_25 = False 
            print("引く理由: ペナルティ")

        # 山札から引くカードの枚数を指定
        # 最後に場に出されたカードに応じて場合分け
        elif top_card.get("special") == "draw_2":
            num_of_draw = 2
            print("引く理由: draw_2")

        elif top_card.get("special") == "wild_draw_4":
            num_of_draw = 4
            print(f"引く理由: wild_draw_4")

        elif top_card.get("special") == "white_wild":
            num_of_draw = 2
            print(f"引く理由: white_wild")

        else:
            num_of_draw = 1
            is_ok_over_25 = True
            print(f"引く理由: 場に出すカードがない(再行動可能)")

        print("---更新前---")
        print(f"山札:{self.num_of_deck}枚")
        for k, v in self.player_card_counts.items():
            print(f"{k}:{v}枚", end=" ")
        print()

        # 手持ちが25枚より多い状態になることが許容されない場合
        if not is_ok_over_25:
            # 引いた後の手札が25枚以下になるように引く枚数を調整する
            print("25枚以下制約あり")
            num_of_draw = max(0, min(25 - self.player_card_counts[player], num_of_draw))

        # 山札とプレイヤーの手札の枚数を更新
        self.num_of_deck -= num_of_draw
        self.player_card_counts[player] += num_of_draw
        
        print("---更新後---")
        print(f"山札から{player}へ{num_of_draw}枚移動")
        print(f"山札:{self.num_of_deck}枚")
        for k, v in self.player_card_counts.items():
            print(f"{k}:{v}枚", end=" ")
        print()

        # 山札が無くなった場合は以下を実行
        if self.num_of_deck <= 0:
            self.deck_empty()

        # 最後に場に出されたカードがドロー系カードの場合
        # 次プレイヤーが同じ被害を被らないようにしておく
        if top_card.get("special") in ["draw_2", "wild_draw_4", "white_wild"]:
            self.feild_cards.append({}) # 一度効力を発動したドローカードは無効化


    def play_card(self, card:any, player:str) -> None:
        """
        カードを場に出した際に呼ばれるメソッド
        ※このメソッドでは「cards_status」を操作しない
        
        Args:
            card(any): 場に出たカード
            player(str): カードを出したプレイヤー
        """

        # プレイヤーの手札を1枚減らす
        self.player_card_counts[player] -= 1 

        # 場のカード枚数を1枚増やす
        self.num_of_field += 1

        # カードを記録する
        self.feild_cards.append(card) # 場に出たカードの記録
        self.update_player_card_log(player, card) # プレイヤーごとのログを取る

        # DEBUG
        print("---場にカードを出した---")
        print("プレイヤー:", player)
        print("カード:", card)
        self.debug_print()   
 

    def debug_print(self) -> None:
        """Debug用のメソッド"""
        print("山札の枚数:", self.num_of_deck)
        print("場の枚数:", self.num_of_field)
        cnt = self.num_of_field + self.num_of_deck
        for k, v in self.player_card_counts.items():
            print(f"{k}の枚数:", v)
            cnt += v
        print("カード合計:", cnt)
        print("CHECK:", cnt==NUM_OF_ALL_CARDS)
        print("最後に記録されたカード:", self.feild_cards[-1])

    
    def set_other_player_cards(self, id:str, cards:list) -> None:
        """
        他のやつが手札公開したときに覚えておくための関数
        args:
            id:str = 公開したプレイヤーのid
            cards:list = 公開した内容

        """

        for i in cards:
            if i not in self.other_open_cards[id]:#公開された中に存在していなかったら
                self.other_open_cards[id].append(i)

    
    def remove_other_player_cards(self, id:str, card:dict) -> None:
        """
        手札公開していたやつが使ったカードを公開していた手札から消去する関数
        args:
            id:str = 公開したプレイヤーのid
            card:dict = 使ったカード

        """

        if len(self.other_open_cards[id]) > 0: #そいつがカードを公開していて
            if card in self.other_open_cards[id]: #そいつがその札持ってたら
                print(id+"が公開済みカードを使いました")
                print(card)
                self.other_open_cards[id].remove(card)


    def init_open_cards(self):
        """
        ワイルドシャッフル時に公開済みカードを初期化する関数
        """

        print("公開カードリセット")
        self.other_open_cards = defaultdict(list)

