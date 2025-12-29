import sys,os
from colorama import Fore
class Debug:
    Logs = {}
    Orderes = []
    All = "All"
    Warn = "WARN"
    Info = "INFO"
    Error_Info = "ERROR INFO"
    Error = "ERROR"
    @staticmethod
    #Adds a log to list
    def Log(log:str|list,log_type:str = "INFO") -> None:
        if log_type not in Debug.Logs:
            Debug.Logs[log_type] = []
        Debug.Logs[f"{log_type}"].append(log)
        Debug.Orderes.append((log_type,log))
    @staticmethod
    #Adds a log to list and write this to console
    def Write(log:str|list,log_type:str = "INFO") -> None:
        Debug.Log(log,log_type)
        print({log_type:log})
    @staticmethod
    #Deletes a log from logs
    def Delete(log:str) -> None:
        try:
            Debug.Logs.remove(log)
        except Exception:
            print(f"can't find '{log}' in debug logs")
    @staticmethod
    #Returns the logs
    def Array(deb_arr:list | None = None) -> list:
        if deb_arr is None:
            deb_arr = Debug.Orderes
        return deb_arr
    @staticmethod
    #Shows the logs
    def Show(log_type:str|list = "All") -> None:
        if log_type != Debug.All:
            if log_type in Debug.Logs:
                print("============DEBUG LOGS=========")
                for l_type,log in Debug.Orderes:
                    print(f"[{l_type}]:{log}"if l_type == log_type else "")
                print("===============================")
            else:
                print("There is no Debug logs")
        if log_type == Debug.All:
            print("============DEBUG LOGS=========")
            for l_type,log in Debug.Orderes:
                print(f"[{l_type}]:{log}")     
            print("===============================")
    @staticmethod
    #Ends the program
    def Break() -> None:
        sys.exit()
    @staticmethod
    def Warning(warn_log:str) -> None:
        print(Fore.RED)
        print(warn_log)
        print(Fore.RESET)
        Debug.Log(f"[WARN]:{warn_log}")
    @staticmethod
    def BreakWCode(exit_code:int) -> None:
        sys.exit(exit_code)
    @staticmethod
    def BreakWWarn(warn:str) -> None:
        Debug.Log(f"[WARN]:{warn}")
        print(Fore.RED)
        print(warn)
        sys.exit()
    @staticmethod
    def Save_Log() -> None:
        folder = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(folder):
            os.makedirs(os.path.join(folder,"logs"))
        else:
            pass
        main = os.path.join(folder,"logs")
        logs = sorted([os.path.join(main,log) for log in os.listdir(main) if log.endswith(".txt") and log.startswith("log")])
        log_index = len(logs) + 1
        with open(os.path.join(main,f"log{log_index}.txt"),"w",encoding = "utf-8") as file:
            for l_type,log in Debug.Orderes:
                file.write(f"[{l_type}]:{log}\n")