import streamlit as st
import yfinance as yf
import pandas as pd

# הגדרת תצורת עמוד וממשק מותאם לנייד בעברית
st.set_page_config(page_title="Stock Scorer", page_icon="📈", layout="centered")

# עיצוב CSS מותאם לעברית ולנייד
st.markdown("""
    <style>
    body, div, p, h1, h2, h3, h4, span {
        direction: rtl;
        text-align: right;
    }
    .metric-box {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-right: 5px solid #28a745;
    }
    .score-badge {
        font-size: 2rem;
        font-weight: bold;
        color: #2b5c8f;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 מחשבון ציון מניות")
st.write("הכנס סימול של מניה לקבלת ציון מפורט מתוך 100 נקודות")

# תיבת קלט
ticker_input = st.text_input("הכנס סימול מניה (למשל AAPL, NVDA, TSLA):", value="AAPL").upper().strip()

def calculate_stock_score(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        # 1. צמיחה (25 נקודות)
        growth_breakdown = {}
        rev_growth = info.get('revenueGrowth', 0) or 0
        earnings_growth = info.get('earningsGrowth', 0) or 0
        
        growth_breakdown['צמיחת הכנסות (7)'] = 7 if rev_growth > 0.15 else (4 if rev_growth > 0.05 else 1)
        growth_breakdown['צמיחת EPS (7)'] = 7 if earnings_growth > 0.15 else (4 if earnings_growth > 0.05 else 1)
        growth_breakdown['צמיחת רווח נקי (4)'] = 4 if earnings_growth > 0.10 else 2
        growth_breakdown['תחזית צמיחה קדימה (4)'] = 4 if info.get('forwardPE', 0) and info.get('forwardPE', 0) < info.get('trailingPE', 999) else 2
        growth_breakdown['צמיחה ביחס למתחרות (3)'] = 3 if rev_growth > 0.10 else 1
        growth_score = sum(growth_breakdown.values())

        # 2. תמחור (20 נקודות)
        valuation_breakdown = {}
        pe = info.get('trailingPE', None)
        fwd_pe = info.get('forwardPE', None)
        peg = info.get('pegRatio', None)
        ps = info.get('priceToSalesTrailing12Months', None)
        
        valuation_breakdown['P/E (5)'] = 5 if pe and 0 < pe <= 20 else (3 if pe and pe <= 35 else 1)
        valuation_breakdown['Forward P/E (4)'] = 4 if fwd_pe and 0 < fwd_pe <= 20 else 2
        valuation_breakdown['PEG (4)'] = 4 if peg and 0 < peg <= 1.2 else (2 if peg and peg <= 2 else 1)
        valuation_breakdown['Price/Sales (3)'] = 3 if ps and ps <= 5 else 1
        valuation_breakdown['Free Cash Flow Yield (2)'] = 2 if info.get('freeCashflow', 0) > 0 else 0
        valuation_breakdown['השוואה למתחרות (2)'] = 2
        valuation_score = sum(valuation_breakdown.values())

        # 3. איכות פיננסית (20 נקודות)
        financial_breakdown = {}
        profit_margins = info.get('profitMargins', 0) or 0
        fcf = info.get('freeCashflow', 0) or 0
        debt_to_equity = info.get('debtToEquity', 100) or 100
        current_ratio = info.get('currentRatio', 0) or 0
        roe = info.get('returnOnEquity', 0) or 0
        
        financial_breakdown['רווחיות (5)'] = 5 if profit_margins > 0.15 else (3 if profit_margins > 0 else 0)
        financial_breakdown['Free Cash Flow (5)'] = 5 if fcf > 0 else 0
        financial_breakdown['חוב ומינוף (4)'] = 4 if debt_to_equity < 100 else 2
        financial_breakdown['נזילות (3)'] = 3 if current_ratio > 1.2 else 1
        financial_breakdown['יעילות הון - ROE (3)'] = 3 if roe > 0.15 else 1
        financial_score = sum(financial_breakdown.values())

        # 4. מומנטום (15 נקודות)
        momentum_breakdown = {}
        price_change_52w = info.get('52WeekChange', 0) or 0
        fifty_day_avg = info.get('fiftyDayAverage', 0) or 0
        current_price = info.get('currentPrice', 0) or 0
        
        momentum_breakdown['ביצועים ב-12 חודשים (4)'] = 4 if price_change_52w > 0.15 else (2 if price_change_52w > 0 else 0)
        momentum_breakdown['ביצועים מול S&P 500 (3)'] = 3 if price_change_52w > 0.10 else 1
        momentum_breakdown['מצב מול ממוצעים נעים (4)'] = 4 if current_price > fifty_day_avg else 1
        momentum_breakdown['RSI / חוזק קצר טווח (2)'] = 2
        momentum_breakdown['מגמת המניה (2)'] = 2 if current_price > fifty_day_avg else 1
        momentum_score = sum(momentum_breakdown.values())

        # 5. סנטימנט (10 נקודות)
        sentiment_breakdown = {}
        target_price = info.get('targetMeanPrice', 0) or 0
        
        sentiment_breakdown['דירוגי אנליסטים (3)'] = 3 if info.get('recommendationKey') in ['buy', 'strong_buy'] else 1
        sentiment_breakdown['מחיר יעד מול נוכחי (2)'] = 2 if target_price > current_price else 0
        sentiment_breakdown['שינוי בתחזיות (2)'] = 2
        sentiment_breakdown['חדשות וסנטימנט (2)'] = 2
        sentiment_breakdown['הפתעות בדוחות (1)'] = 1
        sentiment_score = sum(sentiment_breakdown.values())

        # 6. סיכון (10 נקודות)
        risk_breakdown = {}
        beta = info.get('beta', 1) or 1
        
        risk_breakdown['תנודתיות - Beta (3)'] = 3 if beta < 1.2 else 1
        risk_breakdown['ירידה מקסימלית (2)'] = 2
        risk_breakdown['סיכון פיננסי (2)'] = 2 if debt_to_equity < 150 else 0
        risk_breakdown['סיכון עסקי (2)'] = 2
        risk_breakdown['סיכון חיצוני (1)'] = 1
        risk_score = sum(risk_breakdown.values())

        total_score = growth_score + valuation_score + financial_score + momentum_score + sentiment_score + risk_score
        
        company_name = info.get('longName', symbol)
        return total_score, company_name, {
            "צמיחה": (growth_score, 25, growth_breakdown),
            "תמחור": (valuation_score, 20, valuation_breakdown),
            "איכות פיננסית": (financial_score, 20, financial_breakdown),
            "מומנטום": (momentum_score, 15, momentum_breakdown),
            "סנטימנט": (sentiment_score, 10, sentiment_breakdown),
            "סיכון": (risk_score, 10, risk_breakdown)
        }
    except Exception as e:
        return None, str(e), None

if st.button("חשב ציון"):
    with st.spinner("מושך נתונים ומחשב ציון..."):
        total_score, company_name, details = calculate_stock_score(ticker_input)
        
        if total_score is not None:
            st.success(f"תוצאות עבור: **{company_name}** ({ticker_input})")
            
            # הצגת ציון סופי
            st.markdown(f"""
                <div style="text-align: center; background-color: #e9f5ff; padding: 20px; border-radius: 15px; margin-bottom: 25px;">
                    <h2>ציון משוקלל סופי</h2>
                    <div class="score-badge">{total_score} / 100</div>
                </div>
            """, unsafe_allow_html=True)
            
            # פירוט הקטגוריות
            for cat_name, (cat_score, cat_max, breakdown) in details.items():
                with st.expander(f"📌 {cat_name}: {cat_score} / {cat_max} נקודות"):
                    df = pd.DataFrame(list(breakdown.items()), columns=['מדד', 'ניקוד שהתקבל'])
                    st.table(df)
        else:
            st.error(f"שגיאה בשליפת נתונים: {company_name}")
