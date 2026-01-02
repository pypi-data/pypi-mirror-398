import os, re, sys


class Log4j(object):

    formatters = {
        "d": "(asctime)s.%(msecs)03d",
        "p": "(levelname)s",
        "t": "(threadName)s",
        "C": "(module)s",
        "M": "(funcName)s",
        "L": "(lineno)d",
        "m": "(message)s",
        "n": "",  # new line
    }
    dateFormatters = {
        "y": "%y",
        "Y": "%Y",
        "M": "%M",
        "m": "%m",
        "H": "%H",
        "h": "%h",
        "D": "%D",
        "d": "%d",
        "S": "%f",
        "s": "%s",
    }

    def __init__(
        self,
        quiet=False,
        print_detail=False,
        log4j_log_file="all.log",
        skip_log4j_config_file=False,
    ):
        self.quiet = quiet
        self.print_detail = print_detail
        self.log4j_log_file = log4j_log_file
        self.skip_log4j_config_file = skip_log4j_config_file
        # print("---log4j_log_file", log4j_log_file)
        self.properties = {
            "filename": log4j_log_file,
            "level": "info",
            "when": "D",
            "backCount": 3,
            "maxFileSize": "",
            "fmt": "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s",
            "encoding": "utf-8",
            "datestr": "%Y-%m-%d %H:%M:%S",
        }

    # yy-MM-dd HH:mm:ss.SSS
    def parseDateStr(self, datestr):
        if datestr:
            return self.properties["datestr"]
        datestr = datestr[1 : len(datestr) - 2]
        chars = []
        oldChar = ""
        for c in datestr:
            if c in self.dateFormatters:
                if not c == oldChar:
                    chars.append(self.dateFormatters[c])
            else:
                chars.append(c)
            oldChar = c
        return "".join(chars)

    def parseFormatter(self, formatter):
        fmts = []
        for line in formatter.split("%"):
            mo = re.match(r"([^a-zA-Z])*([a-zA-Z])(\{[^\{\}]+\})*(.)*", line.lstrip())
            if mo:
                c = mo.group(2)
                other = mo.group(4)
                p = self.formatters[c]
                fmts.append(
                    ("%" if p.startswith("(") else "") + p + (other if other else "")
                )
                if c == "d":
                    self.properties["datestr"] = self.parseDateStr(mo.group(3))
        return "".join(fmts)

    def parseLine(self, line):
        prop = self.properties
        if not line.startswith("#"):
            if "log4j.rootLogger" in line or "log4j.logger" in line:
                prop["level"] = line.split("=")[1].strip().split(",")[0]
        if line.startswith("log4j.appender"):
            if ".File=" in line:
                prop["filename"] = line.split("=")[1].strip().split(",")[0]
            if ".MaxBackupIndex=" in line:
                # backCount必须是个整数    if self.backupCount > 0:
                #     TypeError: '>' not supported between instances of 'str' and 'int'
                prop["backCount"] = int(line.split("=")[1].strip().split(",")[0])
            if ".MaxFileSize=" in line:
                prop["maxFileSize"] = line.split("=")[1].strip().split(",")[0]
            if ".ConversionPattern=" in line:
                prop["fmt"] = self.parseFormatter(line.split("=")[1])

    def load(self):
        try:
            if (not self.skip_log4j_config_file) and os.path.exists("log4j.properties"):
                print("log4j file is", os.path.abspath("log4j.properties"))
                with open("log4j.properties", "r+") as pf:
                    for line in pf.readlines():
                        self.parseLine(line)
            else:
                if self.print_detail:
                    print("log4j.properties is not found in", os.path.abspath("."))
                    print("use default log4j configuration")
        except Exception as e:
            print("unwanted", "e")
        return self


if __name__ == "__main__":
    print("unwanted invoked")
