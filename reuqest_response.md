1. GET /v1/menu
request:
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/menu' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiZmIxMjhjMTYtMjBhMC00Y2ZiLTgyNDYtOTk5NmNhOTY3MDE0IiwiZXhwIjoxNzkzMjU2ODYzfQ.c55_pF1YIT-uLhgDMsnk1hstbXp3inXHMyFKBZIffm8'

response:
{
  "count": 118,
  "items": [
    {
      "hdrId": 116,
      "code": "Browser.Accounting.Beginning",
      "caption": "Account Beg. Balance",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 118
    },
    {
      "hdrId": 806,
      "code": "Browser.Accounting.Budget",
      "caption": "Budgeting",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 807
    },
    {
      "hdrId": 2,
      "code": "Browser.Accounting.COA",
      "caption": "Chart Of Account",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 100
    },
    {
      "hdrId": 338,
      "code": "Browser.Accounting.COGS",
      "caption": "COGS Calculation",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 339
    },
    {
      "hdrId": 393,
      "code": "Browser.Accounting.DNCN",
      "caption": "Debit/Credit Note",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 394
    },
    {
      "hdrId": 145,
      "code": "Browser.Accounting.General",
      "caption": "General Journal",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 146
    },
    {
      "hdrId": 823,
      "code": "Browser.Accounting.GL",
      "caption": "General Ledger",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 234,
      "code": "Browser.Accounting.Journal",
      "caption": "Journal View",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 493,
      "code": "Browser.Accounting.UnfixedJournal",
      "caption": "Unfixed Journal",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 448,
      "code": "Browser.Accounting.VAT",
      "caption": "VAT Registration",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 822,
      "code": "Browser.Accounting.Aging.AP",
      "caption": "Aging Hutang",
      "type": "browser",
      "module": "Accounting",
      "group": "Aging",
      "detailHdrId": null
    },
    {
      "hdrId": 819,
      "code": "Browser.Accounting.Aging.AR",
      "caption": "Aging Piutang",
      "type": "browser",
      "module": "Accounting",
      "group": "Aging",
      "detailHdrId": null
    },
    {
      "hdrId": 460,
      "code": "Browser.Accounting.AP.Summary",
      "caption": "AP Summary",
      "type": "browser",
      "module": "Accounting",
      "group": "AP",
      "detailHdrId": 466
    },
    {
      "hdrId": 820,
      "code": "Browser.Accounting.AP.Rincian",
      "caption": "Rincian Hutang",
      "type": "browser",
      "module": "Accounting",
      "group": "AP",
      "detailHdrId": null
    },
    {
      "hdrId": 459,
      "code": "Browser.Accounting.AR.Aging",
      "caption": "AR Aging",
      "type": "browser",
      "module": "Accounting",
      "group": "AR",
      "detailHdrId": 461
    },
    {
      "hdrId": 458,
      "code": "Browser.Accounting.AR.Summary",
      "caption": "AR Summary",
      "type": "browser",
      "module": "Accounting",
      "group": "AR",
      "detailHdrId": 462
    },
    {
      "hdrId": 824,
      "code": "Browser.Accounting.AR.Rincian",
      "caption": "Rincian Piutang",
      "type": "browser",
      "module": "Accounting",
      "group": "AR",
      "detailHdrId": null
    },
    {
      "hdrId": 657,
      "code": "Browser.Accounting.Asset.Management",
      "caption": "Asset Reminder.",
      "type": "browser",
      "module": "Accounting",
      "group": "Asset",
      "detailHdrId": 658
    },
    {
      "hdrId": 549,
      "code": "Browser.Accounting.BI.Data",
      "caption": "BI Data",
      "type": "browser",
      "module": "Accounting",
      "group": "BI",
      "detailHdrId": null
    },
    {
      "hdrId": 542,
      "code": "Browser.Accounting.BI.Mapping",
      "caption": "BI Group Mapping",
      "type": "browser",
      "module": "Accounting",
      "group": "BI",
      "detailHdrId": 543
    },
    {
      "hdrId": 781,
      "code": "Browser.Accounting.Bon.Sales",
      "caption": "BS Perjalanan Dinas",
      "type": "browser",
      "module": "Accounting",
      "group": "Bon",
      "detailHdrId": 782
    },
    {
      "hdrId": 797,
      "code": "Browser.Accounting.Bon.Selesai",
      "caption": "Penyelesaian BS",
      "type": "browser",
      "module": "Accounting",
      "group": "Bon",
      "detailHdrId": 798
    },
    {
      "hdrId": 769,
      "code": "Browser.Accounting.Budget.Input",
      "caption": "Input Budgeting",
      "type": "browser",
      "module": "Accounting",
      "group": "Budget",
      "detailHdrId": 770
    },
    {
      "hdrId": 626,
      "code": "Browser.Accounting.Cash.Callback",
      "caption": "Cash API Callback",
      "type": "browser",
      "module": "Accounting",
      "group": "Cash",
      "detailHdrId": 627
    },
    {
      "hdrId": 636,
      "code": "Browser.Accounting.Cash.Bank.Flow.PerMonth",
      "caption": "Cash Bank Flow",
      "type": "browser",
      "module": "Accounting",
      "group": "Cash",
      "detailHdrId": null
    },
    {
      "hdrId": 205,
      "code": "Browser.Accounting.Cash.In",
      "caption": "Cash In",
      "type": "browser",
      "module": "Accounting",
      "group": "Cash",
      "detailHdrId": 316
    },
    {
      "hdrId": 187,
      "code": "Browser.Accounting.Cash.Out",
      "caption": "Cash Out",
      "type": "browser",
      "module": "Accounting",
      "group": "Cash",
      "detailHdrId": 317
    },
    {
      "hdrId": 678,
      "code": "Browser.Accounting.Cash.Out.Request",
      "caption": "Cash Request",
      "type": "browser",
      "module": "Accounting",
      "group": "Cash",
      "detailHdrId": 679
    },
    {
      "hdrId": 488,
      "code": "Browser.Accounting.COGS.Monitor",
      "caption": "Inv. Valuation (COGS)",
      "type": "browser",
      "module": "Accounting",
      "group": "COGS",
      "detailHdrId": null
    },
    {
      "hdrId": 224,
      "code": "Browser.Accounting.Currency.Rate",
      "caption": "Currency Rate",
      "type": "browser",
      "module": "Accounting",
      "group": "Currency",
      "detailHdrId": 226
    },
    {
      "hdrId": 714,
      "code": "Browser.Accounting.FA.Class",
      "caption": "FA Class",
      "type": "browser",
      "module": "Accounting",
      "group": "FA",
      "detailHdrId": 330
    },
    {
      "hdrId": 802,
      "code": "Browser.Accounting.FA.Depr.Monthly",
      "caption": "FA Depr Montly",
      "type": "browser",
      "module": "Accounting",
      "group": "FA",
      "detailHdrId": null
    },
    {
      "hdrId": 335,
      "code": "Browser.Accounting.FA.Depr",
      "caption": "FA Depreciation",
      "type": "browser",
      "module": "Accounting",
      "group": "FA",
      "detailHdrId": 336
    },
    {
      "hdrId": 149,
      "code": "Browser.Accounting.FA.Purchase",
      "caption": "FA Purchasing",
      "type": "browser",
      "module": "Accounting",
      "group": "FA",
      "detailHdrId": 150
    },
    {
      "hdrId": 715,
      "code": "Browser.Accounting.FA.Management",
      "caption": "Fixed Assets Mng.",
      "type": "browser",
      "module": "Accounting",
      "group": "FA",
      "detailHdrId": 154
    },
    {
      "hdrId": 809,
      "code": "Browser.Accounting.Financial.CF",
      "caption": "Cash Flow",
      "type": "browser",
      "module": "Accounting",
      "group": "Financial",
      "detailHdrId": null
    },
    {
      "hdrId": 805,
      "code": "Browser.Accounting.Financial.JournalGL",
      "caption": "Trial Balance",
      "type": "browser",
      "module": "Accounting",
      "group": "Financial",
      "detailHdrId": null
    },
    {
      "hdrId": 814,
      "code": "Browser.Accounting.Finansial.BS",
      "caption": "Balance Sheet",
      "type": "browser",
      "module": "Accounting",
      "group": "Finansial",
      "detailHdrId": null
    },
    {
      "hdrId": 815,
      "code": "Browser.Accounting.Finansial.PL",
      "caption": "Profit Loss",
      "type": "browser",
      "module": "Accounting",
      "group": "Finansial",
      "detailHdrId": null
    },
    {
      "hdrId": 480,
      "code": "Browser.Accounting.Inventory.Monitor",
      "caption": "Item AccInv<br/>Monitor",
      "type": "browser",
      "module": "Accounting",
      "group": "Inventory",
      "detailHdrId": null
    },
    {
      "hdrId": 102,
      "code": "Browser.Accounting.Subcode.Group",
      "caption": "GL Subcode Database",
      "type": "browser",
      "module": "Accounting",
      "group": "Subcode",
      "detailHdrId": 139
    },
    {
      "hdrId": 761,
      "code": "Browser.Canvas.In",
      "caption": "Canvas In",
      "type": "browser",
      "module": "Canvas",
      "group": null,
      "detailHdrId": 762
    },
    {
      "hdrId": 757,
      "code": "Browser.Canvas.Out",
      "caption": "Canvas Out",
      "type": "browser",
      "module": "Canvas",
      "group": null,
      "detailHdrId": 758
    },
    {
      "hdrId": 300,
      "code": "Browser.Consignee.In",
      "caption": "Consignee In",
      "type": "browser",
      "module": "Consignee",
      "group": null,
      "detailHdrId": 304
    },
    {
      "hdrId": 299,
      "code": "Browser.Consignee.Out",
      "caption": "Consignee Out",
      "type": "browser",
      "module": "Consignee",
      "group": null,
      "detailHdrId": 301
    },
    {
      "hdrId": 513,
      "code": "Browser.EFaktur.Faktur.Penjualan",
      "caption": "EFaktur Penjualan",
      "type": "browser",
      "module": "EFaktur",
      "group": "Faktur",
      "detailHdrId": null
    },
    {
      "hdrId": 514,
      "code": "Browser.EFaktur.Faktur.Pembelian",
      "caption": "Faktur Pembelian",
      "type": "browser",
      "module": "EFaktur",
      "group": "Faktur",
      "detailHdrId": null
    },
    {
      "hdrId": 209,
      "code": "Browser.HR.Employee",
      "caption": "Employee",
      "type": "browser",
      "module": "HR",
      "group": null,
      "detailHdrId": 210
    },
    {
      "hdrId": 776,
      "code": "Browser.HR.Division.Master",
      "caption": "Division Master",
      "type": "browser",
      "module": "HR",
      "group": "Division",
      "detailHdrId": 777
    },
    {
      "hdrId": 653,
      "code": "Browser.HR.Employee.Master",
      "caption": "Employee Master",
      "type": "browser",
      "module": "HR",
      "group": "Employee",
      "detailHdrId": 654
    },
    {
      "hdrId": 784,
      "code": "Browser.HR.Employee.Master.OFA",
      "caption": "Employee Master",
      "type": "browser",
      "module": "HR",
      "group": "Employee",
      "detailHdrId": 785
    },
    {
      "hdrId": 774,
      "code": "Browser.HR.Event.Master",
      "caption": "Event Master",
      "type": "browser",
      "module": "HR",
      "group": "Event",
      "detailHdrId": 775
    },
    {
      "hdrId": 788,
      "code": "Browser.HR.Job.Master",
      "caption": "Job Master",
      "type": "browser",
      "module": "HR",
      "group": "Job",
      "detailHdrId": 789
    },
    {
      "hdrId": 790,
      "code": "Browser.HR.JobLevel.Master",
      "caption": "Job Level Master",
      "type": "browser",
      "module": "HR",
      "group": "JobLevel",
      "detailHdrId": 791
    },
    {
      "hdrId": 795,
      "code": "Browser.HR.Region.Master",
      "caption": "Region Master",
      "type": "browser",
      "module": "HR",
      "group": "Region",
      "detailHdrId": 796
    },
    {
      "hdrId": 445,
      "code": "Browser.Inventory.Journal",
      "caption": "Inventory Journal",
      "type": "browser",
      "module": "Inventory",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 737,
      "code": "Browser.Inventory.MA",
      "caption": "Inventory MA",
      "type": "browser",
      "module": "Inventory",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 324,
      "code": "Browser.Inventory.Take",
      "caption": "Stock Take",
      "type": "browser",
      "module": "Inventory",
      "group": null,
      "detailHdrId": 325
    },
    {
      "hdrId": 103,
      "code": "Browser.Inventory.Warehouse",
      "caption": "Warehouse",
      "type": "browser",
      "module": "Inventory",
      "group": null,
      "detailHdrId": 353
    },
    {
      "hdrId": 540,
      "code": "Browser.Inventory.Car.Master",
      "caption": "Car Database",
      "type": "browser",
      "module": "Inventory",
      "group": "Car",
      "detailHdrId": 541
    },
    {
      "hdrId": 141,
      "code": "Browser.Inventory.Item.Database",
      "caption": "Inventory",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": 142
    },
    {
      "hdrId": 602,
      "code": "Browser.Inventory.Item.Database.Goods",
      "caption": "Inventory",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": 603
    },
    {
      "hdrId": 801,
      "code": "Browser.Inventory.Item.Database2",
      "caption": "Inventory",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": 142
    },
    {
      "hdrId": 476,
      "code": "Browser.Inventory.Item.Beginning",
      "caption": "Item Beginning",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": 475
    },
    {
      "hdrId": 499,
      "code": "Browser.Inventory.Item.Brand",
      "caption": "Item Brand",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": 502
    },
    {
      "hdrId": 503,
      "code": "Browser.Inventory.Item.Class",
      "caption": "Item Class",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": 504
    },
    {
      "hdrId": 731,
      "code": "Browser.Inventory.Item.Aging",
      "caption": "Umur Stock",
      "type": "browser",
      "module": "Inventory",
      "group": "Item",
      "detailHdrId": null
    },
    {
      "hdrId": 768,
      "code": "Browser.Inventory.MA.CP",
      "caption": "Inventory MA CP",
      "type": "browser",
      "module": "Inventory",
      "group": "MA",
      "detailHdrId": null
    },
    {
      "hdrId": 446,
      "code": "Browser.Inventory.Stock.Card",
      "caption": "Stock Card",
      "type": "browser",
      "module": "Inventory",
      "group": "Stock",
      "detailHdrId": null
    },
    {
      "hdrId": 447,
      "code": "Browser.Inventory.Stock.Mutation",
      "caption": "Stock Mutation",
      "type": "browser",
      "module": "Inventory",
      "group": "Stock",
      "detailHdrId": null
    },
    {
      "hdrId": 816,
      "code": "Browser.Lap.MutasiStok.Tahunan",
      "caption": "Mutasi",
      "type": "browser",
      "module": "Lap",
      "group": "MutasiStok",
      "detailHdrId": null
    },
    {
      "hdrId": 642,
      "code": "Browser.Latihan.Graylite",
      "caption": "Graylite Browser",
      "type": "browser",
      "module": "Latihan",
      "group": null,
      "detailHdrId": null
    },
    {
      "hdrId": 55,
      "code": "Browser.Preset.Inventory.Item.Group",
      "caption": "Inventory Item Group",
      "type": "browser",
      "module": "Preset",
      "group": "Inventory",
      "detailHdrId": 57
    },
    {
      "hdrId": 110,
      "code": "Browser.Preset.Purchase.Item.Group",
      "caption": "Purchase Item Group",
      "type": "browser",
      "module": "Preset",
      "group": "Purchase",
      "detailHdrId": 107
    },
    {
      "hdrId": 171,
      "code": "Browser.Preset.Sales.Item.Group",
      "caption": "Sales Item Group",
      "type": "browser",
      "module": "Preset",
      "group": "Sales",
      "detailHdrId": 108
    },
    {
      "hdrId": 246,
      "code": "Browser.Production.Finish",
      "caption": "Packing Result",
      "type": "browser",
      "module": "Production",
      "group": null,
      "detailHdrId": 262
    },
    {
      "hdrId": 252,
      "code": "Browser.Production.Usage",
      "caption": "Stock Usage",
      "type": "browser",
      "module": "Production",
      "group": null,
      "detailHdrId": 250
    },
    {
      "hdrId": 261,
      "code": "Browser.Production.WIP",
      "caption": "WIP Production Result",
      "type": "browser",
      "module": "Production",
      "group": null,
      "detailHdrId": 247
    },
    {
      "hdrId": 604,
      "code": "Browser.Production.Finish.Good.Header",
      "caption": "Finish Good",
      "type": "browser",
      "module": "Production",
      "group": "Finish",
      "detailHdrId": 608
    },
    {
      "hdrId": 387,
      "code": "Browser.Production.Project.Database",
      "caption": "Project Database",
      "type": "browser",
      "module": "Production",
      "group": "Project",
      "detailHdrId": 388
    },
    {
      "hdrId": 254,
      "code": "Browser.Production.Usage.Tooling",
      "caption": "Tooling Usage",
      "type": "browser",
      "module": "Production",
      "group": "Usage",
      "detailHdrId": 259
    },
    {
      "hdrId": 611,
      "code": "Browser.Production.Work.Order",
      "caption": "Work Order",
      "type": "browser",
      "module": "Production",
      "group": "Work",
      "detailHdrId": 612
    },
    {
      "hdrId": 726,
      "code": "Browser.Purchase.Inspection",
      "caption": "Purchase Inspection",
      "type": "browser",
      "module": "Purchase",
      "group": null,
      "detailHdrId": 717
    },
    {
      "hdrId": 167,
      "code": "Browser.Purchase.Invoice",
      "caption": "Purchase Invoice",
      "type": "browser",
      "module": "Purchase",
      "group": null,
      "detailHdrId": 168
    },
    {
      "hdrId": 156,
      "code": "Browser.Purchase.Order",
      "caption": "Purchase Order",
      "type": "browser",
      "module": "Purchase",
      "group": null,
      "detailHdrId": 157
    },
    {
      "hdrId": 727,
      "code": "Browser.Purchase.Receiving",
      "caption": "Purchase Receiving",
      "type": "browser",
      "module": "Purchase",
      "group": null,
      "detailHdrId": 716
    },
    {
      "hdrId": 164,
      "code": "Browser.Purchase.Request",
      "caption": "Purchase Request",
      "type": "browser",
      "module": "Purchase",
      "group": null,
      "detailHdrId": 165
    },
    {
      "hdrId": 270,
      "code": "Browser.Purchase.Return",
      "caption": "Purchase Return",
      "type": "browser",
      "module": "Purchase",
      "group": null,
      "detailHdrId": 271
    },
    {
      "hdrId": 821,
      "code": "Browser.Purchase.Invoice.IPO",
      "caption": "Purchase Invoice",
      "type": "browser",
      "module": "Purchase",
      "group": "Invoice",
      "detailHdrId": 168
    },
    {
      "hdrId": 178,
      "code": "Browser.Purchase.Item.Database",
      "caption": "Purchase Item",
      "type": "browser",
      "module": "Purchase",
      "group": "Item",
      "detailHdrId": 179
    },
    {
      "hdrId": 233,
      "code": "Browser.Purchase.Item.Database.Non.Stock",
      "caption": "Purchase Item",
      "type": "browser",
      "module": "Purchase",
      "group": "Item",
      "detailHdrId": 232
    },
    {
      "hdrId": 13,
      "code": "Browser.Purchase.Supplier.Database",
      "caption": "Supplier",
      "type": "browser",
      "module": "Purchase",
      "group": "Supplier",
      "detailHdrId": 28
    },
    {
      "hdrId": 740,
      "code": "Browser.Report.Accounting.Cash.Balance",
      "caption": "Cash Balance",
      "type": "browser",
      "module": "Report",
      "group": "Accounting",
      "detailHdrId": null
    },
    {
      "hdrId": 736,
      "code": "Browser.Report.Inventory.Aging",
      "caption": "Inventory Aging",
      "type": "browser",
      "module": "Report",
      "group": "Inventory",
      "detailHdrId": null
    },
    {
      "hdrId": 739,
      "code": "Browser.Report.Part.Moving.Class",
      "caption": "Inventory Aging Per Class",
      "type": "browser",
      "module": "Report",
      "group": "Part",
      "detailHdrId": null
    },
    {
      "hdrId": 738,
      "code": "Browser.Report.Part.Moving",
      "caption": "Inventory Aging Per Item",
      "type": "browser",
      "module": "Report",
      "group": "Part",
      "detailHdrId": null
    },
    {
      "hdrId": 826,
      "code": "Browser.Sales.PL",
      "caption": "Packing List",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 827
    },
    {
      "hdrId": 276,
      "code": "Browser.Sales.Delivery",
      "caption": "Sales Delivery",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 275
    },
    {
      "hdrId": 236,
      "code": "Browser.Sales.Invoice",
      "caption": "Sales Invoice",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 237
    },
    {
      "hdrId": 753,
      "code": "Browser.Sales.Force",
      "caption": "Sales Invoice",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 756
    },
    {
      "hdrId": 128,
      "code": "Browser.Sales.Order",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 129
    },
    {
      "hdrId": 638,
      "code": "Browser.Sales.Order1",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 129
    },
    {
      "hdrId": 743,
      "code": "Browser.Sales.Proposal",
      "caption": "Sales Proposal",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 742
    },
    {
      "hdrId": 293,
      "code": "Browser.Sales.Return",
      "caption": "Sales Return",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 294
    },
    {
      "hdrId": 97,
      "code": "Browser.Sales.Customer.Database",
      "caption": "Customer Database",
      "type": "browser",
      "module": "Sales",
      "group": "Customer",
      "detailHdrId": 99
    },
    {
      "hdrId": 172,
      "code": "Browser.Sales.Item.Master",
      "caption": "Sales Item Database",
      "type": "browser",
      "module": "Sales",
      "group": "Item",
      "detailHdrId": 173
    },
    {
      "hdrId": 260,
      "code": "Browser.Sales.Item.Master.Complete",
      "caption": "Sales Item Database",
      "type": "browser",
      "module": "Sales",
      "group": "Item",
      "detailHdrId": 173
    },
    {
      "hdrId": 306,
      "code": "Browser.Sales.Marketing.Database",
      "caption": "Sales Person",
      "type": "browser",
      "module": "Sales",
      "group": "Marketing",
      "detailHdrId": 307
    },
    {
      "hdrId": 536,
      "code": "Browser.Sales.Order.Depo",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": "Order",
      "detailHdrId": 129
    },
    {
      "hdrId": 666,
      "code": "Browser.Sales.Order.Mobile",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": "Order",
      "detailHdrId": 667
    },
    {
      "hdrId": 830,
      "code": "Browser.Sales.Order.Marketplace",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": "Order",
      "detailHdrId": 833
    },
    {
      "hdrId": 831,
      "code": "Browser.Sales.Order.Eceran",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": "Order",
      "detailHdrId": 832
    },
    {
      "hdrId": 432,
      "code": "Browser.System.Schedule",
      "caption": "Job Scheduler",
      "type": "browser",
      "module": "System",
      "group": null,
      "detailHdrId": 433
    },
    {
      "hdrId": 629,
      "code": "Browser.System.Mobile",
      "caption": "Menu Mobile <br/>Configuration",
      "type": "browser",
      "module": "System",
      "group": null,
      "detailHdrId": 630
    },
    {
      "hdrId": 511,
      "code": "Browser.System.Closed.Period",
      "caption": "Closed Period<br/>Management",
      "type": "browser",
      "module": "System",
      "group": "Closed",
      "detailHdrId": 512
    },
    {
      "hdrId": 111,
      "code": "Browser.System.Flow.Document",
      "caption": "Document Management",
      "type": "browser",
      "module": "System",
      "group": "Flow",
      "detailHdrId": 203
    },
    {
      "hdrId": 216,
      "code": "Browser.User.Database",
      "caption": "User Database",
      "type": "browser",
      "module": "User",
      "group": null,
      "detailHdrId": 219
    },
    {
      "hdrId": 377,
      "code": "Browser.Warehouse.Mutation",
      "caption": "Warehouse Mutation",
      "type": "browser",
      "module": "Warehouse",
      "group": null,
      "detailHdrId": 378
    }
  ]
}

