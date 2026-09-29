# CastiFy V6 temporal feature catalog

These are Gregorian calendar features, not NYSE, Tokyo or other exchange calendars.
They use the existing index-local session date; timezone-aware dates are not
converted to UTC. Weekend-dated rows are explicitly rejected by the Monday–Friday
encoding. Basic and advanced modes retain their prior behavior.

All calendar distances are zero-based date differences: a boundary day has distance
zero, and the current day is not added to the count. Month/quarter endpoints come
from calendar arithmetic, never from the next downloaded observation. The quarter
is the Gregorian calendar quarter, not a company's fiscal quarter.

Calendar facts known in advance (such as the number of days in February) are not
future market observations. No prices, volume, returns or target aggregates enter
these inputs. The previous observed-session gap uses one historical date; the first
row remains NaN. A gap may represent a weekend, holiday, missing provider row or
other absence, so it must not be labelled an exchange holiday with certainty.

Three cyclical pairs use phase zero on January, the first of the month and the
first of the year respectively. Day-of-month uses that month's actual length;
day-of-year uses 365 or 366 as appropriate. Temporal features are price/volume
scale invariant; raw calendar distances are deliberately not normalized because
calendar days have a meaningful metric, unlike arbitrary weekday category codes.

## Features

| Feature | Definition | Encoding | Range | Market values? | Future observations? | Exchange-specific? | Notes |
|---|---|---|---|---|---|---|---|
| DOW_Monday | 1 if current session date is Monday, else 0; weekend dates rejected. | one-hot | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| DOW_Tuesday | 1 if current session date is Tuesday, else 0; weekend dates rejected. | one-hot | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| DOW_Wednesday | 1 if current session date is Wednesday, else 0; weekend dates rejected. | one-hot | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| DOW_Thursday | 1 if current session date is Thursday, else 0; weekend dates rejected. | one-hot | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| DOW_Friday | 1 if current session date is Friday, else 0; weekend dates rejected. | one-hot | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| Month_Sin | sin(2*pi*(month-1)/12); calendar phase, not an ordinal category. | cyclical | [-1, 1] | No | No | No | Lookback 0 observed rows; normalized=True |
| Month_Cos | cos(2*pi*(month-1)/12); calendar phase, not an ordinal category. | cyclical | [-1, 1] | No | No | No | Lookback 0 observed rows; normalized=True |
| DayOfMonth_Sin | sin(2*pi*(day-1)/days_in_current_month); calendar phase, not an ordinal category. | cyclical | [-1, 1] | No | No | No | Lookback 0 observed rows; normalized=True |
| DayOfMonth_Cos | cos(2*pi*(day-1)/days_in_current_month); calendar phase, not an ordinal category. | cyclical | [-1, 1] | No | No | No | Lookback 0 observed rows; normalized=True |
| DayOfYear_Sin | sin(2*pi*(day_of_year-1)/(366 if leap year else 365)); calendar phase, not an ordinal category. | cyclical | [-1, 1] | No | No | No | Lookback 0 observed rows; normalized=True |
| DayOfYear_Cos | cos(2*pi*(day_of_year-1)/(366 if leap year else 365)); calendar phase, not an ordinal category. | cyclical | [-1, 1] | No | No | No | Lookback 0 observed rows; normalized=True |
| Calendar_Days_From_Month_Start | Current date minus first calendar day of current month; first day=0. | calendar-day distance | [0, 30] | No | No | No | Lookback 0 observed rows; normalized=False |
| Calendar_Days_To_Month_End | Last calendar day of current month minus current date; last day=0. | calendar-day distance | [0, 30] | No | No | No | Lookback 0 observed rows; normalized=False |
| Calendar_Days_From_Quarter_Start | Current date minus first calendar day of Gregorian quarter; first day=0. | calendar-day distance | [0, 91] | No | No | No | Lookback 0 observed rows; normalized=False |
| Calendar_Days_To_Quarter_End | Last calendar day of Gregorian quarter minus current date; last day=0. | calendar-day distance | [0, 91] | No | No | No | Lookback 0 observed rows; normalized=False |
| Is_Quarter_Start_Region | 1 in first seven calendar days of quarter (elapsed 0..6), else 0. | binary | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| Is_Quarter_End_Region | 1 in last seven calendar days of quarter (remaining 0..6), else 0. | binary | 0 or 1 | No | No | No | Lookback 0 observed rows; normalized=True |
| Calendar_Days_Since_Previous_Session | Current date minus previous observed session date, in local calendar days; first row NaN. Gaps can include missing provider rows. | calendar-day distance | >=1, first row NaN | No | No | No | Lookback 1 observed rows; normalized=False |

## Deliberate omissions

- ISO week cycles: omitted because annual phase already describes within-year
  seasonality; this avoids another near-annual pair and week-53 conventions.
- Quarter sine/cosine: calendar quarter proximity and region flags provide context
  without another cycle closely related to month/annual phase.
- Year-start/end distances: omitted because annual sine/cosine already identifies
  annual position; no absolute year or monotonically increasing session counter.
- First/last trading-day flags and forward trading-session counts: omitted because
  there is no exchange schedule. Calendar-day distances are safe substitutes.
- Explicit holiday proximity: deferred until an exchange-aware, known-in-advance
  schedule is available. Previous observed-session gap is not a holiday classifier.
- Is_Monday/Is_Friday: omitted because weekday one-hot columns already provide them.
- Weekday/month return target encodings: intentionally not implemented. Historical
  return profiles are output-only analysis and cannot enter a feature registry.

All five weekday indicators are retained as requested. They sum to one and thus
have a linear dependence with an intercept, but they are not duplicate columns.
From/to boundary distances are highly negatively correlated; their sums vary with
actual month/quarter lengths, so they are not universally affine duplicates.
V5 correlations are preserved. No feature selection or tuning is performed in V6.
