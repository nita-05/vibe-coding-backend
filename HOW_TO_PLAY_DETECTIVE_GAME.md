# How to Play the Detective Mystery Game

## **Game Overview**
You're helping a Detective solve a mystery by finding 3 clues scattered around the map.

## **Game Elements You See:**

### **1. Detective NPC (Center)**
- The character with "Detective" label
- Stands on a white platform
- This is your quest giver

### **2. Yellow Glowing Spheres (Clues)**
- **3 yellow glowing balls** scattered on the green terrain
- These are the **clues** you need to collect
- Walk into them to collect

### **3. Green Dialogue Triggers**
- **3 green transparent platforms** (at positions 10, 20, 30)
- Walk on them to see dialogue messages
- Each trigger shows different detective dialogue

### **4. Quest Tracker (Top-Right)**
- Shows: **"Quest: Find 3 clues to solve the mystery"**
- Updates as you collect clues
- Turns green when you complete the quest

### **5. Dialogue Box (Bottom Center)**
- Appears when you touch dialogue triggers
- Shows detective messages
- Also shows when you collect clues

---

## **How to Play:**

### **Step 1: Start the Game**
1. Click **Play** in Roblox Studio
2. Your character spawns on the green baseplate

### **Step 2: Find the Clues**
1. **Walk around** the green terrain (use WASD keys)
2. **Look for yellow glowing spheres** - these are the clues
3. **Walk into a yellow sphere** to collect it
4. You'll see a message: "Clue collected! X clue(s) remaining"
5. The quest tracker updates automatically

### **Step 3: Touch Dialogue Triggers (Optional)**
1. **Walk on green transparent platforms**
2. Dialogue box appears at bottom with detective messages:
   - **Trigger 1**: "Detective: Hello, I need your help solving a case."
   - **Trigger 2**: "Detective: I think the culprit left some clues around."
   - **Trigger 3**: "Detective: You found all the clues! The mystery is solved!"

### **Step 4: Complete the Quest**
1. **Collect all 3 yellow clue spheres**
2. Quest tracker turns **green** and says: "Quest Complete! All clues found!"
3. Dialogue box shows: "Congratulations! You solved the mystery!"

---

## **Controls:**
- **W, A, S, D**: Move your character
- **Mouse**: Look around
- **Space**: Jump
- **Walk into objects**: Interact (collect clues, trigger dialogue)

---

## **What Happens When You:**
- **Touch a yellow clue**: It disappears, quest tracker updates, shows collection message
- **Walk on green trigger**: Dialogue box appears with detective message (5 seconds)
- **Collect all 3 clues**: Quest completes, victory message appears

---

## **Tips:**
- The clues are at positions: (15, 0.5, 15), (25, 0.5, 25), (35, 0.5, 35)
- Dialogue triggers are at: (10, 0.5, 10), (20, 0.5, 20), (30, 0.5, 30)
- Walk around the green baseplate to find everything
- The Detective NPC is at the center (0, 0, 0)

---

## **Customization:**
You can customize the baseplate in the script:
- Change `USE_BASEPLATE = false` to remove it
- Change `BASEPLATE_COLOR` to change ground color
- Change `BASEPLATE_MATERIAL` to change ground texture

**Enjoy solving the mystery!** 🕵️