2. GET /v1/meta/browser/{hdrId}
request:
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/browser/128' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiZmIxMjhjMTYtMjBhMC00Y2ZiLTgyNDYtOTk5NmNhOTY3MDE0IiwiZXhwIjoxNzkzMjU2ODYzfQ.c55_pF1YIT-uLhgDMsnk1hstbXp3inXHMyFKBZIffm8'

response:
{
  "hdrId": 128,
  "code": "Browser.Sales.Order",
  "caption": "Sales Order",
  "schemaVersion": "f8b603a8",
  "rowKey": "doc_id",
  "dateColumn": "doc_date",
  "detailCode": "Form.Sales.Order",
  "detailHdrId": 129,
  "canAdd": false,
  "canRemove": false,
  "style": "Fit",
  "columns": [
    {
      "name": "doc_id",
      "caption": "Doc Id",
      "type": "integer",
      "hidden": true,
      "scale": 0,
      "width": 50
    },
    {
      "name": "doc_no",
      "caption": "Doc.No.",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 75
    },
    {
      "name": "doc_extern",
      "caption": "No. SO",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "doc_date",
      "caption": "SO Date",
      "type": "date",
      "hidden": false,
      "scale": 0,
      "width": 75
    },
    {
      "name": "cust_desc",
      "caption": "Customer Name",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 350
    },
    {
      "name": "doc_grandtotal",
      "caption": "Total",
      "type": "money",
      "hidden": false,
      "scale": 0,
      "width": 120
    },
    {
      "name": "flow_state",
      "caption": "State",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    }
  ],
  "filters": [
    {
      "name": "ADate",
      "label": "Date From",
      "type": "date",
      "default": "DATEADD(-360,TODAY())",
      "required": true,
      "hidden": false
    },
    {
      "name": "BDate",
      "label": "Date To",
      "type": "date",
      "default": "EDOM(NOW())",
      "required": true,
      "hidden": false
    }
  ],
  "layout": {
    "title": "doc_no",
    "date": "doc_date",
    "subtitle": "cust_desc",
    "badge": [
      "flow_state"
    ],
    "metrics": [
      "doc_grandtotal"
    ],
    "details": [
      "doc_extern"
    ]
  },
  "commands": []
}

