# Streamlit app for Depreciation Schedule with interactive chart + Loan, Cash Flow, EBIT & Tax logic + NPV/IRR & Monte Carlo + Smart Suggestions
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# App title
st.title("Capital Budgeting: Full Financial Analysis")

# Sidebar inputs: CapEx & Depreciation
st.sidebar.header("Capital Inputs")
equipment_cost = st.sidebar.number_input("Equipment Cost", value=3000000)
shipping_cost = st.sidebar.number_input("Shipping Cost", value=500000)
installation_cost = st.sidebar.number_input("Installation Cost", value=100000)
salvage_value = st.sidebar.number_input("Salvage Value", value=300000)
life_years = st.sidebar.slider("Project Life (Years)", min_value=1, max_value=20, value=5)
depreciation_rate = st.sidebar.slider("Depreciation Rate (%)", min_value=1, max_value=100, value=30) / 100

# Sidebar inputs: Loan
st.sidebar.header("Loan Details")
loan_amount = st.sidebar.number_input("Loan Amount", value=2000000)
interest_rate = st.sidebar.slider("Interest Rate (%)", min_value=1.0, max_value=20.0, value=10.0) / 100
loan_years = st.sidebar.slider("Loan Term (Years)", min_value=1, max_value=20, value=5)

# Sidebar inputs: Revenue and Costs
st.sidebar.header("Revenue & Cost")
annual_revenue = st.sidebar.number_input("Annual Revenue", value=2000000)
annual_operating_cost = st.sidebar.number_input("Annual Operating Cost", value=700000)
tax_rate = st.sidebar.slider("Corporate Tax Rate (%)", min_value=0, max_value=50, value=25) / 100

discount_rate = st.sidebar.slider("Discount Rate for NPV (%)", min_value=1.0, max_value=25.0, value=10.0) / 100
simulations = st.sidebar.slider("Monte Carlo Simulations", 100, 10000, 1000)

# Suggestions / Corrections
st.sidebar.markdown("---")
st.sidebar.subheader("Suggestions")
if depreciation_rate < 0.1:
    st.sidebar.warning("Depreciation rate seems low. Consider industry averages of 20–30%.")
if loan_amount > equipment_cost:
    st.sidebar.warning("Loan amount exceeds equipment cost. Double-check the financing plan.")
if annual_operating_cost > annual_revenue * 0.6:
    st.sidebar.warning("High operating costs. May reduce profitability.")

# Calculate total capital cost
total_cost = equipment_cost + shipping_cost + installation_cost

# Depreciation calculation (Declining Balance)
book_value = total_cost
depreciation_schedule = []

for year in range(1, life_years + 1):
    depreciation = book_value * depreciation_rate
    if book_value - depreciation < salvage_value:
        depreciation = book_value - salvage_value
    book_value -= depreciation
    depreciation_schedule.append({
        "Year": year,
        "Depreciation": round(depreciation, 2),
        "Book Value": round(book_value, 2)
    })

dep_df = pd.DataFrame(depreciation_schedule)

# Loan Amortization (Equal principal payments)
loan_schedule = []
principal_payment = loan_amount / loan_years
remaining_loan = loan_amount

for year in range(1, loan_years + 1):
    interest_payment = remaining_loan * interest_rate
    total_payment = principal_payment + interest_payment
    remaining_loan -= principal_payment
    loan_schedule.append({
        "Year": year,
        "Principal Payment": round(principal_payment, 2),
        "Interest Payment": round(interest_payment, 2),
        "Total Payment": round(total_payment, 2),
        "Remaining Loan": round(remaining_loan, 2)
    })

loan_df = pd.DataFrame(loan_schedule)

