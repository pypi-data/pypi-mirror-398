#!/bin/bash
# =============================================================
# TIBET MCP Server - Publish Script
# Claude & Jasper saying Hello to the World!
# =============================================================

echo "🏔️ TIBET MCP Server - Publishing to the World!"
echo "================================================"
echo ""

cd /srv/jtel-stack/mcp-servers/tibet

# Step 1: Check GitHub auth
echo "📦 Step 1: Checking GitHub auth..."
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub niet ingelogd!"
    echo ""
    echo "Run eerst: gh auth login"
    echo ""
    exit 1
fi
echo "✅ GitHub auth OK!"
echo ""

# Step 2: Create GitHub repo
echo "📦 Step 2: Creating GitHub repo..."
gh repo create humotica/mcp-tibet --public \
    --description "TIBET MCP Server - Trust & provenance for AI systems. By Claude & Jasper from HumoticaOS 💙" \
    --source=. --push

if [ $? -eq 0 ]; then
    echo "✅ GitHub repo created!"
else
    echo "⚠️ GitHub repo might already exist, trying to push..."
    git remote add github https://github.com/humotica/mcp-tibet.git 2>/dev/null
    git push -u github main
fi
echo ""

# Step 3: PyPI (using venv)
echo "📦 Step 3: Publishing to PyPI..."
/srv/jtel-stack/venv/bin/pip install build twine -q

echo "   Building package..."
/srv/jtel-stack/venv/bin/python -m build

if [ -d "dist" ]; then
    echo "   Uploading to PyPI..."
    /srv/jtel-stack/venv/bin/twine upload dist/*
    echo "✅ Published to PyPI!"
else
    echo "⚠️ Build failed - PyPI skipped for now"
fi
echo ""

# Done!
echo "================================================"
echo "🎉 TIBET MCP Server publish complete!"
echo ""
echo "   GitHub: https://github.com/humotica/mcp-tibet"
echo ""
echo "   One love, one fAmIly 💙"
echo "================================================"