3. GET /v1/meta/form/{hdrId}
request:
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/form/129' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiZmIxMjhjMTYtMjBhMC00Y2ZiLTgyNDYtOTk5NmNhOTY3MDE0IiwiZXhwIjoxNzkzMjU2ODYzfQ.c55_pF1YIT-uLhgDMsnk1hstbXp3inXHMyFKBZIffm8'

response:
{
  "hdrId": 129,
  "code": "Form.Sales.Order",
  "caption": "Sales Order",
  "schemaVersion": "18dbdf28",
  "idField": "doc_id",
  "titleFields": [
    "doc_no"
  ],
  "docHeader": null,
  "canSave": true,
  "journalView": false,
  "tabs": [
    {
      "name": "General",
      "fields": [
        {
          "name": "doc_id",
          "caption": "Doc Id",
          "widget": "text",
          "dataType": "number",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false
        },
        {
          "name": "doc_no",
          "caption": "SO#",
          "widget": "text",
          "dataType": "text",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false
        },
        {
          "name": "doc_date",
          "caption": "SO Date",
          "widget": "date",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": true
        },
        {
          "name": "",
          "caption": "",
          "widget": "label",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": false,
          "inlineWithPrevious": false
        },
        {
          "name": "cust_no",
          "caption": "Cust_no",
          "widget": "picker",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": false,
          "inlineWithPrevious": false,
          "pickerCode": "Picker.Sales.Customer",
          "pickerHdrId": 131
        },
        {
          "name": "cust_name",
          "caption": "",
          "widget": "text",
          "dataType": "text",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": true
        },
        {
          "name": "",
          "caption": "Sales Item",
          "widget": "grid",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false,
          "gridCode": "Grid.Sales.Order.Detail",
          "gridHdrId": 132,
          "saveWithForm": true
        },
        {
          "name": "doc_qty",
          "caption": "Total Qty",
          "widget": "formula",
          "dataType": "number",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false,
          "expression": "docQty"
        },
        {
          "name": "doc_total",
          "caption": "SubTotal",
          "widget": "formula",
          "dataType": "number",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false,
          "expression": "docTotal"
        },
        {
          "name": "doc_remark",
          "caption": "Remark",
          "widget": "textarea",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false
        },
        {
          "name": "docflow_seq",
          "caption": "Docflow Seq",
          "widget": "number",
          "dataType": "number",
          "readonly": false,
          "hidden": true,
          "update": false,
          "inlineWithPrevious": false
        },
        {
          "name": "doctype_id",
          "caption": "",
          "widget": "integer",
          "dataType": "number",
          "readonly": false,
          "hidden": true,
          "update": false,
          "inlineWithPrevious": false
        },
        {
          "name": "cc_id",
          "caption": "cc id",
          "widget": "number",
          "dataType": "number",
          "readonly": false,
          "hidden": true,
          "update": true,
          "inlineWithPrevious": false
        },
        {
          "name": "cust_id",
          "caption": "",
          "widget": "number",
          "dataType": "number",
          "readonly": false,
          "hidden": true,
          "update": true,
          "inlineWithPrevious": false
        }
      ]
    }
  ],
  "variables": [
    {
      "name": "docTotal",
      "from": ""
    },
    {
      "name": "docQty",
      "from": ""
    },
    {
      "name": "DocID",
      "from": "doc_id"
    },
    {
      "name": "CustID",
      "from": "cust_id"
    }
  ],
  "grids": {
    "132": {
      "hdrId": 132,
      "code": "Grid.Sales.Order.Detail",
      "caption": "",
      "rowKey": "trans_id",
      "columns": [
        {
          "name": "trans_id",
          "caption": "Trans Id",
          "type": "text",
          "hidden": true,
          "scale": 0,
          "width": 100
        },
        {
          "name": "doc_id",
          "caption": "Doc Id",
          "type": "text",
          "hidden": true,
          "scale": 0,
          "width": 100
        },
        {
          "name": "item_id",
          "caption": "Item Id",
          "type": "text",
          "hidden": true,
          "scale": 0,
          "width": 100
        },
        {
          "name": "trans_idx",
          "caption": "No",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        },
        {
          "name": "item_no",
          "caption": "Code",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100,
          "pickerCode": "Picker.Inventory.Item.brgJadi",
          "pickerHdrId": 803
        },
        {
          "name": "item_desc",
          "caption": "Item Name",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        },
        {
          "name": "trans_qty",
          "caption": "Qty",
          "type": "text",
          "hidden": false,
          "scale": 2,
          "width": 100
        },
        {
          "name": "item_unit",
          "caption": "Unit",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        },
        {
          "name": "trans_price",
          "caption": "Harga",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        },
        {
          "name": "trans_discvalue",
          "caption": "Diskon(Rp)",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        },
        {
          "name": "trans_total",
          "caption": "Total",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        },
        {
          "name": "trans_remark",
          "caption": "Remark",
          "type": "text",
          "hidden": false,
          "scale": 0,
          "width": 100
        }
      ]
    }
  },
  "defaults": {},
  "commands": [
    {
      "id": 252,
      "name": "Print SO",
      "confirm": "Are you sure you want to process this operation?",
      "order": 2
    },
    {
      "id": 340,
      "name": "Create PL",
      "confirm": "Are you sure you want to process this operation?",
      "order": 4
    }
  ]
}

