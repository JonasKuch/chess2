from chess2.gui import Window
from chess2.board import Board
from chess2 import Color
from chess2.pieces import Pawn
import pygame
from chess2 import Action


class EventHandler():
    def __init__(self, window:Window, board:Board):
        self.selected_pos = None
        self.selected_piece = None
        self.valid_moves = None
        self.square_width = 0.8*window.width / 8
        self.board = board
        self.offset_x = (window.width - self.square_width*8)/2
        self.offset_y = (window.height - self.square_width*8)/2
        self.pawn_position = None
    

    def quit_game(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
    

    def _reset_attributes(self):
        self.selected_pos = None
        self.selected_piece = None
        self.valid_moves = None
        self.pawn_position = None


    def _convert_mouse_position(self, position, side): ####### evtl für Color.BLACK muss y nicht invertiert werden
        x, y = position
        if side == Color.WHITE:
            x_board = int((x-self.offset_x) / self.square_width)
            y_board = 7 - int((y-self.offset_y) / self.square_width)
        if side == Color.BLACK:
            x_board = 7 - int((x-self.offset_x) / self.square_width)
            y_board = int((y-self.offset_y) / self.square_width)

        if not self.board.in_bounds((x_board, y_board)):
            return None
        
        return x_board, y_board
        

    def handle_board_input(self, event, turn_color, side):
        # 1) Only handle clicks
        if event.type != pygame.MOUSEBUTTONDOWN:
            return Action.IGNORED
        
        # 2) Convert mouse → board coords (and reset if off-board)
        board_pos = self._convert_mouse_position(event.pos, side)
        if board_pos is None:
            self._reset_attributes()
            return Action.IGNORED
        
        x_board, y_board = board_pos
        selected_square = self.board.grid[y_board][x_board]

        # 3) No piece selected yet → try to select
        if self.selected_pos is None:
            if selected_square is None or selected_square._color != turn_color:
                return Action.IGNORED
            self.selected_pos = x_board, y_board
            self.selected_piece = selected_square
            self.valid_moves = selected_square.get_legal_moves()
            return Action.SELECTED
        
        # 4) A piece is already selected → attempt move
        x_selected, y_selected = self.selected_pos
        if (x_board, y_board) in self.valid_moves:
            self.board.grid[y_selected][x_selected].move((x_board, y_board))
            self._reset_attributes()
            if isinstance(self.board.grid[y_selected][x_selected], Pawn) and y_board in [0, 7]:
                self.board.grid[y_selected][x_selected]._captured = True
                self.pawn_position = board_pos
                return Action.PROMOTE
            return Action.MOVED
        
        # 5) Click wasn’t a legal move → maybe re-select another of yours
        if selected_square and selected_square._color == turn_color:
            self.selected_pos = x_board, y_board
            self.selected_piece = selected_square
            self.valid_moves = selected_square.get_legal_moves()
            return Action.SELECTED
        
        # 6) Otherwise, clear selection
        self._reset_attributes()
        return Action.IGNORED
    

    def handle_buttons_game(self, buttons, event):
        for button in buttons:
            button.handle_event(event)
    

    def handle(self, event, turn_color, side, buttons):
        self.quit_game(event)
        self.handle_buttons_game(buttons, event)
        action = self.handle_board_input(event, turn_color, side)
        return action