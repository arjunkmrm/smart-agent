## What is the lifecycle of transactions?

There are possibly up to six steps for a transaction to settle.

### 1. Input
You can input the instruction types listed below:

| Instruction type | Type of payment | EUCLID proprietary messages| ISO 15022 compliant messages |
|------------------|-----------------------------|------------------------------|-----------------|
| Internal         | Free of payment / against payment internal receipt instruction | 01F/P | 540/541 |
|                  | Free of payment / against payment internal delivery instruction | 02F/P | 542/543 |
|                  | Free of payment delivery instruction without matching | 02A | 542/DLWM |
| Bridge           | Free of payment / against payment Bridge receipt instruction | 03FC/PC | 540/541 |
|                  | Free of payment / against payment Bridge delivery instruction | 07FC/PC | 542/543 |
| External         | Free of payment / against payment external receipt instruction - CBF | 03FK/PK | 540/541 |
|                  | Free of payment / against payment external receipt instruction | 03F/P | 540/541 |
|                  | Free of payment / against payment external delivery instruction - CBF | 07FK/PK | 542/543 |
|                  | Free of payment / against payment external delivery instruction | 07F/P | 542/543 |
| FSA reporting    | Free of payment / against payment internal receipt instruction | 01F/P | 540/541 |
|                  | Free of payment / against payment internal delivery instruction | 02F/P | 542/543 |

### 2. Validation

We validate internal and Bridge instructions. They undergo validation to check whether they can be further processed:

* syntactical validation - validation of field formats
* contextual validation - validation of field content and relationships between fields

External instructions are subject to validation rules that vary depending on the local market, security type, etc.

When an instruction is invalid, we do not process it further and we report this to you. To settle the transaction, you must send a new instruction.  

### 3. Matching – general information

Only valid instructions are included in the matching process.

Matching means that the details of your instruction are compared to those of your counterparty. The purpose is to ensure that :  

* the terms of the transaction are identical in both instructions
* any differences are identified and reported as soon as possible

Not all fields require matching. The matching fields depend on the instruction type and, for external instructions, on local market requirements.

In general, matching is a settlement condition and thus a mandatory step before a transaction can be submitted for settlement. Matching in Euroclear Bank takes place according to our rules.  

#### Matching in Euroclear Bank

Our matching process runs throughout the day and includes instructions that have been received and validated. The matching process compares the terms for the following instructions types:  

| **Instruction type** | **Matching**  |
| --- | --- |
| Internal delivery instructions | Must always match with an internal receipt instruction, except for free of payment internal delivery instructions without matching |
| Bridge receipt and delivery instructions | Must match with a corresponding instruction from CBL |
| External receipt instructions | We attempt to match an instruction in the local market until it is either matched or cancelled. |  |

Instructions for which there is no matching in the local market must match in Euroclear Bank with the notification from the local market that the securities have been received (except for external deliveries without matching).  

For some markets, free of payment external receipt instructions do not require an instruction.

Updated matching results can be received throughout the day via:  

* EUCLID: R70 report
* SWIFT: MT 548

Internal matching results are immediately available, whereas local and Bridge matching and settlement results can be retrieved as soon as they are available in Euroclear Bank.  

#### Mandatory matching fields

For most instructions, the following elements must match:

* participant code/account number
* counterparty code/account number
* security code
* quantity of securities
* trade date
* settlement date
* cash countervalue, if against payment
* cash currency, if against payment

