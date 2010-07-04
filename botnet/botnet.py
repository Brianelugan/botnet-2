'''
Created on Apr 1, 2010

@author: victorhg
'''
import finance
from eliza import eliza
from gtalkbot import GTalkBot, botcommand
from yahoo import YahooGeoPlanetSearch, YahooWeatherSearch, InvalidSearchError

class BotnetJabberClient(GTalkBot):

    BOT_USER = 'pycon.bot@gmail.com'
    BOT_PASS = 'pycon123'
    
    def __init__(self):
        self.eliza = eliza()
        super(BotnetJabberClient,self).__init__(self.BOT_USER, self.BOT_PASS)
        self.geoPlanet = YahooGeoPlanetSearch()
        self.yahooWeather = YahooWeatherSearch()

    @botcommand
    def hello(self, mess, args):
        """Greetings"""
        return "Hi! how can I help you? Type 'help' to see available commands"
    

    @botcommand
    def weather(self, mess, args):
        """Returns the forecasts for any place. Usage: weather [City Name]"""
        try:
            woeid = self.geoPlanet.place_search(args).woeid()
            result = self.format_weather_result(self.yahooWeather.forecast(woeid))
            return result.encode("utf-8")
        except InvalidSearchError:
            return "Invalid Search, plz try again"
        except Exception:
            return "Unknow error... sorry about that"

    @botcommand
    def currency(self, mess, args):
        """Returns updated information about Dollar Quotation"""
        return finance.exchange_rate()
        
    def unknown_command( self, mess, cmd, args):
        return self.eliza.respond(mess.getBody())
        
    
    def format_weather_result(self, result):
        model_header = "{0}\n {1} C - {2} \n Forecasts\n"
        model_forecasts = "{0} -> {1} with max {2} C | min {3} C\n"  
        
        forecast_result = model_header.format(result['title'], result['current_temp'], result['current_condition'])
        for forecast in result['forecasts']:
            forecast_result += model_forecasts.format(forecast['date'], forecast['condition'], forecast['high'], forecast['low'])
        
        return forecast_result
    
