import random
from models.db import Db, pd
from models.bro_clicks.initial_routes import InitialRoutes, ForeignInitialRoutes
from calendar import monthrange
import datetime as dt
from models import config
from threading import Thread, Lock
from copy import deepcopy