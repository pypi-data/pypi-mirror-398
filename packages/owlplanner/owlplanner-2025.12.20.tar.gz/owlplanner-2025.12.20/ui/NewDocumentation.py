import streamlit as st

import sskeys as kz

col1, col2, col3 = st.columns([0.69, 0.02, 0.29], gap="large")
with col1:
    st.markdown("# :material/help: Documentation")
    kz.divider("orange")
    st.markdown("## :orange[Owl Retirement Planner]\n-------")
with col3:
    st.image("http://github.com/mdlacasse/Owl/blob/main/docs/images/owl.png?raw=true")
    st.caption("Retirement planner with great wisdom")

col1, col2 = st.columns([0.80, 0.20], gap="large")
with col1:
    st.markdown("""
### Owl - Optimal Wealth Lab
#### A retirement financial exploration tool based on linear programming

Owl is a free and open-source retirement planning tool that provides cutting-edge
optimization capabilities, allowing users to experiment with their own financial future
while providing a codebase where they can learn and contribute.
The Streamlit interface provides an intuitive and easy-to-use
experience that allows a broad set of users to benefit from the application
with only basic financial knowledge.

**Important:** Owl is not a planning tool in the traditional sense, but rather an environment
for exploring *what if* scenarios. It provides different realizations of a financial strategy
through rigorous mathematical optimization of relevant decision variables.

Using a linear programming approach, Owl can optimize two different objectives:
1. **Maximize net spending** under the constraint of a desired bequest, or
2. **Maximize after-tax bequest** under the constraint of a desired net spending amount.

In each case, Roth conversions are optimized to reduce the tax burden,
while federal income tax and Medicare premiums (including IRMAA) are calculated.

A full description of the package can be found on the GitHub
[repository](https://github.com/mdlacasse/Owl), and the mathematical
formulation of the optimization problem can be found
[here](https://github.com/mdlacasse/Owl/blob/main/docs/owl.pdf).

-------------------------------------------------
### :orange[Table of Contents]

[Getting Started with User Interface](#getting-started-with-user-interface)

[Case Setup](#case-setup)
- [:material/person_add: Create Case](#person-add-create-case)
- [:material/home: Household Financial Profile](#home-household-financial-profile)
    - [:material/work_history: Wages and Contributions](#work-history-wages-and-contributions)
    - [:material/account_balance: Debts and Fixed Assets](#account-balance-debts-and-fixed-assets)
- [:material/currency_exchange: Fixed Income](#currency-exchange-fixed-income)
- [:material/savings: Savings Assets](#savings-savings-assets)
- [:material/percent: Asset Allocation](#percent-asset-allocation)
- [:material/monitoring: Rates Selection](#monitoring-rates-selection)
- [:material/tune: Optimization Parameters](#tune-optimization-parameters)

[Single Scenario](#single-scenario)
- [:material/stacked_line_chart: Graphs](#stacked-line-chart-graphs)
- [:material/data_table: Worksheets](#data-table-worksheets)
- [:material/description: Output Files](#description-output-files)

[Multiple Scenarios](#multiple-scenarios)
- [:material/history: Historical Range](#history-historical-range)
- [:material/finance: Monte Carlo](#finance-monte-carlo)

[Resources](#resources)
- [:material/rocket_launch: Quick Start](#rocket-launch-quick-start)
- [:material/help: Documentation](#help-documentation)
- [:material/settings: Settings](#settings-settings)
- [:material/error: Logs](#error-logs)
- [:material/info: About Owl](#info-about-owl)

[Tips](#tips)
- [:material/lightbulb_2: Advice on Optimization and Roth Conversions]
(#lightbulb-2-advice-on-optimization-and-roth-conversions)
- [:material/rule_settings: Typical Workflow](#rule-settings-typical-workflow)
- [:material/mindfulness: Scope of Use](#mindfulness-scope-of-use)

--------------------------------------------------------------------------------------
### :orange[Getting Started with User Interface]

The Owl interface is organized into four main sections in the menu bar:
[Case Setup](#case-setup), [Single Scenario](#single-scenario),
[Multiple Scenarios](#multiple-scenarios), and [Resources](#resources).

**Navigation and Case Management**

A `Case selector` dropdown box located at the top of most pages allows you to
navigate between different scenarios you've created.
When on the [Create Case](#person-add-create-case) page, the selector box offers two additional options:
- `New Case...` - to create a new case from scratch
- `Upload Case File...` - to create a case from a *case* parameter file

The case selector is present on all pages except those in the [Resources](#resources) section.
The currently displayed case is marked with a small red triangle.

**Typical Workflow**

A typical workflow involves:
1. Creating a base case with your primary assumptions
2. Copying the base case to create variations with different parameters
3. Running all cases and comparing results on the [Output Files](#description-output-files) page

This approach allows you to explore how different assumptions affect your financial outcomes.
The [Typical Workflow](#rule-settings-typical-workflow) section below provides a more detailed example.

**Units and Conventions**

Owl uses a full year as the standard unit of time. All values are entered and
reported as yearly values (wages, income, rates, social security, etc.).

**Dollar values:**
- Most dollar inputs are entered in **thousands** (\\$k)
- **Tables** (Wages and Contributions, Debts, Fixed Assets) use **unit dollars** (\\$)
- **Graphs** display values in thousands, either in nominal dollars or today's dollars
- **Fixed Income** page uses **monthly amounts** in today's dollars (not thousands)

**Related Cases**

Cases are considered "related" if they have the same individual names.
Only related cases can be compared side-by-side on the Output Files page.
All other parameters can differ between related cases.

-------------------------------------------------
### :orange[Case Setup]

This section contains all the steps for creating and configuring case scenarios.
For new cases, every page in this section should be visited and parameters
entered according to your personal situation.

**Progress Tracking**

To help you track your progress, a progress bar appears at the bottom of each Case Setup page.
The progress bar shows:
- Which pages you've visited (marked with a checkmark)
- Your current page (marked with an orange dot)
- Pages not yet visited (marked with an empty circle)
- Overall completion percentage

The progress bar automatically marks each page as visited when you view it.

#### :material/person_add: Create Case

The **Create Case** page is where every new scenario begins.
This page controls case creation, copying, renaming, and deletion.

**Creating a New Case**

To create a scenario from scratch, you must provide:
- First name(s) for each individual
- Marital status (single or married)
- Birth date(s) - year and month
- Life expectancy (expected longevity) for each individual

**Why birth dates matter:** Social Security rules have special considerations
for those born on the 1st or 2nd of the month. If you're not born on those days,
any other day of the month will generate the same results.

**Plan Timeline**

The plan starts on January 1st of the current year and ends on December 31st
of the year when all individuals have passed according to their specified life expectancies.

**Case Management**

- **Copy Case:** Creates a duplicate of the current case with a number appended
  (e.g., "My Case" becomes "My Case (1)"). All parameters are copied.
- **Create Case:** Finalizes the case creation and enables all other Case Setup pages.
  This button is only enabled when all required fields are complete.
- **Delete Case:** Permanently removes the case (cannot be undone).
- **Rename:** Edit the case name directly in the text field.

**Using a Case File**

You can create a case from a *case* parameter file (`.toml` format).
These files are human-readable and contain all parameters for a scenario.
Example case files are available in the GitHub
[examples directory](https://github.com/mdlacasse/Owl/blob/main/examples/).

When you upload a case file, all fields in the Case Setup section will be populated
with the values from the file.

**Saving Case Files**

A case file for your current scenario can be saved from the
[Output Files](#description-output-files) page.
When saved from the interface, the filename will start with `case_` followed by the case name.
You can reload a saved case file later to reproduce the same scenario.

#### :material/home: Household Financial Profile

The **Household Financial Profile** page contains two major sections:
1. **Wages and Contributions** - for each individual
2. **Debts and Fixed Assets** - for the household

You can enter values directly in the tables on this page, or upload an Excel workbook
containing all the data. The Excel file can include:
- Future wages and contributions
- Past and future Roth contributions and conversions
- Debts
- Fixed assets

**Uploading Excel Files**

If your case references a Household Financial Profile file, you'll see a reminder
to upload it. You can upload Excel (`.xlsx`) or OpenDocument Spreadsheet (`.ods`) files.

A template file is available
[here](https://github.com/mdlacasse/Owl/blob/main/examples/template.xlsx?raw=true)
to help you get started.

##### :material/work_history: Wages and Contributions

The **Wages and Contributions** tables track annual income, savings contributions,
Roth conversions, and major expenses for each individual.

**Important:** All values in these tables are in **nominal dollars** (\\$), not thousands (\\$k).

**Table Structure**

Each individual has their own table with 9 columns:

| Column | Description |
|--------|-------------|
| `year` | Calendar year (read-only) |
| `anticipated wages` | Annual gross wages minus tax-deferred contributions |
| `ctrb taxable` | Contributions to taxable accounts |
| `ctrb 401k` | Contributions to 401k/403b accounts (includes employer contributions) |
| `ctrb Roth 401k` | Contributions to Roth 401k accounts |
| `ctrb IRA` | Contributions to traditional IRA accounts |
| `ctrb Roth IRA` | Contributions to Roth IRA accounts |
| `Roth conv` | Manual Roth conversions (overrides optimization if enabled) |
| `big-ticket items` | Major one-time expenses or income (can be negative) |

**Historical Data (Five Years Back)**

The tables include five years of historical data to track past Roth contributions and conversions.
This is required to enforce the five-year maturation rule for Roth accounts.

**Roth Account Rules:**
- **Conversions:** Cannot be withdrawn for 5 years without penalty.
  Owl maintains a retainer equal to all conversions from the last 5 years plus potential gains.
- **Contributions:** Can be withdrawn, but a retainer covers potential gains from
  contributions made over the last 5 years.
- **Gains:** Assumed to be 10% per year for past years, using predicted returns for future years.

**Note:** This approach is more restrictive than actual IRS rules but avoids penalties
while keeping the model simple. In some cases, constraints on Roth withdrawals can make
a zero bequest impossible if Roth conversions took place in the five years before passing.

**Anticipated Wages**

This column represents annual income from employment or other sources (e.g., rentals).
It does **not** include:
- Dividends from taxable investment accounts (calculated automatically)
- Tax-deferred contributions (already subtracted)

**Retirement Age**

There's no fixed "retirement age" in Owl. You simply stop entering wages in the year
you retire or reduce your work load. The transition can be gradual or sudden.

**Contributions**

- **401k/403b:** Includes both your contributions and employer matching
- **IRA:** Treated separately for easier data entry
- **Roth accounts:** Tracked separately for tax-free growth

**Manual Roth Conversions**

The `Roth conv` column allows you to specify Roth conversions manually.
When the option `Convert as in contribution file` is enabled on the
[Optimization Parameters](#tune-optimization-parameters) page,
these values will be used instead of optimized conversions.

This feature is useful for:
- Comparing optimized vs. manual conversion strategies
- Testing specific conversion scenarios

**Big-Ticket Items**

This column tracks major one-time expenses or income:
- House purchases or sales
- Large gifts or inheritances
- Other significant financial events

**Important:** This is the **only** column that can contain negative numbers.
- **Positive values:** Added to cash flow, surplus deposited in taxable accounts
- **Negative values:** May trigger additional withdrawals from retirement accounts

**Excel File Format**

When using an Excel workbook:
- Each individual must have a sheet named with their first name
- Column names are case-sensitive and must be lowercase
- Missing years or empty cells are filled with zeros
- Years outside the plan timeline are ignored (except for the 5-year history)
- Extra columns are ignored (useful for calculations)

**Saving Your Data**

After entering or editing values in the tables, you can save them as an Excel file
from the [Output Files](#description-output-files) page using the
`Download Wages and Contributions` button.
This allows you to reload the same data later.

##### :material/account_balance: Debts and Fixed Assets

These tables track household debts and fixed assets that affect your financial plan.

**Important Note:** Owl does **not** optimize debt payments. The question
*"Should I pay my mortgage or leave my money invested?"* involves risk tolerance
and cannot be answered by comparing interest rates alone.

**Debts**

Debts are used to track mortgage and loan payments that are **not included**
in the net spending amount. These payments are treated as separate expenses.

**Key Points:**
- Debt payments are automatically calculated based on loan terms
- Remaining debt at the end of the plan is deducted from savings accounts
- A bequest of zero ensures sufficient funds remain to pay remaining debts
- Mortgage interest is **not** deducted for tax purposes
  (Owl assumes you take the standard deduction)

**Debts Table Structure**

| Column | Description | Notes |
|--------|-------------|-------|
| `name` | Unique name for the debt | Required |
| `type` | Type of debt | `loan` or `mortgage` |
| `year` | Origination year | Year the loan started |
| `term` | Loan term in years | 1-30 years |
| `amount` | Original loan amount | In dollars (\\$) |
| `rate` | Annual interest rate | As a percentage (e.g., 4.5 for 4.5%) |

**Fixed Assets**

Fixed assets represent illiquid assets such as:
- Primary residence
- Real estate investments
- Collectibles
- Precious metals
- Stocks (restricted or long-term holdings)
- Fixed annuities (lump-sum)

**Tax Treatment**

When a fixed asset is disposed of (in the year of disposition, or "yod"),
the proceeds are separated into three categories based on the asset type:
1. **Tax-free** - Basis returned without tax
2. **Ordinary income** - Taxed at regular income tax rates
3. **Capital gains** - Taxed at capital gains rates

**Fixed Assets Table Structure**

| Column | Description | Notes |
|--------|-------------|-------|
| `name` | Unique name for the asset | Required |
| `type` | Type of asset | See types below |
| `basis` | Cost basis | Original purchase price in dollars |
| `value` | Current value | Current market value in dollars |
| `rate` | Annual growth rate | As a percentage (e.g., 3.0 for 3%) |
| `yod` | Year of disposition | When the asset will be sold/disposed |
| `commission` | Sale commission | As a percentage (e.g., 6.0 for 6%) |

**Fixed Asset Types**

The following asset types are supported:
- **`residence`** - Primary residence (up to \\$250k/\\$500k exclusion for single/married)
- **`real estate`** - Investment real estate (standard capital gains treatment)
- **`collectibles`** - Collectibles
(treated as standard capital gain, while special capital gains rate (28% max) should apply)
- **`precious metals`** - Precious metals
(treated as standard capital gain, while special capital gains rate (28% max) should apply)
- **`stocks`** - Stocks or securities (standard capital gains treatment)
- **`fixed annuity`** - Fixed-rate lump-sum annuities (taxed as ordinary income, minus basis)

**Assets Disposed After Plan End**

If a fixed asset has a year of disposition (yod) that is **after** the end of your plan,
the asset is assumed to be liquidated at the end of the plan and added to your bequest.
These assets are valued at their future value (accounting for growth and commission)
and added to the bequest without tax implications (step-up in basis).

**Excel File Format**

The Household Financial Profile workbook can optionally include:
- A **Debts** sheet with the debt table
- A **Fixed Assets** sheet with the fixed assets table

These sheets follow the same structure as the tables shown in the UI.

#### :material/currency_exchange: Fixed Income

This page is for entering anticipated fixed income from pensions and Social Security.

**Important:** Unlike other pages, amounts on this page are entered as
**monthly amounts in today's dollars**, not in thousands.

**Social Security**

**Primary Insurance Amount (PIA)**

The monthly Social Security amount you enter should be your Primary Insurance Amount (PIA),
which is the monthly benefit you would receive at your Full Retirement Age (FRA).
Your FRA varies between 65 and 67 depending on your birth year.

**Getting Your PIA**

The PIA is always in today's dollars and is updated annually with cost-of-living adjustments (COLA).
You can get your PIA from:
- Your Social Security statement
- The SSA website's benefit estimator
- [ssa.tools](https://ssa.tools/calculator) - a comprehensive calculator that uses your full earnings record

**How Owl Uses Your PIA**

Owl:
- Uses your exact FRA based on your birth year
- Adjusts the PIA based on when you claim benefits (early or late)
- Calculates spousal benefits (claimed when both spouses have claimed)
- Calculates survivor benefits (largest of both benefits)
- Handles partial-year benefits in the first year

**Important Limitations**

Owl does **not** optimize when to claim Social Security.
You must decide your claiming strategy based on your personal goals.
For guidance, consider:
- [opensocialsecurity.com](https://opensocialsecurity.com) - optimization tool
- [ssa.tools](https://ssa.tools) - comprehensive calculators
- [ssa.gov](https://ssa.gov) - official SSA resources

**Complex cases** involving divorce or deceased spouses are not currently supported.

**Pensions**

Pension amounts can be entered for each individual.
Unlike Social Security (which is always inflation-adjusted), pensions can optionally
be indexed for inflation by selecting the corresponding checkbox.

**Starting Dates**

For both Social Security and pensions:
- The selected month and age, combined with your birth month, determines
  when benefits start in the first year
- The total annual amount for the first year is adjusted if benefits don't
  start at the beginning of the year

#### :material/savings: Savings Assets

This page allows you to enter current balances for all savings accounts.

**Important:** All amounts are entered in **thousands of dollars** (\\$k).

**Account Types**

Three types of savings accounts are tracked separately for each spouse:

1. **Taxable** - Investment accounts, CDs, savings accounts
   - Dividends and capital gains are taxed annually
   - Withdrawals are not taxed (basis already taxed)

2. **Tax-deferred** - 401k, 403b, traditional IRA
   - Contributions are pre-tax
   - Withdrawals are taxed as ordinary income
   - Required Minimum Distributions (RMDs) apply after age 73

3. **Tax-free** - Roth 401k, Roth IRA
   - Contributions are post-tax
   - Withdrawals are tax-free (after 5-year rule)
   - No RMDs required

**Account Balance Date**

Account values are assumed to be as of January 1st of the current year.
If you know your balance as of a different date, you can specify the `Account balance date`.
Owl will back-project the amount to January 1st using the return rates and allocations
assumed for the first year.

**Married Couples - Beneficiary Fractions**

For married couples, you can configure:
- **Beneficiary fractions** - How much of each account goes to the surviving spouse
- **Surplus deposit fraction** - How to split surplus budget money between spouses' taxable accounts

**Important Considerations:**

- When beneficiary fractions are not all 1.0, it's recommended to deposit all
  surplus money in the taxable account of the first spouse to pass.
  Otherwise, the optimizer may find creative solutions that generate surpluses
  to maximize the final bequest.

- When fractions between accounts are not all equal, solving can take longer
  (sometimes minutes) as these cases require binary variables and more complex algorithms.

- In some situations, the optimal solution may involve creative transfers from
  tax-deferred to taxable accounts through surpluses and deposits.

- Setting a surplus fraction that deposits in the survivor's account can sometimes
  lead to slow convergence, especially with varying rates.

#### :material/percent: Asset Allocation

This page allows you to select how your assets are allocated among investment options.

**Investment Options**

Owl models four investment types:
1. **S&P 500** - Equities (can represent any mix of stocks)
2. **Corporate Bonds Baa** - Corporate bonds
3. **T-Notes** - 10-year Treasury Notes
4. **Cash Assets** - Assets that track inflation (e.g., TIPS)

**Note:** When using historical data, S&P 500 represents the actual index.
When using non-historical rates, it can represent any equity mix
(domestic, international, emerging markets, etc.).

**Tax Treatment**

The main difference between equities and fixed-income securities is tax treatment:
- **Equities:** Capital gains taxed at preferential rates (0%, 15%, or 20%)
- **Fixed Income:** Interest taxed as ordinary income
- **Cash Assets:** Assumed to merely track inflation (constant real value)

**Allocation Types**

Two allocation strategies are available:

1. **Account Type** - Each account type has its own allocation
   - More aggressive in tax-exempt accounts
   - More conservative in taxable accounts
   - Naturally encourages Roth conversions (better returns in tax-free accounts)

2. **Individual** - All accounts for a given individual share the same allocation
   - More neutral approach
   - Easier to maintain overall portfolio allocation

**Time-Varying Allocations**

Allocation ratios can change over time:
- **Initial allocation** - At the beginning of the plan
- **Final allocation** - At the passing of the individual
- **Interpolation** - Linear or S-curve transition between initial and final

**S-Curve Parameters**

When using an S-curve transition:
- **Center** - Timing of the inflection point (years from now)
- **Width** - Half-width of the transition (years from center)

**Rebalancing**

Owl assumes accounts are regularly rebalanced to maintain the prescribed allocation ratios.

#### :material/monitoring: Rates Selection

This page allows you to select return rates for your investments over the plan timeline.

**All rates are nominal and annual.**

**Rate Types**

**Fixed Rates** - Stay constant year-to-year:
- **Conservative** - Lower expected returns
- **Optimistic** - Higher expected returns
- **Historical Average** - Average over a selected range of past years
- **User** - Rates you specify manually

**Varying Rates** - Change from year to year:
- **Historical** - Actual rate sequences from the past
- **Histochastic** - Stochastic rates derived from historical statistics
- **Stochastic** - Stochastic rates from user-specified statistical parameters

**Rate Components**

Rates are specified for each of the four asset types:
- S&P 500 (includes dividends)
- Corporate Bonds Baa
- T-Notes
- Cash Assets (inflation rate)

**Inflation**

Inflation affects:
- Social Security (COLA adjustments)
- Pensions (if inflation-indexed)
- Cash assets (assumed to track inflation)
- Conversion of nominal to real dollars

**Tax Rate Settings**

This page also includes settings for future tax rates:
- **Heirs marginal tax rate** - Tax rate heirs will pay on inherited tax-deferred balances
- **OBBBA expiration year** - Year when tax rates are expected to revert to pre-TCJA rates

**Expert Forecasts**

For current expert opinions on stock and bond return forecasts, see:
[Morningstar's 2025 forecast](https://www.morningstar.com/portfolios/experts-forecast-stock-bond-returns-2025-edition)

#### :material/tune: Optimization Parameters

This page allows you to configure the optimization objective and constraints.

**Objective Function**

Choose what to optimize:

1. **Maximize Net Spending** (subject to desired bequest)
   - Maximizes lifetime spending while leaving a specified bequest
   - Enter desired bequest from savings accounts (in today's \\$k)
   - Fixed assets liquidated at plan end are added separately to the bequest

2. **Maximize Bequest** (subject to desired net spending)
   - Maximizes after-tax bequest while maintaining specified spending
   - Enter desired annual net spending (in \\$k)

**Roth Conversions**

Configure Roth conversion optimization:
- **Maximum conversion amount** - Annual limit for Roth conversions
- **Which spouse can convert** - Select individual or both
- **Start year** - Year when Roth conversions can begin
- **Convert from contributions file** - Use manual conversions from Wages table instead of optimizing

**Self-Consistent Loop**

The self-consistent loop computes values that are difficult to integrate into linear programming:
- Net Investment Income Tax (NIIT)
- Capital gains tax rate (0%, 15%, or 20%)
- Phase-out of additional exemption for seniors
- Medicare and IRMAA premiums (optional)

**Turning off the loop** sets all these values to zero (faster but less accurate).

**Mutually Exclusive Operations**

Enable this to prevent:
- Roth conversions and withdrawals from tax-free accounts in the same year
- Other conflicting operations

Dropping these constraints can sometimes lead to slightly different optimal solutions.

**Medicare Premiums**

Medicare premiums start automatically when each individual reaches age 65.

Three calculation modes:
1. **Off** - No Medicare/IRMAA calculations
2. **Self-consistent loop** - Calculated iteratively (recommended)
3. **Optimize** - Integrated into optimization (slower, use for single cases only)

**Important:** Medicare optimization should **not** be used for Monte Carlo simulations
due to computational complexity.

**IRMAA History**

If any individual will be eligible for Medicare within the next two years,
you'll see fields for entering Modified Adjusted Gross Income (MAGI) for the past 1-2 years.
These values default to zero and are needed to calculate IRMAA.

**Solver Selection**

Different mixed-integer linear programming solvers are available:
- **HiGHS** (recommended) - Fast and reliable
- **CBC** (COIN-OR) - Slower, uses temporary files
- **MOSEK** - Commercial solver (if available)

All solvers produce very similar results. Performance can be unpredictable due to
the mixed-integer formulation.

**Spending Profile**

Choose how net spending varies over time:

1. **Flat** - Constant spending (adjusted for inflation)
2. **Smile** - Spending follows a "smile curve" pattern:
   - **Dip** - Percentage reduction in early retirement
   - **Increase** - Annual percentage increase (can be negative)
   - **Delay** - Years before the smile pattern starts

Default smile parameters: 15% dip, 12% increase, 0 years delay.

**Note:** Smile curves are re-scaled to have the same total spending as flat curves,
so they don't start at 100%.

**Slack Variable**

Allows net spending to deviate from the desired profile to maximize the objective.
This is provided primarily for educational purposes, as maximizing total spending
will naturally favor smaller spending early and larger spending later.

**Survivor Spending**

For married couples, specify the survivor's net spending as a percentage of
the couple's spending. A typical value is 60%.

--------------------------------------------------------------------------------------
### :orange[Single Scenario]

#### :material/stacked_line_chart: Graphs

This page displays various plots from a single optimized scenario.

**What You'll See**

The graphs show results based on:
- A single instance of rates (fixed or varying, as selected)
- Optimization according to your chosen parameters
- Either maximum net spending or maximum bequest

**Graph Options**

- **Display mode:** Today's dollars or nominal dollars
- **Full screen:** Click any graph to view in full screen
- **Interactive:** When using Plotly (default), you can zoom, pan, and toggle traces
- **Export:** Save plots as PNG files (Plotly)

**Re-running**

If you're using `histochastic` or `stochastic` rates, click the "Re-run" button
to generate a new scenario with different random rates.

#### :material/data_table: Worksheets

This page shows detailed annual worksheets with all transactions and account balances.

**Worksheets Include:**

- **Sources** - Income sources (wages, Social Security, pensions, etc.)
- **Uses** - Spending, taxes, debt payments, etc.
- **Savings** - Account balances and transactions
- **Taxes** - Detailed tax calculations
- **And more...**

**Important:** All values are in **dollars** (\\$), not thousands.

**Download Options**

- Individual worksheets can be downloaded as CSV files
- All worksheets can be downloaded as a single Excel workbook from the
  [Output Files](#description-output-files) page

**Most Actionable Information**

The first few lines of the **Sources** worksheet are the most important,
as they show withdrawals and conversions for the current year and near future.

#### :material/description: Output Files

This page allows you to compare cases and save files for future use.

**Synopsis**

The synopsis displays summary statistics for your scenario:
- Total income over the plan
- Total spending
- Final bequest
- And other key metrics

**Comparing Cases**

If you've created multiple cases (by copying and modifying parameters),
they will be compared side-by-side in the synopsis panel.
Cases must have the same individual names to be compared.

The left column shows values for the selected case,
while the right column shows differences from the selected case.

**Actions**

- **Download Synopsis** - Save the synopsis as a text file
- **Re-run All Cases** - Ensures accurate comparison with current parameters

**Excel Workbooks**

Download data in Excel format:
- **Wages and Contributions** - Data from the Household Financial Profile page
- **Worksheets** - All annual worksheets as a single Excel file

**Case Parameter File**

Download all parameters as a `.toml` file for future use.
With the case file and Wages/Contributions file, you can reproduce
the exact same scenario later.

--------------------------------------------------------------------------------------
### :orange[Multiple Scenarios]

#### :material/history: Historical Range

This page backtests your scenario over a range of historical years.

**How It Works**

- Runs multiple simulations, each starting at a different year in the selected range
- Each simulation uses the actual rate sequence that occurred in the past
- Generates a histogram showing the distribution of results
- Calculates success rate, average, and median

**Results Display**

The histogram shows:
- **N** - Number of runs completed
- **P** - Probability of success (percentage that succeeded)
- **x̄** - Average result
- **M** - Median result

**Beneficiary Fractions**

If beneficiary fractions are not all 1.0, two histograms are displayed:
1. Partial bequest at first spouse's passing
2. Final objective value (net spending or bequest) at surviving spouse's passing

#### :material/finance: Monte Carlo

This page runs Monte Carlo simulations using statistically generated rate sequences.

**How It Works**

- Generates multiple scenarios using stochastic rate models
- Each scenario uses a different random sequence of returns
- Shows distribution of outcomes as a histogram
- Calculates probability of success

**Results Display**

Similar to Historical Range:
- **N** - Number of cases run
- **P** - Probability of success
- **x̄** - Mean outcome
- **M** - Median outcome

**Infeasible Cases**

Cases that fail are termed "infeasible" - the optimizer couldn't find
a solution that satisfied all constraints.

**Performance Considerations**

Monte Carlo simulations are computationally expensive. Consider:
- Turning off Medicare calculations, or using self-consistent loop
- Running locally for better performance
- Being aware of Streamlit Community Server CPU time limits

**Beneficiary Fractions**

Same as Historical Range - two histograms if fractions are not all 1.0.

--------------------------------------------------------------------------------------
### :orange[Resources]

#### :material/rocket_launch: Quick Start

This is the landing page of the application, showing new users how to get started
quickly using an example case file.

#### :material/help: Documentation

These documentation pages you're currently reading.

#### :material/settings: Settings

**Plotting Backend**

Choose between:
- **Plotly** (default) - Interactive graphs, zoom, pan, toggle traces
- **Matplotlib** - Traditional static graphs, more mature codebase

**Plotly Tips:**
- Click legend items to toggle traces
- Double-click to show only that trace
- Double-click again to restore all traces
- Save plots as PNG files

**Menu Location**

- **Top** (default) - Menu bar at the top of the page
- **Sidebar** - Menu as a collapsible sidebar
- Default is top menu unless on a mobile device

**Streamlit App**

For the best experience, especially on Chrome:
- Install the Streamlit app on your device
- Click the "+" icon in the browser URL bar
- Select "Install Streamlit"
- The app provides more screen space and better performance

**Full Screen**

Press F11 in your browser for full-screen mode, which improves graph and worksheet visualization.

**Theme**

Owl's default theme is Dark mode. A Light theme is available in Streamlit's settings menu
(three vertical dots in the upper right).

#### :material/error: Logs

This page displays messages from the underlying Owl calculation engine.
Primarily used for debugging purposes.

#### :material/info: About Owl

Credits, disclaimers, and information about the project.

--------------------------------------------------------------------------------------
### :orange[Tips]

#### :material/lightbulb_2: Advice on Optimization and Roth Conversions

**Medicare Optimization**

Owl can optimize explicitly for Medicare costs, but this can be computationally expensive.
The self-consistent loop is usually sufficient and much faster.

**Roth Conversion Comparisons**

**Always** run comparisons between cases with and without Roth conversions.
These comparisons help quantify the effects of suggested conversions.

**Remember:** Optimizers will find the "best" approach even if it only generates
one more dollar. Real-world considerations (risk, uncertainty) may favor different strategies.

**Tax Rate Uncertainty**

All projections rely on current assumptions. To account for potential future tax rate changes,
you can specify a termination year for current tax rates to revert to higher rates.

#### :material/rule_settings: Typical Workflow

A typical workflow:

1. **Create a base case** representing your primary scenario
2. **Copy the base case** and modify the parameter you want to investigate
3. **Repeat step 2** with other values of the parameter
4. **Run all cases** and compare on the Output Files page

**Example: Investigating Roth Conversions**

1. Create "2025 - Base Case" with Roth conversions up to \\$100k
2. Copy to "2025 - No Roth Conversions" with max conversions set to 0
3. Copy to "2025 - No Roth Limit" with max conversions set to \\$800k
4. Compare all three cases on the Output Files page

**Most Actionable Information**

The first few lines of the **Sources** worksheet show withdrawals and conversions
for this year and the next few years - this is your most actionable information.

#### :material/mindfulness: Scope of Use

**Modeling Philosophy**

Computer modeling is not about predicting the future, but exploring possibilities.
Owl is designed to help you explore parameters and their effects while avoiding overmodeling.

**Overmodeling** occurs when a model has detail far beyond the uncertainty of the problem,
leading to unjustified confidence in results.

**Deliberate Limitations**

As a deliberate design choice, Owl does **not** include:
- State taxes
- Complex federal tax rules beyond the basics

**Why?** Tax rates have varied significantly over the last century.
Assuming current rates will stay fixed for 30 years is unrealistic.
The best we can do is use current rates or project from historical data,
framing the problem within a range of likely scenarios.

**Best Practices**

- **Revisit plans regularly** as new information becomes available
- **Use common sense** - it's your best ally
- **Understand limitations** - critical for interpreting results
- **Focus on actionable decisions** - near-term choices matter most

**Remember:** Retirement planning tools have inherent limitations.
Understanding these limitations is absolutely critical to interpreting results correctly.
""")
