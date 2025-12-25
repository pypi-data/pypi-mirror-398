"""This class is responsible for storing the actual state,
it determines which moves are valid and it's logging all moves"""


class GameState:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]

        self.whiteToMove = True
        self.moveLog = []

        # Königspositionen verfolgen
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)

        # Für Rochade
        self.whiteKingMoved = False
        self.blackKingMoved = False
        self.whiteRooksMoved = [False, False]  # [links, rechts]
        self.blackRooksMoved = [False, False]  # [links, rechts]

        # Für En Passant
        self.enPassantPossible = ()  # Koordinaten wo en passant möglich ist

        # Schach/Matt/Patt Status
        self.checkmate = False
        self.stalemate = False
        self.inCheck = False

        # Mapping für Figurenbewegungen
        self.moveFunctions = {
            "p": self.get_pawn_moves,
            "R": self.get_rook_moves,
            "N": self.get_knight_moves,
            "B": self.get_bishop_moves,
            "Q": self.get_queen_moves,
            "K": self.get_king_moves,
        }

    def make_move(self, move):
        """Führt einen Zug aus"""
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove

        # Königsposition aktualisieren
        if move.piece_moved == "wK":
            self.whiteKingLocation = (move.end_row, move.end_col)
            self.whiteKingMoved = True
        elif move.piece_moved == "bK":
            self.blackKingLocation = (move.end_row, move.end_col)
            self.blackKingMoved = True

        # Turm-Bewegung verfolgen für Rochade
        if move.piece_moved == "wR":
            if move.start_row == 7 and move.start_col == 0:
                self.whiteRooksMoved[0] = True
            elif move.start_row == 7 and move.start_col == 7:
                self.whiteRooksMoved[1] = True
        elif move.piece_moved == "bR":
            if move.start_row == 0 and move.start_col == 0:
                self.blackRooksMoved[0] = True
            elif move.start_row == 0 and move.start_col == 7:
                self.blackRooksMoved[1] = True

        # Bauernumwandlung
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = (
                move.piece_moved[0] + move.promotion_piece
            )

        # En Passant
        if move.is_enpassant_move:
            self.board[move.start_row][
                move.end_col
            ] = "--"  # Gegnerischen Bauern entfernen

        # En Passant Möglichkeit aktualisieren
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:
            self.enPassantPossible = (
                (move.start_row + move.end_row) // 2,
                move.start_col,
            )
        else:
            self.enPassantPossible = ()

        # Rochade ausführen
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # Kurze Rochade
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1
                ]
                self.board[move.end_row][move.end_col + 1] = "--"
            else:  # Lange Rochade
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2
                ]
                self.board[move.end_row][move.end_col - 2] = "--"

    def undo_move(self):
        """Macht den letzten Zug rückgängig"""
        if len(self.moveLog) == 0:
            return

        move = self.moveLog.pop()
        self.board[move.start_row][move.start_col] = move.piece_moved
        self.board[move.end_row][move.end_col] = move.piece_captured
        self.whiteToMove = not self.whiteToMove

        # Königsposition zurücksetzen
        if move.piece_moved == "wK":
            self.whiteKingLocation = (move.start_row, move.start_col)
        elif move.piece_moved == "bK":
            self.blackKingLocation = (move.start_row, move.start_col)

        # En Passant rückgängig
        if move.is_enpassant_move:
            self.board[move.end_row][move.end_col] = "--"
            self.board[move.start_row][move.end_col] = move.piece_captured
            self.enPassantPossible = (move.end_row, move.end_col)

        # Rochade rückgängig
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # Kurze Rochade
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 1
                ]
                self.board[move.end_row][move.end_col - 1] = "--"
            else:  # Lange Rochade
                self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][
                    move.end_col + 1
                ]
                self.board[move.end_row][move.end_col + 1] = "--"

        # Status zurücksetzen
        self.checkmate = False
        self.stalemate = False

    def get_valid_moves(self):
        """Gibt alle gültigen Züge zurück (berücksichtigt Schach)"""
        temp_enpassant = self.enPassantPossible
        moves = self.get_all_possible_moves()

        # Rochade-Züge hinzufügen
        if self.whiteToMove:
            self.get_castle_moves(
                self.whiteKingLocation[0], self.whiteKingLocation[1], moves
            )
        else:
            self.get_castle_moves(
                self.blackKingLocation[0], self.blackKingLocation[1], moves
            )

        # Züge filtern die den König im Schach lassen würden
        for i in range(len(moves) - 1, -1, -1):
            self.make_move(moves[i])
            self.whiteToMove = not self.whiteToMove
            if self.is_in_check():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undo_move()

        # Schachmatt oder Patt prüfen
        if len(moves) == 0:
            if self.is_in_check():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.enPassantPossible = temp_enpassant
        return moves

    def is_in_check(self):
        """Prüft ob der aktuelle Spieler im Schach steht"""
        if self.whiteToMove:
            return self.square_under_attack(
                self.whiteKingLocation[0], self.whiteKingLocation[1]
            )
        else:
            return self.square_under_attack(
                self.blackKingLocation[0], self.blackKingLocation[1]
            )

    def square_under_attack(self, r, c):
        """Prüft ob ein Feld vom Gegner angegriffen wird"""
        self.whiteToMove = not self.whiteToMove
        opp_moves = self.get_all_possible_moves()
        self.whiteToMove = not self.whiteToMove
        for move in opp_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False

    def get_all_possible_moves(self):
        """Gibt alle möglichen Züge zurück (ohne Schach-Prüfung)"""
        moves = []
        for r in range(8):
            for c in range(8):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (
                    turn == "b" and not self.whiteToMove
                ):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)
        return moves

    def get_pawn_moves(self, r, c, moves):
        """Generiert alle Bauernzüge"""
        if self.whiteToMove:  # Weißer Bauer
            if self.board[r - 1][c] == "--":  # Ein Feld vorwärts
                moves.append(Move((r, c), (r - 1, c), self.board))
                if r == 6 and self.board[r - 2][c] == "--":  # Zwei Felder vom Start
                    moves.append(Move((r, c), (r - 2, c), self.board))
            # Schlagen
            if c - 1 >= 0:
                if self.board[r - 1][c - 1][0] == "b":
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))
                elif (r - 1, c - 1) == self.enPassantPossible:
                    moves.append(
                        Move((r, c), (r - 1, c - 1), self.board, is_enpassant=True)
                    )
            if c + 1 <= 7:
                if self.board[r - 1][c + 1][0] == "b":
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))
                elif (r - 1, c + 1) == self.enPassantPossible:
                    moves.append(
                        Move((r, c), (r - 1, c + 1), self.board, is_enpassant=True)
                    )
        else:  # Schwarzer Bauer
            if self.board[r + 1][c] == "--":
                moves.append(Move((r, c), (r + 1, c), self.board))
                if r == 1 and self.board[r + 2][c] == "--":
                    moves.append(Move((r, c), (r + 2, c), self.board))
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == "w":
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))
                elif (r + 1, c - 1) == self.enPassantPossible:
                    moves.append(
                        Move((r, c), (r + 1, c - 1), self.board, is_enpassant=True)
                    )
            if c + 1 <= 7:
                if self.board[r + 1][c + 1][0] == "w":
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
                elif (r + 1, c + 1) == self.enPassantPossible:
                    moves.append(
                        Move((r, c), (r + 1, c + 1), self.board, is_enpassant=True)
                    )

    def get_rook_moves(self, r, c, moves):
        """Generiert alle Turmzüge"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        enemy_color = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_knight_moves(self, r, c, moves):
        """Generiert alle Springerzüge"""
        knight_moves = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]
        ally_color = "w" if self.whiteToMove else "b"
        for m in knight_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_bishop_moves(self, r, c, moves):
        """Generiert alle Läuferzüge"""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        enemy_color = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = r + d[0] * i
                end_col = c + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((r, c), (end_row, end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_queen_moves(self, r, c, moves):
        """Generiert alle Damenzüge (Kombination aus Turm und Läufer)"""
        self.get_rook_moves(r, c, moves)
        self.get_bishop_moves(r, c, moves)

    def get_king_moves(self, r, c, moves):
        """Generiert alle Königszüge"""
        king_moves = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]
        ally_color = "w" if self.whiteToMove else "b"
        for m in king_moves:
            end_row = r + m[0]
            end_col = c + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((r, c), (end_row, end_col), self.board))

    def get_castle_moves(self, r, c, moves):
        """Generiert Rochade-Züge"""
        if self.square_under_attack(r, c):
            return  # Kann nicht rochieren wenn im Schach

        if self.whiteToMove:
            if not self.whiteKingMoved:
                # Kurze Rochade (Königsseite)
                if not self.whiteRooksMoved[1]:
                    if self.board[7][5] == "--" and self.board[7][6] == "--":
                        if not self.square_under_attack(
                            7, 5
                        ) and not self.square_under_attack(7, 6):
                            moves.append(
                                Move((7, 4), (7, 6), self.board, is_castle=True)
                            )
                # Lange Rochade (Damenseite)
                if not self.whiteRooksMoved[0]:
                    if (
                        self.board[7][3] == "--"
                        and self.board[7][2] == "--"
                        and self.board[7][1] == "--"
                    ):
                        if not self.square_under_attack(
                            7, 3
                        ) and not self.square_under_attack(7, 2):
                            moves.append(
                                Move((7, 4), (7, 2), self.board, is_castle=True)
                            )
        else:
            if not self.blackKingMoved:
                # Kurze Rochade
                if not self.blackRooksMoved[1]:
                    if self.board[0][5] == "--" and self.board[0][6] == "--":
                        if not self.square_under_attack(
                            0, 5
                        ) and not self.square_under_attack(0, 6):
                            moves.append(
                                Move((0, 4), (0, 6), self.board, is_castle=True)
                            )
                # Lange Rochade
                if not self.blackRooksMoved[0]:
                    if (
                        self.board[0][3] == "--"
                        and self.board[0][2] == "--"
                        and self.board[0][1] == "--"
                    ):
                        if not self.square_under_attack(
                            0, 3
                        ) and not self.square_under_attack(0, 2):
                            moves.append(
                                Move((0, 4), (0, 2), self.board, is_castle=True)
                            )


class Move:
    # map keys to values
    # key : value
    # We need this to get the correct chess notation for out moves
    ranks_to_row = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_row.items()}

    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_sq, end_sq, board, is_enpassant=False, is_castle=False):
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.board = board
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        # Bauernumwandlung
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
            self.piece_moved == "bp" and self.end_row == 7
        )
        self.promotion_piece = "Q"  # Standard: Dame

        # En Passant
        self.is_enpassant_move = is_enpassant
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"

        # Rochade
        self.is_castle_move = is_castle

        # Eindeutige ID für Zugvergleich
        self.moveID = (
            self.start_row * 1000
            + self.start_col * 100
            + self.end_row * 10
            + self.end_col
        )

    def __eq__(self, other):
        """Vergleicht zwei Züge"""
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_col) + self.get_rank_file(self.end_row, self.end_col)

    def get_rank_file(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]
