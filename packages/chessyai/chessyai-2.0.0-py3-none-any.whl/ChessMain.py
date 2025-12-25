"""
This file will be responsible for handling user input and displaying the current GameState object.
"""
import pygame as p
import ChessEngine
import ChessAI
import os
from datetime import datetime

WIDTH = HEIGHT = 513  # 512 x 512 px
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = HEIGHT
AI_PANEL_WIDTH = 300  # Breite des AI-Analyse-Panels
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 60  # Erhöht für flüssige Animationen
IMAGES = {}
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Farben
COLORS = [p.Color(232, 144, 5), p.Color(105, 20, 14)]
HIGHLIGHT_COLOR = p.Color(186, 202, 68)  # Grün für gültige Züge
SELECTED_COLOR = p.Color(255, 255, 0, 100)  # Gelb für ausgewählte Figur
LAST_MOVE_COLOR = p.Color(170, 162, 58)  # Letzter Zug
CHECK_COLOR = p.Color(255, 0, 0, 150)  # Rot für Schach

# Animation
ANIMATION_SPEED = 15  # Frames pro Animation

# Sound aktivieren
SOUND_ENABLED = True

# Timer Einstellungen (in Sekunden)
TIMER_ENABLED = True
INITIAL_TIME = 600  # 10 Minuten pro Spieler


def load_images():
    """Lädt alle Figurenbilder"""
    pieces = ["bQ", "bK", "bB", "bN", "bR", "bp", "wp", "wR", "wN", "wB", "wQ", "wK"]
    for piece in pieces:
        filepath = os.path.join(DIR_PATH, ("images/" + piece + ".png"))
        IMAGES[piece] = p.transform.smoothscale(p.image.load(filepath), (SQ_SIZE, SQ_SIZE))


def load_sounds():
    """Lädt Soundeffekte"""
    sounds = {}
    sound_files = {
        "move": "move.wav",
        "capture": "capture.wav",
        "check": "check.wav",
        "castle": "castle.wav",
        "game_over": "game_over.wav",
    }

    sounds_dir = os.path.join(DIR_PATH, "sounds")
    if not os.path.exists(sounds_dir):
        os.makedirs(sounds_dir)
        # Erstelle einfache Platzhalter-Sounds wenn keine existieren
        return None

    for name, filename in sound_files.items():
        filepath = os.path.join(sounds_dir, filename)
        if os.path.exists(filepath):
            sounds[name] = p.mixer.Sound(filepath)

    return sounds if sounds else None