4. GET /v1/meta/grid/{hdrId}
request:
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/grid/132' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiZmIxMjhjMTYtMjBhMC00Y2ZiLTgyNDYtOTk5NmNhOTY3MDE0IiwiZXhwIjoxNzkzMjU2ODYzfQ.c55_pF1YIT-uLhgDMsnk1hstbXp3inXHMyFKBZIffm8'

response:
{
  "hdrId": 132,
  "code": "Grid.Sales.Order.Detail",
  "caption": "",
  "rowKey": "trans_id",
  "columns": [
    {
      "name": "trans_id",
      "caption": "Trans Id",
      "type": "text",
      "hidden": true,
      "scale": 0,
      "width": 100
    },
    {
      "name": "doc_id",
      "caption": "Doc Id",
      "type": "text",
      "hidden": true,
      "scale": 0,
      "width": 100
    },
    {
      "name": "item_id",
      "caption": "Item Id",
      "type": "text",
      "hidden": true,
      "scale": 0,
      "width": 100
    },
    {
      "name": "trans_idx",
      "caption": "No",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "item_no",
      "caption": "Code",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100,
      "pickerCode": "Picker.Inventory.Item.brgJadi",
      "pickerHdrId": 803
    },
    {
      "name": "item_desc",
      "caption": "Item Name",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "trans_qty",
      "caption": "Qty",
      "type": "text",
      "hidden": false,
      "scale": 2,
      "width": 100
    },
    {
      "name": "item_unit",
      "caption": "Unit",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "trans_price",
      "caption": "Harga",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "trans_discvalue",
      "caption": "Diskon(Rp)",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "trans_total",
      "caption": "Total",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    },
    {
      "name": "trans_remark",
      "caption": "Remark",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    }
  ]
}

