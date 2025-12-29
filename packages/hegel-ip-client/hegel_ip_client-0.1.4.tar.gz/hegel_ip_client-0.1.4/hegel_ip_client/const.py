"""Constants for Hegel amplifier communication."""

# Centralized command strings
COMMANDS = {
    "power_on": "-p.1\r",
    "power_off": "-p.0\r",
    "power_query": "-p.?\r",
    "volume_set": lambda level: f"-v.{level}\r",  # 0..99
    "volume_query": "-v.?\r",
    "volume_up": "-v.u\r",
    "volume_down": "-v.d\r",
    "mute_on": "-m.1\r",
    "mute_off": "-m.0\r",
    "mute_query": "-m.?\r",
    "input_set": lambda idx: f"-i.{idx}\r",  # 1..9 (depends on model)
    "input_query": "-i.?\r",
    # reset/query if needed (some amps may expose this)
    "reset_query": "-r.?\r",
}
