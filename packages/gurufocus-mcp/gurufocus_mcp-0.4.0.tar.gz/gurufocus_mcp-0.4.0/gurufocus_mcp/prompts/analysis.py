"""Investment analysis prompts for GuruFocus MCP."""

from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register investment analysis prompts.

    Args:
        mcp: FastMCP server instance
    """

    @mcp.prompt("qgarp_scorecard")
    def qgarp_scorecard(ticker: str) -> str:
        """Generate a Quality Growth at a Reasonable Price (QGARP) investment scorecard.

        Args:
            ticker: The stock ticker symbol to analyze (e.g. AAPL)
        """
        return f"""You are an investment analyst applying the QGARP (Quality Growth at a Reasonable Price) framework. Using the GuruFocus data provided, generate a comprehensive investment scorecard for {ticker}.

## Instructions

1. Fetch data using these GuruFocus MCP tools:
   - `get_stock_summary` - for company overview, quality scores, valuation
   - `get_stock_keyratios` - for detailed financial ratios and growth rates
   - `get_stock_financials` - for historical financial performance

2. Generate the scorecard below, applying PASS/FAIL/WATCH ratings based on the thresholds specified.

---

# QGARP INVESTMENT SCORECARD: {ticker}

## 1. COMPANY OVERVIEW
| Field | Value |
|-------|-------|
| Company | |
| Sector / Industry | |
| Market Cap | |
| Current Price | |
| 52-Week Range | |

**Business Summary**: [1-2 sentence description]

---

## 2. QGARP SCREENING CRITERIA

| Metric | Value | Threshold | Result |
|--------|-------|-----------|--------|
| ROIC (5yr avg or current) | | >10% | PASS/FAIL |
| Revenue Growth (5yr CAGR) | | >10% | PASS/FAIL |
| EPS Growth (5yr CAGR) | | >10% | PASS/FAIL |
| Debt-to-Equity | | <0.5 | PASS/FAIL |
| P/E Ratio | | <40 | PASS/FAIL |

**QGARP Screen Result**: [X/5 PASS] → PROCEED / FAIL

---

## 3. QUALITY SCORES

| Metric | Score | Rating |
|--------|-------|--------|
| GF Score | /100 | |
| Financial Strength | /10 | |
| Profitability Rank | /10 | |
| Growth Rank | /10 | |
| Piotroski F-Score | /9 | |
| Altman Z-Score | | Safe (>2.99) / Grey (1.81-2.99) / Distress (<1.81) |

**Quality Assessment**: [Strong / Moderate / Weak]

---

## 4. FINANCIAL STRENGTH & RISK ANALYSIS

### Balance Sheet Health
| Metric | Value | Threshold | Result |
|--------|-------|-----------|--------|
| Debt-to-Equity | | <0.5 (ideal <0.3) | |
| Debt-to-EBITDA | | <3.0x | |
| Interest Coverage | | >5.0x | |
| Current Ratio | | >1.5 | |
| Quick Ratio | | >1.0 | |
| Cash Ratio | | >0.3 | |

### Red Flag Check
- [ ] Debt-to-Equity > 0.8 → **DISQUALIFY**
- [ ] Interest Coverage < 2x → **DISQUALIFY**
- [ ] Deteriorating debt metrics (3+ years) → **WATCH**

**Financial Strength Verdict**: [PASS / PASS WITH CAUTION / FAIL]

---

## 5. RULE #1 "BIG FOUR" GROWTH ANALYSIS

| Metric | 1-Year | 3-Year | 5-Year | 10-Year | Consistent >10%? |
|--------|--------|--------|--------|---------|------------------|
| Revenue Growth | | | | | |
| EPS Growth | | | | | |
| Book Value/Share Growth | | | | | |
| Operating Cash Flow Growth | | | | | |

**Growth Consistency**: [Excellent / Good / Inconsistent / Poor]
**Conservative Growth Rate for Valuation**: [X]% (use lowest of Equity growth or analyst EPS estimate)

---

## 6. PROFITABILITY METRICS

