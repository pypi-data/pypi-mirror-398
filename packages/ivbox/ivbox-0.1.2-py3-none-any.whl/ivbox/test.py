import os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(PARENT_DIR)

from DatabaseORM.SQLiteORM import *
import re
import requests
from datetime import datetime
import json

db = SQLiteORM("productos.db")

db.connect_DB()

# Get autoincrement primary keys