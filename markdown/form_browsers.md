query:
select * from system.[form.headers] where hdr_id = 129
response:
hdr_id	hdr_code	hdr_expr	hdr_basetable	hdr_cap	hdr_type	dtl_type	dtl_code	hdr_level	hdr_remark	doc_header	hdr_addremove	cc_link	hdr_report	dtl_journal	hdr_callback	param1	param2	param3	param4	param5	created_date
129	Form.Sales.Order	SELECT  	a.doc_id, a.doctype_id, a.doc_no, a.doc_extern, a.doc_date, a.doc_deldate, a.doc_term, a.doc_currency, a.doc_saletype, a.doc_vatpercent,     a.docflow_seq, a.cust_id, a.doc_remark, a.doc_total, a.doc_discremark, a.doc_discfactor, a.doc_discvalue, 0 as valuediscremark,e.doc_no as proposal_no,e.proposal_id,a.cc_id,     case  	when ltrim(rtrim(a.doc_discremark)) <> '' and ltrim(rtrim(a.doc_discremark)) <> '0' then 0  	else a.doc_discvalue  	end as inputdiscvalue, 	a.doc_grandtotal, a.doc_qty, b.cust_no, b.cust_desc, a.doc_vattype, a.doc_vat, 	a.sales_id,d.sales_no, d.sales_desc, a.ware_id, a.doc_user,a.cust_name FROM Sales.[Order.Header] a  	LEFT JOIN Sales.[Customer.Master] b ON a.cust_id = b.cust_ID  	LEFT JOIN Sales.[Marketing.Master] d ON a.sales_id=d.sales_id 	LEFT join sales.[order.header] e on a.proposal_id = e.proposal_id	Sales.[Order.Header]	Sales Order	DETAIL	0		All	cust_no,cust_desc,cust_id	SO 	NULL	1		1							2021-09-03

query:
select * from system.[form.headers] where hdr_id = 128
response:
hdr_id	hdr_code	hdr_expr	hdr_basetable	hdr_cap	hdr_type	dtl_type	dtl_code	hdr_level	hdr_remark	doc_header	hdr_addremove	cc_link	hdr_report	dtl_journal	hdr_callback	param1	param2	param3	param4	param5	created_date
128	Browser.Sales.Order	SELECT a.doc_id, a.doc_no, a.doc_extern, a.doc_date, a.doc_deldate,  a.docflow_seq, a.cust_id, a.doc_remark, a.doc_qty, a.doc_total, a.doc_discremark, a.doc_discfactor, a.doc_discvalue, a.doc_grandtotal, b.cust_no, b.cust_desc, c.flow_state, a.doc_vattype,  a.doc_vat FROM Sales.[Order.Header] a INNER JOIN Sales.[Customer.Master] b ON a.cust_id = b.cust_ID INNER JOIN System.[Flow.State] c ON a.doctype_id = c.doctype_id AND  a.docflow_seq = c.docflow_seq where a.doc_date between ::ADate:: and ::BDate:: 		Sales Order	BROWSER	0	Form.Sales.Order	All		All	1	1		1			1	NULL	NULL	NULL	2021-09-03
