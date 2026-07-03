#!/bin/bash
# Toggle script for V.E.N.U.S. Companion

exec &> "$HOME/companion/toggle.log"
echo "=== Toggle triggered at $(date) ==="
echo "User: $(whoami)"
echo "DISPLAY: $DISPLAY"
echo "XAUTHORITY: $XAUTHORITY"
echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"

if pgrep -f "companion_gui.py" >/dev/null; then
    echo "Companion is running. Killing..."
    pkill -f "companion_gui.py"
else
    echo "Companion not running. Starting..."
    
    # Determine correct environment variables
    TARGET_DISPLAY=${DISPLAY:-:0}
    
    TARGET_RUNTIME="/run/user/1000"
    if [ "$XDG_RUNTIME_DIR" != "/run/user/0" ] && [ -n "$XDG_RUNTIME_DIR" ]; then
        TARGET_RUNTIME="$XDG_RUNTIME_DIR"
    fi
    
    TARGET_DBUS="unix:path=/run/user/1000/bus"
    if [ -n "$DBUS_SESSION_BUS_ADDRESS" ] && [[ "$DBUS_SESSION_BUS_ADDRESS" != *"/run/user/0"* ]]; then
        TARGET_DBUS="$DBUS_SESSION_BUS_ADDRESS"
    fi

    TARGET_XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}

    echo "Launching with DISPLAY=$TARGET_DISPLAY XDG_RUNTIME_DIR=$TARGET_RUNTIME DBUS_SESSION_BUS_ADDRESS=$TARGET_DBUS XAUTHORITY=$TARGET_XAUTHORITY"

    # Start daemonized process using setsid
    env DISPLAY="$TARGET_DISPLAY" XDG_RUNTIME_DIR="$TARGET_RUNTIME" DBUS_SESSION_BUS_ADDRESS="$TARGET_DBUS" XAUTHORITY="$TARGET_XAUTHORITY" setsid python3 -u "$HOME/.local/bin/companion_gui.py" < /dev/null > "$HOME/companion/companion_gui.log" 2>&1 &
    
    echo "Launched."
fi
