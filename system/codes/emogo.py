import threading
import time
import can
import sys

class Stone:
    # 定数の定義
    COLOR_VALUES = {
        'black': 0x01,
        'white': 0x02
    }

    DIRECTION_VALUES = {
        'north': 90,
        'east': 180,
        'south': 270,
        'west': 0
    }

    EMOTION_VALUES = {
        'dead': 0,
        'defensive': 1,
        'normal': 2,
        'offensive': 3
    }

    def __init__(self):
        self.color = None
        self.direction = self.DIRECTION_VALUES['north']
        self.emotion = self.EMOTION_VALUES['normal']

    # 色を設定するメソッド
    def set_color(self, color):
        if color in self.COLOR_VALUES:
            self.color = self.COLOR_VALUES[color]
        elif color in self.COLOR_VALUES.values():
            self.color = color
        else:
            raise ValueError("Invalid color")

    # 色を取得するメソッド
    def get_color(self):
        return self.color or 0x00  # 0x00 は石がないことを示す

    # 向きを設定するメソッド
    def set_direction(self, direction):
        if direction in self.DIRECTION_VALUES:
            self.direction = self.DIRECTION_VALUES[direction]
        elif direction in self.DIRECTION_VALUES.values():
            self.direction = direction
        else:
            raise ValueError("Invalid direction")

    # 向きを取得するメソッド
    def get_direction(self):
        return self.direction or 0

    # 感情を設定するメソッド
    def set_emotion(self, emotion):
        if emotion in self.EMOTION_VALUES:
            self.emotion = self.EMOTION_VALUES[emotion]
        elif emotion in self.EMOTION_VALUES.values():
            self.emotion = emotion
        else:
            raise ValueError("Invalid emotion")

    # 感情を取得するメソッド
    def get_emotion(self):
        return self.emotion or self.EMOTION_VALUES['dead']

