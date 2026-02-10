# Node.js Upgrade Guide

## Issue
Your current Node.js version (18.20.8) is too old for the frontend dependencies:
- Vite 7 requires Node.js 20.19+ or 22.12+
- React Router 7 requires Node.js 20+
- @vitejs/plugin-react 5 requires Node.js 20.19+ or 22.12+

## Solution: Upgrade to Node.js 22 (LTS)

### Option 1: Using Homebrew (Recommended)

```bash
# Upgrade to Node.js 22 (current LTS)
brew update
brew upgrade node

# Or install Node 22 specifically
brew install node@22
brew unlink node
brew link node@22

# Verify version
node --version  # Should show v22.x.x
```

### Option 2: Using NVM (Node Version Manager)

If you prefer using NVM for managing multiple Node versions:

```bash
# Install NVM if not installed
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install Node 22
nvm install 22
nvm use 22
nvm alias default 22

# Verify version
node --version  # Should show v22.x.x
```

## After Upgrading Node.js

1. **Reinstall Frontend Dependencies:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

2. **Start Frontend:**
```bash
npm run dev
```

## Alternative: Downgrade Frontend Dependencies (Not Recommended)

If you cannot upgrade Node.js right now, you can temporarily downgrade the frontend dependencies:

```bash
cd frontend
npm install vite@6.0.5 @vitejs/plugin-react@4.3.4 react-router-dom@6.28.0 --save-exact
npm install
```

However, this is not recommended as you'll miss out on:
- Latest features and improvements
- Security updates
- Better performance

## Recommended Versions

- **Node.js:** 22.x (LTS) or 20.x
- **npm:** 10.x (comes with Node)

## Verify Everything Works

After upgrading Node.js:

```bash
# Check versions
node --version    # Should be 20+ or 22+
npm --version     # Should be 10+

# Test frontend
cd frontend
npm run dev       # Should start without errors

# Test backend (Python, no changes needed)
cd ../backend
uvicorn main:app --reload
```

## Current Status

- ✅ Backend: Ready (Python-based, no Node.js dependency)
- ⚠️ Frontend: Needs Node.js 20+ to run
- ✅ Database: Ready and migrated

Once you upgrade Node.js, everything will work smoothly! 🚀
