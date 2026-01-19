# 🎮 Vibe Studio - User Guide

**Create Roblox games with AI-powered code generation!**

---

## 🚀 Quick Start

### Step 1: Access the IDE
1. Open your browser and go to **http://localhost:5173** (or your deployed URL)
2. You'll see the **Vibe Studio** interface

### Step 2: Sign In (Optional but Recommended)
- Click **"Sign In"** in the top-right corner
- Choose:
  - **Email/Password**: Create an account with email
  - **Google Sign-In**: Quick sign-in with your Google account
- **Why sign in?** Your projects are saved to the cloud and accessible from any device!

### Step 3: Generate Your First Game
1. Click the **"Generate"** button (sparkles icon) in the top toolbar
2. Enter a prompt describing your game, for example:
   - `"Create a coin collector game with obstacles"`
   - `"Make a racing game with 3 laps and checkpoints"`
   - `"Build an obby with 10 floating platforms"`
3. Click **"Generate"** and wait a few seconds
4. Your game code will appear in the editor!

---

## 📝 Using the IDE

### **File Explorer (Left Sidebar)**
- **View all files** in your project as a tree
- **Click any file** to open it in the editor
- **Right-click** files/folders for:
  - ✏️ **Rename**
  - ➕ **New File** / **New Folder**
  - 🗑️ **Delete**

### **Editor (Center)**
- **Edit code** directly in the Monaco editor
- **Syntax highlighting** for Lua
- **Auto-complete** Roblox APIs (type `game:` or `Instance.` to see suggestions)
- **Real-time error detection** (red squiggles = syntax errors)
- **Multiple tabs** - open several files at once
- **Split view** - click the grid icon to edit two files side-by-side

### **AI Panel (Right Side)**
- **Ask questions** about your code
- **Explain code** - Select code → Click "Explain"
- **Fix errors** - Select broken code → Click "Fix"
- **Generate code** - Type what you need → Click "Insert" or "Replace"
- **Chat with AI** - Type any question in the input box

### **Search & Replace**
- Press **Ctrl+F** (or Cmd+F on Mac) to search
- Search in **current file** or **all files**
- Use **regex** for advanced patterns
- **Replace** text across multiple files

### **Code Formatting**
- Click the **format button** (align icon) or press **Ctrl+Shift+F**
- Automatically indents and cleans up your Lua code

---

## 💾 Saving & Loading Projects

### **Save Your Project**
1. Click **"Save"** button in the top toolbar
2. Enter a project name (e.g., "My Racing Game")
3. Your project is saved to the cloud!
4. **Auto-save**: If you're signed in, your last project auto-loads when you return

### **Load Saved Projects**
1. Click **"Projects"** button (folder icon) in the top toolbar
2. See all your saved projects
3. **Search** by name
4. Click **"Load"** to open a project
5. **Rename** or **Delete** projects using the icons

---

## 🎯 Creating Games - Complete Workflow

### **Method 1: Generate from Prompt (Recommended)**
1. Click **"Generate"** button
2. Describe your game in natural language:
   ```
   "Create a coin collector game with:
   - 50 coins scattered randomly
   - Moving obstacles
   - Score UI showing coins collected
   - Win message at 25 coins"
   ```
3. Wait 10-30 seconds for AI to generate code
4. Review the generated files in the editor
5. Edit if needed
6. **Save** your project
7. **Copy code** to Roblox Studio (see below)

### **Method 2: Start from Scratch**
1. Click **"+"** in File Explorer to create a new file
2. Name it (e.g., `ServerScriptService/Main.server.lua`)
3. Start coding or use **AI Panel** to generate code
4. Save your project

### **Method 3: Load Existing Project**
1. Click **"Projects"** button
2. Select a saved project
3. Continue editing
4. Save changes (updates the same project)

---

## 🤖 Using AI Features

### **Explain Code**
1. **Select** code in the editor
2. Click **"Explain"** in AI Panel
3. AI explains what the code does

### **Fix Errors**
1. **Select** broken code (or entire file)
2. Click **"Fix"** in AI Panel
3. AI suggests fixes

### **Generate New Code**
1. Type what you need in the AI input box:
   ```
   "Add a timer that counts down from 60 seconds"
   ```
2. Click **"Insert"** to add at cursor, or **"Replace"** to replace selection
3. Or click **"Insert into editor"** / **"Replace selection"** buttons

### **Chat with AI**
- Type any question in the AI input box
- Press **Enter** to send
- AI responds with helpful code suggestions

---

