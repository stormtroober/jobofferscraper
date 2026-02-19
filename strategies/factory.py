from strategies.justjoinit import JustJoinITStrategy
from strategies.nofluff import NoFluffJobsStrategy
from strategies.theprotocol import TheProtocolStrategy
from strategies.reply import ReplyStrategy
from strategies.bulldogjob import BulldogJobStrategy
from strategies.builtin import BuiltInStrategy

def get_strategy(url, driver):
    """
    Returns the appropriate strategy instance for the given URL.
    """
    if "nofluffjobs.com" in url:
        return NoFluffJobsStrategy(driver)
    elif "theprotocol.it" in url:
        return TheProtocolStrategy(driver)
    elif "reply.com" in url:
        return ReplyStrategy(driver)
    elif "bulldogjob.com" in url:
        return BulldogJobStrategy(driver)
    elif "builtin.com" in url:
        return BuiltInStrategy(driver)
    else:
        return JustJoinITStrategy(driver)