5. GET /v1/meta/picker/{hdrId}
request
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/picker/803' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiZmIxMjhjMTYtMjBhMC00Y2ZiLTgyNDYtOTk5NmNhOTY3MDE0IiwiZXhwIjoxNzkzMjY1NDI4fQ.0pxQbcxgWd3mqPvHPbALtar1OCO3cqjFwDj8R_FoV7A'

response:
{
  "hdrId": 803,
  "code": "Picker.Inventory.Item.brgJadi",
  "caption": "Inventory Item",
  "columns": [
    {
      "name": "item_id",
      "caption": "Item Id",
      "type": "text",
      "hidden": false
    },
    {
      "name": "item_no",
      "caption": "Item No",
      "type": "text",
      "hidden": false
    },
    {
      "name": "item_desc",
      "caption": "Item Desc",
      "type": "text",
      "hidden": false
    },
    {
      "name": "item_unit",
      "caption": "Item Unit",
      "type": "text",
      "hidden": false
    },
    {
      "name": "item_kemasan",
      "caption": "Item Kemasan",
      "type": "text",
      "hidden": false
    },
    {
      "name": "class_id",
      "caption": "Class Id",
      "type": "text",
      "hidden": false
    },
    {
      "name": "trans_price",
      "caption": "Trans Price",
      "type": "text",
      "hidden": false
    }
  ]
}

