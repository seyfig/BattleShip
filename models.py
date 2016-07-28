"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

ShipTypes = 5


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    wins = ndb.IntegerProperty(required=True, default=0)
    losses = ndb.IntegerProperty(required=True, default=0)
    winloss_ratio = ndb.FloatProperty(required=True, default=0.0)
    total_guesses = ndb.IntegerProperty(required=True, default=0)

    def to_form(self):
        return RankingForm(user_name=self.name, winloss=self.winloss_ratio,
                           guesses=self.total_guesses)


class Game(ndb.Model):
    """Game object"""
    number_of_players = ndb.IntegerProperty(required=True, default=2)
    player1 = ndb.KeyProperty(required=True, kind='User')
    player2 = ndb.KeyProperty(required=False, kind='User')
    board_ship1 = ndb.IntegerProperty(repeated=True)
    board_ship2 = ndb.IntegerProperty(repeated=True)
    board_hit1 = ndb.BooleanProperty(repeated=True)
    board_hit2 = ndb.BooleanProperty(repeated=True)
    ships1 = ndb.IntegerProperty(repeated=True)
    ships2 = ndb.IntegerProperty(repeated=True)
    rows = ndb.IntegerProperty(required=True, default=10)
    columns = ndb.IntegerProperty(required=True, default=10)
    turn = ndb.IntegerProperty(required=True, default=0)
    player1_turn = ndb.BooleanProperty(required=True, default=0)
    player2_turn = ndb.BooleanProperty(required=True, default=0)
    game_over = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def new_game(cls, number_of_players, user, opponent, rows, columns):
        """Creates and returns a new game"""
        if rows < 0 or columns < 0:
            raise ValueError('Dimensions must be greater than 0')
        game = Game(number_of_players=number_of_players,
                    player1=user,
                    player2=opponent,
                    board_ship1=[0 for col in range(columns * rows)],
                    board_ship2=[0 for col in range(columns * rows)],
                    board_hit1=[False for col in range(columns * rows)],
                    board_hit2=[False for col in range(columns * rows)],
                    ships1=[0 for col in range(ShipTypes)],
                    ships2=[0 for col in range(ShipTypes)],
                    rows=rows,
                    columns=columns,
                    turn=0,
                    player1_turn=True,
                    player2_turn=True,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.player1.get().name
        form.opponent_name = self.player2.get().name
        form.game_over = self.game_over
        form_message = message
        if self.game_over:
            form_message += " Game over!!!"
        elif (self.turn == 0):
            if(self.player1_turn):
                form_message += " Player1 required to place ships."
            if(self.player2_turn):
                form_message += " Player2 required to place ships."
        elif (self.player1_turn):
            form_message += " It's Player1's turn."
        elif (self.player2_turn):
            form_message += " It's Player2's turn."
        form.message = form_message
        return form

    def end_game(self, user):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=user, date=date.today(), won=True,
                      guesses=self.turn)
        score.put()
        winner = user.get()
        print "winner: ", winner.name
        winner.wins += 1
        winner.winloss_ratio = float(
            winner.wins / (winner.wins + winner.losses))
        winner.total_guesses += self.turn
        winner.put()
        if self.player1 == user:
            loser_key = self.player2
        else:
            loser_key = self.player1
        score = Score(user=loser_key, date=date.today(), won=False,
                      guesses=self.turn)
        score.put()
        loser = loser_key.get()
        loser.losses += 1
        loser.winloss_ratio = float(loser.wins / (loser.wins + loser.losses))
        loser.total_guesses += self.turn
        loser.put()

    def get_board(self, user):
        if self.player1 == user.key:
            return self.board_ship2
        elif self.player2 == user.key:
            return self.board_ship1

    def set_board_point(self, user, d, type):
        if self.player1 == user.key:
            self.board_ship2[d] = type
        elif self.player2 == user.key:
            self.board_ship1[d] = type

    def get_board_point(self, user, d):
        if self.player1 == user.key:
            return self.board_ship2[d]
        elif self.player2 == user.key:
            return self.board_ship1[d]

    def get_board_point_fire(self, user, d):
        if self.player1 == user.key:
            return self.board_ship1[d]
        elif self.player2 == user.key:
            return self.board_ship2[d]

    def set_ship(self, user, ship_type):
        if self.player1 == user.key:
            self.ships1[ship_type - 1] = 1
            if (sum(self.ships1) == ShipTypes):
                self.player1_turn = False
        elif self.player2 == user.key:
            self.ships2[ship_type - 1] = 1
            if (sum(self.ships2) == ShipTypes):
                self.player2_turn = False
        self.advance_turn()

    def advance_turn(self):
        if self.turn == 0:
            if not self.player2_turn and not self.player1_turn:
                self.turn += 1
                self.player1_turn = True
                self.player2_turn = False
        elif self.player1_turn:
            self.player1_turn = False
            self.player2_turn = True
        elif self.player2_turn:
            self.player1_turn = True
            self.player2_turn = False
            self.turn += 1

    def check_ship(self, user, ship_type):
        if self.player1 == user.key:
            return self.ships1[ship_type - 1] == 0
        elif self.player2 == user.key:
            return self.ships2[ship_type - 1] == 0

    def sink_ship(self, user, ship_type):
        if self.player1 == user.key:
            self.ships2[ship_type - 1] = -1
            if (sum(self.ships2) == -ShipTypes):
                self.end_game(user.key)
        elif self.player2 == user.key:
            self.ships1[ship_type - 1] = -1
            if (sum(self.ships1) == -ShipTypes):
                self.end_game(user.key)

    def already_fired(self, user, d):
        if self.player1 == user.key:
            return self.board_hit2[d]
        elif self.player2 == user.key:
            return self.board_hit1[d]

    def set_fired(self, user, d):
        if self.player1 == user.key:
            self.board_hit2[d] = True
        elif self.player2 == user.key:
            self.board_hit1[d] = True
        self.advance_turn()


