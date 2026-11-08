# The AI-ready model: every description the agent wrote

## Channels

- **table Channels**: Order channel dimension: how the customer ordered (In-store, Mobile Order or Delivery). Filters both Sales and Tickets.
- **column ChannelID**: Channel key used by the Sales and Tickets relationships. Not meaningful to users.
- **column Channel**: Order channel: In-store, Mobile Order or Delivery. Use for channel mix and in-store vs mobile vs delivery comparisons.

## Date

- **table Date**: Calendar table: one row per day, contiguous, marked as the model's date table. Use it for all time filtering and grouping of sales and tickets.
- **column Date**: Calendar day. The primary date for every sales and ticket question; there is no separate order or ship date.
- **column Year**: Calendar year number (e.g. 2025). Use to filter or group by year. Calendar year, not a fiscal year.
- **column Month**: Month as a date (first day of the month), shown as 'Jan 2025'. Use for monthly trends over time; it keeps months of different years apart.
- **column 'Month Name'**: Month name (Jan to Dec), sorted by month number. Combines the same month across years; use for seasonality, and Month for a timeline.
- **column 'Month No'**: Month number 1 to 12. Sort order for Month Name.
- **column Weekday**: Day of week (Mon to Sun), sorted Monday first. Use for weekday vs weekend and day-of-week patterns.
- **column 'Weekday No'**: Day-of-week number, 1 = Monday to 7 = Sunday. Sort order for Weekday.

## Products

- **table Products**: Product dimension: one row per menu item, with category and list price. Filters Sales only; Tickets have no product detail.
- **column ProductID**: Product key used by the Sales relationship. Not meaningful to users.
- **column Product**: Menu item name (e.g. Latte, Cold Brew, Butter Croissant). The default label for a product; use it for questions about a product, item or drink by name.
- **column Category**: Product category: Espresso Bar, Brewed & Cold, Tea & More, Bakery & Food or Retail. Use for category, product line or menu section questions.
- **column 'List Price'**: Standard menu price for one unit of the product. Not the realized selling price: for price actually achieved, divide Total Sales by Units.

## Sales

- **table Sales**: Sales fact: one row per day, store, product and channel. Use its measures for revenue, cost, margin and units sold. Filter by Date, Stores, Products and Channels.
- **measure 'Total Sales'**: Net sales revenue. Default measure for questions about sales or revenue. Works by date, store, product, category and channel. Sum of Sales[Net Sales].
- **measure 'Total COGS'**: Total COGS (cost of goods sold) for the items sold, in currency. Use for questions about cost. Sum of Sales[COGS].
- **measure GM**: GM = gross margin (gross profit) in currency: Total Sales minus Total COGS. Use for 'gross margin', 'gross profit' or 'margin dollars'. Not General Manager. For the rate use GM %.
- **measure 'GM %'**: GM % = gross margin percentage: GM divided by Total Sales. Use for 'margin %', 'margin rate' or 'profitability'. Higher is better. A ratio; never sum or average it across rows.
- **measure Units**: Number of items sold. Use for 'units', 'quantity', 'items sold' or 'volume'. Counts items, not transactions; for transactions use Tickets[Ticket Count]. Sum of Sales[Qty].
- **column Date**: Sales date (day grain). Relates to Date[Date]; use the Date table for time filtering and grouping.
- **column StoreID**: Store key. Relates to Stores[StoreID]; use Stores columns to filter by store.
- **column ProductID**: Product key. Relates to Products[ProductID]; use Products columns to filter by product.
- **column ChannelID**: Channel key. Relates to Channels[ChannelID]; use Channels[Channel] to filter by channel.
- **column Qty**: Quantity of items sold on the row. Use the Units measure instead.
- **column 'Net Sales'**: Net sales amount for the row. Use the Total Sales measure instead.
- **column COGS**: Cost of goods sold (COGS) amount for the row. Use the Total COGS measure instead.

## Stores

- **table Stores**: Store dimension: one row per store location, with city, province and opening date. Filters both Sales and Tickets.
- **column StoreID**: Store key used by the Sales and Tickets relationships. Not meaningful to users.
- **column 'Store Name'**: Store name (e.g. King West, Gastown). The default label for a store; use it when users ask about a store, location, shop or cafe by name.
- **column City**: City where the store is located (e.g. Toronto, Montreal). Use for city-level comparisons; a city can have several stores.
- **column Province**: Canadian province code of the store (e.g. ON = Ontario, QC = Quebec, BC = British Columbia, AB = Alberta). Use for regional comparisons.
- **column 'Open Date'**: Date the store opened. Stores opened during the data period have partial history; take this into account when comparing periods or ranking stores on totals.

## Tickets

- **table Tickets**: Tickets fact: number of tickets (transactions) per day, store and channel. Has no product detail, so it cannot be filtered by Products. Use for traffic and average ticket.
- **measure 'Ticket Count'**: Number of tickets (transactions). Use for 'transactions', 'tickets', 'traffic' or 'customer count'. Works by date, store and channel; not by product or category.
- **measure 'Avg Ticket'**: Avg Ticket = average ticket: Total Sales divided by Ticket Count, i.e. average spend per transaction. Use by date, store or channel. Not meaningful by product or category.
- **column Date**: Ticket date (day grain). Relates to Date[Date]; use the Date table for time filtering and grouping.
- **column StoreID**: Store key. Relates to Stores[StoreID]; use Stores columns to filter by store.
- **column ChannelID**: Channel key. Relates to Channels[ChannelID]; use Channels[Channel] to filter by channel.
- **column Tickets**: Number of tickets on the row. Use the Ticket Count measure instead.
