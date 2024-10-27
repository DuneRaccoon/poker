# gui.py

import pygame
import sys
from pygame.locals import *
from typing import List, Tuple, Optional
from .game import Game
from .player import Player
from .ai import AIPlayer
from .card import Card

class GUI:
    """
    A class to handle the graphical user interface for the poker game.
    """

    def __init__(self, game: Game):
        pygame.init()
        self.screen_width = 1024
        self.screen_height = 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Python Poker Game')
        self.clock = pygame.time.Clock()
        self.game = game
        self.load_assets()
        self.font = pygame.font.SysFont('Arial', 20)
        self.running = True

        # Define buttons and their positions
        self.button_fold = pygame.Rect(50, self.screen_height - 100, 100, 50)
        self.button_check = pygame.Rect(200, self.screen_height - 100, 100, 50)
        self.button_call = pygame.Rect(350, self.screen_height - 100, 100, 50)
        self.button_raise = pygame.Rect(500, self.screen_height - 100, 100, 50)

        # Input box for raise amount
        self.raise_input_active = False
        self.raise_input_box = pygame.Rect(650, self.screen_height - 100, 100, 50)
        self.raise_input_text = ''

    def load_assets(self):
        """
        Loads images, sounds, and fonts needed for the GUI.
        """
        # Load table background image
        self.table_image = pygame.image.load('images/table.png').convert()

        # Load card images
        self.card_images = {}
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        for suit in suits:
            for rank in ranks:
                card = f'{rank}_of_{suit}'
                image_path = f'images/cards/{card}.png'
                self.card_images[card] = pygame.image.load(image_path).convert_alpha()

        # Load card back image
        self.card_back = pygame.image.load('assets/images/cards/back.png').convert_alpha()

        # Load chip images (if any)
        # self.chip_image = pygame.image.load('assets/images/chips/chip.png').convert_alpha()

        # Load player avatars (if any)
        # self.avatar_image = pygame.image.load('assets/images/avatars/player.png').convert_alpha()

    def draw_table(self):
        """
        Draws the poker table background.
        """
        self.screen.blit(self.table_image, (0, 0))

    def draw_players(self):
        """
        Draws the players, their chips, and their cards.
        """
        num_players = len(self.game.players)
        angle_step = 360 / num_players
        radius = 250
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        for i, player in enumerate(self.game.players):
            angle = angle_step * i - 90  # Start at the top of the circle
            x = center_x + radius * pygame.math.cos(pygame.math.radians(angle))
            y = center_y + radius * pygame.math.sin(pygame.math.radians(angle))

            # Draw player name
            name_text = self.font.render(player.name, True, (255, 255, 255))
            self.screen.blit(name_text, (x - name_text.get_width() // 2, y - 80))

            # Draw player chips
            chips_text = self.font.render(f'Chips: {player.chips}', True, (255, 255, 0))
            self.screen.blit(chips_text, (x - chips_text.get_width() // 2, y - 60))

            # Draw player cards
            if isinstance(player, AIPlayer) or player.folded:
                # Show card backs for AI players or if folded
                self.screen.blit(self.card_back, (x - 36, y - 50))
                self.screen.blit(self.card_back, (x + 4, y - 50))
            else:
                # Show actual cards for the human player
                if player.hand:
                    for idx, card in enumerate(player.hand):
                        card_image = self.get_card_image(card)
                        self.screen.blit(card_image, (x - 36 + idx * 40, y - 50))

            # Indicate if player is the dealer
            if player.is_dealer:
                dealer_text = self.font.render('D', True, (255, 0, 0))
                self.screen.blit(dealer_text, (x - dealer_text.get_width() // 2, y - 100))

    def draw_community_cards(self):
        """
        Draws the community cards on the table.
        """
        center_x = self.screen_width // 2 - 100
        center_y = self.screen_height // 2 - 150

        for idx, card in enumerate(self.game.community_cards):
            card_image = self.get_card_image(card)
            self.screen.blit(card_image, (center_x + idx * 80, center_y))

    def draw_pot(self):
        """
        Displays the current pot amount.
        """
        pot_text = self.font.render(f'Pot: {self.game.pot}', True, (255, 255, 255))
        self.screen.blit(pot_text, (self.screen_width // 2 - pot_text.get_width() // 2, self.screen_height // 2 - 200))

    def draw_buttons(self):
        """
        Draws action buttons for the player.
        """
        # Draw Fold button
        pygame.draw.rect(self.screen, (200, 0, 0), self.button_fold)
        fold_text = self.font.render('Fold', True, (255, 255, 255))
        self.screen.blit(fold_text, (self.button_fold.x + 25, self.button_fold.y + 15))

        # Draw Check button
        pygame.draw.rect(self.screen, (0, 200, 0), self.button_check)
        check_text = self.font.render('Check', True, (255, 255, 255))
        self.screen.blit(check_text, (self.button_check.x + 20, self.button_check.y + 15))

        # Draw Call button
        pygame.draw.rect(self.screen, (0, 0, 200), self.button_call)
        call_text = self.font.render('Call', True, (255, 255, 255))
        self.screen.blit(call_text, (self.button_call.x + 25, self.button_call.y + 15))

        # Draw Raise button
        pygame.draw.rect(self.screen, (200, 200, 0), self.button_raise)
        raise_text = self.font.render('Raise', True, (0, 0, 0))
        self.screen.blit(raise_text, (self.button_raise.x + 25, self.button_raise.y + 15))

        # Draw input box for raise amount
        pygame.draw.rect(self.screen, (255, 255, 255), self.raise_input_box, 2)
        input_text = self.font.render(self.raise_input_text, True, (255, 255, 255))
        self.screen.blit(input_text, (self.raise_input_box.x + 5, self.raise_input_box.y + 15))

    def get_card_image(self, card: Card):
        """
        Retrieves the image for a given card.

        Parameters:
            card (Card): The card object.

        Returns:
            Surface: The Pygame surface of the card image.
        """
        card_key = f'{card.rank}_of_{card.suit}'
        return self.card_images.get(card_key, self.card_back)

    def update_display(self):
        """
        Updates the game display with the current game state.
        """
        self.screen.fill((0, 128, 0))  # Green background
        self.draw_table()
        self.draw_players()
        self.draw_community_cards()
        self.draw_pot()
        self.draw_buttons()
        pygame.display.flip()

    def handle_events(self):
        """
        Handles Pygame events, such as user input and window events.
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                if self.button_fold.collidepoint(event.pos):
                    self.player_action('fold')
                elif self.button_check.collidepoint(event.pos):
                    self.player_action('check')
                elif self.button_call.collidepoint(event.pos):
                    self.player_action('call')
                elif self.button_raise.collidepoint(event.pos):
                    self.raise_input_active = True
                elif self.raise_input_box.collidepoint(event.pos):
                    self.raise_input_active = True
                else:
                    self.raise_input_active = False
            elif event.type == KEYDOWN:
                if self.raise_input_active:
                    if event.key == K_RETURN:
                        self.player_action('raise', self.raise_input_text)
                        self.raise_input_text = ''
                        self.raise_input_active = False
                    elif event.key == K_BACKSPACE:
                        self.raise_input_text = self.raise_input_text[:-1]
                    else:
                        self.raise_input_text += event.unicode
                elif event.key == K_ESCAPE:
                    self.running = False
                    pygame.quit()
                    sys.exit()

    def run(self):
        """
        The main loop of the GUI, which updates the display and handles events.
        """
        while self.running:
            self.handle_events()
            self.update_display()
            self.clock.tick(30)  # Limit to 30 FPS

            # Run the game logic
            self.game_loop()

    def game_loop(self):
        """
        The game logic loop, which progresses the game state.
        """
        if not self.game.round_active:
            self.game.start_new_round()
            self.game.round_active = True
            self.game.betting_phase = 'pre-flop'
            self.game.current_player_index = 0

        if self.game.betting_phase:
            self.handle_betting()
        else:
            if len(self.game.community_cards) < 5:
                # Deal the next set of community cards
                if len(self.game.community_cards) == 0:
                    self.game.deal_community_cards(3)  # Flop
                else:
                    self.game.deal_community_cards(1)  # Turn or River
                self.game.betting_phase = True
                self.game.current_player_index = 0
            else:
                # Showdown
                winner = self.game.determine_winner()
                self.display_winner(winner)
                self.game.round_active = False

    def handle_betting(self):
        """
        Handles the betting rounds.
        """
        current_player = self.game.players[self.game.current_player_index]
        if current_player.folded or current_player.all_in:
            self.next_player()
            return

        if isinstance(current_player, AIPlayer):
            action_str = current_player.get_action(self.game.get_game_state())
            print(f"{current_player.name} decides to {action_str}")
            self.next_player()
        else:
            # Wait for the human player's action
            pass  # The action is handled in the event loop

    def player_action(self, action: str, amount: Optional[str] = None):
        """
        Handles the human player's action.

        Parameters:
            action (str): The action taken ('fold', 'check', 'call', 'raise').
            amount (str, optional): The raise amount if action is 'raise'.
        """
        player = self.game.players[self.game.current_player_index]
        if action == 'fold':
            player.fold()
            self.next_player()
        elif action == 'check':
            player.check()
            self.next_player()
        elif action == 'call':
            player.call(self.game.current_bet)
            self.game.pot += player.current_bet
            self.next_player()
        elif action == 'raise':
            try:
                raise_amount = float(amount)
                player.raise_bet(raise_amount)
                self.game.current_bet = player.current_bet
                self.game.pot += player.current_bet
                self.next_player()
            except ValueError:
                print("Invalid raise amount.")
        else:
            print("Unknown action.")

    def next_player(self):
        """
        Moves to the next player in the betting round.
        """
        self.game.current_player_index += 1
        if self.game.current_player_index >= len(self.game.players):
            self.game.current_player_index = 0
            self.game.betting_phase = False

    def display_winner(self, winner: Player):
        """
        Displays the winner of the round.

        Parameters:
            winner (Player): The player who won the round.
        """
        winner_text = self.font.render(f'{winner.name} wins the pot of {self.game.pot} chips!', True, (255, 255, 255))
        self.screen.blit(winner_text, (self.screen_width // 2 - winner_text.get_width() // 2, self.screen_height // 2))
        pygame.display.flip()
        pygame.time.wait(3000)  # Wait for 3 seconds before starting the next round

        # Reset the game state for the next round
        self.game.reset_round()

