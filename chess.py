import tkinter as tk
from tkinter import messagebox
import copy
import random

# Unicode Chess Pieces
PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

PIECE_VALUES = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}

# Piece-Square Tables (mirrored from chess.html)
PST = {
    'p': [0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10, 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5, 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0],
    'n': [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30, -30,5,15,20,20,15,5,-30, -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30, -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50],
    'b': [-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,10,10,10,10,0,-10, -10,5,5,10,10,5,5,-10, -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10, -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20],
    'r': [0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0],
    'q': [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10, -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10, -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20],
    'k': [-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30, -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]
}

class ChessGame:
    def __init__(self):
        self.board = [
            ['r','n','b','q','k','b','n','r'],
            ['p','p','p','p','p','p','p','p'],
            [None]*8, [None]*8, [None]*8, [None]*8,
            ['P','P','P','P','P','P','P','P'],
            ['R','N','B','Q','K','B','N','R']
        ]
        self.turn = 'w'
        self.castling_rights = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant_target = None

    def get_color(self, piece):
        if not piece: return None
        return 'w' if piece.isupper() else 'b'

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_pseudo_legal_moves(self, board, r, c, cr, ep):
        piece = board[r][c]
        if not piece: return []
        color = self.get_color(piece)
        type = piece.lower()
        moves = []

        def add_move(tr, tc):
            if self.in_bounds(tr, tc):
                target = board[tr][tc]
                if not target or self.get_color(target) != color:
                    moves.append(((r, c), (tr, tc)))

        if type == 'p':
            dir = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            # Forward
            if self.in_bounds(r+dir, c) and not board[r+dir][c]:
                moves.append(((r, c), (r+dir, c)))
                if r == start_row and not board[r+2*dir][c]:
                    moves.append(((r, c), (r+2*dir, c)))
            # Captures
            for dc in [-1, 1]:
                if self.in_bounds(r+dir, c+dc):
                    target = board[r+dir][c+dc]
                    if target and self.get_color(target) != color:
                        moves.append(((r, c), (r+dir, c+dc)))
                    if ep == (r+dir, c+dc):
                        moves.append(((r, c), (r+dir, c+dc)))
        elif type == 'n':
            offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
            for dr, dc in offsets: add_move(r+dr, c+dc)
        elif type == 'k':
            offsets = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for dr, dc in offsets: add_move(r+dr, c+dc)
            # Castling
            row = 7 if color == 'w' else 0
            if r == row and c == 4:
                if cr[color+'K'] and not board[row][5] and not board[row][6] and board[row][7] == ('R' if color=='w' else 'r'):
                    moves.append(((r, c), (row, 6)))
                if cr[color+'Q'] and not board[row][3] and not board[row][2] and not board[row][1] and board[row][0] == ('R' if color=='w' else 'r'):
                    moves.append(((r, c), (row, 2)))
        else:
            dirs = []
            if type in ['b', 'q']: dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if type in ['r', 'q']: dirs += [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, dc in dirs:
                tr, tc = r + dr, c + dc
                while self.in_bounds(tr, tc):
                    if not board[tr][tc]:
                        moves.append(((r, c), (tr, tc)))
                    else:
                        if self.get_color(board[tr][tc]) != color:
                            moves.append(((r, c), (tr, tc)))
                        break
                    tr, tc = tr + dr, tc + dc
        return moves

    def simulate_move(self, board, move):
        nb = [row[:] for row in board]
        (fr, fc), (tr, tc) = move
        piece = nb[fr][fc]
        nb[tr][tc] = piece
        nb[fr][fc] = None
        # Pawn promotion to Queen
        if piece.lower() == 'p' and (tr == 0 or tr == 7):
            nb[tr][tc] = 'Q' if piece.isupper() else 'q'
        return nb

    def find_king(self, board, color):
        k = 'K' if color == 'w' else 'k'
        for r in range(8):
            for c in range(8):
                if board[r][c] == k: return (r, c)
        return None

    def is_attacked(self, board, r, c, by_color):
        # Check every piece of the opponent
        opp_moves = []
        for fr in range(8):
            for fc in range(8):
                if board[fr][fc] and self.get_color(board[fr][fc]) == by_color:
                    # Use pseudo moves without recursion
                    piece = board[fr][fc]
                    type = piece.lower()
                    if type == 'p':
                        dir = 1 if by_color == 'w' else -1
                        if fr-dir == r and (fc-1 == c or fc+1 == c): return True
                    else:
                        for m_from, m_to in self.get_pseudo_legal_moves(board, fr, fc, {'wK':False,'wQ':False,'bK':False,'bQ':False}, None):
                            if m_to == (r, c): return True
        return False

    def is_in_check(self, board, color):
        kp = self.find_king(board, color)
        if not kp: return False
        return self.is_attacked(board, kp[0], kp[1], 'b' if color == 'w' else 'w')

    def get_legal_moves(self, board, color, cr, ep):
        legal = []
        for r in range(8):
            for c in range(8):
                if board[r][c] and self.get_color(board[r][c]) == color:
                    pseudo = self.get_pseudo_legal_moves(board, r, c, cr, ep)
                    for move in pseudo:
                        nb = self.simulate_move(board, move)
                        if not self.is_in_check(nb, color):
                            legal.append(move)
        return legal

class ChessAI:
    def evaluate(self, board):
        score = 0
        for r in range(8):
            for c in range(8):
                p = board[r][c]
                if p:
                    val = PIECE_VALUES[p.lower()]
                    pst_row = r if p.isupper() else 7 - r
                    pos_val = PST[p.lower()][pst_row * 8 + c]
                    if p.isupper(): score += val + pos_val
                    else: score -= val + pos_val
        return score

    def minimax(self, game, board, depth, alpha, beta, maximizing, cr, ep):
        color = 'w' if maximizing else 'b'
        moves = game.get_legal_moves(board, color, cr, ep)
        
        if depth == 0 or not moves:
            return self.evaluate(board)

        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                nb = game.simulate_move(board, move)
                eval = self.minimax(game, nb, depth-1, alpha, beta, False, cr, ep)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                nb = game.simulate_move(board, move)
                eval = self.minimax(game, nb, depth-1, alpha, beta, True, cr, ep)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Master - Python")
        self.game = ChessGame()
        self.ai = ChessAI()
        self.selected = None
        self.legal_moves = []
        
        self.canvas = tk.Canvas(root, width=560, height=560)
        self.canvas.pack(side=tk.LEFT, padx=20, pady=20)
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.side_panel = tk.Frame(root, width=200, bg="#272522")
        self.side_panel.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.status_label = tk.Label(self.side_panel, text="White's Turn", fg="white", bg="#272522", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=20)
        
        self.new_game_btn = tk.Button(self.side_panel, text="New Game", command=self.reset_game)
        self.new_game_btn.pack(pady=10)

        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#f0d9b5", "#b58863"]
        
        for r in range(8):
            for c in range(8):
                x1, y1 = c * 70, r * 70
                x2, y2 = x1 + 70, y1 + 70
                color = colors[(r + c) % 2]
                
                # Highlights
                if self.selected == (r, c):
                    color = "#f6f669"
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                
                # Draw pieces
                p = self.game.board[r][c]
                if p:
                    char = PIECES[p]
                    f_color = "white" if p.isupper() else "black"
                    self.canvas.create_text(x1+35, y1+35, text=char, font=("Arial", 44), fill=f_color)

                # Legal move dots
                for move in self.legal_moves:
                    if move[1] == (r, c):
                        self.canvas.create_oval(x1+25, y1+25, x2-25, y2-25, fill="rgba(0,0,0,0.2)", outline="")

    def on_click(self, event):
        if self.game.turn != 'w': return
        
        c, r = event.x // 70, event.y // 70
        if not (0 <= r < 8 and 0 <= c < 8): return

        clicked_move = next((m for m in self.legal_moves if m[1] == (r, c)), None)
        
        if clicked_move:
            self.execute_move(clicked_move)
            self.root.after(100, self.ai_turn)
        else:
            piece = self.game.board[r][c]
            if piece and self.game.get_color(piece) == 'w':
                self.selected = (r, c)
                self.legal_moves = [m for m in self.game.get_legal_moves(self.game.board, 'w', self.game.castling_rights, self.game.en_passant_target) if m[0] == (r, c)]
            else:
                self.selected = None
                self.legal_moves = []
        
        self.draw_board()

    def execute_move(self, move):
        (fr, fc), (tr, tc) = move
        piece = self.game.board[fr][fc]
        
        # Logic for special moves
        if piece.lower() == 'k':
            self.game.castling_rights[self.game.turn + 'K'] = False
            self.game.castling_rights[self.game.turn + 'Q'] = False
            # Move rook if castling
            if abs(fc - tc) == 2:
                rook_f = (fr, 7 if tc == 6 else 0)
                rook_t = (fr, 5 if tc == 6 else 3)
                self.game.board[rook_t[0]][rook_t[1]] = self.game.board[rook_f[0]][rook_f[1]]
                self.game.board[rook_f[0]][rook_f[1]] = None

        self.game.board = self.game.simulate_move(self.game.board, move)
        self.game.turn = 'b' if self.game.turn == 'w' else 'w'
        self.selected = None
        self.legal_moves = []
        self.status_label.config(text="AI is thinking..." if self.game.turn == 'b' else "White's Turn")
        self.draw_board()
        self.check_game_over()

    def ai_turn(self):
        moves = self.game.get_legal_moves(self.game.board, 'b', self.game.castling_rights, self.game.en_passant_target)
        if not moves: return

        best_move = None
        best_eval = float('inf')
        
        # Evaluate moves
        random.shuffle(moves)
        for move in moves:
            nb = self.game.simulate_move(self.game.board, move)
            score = self.ai.minimax(self.game, nb, 2, -float('inf'), float('inf'), True, self.game.castling_rights, self.game.en_passant_target)
            if score < best_eval:
                best_eval = score
                best_move = move
        
        if best_move:
            self.execute_move(best_move)

    def check_game_over(self):
        moves = self.game.get_legal_moves(self.game.board, self.game.turn, self.game.castling_rights, self.game.en_passant_target)
        if not moves:
            if self.game.is_in_check(self.game.board, self.game.turn):
                winner = "Black" if self.game.turn == 'w' else "White"
                messagebox.showinfo("Game Over", f"Checkmate! {winner} wins.")
            else:
                messagebox.showinfo("Game Over", "Stalemate! It's a draw.")
            self.reset_game()

    def reset_game(self):
        self.game = ChessGame()
        self.selected = None
        self.legal_moves = []
        self.status_label.config(text="White's Turn")
        self.draw_board()

if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#312e2b")
    gui = ChessGUI(root)
    root.mainloop()
