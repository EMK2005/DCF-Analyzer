# DCF Analyzer

An AI-powered Discounted Cash Flow analyzer. Upload any company's 10-K annual filing and get an interactive DCF model in minutes.

## Features
- 📄 Upload any 10-K PDF — AI extracts all key financials automatically
- 🔍 Review and edit every line item before modeling
- 📈 5-year FCF projection with interactive assumption sliders
- 💰 Dual terminal value: Gordon Growth Model + Exit EV/EBITDA Multiple side by side
- 📊 WACC: auto-calculated from filing data + manual override slider
- 🗺️ Sensitivity heatmaps: WACC × TGR and Revenue Growth × EBITDA Margin
- 📋 Full projection table with implied price vs. market

## Setup

### 1. Clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/dcf-analyzer.git
cd dcf-analyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run locally
```bash
streamlit run app.py
```

Enter your Anthropic API key in the app's Home page when prompted.

---

## Deploy to Streamlit Community Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo, set `app.py` as the main file
5. Click **Deploy**

Your app will be live at `https://your-app-name.streamlit.app`

---

## How it works

```
You upload 10-K PDF
      ↓
Claude API reads the PDF and extracts:
  - Income Statement (Revenue, EBITDA, EBIT, Net Income, D&A)
  - Cash Flow Statement (OCF, Capex, FCF)
  - Balance Sheet (Cash, Debt, Shares)
  - WACC inputs (Beta, Cost of Debt, Capital Structure)
      ↓
You review and edit every figure
      ↓
Interactive DCF dashboard:
  - Sliders: growth rate, EBITDA margin, WACC, terminal growth, exit multiple
  - Charts: revenue/EBITDA projections, FCF waterfall, valuation bridge
  - Sensitivity heatmaps
  - Implied price vs. current market price
```

## Cost

Each 10-K extraction costs approximately **$0.10–0.30** in Claude API credits, depending on the filing length. Get your API key at [console.anthropic.com](https://console.anthropic.com).

## Disclaimer

This tool is for educational and research purposes only. DCF outputs are highly sensitive to assumptions. This is not investment advice.
