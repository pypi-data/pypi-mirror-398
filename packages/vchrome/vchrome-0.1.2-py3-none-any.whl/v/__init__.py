import sys
from vchrome import *
Chrome.C = Chrome
Chrome.Chrome = Chrome
sys.modules[__name__] = Chrome