| Metric | Value | vs Industry | Trend |
|--------|-------|-------------|-------|
| ROE | | | |
| ROA | | | |
| ROIC | | | |
| Gross Margin | | | |
| Operating Margin | | | |
| Net Margin | | | |
| FCF Margin | | | |

**Profitability Assessment**: [Superior / Average / Below Average]

---

## 7. MOAT INDICATORS

| Indicator | Evidence | Strength |
|-----------|----------|----------|
| ROIC Persistence (5-10yr above WACC ~8-10%) | | |
| Gross Margin Stability | | |
| Pricing Power (margin trends) | | |
| Cash Conversion Cycle | | |

**Preliminary Moat Rating**: [None / Weak / Narrow / Wide]
**Note**: Full moat analysis requires qualitative research beyond financial data.

---

## 8. VALUATION ANALYSIS

### Current Multiples vs History & Industry
| Metric | Current | Historical Median | Industry Median | Assessment |
|--------|---------|-------------------|-----------------|------------|
| P/E | | | | |
| P/B | | | | |
| P/S | | | | |
| EV/EBITDA | | | | |
| PEG | | | | |

### Intrinsic Value Estimates
| Method | Value | vs Current Price |
|--------|-------|------------------|
| GF Value | | Premium/Discount % |
| DCF (Earnings-based) | | |
| DCF (FCF-based) | | |

### Rule #1 Sticker Price Calculation
- Current EPS (TTM): $
- Conservative Growth Rate: %
- Future P/E (2x growth rate, max 40):
- Future EPS (10yr): $
- Future Price: $
- **Sticker Price** (÷4.05 for 15% return): $
- **Buy Price** (50% MOS): $

**Valuation Verdict**: [Undervalued / Fairly Valued / Overvalued]
**Current Price vs Buy Price**: [X]% [above/below]

---

## 9. BUSINESS CYCLE PHASE

Based on revenue growth rate and operating margin trends:

| Metric | Value |
|--------|-------|
| Revenue Growth (5yr) | |
| Operating Margin | |
| Operating Margin Trend | Expanding / Stable / Contracting |
| FCF Generation | Positive / Negative |
| Capital Returns (Dividends/Buybacks) | Yes / No |

**Phase Classification**: [1-Startup / 2-Hypergrowth / 3-Self-Funding / 4-Operating Leverage / 5-Capital Return / 6-Decline]