class Board:
    def __init__(self, n, m):
        self.n = n  # 行数
        self.m = m  # 列数
        self.board = [[None for _ in range(m)] for _ in range(n)]  # [行][列] の順序
        self.connect = []

    # 石を置くメソッド
    def place_stone(self, x, y, color):
        if 1 <= x <= self.n and 1 <= y <= self.m:
            ix = x - 1  # 行インデックス
            iy = y - 1  # 列インデックス
            if self.board[ix][iy] is None:
                stone = Stone()
                stone.set_color(color)
                stone.set_direction('north')
                stone.set_emotion('normal')
                self.board[ix][iy] = stone
                # ここで死に石判定を行う
                self.check_dead_stones_after_placement(x, y, color)
            else:
                raise RuntimeError(f"Position ({x}, {y}) already has a stone")
        else:
            raise IndexError(f"Position ({x}, {y}) is out of bounds")

    # 石を取り除くメソッド
    def remove_stone(self, x, y):
        if 1 <= x <= self.n and 1 <= y <= self.m:
            ix = x - 1  # 行インデックス
            iy = y - 1  # 列インデックス
            if self.board[ix][iy] is not None:
                self.board[ix][iy] = None
            else:
                raise RuntimeError(f"No stone at position ({x}, {y}) to remove")
        else:
            raise IndexError(f"Position ({x}, {y}) is out of bounds")

    # 石を取得するメソッド
    def get_stone(self, x, y):
        if 1 <= x <= self.n and 1 <= y <= self.m:
            ix = x - 1  # 行インデックス
            iy = y - 1  # 列インデックス
            return self.board[ix][iy]
        else:
            raise IndexError(f"Position ({x}, {y}) is out of bounds")

    # 死に石判定を行うメソッド
    def check_dead_stones_after_placement(self, x, y, color):
        opponent_color = 'white' if color == 'black' else 'black'

        # 1. 相手の死に石を判定し、感情を 'dead' に設定
        opponent_dead_stones = self.find_dead_stones(opponent_color)
        for ix, iy in opponent_dead_stones:
            stone = self.board[ix][iy]
            if stone:
                stone.set_emotion('dead')

        # 2. 自分の死に石を判定し、感情を 'dead' に設定
        self_dead_stones = self.find_dead_stones(color)
        for ix, iy in self_dead_stones:
            stone = self.board[ix][iy]
            if stone:
                stone.set_emotion('dead')

        # 3. 繋がりと感情の更新
        self.check_connect()

    # 死に石を見つけるメソッド
    def find_dead_stones(self, color):
        visited = [[False for _ in range(self.m)] for _ in range(self.n)]
        dead_stones = []

        for ix in range(self.n):
            for iy in range(self.m):
                if visited[ix][iy]:
                    continue
                stone = self.board[ix][iy]
                if stone is None or stone.get_color() != Stone.COLOR_VALUES[color]:
                    continue
                group, liberties = self.dfs(ix, iy, color, visited)
                if liberties == 0:
                    dead_stones.extend(group)
        return dead_stones

    # 深さ優先探索でグループと呼吸点を計算
    def dfs(self, ix, iy, color, visited):
        stack = [(ix, iy)]
        group = []
        liberties = set()  # 呼吸点をセットで管理
        visited[ix][iy] = True

        while stack:
            x, y = stack.pop()
            group.append((x, y))

            neighbors = [
                (x - 1, y),  # 上
                (x + 1, y),  # 下
                (x, y - 1),  # 左
                (x, y + 1)   # 右
            ]

            for nx, ny in neighbors:
                if 0 <= nx < self.n and 0 <= ny < self.m:
                    neighbor_stone = self.board[nx][ny]
                    if neighbor_stone is None or neighbor_stone.get_emotion() == Stone.EMOTION_VALUES['dead']:
                        liberties.add((nx, ny))  # 呼吸点をセットに追加
                    elif neighbor_stone.get_color() == Stone.COLOR_VALUES[color] and not visited[nx][ny]:
                        visited[nx][ny] = True
                        stack.append((nx, ny))
        return group, len(liberties)

    # 連のためのDFS（死に石も含む）
    def dfs_for_connect(self, ix, iy, color, visited):
        stack = [(ix, iy)]
        group = []
        liberties = set()
        visited[ix][iy] = True

        while stack:
            x, y = stack.pop()
            group.append((x, y))

            neighbors = [
                (x - 1, y),  # 上
                (x + 1, y),  # 下
                (x, y - 1),  # 左
                (x, y + 1)   # 右
            ]

            for nx, ny in neighbors:
                if 0 <= nx < self.n and 0 <= ny < self.m:
                    if not visited[nx][ny]:
                        neighbor_stone = self.board[nx][ny]
                        if neighbor_stone is not None and neighbor_stone.get_color() == color:
                            visited[nx][ny] = True
                            stack.append((nx, ny))
                        elif neighbor_stone is None or neighbor_stone.get_emotion() == Stone.EMOTION_VALUES['dead']:
                            liberties.add((nx, ny))
        return group, len(liberties)

    # 連と感情を再計算するメソッド
    def check_connect(self):
        self.connect = []
        visited = [[False for _ in range(self.m)] for _ in range(self.n)]

        for ix in range(self.n):
            for iy in range(self.m):
                if visited[ix][iy]:
                    continue
                stone = self.board[ix][iy]
                if stone is None:
                    continue  # 死に石も含めるため、感情チェックを削除
                color = stone.get_color()
                group, liberties_count = self.dfs_for_connect(ix, iy, color, visited)
                # 感情の設定
                emotion = 'normal'
                if liberties_count == 1:
                    emotion = 'defensive'
                elif liberties_count == 0:
                    emotion = 'dead'
                for gx, gy in group:
                    self.board[gx][gy].set_emotion(emotion)
                self.connect.append(group)

    # 指定された位置の石と連絡している石を取得するメソッド
    def get_connect(self, x, y):
        if 1 <= x <= self.n and 1 <= y <= self.m:
            ix = x - 1  # 行インデックス
            iy = y - 1  # 列インデックス
            start_stone = self.board[ix][iy]
            if start_stone is None:
                raise RuntimeError(f"No stone at position ({x}, {y})")
            else:
                color = start_stone.get_color()
                connected_stones = self.dfs_get_connected_stones(ix, iy, color)
                return [(cx + 1, cy + 1) for cx, cy in connected_stones]
        else:
            raise IndexError(f"Position ({x}, {y}) is out of bounds")

    # 深さ優先探索で連絡している石を取得するメソッド（死に石も含む）
    def dfs_get_connected_stones(self, ix, iy, color):
        stack = [(ix, iy)]
        connected = []
        visited = [[False for _ in range(self.m)] for _ in range(self.n)]
        visited[ix][iy] = True

        while stack:
            x, y = stack.pop()
            connected.append((x, y))

            neighbors = [
                (x - 1, y),  # 上
                (x + 1, y),  # 下
                (x, y - 1),  # 左
                (x, y + 1)   # 右
            ]

            for nx, ny in neighbors:
                if 0 <= nx < self.n and 0 <= ny < self.m:
                    if not visited[nx][ny]:
                        neighbor_stone = self.board[nx][ny]
                        if neighbor_stone is not None and neighbor_stone.get_color() == color:
                            visited[nx][ny] = True
                            stack.append((nx, ny))
        return connected

    # 石の数を数えるメソッド
    def stone_counts(self):
        black_count = 0
        white_count = 0
        for row in self.board:
            for stone in row:
                if stone and stone.get_emotion() != Stone.EMOTION_VALUES['dead']:
                    if stone.get_color() == Stone.COLOR_VALUES['black']:
                        black_count += 1
                    elif stone.get_color() == Stone.COLOR_VALUES['white']:
                        white_count += 1
        return {'black': black_count, 'white': white_count}

    # ボードの状態を取得するメソッド
    def get_board_state(self):
        state = []
        for ix, row in enumerate(self.board):
            for iy, stone in enumerate(row):
                if stone:
                    x = ix + 1
                    y = iy + 1
                    state.append({
                        'x': x,
                        'y': y,
                        'color': stone.get_color(),
                        'emotion': stone.get_emotion(),
                        'direction': stone.get_direction()
                    })
        return state

    # 指定した碁石の状態（感情、向き）を直接変更するメソッド
    def set_stone_state(self, x, y, emotion=None, direction=None):
        if 1 <= x <= self.n and 1 <= y <= self.m:
            ix = x - 1  # 行インデックス
            iy = y - 1  # 列インデックス
            stone = self.board[ix][iy]
            if stone is not None:
                if emotion is not None:
                    stone.set_emotion(emotion)
                if direction is not None:
                    stone.set_direction(direction)
            else:
                raise RuntimeError(f"No stone at position ({x}, {y}) to set state")
        else:
            raise IndexError(f"Position ({x}, {y}) is out of bounds")

