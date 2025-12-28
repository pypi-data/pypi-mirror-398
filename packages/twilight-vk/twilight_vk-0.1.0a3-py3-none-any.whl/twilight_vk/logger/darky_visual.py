import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

class VisualMeta(type):

    '''Automatic attribute formatting'''

    def __getattribute__(cls, name):
        attr = super().__getattribute__(name)
        if name != 'prefix' and isinstance(attr, str) and attr.isdigit():
            return f"{cls.prefix}{attr}m"
        return attr

    def __getattr__(cls, name):
        logger.warning(f"Attribute '{name}' not found in '{cls.__name__}'")
        return f"<{cls.__name__}.{name}>"

class Visual(metaclass=VisualMeta):

    '''Styles for print functions and etc'''

    prefix = "\033["
    
    @staticmethod
    def ansi(silent:bool=False) -> None:
        if os.name == "nt":
            os.system('')
            if silent==False:
                logger.info(f"ANSI support initiated!")

    @staticmethod
    def hex_to_rgb(hex:str) -> tuple[int, int, int]:
        '''
        Converts HEX code to RGB

        :param hex: your hex code need to be converted to rgb code
        :type hex: str

        :returns: tuple of RGB integers (R, G, B)
        '''
        hex = hex.lstrip("#")

        if len(hex) not in (3, 6):
            raise ValueError(f"Invalid HEX code: #{hex}")
        
        if len(hex) == 3:
            hex = ''.join(c * 2 for c in hex)
            
        return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def CUSTOM_COLOR(color: str = "#FFF") -> str:
        pass
    
    @staticmethod
    def GRADIENT(text: str | list[str], colors: list = ["#FFF"]) -> str:
        pass


class STYLE(Visual):
    RESET = "0"
    BOLD = "1"
    DIM = "2"
    ITALIC = "3"
    UNDERLINE = "4"
    BLINK = "5"
    NEGATIVE = "7"
    INVISIBLE = "8"
    CROSS = "9"

class FG(STYLE):
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    PURPLE = "35"
    CIAN = "36"
    WHITE = "37"

    @staticmethod
    def CUSTOM_COLOR(color:str="#FFFFFF") -> str:
        r, g, b = Visual.hex_to_rgb(color)
        return f"{Visual.prefix}{"3"}8;2;{r};{g};{b}m"
    
    @staticmethod
    def GRADIENT(text:str|list[str], colors:list=["#FFFFFF"]) -> str:

        '''
        Returns the prepared gradient text
        
        :param text: - input text to gradient
        :type text: str

        :param colors: - list of HEX colors for gradient
        :type colors: list
        '''

        if len(colors) == 0:
            return text

        if len(colors) == 1:
            return f"{FG.CUSTOM_COLOR(colors[0])}{text}{STYLE.RESET}"
        
        #handling multilined text(ansii art support)
        if "\n" in text or isinstance(text, list):
            if not isinstance(text, list):
                lines = text.split('\n')
            else:
                lines = text.copy()
            for line in range(len(lines)):
                lines[line] = FG.GRADIENT(lines[line], colors)
            return f"{'\n'.join(lines)}{STYLE.RESET}"

        rgb = [Visual.hex_to_rgb(color) for color in colors]

        segment = len(text) // (len(colors)-1) #HelloWorld (RED to BLUE) segment = 10 // (2-1) 10

        result = ""
        for i in range(len(colors) - 1): #grabs the pair of colors even if there as more of them

            start_r, start_g, start_b = rgb[i]
            end_r, end_g, end_b = rgb[i+1]

            for step in range(segment):
                if i * segment + step >= len(text):
                    break
                char = text[i * segment + step]
                r = int(start_r + (end_r - start_r) * (step / segment))
                g = int(start_g + (end_g - start_g) * (step / segment))
                b = int(start_b + (end_b - start_b) * (step / segment))
                color_code = f"{Visual.prefix}{"3"}8;2;{r};{g};{b}m"
                result += f"{color_code}{char}"

        return f"{result}{STYLE.RESET}"

class BG(STYLE):
    BLACK = "40"
    RED = "41"
    GREEN = "42"
    YELLOW = "43"
    BLUE = "44"
    PURPLE = "45"
    CIAN = "46"
    WHITE = "47"

    @staticmethod
    def CUSTOM_COLOR(color:str="#FFFFFF") -> str:
        r, g, b = Visual.hex_to_rgb(color)
        return f"{Visual.prefix}{"4"}8;2;{r};{g};{b}m"
    
    @staticmethod
    def GRADIENT(text:str|list[str], colors:list=["#FFFFFF"]) -> str:

        '''
        Returns the prepared gradient text
        
        :param text: - input text to gradient
        :type text: str

        :param colors: - list of HEX colors for gradient
        :type colors: list
        '''

        if len(colors) == 0:
            return text

        if len(colors) == 1:
            return f"{BG.CUSTOM_COLOR(colors[0])}{text}{STYLE.RESET}"
        
        #handling multilined text(ansii art support)
        if "\n" in text or isinstance(text, list):
            if not isinstance(text, list):
                lines = text.split('\n')
            else:
                lines = text.copy()
            for line in range(len(lines)):
                lines[line] = BG.GRADIENT(lines[line], colors)
            return f"{'\n'.join(lines)}{STYLE.RESET}"

        rgb = [Visual.hex_to_rgb(color) for color in colors]

        segment = len(text) // (len(colors)-1) #HelloWorld (RED to BLUE) segment = 10 // (2-1) 10

        result = ""
        for i in range(len(colors) - 1): #grabs the pair of colors even if there as more of them

            start_r, start_g, start_b = rgb[i]
            end_r, end_g, end_b = rgb[i+1]

            for step in range(segment):
                if i * segment + step >= len(text):
                    break
                char = text[i * segment + step]
                r = int(start_r + (end_r - start_r) * (step / segment))
                g = int(start_g + (end_g - start_g) * (step / segment))
                b = int(start_b + (end_b - start_b) * (step / segment))
                color_code = f"{Visual.prefix}{"4"}8;2;{r};{g};{b}m"
                result += f"{color_code}{char}"

        return f"{result}{STYLE.RESET}"