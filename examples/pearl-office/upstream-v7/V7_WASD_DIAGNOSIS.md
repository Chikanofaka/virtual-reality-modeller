# V7 WASD diagnosis

## Concrete stale-runtime problem found
The Safari screenshots supplied after V6 still visibly showed the V5 HUD label (`MAIN REPO + SIGNAL NAVIGATION V5`). All earlier builds reused localhost:8015, so an older Python server or Safari cache could continue serving V5 even when a newer folder was downloaded. V7 uses a new port (8027), a new JavaScript filename (`app_v7.js`), and a cache-busting query string.

## Keyboard hardening
V7 accepts physical WASD via three KeyboardEvent identifiers:
- `event.code` (`KeyW`, etc.)
- `event.key` (`w`, `a`, `s`, `d`)
- legacy `keyCode` / `which` (87/65/83/68)

Listeners exist at window, document, and canvas capture levels, deduplicated using a WeakSet. Clicking or dragging the canvas restores focus to it. The HUD reports the last raw keyboard event and active focus target.

## Navigation hardening
The whole office shell is now one continuous walkable polygon. The detailed visual model is unchanged. The only special interior barrier retained in navigation is the Pearl Office glass ring, with its approved portal opening. This removes all room-island/corridor-gap dead zones as a cause of failed WASD movement.

## Diagnostic D-pad
The W/A/S/D buttons at bottom-left drive the same `keys` state as the physical keyboard. If the D-pad moves the camera but a physical W does not, the remaining problem is Safari/macOS keyboard delivery/focus. If neither moves it, the problem is locomotion/render state and the HUD coordinates expose that immediately.
