
import pygame as p
import ChessEngine, PlayAI
import sys
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 600
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}



def loadImages():
    
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))


def main():
    
    p.init()
    # start_drag = None
    screen = p.display.set_mode((BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  
    animate = False  
    loadImages()  
    running = True
    square_selected = ()  
    player_clicks = [] 
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    player_one = True  
    player_two = False  

    while running:
        human_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  
                        square_selected = ()  
                        player_clicks = []  
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  
                    if len(player_clicks) == 2 and human_turn:  
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()  
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]
            # elif e.type == p.MOUSEBUTTONDOWN:
            #         if not game_over:
            #             location = p.mouse.get_pos()  
            #             col = location[0] // SQUARE_SIZE
            #             row = location[1] // SQUARE_SIZE
            #             if square_selected == (row, col) or col >= 8:  
            #                 square_selected = ()  
            #                 player_clicks = []  
            #             else:
            #                 square_selected = (row, col)
            #                 player_clicks.append(square_selected)  
            #                 start_drag = square_selected
            #         if len(player_clicks) == 2 and human_turn:  
            #             move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
            #             for i in range(len(valid_moves)):
            #                 if move == valid_moves[i]:
            #                     game_state.makeMove(valid_moves[i])
            #                     move_made = True
            #                     animate = True
            #                     square_selected = ()  
            #                     player_clicks = []
            #             if not move_made:
            #                 player_clicks = [square_selected]

            # elif e.type == p.MOUSEMOTION and start_drag:
            #         if len(player_clicks) == 1:
            #             location = p.mouse.get_pos()
            #             col = location[0] // SQUARE_SIZE
            #             row = location[1] // SQUARE_SIZE
            #             if (row, col) != start_drag:
            #                 square_selected = (row, col)

            # elif e.type == p.MOUSEBUTTONUP and start_drag:
            #         if len(player_clicks) == 1:  # Piece has been selected
            #             location = p.mouse.get_pos()
            #             col = location[0] // SQUARE_SIZE
            #             row = location[1] // SQUARE_SIZE
            #             player_clicks.append((row, col))  # Add the second click
            #             move = ChessEngine.Move(player_clicks[0], player_clicks[1], game_state.board)
            #             for i in range(len(valid_moves)):
            #                 if move == valid_moves[i]:
            #                     game_state.makeMove(valid_moves[i])
            #                     move_made = True
            #                     animate = True
            #                     square_selected = ()  
            #                     player_clicks = []
            #             if not move_made:
            #                 player_clicks = []
            #         start_drag = None


            # key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo 
                    game_state.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                if e.key == p.K_r:  
                    game_state = ChessEngine.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # AI move finder
        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  
                move_finder_process = Process(target=PlayAI.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = PlayAI.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()


def drawGameState(screen, game_state, valid_moves, square_selected):
   
    drawBoard(screen)  # draw squares on the board
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # draw pieces on top of those squares


def drawBoard(screen):
   
    global colors
    colors = [p.Color(234,235,200), p.Color(119,154,88)]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, gamestate, valid_moves, square_selected):
   
    if (len(gamestate.move_log)) > 0:
        last_move = gamestate.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('green'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if gamestate.board[row][col][0] == (
                'w' if gamestate.white_to_move else 'b'): 
            
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE)) #so that I can put image on it 
            s.set_alpha(100)  # transparency value
            s.fill(p.Color('blue')) 
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE)) #blit just copies the image
           
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))

def drawEvaluationBar(screen, game_state):
    # Calculate evaluation score
    evaluation_score = game_state.evaluatePosition()
    
    # Map evaluation score to bar lengths
    white_bar_length = int(abs(EVAL_BAR_HEIGHT * evaluation_score))
    black_bar_length = int(abs(EVAL_BAR_HEIGHT * evaluation_score))
    
    # Determine bar colors based on evaluation score
    if evaluation_score >= 0:
        white_bar_color = (255, 255, 255)  # White for positive score
        black_bar_color = (0, 0, 0)  # Black for positive score
        black_bar_length = max(0, EVAL_BAR_HEIGHT - white_bar_length)
    else:
        white_bar_color = (0, 0, 0)  # Black for negative score
        black_bar_color = (255, 255, 255)  # White for negative score
        white_bar_length = max(0, EVAL_BAR_HEIGHT - black_bar_length)
    
    # Draw white bar
    p.draw.rect(screen, white_bar_color, (EVAL_BAR_POS_X, EVAL_BAR_POS_Y, EVAL_BAR_WIDTH, white_bar_length))
    
    # Draw black bar
    p.draw.rect(screen, black_bar_color, (EVAL_BAR_POS_X, EVAL_BAR_POS_Y + white_bar_length, EVAL_BAR_WIDTH, black_bar_length))

def drawPieces(screen, board):
   
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def drawMoveLog(screen, game_state, font):
    move_log_rect = p.Rect(BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('black'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('white'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
   
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10  # frames to move one square
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count, move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        #erasung pieces from end 
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # captured piece 
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
      
        screen.blit(IMAGES[move.piece_moved], p.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()