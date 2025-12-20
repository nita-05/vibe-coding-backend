# Troubleshooting: Can't Disable Roblox Studio Stats Overlay

If **nothing works** to disable the stats overlay, try these solutions:

## **Solution 1: Check Browser Extensions**
The overlay might be from a browser extension, not Roblox Studio:
1. Open your browser (Chrome/Edge)
2. Go to `chrome://extensions` (or `edge://extensions`)
3. Look for extensions like:
   - Performance Monitor
   - Stats Overlay
   - Developer Tools
   - Roblox Enhancer
4. **Disable** any suspicious extensions
5. Refresh Roblox Studio

## **Solution 2: Check if You're in Play Mode**
The stats might be different in Play mode:
1. **Exit Play mode** completely (press ESC → Resume, or click Stop)
2. Make sure you're in **Edit mode** (not Play mode)
3. Then try `Ctrl + Shift + F8`

## **Solution 3: Check Roblox Studio Version**
Newer versions might have different locations:
1. Click **Help** → **About** to see your version
2. Try **File** → **Settings** → **Studio** → **View** tab
3. Look for **"Show Developer Stats"** checkbox
4. Uncheck it and click **OK**

## **Solution 4: Check Test Tab**
1. Click **Test** tab at the top
2. Look for **"Show Stats"** or **"Performance Stats"** button
3. Click to toggle off

## **Solution 5: Reset Roblox Studio Settings**
1. Close Roblox Studio completely
2. Press `Win + R` (Windows) or `Cmd + Space` (Mac)
3. Type: `%LocalAppData%\Roblox\Studio\` (Windows)
   Or: `~/Library/Application Support/Roblox/Studio/` (Mac)
4. Find and delete `StudioSettings.xml` (backup first!)
5. Restart Roblox Studio (settings will reset to default)

## **Solution 6: Check if It's a Plugin**
1. Click **Plugins** tab
2. Look for any active plugins
3. Disable any stats/performance plugins

## **Solution 7: Manual Studio Settings File Edit**
1. Close Roblox Studio
2. Navigate to: `%LocalAppData%\Roblox\Studio\`
3. Open `StudioSettings.xml` in Notepad
4. Find `<ShowStats>` or `<DeveloperStats>` tag
5. Change value to `false`
6. Save and restart Studio

## **Solution 8: Check if It's Actually Roblox Studio Stats**
- If the overlay shows **Mem, CPU, GPU, Sent, Recv, NetworkPing** - it's Studio's stats
- If it shows different info, it might be a game script or extension

## **Still Not Working?**
1. **Restart Roblox Studio completely**
2. **Restart your computer**
3. **Update Roblox Studio** (Help → Check for Updates)
4. **Reinstall Roblox Studio** (last resort)

---

**Most Common Issue:** The stats toggle is usually in:
- **View tab** → Toolbar button (not dropdown)
- **File** → **Studio Settings** → **View** section
- Keyboard shortcut: `Ctrl + Shift + F8`

Try Solution 1 (browser extensions) first - that's often the culprit!

