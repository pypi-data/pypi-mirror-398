---
title: "Python SDK"
description: "Documentation for the Kelviq Python SDK"
icon: 'python'
---

## Overview

The Kelviq Python SDK provides a convenient way to interact with the Kelviq REST APIs from your Python application. The SDK supports both synchronous and asynchronous operations.


## Installation

To install the Kelviq SDK in your environment, run the following command:

```shell
pip install kelviq-sdk
```

## Prerequisites

Before you can initialize the client and use the SDK methods, you need a Server API Key.

You can obtain this key from the Kelviq application:

    1. Navigate to Settings.
    2. Go to the [Developers](https://app.kelviq.com/settings/developers) section.
    3. Copy the Server API Key.

Once copied, add this key to your environment variables or directly in your code (though environment variables are recommended for security).


```python
# Example of setting it in your code (ensure you handle this securely)
ACCESS_TOKEN = "__YOUR_API_KEY__"
```

## Configuring the Client

The SDK supports both synchronous and asynchronous clients. The primary difference lies in how you create the client instance. Once created, both client types can invoke the same methods to communicate with the Kelviq application.


#### How to Create a Synchronous Client

Use the synchronous client for traditional, blocking I/O operations.

```python
from kelviq_sdk import Kelviq

client = Kelviq.create_sync_client(access_token=ACCESS_TOKEN)
```

#### How to Create an Asynchronous Client
Use the asynchronous client for non-blocking I/O operations, suitable for applications using `asyncio`.


```python
from kelviq_sdk import Kelviq

async_client = Kelviq.create_async_client(access_token=ACCESS_TOKEN)
```



## Supported Functionalities

The SDK currently supports the following operations:

    1. [Customers](/backend-integration/python-sdk#customers)

    2. [Checkout](/backend-integration/python-sdk#checkout-client-checkout)

    3. [Entitlements](/backend-integration/python-sdk#entitlements-client-entitlements)

    4. [Reporting](/backend-integration/python-sdk#reporting-client-reporting)

    5. [Subscriptions](/backend-integration/python-sdk#subscriptions)


Further details on each method, including parameters and return values, should be added under each functionality.

---

## Customers

The `customers` module allows you to manage customer records within Kelviq. You can access these operations via the `customers` attribute on an initialized `Kelviq` client instance.

All methods are available in both synchronous and asynchronous versions, depending on how the `Kelviq` client was instantiated.

---

### Creates a new customer


**Synchronous**:

    ```python
    new_customer = client.customers.create(
        customerId="unique-customer-id-123",
        email="new.customer@example.com",
        name="John Doe",
        metadata={"source": "sdk_import", "priority": "high"}
    )
    print(f"Customer Created: ID = {new_customer.id}, Customer Client ID = {new_customer.customerId}")
    ```

**Asynchronous**:
    ```python
    new_customer = await async_client.customers.create(
        customerId="unique-customer-id-456",
        email="another.new.customer@example.com",
        name="Jane Roe"
    )
    print(f"Customer Created (Async): ID = {new_customer.id}, Customer Client ID = {new_customer.customerId}")
    ```

<Accordion title="Response">
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // Server-generated UUID
  "customerId": "unique-customer-id-123",
  "name": "John Doe",
  "email": "new.customer@example.com",
  "details": {}, // Or any server-added details
  "metadata": {
    "source": "sdk_import",
    "priority": "high"
  },
  "createdOn": "2025-06-04T06:03:30.195790Z",
  "modifiedOn": "2025-06-04T06:03:30.195831Z"
}
```
</Accordion>


**Required Parameters:**

* `customerId` (str): A unique identifier for the customer that you define. This ID will be used to reference the customer in subsequent API calls.

**Optional Parameters:**

* `email` (str): The email address of the customer. Must be a valid email format.
* `name` (str): The name of the customer.
* `metadata` (Dict[str, str]): A dictionary of custom key-value pairs to store additional information about the customer.


**Returns:**
An instance of `CustomerResponse` (Pydantic model), representing the newly created customer record. Key attributes include:

* `id` (str): The server-generated unique UUID for the customer record.
* `customerId` (str): The client-provided customer identifier.
* `name` (str): The customer's name.
* `email` (str): The customer's email.
* `details` ([Dict[str, Any]]): Any server-added details about the customer (typically read-only).
* `metadata` ([Dict[str, str]]): The metadata associated with the customer.
* `createdOn` (string) : ISO 8601 timestamp of when the customer was created.
* `modifiedOn` (string) : ISO 8601 timestamp of when the customer was last modified.

### Updates an existing customer

This operation performs a partial update (PATCH), so you only need to provide the fields you want to change.

**Synchronous**:

    ```python
        updated_customer = client.customers.update(
            customerId="unique-customer-id-123",
            name="Johnathan Doe",
            metadata={"source": "sdk_import", "priority": "very_high", "status": "active"}
        )
        print(f"Customer Updated: {updated_customer.name}")
    ```

**Asynchronous**:

    ```python
        updated_customer = await async_client.customers.update(
            customerId="unique-customer-id-456",
            email="jane.roe.updated@example.com"
        )
        print(f"Customer Updated (Async): {updated_customer.email}")
    ```

<Accordion title="Response">
```json
{
  "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef", // Server-generated UUID
  "customerId": "unique-customer-id-123",
  "name": "Johnathan Doe",
  "email": "new.customer@example.com",
  "details": {}, // Or any server-added details
  "metadata": {
    "source": "sdk_import",
    "priority": "high",
    "status": "active"
  },
  "createdOn": "2025-06-04T06:03:30.195790Z",
  "modifiedOn": "2025-06-04T06:03:30.195831Z"
}
```
</Accordion>


**Parameters:**

**Required Parameters:**

* `customerId` (str): A unique identifier for the customer that you define. This ID will be used to reference the customer in subsequent API calls.

**Optional Parameters:**

* `email` (str): The email address of the customer. Must be a valid email format.
* `name` (str): The name of the customer.
* `metadata` (Dict[str, str]): A dictionary of custom key-value pairs to store additional information about the customer.


**Returns:**
An instance of `CustomerResponse` (Pydantic model), representing the newly created customer record. Key attributes include:

* `id` (str): The server-generated unique UUID for the customer record.
* `customerId` (str): The client-provided customer identifier.
* `name` (str): The customer's name.
* `email` (str): The customer's email.
* `details` ([Dict[str, Any]]): Any server-added details about the customer (typically read-only).
* `metadata` ([Dict[str, Any]]): The metadata associated with the customer.
* `createdOn` (string) : ISO 8601 timestamp of when the customer was created.
* `modifiedOn` (string) : ISO 8601 timestamp of when the customer was last modified.

---

## Checkout

The checkout module provides functionalities for creating and managing checkout sessions. You can access these operations via the checkout attribute on an initialized Kelviq client instance.

`create_session(...)`
This operation creates a new checkout session for a customer, allowing them to proceed with a purchase or subscription.

**Synchronous**:

```python
response = client.checkout.create_session(
    planIdentifier="plan-pro-monthly",
    chargePeriod="MONTHLY",
    customerId="cust_789", // Recommended, otherwise it will create a new customer
    successUrl="https://kelviq.com/checkout/success"
)
print(f"Checkout Session URL: {response.checkoutUrl}")
```

**Asynchronous**:

```python
response = await async_client.checkout.create_session(
    planIdentifier="plan-pro-monthly",
    chargePeriod="MONTHLY",
    customerId="cust_789",
    successUrl="https://kelviq.com/checkout/success",
    offeringId="96d3a293-34ac-48a5-b73d-976b15781afd",
    pricingTableId="6db2717a-4e43-4ae1-a293-6c0a775f6264",
    ruleId="f2ebc23f-3f79-4cf4-b17e-fe8e30a42ab2",
    features=[{'identifier':"seats", 'quantity': 5}],
    ipAddress="103.154.35.20",
)
print(f"Checkout Session URL: {response.checkoutUrl}")

```


<Accordion title="Response">

  ```json
   {
        "checkoutUrl": "https://checkout.stripe.com/c/pay/cs_test_b1sNi7D6u9iMCUFV1UZi9ZaiXKdOOmr3DCUW6XdCZIr5Id1F7#fid2cGd2ZndsdXsdjahsdkhsdhc%2FY2RpdmApJ3Zxd2x1YERmZmpwa3EnPydkZmZxWjRLZjV3X0BAckFBYGJKSEInKSdkdWxOYHwnPyd1blpxYHZxWjA0Tj1DSGdWRmwxYkdiMFxGQ29zf2BdTldOTGQzUlNqfWd9U1ZkanNHMlVnczxidEg0fFFqYVJNYzw8XEh2YVA8dkQ1bmA9NW5sS1c2PHE8hH89Q11Uf1E2NTVgY0M1Q0ZmYycpJ2N3amhWYHdzYHcnP3F3cGApJ2lkfGpwc",
        "checkoutSessionId": "cs_test_b1sNi7D6u9iMCUFV1UZi9ZwerfaiXKdOOmr3DCUW6XdCZIr5Id1F7G",
    }
  ```
</Accordion>


**Required Parameters:**

* `planIdentifier` (str): The identifier of the specific plan the customer is checking out with. planIdentifier is mandatory.

* `successUrl` (str): The URL to which the user will be redirected after a successful checkout.

* `chargePeriod` (str): Required. The billing cycle for the subscription. Must be one of:

        * `"ONE_TIME"`

        * `"MONTHLY"`

        * `"YEARLY"`

        * `"WEEKLY"`

        * `"DAILY"`

        * `"THREE_MONTHS"`

        * `"SIX_MONTHS"`



**Optional Parameters:**

    * `offeringId` (str): The ID (uuid) of the offering the customer is checking out with.

    * `pricingTableId` (str): Required. The id (uuid) of the pricingTable being used for this checkout. (Considered only if `offeringId` is not provided)

    * `ruleId` (str): Required. The id (uuid) of the pricing rule being applied. (Considered only if `offeringId` is not provided)

    * `customerId` (str): Required. The ID of the customer initiating the checkout. (If not provided, a new customer will be created)

    * `features` (List[Dict[str, Union[str, int]]]): **Required**. A list of dictionaries, where each dictionary represents a feature and its desired quantity. Each dictionary **must** have two keys:
        * `"identifier"` (str): The unique identifier for the feature.
        * `"quantity"` (int): The desired quantity for this feature.
            * Example: `[{"identifier": "seats", "quantity": 10}, {"identifier": "api-calls-tier1", "quantity": 5000}]`

    * `ipAddress` (str): The IP Address of the customer, used for location based pricing.


**Returns**:

An instance of CreateCheckoutSessionResponse (Pydantic model), which includes:

    * `checkoutSessionId` (str): The unique ID for the created checkout session.

    * `checkoutUrl` (str): The URL that the customer should be redirected to in order to complete the payment and activate the subscription/purchase.

---

## Entitlements

The entitlements module allows you to check and retrieve customer entitlements for various features. These operations target a specific edge API endpoint (https://edge.api.kelviq.com by default) and use the GET HTTP method with query parameters.


### Checks if a specific customer has access to a particular feature.
This method directly returns a boolean indicating access status.

**Synchronous**:

```python
has_feature_access = client.entitlements.has_access(
    customerId="cust_123",
    featureId="premium-reporting"
)
```

**Asynchronous**:

```python
has_feature_access = await async_client.entitlements.has_access(
    customerId="cust_456",
    featureId="advanced-analytics"
)
```

<Accordion title="Response">

  ```shell
   True
  ```
</Accordion>

**Required Parameters**:

    * `customerId` (str): The unique identifier for the customer.

    * `featureId` (str): The unique identifier for the feature whose access is being checked.

**Returns**:

    * `bool`: True if the customer has access to the specified feature (considering feature type, limits, etc.), False otherwise or if the feature is not found in their entitlements.



### Retrieves the detailed entitlement information for a specific feature for a given customer.

**Synchronous**:

```python
entitlement_response = client.entitlements.get_entitlement(
    customerId="cust_123",
    featureId="premium-reporting"
)
```


**Asynchronous**:

```python
entitlement_response = await async_client.entitlements.get_entitlement(
    customerId="cust_456",
    featureId="advanced-analytics"
)
```

<Accordion title="Response">

  ```json
   {
        "customerId": "cust_456",
        "entitlements": [
            {
                "featureId": "advanced-analytics",
                "featureType": "METER",
                "hasAccess": true,
                "resetAt": "2025-05-22 08:27:45",
                "hardLimit": false,
                "usageLimit": 3,
                "currentUsage": 0,
                "remaining": 3
            }
        ]
   }
  ```
</Accordion>

**Required Parameters**:

    * `customerId` (str): The unique identifier for the customer.

    * `featureId` (str): The unique identifier for the feature whose access is being checked.

**Returns**:

An instance of CheckEntitlementsResponse (Pydantic model). When querying for a specific featureId, the entitlements list within this response is typically expected to contain a single EntitlementDetail object corresponding to the requested feature if found. The structure includes:

    * `customerId` (str): The customer's ID.

    * `entitlements` (List[EntitlementDetail]): A list containing the details for the requested feature. Each EntitlementDetail has fields like:

        * `featureId`: str

        * `hasAccess`: bool

        * `featureType`: str

        * `resetAt`: str

        * `hardLimit`: Optional[bool]

        * `usageLimit`: Optional[int]

        * `currentUsage`: Optional[int]

        * `remaining`: Optional[int]


### Retrieves all entitlements for a given customer.

**Synchronous**:

```python
all_entitlements_response = client.entitlements.get_all_entitlements(
    customerId="cust_123"
)
```

**Asynchronous**:

```python
all_entitlements_response = await async_client.entitlements.get_all_entitlements(
    customerId="cust_456"
)
```

<Accordion title="Response">


  ```json
   {
        "customerId": "cust_456",
        "entitlements": [
            {
                "featureId": "advanced-analytics",
                "featureType": "METER",
                "hasAccess": true,
                "resetAt": "2025-05-22 08:27:45",
                "hardLimit": false,
                "usageLimit": 3,
                "currentUsage": 0,
                "remaining": 3
            }
        ]
    }
  ```
</Accordion>

**Required Parameters**:

    * `customerId` (str): The unique identifier for the customer.


**Returns**:


    * `customerId` (str): The customer's ID.

    * `entitlements` (List[EntitlementDetail]): A list containing the details for the requested feature. Each EntitlementDetail has fields like:

        * `featureId`: str

        * `hasAccess`: bool

        * `featureType`: str

        * `resetAt`: str

        * `hardLimit`: Optional[bool]

        * `usageLimit`: Optional[int]

        * `currentUsage`: Optional[int]

        * `remaining`: Optional[int]

---

## Reporting

### Reporting pre-aggregated usages for customer

This endpoint is used for reporting the pre-aggregated feature usage from your application (client-level) to the Kelviq application. It allows you to update the usage count for a specific feature associated with a customer.


**Synchronous**:

```python
# Assuming 'client' is your synchronous Kelviq client
response = client.reporting.report_usage(
    value=150,
    customerId="customer_001",
    featureId="seats",
    behaviour="SET" # Or 'DELTA'
)
```

**Asynchronous**:

```python
# Assuming 'async_client' is your asynchronous Kelviq client
response = await async_client.reporting.report_usage(
    value=75,
    customerId="customer_001",
    featureId="seats",
    behaviour="DELTA"
)
```

<Accordion title="Response">


  ```json
   {
        "value": 150,
        "customerId": "customer_001",
        "featureId": "seats",
        "behaviour": "SET",
        "orgId": "1",
        "eventName": "aggregated.usage",
        "idempotencyKey": "597ee95063c744ed9bcc9b1cf5676a8a",
        "timestamp": "2025-05-22 08:27:45.430732"
    }
  ```
</Accordion>


**Required Parameters**:

    * `value` (int): The usage value being reported.

    * `customerId` (str): The unique identifier for the customer associated with this usage.

    * `featureId` (str): The unique identifier for the feature for which usage is being reported.

    * `behaviour` parameter dictates how the usage is updated:

        * `SET`: This will replace the current usage value for the feature with the new `value` provided.

        * `DELTA`: This will increment the existing usage value for the feature by the amount specified in the `value` parameter


**Returns**:

An instance of ReportUsageResponse (Pydantic model), which includes:

    * `value` (int): The usage value that was recorded.

    * `customerId` (str): The customer ID associated with the usage.

    * `featureId` (str): The feature Identifier for which usage was recorded.

    * `behaviour` (str): The behaviour type ("SET" or "DELTA") that was processed.

    * `orgId` (str): The organization ID associated with this record, as determined by the server.

    * `eventName` (str): An internal event name generated by the server for this usage report (e.g., "aggregated.usage").

    * `idempotencyKey` (str): A unique idempotency key generated by the server for this specific usage report instance.

    * `timestamp` (str): The server-generated UTC timestamp (str format) indicating when the usage report was processed.


### Reporting raw events for customer

Raw events are primarily used for metered billing scenarios, particularly when a customer is subscribed to a plan with usage-based billing (often referred to as "pay as you go"). Each event reported can contribute to the billable usage for that customer.

**Synchronous**:

```python
import uuid

# Assuming 'client' is your synchronous Kelviq client
response = client.reporting.report_event(
    customerId="customer_002",
    eventName="api_invoked",
    idempotencyKey=uuid.uuid4().hex,
    timestamp="2025-05-22 07:53:55.747959",
    properties={"featureId": "api-usage", "value": 2}
)

```

**Asynchronous**:

```python
import uuid

# Assuming 'async_client' is your asynchronous Kelviq client
response = await async_client.reporting.report_event(
    customerId="customer_002",
    eventName="api_invoked",
    idempotencyKey=uuid.uuid4().hex,
    timestamp="2025-05-22 07:53:55.747959",
    properties={"featureId": "api-usage", "value": 2}
)
```

<Accordion title="Response">


  ```json
   {
        "customerId": "customer_002",
        "eventName": "api_invoked",
        "idempotencyKey": "45f05c737a0b44d482c6042816d5645d",
        "timestamp": "2025-05-22 07:53:55.747959",
        "properties": {
            "featureId": "api-usage",
            "value": 2
        },
        "orgId": "1"
    }
  ```
</Accordion>


**Required Parameters**:

    * `customerId` (str): The unique identifier for the customer who performed the event.

    * `eventName` (str): The name of the event (e.g., "user_login", "item_purchased", "feature_activated").

    * `idempotencyKey` (str): A unique client-generated key to ensure that the event is processed at most once, even if the request is retried. A UUID is a good choice.

    * `timestamp` (str): The UTC timestamp indicating when the event occurred. This must be a str formatted as "%Y-%m-%d %H:%M:%S.%f" (e.g., "2025-05-23 10:30:00.123456").

    * `properties` ([Dict[str, Any]], default: None): A dictionary of additional custom properties associated with the event. Values can be strs, numbers, booleans.

**Returns**:

An instance of ReportEventResponse (Pydantic model), which includes:

    * `customerId` (str): The customer ID associated with the event.

    * `eventName` (str): The name of the event that was recorded.

    * `idempotencyKey` (str): The idempotency key that was used for the request.

    * `timestamp` (str): The timestamp (str format) that was recorded for the event.

    * `properties` ([Dict[str, Any]]): The custom properties associated with the event, if provided and returned by the server.

    * `orgId` (str): The organization ID associated with this record, as determined by the server.

---

## Subscriptions

The subscriptions module allows you to manage customer subscriptions, including updates and cancellation. You can access these operations via the `subscriptions` attribute on an initialized Kelviq client instance.


### Updates an existing subscription to a new plan


**Synchronous**:

```python
# Assuming 'client' is your synchronous Kelviq client
try:
    response = client.subscriptions.update(
        subscriptionId="78058918-9746-4280-9b9b-1bd5115eec6e",
        planIdentifier="premium-plan",
        chargePeriod="MONTHLY",
    )
    print(response.subscriptionId)
except Exception as e:
    print(f"Error updating subscription: {e}")
```


**Asynchronous**:

```python
# Assuming 'async_client' is your asynchronous Kelviq client
try:
    response = await async_client.subscriptions.update(
        subscriptionId="78058918-9746-4280-9b9b-1bd5115eec6e",
        planIdentifier="new_plan_enterprise",
        chargePeriod="YEARLY",
        offeringId="offer_abc",
        pricingTableId="pw_def",
        ruleId="rule_ghi",
        ipAddress="103.154.35.20",
        features=[{'identifier': "seats", 'quantity': 10}]
    )
    print(response.subscriptionId)
except Exception as e:
    print(f"Error updating subscription: {e}")
```

<Accordion title="Response">

  ```json
   {
      "subscriptionId": "dffaf07e-4517-47db-ba3a-59a05aa2d465"
   }
  ```
</Accordion>

**Required Parameters**:

* `subscriptionId` (str): Required. The unique identifier of the subscription to be updated.
* `planIdentifier` (str): Required. The identifier of the new plan.
* `chargePeriod` (str): Required. The new charging period for the subscription. Must be one of:
    * `"ONE_TIME"`
    * `"MONTHLY"`
    * `"YEARLY"`
    * `"WEEKLY"`
    * `"DAILY"`
    * `"THREE_MONTHS"`
    * `"SIX_MONTHS"`

**Optional Parameters:**

* `offeringId` (str): Optional. The ID of the new offering, if applicable.
* `pricingTableId` (str): Optional. The ID of the new pricingTable, if applicable.
* `ruleId` (str): Optional. The ID of the new pricing rule, if applicable.
* `ipAddress` (str): The IP Address of the customer, used for location based pricing.
* `features` ([List[Dict[str, Any]]]): Optional. A list of dictionaries, where each dictionary represents a feature and its desired quantity to update for the subscription. Each dictionary **must** have two keys:
    * `"identifier"` (str): The unique identifier for the feature.
    * `"quantity"` (int): The desired quantity for this feature.
        * Example: `[{'identifier': 'seats', 'quantity': 10}, {'identifier': 'projects', 'quantity': 5}]`

**Returns**:

An instance of `UpdateSubscriptionResponse`, which includes:

* `subscriptionId` (str): UUID of the updated subscription.


### Cancel an active subscription for a customer.


**Synchronous**:

```python
# Assuming 'client' is your synchronous Kelviq client
try:
    response = client.subscriptions.cancel(
        subscriptionId="78058918-9746-4280-9b9b-1bd5115eec6e",
        cancellationType="CURRENT_PERIOD_ENDS" # Or "IMMEDIATE", "SPECIFIC_DATE"
        # cancellationDate="2025-12-31" # Required if cancellationType is "SPECIFIC_DATE"
    )
    print(response.message)
except Exception as e:
    print(f"Error cancelling subscription: {e}")
```


**Asynchronous**:

```python
# Assuming 'async_client' is your asynchronous Kelviq client
try:
    response = await async_client.subscriptions.cancel(
        subscriptionId="78058918-9746-4280-9b9b-1bd5115eec6e",
        cancellationType="IMMEDIATE"
    )
    print(response.message)
except Exception as e:
    print(f"Error cancelling subscription: {e}")
```

<Accordion title="Response">

  ```json
   {
      "message": "Subscription cancellation processed successfully."
   }
  ```
</Accordion>

**Required Parameters**:

* `subscriptionId` (str): The unique identifier of the subscription to be cancelled.

* `cancellationType` (str): The type of cancellation to perform. Must be one of:

    * `"IMMEDIATE"`: The subscription is cancelled immediately.
    * `"CURRENT_PERIOD_ENDS"`: The subscription will remain active until the end of the current billing period and then cancel.
    * `"SPECIFIC_DATE"`: The subscription will be cancelled on the specified `cancellationDate`.

* `cancellationDate` (str): The specific date for cancellation if `cancellationType` is `"SPECIFIC_DATE"`. Must be in `YYYY-MM-DD` format. This parameter is **required** if `cancellationType` is `"SPECIFIC_DATE"`.

**Returns**:

An instance of `CancelSubscriptionResponse`, which includes:

* `message` (str): A confirmation message indicating the result of the cancellation request.