## 📤 Exporting to Roblox Studio

### **Step 1: Copy Code**
1. In the IDE, open the file you want to copy
2. **Select all** (Ctrl+A / Cmd+A)
3. **Copy** (Ctrl+C / Cmd+C)

### **Step 2: Paste into Roblox Studio**
1. Open **Roblox Studio**
2. Create a **new place** (File → New → Baseplate)
3. In **Explorer**, right-click `ServerScriptService` → **Insert Object → Script**
4. **Delete** the default code
5. **Paste** your code (Ctrl+V / Cmd+V)
6. Click **Play** ▶️
7. Your game should appear!

### **Step 3: Test Your Game**
- Walk around, test mechanics
- Check if UI appears
- Verify scoring/collectibles work
- Fix any issues using the IDE's AI features

---

## 🎨 IDE Features Overview

| Feature | How to Use |
|---------|-----------|
| **Multi-file editing** | Click files in explorer to open tabs |
| **Split view** | Click grid icon → Click another tab |
| **Search** | Press Ctrl+F → Type search term |
| **Format code** | Click format icon or Ctrl+Shift+F |
| **AI help** | Select code → Click Explain/Fix/Insert |
| **Save project** | Click Save → Enter name |
| **Load project** | Click Projects → Click Load |
| **Rename file** | Right-click file → Rename |
| **Delete file** | Right-click file → Delete |

---

## 💡 Tips & Best Practices

### **Writing Good Prompts**
✅ **Good prompts:**
- `"Create a coin collector with 50 coins, obstacles, and score UI"`
- `"Make a racing game: 3 laps, checkpoints every 100 studs, lap counter"`
- `"Build an obby: 10 floating platforms, moving obstacles, finish line"`

❌ **Vague prompts:**
- `"Make a game"` (too generic)
- `"Something fun"` (not specific)

### **Editing Generated Code**
- Use **AI Panel** to explain complex code
- **Fix errors** using the Fix button
- **Add features** by asking AI: "Add a timer UI"
- **Test incrementally** - save often!

### **Project Management**
- **Name projects clearly**: "Racing Game v1", "Coin Collector Final"
- **Save frequently** - your work is auto-saved to cloud
- **Use Projects modal** to organize multiple games

---

## 🔧 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+F` / `Cmd+F` | Open search |
| `Ctrl+Shift+F` / `Cmd+Shift+F` | Format code |
| `Ctrl+S` / `Cmd+S` | Save (if implemented) |
| `Enter` | Send AI message |
| `Shift+Enter` | New line in AI input |

---

## ❓ Troubleshooting

### **"Not authenticated" error**
- Sign in using the top-right avatar menu
- Projects require authentication to save

### **AI not responding**
- Check your internet connection
- Backend needs `OPENAI_API_KEY` configured
- Try refreshing the page

### **Code doesn't work in Roblox Studio**
- Make sure you pasted into the correct location (`ServerScriptService` for server scripts)
- Check for syntax errors (red squiggles in IDE)
- Use AI "Fix" button to resolve errors
- Verify all required files are included

### **Can't see files in explorer**
- Click the **menu icon** (☰) on mobile/tablet to open sidebar
- Files appear after you generate or create them

---

## 🎓 Example: Creating a Coin Collector Game

1. **Sign in** (optional but recommended)
2. Click **"Generate"**
3. Enter prompt:
   ```
   Create a coin collector game with:
   - 50 glowing yellow coins scattered randomly
   - Red obstacles that kill the player
   - Score UI showing coins collected
   - Win message when player collects 25 coins
   ```
4. Wait for generation (10-30 seconds)
5. **Review files** in the editor:
   - `ServerScriptService/CoinService.server.lua` - Coin spawning logic
   - `ServerScriptService/HazardManager.server.lua` - Obstacle handling
   - `StarterPlayer/StarterPlayerScripts/GameUI.client.lua` - UI display
6. **Edit if needed** (use AI to add features)
7. Click **"Save"** → Name it "Coin Collector"
8. **Copy each file** to Roblox Studio
9. **Test in Roblox Studio** - Click Play!

---

## 🚀 Ready to Create?

**Your IDE is fully functional and ready for real users!**

- ✅ Real authentication (Google OAuth + Email/Password)
- ✅ Real project saving (cloud storage)
- ✅ Real AI code generation (OpenAI)
- ✅ Real Lua syntax validation
- ✅ Real Roblox IntelliSense
- ✅ Real file operations (create/rename/delete)

**Start creating amazing Roblox games!** 🎮✨