class Ship(ndb.Model):
    """Ship Object"""
    user = ndb.KeyProperty(required=True, kind='User')
    game = ndb.KeyProperty(required=True, kind='Game')
    type = ndb.IntegerProperty(required=True)
    position = ndb.IntegerProperty(repeated=True)
    hits = ndb.IntegerProperty(required=True)

    def place_ship(self, game, user, type, start_position, end_position):
        """Create and place ship on board"""
        self.game = game.key
        self.user = user.key
        self.type = int(type)
        self.hits = 0
        if not game.check_ship(user, self.type):
            raise ValueError('Ship already placed')
        start = Point()
        start.PointFromCoordinate(game.rows, game.columns, start_position)
        start.PointFromCoordinate(game.rows, game.columns, start_position)
        end = Point()
        end.PointFromCoordinate(game.rows, game.columns, end_position)
        if (not start.valid):
            raise ValueError('Incorrect start position')
        if (not end.valid):
            raise ValueError('Incorrect end position')
        positions = []

        for a in range(game.rows):
            s = ""
            for b in range(game.columns):
                ab = str(game.board_ship2[(a) * game.columns + b])
                if len(ab) == 1:
                    ab = " " + ab
                s = s + ab + "|"
            print s, "\n"

        if(start.x == end.x):
            if abs(start.y - end.y) + 1 != self.length():
                raise ValueError('Not compatible start and end positions')
            min_y = min(start.y, end.y)
            max_y = max(start.y, end.y)
            for i in range(min_y, max_y + 1):

                p = Point()
                p.PointFromXY(game.rows, game.columns, start.x, i)
                if (not p.valid):
                    raise ValueError('Incorrect position to place ship')
                # check whether point is occupied or not
                if(game.get_board_point(user, p.d) != 0):
                    raise ValueError(
                        'Occupied position to place ship: %s val:%s' % (
                            p.coordinate,
                            game.get_board_point(user, p.d))
                    )
                # flag cells near to a ship
                positions.append(p.d)
                game.set_board_point(user, p.d, self.type)
                # Flag neighbour positions
                for j in range(2):
                    k = j * 2 - 1
                    n = Point()
                    n.PointFromXY(game.rows, game.columns, start.x + k, i)
                    if (n.valid):
                        game.set_board_point(user, n.d, -1)
            # Flag neighbour positions
            n = Point()
            n.PointFromXY(game.rows, game.columns, start.x, min_y - 1)
            if(n.valid):
                game.set_board_point(user, n.d, -1)
            n = Point()
            n.PointFromXY(game.rows, game.columns, start.x, max_y + 1)
            if(n.valid):
                game.set_board_point(user, n.d, -1)
        elif(start.y == end.y):
            if abs(start.x - end.x) + 1 != self.length():
                raise ValueError('Not compatible start and end positions')
            min_x = min(start.x, end.x)
            max_x = max(start.x, end.x)
            for i in range(min_x, max_x + 1):
                p = Point()
                p.PointFromXY(game.rows, game.columns, i, start.y)
                if (not p.valid):
                    raise ValueError('Incorrect position to place ship')
                if(game.get_board_point(user, p.d) != 0):
                    raise ValueError('occupied position to place ship')
                positions.append(p.d)
                game.set_board_point(user, p.d, self.type)
                # Flag neighbour positions
                for j in range(2):
                    k = j * 2 - 1
                    n = Point()
                    n.PointFromXY(game.rows, game.columns, i, start.y + k)
                    if (n.valid):
                        game.set_board_point(user, n.d, -1)
            # Flag neighbour positions
            n = Point()
            n.PointFromXY(game.rows, game.columns, min_x - 1, start.y)
            if(n.valid):
                game.set_board_point(user, n.d, -1)
            n = Point()
            n.PointFromXY(game.rows, game.columns, max_x + 1, start.y)
            if(n.valid):
                game.set_board_point(user, n.d, -1)
        self.position = positions
        game.set_ship(user, self.type)

    def length(self):
        if self.type == 1:
            return 5
        elif self.type == 2:
            return 4
        elif self.type == 3:
            return 3
        elif self.type == 4:
            return 3
        elif self.type == 5:
            return 2
        else:
            return -1

    def is_sank(self):
        return self.hits > 0 and self.hits == self.length()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