def main():
    p.init()
    p.mixer.init()

    # AI Visualisierung Toggle
    show_ai_analysis = False
    show_welcome = True  # Willkommensbildschirm anzeigen
    window_width = WIDTH + MOVE_LOG_PANEL_WIDTH

    screen = p.display.set_mode((window_width, HEIGHT))
    p.display.set_caption("ChessyAI - Chess Engine")
    clock = p.time.Clock()

    gs = ChessEngine.GameState()
    valid_moves = gs.get_valid_moves()
    move_made = False
    animate = False  # Flag für Animation

    load_images()
    sounds = load_sounds()

    running = True
    sq_selected = ()
    player_clicks = []
    game_over = False

    # Spieler-Konfiguration (True = Mensch, False = KI)
    player_one = True  # Weiß
    player_two = False  # Schwarz (KI)

    ai_thinking = False
    move_log_font = p.font.SysFont("Arial", 14, False, False)

    # Timer
    white_time = INITIAL_TIME
    black_time = INITIAL_TIME
    last_time = p.time.get_ticks()

    # Bauernumwandlung
    promotion_screen = False
    promotion_move = None

    while running:
        human_turn = (gs.whiteToMove and player_one) or (
            not gs.whiteToMove and player_two
        )

        for e in p.event.get():
            if e.type == p.QUIT:
                running = False

            # Mausklick
            elif e.type == p.MOUSEBUTTONDOWN:
                if show_welcome:
                    show_welcome = False
                    continue
                if not game_over and human_turn and not promotion_screen:
                    location = p.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = location[1] // SQ_SIZE

                    if col < 8:  # Nur auf dem Schachbrett
                        if sq_selected == (row, col):
                            sq_selected = ()
                            player_clicks = []
                        else:
                            sq_selected = (row, col)
                            player_clicks.append(sq_selected)

                        if len(player_clicks) == 2:
                            move = ChessEngine.Move(
                                player_clicks[0], player_clicks[1], gs.board
                            )

                            for valid_move in valid_moves:
                                if move == valid_move:
                                    # Bauernumwandlung prüfen
                                    if valid_move.is_pawn_promotion:
                                        promotion_screen = True
                                        promotion_move = valid_move
                                    else:
                                        gs.make_move(valid_move)
                                        move_made = True
                                        animate = True
                                        play_sound(sounds, valid_move, gs)
                                        print(valid_move.get_chess_notation())
                                    sq_selected = ()
                                    player_clicks = []
                                    break

                            if not move_made and not promotion_screen:
                                player_clicks = [sq_selected]

                # Bauernumwandlung Auswahl
                elif promotion_screen:
                    location = p.mouse.get_pos()
                    piece = get_promotion_choice(location, gs.whiteToMove)
                    if piece:
                        promotion_move.promotion_piece = piece
                        gs.make_move(promotion_move)
                        move_made = True
                        animate = True
                        play_sound(sounds, promotion_move, gs)
                        promotion_screen = False
                        promotion_move = None

            # Tastatur
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # Z = Zug rückgängig
                    gs.undo_move()
                    move_made = True
                    animate = False
                    game_over = False
                    promotion_screen = False
                if e.key == p.K_r:  # R = Reset
                    gs = ChessEngine.GameState()
                    valid_moves = gs.get_valid_moves()
                    sq_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    promotion_screen = False
                    white_time = INITIAL_TIME
                    black_time = INITIAL_TIME
                if e.key == p.K_s:  # S = Speichern als PGN
                    save_pgn(gs)
                if e.key == p.K_v:  # V = AI-Visualisierung Toggle
                    show_ai_analysis = not show_ai_analysis
                    window_width = (
                        WIDTH
                        + MOVE_LOG_PANEL_WIDTH
                        + (AI_PANEL_WIDTH if show_ai_analysis else 0)
                    )
                    screen = p.display.set_mode((window_width, HEIGHT))
                if e.key == p.K_f:  # F = KI-Zug erzwingen
                    if not game_over and human_turn:
                        ai_move = ChessAI.find_best_move(gs, valid_moves)
                        if ai_move:
                            gs.make_move(ai_move)
                            move_made = True
                            animate = True
                            play_sound(sounds, ai_move, gs)

        # KI Zug
        if not game_over and not human_turn and not promotion_screen:
            ai_move = ChessAI.find_best_move(gs, valid_moves)
            if ai_move is None:
                ai_move = ChessAI.find_random_move(valid_moves)
            if ai_move:
                gs.make_move(ai_move)
                move_made = True
                animate = True
                play_sound(sounds, ai_move, gs)

        # Gültige Züge neu berechnen
        if move_made:
            valid_moves = gs.get_valid_moves()
            move_made = False

            if gs.checkmate:
                game_over = True
                winner = "Schwarz" if gs.whiteToMove else "Weiß"
                print(f"Schachmatt! {winner} gewinnt!")
                if sounds and "game_over" in sounds:
                    sounds["game_over"].play()
            elif gs.stalemate:
                game_over = True
                print("Patt! Unentschieden!")
                if sounds and "game_over" in sounds:
                    sounds["game_over"].play()

        # Timer aktualisieren
        if TIMER_ENABLED and not game_over and not promotion_screen:
            current_time = p.time.get_ticks()
            elapsed = (current_time - last_time) / 1000
            last_time = current_time

            if gs.whiteToMove:
                white_time -= elapsed
                if white_time <= 0:
                    white_time = 0
                    game_over = True
                    print("Zeit abgelaufen! Schwarz gewinnt!")
            else:
                black_time -= elapsed
                if black_time <= 0:
                    black_time = 0
                    game_over = True
                    print("Zeit abgelaufen! Weiß gewinnt!")

        draw_gamestate(screen, gs, valid_moves, sq_selected)
        draw_move_log(screen, gs, move_log_font)

        if TIMER_ENABLED:
            draw_timer(screen, white_time, black_time, gs.whiteToMove)

        if show_ai_analysis:
            draw_ai_analysis(screen, gs)

        if promotion_screen:
            draw_promotion_screen(screen, gs.whiteToMove)

        if game_over:
            draw_end_game_text(screen, gs, white_time, black_time)

        if show_welcome:
            draw_welcome_screen(screen)

        clock.tick(MAX_FPS)
        p.display.flip()

    p.quit()


