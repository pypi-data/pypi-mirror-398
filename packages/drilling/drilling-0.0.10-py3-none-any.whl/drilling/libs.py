import pandas as pd
import yaml

import sys 
from pathlib import Path
import ipynbname

from datetime import datetime, timedelta
# SQLAlchemy
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, DateTime, Integer, Boolean, Time, Date, Numeric, inspect, insert, text
)
