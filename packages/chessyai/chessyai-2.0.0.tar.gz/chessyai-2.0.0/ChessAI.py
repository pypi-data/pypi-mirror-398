"""
Chess AI using Minimax algorithm with Alpha-Beta Pruning
"""

import random

# Figurenwerte
PIECE_VALUES = {
    "K": 0,  # König ist unendlich wertvoll, aber wir wollen ihn nicht bewerten
    "Q": 900,  # Dame
    "R": 500,  # Turm
    "B": 330,  # Läufer
    "N": 320,  # Springer
    "p": 100,  # Bauer
}

# Positionstabellen für bessere Stellungsbewertung
# Bauern sollten vorrücken
PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# Springer sind besser im Zentrum
KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

# Läufer
BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

# Turm
ROOK_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]

# Dame
QUEEN_TABLE = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]

# König Mittelspiel - sollte in der Ecke bleiben
KING_MIDDLE_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]

POSITION_TABLES = {
    "p": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
    "K": KING_MIDDLE_TABLE,
}

CHECKMATE = 100000
STALEMATE = 0
DEPTH = 3  # Suchtiefe

# Globale Variablen für Visualisierung
ai_analysis = {
    "moves_evaluated": [],  # Liste von (move, score) Tupeln
    "nodes_searched": 0,  # Anzahl durchsuchter Knoten
    "pruned_branches": 0,  # Anzahl abgeschnittener Zweige
    "best_line": [],  # Beste Zugfolge
    "position_score": 0,  # Aktuelle Stellungsbewertung
    "depth": DEPTH,  # Suchtiefe
    "material_balance": {},  # Materialbalance
    "search_tree": [],  # Suchbaum für Visualisierung
}


def get_analysis():
    """Gibt die aktuelle Analyse zurück"""
    return ai_analysis


def reset_analysis():
    """Setzt die Analyse zurück"""
    global ai_analysis
    ai_analysis = {
        "moves_evaluated": [],
        "nodes_searched": 0,
        "pruned_branches": 0,
        "best_line": [],
        "position_score": 0,
        "depth": DEPTH,
        "material_balance": {},
        "search_tree": [],
    }


def calculate_material_balance(gs):
    """Berechnet die Materialbalance"""
    balance = {"w": {}, "b": {}}
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != "--":
                color = piece[0]
                piece_type = piece[1]
                if piece_type not in balance[color]:
                    balance[color][piece_type] = 0
                balance[color][piece_type] += 1
    return balance


def find_best_move(gs, valid_moves):
    """Findet den besten Zug mit Minimax und Alpha-Beta Pruning"""
    global next_move, ai_analysis
    next_move = None
    reset_analysis()

    # Materialbalance berechnen
    ai_analysis["material_balance"] = calculate_material_balance(gs)
    ai_analysis["position_score"] = score_board(gs)

    random.shuffle(valid_moves)  # Für Varianz bei gleich guten Zügen

    # Alle Züge mit ihren Scores sammeln
    move_scores = []

    for move in valid_moves:
        gs.make_move(move)
        next_moves = gs.get_valid_moves()
        score = -find_move_negamax_alpha_beta(
            gs,
            next_moves,
            DEPTH - 1,
            -CHECKMATE,
            CHECKMATE,
            -1 if gs.whiteToMove else 1,
            [move],
        )
        gs.undo_move()
        move_scores.append((move, score))

    # Nach Score sortieren
    move_scores.sort(key=lambda x: x[1], reverse=True)
    ai_analysis["moves_evaluated"] = move_scores[:10]  # Top 10 Züge

    if move_scores:
        next_move = move_scores[0][0]
        ai_analysis["best_line"] = [next_move]

    return next_move


def find_move_negamax_alpha_beta(
    gs, valid_moves, depth, alpha, beta, turn_multiplier, current_line=None
):
    """Negamax mit Alpha-Beta Pruning"""
    global ai_analysis

    ai_analysis["nodes_searched"] += 1

    if depth == 0:
        return turn_multiplier * score_board(gs)

    max_score = -CHECKMATE
    for move in valid_moves:
        gs.make_move(move)
        next_moves = gs.get_valid_moves()

        new_line = (current_line or []) + [move]
        score = -find_move_negamax_alpha_beta(
            gs, next_moves, depth - 1, -beta, -alpha, -turn_multiplier, new_line
        )

        if score > max_score:
            max_score = score
            if depth == DEPTH - 1 and current_line:
                ai_analysis["best_line"] = current_line + [move]

        gs.undo_move()

        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            ai_analysis["pruned_branches"] += 1
            break

    return max_score


def score_board(gs):
    """Bewertet die aktuelle Stellung"""
    if gs.checkmate:
        if gs.whiteToMove:
            return -CHECKMATE  # Schwarz gewinnt
        else:
            return CHECKMATE  # Weiß gewinnt
    elif gs.stalemate:
        return STALEMATE

    score = 0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != "--":
                # Positionsbonus
                piece_position_score = 0
                piece_type = piece[1]

                if piece_type in POSITION_TABLES:
                    if piece[0] == "w":
                        piece_position_score = POSITION_TABLES[piece_type][r][c]
                    else:
                        # Für Schwarz die Tabelle spiegeln
                        piece_position_score = POSITION_TABLES[piece_type][7 - r][c]

                if piece[0] == "w":
                    score += PIECE_VALUES[piece_type] + piece_position_score
                else:
                    score -= PIECE_VALUES[piece_type] + piece_position_score

    return score


def find_random_move(valid_moves):
    """Wählt einen zufälligen Zug (Fallback)"""
    return random.choice(valid_moves) if valid_moves else None
