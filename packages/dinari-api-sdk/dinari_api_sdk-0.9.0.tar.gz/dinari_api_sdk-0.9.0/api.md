# V2

Types:

```python
from dinari_api_sdk.types import V2ListOrdersResponse
```

Methods:

- <code title="get /api/v2/orders/">client.v2.<a href="./src/dinari_api_sdk/resources/v2/v2.py">list_orders</a>(\*\*<a href="src/dinari_api_sdk/types/v2_list_orders_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2_list_orders_response.py">V2ListOrdersResponse</a></code>

## MarketData

Types:

```python
from dinari_api_sdk.types.v2 import MarketDataRetrieveMarketHoursResponse
```

Methods:

- <code title="get /api/v2/market_data/market_hours/">client.v2.market_data.<a href="./src/dinari_api_sdk/resources/v2/market_data/market_data.py">retrieve_market_hours</a>() -> <a href="./src/dinari_api_sdk/types/v2/market_data_retrieve_market_hours_response.py">MarketDataRetrieveMarketHoursResponse</a></code>

### Stocks

Types:

```python
from dinari_api_sdk.types.v2.market_data import (
    StockListResponse,
    StockRetrieveCurrentPriceResponse,
    StockRetrieveCurrentQuoteResponse,
    StockRetrieveDividendsResponse,
    StockRetrieveHistoricalPricesResponse,
    StockRetrieveNewsResponse,
)
```

Methods:

- <code title="get /api/v2/market_data/stocks/">client.v2.market_data.stocks.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/stocks.py">list</a>(\*\*<a href="src/dinari_api_sdk/types/v2/market_data/stock_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stock_list_response.py">StockListResponse</a></code>
- <code title="get /api/v2/market_data/stocks/{stock_id}/current_price">client.v2.market_data.stocks.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/stocks.py">retrieve_current_price</a>(stock_id) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stock_retrieve_current_price_response.py">StockRetrieveCurrentPriceResponse</a></code>
- <code title="get /api/v2/market_data/stocks/{stock_id}/current_quote">client.v2.market_data.stocks.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/stocks.py">retrieve_current_quote</a>(stock_id) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stock_retrieve_current_quote_response.py">StockRetrieveCurrentQuoteResponse</a></code>
- <code title="get /api/v2/market_data/stocks/{stock_id}/dividends">client.v2.market_data.stocks.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/stocks.py">retrieve_dividends</a>(stock_id) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stock_retrieve_dividends_response.py">StockRetrieveDividendsResponse</a></code>
- <code title="get /api/v2/market_data/stocks/{stock_id}/historical_prices/">client.v2.market_data.stocks.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/stocks.py">retrieve_historical_prices</a>(stock_id, \*\*<a href="src/dinari_api_sdk/types/v2/market_data/stock_retrieve_historical_prices_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stock_retrieve_historical_prices_response.py">StockRetrieveHistoricalPricesResponse</a></code>
- <code title="get /api/v2/market_data/stocks/{stock_id}/news">client.v2.market_data.stocks.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/stocks.py">retrieve_news</a>(stock_id, \*\*<a href="src/dinari_api_sdk/types/v2/market_data/stock_retrieve_news_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stock_retrieve_news_response.py">StockRetrieveNewsResponse</a></code>

#### Splits

Types:

```python
from dinari_api_sdk.types.v2.market_data.stocks import (
    StockSplit,
    SplitListResponse,
    SplitListForStockResponse,
)
```

Methods:

- <code title="get /api/v2/market_data/stocks/splits">client.v2.market_data.stocks.splits.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/splits.py">list</a>(\*\*<a href="src/dinari_api_sdk/types/v2/market_data/stocks/split_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stocks/split_list_response.py">SplitListResponse</a></code>
- <code title="get /api/v2/market_data/stocks/{stock_id}/splits">client.v2.market_data.stocks.splits.<a href="./src/dinari_api_sdk/resources/v2/market_data/stocks/splits.py">list_for_stock</a>(stock_id, \*\*<a href="src/dinari_api_sdk/types/v2/market_data/stocks/split_list_for_stock_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/market_data/stocks/split_list_for_stock_response.py">SplitListForStockResponse</a></code>

## Entities

Types:

```python
from dinari_api_sdk.types.v2 import Entity, EntityListResponse
```

Methods:

- <code title="post /api/v2/entities/">client.v2.entities.<a href="./src/dinari_api_sdk/resources/v2/entities/entities.py">create</a>(\*\*<a href="src/dinari_api_sdk/types/v2/entity_create_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entity.py">Entity</a></code>
- <code title="patch /api/v2/entities/{entity_id}">client.v2.entities.<a href="./src/dinari_api_sdk/resources/v2/entities/entities.py">update</a>(entity_id, \*\*<a href="src/dinari_api_sdk/types/v2/entity_update_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entity.py">Entity</a></code>
- <code title="get /api/v2/entities/">client.v2.entities.<a href="./src/dinari_api_sdk/resources/v2/entities/entities.py">list</a>(\*\*<a href="src/dinari_api_sdk/types/v2/entity_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entity_list_response.py">EntityListResponse</a></code>
- <code title="get /api/v2/entities/{entity_id}">client.v2.entities.<a href="./src/dinari_api_sdk/resources/v2/entities/entities.py">retrieve_by_id</a>(entity_id) -> <a href="./src/dinari_api_sdk/types/v2/entity.py">Entity</a></code>
- <code title="get /api/v2/entities/me">client.v2.entities.<a href="./src/dinari_api_sdk/resources/v2/entities/entities.py">retrieve_current</a>() -> <a href="./src/dinari_api_sdk/types/v2/entity.py">Entity</a></code>

### Accounts

Types:

```python
from dinari_api_sdk.types.v2.entities import Account, Jurisdiction, AccountListResponse
```

Methods:

- <code title="post /api/v2/entities/{entity_id}/accounts">client.v2.entities.accounts.<a href="./src/dinari_api_sdk/resources/v2/entities/accounts.py">create</a>(entity_id, \*\*<a href="src/dinari_api_sdk/types/v2/entities/account_create_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entities/account.py">Account</a></code>
- <code title="get /api/v2/entities/{entity_id}/accounts">client.v2.entities.accounts.<a href="./src/dinari_api_sdk/resources/v2/entities/accounts.py">list</a>(entity_id, \*\*<a href="src/dinari_api_sdk/types/v2/entities/account_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entities/account_list_response.py">AccountListResponse</a></code>

### KYC

Types:

```python
from dinari_api_sdk.types.v2.entities import (
    BaselineKYCCheckData,
    KYCInfo,
    KYCStatus,
    UsKYCCheckData,
    KYCCreateManagedCheckResponse,
)
```

Methods:

- <code title="get /api/v2/entities/{entity_id}/kyc">client.v2.entities.kyc.<a href="./src/dinari_api_sdk/resources/v2/entities/kyc/kyc.py">retrieve</a>(entity_id) -> <a href="./src/dinari_api_sdk/types/v2/entities/kyc_info.py">KYCInfo</a></code>
- <code title="post /api/v2/entities/{entity_id}/kyc/url">client.v2.entities.kyc.<a href="./src/dinari_api_sdk/resources/v2/entities/kyc/kyc.py">create_managed_check</a>(entity_id) -> <a href="./src/dinari_api_sdk/types/v2/entities/kyc_create_managed_check_response.py">KYCCreateManagedCheckResponse</a></code>
- <code title="post /api/v2/entities/{entity_id}/kyc">client.v2.entities.kyc.<a href="./src/dinari_api_sdk/resources/v2/entities/kyc/kyc.py">submit</a>(entity_id, \*\*<a href="src/dinari_api_sdk/types/v2/entities/kyc_submit_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entities/kyc_info.py">KYCInfo</a></code>

#### Document

Types:

```python
from dinari_api_sdk.types.v2.entities.kyc import (
    KYCDocument,
    KYCDocumentType,
    DocumentRetrieveResponse,
)
```

Methods:

- <code title="get /api/v2/entities/{entity_id}/kyc/{kyc_id}/document">client.v2.entities.kyc.document.<a href="./src/dinari_api_sdk/resources/v2/entities/kyc/document.py">retrieve</a>(kyc_id, \*, entity_id) -> <a href="./src/dinari_api_sdk/types/v2/entities/kyc/document_retrieve_response.py">DocumentRetrieveResponse</a></code>
- <code title="post /api/v2/entities/{entity_id}/kyc/{kyc_id}/document">client.v2.entities.kyc.document.<a href="./src/dinari_api_sdk/resources/v2/entities/kyc/document.py">upload</a>(kyc_id, \*, entity_id, \*\*<a href="src/dinari_api_sdk/types/v2/entities/kyc/document_upload_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/entities/kyc/kyc_document.py">KYCDocument</a></code>

## Accounts

Types:

```python
from dinari_api_sdk.types.v2 import (
    Chain,
    AccountGetCashBalancesResponse,
    AccountGetDividendPaymentsResponse,
    AccountGetInterestPaymentsResponse,
    AccountGetPortfolioResponse,
)
```

Methods:

- <code title="get /api/v2/accounts/{account_id}">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">retrieve</a>(account_id) -> <a href="./src/dinari_api_sdk/types/v2/entities/account.py">Account</a></code>
- <code title="post /api/v2/accounts/{account_id}/deactivate">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">deactivate</a>(account_id) -> <a href="./src/dinari_api_sdk/types/v2/entities/account.py">Account</a></code>
- <code title="get /api/v2/accounts/{account_id}/cash">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">get_cash_balances</a>(account_id) -> <a href="./src/dinari_api_sdk/types/v2/account_get_cash_balances_response.py">AccountGetCashBalancesResponse</a></code>
- <code title="get /api/v2/accounts/{account_id}/dividend_payments">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">get_dividend_payments</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/account_get_dividend_payments_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/account_get_dividend_payments_response.py">AccountGetDividendPaymentsResponse</a></code>
- <code title="get /api/v2/accounts/{account_id}/interest_payments">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">get_interest_payments</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/account_get_interest_payments_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/account_get_interest_payments_response.py">AccountGetInterestPaymentsResponse</a></code>
- <code title="get /api/v2/accounts/{account_id}/portfolio">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">get_portfolio</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/account_get_portfolio_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/account_get_portfolio_response.py">AccountGetPortfolioResponse</a></code>
- <code title="post /api/v2/accounts/{account_id}/faucet">client.v2.accounts.<a href="./src/dinari_api_sdk/resources/v2/accounts/accounts.py">mint_sandbox_tokens</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/account_mint_sandbox_tokens_params.py">params</a>) -> None</code>

### Wallet

Types:

```python
from dinari_api_sdk.types.v2.accounts import Wallet
```

Methods:

- <code title="post /api/v2/accounts/{account_id}/wallet/internal">client.v2.accounts.wallet.<a href="./src/dinari_api_sdk/resources/v2/accounts/wallet/wallet.py">connect_internal</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/wallet_connect_internal_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/wallet/wallet.py">Wallet</a></code>
- <code title="get /api/v2/accounts/{account_id}/wallet">client.v2.accounts.wallet.<a href="./src/dinari_api_sdk/resources/v2/accounts/wallet/wallet.py">get</a>(account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/wallet/wallet.py">Wallet</a></code>

#### External

Types:

```python
from dinari_api_sdk.types.v2.accounts.wallet import WalletChainID, ExternalGetNonceResponse
```

Methods:

- <code title="post /api/v2/accounts/{account_id}/wallet/external">client.v2.accounts.wallet.external.<a href="./src/dinari_api_sdk/resources/v2/accounts/wallet/external.py">connect</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/wallet/external_connect_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/wallet/wallet.py">Wallet</a></code>
- <code title="get /api/v2/accounts/{account_id}/wallet/external/nonce">client.v2.accounts.wallet.external.<a href="./src/dinari_api_sdk/resources/v2/accounts/wallet/external.py">get_nonce</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/wallet/external_get_nonce_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/wallet/external_get_nonce_response.py">ExternalGetNonceResponse</a></code>

### Orders

Types:

```python
from dinari_api_sdk.types.v2.accounts import (
    BrokerageOrderStatus,
    Order,
    OrderSide,
    OrderTif,
    OrderType,
    OrderListResponse,
    OrderBatchCancelResponse,
    OrderGetFulfillmentsResponse,
)
```

Methods:

- <code title="get /api/v2/accounts/{account_id}/orders/{order_id}">client.v2.accounts.orders.<a href="./src/dinari_api_sdk/resources/v2/accounts/orders.py">retrieve</a>(order_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order.py">Order</a></code>
- <code title="get /api/v2/accounts/{account_id}/orders">client.v2.accounts.orders.<a href="./src/dinari_api_sdk/resources/v2/accounts/orders.py">list</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_list_response.py">OrderListResponse</a></code>
- <code title="post /api/v2/accounts/{account_id}/orders/cancel">client.v2.accounts.orders.<a href="./src/dinari_api_sdk/resources/v2/accounts/orders.py">batch_cancel</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_batch_cancel_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_batch_cancel_response.py">OrderBatchCancelResponse</a></code>
- <code title="post /api/v2/accounts/{account_id}/orders/{order_id}/cancel">client.v2.accounts.orders.<a href="./src/dinari_api_sdk/resources/v2/accounts/orders.py">cancel</a>(order_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order.py">Order</a></code>
- <code title="get /api/v2/accounts/{account_id}/orders/{order_id}/fulfillments">client.v2.accounts.orders.<a href="./src/dinari_api_sdk/resources/v2/accounts/orders.py">get_fulfillments</a>(order_id, \*, account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_get_fulfillments_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_get_fulfillments_response.py">OrderGetFulfillmentsResponse</a></code>

### OrderFulfillments

Types:

```python
from dinari_api_sdk.types.v2.accounts import Fulfillment, OrderFulfillmentQueryResponse
```

Methods:

- <code title="get /api/v2/accounts/{account_id}/order_fulfillments/{order_fulfillment_id}">client.v2.accounts.order_fulfillments.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_fulfillments.py">retrieve</a>(order_fulfillment_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/fulfillment.py">Fulfillment</a></code>
- <code title="get /api/v2/accounts/{account_id}/order_fulfillments">client.v2.accounts.order_fulfillments.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_fulfillments.py">query</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_fulfillment_query_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_fulfillment_query_response.py">OrderFulfillmentQueryResponse</a></code>

### OrderRequests

Types:

```python
from dinari_api_sdk.types.v2.accounts import (
    CreateLimitBuyOrderInput,
    CreateLimitSellOrderInput,
    CreateMarketBuyOrderInput,
    CreateMarketSellOrderInput,
    OrderRequest,
    OrderRequestStatus,
    OrderRequestListResponse,
    OrderRequestGetFeeQuoteResponse,
)
```

Methods:

- <code title="get /api/v2/accounts/{account_id}/order_requests/{order_request_id}">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">retrieve</a>(order_request_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request.py">OrderRequest</a></code>
- <code title="get /api/v2/accounts/{account_id}/order_requests">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">list</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_request_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request_list_response.py">OrderRequestListResponse</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/limit_buy">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">create_limit_buy</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_request_create_limit_buy_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request.py">OrderRequest</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/limit_sell">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">create_limit_sell</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_request_create_limit_sell_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request.py">OrderRequest</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/market_buy">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">create_market_buy</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_request_create_market_buy_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request.py">OrderRequest</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/market_sell">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">create_market_sell</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_request_create_market_sell_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request.py">OrderRequest</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/fee_quote">client.v2.accounts.order_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/order_requests.py">get_fee_quote</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_request_get_fee_quote_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_request_get_fee_quote_response.py">OrderRequestGetFeeQuoteResponse</a></code>

#### Eip155

Types:

```python
from dinari_api_sdk.types.v2.accounts.order_requests import (
    Eip155OrderRequestPermitTransaction,
    Eip155CreatePermitResponse,
    Eip155CreatePermitTransactionResponse,
    Eip155SubmitResponse,
)
```

Methods:

- <code title="post /api/v2/accounts/{account_id}/order_requests/eip155/permit">client.v2.accounts.order_requests.eip155.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/eip155.py">create_permit</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_requests/eip155_create_permit_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_requests/eip155_create_permit_response.py">Eip155CreatePermitResponse</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/eip155/permit_transaction">client.v2.accounts.order_requests.eip155.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/eip155.py">create_permit_transaction</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_requests/eip155_create_permit_transaction_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_requests/eip155_create_permit_transaction_response.py">Eip155CreatePermitTransactionResponse</a></code>
- <code title="post /api/v2/accounts/{account_id}/order_requests/eip155">client.v2.accounts.order_requests.eip155.<a href="./src/dinari_api_sdk/resources/v2/accounts/order_requests/eip155.py">submit</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/order_requests/eip155_submit_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/order_requests/eip155_submit_response.py">Eip155SubmitResponse</a></code>

### WithdrawalRequests

Types:

```python
from dinari_api_sdk.types.v2.accounts import WithdrawalRequest, WithdrawalRequestListResponse
```

Methods:

- <code title="post /api/v2/accounts/{account_id}/withdrawal_requests">client.v2.accounts.withdrawal_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/withdrawal_requests.py">create</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/withdrawal_request_create_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/withdrawal_request.py">WithdrawalRequest</a></code>
- <code title="get /api/v2/accounts/{account_id}/withdrawal_requests/{withdrawal_request_id}">client.v2.accounts.withdrawal_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/withdrawal_requests.py">retrieve</a>(withdrawal_request_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/withdrawal_request.py">WithdrawalRequest</a></code>
- <code title="get /api/v2/accounts/{account_id}/withdrawal_requests">client.v2.accounts.withdrawal_requests.<a href="./src/dinari_api_sdk/resources/v2/accounts/withdrawal_requests.py">list</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/withdrawal_request_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/withdrawal_request_list_response.py">WithdrawalRequestListResponse</a></code>

### Withdrawals

Types:

```python
from dinari_api_sdk.types.v2.accounts import Withdrawal, WithdrawalListResponse
```

Methods:

- <code title="get /api/v2/accounts/{account_id}/withdrawals/{withdrawal_id}">client.v2.accounts.withdrawals.<a href="./src/dinari_api_sdk/resources/v2/accounts/withdrawals.py">retrieve</a>(withdrawal_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/withdrawal.py">Withdrawal</a></code>
- <code title="get /api/v2/accounts/{account_id}/withdrawals">client.v2.accounts.withdrawals.<a href="./src/dinari_api_sdk/resources/v2/accounts/withdrawals.py">list</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/withdrawal_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/withdrawal_list_response.py">WithdrawalListResponse</a></code>

### TokenTransfers

Types:

```python
from dinari_api_sdk.types.v2.accounts import TokenTransfer, TokenTransferListResponse
```

Methods:

- <code title="post /api/v2/accounts/{account_id}/token_transfers">client.v2.accounts.token_transfers.<a href="./src/dinari_api_sdk/resources/v2/accounts/token_transfers.py">create</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/token_transfer_create_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/token_transfer.py">TokenTransfer</a></code>
- <code title="get /api/v2/accounts/{account_id}/token_transfers/{transfer_id}">client.v2.accounts.token_transfers.<a href="./src/dinari_api_sdk/resources/v2/accounts/token_transfers.py">retrieve</a>(transfer_id, \*, account_id) -> <a href="./src/dinari_api_sdk/types/v2/accounts/token_transfer.py">TokenTransfer</a></code>
- <code title="get /api/v2/accounts/{account_id}/token_transfers">client.v2.accounts.token_transfers.<a href="./src/dinari_api_sdk/resources/v2/accounts/token_transfers.py">list</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/token_transfer_list_params.py">params</a>) -> <a href="./src/dinari_api_sdk/types/v2/accounts/token_transfer_list_response.py">TokenTransferListResponse</a></code>

### Activities

Methods:

- <code title="get /api/v2/accounts/{account_id}/activities/brokerage">client.v2.accounts.activities.<a href="./src/dinari_api_sdk/resources/v2/accounts/activities.py">retrieve_brokerage</a>(account_id, \*\*<a href="src/dinari_api_sdk/types/v2/accounts/activity_retrieve_brokerage_params.py">params</a>) -> None</code>