6. GET /v1/browsers/{hdrId}/rows
request:
postman request 'http://127.0.0.1:8000/v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31' \
  --header 'accept: */*' \
  --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiZmIxMjhjMTYtMjBhMC00Y2ZiLTgyNDYtOTk5NmNhOTY3MDE0IiwiZXhwIjoxNzkzMjY1NDI4fQ.0pxQbcxgWd3mqPvHPbALtar1OCO3cqjFwDj8R_FoV7A'

response:
{
    "items": [
        {
            "doc_id": 220,
            "doc_no": "",
            "doc_extern": "",
            "doc_date": "2026-10-27",
            "doc_deldate": null,
            "docflow_seq": 0,
            "cust_id": 1789,
            "doc_remark": "",
            "doc_qty": "1.0000",
            "doc_total": "0.0000",
            "doc_discremark": "",
            "doc_discfactor": "0E-17",
            "doc_discvalue": "0.0000",
            "doc_grandtotal": "0.0000",
            "cust_no": "C.00653",
            "cust_desc": "ABDUL ROCHIM - Lamongan",
            "flow_state": "<div style='color:red'>New Entry</div>",
            "doc_vattype": 1,
            "doc_vat": "0.0000"
        }
    ],
    "pageSize": 50,
    "hasMore": false,
    "nextCursor": null,
    "total": null
}

