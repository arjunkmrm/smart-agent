## Unmatched, unsettled, alleged reporting
21/05/2021

### Internal and Bridge instructions

We report matching and settlement results for internal and Bridge instructions including reasons why the instructions remain unmatched or unsettled.

We provide:

* the reason(s) why instructions have not matched, using ISO 15022-compliant reason codes, as illustrated below
* information that differs between the unmatched instruction and the best matching candidate
* the Euroclear Bank reference of the best matching candidate, which is an instruction from a counterparty that has a single (or, in certain circumstances, two, such as dual) unmatched field(s) that prevent it from matching with your instruction

| If | Then |
| --- | --- |
| more than one possible matching candidate is identified | the best matching candidate and the associated reason is determined according to the unmatched field(s), using the order indicated below |
| no matching candidate is identified | the general reason code CMIS (Counterparty instruction is missing or differs) is reported to you |

Every day, at the end of the real-time settlement process, we clean unmatched instructions. For more information, see the [Recycling of instructions](https://my.euroclear.com/eb/en/reference/services/settlement/what-is-the-lifecycle-of-transactions.html#par_textimage_11) section.

You can see the reason codes that might appear in your reports below:

| Single unmatched fields | Reason code | Dual unmatched fields | Reason |
| --- | --- | --- | --- |
| Quantity of securities | DQUA | Settlement amount and settlement date | DMON |
| Settlement amount | DMON | Settlement amount and settlement amount currency | DMON |
| Settlement date | DDAT | Settlement amount and trade price | DMON |
| Settlement amount currency | NCRR | Settlement date and trade date | DDAT |
| Trade date | DTRD |  |  |
| Trade price | DDEA |  |  |
| Place of settlement | DEPT |  |  |
| Disagreement common reference  | IIND  |  |  |
| Incorrect buyer or seller  | IIEXE  |  |  |

### External instructions

The reasons why external instructions remain unmatched or unsettled are defined by the Specialised Depositary or CSD where matching and settlement takes place.

We report alleged trades to you via EasyWay, EUCLID and SWIFT:  

* if and when made available by the Specialised Depositary
* if the counterparty has supplied your Euroclear account number

Pending allegements will be removed from your reports upon either:  

* receipt of positive matching and/or settlement feedback from the local market
* cancellation by the counterparty.

Old allegements will be removed from your reporting based on local market recycling rules.  