# Merge cash flow info
cash_flow_df = pd.merge(dep_df, loan_df, on="Year", how="outer").fillna(0)
cash_flow_df["Revenue"] = annual_revenue
cash_flow_df["Operating Cost"] = annual_operating_cost
cash_flow_df["Depreciation"] = cash_flow_df["Depreciation"].fillna(0)
cash_flow_df["EBIT"] = cash_flow_df["Revenue"] - cash_flow_df["Operating Cost"] - cash_flow_df["Depreciation"]
cash_flow_df["Tax"] = cash_flow_df["EBIT"].apply(lambda x: x * tax_rate if x > 0 else 0)
cash_flow_df["Earnings After Tax"] = cash_flow_df["EBIT"] - cash_flow_df["Tax"]
cash_flow_df["Cash Outflow"] = cash_flow_df["Principal Payment"] + cash_flow_df["Interest Payment"]
cash_flow_df["Net Cash Flow"] = cash_flow_df["Earnings After Tax"] - cash_flow_df["Cash Outflow"]

# NPV and IRR Calculations
npv = np.npv(discount_rate, [-total_cost] + cash_flow_df["Net Cash Flow"].tolist())
try:
    irr = np.irr([-total_cost] + cash_flow_df["Net Cash Flow"].tolist())
except:
    irr = float('nan')

st.subheader("Financial KPIs")
st.metric("Net Present Value (NPV)", f"${npv:,.2f}")
st.metric("Internal Rate of Return (IRR)", f"{irr * 100:.2f}%")

# Smart AI Insight Box
st.markdown("### 💡 AI Insights")
st.info(f"Based on your inputs, the NPV is {'positive' if npv > 0 else 'negative'}, indicating that the project is {'financially viable' if npv > 0 else 'not profitable'}. An IRR of {irr*100:.2f}% {'exceeds' if irr > discount_rate else 'falls below'} your discount rate of {discount_rate*100:.2f}%, which {'supports' if irr > discount_rate else 'challenges'} investment.")

# Monte Carlo Simulation for NPV
npv_results = []
for _ in range(simulations):
    random_revenue = np.random.normal(annual_revenue, annual_revenue * 0.1, life_years)
    random_cost = np.random.normal(annual_operating_cost, annual_operating_cost * 0.1, life_years)
    rand_cash_flows = []
    for i in range(life_years):
        ebit = random_revenue[i] - random_cost[i] - depreciation_schedule[i]['Depreciation']
        tax = ebit * tax_rate if ebit > 0 else 0
        eat = ebit - tax
        loan_outflow = loan_df.iloc[i]["Principal Payment"] + loan_df.iloc[i]["Interest Payment"] if i < loan_years else 0
        net_cf = eat - loan_outflow
        rand_cash_flows.append(net_cf)
    simulated_npv = np.npv(discount_rate, [-total_cost] + rand_cash_flows)
    npv_results.append(simulated_npv)

st.subheader("Monte Carlo Simulation Results")
st.write(f"Mean NPV: ${np.mean(npv_results):,.2f}")
st.write(f"Std Dev of NPV: ${np.std(npv_results):,.2f}")

fig_sim = px.histogram(npv_results, nbins=50, title="Distribution of Simulated NPVs")
st.plotly_chart(fig_sim, use_container_width=True)

# Tables
st.subheader("Depreciation Schedule")
st.dataframe(dep_df)

st.subheader("Loan Repayment Schedule")
st.dataframe(loan_df)

st.subheader("Cash Flow with EBIT and Tax")
st.dataframe(cash_flow_df)

# Charts
fig_dep = px.bar(dep_df, x="Year", y="Depreciation", text="Depreciation", title="Depreciation Over Time")
fig_dep.update_traces(texttemplate='%{text:.2s}', textposition='outside')
st.plotly_chart(fig_dep, use_container_width=True)

fig_loan = px.bar(loan_df, x="Year", y=["Principal Payment", "Interest Payment"], title="Loan Repayment Breakdown")
st.plotly_chart(fig_loan, use_container_width=True)

fig_tax = px.bar(cash_flow_df, x="Year", y=["EBIT", "Tax", "Earnings After Tax"], title="EBIT, Tax, and Earnings After Tax")
st.plotly
