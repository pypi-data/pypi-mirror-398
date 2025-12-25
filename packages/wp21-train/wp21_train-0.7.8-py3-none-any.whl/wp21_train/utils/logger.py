def log_message(level, message):
    RESET = "\033[0m"
    BOLD  = "\033[1m"

    COLOURS = {
        "INFO"         : f"{BOLD}\033[34m",
        "WARNING"      : f"{BOLD}\033[33m",
        "CRIT. WARNING": f"{BOLD}\033[38;5;208m",
        "ERROR"        : f"{BOLD}\033[31m"}

    colour = COLOURS.get(level.upper(), BOLD)
    print(f"{colour}[{level.upper()}]{RESET} {message}")