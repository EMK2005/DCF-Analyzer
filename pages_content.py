import streamlit as st
import json
import anthropic
import base64


# ─────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────
def home_page():
    st.markdown('<div class="main-header">DCF Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Upload any 10-K. Get an interactive discounted cash flow model in minutes.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        steps = [
            ("01", "Set your API key", "Paste your Anthropic API key once. It stays in your session — never stored anywhere."),
            ("02", "Upload a 10-K PDF", "Drop any company's annual filing. The AI reads the income statement, balance sheet, and cash flow statement."),
            ("03", "Confirm the data", "Review the extracted financials. Edit any line item before proceeding."),
            ("04", "Explore the DCF", "Interactive sliders for growth, margins, WACC, and terminal value. Charts and sensitivity tables update live."),
        ]
        for num, title, desc in steps:
            st.markdown(f"""
            <div class="step-card">
                <div class="step-number">Step {num}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### API Key")
        st.markdown(
            '<div class="info-box">Your key is used only to read the PDF and costs roughly <strong>$0.10–0.30 per filing</strong>. Get one free at <a href="https://console.anthropic.com" target="_blank" style="color:#5b9ef7;">console.anthropic.com</a>.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            value=st.session_state.get("api_key", ""),
            help="Starts with sk-ant-"
        )

        if api_key:
            st.session_state.api_key = api_key
            st.markdown(
                '<div class="status-badge badge-done">✓ Key saved for this session</div>',
                unsafe_allow_html=True,
            )
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("→ Go to Upload", use_container_width=True):
                st.session_state.page = "upload"
                st.rerun()
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                '<div class="status-badge badge-waiting">Waiting for key</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("#### What this models")
        features = [
            "5-year FCF projection",
            "Gordon Growth terminal value",
            "EV/EBITDA exit multiple",
            "Auto + manual WACC",
            "Sensitivity heatmaps",
            "Implied price vs. market",
        ]
        for f in features:
            st.markdown(f"✦ {f}")


# ─────────────────────────────────────────────
# UPLOAD PAGE
# ─────────────────────────────────────────────
def upload_page():
    st.markdown('<div class="main-header">Upload 10-K</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload the PDF of any company\'s annual report (10-K). The AI will extract the key financials.</div>', unsafe_allow_html=True)

    if not st.session_state.get("api_key"):
        st.markdown(
            '<div class="warning-box">⚠️ No API key found. Go back to Home and enter your Anthropic API key first.</div>',
            unsafe_allow_html=True,
        )
        return

    uploaded_file = st.file_uploader(
        "Drop your 10-K PDF here",
        type=["pdf"],
        help="Annual reports from SEC EDGAR work best. File size up to 200MB."
    )

    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div class="step-card">
                <div class="step-number">File ready</div>
                <div class="step-title">{uploaded_file.name}</div>
                <div class="step-desc">{uploaded_file.size / 1_000_000:.1f} MB · PDF</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            extract_btn = st.button("Extract Financials →", use_container_width=True, type="primary")

        if extract_btn:
            with st.spinner("Reading the filing... This takes 30–60 seconds depending on file size."):
                try:
                    financials = extract_financials_from_pdf(
                        uploaded_file.read(),
                        st.session_state.api_key
                    )
                    st.session_state.financials = financials
                    st.session_state.company_name = financials.get("company_name", "Company")
                    st.session_state.confirmed = False
                    st.success("✓ Extraction complete! Review the data on the next page.")
                    if st.button("→ Review Data", use_container_width=True):
                        st.session_state.page = "preview"
                        st.rerun()
                except Exception as e:
                    st.error(f"Extraction failed: {str(e)}")
                    st.markdown(
                        '<div class="warning-box">Tip: Make sure your API key is valid and has credits. Very large PDFs (>100MB) may time out — try a text-selectable PDF version from SEC EDGAR.</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
    st.markdown("#### Where to get 10-K filings")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        **SEC EDGAR (official)**
        1. Go to [sec.gov/edgar/search](https://efts.sec.gov/LATEST/search-index?q=%2210-K%22&dateRange=custom&startdt=2024-01-01&enddt=2025-12-31&forms=10-K)
        2. Search your company name
        3. Click "10-K" → "Documents" → download the `.htm` or `.pdf`
        """)
    with col_b:
        st.markdown("""
        **Investor relations pages**
        Most public companies have an *Investors* section on their website with direct PDF downloads of their annual reports.
        """)