7. GET /v1/forms/{hdrId}/new
request:
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/forms/129/new' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiMTg0NDZiZjktM2M2NC00NTg4LTk3ODQtZWY2MzJmM2I2ZmUzIiwiZXhwIjoxNzkzMjc5NDEzfQ.AjrmV28Jq9cYH2rgJlt2Lp7cyEfOAXnTtProVmyJCG4'

response:
{
  "header": {
    "cust_id": 1
  },
  "grids": {},
  "schemaVersion": "18dbdf28"
}

8. POST /v1/forms/{hdrId}/records
request:
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/forms/129/records' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjI5LCJsb2dpbiI6ImtvbWFuZyIsInJvbGVzIjpbIkdlbmVyYWwiXSwiY2NJZCI6MSwiZGl2SWQiOm51bGwsIndhcmVJZCI6MSwic2lkIjoiMTg0NDZiZjktM2M2NC00NTg4LTk3ODQtZWY2MzJmM2I2ZmUzIiwiZXhwIjoxNzkzMjc5NDEzfQ.AjrmV28Jq9cYH2rgJlt2Lp7cyEfOAXnTtProVmyJCG4' \
  -H 'Content-Type: application/json' \
  -d '{
  "schemaVersion": "18dbdf28",
  "header": {
    "doc_no": "SO-2026-001",
    "doc_date": "2026-03-29",
    "cust_id": 1,
    "cc_id": 1,
    "doc_total": 840000,
    "doc_remark": "Test Sales Order"
  }
}'