**Appropriate Valuation Method**: [TAM-based / DCF & Rule #1 / Dividend Discount]
**Required Margin of Safety**: [40% / 50% / 60-70%]

---

## 10. INSTITUTIONAL ACTIVITY

| Category | Buying % | Selling % | Net |
|----------|----------|-----------|-----|
| Gurus | | | |
| Funds | | | |
| ETFs | | | |

**Institutional Sentiment**: [Accumulation / Mixed / Distribution]

---

## 11. SUMMARY SCORECARD

| Category | Score/Rating | Weight | Weighted |
|----------|--------------|--------|----------|
| QGARP Screen | /5 | 20% | |
| Quality Scores | /10 | 15% | |
| Financial Strength | PASS/FAIL | 20% | |
| Growth Consistency | /4 | 15% | |
| Profitability | /10 | 10% | |
| Valuation | /10 | 20% | |

**OVERALL SCORE**: [X/100]

---

## 12. INVESTMENT DECISION

### Proceed to Full Analysis?
- [ ] QGARP Screen: PASS (≥4/5)
- [ ] Financial Strength: PASS
- [ ] Quality Score (GF): ≥70
- [ ] Growth Consistency: ≥2/4 Big Four above 10%

**GATE DECISION**: [✅ PROCEED TO MOAT & QUALITATIVE ANALYSIS / ❌ DISCARD / ⏸️ WATCHLIST]

### If Proceeding - Key Items for Deep Dive:
1. **Moat Analysis**: [Specific areas to investigate]
2. **Risk Factors**: [10-K review priorities]
3. **Recession Scenario**: [Key questions to answer]
4. **Catalysts**: [Potential positive/negative triggers]

### Price Targets
| Level | Price | Notes |
|-------|-------|-------|
| Buy Price (50% MOS) | $ | Aggressive entry |
| Sticker Price (Fair Value) | $ | Hold zone ceiling |
| Sell Price (150% of Fair Value) | $ | Overvaluation exit |
| Stop Loss (15-20% below entry) | $ | Risk management |

---

*Generated: [Date]*
*Data Source: GuruFocus MCP Server*
*Note: This scorecard provides quantitative screening only. Full investment decision requires qualitative moat analysis, 10-K risk review, and recession scenario testing per the QGARP Investment Process.*

**Disclaimer**: This output is for educational and informational purposes only and does not constitute investment advice, recommendation, or offer to sell or a solicitation of an offer to buy any securities. Returns are not guaranteed. Users should conduct their own due diligence and consult with a qualified financial advisor before making any investment decisions. "Rule #1", "Phil Town", and "Sticker Price" are utilized here for educational demonstration of published methodologies and do not imply any affiliation with or endorsement by Rule #1 Investing, LLC.
"""

    @mcp.prompt("execution_risk_analysis")
    def execution_risk_analysis(ticker: str) -> str:
        """Analyze execution risks for a company based on SEC filings and news.

        Performs qualitative risk assessment across four dimensions:
        Concentration, Disruption, Outside Forces, and Competition.

        Args:
            ticker: The stock ticker symbol to analyze (e.g. AAPL)
        """
        return f"""You are an expert risk analyst specializing in identifying and evaluating operational and strategic risks from financial filings and news sources.

## YOUR MISSION

Perform a comprehensive execution risk assessment for **{ticker}** by:
1. Searching for and analyzing the most recent 10-K and 10-Q SEC filings
2. Searching for recent news and developments about the company
3. Assessing four critical risk dimensions using the Red/Yellow/Green framework
4. Providing evidence-based ratings with specific citations

## DATA ACQUISITION

**Search for these sources:**
1. **SEC 10-K Filing** (annual report) - Focus on:
   - Risk Factors section
   - MD&A (Management Discussion & Analysis)
   - Business Overview
2. **SEC 10-Q Filing** (quarterly) - Focus on:
   - Updated risk factors
   - Recent developments
3. **Recent News** - Search for:
   - "{ticker} customer concentration"
   - "{ticker} regulatory risk"
   - "{ticker} competition pressure"
   - "{ticker} industry disruption"

State which documents you found: "Analyzing {ticker} using 10-K from [date] and 10-Q from [quarter]"

## RISK ASSESSMENT FRAMEWORK

Apply these classifications strictly:

### Concentration Risk
- 🔴 **Red**: Single customer >20% of revenue, or top 3 customers >50%
- 🟡 **Yellow**: Largest customer 10-20% of revenue
- 🟢 **Green**: Highly diversified, no customer >10%

### Disruption Risk
- 🔴 **Red**: Identifiable disruption threat to core business (AI replacing product, technology shift, new business models)
- 🟡 **Yellow**: Normal industry evolution, manageable adaptation required
- 🟢 **Green**: Company is the disruptor or well-positioned for change

### Outside Forces Risk
- 🔴 **Red**: High exposure to regulation, commodity prices, government policy, interest rates, or geopolitical factors
- 🟡 **Yellow**: Normal exposure, manageable with existing strategies
- 🟢 **Green**: Low exposure, business relatively insulated

### Competition Risk
- 🔴 **Red**: Severe pricing pressure, margin compression, fragmented market with no differentiation
- 🟡 **Yellow**: Normal competitive environment, stable market position
- 🟢 **Green**: Monopoly/Duopoly dynamics, strong moat, pricing power

## OUTPUT FORMAT

Generate the following report in clean Markdown (no code blocks):

---

# ⚠️ Execution Risk Analysis: [Company Name] ({ticker})

## 📊 Overall Summary
**Overall Risk Level:** [High 🔴 / Medium 🟡 / Low 🟢]
**Primary Risk Factors:** [List 1-2 highest risk areas]
**Key Mitigation:** [Strongest defensive position if any]

---

## 🎯 RISK ASSESSMENT DETAILS

### 🧩 Concentration
- **Rating:** [🔴 Red / 🟡 Yellow / 🟢 Green] | **Trend:** [↗️ Increasing / ➡️ Stable / ↘️ Decreasing]
- **Evidence:**
  - [Specific data point with citation, e.g., "Top 3 customers = 45% of revenue (10-K Risk Factors)"]
  - [Additional supporting evidence]

### 🔄 Disruption
- **Rating:** [🔴 Red / 🟡 Yellow / 🟢 Green] | **Trend:** [↗️/➡️/↘️]
- **Evidence:**
  - [Specific threat or advantage with citation]
  - [Technology/market shift details]

### 🌍 Outside Forces
- **Rating:** [🔴 Red / 🟡 Yellow / 🟢 Green] | **Trend:** [↗️/➡️/↘️]
- **Evidence:**
  - [Regulatory exposure details]
  - [Commodity/macro dependencies]
  - [Geopolitical factors]

### 🏁 Competition
- **Rating:** [🔴 Red / 🟡 Yellow / 🟢 Green] | **Trend:** [↗️/➡️/↘️]
- **Evidence:**
  - [Market structure data with citation]
  - [Margin trends, pricing power indicators]

---

## 📋 Risk Assessment Matrix

| Risk Factor | Rating | Evidence Strength | Trend | Management Response |
|-------------|--------|-------------------|-------|---------------------|
| Concentration | [🔴/🟡/🟢] | [Strong/Moderate/Limited] | [↗️/➡️/↘️] | [Disclosed actions] |
| Disruption | [🔴/🟡/🟢] | [Strong/Moderate/Limited] | [↗️/➡️/↘️] | [Disclosed actions] |
| Outside Forces | [🔴/🟡/🟢] | [Strong/Moderate/Limited] | [↗️/➡️/↘️] | [Disclosed actions] |
| Competition | [🔴/🟡/🟢] | [Strong/Moderate/Limited] | [↗️/➡️/↘️] | [Disclosed actions] |

---

## 🔍 Risk Interconnections

[2-3 sentences analyzing how risks compound or offset each other]

## 🛡️ Defensive Positions

[List 1-3 company strengths that mitigate risks, based on filing disclosures]

---

## 📗 Sources

[1] [Company] 10-K [Date] - sec.gov
[2] [Company] 10-Q [Quarter] - sec.gov
[3] [News/Research source] - domain.com

---

## 📌 Risk-Adjusted Investment Implications

| Scenario | Probability | Impact on Fair Value |
|----------|-------------|----------------------|
| [Key risk scenario 1] | [X%] | [+/-X%] |
| [Key risk scenario 2] | [X%] | [+/-X%] |
| [Status quo] | [X%] | [Neutral] |

**Risk-Adjusted Recommendation**: [Summary guidance on margin of safety adjustments and key monitoring items]

---

*Generated: [Date]*
*Analysis Framework: Execution Risk Protocol v2.0*

**Disclaimer**: This analysis is for educational and informational purposes only and does not constitute investment advice. Risk assessments are based on publicly available information and may not reflect all material risks. Users should conduct their own due diligence and consult with a qualified financial advisor before making investment decisions.

---

## BEHAVIORAL RULES

- Apply Red/Yellow/Green classifications strictly per defined criteria
- Default to Yellow if evidence is ambiguous or limited
- Prioritize most recent filing data (last 12 months)
- State "Limited disclosure" if company doesn't provide specific risk data
- Use bullet points for evidence (not paragraphs)
- Include trend arrows to show directional changes
- Cite filing sections inline with evidence statements
- Calculate overall risk as weighted average: Red=3, Yellow=2, Green=1
  - 2.5+ = High Risk (Red)
  - 1.5-2.4 = Medium Risk (Yellow)
  - <1.5 = Low Risk (Green)
"""
