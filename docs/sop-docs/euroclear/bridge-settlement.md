## Bridge settlement

### What is a Bridge settlement transaction?

A transaction between a Euroclear Bank client and a Clearstream Banking Luxembourg (CBL) client. It settles on a book-entry basis, either:  
* against payment in any [currency accepted for Bridge settlement](https://my.euroclear.com/content/dam/euroclear/Operational/EB/Guides/OP0011-Eligible-currencies.pdf) provided that the security has the multi-currency treatment flag open
* free of payment

### Why is this called ‘Bridge’ settlement?
The word ‘Bridge’ is iconic in that the first ‘electronic Bridge’, in 1977, took over the role of a real bridge: Pont Adolphe in Luxembourg separated the area in the city where the depositaries of Euroclear and Clearstream (called ‘Cedel’ at the time) were located. 

Before the electronic Bridge existed, armoured trucks crossed Pont Adolphe back and forth every day between the depositaries, to physically deliver securities to the other ICSD ‘over the Bridge’.   

The Bridge was unique at the time in it offering ‘interoperability’ between the two ICSDs. The Bridge today is still unique due to its high efficiency.  

### What is the lifecycle of a Bridge settlement transaction?

[See the transaction lifecycle](https://my.euroclear.com/eb/en/reference/services/settlement/what-is-the-lifecycle-of-transactions.html)  

### When will I receive the final feedback on my instruction?

| Process | Applicable Currency | Time (Brussels time) | Instruction type |
|---------|---------------------|----------------------|------------------|
| **Overnight Batch Process** | | 23:30 on SD (EFB1) - Receipts<br>01:00 on SD (CFB1) - Deliveries | |
| **Real-Time Process** | | | |
| Mandatory against payment 1 | All except ARS, CAD, EUR, GBP, MXN, PEN, USD | 14:15 on SD - Receipts<br>14:25 on SD - Deliveries | |
| Mandatory against payment 2 | EUR, GBP | 15:55 on SD - Receipts<br>15:45 on SD - Deliveries | |
| Mandatory against payment 3 | ARS, CAD, MXN, PEN, USD | 17:35 on SD - Receipts<br>17:25 on SD - Deliveries | |
| Optional against payment | All currencies | 18:55 on SD - Receipts<br>19:05 on SD - Deliveries | |


SD = Settlement date

**Note** - the timing in the table above is indicative only based on the ultimate timing by which a transmission should be sent to or received from CBL

### What is near real-time matching on the Bridge?

Matching (ACE) files will be exchanged periodically every two minutes.   

### What is the Bridge settlement transaction positioning window for value S

The Bridge settlement processing window for value S comprises:

* the batch process
* the automatic real-time process for against payment instructions that runs until:
	+ 14.10 on S for deliveries and receipts in all currencies, except: ARS, CAD, EUR, GBP, MXN, PEN and USD
	+ 15:30 on S for deliveries in EUR and GBP
	+ 15.50 on S for receipts in EUR and GBP
	+ 17:10 on S for deliveries in MXN, PEN, USD, CAD and ARS
	+ 17.30 on S for receipts in MXN, PEN, USD, CAD and ARS
	+ 18:50 on S for the optional real-time process for all against payment instructions

**Note:** The timing on the figure above is indicative only and shows the ultimate timing by which a transmission should be sent to or received from CBL.

The optional real-time process allows you to settle Bridge transactions that remain unsettled after the automatic real-time processing.  

| Timing | Detail |
|--------|--------|
| Matching (via ACE files) | Every two minutes |
| Euroclear Proposed Delivery Transmission (EPD) | At hh:15 |
| Euroclear Feedback Transmission (EFB) | At hh:35<br>At hh:55 |
| Clearstream Proposed Delivery Transmission (CPD) | At hh:05 |
| Clearstream Feedback Transmission (CFB) | At hh:25<br>At hh:45 |