def play_sound(sounds, move, gs):
    """Spielt den passenden Sound ab"""
    if not sounds or not SOUND_ENABLED:
        return

    if gs.is_in_check():
        if "check" in sounds:
            sounds["check"].play()
    elif move.is_castle_move:
        if "castle" in sounds:
            sounds["castle"].play()
    elif move.piece_captured != "--":
        if "capture" in sounds:
            sounds["capture"].play()
    else:
        if "move" in sounds:
            sounds["move"].play()


def get_promotion_choice(location, is_white):
    """Ermittelt die gewählte Umwandlungsfigur"""
    x, y = location
    center_x = WIDTH // 2
    center_y = HEIGHT // 2

    # Prüfen ob Klick im Auswahlbereich
    if center_y - SQ_SIZE // 2 <= y <= center_y + SQ_SIZE // 2:
        pieces = ["Q", "R", "B", "N"]
        start_x = center_x - 2 * SQ_SIZE
        for i, piece in enumerate(pieces):
            if start_x + i * SQ_SIZE <= x <= start_x + (i + 1) * SQ_SIZE:
                return piece
    return None


def draw_promotion_screen(screen, is_white):
    """Zeigt Bauernumwandlungs-Dialog"""
    # Hintergrund abdunkeln
    s = p.Surface((WIDTH, HEIGHT))
    s.set_alpha(200)
    s.fill(p.Color("black"))
    screen.blit(s, (0, 0))

    # Auswahlbox
    pieces = ["Q", "R", "B", "N"]
    color = "w" if is_white else "b"
    center_x = WIDTH // 2
    center_y = HEIGHT // 2

    # Hintergrund für Auswahl
    box_rect = p.Rect(
        center_x - 2 * SQ_SIZE, center_y - SQ_SIZE // 2 - 30, 4 * SQ_SIZE, SQ_SIZE + 50
    )
    p.draw.rect(screen, p.Color("white"), box_rect)
    p.draw.rect(screen, p.Color("black"), box_rect, 3)

    # Text
    font = p.font.SysFont("Helvetica", 20, True, False)
    text = font.render("Wähle Umwandlung:", True, p.Color("black"))
    screen.blit(text, (center_x - text.get_width() // 2, center_y - SQ_SIZE // 2 - 25))

    # Figuren zeichnen
    for i, piece in enumerate(pieces):
        piece_key = color + piece
        x = center_x - 2 * SQ_SIZE + i * SQ_SIZE
        y = center_y - SQ_SIZE // 2 + 20
        screen.blit(IMAGES[piece_key], p.Rect(x, y, SQ_SIZE, SQ_SIZE))


def draw_gamestate(screen, gs, valid_moves, sq_selected):
    """Zeichnet das komplette Spielfeld"""
    draw_board(screen)
    highlight_squares(screen, gs, valid_moves, sq_selected)
    draw_pieces(screen, gs.board)


def draw_board(screen):
    """Zeichnet das Schachbrett"""
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = COLORS[((r + c) % 2)]
            p.draw.rect(
                screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE)
            )


def highlight_squares(screen, gs, valid_moves, sq_selected):
    """Hebt ausgewählte Figur und gültige Züge hervor"""
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ("w" if gs.whiteToMove else "b"):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(SELECTED_COLOR)
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))

            s.fill(HIGHLIGHT_COLOR)
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col * SQ_SIZE, move.end_row * SQ_SIZE))

    # Letzten Zug hervorheben
    if len(gs.moveLog) > 0:
        last_move = gs.moveLog[-1]
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(80)
        s.fill(LAST_MOVE_COLOR)
        screen.blit(s, (last_move.start_col * SQ_SIZE, last_move.start_row * SQ_SIZE))
        screen.blit(s, (last_move.end_col * SQ_SIZE, last_move.end_row * SQ_SIZE))

    # König im Schach
    if gs.is_in_check():
        king_pos = gs.whiteKingLocation if gs.whiteToMove else gs.blackKingLocation
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(150)
        s.fill(CHECK_COLOR)
        screen.blit(s, (king_pos[1] * SQ_SIZE, king_pos[0] * SQ_SIZE))


