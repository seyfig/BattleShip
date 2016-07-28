# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import endpoints
from protorpc import remote, messages
from google.appengine.ext import ndb

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms

# BATTLESHIP
from models import Ship, Point, ShipType, History, HistoryForms
from models import PlaceShipForm, GameForms, CancelGameForm, RankingForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
CANCEL_GAME_REQUEST = endpoints.ResourceContainer(
    CancelGameForm,
    urlsafe_game_key=messages.StringField(1),)
PLACE_SHIP_REQUEST = endpoints.ResourceContainer(
    PlaceShipForm,
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
USER_RANKINGS_REQUEST = endpoints.ResourceContainer(
    RankingForms,)
GET_GAME_HISTORY_REQUEST = endpoints.ResourceContainer(
    HistoryForms,
    urlsafe_game_key=messages.StringField(1),)


@endpoints.api(name='battleship', version='v1')
class BattleshipApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        number_of_players = request.number_of_players
        user = User.query(User.name == request.user_name).get()
        opponent_key = None
        if not user:
            raise endpoints.NotFoundException(
                'A User with that user name does not exist!')
        if number_of_players != 2:
            raise endpoints.BadRequestException(
                'Number of players must be 2!')
        else:
            opponent = User.query(User.name == request.opponent_name).get()
            if not opponent:
                raise endpoints.NotFoundException(
                    'A User with that opponent name does not exists!')
            opponent_key = opponent.key
        rows = request.rows
        columns = request.columns
        try:
            game = Game.new_game(
                number_of_players,
                user.key,
                opponent_key,
                rows,
                columns)
        except ValueError:
            raise endpoints.BadRequestException('Dimensions must '
                                                'be greater than 0!')
        return game.to_form('New game is set, place your ships!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_HISTORY_REQUEST,
                      response_message=HistoryForms,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return game history."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        histories = History.query(ancestor=game.key)
        histories = histories.order(History.turn)
        histories = histories.order(History.player_turn)
        return HistoryForms(items=[history.to_form() for history in histories])

    @endpoints.method(request_message=CANCEL_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/cancel_game',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        """Cancel (resign) game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        user = User.query(User.name == request.user_name).get()
        if not user or (game.player1 != user.key and
                        game.player2 != user.key):
            raise endpoints.NotFoundException(
                'User not exist or not associated with this game')
        if game.game_over:
            raise endpoints.BadRequestException(
                'Game already ended!')
        return self._cancel_game(game, user)

    @endpoints.method(request_message=PLACE_SHIP_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/place_ship',
                      name='place_ship',
                      http_method='POST')
    def place_ship(self, request):
        """Place ship for player"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        user = User.query(User.name == request.user_name).get()
        if not user or (game.player1 != user.key and
                        game.player2 != user.key):
            raise endpoints.NotFoundException(
                'User not exist or not associated with this game')
        ship_type = request.ship_type
        if not ship_type:
            raise endpoints.NotFoundException(
                'Ship Type is not correct!')
        sp = request.start_position
        ep = request.end_position
        return self._place_ship(game, user, ship_type, sp, ep)

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move, Fire for user. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        if game.game_over:
            return game.to_form('Game already over!')
        user = User.query(User.name == request.user_name).get()
        if not user or (game.player1 != user.key and
                        game.player2 != user.key):
            raise endpoints.NotFoundException(
                'User not exist or not associated with this game')
        if ((game.player1 == user.key and not game.player1_turn) or
                (game.player2 == user.key and not game.player2_turn)):
            return game.to_form("It's not user's turn!")
        position = request.position
        p = Point()
        p.PointFromCoordinate(game.rows, game.columns, position)
        if(not p.valid):
            raise endpoints.BadRequestException('Incorrect position')
        if (game.already_fired(user, p.d)):
            return game.to_form('Position already fired!')
        at_position = game.get_board_point_fire(user, p.d)
        return self._make_move(game, user, at_position, p)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='game/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's continuing games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'User with that name does not exist!')
        games = Game.query(
            (Game.player1 == user.key or
                Game.player2 == user.key) and
            not Game.game_over)
        return GameForms(items=[game.to_form("") for game in games])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_RANKINGS_REQUEST,
                      response_message=RankingForms,
                      path='rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Returns users sorted by their rankings"""
        users = User.query()
        users.order(User.winloss_ratio)
        users.order(User.total_guesses)
        return RankingForms(items=[user.to_form() for user in users])

    @ndb.transactional(xg=True)
    def _place_ship(self, game, user, ship_type, start_position, end_position):
        try:
            ship = Ship(parent=game.key)
            ship.place_ship(game, user, ship_type,
                            start_position, end_position)
            ship.put()
            game.put()
        except ValueError as e:
            raise endpoints.BadRequestException(e)
        return game.to_form('Ship placed!')

    @ndb.transactional(xg=True)
    def _make_move(self, game, user, at_position, p):
        try:
            history = History(parent=game.key)
            history.user = user.key
            history.guess = p.coordinate
            history.turn = game.turn
            if game.player1_turn:
                history.player_turn = 1
            else:
                history.player_turn = 2
            if at_position <= 0:
                message = 'Miss!'
                history.result = 'miss'
                history.put()
                game.set_fired(user, p.d)
                game.put()
            else:
                message = "Hit!"
                history.result = 'hit'
                ships_query = Ship.query(ancestor=game.key)
                filter_query = ndb.query.FilterNode('user', '=', user.key)
                ships_query1 = ships_query.filter(filter_query)
                filter_query = ndb.query.FilterNode('type', '=', at_position)
                ships_query2 = ships_query1.filter(filter_query)
                ship = ships_query2.get()
                if not ship:
                    filter_query = ndb.query.FilterNode(
                        'type', '=', str(at_position))
                    ships_query3 = ships_query1.filter(filter_query)
                    ship = ships_query3.get()
                ship.hits += 1
                game.set_fired(user, p.d)
                if(ship.is_sank()):
                    message += " Ship %s sank" % ShipType(at_position)
                    game.sink_ship(user, at_position)
                history.put()
                ship.put()
                game.put()
        except ValueError as e:
            raise endpoints.BadRequestException(e)
        return game.to_form(message)

    @ndb.transactional(xg=True)
    def _cancel_game(self, game, user):
        try:
            if(game.player1 == user.key):
                game.end_game(game.player2)
            elif (game.player2 == user.key):
                game.end_game(game.player1)
            return game.to_form('You resigned from game, '
                                'you have lost the game!')
        except ValueError as e:
            raise endpoints.BadRequestException(e)


api = endpoints.api_server([BattleshipApi])