class CANInterface:
    def __init__(self, channel='can0', bustype='socketcan'):
        self.emogo = None
        self.bus = can.interface.Bus(channel=channel, bustype=bustype)
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True  # Daemon thread
        self.receive_thread.start()

    # CANメッセージを受信するメソッド
    def receive_messages(self):
        while True:
            message = self.bus.recv()
            if message is not None:
                can_id = message.arbitration_id
                data = message.data
                self.process_message(can_id, data)

    # メッセージを処理するメソッド
    def process_message(self, can_id, data):
        # CAN ID から石の位置を取得
        if (can_id & 0xF00) == 0x600:
            x = (can_id & 0x0F0) >> 4
            y = can_id & 0x00F
            # データの解釈
            action = data[0]
            if action == 0:  # 取り除かれた
                self.emogo.handle_stone_removed(x, y)
            elif action == 1:  # 置かれた
                self.emogo.handle_stone_placed(x, y)
            elif action == 2:  # タップされた
                self.emogo.handle_stone_tapped(x, y)
            else:
                print(f"Unknown action: {action}")
        else:
            print(f"Unknown CAN ID: 0x{can_id:X}")

    # メッセージを送信するメソッド
    def send_message(self, can_id, data):
        message = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
        try:
            self.bus.send(message)
            # メッセージ内容を表示します
            data_bytes = ' '.join(f"{byte:02X}" for byte in data)
            print(f"{can_id:03X}#{data_bytes}")
        except can.CanError as e:
            print(f"Error sending CAN message: {e}")

    # Emogo インスタンスを設定するメソッド
    def set_emogo(self, emogo):
        self.emogo = emogo