def draw_pieces(screen, board):
    """Zeichnet die Figuren"""
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_move_log(screen, gs, font):
    """Zeichnet das Zugprotokoll"""
    move_log_rect = p.Rect(WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color(40, 40, 40), move_log_rect)

    # Titel
    title_font = p.font.SysFont("Arial", 18, True, False)
    title = title_font.render("Zugprotokoll", True, p.Color("white"))
    screen.blit(title, (WIDTH + 10, 10))

    move_log = gs.moveLog
    move_texts = []

    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + ". " + move_log[i].get_chess_notation()
        if i + 1 < len(move_log):
            move_string += "  " + move_log[i + 1].get_chess_notation()
        move_texts.append(move_string)

    padding = 40
    line_spacing = 20

    for i, text in enumerate(move_texts[-20:]):  # Letzte 20 Züge
        text_object = font.render(text, True, p.Color("white"))
        text_location = (WIDTH + 10, padding + i * line_spacing)
        screen.blit(text_object, text_location)


def draw_timer(screen, white_time, black_time, white_to_move):
    """Zeichnet die Schachuhren"""
    font = p.font.SysFont("Arial", 24, True, False)

    # Weiß Timer
    white_mins = int(white_time // 60)
    white_secs = int(white_time % 60)
    white_text = f"Weiß: {white_mins:02d}:{white_secs:02d}"
    white_color = p.Color("yellow") if white_to_move else p.Color("white")
    white_surface = font.render(white_text, True, white_color)
    screen.blit(white_surface, (WIDTH + 10, HEIGHT - 80))

    # Schwarz Timer
    black_mins = int(black_time // 60)
    black_secs = int(black_time % 60)
    black_text = f"Schwarz: {black_mins:02d}:{black_secs:02d}"
    black_color = p.Color("yellow") if not white_to_move else p.Color("white")
    black_surface = font.render(black_text, True, black_color)
    screen.blit(black_surface, (WIDTH + 10, HEIGHT - 50))


def draw_end_game_text(screen, gs, white_time=None, black_time=None):
    """Zeigt Spielende-Text"""
    font = p.font.SysFont("Helvetica", 32, True, False)

    if gs.checkmate:
        winner = "Schwarz" if gs.whiteToMove else "Weiß"
        text = f"Schachmatt! {winner} gewinnt!"
    elif gs.stalemate:
        text = "Patt! Unentschieden!"
    elif white_time is not None and white_time <= 0:
        text = "Zeit abgelaufen! Schwarz gewinnt!"
    elif black_time is not None and black_time <= 0:
        text = "Zeit abgelaufen! Weiß gewinnt!"
    else:
        text = "Spielende!"

    # Hintergrund
    s = p.Surface((WIDTH, 100))
    s.set_alpha(200)
    s.fill(p.Color("black"))
    screen.blit(s, (0, HEIGHT // 2 - 50))

    text_object = font.render(text, True, p.Color("white"))
    text_location = (WIDTH // 2 - text_object.get_width() // 2, HEIGHT // 2 - 20)
    screen.blit(text_object, text_location)

    small_font = p.font.SysFont("Helvetica", 16, False, False)
    hint = "R=Neustart | Z=Rückgängig | S=PGN Speichern | V=KI-Analyse"
    hint_object = small_font.render(hint, True, p.Color("white"))
    hint_location = (WIDTH // 2 - hint_object.get_width() // 2, HEIGHT // 2 + 20)
    screen.blit(hint_object, hint_location)


def draw_welcome_screen(screen):
    """Zeigt den Willkommensbildschirm mit Tastenbelegung"""
    # Halbtransparenter Hintergrund
    overlay = p.Surface((WIDTH + MOVE_LOG_PANEL_WIDTH, HEIGHT))
    overlay.set_alpha(230)
    overlay.fill(p.Color(20, 20, 30))
    screen.blit(overlay, (0, 0))

    center_x = (WIDTH + MOVE_LOG_PANEL_WIDTH) // 2
    y_offset = 40

    # Titel
    title_font = p.font.SysFont("Arial", 42, True, False)
    title = title_font.render("ChessyAI", True, p.Color(255, 215, 0))
    screen.blit(title, (center_x - title.get_width() // 2, y_offset))
    y_offset += 55

    # Untertitel
    subtitle_font = p.font.SysFont("Arial", 18, False, True)
    subtitle = subtitle_font.render(
        "Schach-Engine mit KI-Gegner", True, p.Color(180, 180, 200)
    )
    screen.blit(subtitle, (center_x - subtitle.get_width() // 2, y_offset))
    y_offset += 50

    # Tastenbelegung Box
    box_width = 400
    box_height = 280
    box_x = center_x - box_width // 2
    box_y = y_offset

    # Box-Hintergrund
    box_rect = p.Rect(box_x, box_y, box_width, box_height)
    p.draw.rect(screen, p.Color(40, 40, 55), box_rect, border_radius=10)
    p.draw.rect(screen, p.Color(100, 100, 140), box_rect, 2, border_radius=10)

    # Tastenbelegung Titel
    header_font = p.font.SysFont("Arial", 20, True, False)
    header = header_font.render("Tastenbelegung", True, p.Color(100, 200, 255))
    screen.blit(header, (center_x - header.get_width() // 2, box_y + 15))

    # Tasten-Liste
    key_font = p.font.SysFont("Arial", 16, True, False)
    desc_font = p.font.SysFont("Arial", 16, False, False)

    keys = [
        ("V", "KI-Analyse Panel ein/ausblenden", p.Color(100, 255, 150)),
        ("Z", "Letzten Zug rückgängig machen", p.Color(255, 200, 100)),
        ("R", "Neues Spiel starten", p.Color(255, 150, 150)),
        ("S", "Partie als PGN speichern", p.Color(150, 200, 255)),
        ("F", "KI-Zug erzwingen (für Weiß)", p.Color(200, 150, 255)),
    ]

    key_y = box_y + 55
    for key, description, color in keys:
        # Taste in Box
        key_box = p.Rect(box_x + 30, key_y, 40, 30)
        p.draw.rect(screen, p.Color(60, 60, 80), key_box, border_radius=5)
        p.draw.rect(screen, color, key_box, 2, border_radius=5)

        key_text = key_font.render(key, True, color)
        screen.blit(
            key_text,
            (
                key_box.centerx - key_text.get_width() // 2,
                key_box.centery - key_text.get_height() // 2,
            ),
        )

        # Beschreibung
        desc_text = desc_font.render(description, True, p.Color(200, 200, 210))
        screen.blit(desc_text, (box_x + 90, key_y + 5))

        key_y += 42

    y_offset = box_y + box_height + 25

    # Maussteuerung
    mouse_font = p.font.SysFont("Arial", 14, False, False)
    mouse_info = [
        "Klicke auf eine Figur, dann auf das Zielfeld",
        "Gueltige Zuege werden gruen hervorgehoben",
    ]

    for info in mouse_info:
        text = mouse_font.render(info, True, p.Color(150, 150, 170))
        screen.blit(text, (center_x - text.get_width() // 2, y_offset))
        y_offset += 22

    # Start-Hinweis
    y_offset += 20
    start_font = p.font.SysFont("Arial", 20, True, False)
    start_text = start_font.render(
        "Klicke irgendwo um zu starten!", True, p.Color(255, 255, 100)
    )

    # Blinkeffekt
    alpha = int(128 + 127 * abs((p.time.get_ticks() % 1000) / 500 - 1))
    start_surface = p.Surface(start_text.get_size(), p.SRCALPHA)
    start_surface.fill((255, 255, 100, alpha))
    start_text_final = start_font.render(
        "Klicke irgendwo um zu starten!", True, p.Color(255, 255, 100)
    )

    screen.blit(start_text_final, (center_x - start_text.get_width() // 2, y_offset))


def draw_ai_analysis(screen, gs):
    """Zeichnet das AI-Analyse Panel mit Minimax-Visualisierung"""
    panel_x = WIDTH + MOVE_LOG_PANEL_WIDTH
    panel_rect = p.Rect(panel_x, 0, AI_PANEL_WIDTH, HEIGHT)

    # Hintergrund
    p.draw.rect(screen, p.Color(25, 25, 35), panel_rect)
    p.draw.line(screen, p.Color(60, 60, 80), (panel_x, 0), (panel_x, HEIGHT), 2)

    # Analyse-Daten holen
    analysis = ChessAI.get_analysis()

    # Titel
    title_font = p.font.SysFont("Arial", 18, True, False)
    title = title_font.render("KI-Analyse (Minimax)", True, p.Color(100, 200, 255))
    screen.blit(title, (panel_x + 10, 10))

    y_offset = 45
    font = p.font.SysFont("Arial", 13, False, False)
    bold_font = p.font.SysFont("Arial", 13, True, False)
    small_font = p.font.SysFont("Arial", 11, False, False)

    # Suchtiefe
    depth_text = bold_font.render(
        f"Suchtiefe: {analysis['depth']}", True, p.Color("white")
    )
    screen.blit(depth_text, (panel_x + 10, y_offset))
    y_offset += 25

    # Statistiken
    stats_color = p.Color(180, 180, 180)
    nodes_text = font.render(
        f"Knoten durchsucht: {analysis['nodes_searched']:,}", True, stats_color
    )
    screen.blit(nodes_text, (panel_x + 10, y_offset))
    y_offset += 20

    pruned_text = font.render(
        f"Abgeschnittene Zweige: {analysis['pruned_branches']:,}", True, stats_color
    )
    screen.blit(pruned_text, (panel_x + 10, y_offset))
    y_offset += 30

    # Bewertungsbalken
    score = analysis["position_score"]
    draw_evaluation_bar(
        screen, panel_x + 10, y_offset, AI_PANEL_WIDTH - 20, 30, score, gs.whiteToMove
    )
    y_offset += 50

    # Materialbalance
    material = analysis["material_balance"]
    mat_title = bold_font.render("Materialbalance:", True, p.Color("white"))
    screen.blit(mat_title, (panel_x + 10, y_offset))
    y_offset += 22

    white_mat = material.get("white", 0)
    black_mat = material.get("black", 0)
    diff = white_mat - black_mat
    diff_color = (
        p.Color(100, 255, 100)
        if diff > 0
        else p.Color(255, 100, 100) if diff < 0 else p.Color(200, 200, 200)
    )
    diff_str = f"+{diff}" if diff > 0 else str(diff)

    mat_text = font.render(
        f"Weiß: {white_mat}  |  Schwarz: {black_mat}  ({diff_str})", True, diff_color
    )
    screen.blit(mat_text, (panel_x + 10, y_offset))
    y_offset += 35

    # Top Züge mit Bewertungen
    moves_title = bold_font.render("Top Züge (bewertet):", True, p.Color("white"))
    screen.blit(moves_title, (panel_x + 10, y_offset))
    y_offset += 25

    moves_evaluated = analysis["moves_evaluated"]
    if moves_evaluated:
        # Sortiert nach Score (beste zuerst für Weiß, umgekehrt für Schwarz)
        for i, (move, score) in enumerate(moves_evaluated[:8]):
            # Farbcodierung basierend auf Bewertung
            if score > 100:
                move_color = p.Color(100, 255, 100)  # Grün - gut
            elif score > 0:
                move_color = p.Color(180, 255, 180)  # Hellgrün
            elif score > -100:
                move_color = p.Color(255, 255, 180)  # Gelb - neutral
            elif score > -300:
                move_color = p.Color(255, 180, 100)  # Orange
            else:
                move_color = p.Color(255, 100, 100)  # Rot - schlecht

            # Rang-Symbol (ASCII-kompatibel)
            rank_symbols = ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."]
            rank = rank_symbols[i] if i < len(rank_symbols) else f"{i+1}."

            # Score formatieren
            score_str = f"+{score/100:.2f}" if score >= 0 else f"{score/100:.2f}"

            move_str = f"{rank} {move.get_chess_notation():6s} ({score_str})"
            move_text = small_font.render(move_str, True, move_color)
            screen.blit(move_text, (panel_x + 15, y_offset))

            # Mini-Bewertungsbalken
            bar_width = 60
            bar_x = panel_x + AI_PANEL_WIDTH - bar_width - 15
            draw_mini_eval_bar(screen, bar_x, y_offset + 2, bar_width, 12, score)

            y_offset += 18
    else:
        no_moves = font.render("Keine Analyse verfügbar", True, p.Color(150, 150, 150))
        screen.blit(no_moves, (panel_x + 10, y_offset))
        y_offset += 20

    y_offset += 20

    # Suchbaum-Visualisierung (vereinfacht)
    tree_title = bold_font.render("Suchbaum-Tiefe:", True, p.Color("white"))
    screen.blit(tree_title, (panel_x + 10, y_offset))
    y_offset += 25

    # Visualisiere die Suchtiefe als Baumstruktur
    draw_search_tree_visualization(
        screen, panel_x + 10, y_offset, AI_PANEL_WIDTH - 20, 80, analysis
    )
    y_offset += 95

    # Hinweis
    hint_font = p.font.SysFont("Arial", 10, False, True)
    hint = hint_font.render("Drücke 'V' zum Ausblenden", True, p.Color(100, 100, 120))
    screen.blit(hint, (panel_x + 10, HEIGHT - 20))


def draw_evaluation_bar(screen, x, y, width, height, score, white_to_move):
    """Zeichnet einen Bewertungsbalken wie bei chess.com"""
    # Hintergrund
    p.draw.rect(screen, p.Color(40, 40, 40), (x, y, width, height))

    # Score auf 0-1 normalisieren (±10 Bauern = ±1000 Centipawns)
    normalized = max(-1, min(1, score / 1000))

    # Weiß-Anteil berechnen (0.5 = ausgeglichen)
    white_portion = 0.5 + (normalized * 0.5)

    # Weiße Seite
    white_width = int(width * white_portion)
    p.draw.rect(screen, p.Color(240, 240, 240), (x, y, white_width, height))

    # Schwarze Seite
    black_width = width - white_width
    p.draw.rect(screen, p.Color(30, 30, 30), (x + white_width, y, black_width, height))

    # Mittellinie
    p.draw.line(
        screen,
        p.Color(100, 100, 100),
        (x + width // 2, y),
        (x + width // 2, y + height),
        1,
    )

    # Score-Text in der Mitte
    font = p.font.SysFont("Arial", 12, True, False)
    score_pawns = score / 100
    if abs(score_pawns) < 0.1:
        score_text = "0.0"
    else:
        score_text = f"+{score_pawns:.1f}" if score_pawns > 0 else f"{score_pawns:.1f}"

    text_color = p.Color("black") if white_portion > 0.5 else p.Color("white")
    text_surface = font.render(score_text, True, text_color)
    text_x = (
        x + (white_width - text_surface.get_width()) // 2
        if white_portion > 0.5
        else x + white_width + (black_width - text_surface.get_width()) // 2
    )
    screen.blit(text_surface, (text_x, y + (height - text_surface.get_height()) // 2))

    # Rahmen
    p.draw.rect(screen, p.Color(80, 80, 80), (x, y, width, height), 1)


def draw_mini_eval_bar(screen, x, y, width, height, score):
    """Zeichnet einen Mini-Bewertungsbalken für einzelne Züge"""
    # Hintergrund
    p.draw.rect(screen, p.Color(50, 50, 50), (x, y, width, height))

    # Normalisieren
    normalized = max(-1, min(1, score / 500))

    if normalized >= 0:
        bar_width = int(width * 0.5 * normalized)
        p.draw.rect(
            screen, p.Color(100, 200, 100), (x + width // 2, y, bar_width, height)
        )
    else:
        bar_width = int(width * 0.5 * abs(normalized))
        p.draw.rect(
            screen,
            p.Color(200, 100, 100),
            (x + width // 2 - bar_width, y, bar_width, height),
        )

    # Mittellinie
    p.draw.line(
        screen,
        p.Color(150, 150, 150),
        (x + width // 2, y),
        (x + width // 2, y + height),
        1,
    )


def draw_search_tree_visualization(screen, x, y, width, height, analysis):
    """Zeichnet eine verbesserte Visualisierung des Suchbaums"""
    depth = analysis["depth"]
    nodes = analysis["nodes_searched"]
    pruned = analysis["pruned_branches"]

    # Hintergrund für den Baum
    tree_bg = p.Rect(x, y, width, height - 15)
    p.draw.rect(screen, p.Color(35, 35, 45), tree_bg)
    p.draw.rect(screen, p.Color(60, 60, 80), tree_bg, 1)

    # Padding innerhalb des Rahmens
    inner_x = x + 10
    inner_y = y + 8
    inner_width = width - 20
    inner_height = height - 30

    # Baum-Struktur zeichnen
    levels = min(depth + 1, 4)  # Max 4 Ebenen anzeigen
    level_height = inner_height // levels

    # Zuerst alle Linien zeichnen (hinter den Knoten)
    for level in range(1, levels):
        if level == 0:
            num_nodes = 1
        else:
            num_nodes = min(6, 2**level)

        node_spacing = inner_width // (num_nodes + 1)
        parent_num_nodes = min(6, 2 ** (level - 1))
        parent_spacing = inner_width // (parent_num_nodes + 1)

        for n in range(num_nodes):
            node_x = inner_x + node_spacing * (n + 1)
            node_y = inner_y + level * level_height
            parent_x = inner_x + parent_spacing * ((n // 2) + 1)
            parent_y = inner_y + (level - 1) * level_height

            # Gradient-Linie (heller oben, dunkler unten)
            line_color = p.Color(80, 100, 140)
            p.draw.line(
                screen, line_color, (parent_x, parent_y + 6), (node_x, node_y - 2), 2
            )

    # Dann alle Knoten zeichnen
    for level in range(levels):
        if level == 0:
            num_nodes = 1
        else:
            num_nodes = min(6, 2**level)

        node_spacing = inner_width // (num_nodes + 1)

        for n in range(num_nodes):
            node_x = inner_x + node_spacing * (n + 1)
            node_y = inner_y + level * level_height

            # Knotengröße und Farbe basierend auf Tiefe
            if level == 0:
                # Wurzelknoten - größer und golden
                radius = 8
                node_color = p.Color(255, 200, 50)
                border_color = p.Color(200, 150, 0)
            elif level == levels - 1:
                # Blattknoten - blau
                radius = 5
                node_color = p.Color(100, 180, 255)
                border_color = p.Color(60, 120, 200)
            else:
                # Zwischenknoten - grün abgestuft
                radius = 6
                green_intensity = 255 - (level * 50)
                node_color = p.Color(100, green_intensity, 100)
                border_color = p.Color(60, green_intensity - 40, 60)

            # Knoten mit Rand zeichnen
            p.draw.circle(screen, node_color, (node_x, node_y), radius)
            p.draw.circle(screen, border_color, (node_x, node_y), radius, 1)

    # Legende unter dem Baum
    font = p.font.SysFont("Arial", 10, False, False)
    legend_y = y + height - 12

    # Tiefe-Anzeige
    depth_text = font.render(f"Tiefe: {depth}", True, p.Color(255, 200, 50))
    screen.blit(depth_text, (x + 5, legend_y))

    # Knoten-Anzeige
    nodes_text = font.render(f"{nodes:,} Knoten", True, p.Color(100, 180, 255))
    screen.blit(nodes_text, (x + 60, legend_y))

    # Pruning-Anzeige
    if pruned > 0:
        pruned_text = font.render(f"{pruned:,} Schnitte", True, p.Color(255, 150, 100))
        screen.blit(pruned_text, (x + 145, legend_y))


def save_pgn(gs):
    """Speichert die Partie als PGN-Datei"""
    pgn_dir = os.path.join(DIR_PATH, "games")
    if not os.path.exists(pgn_dir):
        os.makedirs(pgn_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(pgn_dir, f"game_{timestamp}.pgn")

    with open(filename, "w") as f:
        # PGN Header
        f.write('[Event "Chessy Game"]\n')
        f.write(f'[Date "{datetime.now().strftime("%Y.%m.%d")}"]\n')
        f.write('[White "Player"]\n')
        f.write('[Black "Chessy AI"]\n')

        # Ergebnis
        if gs.checkmate:
            result = "0-1" if gs.whiteToMove else "1-0"
        elif gs.stalemate:
            result = "1/2-1/2"
        else:
            result = "*"
        f.write(f'[Result "{result}"]\n\n')

        # Züge
        moves = []
        for i, move in enumerate(gs.moveLog):
            if i % 2 == 0:
                moves.append(f"{i // 2 + 1}.")
            moves.append(move.get_chess_notation())

        f.write(" ".join(moves))
        f.write(f" {result}\n")

    print(f"Partie gespeichert: {filename}")


def load_pgn(filename):
    """Lädt eine PGN-Datei (TODO: Vollständige Implementierung)"""
    # Grundlegende PGN-Parsing Logik
    pass


if __name__ == "__main__":
    main()
