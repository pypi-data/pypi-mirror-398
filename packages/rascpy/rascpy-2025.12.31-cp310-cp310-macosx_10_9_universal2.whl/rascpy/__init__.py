__version__ = '2025.12.31' 

from .Lan_CHN import CHN
from .Lan_EN import EN
import locale
if locale.getdefaultlocale()[0].split('_')[0] == 'zh':
    lan = CHN
elif locale.getdefaultlocale()[0].split('_')[0] == 'en':
    lan = EN
else:
    lan = EN
    
'''

通过改变lan的值，就可以实现语言的切换
例：加入德语的方法
from Lan_GER import GER
lan = GER

'''