class Emogo:
    def __init__(self, board_size_n=9, board_size_m=9):
        self.board = Board(board_size_n, board_size_m)
        self.can_interface = CANInterface()
        self.current_player = 'black'  # 黒石が先攻
        self.game_over = False
        self.waiting_for_dead_stones_removal = False  # 死に石の除去待ちフラグ
        self.dead_stones_list = []  # 死に石のリスト
        self.can_interface.set_emogo(self)  # CANInterfaceにEmogoのインスタンスを設定
        self.consecutive_passes = 0  # 連続パス回数
        self.input_thread = threading.Thread(target=self.handle_keyboard_input)
        self.input_thread.daemon = True  # Daemon thread
        self.input_thread.start()

    # ゲームを開始するメソッド
    def start_game(self):
        print("Game started! Black goes first.")
        self.game_thread = threading.Thread(target=self.game_loop)
        self.game_thread.daemon = True  # Daemon thread
        self.game_thread.start()

    # ゲームループ
    def game_loop(self):
        while not self.game_over:
            time.sleep(0.1)  # 100ms 待機

    # キーボード入力を処理するメソッド
    def handle_keyboard_input(self):
        while not self.game_over:
            user_input = input()
            if user_input.lower() == 'pass':
                self.handle_pass()
            elif user_input.lower() == 'quit':
                print("Game terminated by user.")
                self.game_over = True
                sys.exit()
            else:
                print("Unknown command. Type 'pass' to pass your turn or 'quit' to exit.")

    # パスを処理するメソッド
    def handle_pass(self):
        if self.waiting_for_dead_stones_removal:
            print("Cannot pass while waiting for dead stones to be removed.")
            return

        print(f"{self.current_player.capitalize()} passed.")
        self.consecutive_passes += 1
        if self.consecutive_passes >= 2:
            print("Both players have passed consecutively. The game is over.")
            self.game_over = True
            self.calculate_final_score()
        else:
            self.switch_player()

    # 石が置かれたことを処理するメソッド
    def handle_stone_placed(self, x, y):
        if self.game_over:
            print("Game is over. No more moves can be made.")
            return

        try:
            if self.waiting_for_dead_stones_removal:
                # 死に石除去待ちの場合、新しい石は死に石とする
                self.board.place_stone(x, y, self.current_player)
                # 直接その石の状態を変更
                self.board.set_stone_state(x, y, emotion='dead')
                # 追加された石を死に石リストに追加
                self.dead_stones_list.append((x, y))
                # 更新した石の状態を送信
                stone = self.board.get_stone(x, y)
                stone_info = {
                    'x': x,
                    'y': y,
                    'color': stone.get_color(),
                    'emotion': stone.get_emotion(),
                    'direction': stone.get_direction()
                }
                self.send_stone_update(stone_info)
                self.display_board(self.board)
                print(f"Stone placed at ({x}, {y}) is immediately dead.")
            else:
                color = self.current_player
                self.board.place_stone(x, y, color)
                self.update_board_state()
                self.display_board(self.board)
                print(f"{self.current_player.capitalize()} placed a stone at ({x}, {y}).")
                self.consecutive_passes = 0  # パス回数をリセット
                self.check_for_dead_stones()
                if not self.waiting_for_dead_stones_removal:
                    self.switch_player()
        except Exception as e:
            print(f"Error: {e}")

    # 石が取り除かれたことを処理するメソッド
    def handle_stone_removed(self, x, y):
        try:
            self.board.remove_stone(x, y)
            # 石が取り除かれたら、死に石リストから削除
            if (x, y) in self.dead_stones_list:
                self.dead_stones_list.remove((x, y))
            self.display_board(self.board)
            print(f"Stone at ({x}, {y}) was removed.")
            # 死に石リストが空か確認
            if not self.dead_stones_list:
                self.waiting_for_dead_stones_removal = False
                print("All dead stones have been removed. Game resumes.")
                self.switch_player()
            else:
                # まだ死に石が残っている場合、リストを表示
                print("Please remove the remaining dead stones:")
                for x_remain, y_remain in self.dead_stones_list:
                    print(f"- Stone at ({x_remain}, {y_remain})")
        except Exception as e:
            print(f"Error: {e}")

    # 石がタップされたことを処理するメソッド
    def handle_stone_tapped(self, x, y):
        try:
            print(f"Stone at ({x}, {y}) was tapped.")
            connected_stones = self.board.get_connect(x, y)
            if connected_stones:
                # タップされた石と連絡する全ての石にメッセージを送信
                for stone_x, stone_y in connected_stones:
                    can_id = 0x400 | (stone_x << 4) | stone_y
                    data = [0x02, 0xFF]
                    self.can_interface.send_message(can_id, data)
                # 0.5秒待機してから全石に対してメッセージを送信
                def blink_stones():
                    for _ in range(3):
                        time.sleep(0.5)
                        # 全石に対してメッセージを送信（ブロードキャスト）
                        can_id = 0x1FF
                        data_on = [0x03, 0xFF]
                        data_off = [0x03, 0x00]
                        self.can_interface.send_message(can_id, data_on)
                        time.sleep(0.5)
                        self.can_interface.send_message(can_id, data_off)
                    # 最後に連絡する各石にメッセージを送信
                    for stone_x, stone_y in connected_stones:
                        can_id = 0x400 | (stone_x << 4) | stone_y
                        data = [0x02, 0x00]
                        self.can_interface.send_message(can_id, data)
                # 点滅処理を別スレッドで実行
                threading.Thread(target=blink_stones).start()
            else:
                print(f"No connected stones found for ({x}, {y})")
        except Exception as e:
            print(f"Error handling stone tap: {e}")

    # 死に石があるかチェックし、処理を行う
    def check_for_dead_stones(self):
        dead_stones = self.get_dead_stones()
        if dead_stones:
            self.waiting_for_dead_stones_removal = True
            self.dead_stones_list = dead_stones.copy()
            print("Dead stones detected. Please remove the following stones:")
            for x, y in dead_stones:
                print(f"- Stone at ({x}, {y})")
        else:
            self.waiting_for_dead_stones_removal = False
            self.dead_stones_list = []

    # 死に石のリストを取得する
    def get_dead_stones(self):
        dead_stones = []
        board_state = self.board.get_board_state()
        for stone_info in board_state:
            if stone_info['emotion'] == Stone.EMOTION_VALUES['dead']:
                dead_stones.append((stone_info['x'], stone_info['y']))
        return dead_stones

    # ボードの状態を更新し、各石に通知するメソッド
    def update_board_state(self):
        # Boardの状態を更新（感情などの再計算はBoard内で行われる）
        stone_counts = self.board.stone_counts()
        print(f"Black stones: {stone_counts['black']}, White stones: {stone_counts['white']}")

        # 各石に状態を通知
        board_state = self.board.get_board_state()
        for stone_info in board_state:
            self.send_stone_update(stone_info)

    # 石に状態を送信するメソッド
    def send_stone_update(self, stone_info):
        can_id = 0x400 | (stone_info['x'] << 4) | stone_info['y']
        command = 1  # 状態変更の命令コードは1
        color = stone_info['color']
        emotion = stone_info['emotion']
        direction = stone_info['direction']
        direction_high = (direction >> 8) & 0xFF
        direction_low = direction & 0xFF
        data = [
            command & 0xFF,
            color & 0xFF,
            emotion & 0xFF,
            direction_high,
            direction_low
        ]
        self.can_interface.send_message(can_id, data)

    # プレイヤーを交代するメソッド
    def switch_player(self):
        self.current_player = 'white' if self.current_player == 'black' else 'black'
        print(f"Now it's {self.current_player.capitalize()}'s turn.")

    # 最終スコアを計算するメソッド（簡易的な実装）
    def calculate_final_score(self):
        stone_counts = self.board.stone_counts()
        print(f"Final Score:")
        print(f"Black stones: {stone_counts['black']}")
        print(f"White stones: {stone_counts['white']}")
        if stone_counts['black'] > stone_counts['white']:
            print("Black wins!")
        elif stone_counts['white'] > stone_counts['black']:
            print("White wins!")
        else:
            print("It's a tie!")

    # 碁盤の状態を表示するメソッド
    def display_board(self, board):
        for x in range(1, board.n + 1):
            row = []
            for y in range(1, board.m + 1):
                stone = board.get_stone(x, y)
                if stone is None:
                    row.append('.')
                else:
                    emotion = stone.get_emotion()
                    color = stone.get_color()
                    if emotion == Stone.EMOTION_VALUES['dead']:
                        symbol = 'X' if color == Stone.COLOR_VALUES['black'] else 'x'
                    elif emotion == Stone.EMOTION_VALUES['defensive']:
                        symbol = 'D' if color == Stone.COLOR_VALUES['black'] else 'd'
                    elif emotion == Stone.EMOTION_VALUES['offensive']:
                        symbol = 'O' if color == Stone.COLOR_VALUES['black'] else 'o'
                    else:  # normal
                        symbol = '○' if color == Stone.COLOR_VALUES['black'] else '●'
                    row.append(symbol)
            print(' '.join(row))
        print()  # 改行

# ゲームを開始
if __name__ == "__main__":
    game = Emogo(5, 5)
    game.start_game()

    # スクリプトを終了しないように待機
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Game terminated.")