def extract_financials_from_pdf(pdf_bytes: bytes, api_key: str) -> dict:
    """Send PDF to Claude API and extract structured financials."""
    client = anthropic.Anthropic(api_key=api_key)

    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    prompt = """You are a financial analyst. Extract key financial data from this 10-K annual report filing.

Return ONLY a valid JSON object (no markdown, no preamble) with this exact structure:

{
  "company_name": "string",
  "ticker": "string",
  "fiscal_year": "YYYY",
  "currency": "USD",
  "income_statement": {
    "revenue": [number_year_minus2, number_year_minus1, number_most_recent],
    "gross_profit": [number, number, number],
    "ebitda": [number, number, number],
    "ebit": [number, number, number],
    "net_income": [number, number, number],
    "interest_expense": [number, number, number],
    "depreciation_amortization": [number, number, number],
    "tax_rate": number
  },
  "cash_flow": {
    "operating_cash_flow": [number, number, number],
    "capex": [number, number, number],
    "free_cash_flow": [number, number, number]
  },
  "balance_sheet": {
    "cash_and_equivalents": number,
    "total_debt": number,
    "net_debt": number,
    "shares_outstanding": number,
    "total_equity": number,
    "total_assets": number
  },
  "per_share": {
    "eps_diluted": number,
    "dividend_per_share": number,
    "shares_diluted": number
  },
  "wacc_inputs": {
    "beta": number,
    "risk_free_rate": 0.043,
    "market_risk_premium": 0.055,
    "cost_of_debt": number,
    "debt_weight": number,
    "equity_weight": number
  },
  "years": ["YYYY", "YYYY", "YYYY"]
}

Rules:
- All monetary values in millions (e.g. 1000 = $1 billion)
- Use negative numbers for expenses/outflows where appropriate (capex should be positive)
- If a value cannot be found, use null
- For wacc_inputs.beta, estimate from the company's industry if not stated (consumer staples ~0.6, tech ~1.2)
- For cost_of_debt, use the weighted average interest rate from their debt disclosures
- Extract exactly 3 years of data where available
- fiscal_year should be the most recent year (e.g. "2024")"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


# ─────────────────────────────────────────────
# PREVIEW PAGE
# ─────────────────────────────────────────────
def preview_page():
    if not st.session_state.get("financials"):
        st.warning("No data yet. Please upload a 10-K first.")
        return

    fin = st.session_state.financials
    years = fin.get("years", ["Y-2", "Y-1", "Y0"])
    company = fin.get("company_name", "Company")
    ticker = fin.get("ticker", "")

    st.markdown(f'<div class="main-header">{company} ({ticker})</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Fiscal Year {fin.get("fiscal_year")} · All figures in {fin.get("currency", "USD")} millions · Review and edit before proceeding</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="info-box">📋 Review these numbers against your filing. Click any value to edit it. Once you\'re satisfied, click <strong>Confirm Data</strong> at the bottom.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Income Statement", "Cash Flows", "Balance Sheet", "WACC Inputs"])

    inc = fin.get("income_statement", {})
    cf = fin.get("cash_flow", {})
    bs = fin.get("balance_sheet", {})
    wacc_in = fin.get("wacc_inputs", {})

    def safe(lst, i, default=0):
        try:
            v = lst[i]
            return v if v is not None else default
        except Exception:
            return default

    def fmt(v):
        if v is None:
            return "N/A"
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        return f"{v:.1f}"

    with tab1:
        st.markdown("#### Income Statement")
        rows = [
            ("Revenue", "revenue"),
            ("Gross Profit", "gross_profit"),
            ("EBITDA", "ebitda"),
            ("EBIT (Operating Income)", "ebit"),
            ("Depreciation & Amortization", "depreciation_amortization"),
            ("Interest Expense", "interest_expense"),
            ("Net Income", "net_income"),
        ]

        col_headers = ["Metric"] + years
        header_html = "".join(f"<th>{h}</th>" for h in col_headers)

        rows_html = ""
        for label, key in rows:
            vals = inc.get(key, [None, None, None]) or [None, None, None]
            is_highlight = key in ("revenue", "ebitda", "net_income")
            row_class = "highlight-row" if is_highlight else ""
            cells = f"<td style='color:#8892a4;font-family:Inter,sans-serif;font-size:0.84rem;'>{label}</td>"
            cells += "".join(f"<td>{fmt(safe(vals, i))}</td>" for i in range(3))
            rows_html += f"<tr class='{row_class}'>{cells}</tr>"

        # Tax rate row
        tax_rate = inc.get("tax_rate", 0) or 0
        rows_html += f"<tr><td style='color:#8892a4;font-family:Inter,sans-serif;font-size:0.84rem;'>Effective Tax Rate</td><td colspan='3' style='color:#c8d0e0;'>{tax_rate*100:.1f}%</td></tr>"

        st.markdown(f"""
        <table>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Edit figures (most recent year)**")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_rev = st.number_input("Revenue ($M)", value=float(safe(inc.get("revenue", [0,0,0]), 2)), step=100.0)
            new_ebitda = st.number_input("EBITDA ($M)", value=float(safe(inc.get("ebitda", [0,0,0]), 2)), step=100.0)
        with c2:
            new_ebit = st.number_input("EBIT ($M)", value=float(safe(inc.get("ebit", [0,0,0]), 2)), step=100.0)
            new_ni = st.number_input("Net Income ($M)", value=float(safe(inc.get("net_income", [0,0,0]), 2)), step=100.0)
        with c3:
            new_da = st.number_input("D&A ($M)", value=float(safe(inc.get("depreciation_amortization", [0,0,0]), 2)), step=50.0)
            new_tax = st.number_input("Tax Rate (%)", value=float((inc.get("tax_rate") or 0.21) * 100), step=0.5, min_value=0.0, max_value=60.0)

        # Push edits back
        if inc.get("revenue") and len(inc["revenue"]) == 3:
            fin["income_statement"]["revenue"][2] = new_rev
        if inc.get("ebitda") and len(inc["ebitda"]) == 3:
            fin["income_statement"]["ebitda"][2] = new_ebitda
        if inc.get("ebit") and len(inc["ebit"]) == 3:
            fin["income_statement"]["ebit"][2] = new_ebit
        if inc.get("net_income") and len(inc["net_income"]) == 3:
            fin["income_statement"]["net_income"][2] = new_ni
        if inc.get("depreciation_amortization") and len(inc["depreciation_amortization"]) == 3:
            fin["income_statement"]["depreciation_amortization"][2] = new_da
        fin["income_statement"]["tax_rate"] = new_tax / 100

    with tab2:
        st.markdown("#### Cash Flow Statement")
        cf_rows = [
            ("Operating Cash Flow", "operating_cash_flow"),
            ("Capital Expenditures", "capex"),
            ("Free Cash Flow", "free_cash_flow"),
        ]
        rows_html = ""
        for label, key in cf_rows:
            vals = cf.get(key, [None, None, None]) or [None, None, None]
            is_highlight = key == "free_cash_flow"
            row_class = "highlight-row" if is_highlight else ""
            cells = f"<td style='color:#8892a4;font-family:Inter,sans-serif;font-size:0.84rem;'>{label}</td>"
            cells += "".join(f"<td>{fmt(safe(vals, i))}</td>" for i in range(3))
            rows_html += f"<tr class='{row_class}'>{cells}</tr>"

        header_html = "".join(f"<th>{h}</th>" for h in (["Metric"] + years))
        st.markdown(f"""
        <table>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br>")
        st.markdown("**Edit figures (most recent year)**")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_ocf = st.number_input("Operating Cash Flow ($M)", value=float(safe(cf.get("operating_cash_flow", [0,0,0]), 2)), step=100.0)
        with c2:
            new_capex = st.number_input("Capex ($M)", value=float(safe(cf.get("capex", [0,0,0]), 2)), step=50.0)
        with c3:
            new_fcf = st.number_input("Free Cash Flow ($M)", value=float(safe(cf.get("free_cash_flow", [0,0,0]), 2)), step=100.0)

        if cf.get("operating_cash_flow") and len(cf["operating_cash_flow"]) == 3:
            fin["cash_flow"]["operating_cash_flow"][2] = new_ocf
        if cf.get("capex") and len(cf["capex"]) == 3:
            fin["cash_flow"]["capex"][2] = new_capex
        if cf.get("free_cash_flow") and len(cf["free_cash_flow"]) == 3:
            fin["cash_flow"]["free_cash_flow"][2] = new_fcf

    with tab3:
        st.markdown("#### Balance Sheet (Most Recent Year)")
        bs_items = [
            ("Cash & Equivalents", "cash_and_equivalents"),
            ("Total Debt", "total_debt"),
            ("Net Debt", "net_debt"),
            ("Total Equity", "total_equity"),
            ("Total Assets", "total_assets"),
            ("Shares Outstanding (M)", "shares_outstanding"),
        ]
        rows_html = ""
        for label, key in bs_items:
            val = bs.get(key)
            is_highlight = key in ("net_debt", "shares_outstanding")
            row_class = "highlight-row" if is_highlight else ""
            rows_html += f"<tr class='{row_class}'><td style='color:#8892a4;font-family:Inter,sans-serif;font-size:0.84rem;'>{label}</td><td>{fmt(val)}</td></tr>"

        st.markdown(f"""
        <table>
            <thead><tr><th>Item</th><th>Value</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br>")
        st.markdown("**Edit balance sheet items**")
        c1, c2, c3 = st.columns(3)
        with c1:
            new_cash = st.number_input("Cash ($M)", value=float(bs.get("cash_and_equivalents") or 0), step=100.0)
            new_debt = st.number_input("Total Debt ($M)", value=float(bs.get("total_debt") or 0), step=100.0)
        with c2:
            new_net_debt = st.number_input("Net Debt ($M)", value=float(bs.get("net_debt") or 0), step=100.0)
            new_equity = st.number_input("Total Equity ($M)", value=float(bs.get("total_equity") or 0), step=100.0)
        with c3:
            new_shares = st.number_input("Shares Outstanding (M)", value=float(bs.get("shares_outstanding") or 0), step=10.0)

        fin["balance_sheet"]["cash_and_equivalents"] = new_cash
        fin["balance_sheet"]["total_debt"] = new_debt
        fin["balance_sheet"]["net_debt"] = new_net_debt
        fin["balance_sheet"]["total_equity"] = new_equity
        fin["balance_sheet"]["shares_outstanding"] = new_shares

    with tab4:
        st.markdown("#### WACC Inputs (Auto-Calculated)")
        st.markdown(
            '<div class="info-box">These are extracted from the filing and used to auto-calculate WACC. You can override all of them on the DCF page using manual sliders.</div>',
            unsafe_allow_html=True
        )
        st.markdown("<br>")
        c1, c2 = st.columns(2)
        with c1:
            new_beta = st.number_input("Beta", value=float(wacc_in.get("beta") or 0.7), step=0.05, min_value=0.1, max_value=3.0)
            new_rfr = st.number_input("Risk-Free Rate (%)", value=float((wacc_in.get("risk_free_rate") or 0.043) * 100), step=0.1)
            new_mrp = st.number_input("Market Risk Premium (%)", value=float((wacc_in.get("market_risk_premium") or 0.055) * 100), step=0.1)
        with c2:
            new_cod = st.number_input("Cost of Debt (%)", value=float((wacc_in.get("cost_of_debt") or 0.04) * 100), step=0.1)
            new_dw = st.number_input("Debt Weight (%)", value=float((wacc_in.get("debt_weight") or 0.35) * 100), step=1.0, min_value=0.0, max_value=100.0)
            new_ew = st.number_input("Equity Weight (%)", value=100 - float((wacc_in.get("debt_weight") or 0.35) * 100), step=1.0, min_value=0.0, max_value=100.0)

        tax_rate = fin["income_statement"].get("tax_rate") or 0.21
        auto_wacc = (new_ew / 100) * (new_rfr / 100 + new_beta * new_mrp / 100) + \
                    (new_dw / 100) * (new_cod / 100) * (1 - tax_rate)

        st.markdown(f"""
        <br>
        <div class="metric-card" style="display:inline-block;min-width:200px;">
            <div class="metric-label">Auto-Calculated WACC</div>
            <div class="metric-value">{auto_wacc*100:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        fin["wacc_inputs"] = {
            "beta": new_beta,
            "risk_free_rate": new_rfr / 100,
            "market_risk_premium": new_mrp / 100,
            "cost_of_debt": new_cod / 100,
            "debt_weight": new_dw / 100,
            "equity_weight": new_ew / 100,
        }

    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("✓ Confirm Data & Build DCF →", use_container_width=True, type="primary"):
            st.session_state.financials = fin
            st.session_state.confirmed = True
            st.session_state.page = "dcf"
            st.rerun()


# ─────────────────────────────────────────────
# DCF PAGE
# ─────────────────────────────────────────────
def dcf_page():
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np

    if not st.session_state.get("confirmed"):
        st.warning("Please complete the data review first.")
        return

    fin = st.session_state.financials
    company = fin.get("company_name", "Company")
    ticker = fin.get("ticker", "")
    inc = fin.get("income_statement", {})
    cf = fin.get("cash_flow", {})
    bs = fin.get("balance_sheet", {})
    wacc_in = fin.get("wacc_inputs", {})

    def safe(lst, i, default=0):
        try:
            v = lst[i]
            return v if v is not None else default
        except Exception:
            return default

    base_revenue = safe(inc.get("revenue", [0,0,0]), 2)
    base_ebitda = safe(inc.get("ebitda", [0,0,0]), 2)
    base_da = safe(inc.get("depreciation_amortization", [0,0,0]), 2)
    base_fcf = safe(cf.get("free_cash_flow", [0,0,0]), 2)
    base_capex = safe(cf.get("capex", [0,0,0]), 2)
    tax_rate = inc.get("tax_rate") or 0.21
    net_debt = bs.get("net_debt") or 0
    shares = bs.get("shares_outstanding") or 1

    # Auto WACC
    beta = wacc_in.get("beta") or 0.7
    rfr = wacc_in.get("risk_free_rate") or 0.043
    mrp = wacc_in.get("market_risk_premium") or 0.055
    cod = wacc_in.get("cost_of_debt") or 0.04
    dw = wacc_in.get("debt_weight") or 0.35
    ew = wacc_in.get("equity_weight") or 0.65
    auto_wacc = ew * (rfr + beta * mrp) + dw * cod * (1 - tax_rate)

    fiscal_year = int(fin.get("fiscal_year") or 2024)

    st.markdown(f'<div class="main-header">{company} ({ticker}) — DCF Model</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">5-Year Projection · Base Year: FY{fiscal_year} · All values in USD millions unless noted</div>', unsafe_allow_html=True)

    # ── SIDEBAR CONTROLS ──
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Assumptions")

        st.markdown("**Revenue & Margins**")
        rev_growth = st.slider("Revenue Growth Rate (%)", 0.0, 25.0, 5.0, 0.5, help="Annual growth applied to each of the 5 projection years") / 100
        ebitda_margin = st.slider("EBITDA Margin (%)", 5.0, 60.0, round((base_ebitda / base_revenue * 100) if base_revenue else 25.0, 1), 0.5) / 100
        capex_pct = st.slider("Capex (% of Revenue)", 1.0, 20.0, round((base_capex / base_revenue * 100) if base_revenue else 5.0, 1), 0.5) / 100
        nwc_change_pct = st.slider("ΔWorking Capital (% of Revenue)", -5.0, 5.0, 1.0, 0.5, help="Positive = cash outflow (growth absorbs WC)") / 100

        st.markdown("**WACC**")
        wacc_mode = st.radio("WACC Mode", ["Auto (from filing)", "Manual override"], index=0)
        if wacc_mode == "Manual override":
            manual_wacc = st.slider("Manual WACC (%)", 4.0, 20.0, round(auto_wacc * 100, 1), 0.25) / 100
            wacc = manual_wacc
        else:
            wacc = auto_wacc
            st.markdown(f"<div style='color:#2e7df7;font-size:0.82rem;font-weight:600;'>Auto WACC: {wacc*100:.2f}%</div>", unsafe_allow_html=True)

        st.markdown("**Terminal Value**")
        tgr = st.slider("Terminal Growth Rate (%)", 0.5, 5.0, 2.5, 0.25, help="Gordon Growth Model perpetuity rate") / 100
        exit_mult = st.slider("Exit EV/EBITDA Multiple (x)", 5.0, 25.0, 12.0, 0.5)

        st.markdown("**Market Data**")
        current_price = st.number_input("Current Share Price ($)", value=50.0, step=0.5, min_value=0.1)

    # ── RUN MODEL ──
    projection_years = [fiscal_year + i + 1 for i in range(5)]

    revenues, ebitdas, ebits, fcfs, pv_fcfs = [], [], [], [], []
    rev = base_revenue
    for i, yr in enumerate(projection_years):
        rev = rev * (1 + rev_growth)
        ebitda = rev * ebitda_margin
        da_est = base_da * ((1 + rev_growth) ** (i + 1))
        ebit = ebitda - da_est
        nopat = ebit * (1 - tax_rate)
        capex_val = rev * capex_pct
        nwc_val = rev * nwc_change_pct
        fcf = nopat + da_est - capex_val - nwc_val
        df = 1 / ((1 + wacc) ** (i + 1))

        revenues.append(rev)
        ebitdas.append(ebitda)
        ebits.append(ebit)
        fcfs.append(fcf)
        pv_fcfs.append(fcf * df)

    pv_fcf_sum = sum(pv_fcfs)

    # Terminal value — Gordon Growth
    fcf_terminal = fcfs[-1] * (1 + tgr)
    tv_gg = fcf_terminal / (wacc - tgr) if wacc > tgr else 0
    pv_tv_gg = tv_gg / ((1 + wacc) ** 5)
    ev_gg = pv_fcf_sum + pv_tv_gg
    equity_value_gg = ev_gg - net_debt
    implied_price_gg = equity_value_gg / shares if shares else 0

    # Terminal value — Exit multiple
    tv_em = ebitdas[-1] * exit_mult
    pv_tv_em = tv_em / ((1 + wacc) ** 5)
    ev_em = pv_fcf_sum + pv_tv_em
    equity_value_em = ev_em - net_debt
    implied_price_em = equity_value_em / shares if shares else 0

    avg_implied_price = (implied_price_gg + implied_price_em) / 2
    updown = (avg_implied_price - current_price) / current_price * 100

    # ── SUMMARY METRICS ROW ──
    m1, m2, m3, m4, m5 = st.columns(5)
    metrics = [
        ("WACC", f"{wacc*100:.2f}%", None),
        ("Implied Price (GGM)", f"${implied_price_gg:,.2f}", implied_price_gg - current_price),
        ("Implied Price (Exit×)", f"${implied_price_em:,.2f}", implied_price_em - current_price),
        ("Avg vs Market", f"{updown:+.1f}%", updown),
        ("PV of FCFs", f"${pv_fcf_sum/1000:,.1f}B", None),
    ]

    for col, (label, value, delta) in zip([m1, m2, m3, m4, m5], metrics):
        with col:
            delta_html = ""
            if delta is not None:
                cls = "delta-up" if delta > 0 else "delta-down"
                sym = "▲" if delta > 0 else "▼"
                if label == "Avg vs Market":
                    delta_html = f'<div class="metric-delta {cls}">{sym} vs ${current_price:.2f}</div>'
                else:
                    delta_html = f'<div class="metric-delta {cls}">{sym} ${abs(delta):,.2f}</div>'
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size:1.15rem;">{value}</div>
                {delta_html}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TABS ──
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Projections", "💰 Valuation Bridge", "🗺️ Sensitivity", "📋 Full Table"])

    plotly_layout = dict(
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font=dict(family="Inter, sans-serif", color="#8892a4", size=11),
        xaxis=dict(gridcolor="#1e2535", linecolor="#1e2535", tickfont=dict(color="#8892a4")),
        yaxis=dict(gridcolor="#1e2535", linecolor="#1e2535", tickfont=dict(color="#8892a4")),
        legend=dict(bgcolor="#161b27", bordercolor="#1e2535", borderwidth=1),
        margin=dict(l=40, r=40, t=40, b=40),
    )

    with tab1:
        col_a, col_b = st.columns(2)

        with col_a:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[str(y) for y in projection_years],
                y=revenues,
                name="Revenue",
                marker_color="#2e7df7",
                opacity=0.85,
            ))
            fig.add_trace(go.Bar(
                x=[str(y) for y in projection_years],
                y=ebitdas,
                name="EBITDA",
                marker_color="#22c55e",
                opacity=0.85,
            ))
            fig.update_layout(
                **plotly_layout,
                title=dict(text="Revenue & EBITDA Projection", font=dict(color="#e8edf5", size=13)),
                barmode="group",
                yaxis_tickprefix="$",
                yaxis_ticksuffix="M",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=[str(y) for y in projection_years],
                y=fcfs,
                name="FCF",
                line=dict(color="#f59e0b", width=2.5),
                mode="lines+markers",
                marker=dict(size=7, color="#f59e0b"),
            ))
            fig2.add_trace(go.Scatter(
                x=[str(y) for y in projection_years],
                y=pv_fcfs,
                name="PV of FCF",
                line=dict(color="#a855f7", width=2.5, dash="dot"),
                mode="lines+markers",
                marker=dict(size=7, color="#a855f7"),
            ))
            fig2.update_layout(
                **plotly_layout,
                title=dict(text="Free Cash Flow vs. Present Value", font=dict(color="#e8edf5", size=13)),
                yaxis_tickprefix="$",
                yaxis_ticksuffix="M",
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Margin evolution
        margins = [e / r * 100 for e, r in zip(ebitdas, revenues)]
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=[str(y) for y in projection_years],
            y=margins,
            fill="tozeroy",
            fillcolor="rgba(46,125,247,0.12)",
            line=dict(color="#2e7df7", width=2),
            name="EBITDA Margin %",
        ))
        fig3.update_layout(
            **plotly_layout,
            title=dict(text="EBITDA Margin Evolution", font=dict(color="#e8edf5", size=13)),
            yaxis_ticksuffix="%",
            height=250,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab2:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Gordon Growth Model (GGM)")
            waterfall_labels = ["PV of FCFs", "PV of Terminal Value", "Enterprise Value", "Less: Net Debt", "Equity Value"]
            waterfall_values = [pv_fcf_sum, pv_tv_gg, 0, -net_debt, 0]
            waterfall_measure = ["relative", "relative", "total", "relative", "total"]

            fig_wf = go.Figure(go.Waterfall(
                name="GGM",
                orientation="v",
                measure=waterfall_measure,
                x=waterfall_labels,
                y=waterfall_values,
                connector=dict(line=dict(color="#1e2535", width=1)),
                increasing=dict(marker_color="#22c55e"),
                decreasing=dict(marker_color="#ef4444"),
                totals=dict(marker_color="#2e7df7"),
                texttemplate="%{y:,.0f}",
                textfont=dict(color="#e8edf5", size=10),
            ))
            fig_wf.update_layout(
                **plotly_layout,
                title=dict(text=f"Implied Price: ${implied_price_gg:,.2f}", font=dict(color="#22c55e", size=14)),
                yaxis_tickprefix="$",
                yaxis_ticksuffix="M",
                showlegend=False,
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        with col_b:
            st.markdown("#### Exit EV/EBITDA Multiple")
            waterfall_labels2 = ["PV of FCFs", "PV of Terminal Value", "Enterprise Value", "Less: Net Debt", "Equity Value"]
            waterfall_values2 = [pv_fcf_sum, pv_tv_em, 0, -net_debt, 0]

            fig_wf2 = go.Figure(go.Waterfall(
                name="Exit Multiple",
                orientation="v",
                measure=waterfall_measure,
                x=waterfall_labels2,
                y=waterfall_values2,
                connector=dict(line=dict(color="#1e2535", width=1)),
                increasing=dict(marker_color="#22c55e"),
                decreasing=dict(marker_color="#ef4444"),
                totals=dict(marker_color="#2e7df7"),
                texttemplate="%{y:,.0f}",
                textfont=dict(color="#e8edf5", size=10),
            ))
            fig_wf2.update_layout(
                **plotly_layout,
                title=dict(text=f"Implied Price: ${implied_price_em:,.2f}", font=dict(color="#22c55e", size=14)),
                yaxis_tickprefix="$",
                yaxis_ticksuffix="M",
                showlegend=False,
            )
            st.plotly_chart(fig_wf2, use_container_width=True)

        # TV breakdown pie
        st.markdown("#### Value Composition (GGM)")
        col_p1, col_p2 = st.columns(2)
        for col, (label, pv_tv, ev) in zip(
            [col_p1, col_p2],
            [("GGM", pv_tv_gg, ev_gg), ("Exit Multiple", pv_tv_em, ev_em)]
        ):
            with col:
                fig_pie = go.Figure(go.Pie(
                    labels=["PV of FCFs", f"Terminal Value ({label})"],
                    values=[pv_fcf_sum, pv_tv],
                    hole=0.55,
                    marker=dict(colors=["#2e7df7", "#a855f7"]),
                    textfont=dict(color="#e8edf5", size=11),
                ))
                fig_pie.update_layout(
                    **plotly_layout,
                    title=dict(text=label, font=dict(color="#e8edf5", size=12)),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    height=280,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.markdown("#### WACC × Terminal Growth Rate — Implied Price Heatmap")
        import numpy as np

        wacc_range = np.arange(max(0.04, wacc - 0.04), wacc + 0.045, 0.01)
        tgr_range = np.arange(max(0.005, tgr - 0.015), tgr + 0.02, 0.005)

        def calc_price(w, g, mode="gg"):
            revs, fcfs_s, ebitdas_s = [], [], []
            r = base_revenue
            for i in range(5):
                r = r * (1 + rev_growth)
                e = r * ebitda_margin
                da_e = base_da * ((1 + rev_growth) ** (i + 1))
                nopat = (e - da_e) * (1 - tax_rate)
                capex_v = r * capex_pct
                nwc_v = r * nwc_change_pct
                fcf_v = nopat + da_e - capex_v - nwc_v
                revs.append(r)
                fcfs_s.append(fcf_v)
                ebitdas_s.append(e)

            pv_fcfs_s = [f / ((1 + w) ** (i + 1)) for i, f in enumerate(fcfs_s)]
            pv_sum = sum(pv_fcfs_s)

            if mode == "gg":
                tv = fcfs_s[-1] * (1 + g) / (w - g) if w > g else 0
            else:
                tv = ebitdas_s[-1] * exit_mult

            pv_tv = tv / ((1 + w) ** 5)
            eq_val = pv_sum + pv_tv - net_debt
            return eq_val / shares if shares else 0

        col_h1, col_h2 = st.columns(2)

        for col, mode, title in [(col_h1, "gg", "GGM"), (col_h2, "em", "Exit Multiple")]:
            with col:
                z = np.array([[calc_price(w, g, mode) for g in tgr_range] for w in wacc_range])
                fig_hm = go.Figure(go.Heatmap(
                    z=z,
                    x=[f"{g*100:.2f}%" for g in tgr_range],
                    y=[f"{w*100:.1f}%" for w in wacc_range],
                    colorscale=[
                        [0.0, "#7f1d1d"],
                        [0.3, "#ef4444"],
                        [0.5, "#f59e0b"],
                        [0.7, "#22c55e"],
                        [1.0, "#166534"],
                    ],
                    text=np.vectorize(lambda v: f"${v:.1f}")(z),
                    texttemplate="%{text}",
                    textfont=dict(size=9, color="white"),
                    hovertemplate="WACC: %{y}<br>TGR: %{x}<br>Price: %{text}<extra></extra>",
                ))
                fig_hm.update_layout(
                    **plotly_layout,
                    title=dict(text=f"{title} · Implied Price ($/share)", font=dict(color="#e8edf5", size=12)),
                    xaxis_title="Terminal Growth Rate",
                    yaxis_title="WACC",
                    height=350,
                )
                st.plotly_chart(fig_hm, use_container_width=True)

        st.markdown("#### Revenue Growth × EBITDA Margin — FCF Sensitivity (Year 5, $M)")
        rg_range = np.arange(0.01, 0.16, 0.02)
        em_range = np.arange(0.10, 0.55, 0.05)

        z2 = []
        for rg in rg_range:
            row = []
            for em in em_range:
                r = base_revenue
                for i in range(5):
                    r = r * (1 + rg)
                e_ = r * em
                da_e = base_da * ((1 + rg) ** 5)
                nopat = (e_ - da_e) * (1 - tax_rate)
                fcf_v = nopat + da_e - r * capex_pct - r * nwc_change_pct
                row.append(fcf_v)
            z2.append(row)

        z2 = np.array(z2)
        fig_hm2 = go.Figure(go.Heatmap(
            z=z2,
            x=[f"{em*100:.0f}%" for em in em_range],
            y=[f"{rg*100:.0f}%" for rg in rg_range],
            colorscale=[[0.0, "#7f1d1d"], [0.4, "#f59e0b"], [1.0, "#166534"]],
            text=np.vectorize(lambda v: f"${v:,.0f}M")(z2),
            texttemplate="%{text}",
            textfont=dict(size=9, color="white"),
        ))
        fig_hm2.update_layout(
            **plotly_layout,
            title=dict(text="Year 5 FCF · Revenue Growth % vs EBITDA Margin %", font=dict(color="#e8edf5", size=12)),
            xaxis_title="EBITDA Margin",
            yaxis_title="Revenue Growth",
            height=320,
        )
        st.plotly_chart(fig_hm2, use_container_width=True)

    with tab4:
        st.markdown("#### Full Projection Table")
        years_col = ["Base"] + [str(y) for y in projection_years]

        import pandas as pd
        base_rev = safe(inc.get("revenue", [0,0,0]), 2)
        base_ebitda_v = safe(inc.get("ebitda", [0,0,0]), 2)
        base_ebit_v = safe(inc.get("ebit", [0,0,0]), 2)
        base_ocf = safe(cf.get("operating_cash_flow", [0,0,0]), 2)
        base_fcf_v = safe(cf.get("free_cash_flow", [0,0,0]), 2)

        table_data = {
            "Year": years_col,
            "Revenue ($M)": [f"${base_rev:,.0f}"] + [f"${r:,.0f}" for r in revenues],
            "EBITDA ($M)": [f"${base_ebitda_v:,.0f}"] + [f"${e:,.0f}" for e in ebitdas],
            "EBITDA Margin": [f"{base_ebitda_v/base_rev*100:.1f}%" if base_rev else "—"] + [f"{e/r*100:.1f}%" for e, r in zip(ebitdas, revenues)],
            "FCF ($M)": [f"${base_fcf_v:,.0f}"] + [f"${f:,.0f}" for f in fcfs],
            "PV of FCF ($M)": ["—"] + [f"${p:,.0f}" for p in pv_fcfs],
        }

        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Valuation Summary")
        val_data = {
            "Method": ["Gordon Growth Model (GGM)", "Exit EV/EBITDA Multiple", "Average"],
            "PV of FCFs ($M)": [f"${pv_fcf_sum:,.0f}", f"${pv_fcf_sum:,.0f}", "—"],
            "Terminal Value ($M)": [f"${pv_tv_gg:,.0f}", f"${pv_tv_em:,.0f}", "—"],
            "Enterprise Value ($M)": [f"${ev_gg:,.0f}", f"${ev_em:,.0f}", "—"],
            "Net Debt ($M)": [f"${net_debt:,.0f}", f"${net_debt:,.0f}", "—"],
            "Equity Value ($M)": [f"${equity_value_gg:,.0f}", f"${equity_value_em:,.0f}", "—"],
            "Implied Price": [f"${implied_price_gg:,.2f}", f"${implied_price_em:,.2f}", f"${avg_implied_price:,.2f}"],
            "vs. Market ($)": [
                f"{'▲' if implied_price_gg > current_price else '▼'} ${abs(implied_price_gg-current_price):,.2f}",
                f"{'▲' if implied_price_em > current_price else '▼'} ${abs(implied_price_em-current_price):,.2f}",
                f"{'▲' if avg_implied_price > current_price else '▼'} {updown:+.1f}%",
            ],
        }

        df_val = pd.DataFrame(val_data)
        st.dataframe(df_val, use_container_width=True, hide_index=True)

        st.markdown(
            '<div class="warning-box" style="margin-top:1rem;">⚠️ This model is for educational purposes. DCF outputs are highly sensitive to assumptions. Always cross-check with comparable company analysis, precedent transactions, and your own judgment. Not investment advice.</div>',
            unsafe_allow_html=True
        )