Any internal or Bridge settlement instruction that does not contain one of the mandatory matching fields will be rejected by our system. For more detailed information on rejection messages, please refer to the [EUCLID and SWIFT data reference manual](https://my.euroclear.com/apps/en/drm.html).  

#### Matching for internal and Bridge instructions

We compare the above settlement details of the two instructions and perform [optional matching](https://my.euroclear.com/eb/en/reference/services/settlement/what-is-the-lifecycle-of-transactions.html#par_textimage_914818927) on the below fields:

* common reference
* client of delivering/receiving agent (Buyer/Seller) only when BIC format is used

 Instructions remain unmatched if there is any difference greater than the acceptable tolerances:

* cash amount - for against payment internal and Bridge instructions with a cash amount that is:
	+ lower than or equal to EUR 100,000, the matching tolerance is EUR 2
	+ higher than EUR 100,000, the matching tolerance is EUR 25

The cash countervalue indicated by the seller will be used for execution.  

* trade price - if indicated by both parties, the trade price must match up to and including the fifth decimal.

#### How does optional matching work?

***Common reference***  
If one party uses an optional matching field, the other party must input the same value in the field or leave the field blank.

| **Party A** | **Party B** | **Will the instructions match?** |
| --- | --- | --- |
| Enters a value | Enters the same value | Yes |
| Enters a value | Leaves the field blank | Yes |
| Leaves the field blank | Leaves the field blank | Yes |
| Enters a value | Enters a different value | No |

#### Client of the receiving/delivering agent (buyer/seller)

A matching attempt will only occur when both settlement parties complete the field with a BIC11 format.

**Note**: If you input a BIC8 in the BUYR/SELL field for your Bridge instruction, we will add a branch code ‘XXX’ making it a BIC11 and a matching criterion.  

Optional matching on this field for Bridge instructions:  

| Your instruction | Counterparty instruction | Outcome |
| --- | --- | --- |
| BIC-11 format | BIC-11 format | Matching attempt is performed |
| BIC-8 format | BIC-11 format | Branch code ‘XXX’ added to BIC8 code, and matching attempt is performed |
| BIC -11 format | Other format | No matching attempt is performed |
| Other format | BIC-11 format | No matching attempt is performed |
| Other format | Other format | No matching attempt is performed |


#### Matching in the local market: three steps

1. We send external instructions to the Depositary or CSD for matching with the instruction of the counterparty in the domestic market.
2. The Depositary or CSD informs us of the domestic matching results.  
3. We report the matching results to you.

An instruction sent for matching in the local market is recycled until either:  
* matching is successful
* the instruction is cancelled by you or us
* the instruction is cancelled in the domestic CSD

Matching of instructions can be binding, so instructions can no longer be cancelled or can only be cancelled upon request by both parties. In this case, the instruction that is matched locally is automatically submitted for settlement in the local market.

Matching elements, tolerances and priorities vary according to domestic market rules. For more information, consult the specific market information in the Knowledge base app.  

### 4. Positioning of instructions

We perform a transaction-by-transaction positioning, taking into account your priorities and options, to verify whether either:  
* the securities are available to execute the delivery instruction
* cash/credit/collateral is available to execute the receipt instruction.

This verification is done between matching and settlement, unless positioning takes place in a market where matching is binding. In this case, positioning takes place before instructions are sent to the local market for matching.

For Bridge and external transactions:  
* positioning always takes place before a message committing us to the transaction is sent to CBL or the relevant Depositary
* to ensure that cash/securities are not used twice for different instructions, they are immediately provisionally debited to your account.

#### Securities positioning

| **Instruction type** | **Securities positioning** |
| --- | --- |
| Internal delivery instructions | The securities position is verified:* if positioning is successful, the instructions are further processed in the same processing cycle if the counterparty has enough cash/credit in its account to execute an against payment delivery instruction
* if successful, the transaction settles and reaches end of life
 |
| Bridge delivery instructions | The securities position is verified. If positioning is successful:* securities are provisionally debited
* for against payment instructions, cash is credited when CBL accept the delivery
 |
| External delivery instructions | The securities position is verified. If positioning is successful:* securities are provisionally debited in the same processing cycle for settlement in our Depositary or CSD
* the securities position in our Depositary is verified, and if it does not have enough securities, a realignment of securities (transhipment) is required between our Depositary and CBL's Depositary to allow settlement. The positions in domestic securities held by us and CBL are frequently realigned (as a result of Bridge settlement) in accordance with the total amount recorded in our books.
 |


### Cash positioning

| **Instruction type** | **Cash positioning** |
| --- | --- |
| Against payment internal receipt instructions | The cash available in your Cash Account is verified.
* Internal receipt instructions are positioned for cash in the processing cycle showing receipt of the relevant securities.
* If positioning is successful, cash is debited and securities are credited to the relevant account.
* If successful, the transaction settles and reaches end of life.
 |
| Against payment external receipt instructions | The available cash position is verified before the instruction is sent to our Depositary or CSD.
* If positioning is successful, cash is provisionally debited.
* Once the receipt has been confirmed, the provisional cash amount debited is confirmed.

The following criteria are considered during the positioning check:
* our cash credit position in the local market:
* your cash position (if you have enough available cash/credit)
* your collateral position (if you have enough available collateral)
 |
| Against payment Bridge receipt instructions | * **If there is sufficient cash/credit in your account**, we check if we can accept the receipt within the joint Bridge risk management principles
	+ **If we can accept the receipt**, we:
		- debit the cash amount from your account and credit your account with the securities
	+ **If we can not accept the receipt,** we
		- position the cash on your account until the next scheduled file exchange with CBL:
			* **if CBL confirms your transaction has settled**, we will credit your account with the securities
			* **if CBL confirms your transaction has not settled**, we will remove the cash positioning
* **If there is not sufficient cash/credit in your account**:
	+ your transaction will not settle
	+ CBL needs to send a new proposal for settlement

### Unsuccessful positioning

If securities or cash positioning in Euroclear Bank is unsuccessful, it is re-attempted in the next positioning attempt (recycling) until the instruction has either been:

* successfully positioned
* cancelled by you or us

For external against payment receipt instructions, if cash positioning is unsuccessful, we do not send the instruction to the local market for settlement.

For Bridge instructions, if securities have been proposed by CBL but you do not have enough cash available, we send a negative settlement feedback to CBL. 

### Reversal of provisional debits for unsettled instructions on T2S markets

If your external against payment instructions are positioned, but remain unsettled at the end of the T2S against payment RTS process (DVP cut-off), we reverse the provisional debit of securities (for delivery instructions) or cash (for receipt instructions). In this way, we optimise use of cash and securities by ensuring they can be used for other transactions.

This is done in two steps at predefined times

1. we put the unsettled instructions ‘on hold’ on the T2S platform.
2. we reverse the related provisional debits in our system until the start of the following T2S business day.

At the start of the following T2S settlement process, on the following T2S business day:

1. we position the instructions again
2. if sufficient cash (receipt instructions) or securities (delivery instructions) are available, we release the instructions (ie. we remove the hold) for settlement on the T2S platform


This functionality is only available for T2S markets. For more details, consult the online market guides:

* [Germany](https://my.euroclear.com/eb/en/reference/markets/germany/settlement-process-.html)
* [France](https://my.euroclear.com/eb/en/reference/markets/france/settlement-process1.html)
* [Belgium](https://my.euroclear.com/eb/en/reference/markets/belgium/settlement-process1.html)
* [The Netherlands](https://my.euroclear.com/eb/en/reference/markets/the-netherlands/settlement-process1.html)


### Settlement

Once an internal or Bridge instruction has been successfully matched and positioned, and the cash is confirmed, the instruction is executed and considered as settled. For Bridge instructions, we need to receive the feedback from CBL to confirm settlement.

External transactions settle in the domestic market; we need to receive settlement confirmation to report.  


### 5. Recycling of instructions

#### Internal and Bridge instructions

##### Unmatched instructions
Internal and Bridge instructions that remain unmatched after the batch process dated S are recycled in the automatic real-time process. They continue to be recycled until they are cancelled by you or by Euroclear Bank.

##### Cleaning of unmatched instructions

Every day, at the end of the real-time process, we automatically cancel all internal and Bridge instructions with:


* an internal status of unmatched and input date of more than one month in the past
* an internal status of unmatched and contractual settlement date of more than one month in the past


**Note**: If you do not want us to cancel instructions automatically, you can subscribe to opt out of the monthly cleaning. To do so, contact our Client Service Administration team.

***Reporting***

The instructions cancelled by this daily cleaning are reported with the narrative ‘MATCHING UNSUCCESSFUL – END OF RECYCLING’ in the:

* cancellation narrative field of the R21, Securities Transaction Instructions at End of Life report and the R76, Cancelled Instructions report
* reason narrative field (:70D::REAS) of the MT 548, Settlement Status and Processing Advice

For more information, refer to the [EUCLID and SWIFT data reference manual](https://my.euroclear.com/eb/en/reference/connectivity-basics/euclid-and-swift-data-reference-manual.html).


***Fees***

The standard cancellation fee applies.

For more details, see our [general fees brochure](https://my.euroclear.com/content/dam/euroclear/Operational/EB/Tariff%20information/MA0007-General%20fees%20brochure.pdf) (pdf-1002KB).

##### Matched instructions

Internal and Bridge instructions that remain unsettled after the batch process dated S are recycled in the automatic real-time process, until they are settled or cancelled by you.

* If they do not contain the real-time indicator, they are re-submitted for settlement in the following batch process dated S+1.
* If both matched instructions contain the real-time indicator, they are recycled in the optional real-time process.

For more information on the automatic and optional real-time process and the real-time indicator, consult the Internal settlement and Bridge settlement sections.

##### External instructions

For information on the recycling of external instructions, consult the specific market information.  

##### Automatic recycling of instructions: ‘new issues recycling’

You are automatically subscribed to new issues recycling. When you send an instruction for a security that we have not yet been accepted, your instruction will be recycled while we investigate the eligibility of the security.

The investigation continues until whichever is later of the following:  

* the contractual settlement date of the instruction
* four Business Days following the input of the instruction

If the investigation would take longer, your instruction would be cancelled. The investigation will continue despite cancellation of the instruction.

During the investigation period, the instruction will retain the status LIMB (EUCLID proprietary format) or: 25D::IPRC//PACK (ISO 15022-compliant format) until either:

* we accept the security as the eligibility criteria have been met: the instruction will then be recycled in the standard validation process
* we reject the security because the eligibility criteria have not been met, and cancel the instruction
* you cancel the instruction

Note: You can opt out of this automatic recycling service, by sending us an MT 599 message.

### 6. End of life: settlement or cancellation

An instruction reaches end of life when:

* **successfully settled** in Euroclear Bank, reported to Euroclear Bank as having settled in CBL, or confirmed in the local market, and the corresponding securities and cash movements have been reflected in your Securities Clearance and Cash Accounts
* it has been **cancelled** by you or us

#### Cancellation of internal and Bridge instructions

* Unmatched instructions are subject to unilateral cancellation.
* Matched instructions are subject to bilateral cancellation.

These cancellation rules also apply to primary market distributions.

#### Cancellation of external instructions

We follow the cancellation rules of the local market.

When your instruction is unmatched, we will cancel the instruction upon your request.

We will only execute the cancellation of a matched instruction when both you and your counterparty have requested the cancellation. If only one party sends us a request to cancel a matched instruction, the cancellation request will remain pending and the instruction will be:

* eligible for full or partial settlement
* subject to cash penalties and mandatory buy-ins as from the time the CSDR settlement discipline regime enters into force

Once you have submitted a cancellation request, it cannot be withdrawn and remains pending until your instruction is either settled or bilaterally cancelled.

We report to you the status of your Bridge cancellation request after we exchange communication with CBL as per the standard Bridge processing rules.

#### Bilateral cancellation request and reporting

Once you send a valid cancellation request, we will check if your instruction is unmatched or matched:

* if your instruction is unmatched, we will execute and report your cancellation request
* if your instruction is matched, we will check if your counterparty has requested the cancellation:
	+ if your counterparty has not requested a cancellation, we will report to you that your cancellation request is pending your counterparty cancellation request and we will report to your counterparty that you have requested a cancellation and that his cancellation request is missing
	+ if/once we have received a valid cancellation request from your counterparty, we will execute and report to both parties the cancellation request as executed