class History(ndb.Model):
    """User profile"""
    user = ndb.KeyProperty(required=True, kind='User')
    turn = ndb.IntegerProperty(required=True)
    player_turn = ndb.IntegerProperty(required=True)
    guess = ndb.StringProperty(required=True)
    result = ndb.StringProperty(required=True)

    def to_form(self):
        return HistoryForm(user_name=self.user.get().name, turn=self.turn,
                           player_turn=self.player_turn, guess=self.guess,
                           result=self.result)


class ShipType(messages.Enum):
    """ShipType -- ShipType and size"""
    CARRIER = 1
    BATTLESHIP = 2
    SUBMARINE = 3
    CRUISER = 4
    DESTROYER = 5


class Point:
    """Point on board with coordinates"""

    def PointFromXY(self, rows, columns, x, y):
        self.valid = True
        if(rows <= 0 or columns <= 0 or rows > 26):
            self.valid = False
        else:
            self.rows = rows
            self.columns = columns
            self.x = x
            self.y = y
            if (not (self.x >= 1 and self.x <= self.columns) or
                    not (self.x >= 1 and self.y <= self.rows)):
                self.valid = False
            else:
                self.d = (y - 1) * columns + x - 1  # 1D coordinates
                self.coordinate = str(chr(y + 64)) + str(x)

    def PointFromCoordinate(cls, rows, columns, coordinate):
        cls.valid = True
        if(rows <= 0 or columns <= 0 or rows > 26):
            cls.valid = False
        elif len(coordinate) != 2:
            cls.valid = False
        else:
            cls.rows = rows
            cls.columns = columns
            cls.coordinate = coordinate
            p = list(coordinate)
            y = ord(p[0]) - 64
            x = int(p[1])
            if (not (x >= 1 and x <= cls.columns) or
                    not (x >= 1 and y <= cls.rows)):
                cls.valid = False
            else:
                cls.x = x
                cls.y = y
                cls.d = (y - 1) * columns + x - 1
        return cls

    def PointFromIndex(cls, rows, columns, d):
        cls.valid = True
        if(rows <= 0 or columns <= 0 or rows > 26):
            cls.valid = False
        elif d < 0 or d > rows * columns:
            cls.valid = False
        else:
            cls.rows = rows
            cls.columns = columns
            cls.d = d
            cls.y = int(d / columns) + 1
            cls.x = d % columns + 1
            if (not (cls.x >= 1 and cls.x <= cls.columns) or
                    not (cls.x >= 1 and cls.y <= cls.rows)):
                cls.valid = False
            else:
                cls.d = (cls.y - 1) * columns + cls.x - 1
                cls.coordinate = str(chr(cls.y + 64)) + str(cls.x)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    user_name = messages.StringField(2, required=True)
    opponent_name = messages.StringField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    message = messages.StringField(5, required=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    number_of_players = messages.IntegerField(1, default=2)
    user_name = messages.StringField(2, required=True)
    opponent_name = messages.StringField(3)
    rows = messages.IntegerField(4, default=10)
    columns = messages.IntegerField(5, default=10)


class CancelGameForm(messages.Message):
    """Used to cancel a new game"""
    user_name = messages.StringField(2, required=True)


class PlaceShipForm(messages.Message):
    """Used to place ship"""
    user_name = messages.StringField(1, required=True)
    ship_type = messages.EnumField('ShipType', 2, required=True)
    start_position = messages.StringField(3, required=True)
    end_position = messages.StringField(4, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    user_name = messages.StringField(1, required=True)
    position = messages.StringField(2, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class HistoryForm(messages.Message):
    """RankingForm"""
    user_name = messages.StringField(1, required=True)
    turn = messages.IntegerField(2, required=True)
    player_turn = messages.IntegerField(3, required=True)
    guess = messages.StringField(4, required=True)
    result = messages.StringField(5, required=True)


class RankingForm(messages.Message):
    """RankingForm"""
    user_name = messages.StringField(1, required=True)
    winloss = messages.FloatField(2, required=True)
    guesses = messages.IntegerField(3, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class HistoryForms(messages.Message):
    """Return multiple RankingForms"""
    items = messages.MessageField(HistoryForm, 1, repeated=True)


class RankingForms(messages.Message):
    """Return multiple RankingForms"""
    items = messages.MessageField(RankingForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
