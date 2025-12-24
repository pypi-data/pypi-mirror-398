# License Guide for Gemini SRE Client

## Chosen License: MIT License

This project uses the **MIT License** - one of the most permissive and popular open-source licenses.

## What This Means

### ✅ For Users (What They CAN Do)

Users of your library have **complete freedom** to:

1. **Use** - Use the software for any purpose (personal, commercial, educational)
2. **Modify** - Change the code however they want
3. **Distribute** - Share the original or modified versions
4. **Sublicense** - Include it in proprietary software
5. **Sell** - Use it in commercial products they sell

**No restrictions.** They don't need to:
- Ask your permission
- Pay you anything
- Share their modifications
- Open-source their code
- Credit you (though they must include the license notice)

### 🛡️ For You (Your Protection)

**Zero Liability Protection**:
- You have **NO responsibility** for how people use this library
- You provide **NO warranty** (code is "AS IS")
- You are **NOT liable** for any damages, bugs, or issues
- Users accept **ALL risk** when using your code

The license explicitly states:
```
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND...
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY...
```

### 📋 Only Requirement

Users must:
1. Include the original copyright notice
2. Include the MIT License text

That's it! Just copy-paste the LICENSE file when they redistribute.

## Why MIT? (Comparison)

| What You Want | MIT ✅ | Apache 2.0 | GPL v3 | Proprietary |
|---------------|--------|------------|--------|-------------|
| Users can use commercially | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Restricted |
| Users can modify | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| Users can keep changes private | ✅ Yes | ✅ Yes | ❌ Must share | N/A |
| Users can use in proprietary software | ✅ Yes | ✅ Yes | ❌ Must open-source | N/A |
| Your liability protection | ✅ Full | ✅ Full | ✅ Full | ❌ You're liable |
| Simplicity | ✅ Very simple | 🟡 Complex | 🟡 Complex | 🟡 Complex |
| Industry adoption | ✅ Highest | 🟢 High | 🟡 Medium | ❌ Limited |

## Real-World Examples

Major projects using MIT License:
- **React** (Facebook) - Frontend library
- **Node.js** - JavaScript runtime
- **Ruby on Rails** - Web framework
- **jQuery** - JavaScript library
- **TensorFlow** (MIT-compatible) - ML framework
- **.NET Core** (Microsoft) - Application framework

## Common Questions

### Q: Can companies use this to make money?
**A: YES!** They can build paid products using your library without paying you or sharing their code.

### Q: If someone finds a bug and loses money, am I liable?
**A: NO!** The MIT License explicitly disclaims all warranties and liability. They use it at their own risk.

### Q: Do I have to provide support?
**A: NO!** You have no obligation to help, fix bugs, or maintain the code.

### Q: Can I change the license later?
**A: Sort of.** You can change the license for **future versions**, but code already released under MIT will remain MIT forever. Past users keep their MIT rights.

### Q: What if I want attribution?
**A: It's included!** Users must keep the copyright notice, which includes your name. But they don't have to actively credit you in documentation or UI.

### Q: Can I add "no military use" or similar restrictions?
**A: NO!** That would make it NOT open-source. MIT is fully permissive - you can't add restrictions. If you need restrictions, you need a different license (not recommended for libraries).

### Q: What if someone patents something using my code?
**A: That's allowed.** MIT doesn't include explicit patent clauses. If patents are a concern, consider Apache 2.0 (but it's more complex).

## How to Update Copyright Year

The LICENSE file shows:
```
Copyright (c) 2025 Giorgio C
```

**Option 1 (Recommended for libraries):** Keep it simple
```
Copyright (c) 2025 Giorgio C
```
Don't update the year. This marks when you first published.

**Option 2 (For long-term projects):** Use a range
```
Copyright (c) 2025-2026 Giorgio C
```
Update when you make significant changes in new years.

**Option 3 (Minimal):** Just use the start year
```
Copyright (c) 2025 Giorgio C
```
This is legally sufficient and common.

## License Enforcement

**Good news:** You don't have to enforce anything!

- Users failing to include the license? → Not your problem
- Someone violating the terms? → Optional to pursue (rarely done)
- The warranty disclaimer protects you automatically

## Next Steps for GitHub

When you push to GitHub:

1. ✅ Include the `LICENSE` file (Done!)
2. ✅ Reference it in `README.md` (Done!)
3. ✅ GitHub will auto-detect "MIT License"
4. ✅ Add license badge to README (Done!)
5. ✅ Users will see "MIT License" in the repository info

## Alternative If You Change Your Mind

If you later decide MIT is too permissive (unlikely for a library):

**More restrictive alternatives:**
- **Apache 2.0** - Like MIT but with explicit patent grants (more complex)
- **LGPL** - Users can link to your library in closed-source apps, but modifications to your library must be shared
- **GPL v3** - Strongest copyleft; forces all derivative work to be open-source (NOT recommended for libraries)

**More permissive alternatives:**
- **BSD 0-Clause** / **Unlicense** - Even simpler than MIT (but MIT is already industry standard)

**Note:** Changing retroactively doesn't affect previously released code.

## Summary

✅ **MIT License is PERFECT for your needs:**
- Maximum freedom for users
- Zero responsibility for you
- Zero liability for you
- Industry-standard and trusted
- Simple and clear

🎉 **Your project is now properly licensed for public release!**

---

**Questions?** Check [choosealicense.com](https://choosealicense.com/) for more details about MIT and other licenses.
