# Quack Sleep Doc

> Not an actual doctor or a serious sleep helper! If you need that consult a real doctor!

A tool that reminds you to go to bed at a time you configured.


## Setup

Then, you create a config file in `~/.config/quack-sleep/config.json`.

```json
{
    "language": "de",
    "time_gentle_reminder": "22:30",
    "time_strict_reminder": "23:00",
    "gentle_spacing_minutes": 5,
    "strict_spacing_minutes": 1,
    "countdown_initial": 15,
    "countdown_reduction": 5,
    "countdown_minimum": 1
}
```

Optionally, you can configure your own messages that remind you to go to sleep in `~/.config/quack-sleep/messages.txt`. Where each line is a message. Here is an example file in german.

```
Morgen wirst du froh sein, dass du jetzt schlafen gehst.
Schlaf ist wie ein kostenloses Upgrade.
Dein Gehirn ruft an: Es möchte ins Bett.
Produktivität beginnt mit Erholung.
Selbst KI gönnt sich Ruhezyklen – du solltest das auch.
```

Finally, once you have everything configured, you should add the script to the autostart to make sure it always runs.

**Linux**: Assuming you have screen (`apt install screen`) you can add the following to the bottom of your `~/.profile` file.

```bash
protected_screen() {
    local name="$1"
    shift

    if [ -z "$name" ]; then
        echo "Usage: protected_screen <session-name> <command> [args...]"
        return 1
    fi

    # Check if the screen session already exists
    if screen -ls | grep -q "[.]${name}[[:space:]]"; then
        echo "Screen session '$name' already exists. Skipping."
        return 0
    fi

    if [ $# -eq 0 ]; then
        echo "No command provided. Starting empty screen session '$name'."
        screen -dmS "$name"
    else
        echo "Starting screen session '$name' with command: $*"
        screen -dmS "$name" "$@"
    fi
}

protected_screen quack-sleep uvx run quack-sleep-doctor
```

**Windows**: Here we will use the ps1 script provided in the repository to launch the app. First clone the repository, then run `uv sync` to install it. Lastly, add the start.ps1 to your autostart folder.
