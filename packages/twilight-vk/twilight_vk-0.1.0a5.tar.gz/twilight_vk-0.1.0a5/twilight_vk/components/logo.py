from ..logger.darky_visual import STYLE, FG, BG
from ..utils.config import CONFIG

class LogoComponent:

    def __init__(self):
        self._template = [
            "",
            "            ███████ ██████  ██████   ██████  ██████              ",
            "            ██      ██   ██ ██   ██ ██    ██ ██   ██             ",
            "█████ █████ █████   ██████  ██████  ██    ██ ██████  █████ █████ ",
            "            ██      ██   ██ ██   ██ ██    ██ ██   ██             ",
            "            ███████ ██   ██ ██   ██  ██████  ██   ██             ",
            "                    ---Unable to find logo---                    ",
            "           Make sure you choose the right type of logo.          "
        ]

        self._simplified_logo = [
            "",
            "  ______         _ ___       __    __ ",
            " /_  __/      __(_) (_)___ _/ /_  / /_",
            "  / / | | /| / / / / / __ `/ __ \\/ __/",
            " / /  | |/ |/ / / / / /_/ / / / / /_  ",
            "/_/   |__/|__/_/_/_/\\__, /_/ /_/\\__/  ",
            "                   /____/             "
        ]
        self._simplified_meta = f"VERSION: {CONFIG.FRAMEWORK.version}\ndeveloped by {CONFIG.FRAMEWORK.developer}"

        self._logo = [
            "",
            "  :::::::::::   :::       :::   :::::::::::   :::          :::::::::::    ::::::::    :::    :::   :::::::::::",
            "     :+:       :+:       :+:       :+:       :+:              :+:       :+:    :+:   :+:    :+:       :+:     ",
            "    +:+       +:+       +:+       +:+       +:+              +:+       +:+          +:+    +:+       +:+      ",
            "   +#+       +#+  +:+  +#+       +#+       +#+              +#+       :#:          +#++:++#++       +#+       ",
            "  +#+       +#+ +#+#+ +#+       +#+       +#+              +#+       +#+   +#+#   +#+    +#+       +#+        ",
            " #+#        #+#+# #+#+#        #+#       #+#              #+#       #+#    #+#   #+#    #+#       #+#         ",
            "###         ###   ###     ###########   ##########   ###########    ########    ###    ###       ###          "
        ]
        self._beginmeta = f"██VERSION: {CONFIG.FRAMEWORK.version}"
        self._endmeta = f"developed by {CONFIG.FRAMEWORK.developer}██"
        self._meta = f"{self._beginmeta}{"█"*(len(self._logo[-1])-len(self._beginmeta)-len(self._endmeta))}{self._endmeta}"

        self._colored_logo = FG.GRADIENT(self._logo, ["#44F", "#D0F"])
        self._colored_meta = f"{FG.BLACK}{FG.GRADIENT(self._meta, ["#44F", "#D4F"])}{STYLE.RESET}"

        self.template = "\n".join(self._template)
        self.default = "\n".join(["\n".join(self._logo), self._meta])
        self.simplified = "\n".join(["\n".join(self._simplified_logo), self._simplified_meta])
        self.colored = "\n".join([self._colored_logo, self._colored_meta])
    
    def __getattr__(self, name):
        if name not in ["simplified", "default", "colored"]:
            name = "template"
        attr = getattr(self, name)
        return attr
    
    def printAll(self):
        for types in [self.simplified, self.default, self.colored, self.test]:
            print(types)