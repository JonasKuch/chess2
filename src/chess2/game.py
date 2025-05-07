'''
this module handles metadata, like checkmate, or which player is to turn and implements the final game loop
'''


from chess2.board import Board
from chess2 import Color, Action
from chess2.gui import GameLoop
from chess2.gui import StartScreen, EndScreen
from chess2.move import Move
from chess2.bot import MoveGenerator
import pygame
import time



class Game():
    def __init__(self, in_gui = True, width = 700, height = 800, with_takeback = True):
        self.board = Board()
        self.gui = GameLoop(width, height, self.board, self.on_undo, self.on_redo, self.on_give_up)
        self.move = Move()
        self.start_screen = StartScreen(self.gui.window)
        self.end_screen = EndScreen(self.gui.window, self.start_screen)
        self.bot = MoveGenerator("src/chess2/bot/saved_models/model_64_30_1e-3_1e-4_23.pth")
        self.in_gui = in_gui
        self.action = None
        self.with_takeback = with_takeback
        self.running = True
        self.message = None


    def translate_input(self, input_string):
        '''
        könnte man hier noch einfügen um make_move ein bisschen übersichtlicher zu gestalten
        '''
        pass


    def make_move(self):
        move_dict = {
            'a' : 0,
            'b' : 1,
            'c' : 2,
            'd' : 3,
            'e' : 4,
            'f' : 5,
            'g' : 6,
            'h' : 7,
            '1' : 0,
            '2' : 1,
            '3' : 2,
            '4' : 3,
            '5' : 4,
            '6' : 5,
            '7' : 6,
            '8' : 7
        }

        while True:
            move_str = input("Encode your move coordinates like this: a2a4 and press Enter when you are done\n")

            if move_str == "quit":
                return False
            
            if len(move_str) == 4:
                try:
                    x_old, y_old = move_dict[move_str[0]], move_dict[move_str[1]]
                    new_pos = move_dict[move_str[2]], move_dict[move_str[3]]
                except:
                    print("Not the right format")
                    continue
            else:
                print("Not the right format")
                continue

            if not self.board.grid[y_old][x_old] == None:
                if self.board.grid[y_old][x_old]._color == self.board.turn:
                    if new_pos in self.board.grid[y_old][x_old].get_legal_moves(): # eigentlich muss ich das hier nicht mehr checken, da ich das schon in der move() function der Piece Klasse checke
                        self.board.grid[y_old][x_old].move(new_pos)
                        break

            print('Not a legal move')

        return True
        

    def game_loop_terminal(self):
        self.start_game()
        while True:
            go_on = self.make_move()
            if not go_on:
                print("Game Quit")
                break
            self.board.update_grid()
            self.board.update_checks()
            self.swap_turns()
            self.board.print(self.board.turn)
            if self.board.check_if_mate(): 
                winning_color = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
                print(f"Check Mate! {winning_color.name} won!")
                break
    

    def start_game(self):
        self.board.initialize()
        if not self.in_gui: self.board.print(self.board.turn)
    

    def swap_turns(self, turn_board):
        if turn_board: time.sleep(0.5)
        self.board.turn = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE


    def on_undo(self):
        if not self.with_takeback:
            return None
        if self.move.move_num < 1:
            return None
        if self.start_screen.play_bot:
            self.move.move_num -= 2
        if not self.start_screen.play_bot:
            self.move.move_num -= 1
        other_board = self.move.load_board_state(self.move.move_num)
        self.board.load_state(other_board)
        self.move.move_cache[self.move.move_num] = self.board.clone()    # Wichtig, da sindt der nächste zug direkt auf das gerade initialisierte board angewendet werden würde bevor es gecached wird


    def on_redo(self):
        if self.move.move_num >= self.move.max_move:
            return None
        if self.start_screen.play_bot:
            self.move.move_num += 2
        if not self.start_screen.play_bot:
            self.move.move_num += 1
        other_board = self.move.move_cache[self.move.move_num]
        self.board.load_state(other_board)
        self.move.move_cache[self.move.move_num] = self.board.clone()    # Wichtig, da sindt der nächste zug direkt auf das gerade initialisierte board angewendet werden würde bevor es gecached wird


    def on_give_up(self):
        winning_color = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
        self.message = f"{self.board.turn.name} GAVE UP! {winning_color.name} WON!"
        self.swap_turns(None)
        self.running = False

    
    def check_for_end(self):
        if self.board.check_if_mate():
            winning_color = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
            self.message = f"CHECK MATE! {winning_color.name} WON!"
            self.running = False
            return True

        if any(count == 3 for count in self.move.repetition_counter.values()):
            self.message = "MOVE REPETITION! DRAW!"
            self.running = False
            return True


        if self.board.halfmove_clock >= 100:
            self.message = "50 MOVE RULE DRAW"
            self.running = False
            return True

        if self.board.get_possible_moves_of_all_pieces(self.board.turn) == []:
            self.message = "STALEMATE"
            self.running = False
            return True
        
        return False
    

    def game_loop_gui(self, play_bot , turn_board, show_legal_moves, side = Color.WHITE, with_takeback = True):
        self.with_takeback = with_takeback
        self.start_game()
        self.move.cache_board_state(self.board)

        while self.running:
            if not play_bot or self.board.turn == side:
                action = self.gui.gameloop(turn = self.board.turn, side = self.board.turn if turn_board else side, show_legal_moves = show_legal_moves)

                if action == Action.MOVED or action == Action.PROMOTE:
                    self.swap_turns(turn_board)
                    self.move.cache_board_state(self.board)
                    self.check_for_end()

            bot_side = Color.BLACK if side == Color.WHITE else Color.WHITE
            if play_bot and self.board.turn == bot_side and self.running:
                # self.board.load_state(self.bot.stockfish_move(bot_side, self.board))
                self.board.load_state(self.bot.model_move(bot_side, self.board))
                self.swap_turns(turn_board)
                self.move.cache_board_state(self.board)
                self.check_for_end()

            self.gui.tick(60)


    def reset_all_properties(self):
        self.board.__init__()
        self.move.__init__()
        self.running = True
        self.message = None
        self.start_screen.running = True
        self.end_screen.running = True


    def play(self):
        while True:            
            self.start_screen.start_screen_loop()
            self.game_loop_gui(play_bot=self.start_screen.play_bot, 
                                         turn_board=self.start_screen.flip_board, 
                                         show_legal_moves=self.start_screen.show_moves,
                                         side=self.start_screen.chosen_color,
                                         with_takeback=self.start_screen.with_takeback)
            self.end_screen.end_screen_loop(self.message, self.board)
            self.reset_all_properties()