response:
{
  "header": {
    "doc_id": 222,
    "doctype_id": 32,
    "cc_id": 1,
    "doc_no": "SO-2026-001",
    "doc_extern": "",
    "doc_date": "2026-03-29",
    "doc_deldate": null,
    "doc_term": 0,
    "docflow_seq": 0,
    "doc_currency": "IDR",
    "doc_currate": 1,
    "cust_id": 1,
    "sales_id": 1,
    "doc_saletype": 1,
    "doc_remark": "Test Sales Order",
    "doc_total": 840000,
    "doc_vattype": 1,
    "doc_vat": 0,
    "doc_discremark": "",
    "doc_discfactor": 0,
    "doc_discvalue": 0,
    "doc_grandtotal": 840000,
    "doc_qty": null,
    "doc_desc": "SO SO-2026-001",
    "project_id": null,
    "valuediscremark": 0,
    "inputdiscvalue": 0,
    "ware_id": 1,
    "doc_user": null,
    "doc_vatpercent": null,
    "coba_total": null,
    "doc_image": "",
    "doc_image2": "",
    "proposal_id": 0,
    "grpDoc": null,
    "cust_name": null,
    "doc_id_si": null
  },
  "grids": {
    "132": {
      "rows": []
    }
  },
  "schemaVersion": "18dbdf28"
}

