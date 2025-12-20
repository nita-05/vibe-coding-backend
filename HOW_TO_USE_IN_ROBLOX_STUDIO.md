
# How to Use Generated Code in Roblox Studio

Follow these steps every time you want to play-test a generated script inside Roblox Studio.

---

## 1. Copy the code

1. Generate a script in the Vibe Coding UI.
2. Click **Copy Code** (from the code editor or Game Preview card).

The Lua source is in your clipboard.

---

## 2. Open Roblox Studio

1. Launch Roblox Studio.
2. Click **File → New → Baseplate** (or any template you prefer).

---

## 3. Insert a new script

1. In the **Explorer** panel (right side), find `ServerScriptService`.
2. Right-click → **Insert Object → Script**.
3. Double-click the new `Script` to open the editor.
4. Select all default code (`Ctrl+A`) and delete.
5. Paste (`Ctrl+V`) the generated Lua code.

> Tip: rename the script to something meaningful, e.g. `VibeMainScript`.

---

## 4. Play-test

1. Click the green **Play** button (or press `F5`).
2. Roblox loads the place with your generated logic.
3. Use **W A S D** + mouse to move; follow on-screen chat instructions.
4. Stop the session with the red **Stop** button (or `Shift+F5`).

---

## 5. Iterating quickly

1. Stop the game (`Shift+F5`).
2. Paste new code over the same script.
3. Click Play again.

No need to reinsert a new script each time.

---

## 6. Publishing manually

If you don’t use the automatic Open Cloud publishing:

1. Click **File → Publish to Roblox**.
2. Select an existing place or create a new one.
3. Roblox Studio uploads your local changes.

---

## 7. Troubleshooting

| Issue | Fix |
|-------|-----|
| Game loads but nothing happens | Ensure the script is inside `ServerScriptService`, not `Workspace`. |
| Touch events don’t react | Make sure you pasted the entire script (no missing lines). |
| Chat instructions missing | Check the **Output** window for errors (View → Output). |
| Only one team/flag appears | Re-run generation; new prompts now enforce both bases/flags. |

---

You’re ready to test every generated game directly inside Roblox Studio. Have fun exploring!

