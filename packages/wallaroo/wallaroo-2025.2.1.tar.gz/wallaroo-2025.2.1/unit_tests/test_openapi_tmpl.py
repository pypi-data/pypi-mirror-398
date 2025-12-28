import pyarrow as pa

from wallaroo.openapi_tmpl import (
    arrow_schema_to_openapi_yaml,
    decode_arrow_schema_from_base64,
)


def test_arrow_schema_to_openapi_yaml():
    """Test arrow_schema_to_openapi_yaml function with comprehensive test cases."""

    # Test cases mapping base64-encoded Arrow schemas to expected OpenAPI YAML outputs
    test_cases = {
        "/////3ABAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAMAAADMAAAAZAAAAAQAAAAQ////AAABDBQAAAAgAAAABAAAAAEAAAAYAAAACwAAAGNvbmZpZGVuY2VzAET///9A////AAABAxAAAAAYAAAABAAAAAAAAAAEAAAAaXRlbQAAAAAy////AAABAGz///8AAAEMFAAAABwAAAAEAAAAAQAAABQAAAAHAAAAY2xhc3NlcwCc////mP///wAAAQIQAAAAIAAAAAQAAAAAAAAABAAAAGl0ZW0AAAAACAAMAAgABwAIAAAAAAAAAUAAAADQ////AAABDBQAAAAgAAAABAAAAAEAAAAoAAAABQAAAGJveGVzAAAABAAEAAQAAAAQABQACAAGAAcADAAAABAAEAAAAAAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAGAAYAAAAAAAEAAAAAAA==": """
properties:
  boxes:
    type: array
    items:
      type: number
      format: float
  classes:
    type: array
    items:
      type: integer
      format: int64
  confidences:
    type: array
    items:
      type: number
      format: float
required: []
""",
        "/////3AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAUAAAAEAAUAAgABgAHAAwAAAAQABAAAAAAAAEFEAAAABwAAAAEAAAAAAAAAAQAAABmYWlsAAAAAAQABAAEAAAA": """
properties:
  fail:
    type: string
required: []
""",
        "/////9AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAEAAAApP///wAAAQwUAAAAHAAAAAQAAAABAAAAFAAAAAUAAABpbWFnZQAAANT////Q////AAABDBQAAAAgAAAABAAAAAEAAAAoAAAABAAAAGl0ZW0AAAAABAAEAAQAAAAQABQACAAGAAcADAAAABAAEAAAAAAAAQIQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAEAAYAAAAQAAAA": """
properties:
  image:
    type: array
    items:
      type: array
      items:
        type: integer
        format: int32
required: []
""",
        "/////3AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAUAAAAEAAUAAgABgAHAAwAAAAQABAAAAAAAAEFEAAAABwAAAAEAAAAAAAAAAUAAABpbWFnZQAAAAQABAAEAAAA": """
properties:
  image:
    type: string
required: []
""",
        "/////6gAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAIAAABIAAAABAAAAND///8AAAEFEAAAACAAAAAEAAAAAAAAAA4AAABnZW5lcmF0ZWRfdGV4dAAAyP///xAAFAAIAAYABwAMAAAAEAAQAAAAAAABBRAAAAAcAAAABAAAAAAAAAAEAAAAdGV4dAAAAAAEAAQABAAAAAAAAAA=": """
properties:
  text:
    type: string
  generated_text:
    type: string
required: []
""",
        "/////4AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAUAAAAEAAUAAgABgAHAAwAAAAQABAAAAAAAAECEAAAACAAAAAEAAAAAAAAAAQAAAB0ZXN0AAAAAAgADAAIAAcACAAAAAAAAAEIAAAAAAAAAA==": """
properties:
  test:
    type: integer
    format: int32
required: []
""",
        "//////gAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAQAAACYAAAAXAAAADAAAAAEAAAAiP///wAAAQUQAAAAGAAAAAQAAAAAAAAABAAAAGZvdjQAAAAAeP///7D///8AAAEFEAAAABgAAAAEAAAAAAAAAAQAAABmb3YzAAAAAKD////Y////AAABBRAAAAAYAAAABAAAAAAAAAAEAAAAZm92MgAAAADI////EAAUAAgABgAHAAwAAAAQABAAAAAAAAEFEAAAABwAAAAEAAAAAAAAAAQAAABmb3YxAAAAAAQABAAEAAAAAAAAAA==": """
properties:
  fov1:
    type: string
  fov2:
    type: string
  fov3:
    type: string
  fov4:
    type: string
required: []
""",
        "/////3AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAUAAAAEAAUAAgABgAHAAwAAAAQABAAAAAAAAEFEAAAABwAAAAEAAAAAAAAAAYAAABpbWFnZXMAAAQABAAEAAAA": """
properties:
  images:
    type: string
required: []
""",
        "/////5gCAAAQAAAAAAAKAA4ABgAFAAgACgAAAAABBAAQAAAAAAAKAAwAAAAEAAgACgAAAPABAAAEAAAAAQAAAAwAAAAIAAwABAAIAAgAAAAIAAAAEAAAAAYAAABwYW5kYXMAALoBAAB7ImluZGV4X2NvbHVtbnMiOiBbeyJraW5kIjogInJhbmdlIiwgIm5hbWUiOiBudWxsLCAic3RhcnQiOiAwLCAic3RvcCI6IDE3LCAic3RlcCI6IDF9XSwgImNvbHVtbl9pbmRleGVzIjogW3sibmFtZSI6IG51bGwsICJmaWVsZF9uYW1lIjogbnVsbCwgInBhbmRhc190eXBlIjogInVuaWNvZGUiLCAibnVtcHlfdHlwZSI6ICJvYmplY3QiLCAibWV0YWRhdGEiOiB7ImVuY29kaW5nIjogIlVURi04In19XSwgImNvbHVtbnMiOiBbeyJuYW1lIjogImlucHV0cyIsICJmaWVsZF9uYW1lIjogImlucHV0cyIsICJwYW5kYXNfdHlwZSI6ICJsaXN0W2Zsb2F0NjRdIiwgIm51bXB5X3R5cGUiOiAib2JqZWN0IiwgIm1ldGFkYXRhIjogbnVsbH1dLCAiY3JlYXRvciI6IHsibGlicmFyeSI6ICJweWFycm93IiwgInZlcnNpb24iOiAiMTQuMC4wIn0sICJwYW5kYXNfdmVyc2lvbiI6ICIyLjIuMCJ9AAABAAAABAAAAND///8AAAEMFAAAACAAAAAEAAAAAQAAACgAAAAGAAAAaW5wdXRzAAAEAAQABAAAABAAFAAIAAYABwAMAAAAEAAQAAAAAAABAxAAAAAcAAAABAAAAAAAAAAEAAAAaXRlbQAABgAIAAYABgAAAAAAAgAAAAAA": """
properties:
  inputs:
    type: array
    items:
      type: number
      format: double
required: []
""",
        "/////+AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAIAAAA0AAAABAAAAJz///8AAAEFEAAAABwAAAAEAAAAAAAAAAQAAAB0ZXh0AAAAAAQABAAEAAAAyP///wAAARAUAAAAJAAAAAQAAAABAAAAMAAAAAkAAABlbWJlZGRpbmcABgAIAAQABgAAAAADAAAQABQACAAGAAcADAAAABAAEAAAAAAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAGAAYAAAAAAAIAAAAAAA==": """
properties:
  embedding:
    type: array
    items:
      type: number
      format: double
    minItems: 768
    maxItems: 768
  text:
    type: string
required: []
""",
        "/////3gAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAUAAAAEAAUAAgABgAHAAwAAAAQABAAAAAAAAEDEAAAABwAAAAEAAAAAAAAAAUAAABpbnB1dAAGAAgABgAGAAAAAAABAAAAAAA=": """
properties:
  input:
    type: number
    format: float
required: []
""",
        "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AAAAAhAAAAAoAAAABAAAAAAAAAAVAAAAUHJpb3IzTW9udGhBbGVydENvdW50AAAA/P3//wAAAAFAAAAASP7//wAAAAMQAAAAKAAAAAQAAAAAAAAAEAAAAFByaW9yUGVyaW9kQWxlcnQAAAYACAAGAAYAAAAAAAIAhP7//wAAAAUQAAAAHAAAAAQAAAAAAAAACQAAAFNlcnZpY2VUbwAAABz///+w/v//AAAABRAAAAAcAAAABAAAAAAAAAALAAAAU2VydmljZUZyb20ASP///9z+//8AAAAFEAAAABwAAAAEAAAAAAAAAAsAAABJbnZvaWNlRGF0ZQB0////CP///wAAAAUQAAAAIAAAAAQAAAAAAAAADwAAAFNlcnZpY2VUeXBlRGVzYwCk////OP///wAAAAIQAAAAGAAAAAQAAAAAAAAABgAAAEJpbGxJZAAAHP///wAAAAFAAAAAaP///wAAAAUQAAAAIAAAAAQAAAAAAAAACwAAAFNlcnZpY2VUeXBlAAQABAAEAAAAmP///wAAAAIQAAAAHAAAAAQAAAAAAAAACQAAAEFjY291bnRJZAAAAID///8AAAABQAAAAMz///8AAAACEAAAABwAAAAEAAAAAAAAAAoAAABTdXBwbGllcklkAAC0////AAAAAUAAAAAQABQACAAAAAcADAAAABAAEAAAAAAAAAIQAAAALAAAAAQAAAAAAAAAEwAAAFV0aWxpdHlBbGVydERhaWx5SWQACAAMAAgABwAIAAAAAAAAAUAAAAA=": """
properties:
  UtilityAlertDailyId:
    type: integer
    format: int64
  SupplierId:
    type: integer
    format: int64
  AccountId:
    type: integer
    format: int64
  ServiceType:
    type: string
  BillId:
    type: integer
    format: int64
  ServiceTypeDesc:
    type: string
  InvoiceDate:
    type: string
  ServiceFrom:
    type: string
  ServiceTo:
    type: string
  PriorPeriodAlert:
    type: number
    format: double
  Prior3MonthAlertCount:
    type: integer
    format: int64
  Prior3MonthEstimateCount:
    type: integer
    format: int64
  DailyConsumption:
    type: number
    format: double
  LastBillDailyConsumption:
    type: number
    format: double
  PriorYearDailyConsumption:
    type: number
    format: double
  ConsumptionPercentVarPriorPeriod:
    type: number
    format: double
  ConsumptionPercentVarYOY:
    type: number
    format: double
  CurrentCharges:
    type: number
    format: double
  LastBillCurrentCharges:
    type: number
    format: double
  PriorYearCurrentCharges:
    type: number
    format: double
  CurrentChargesVarYOY:
    type: number
    format: double
  CurrentServiceDays:
    type: integer
    format: int64
  PriorBillServiceDays:
    type: number
    format: double
  PriorYearServiceDays:
    type: number
    format: double
  Estimated:
    type: string
  PriorYearCDD:
    type: number
    format: double
  CurrentPrecipitation:
    type: number
    format: double
  AccountType:
    type: string
  OneSiteSiteId:
    type: number
    format: double
  AssetClass:
    type: string
  NumOfBuildings:
    type: number
    format: double
  TotalUnits:
    type: number
    format: double
  TotalSqFt:
    type: number
    format: double
  YearBuilt:
    type: number
    format: double
  NumOfStories:
    type: number
    format: double
  ClimateRegion:
    type: string
  PropertyType:
    type: string
  AssetType:
    type: string
  CommunityType:
    type: string
  MarketSegment:
    type: string
required:
- UtilityAlertDailyId
- SupplierId
- AccountId
- ServiceType
- BillId
- ServiceTypeDesc
- InvoiceDate
- ServiceFrom
- ServiceTo
- PriorPeriodAlert
- Prior3MonthAlertCount
- Prior3MonthEstimateCount
- DailyConsumption
- LastBillDailyConsumption
- PriorYearDailyConsumption
- ConsumptionPercentVarPriorPeriod
- ConsumptionPercentVarYOY
- CurrentCharges
- LastBillCurrentCharges
- PriorYearCurrentCharges
- CurrentChargesVarYOY
- CurrentServiceDays
- PriorBillServiceDays
- PriorYearServiceDays
- Estimated
- PriorYearCDD
- CurrentPrecipitation
- AccountType
- OneSiteSiteId
- AssetClass
- NumOfBuildings
- TotalUnits
- TotalSqFt
- YearBuilt
- NumOfStories
- ClimateRegion
- PropertyType
- AssetType
- CommunityType
- MarketSegment
""",
        "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:": """
properties:
  tradelines_dataRepositoryType:
    type: array
    items:
      type: string
  tradelines_recordType:
    type: array
    items:
      type: string
  tradelines_tradelineDate:
    type: array
    items:
      type: string
  tradelines_scoreTypeCode:
    type: array
    items:
      type: string
  tradelines_creditLoanType:
    type: array
    items:
      type: string
  tradelines_businessType:
    type: array
    items:
      type: string
  tradelines_monthlyPaymentAmount:
    type: array
    items:
      type: integer
      format: int64
  tradelines_accountStatusType:
    type: array
    items:
      type: string
  tradelines_accountType:
    type: array
    items:
      type: string
  tradelines_unpaidBalanceAmount:
    type: array
    items:
      type: integer
      format: int64
  tradelines_creditLimit:
    type: array
    items:
      type: integer
      format: int64
  tradelines_createDate:
    type: array
    items:
      type: string
  ficoScore_creditScore:
    type: integer
    format: int64
  rentalHistory_onTimeFeeCount:
    type: integer
    format: int64
  rentalHistory_lateFeeCount:
    type: integer
    format: int64
  rentalHistory_avgDaysBehind:
    type: integer
    format: int64
  rentalHistory_averageRent:
    type: integer
    format: int64
  rentalHistory_badLeaseOutcomeCount:
    type: integer
    format: int64
  income_applicantIncome:
    type: integer
    format: int64
  example_1:
    type: integer
    format: int64
  example_2:
    type: integer
    format: int64
  example_3:
    type: integer
    format: int64
  example_4:
    type: integer
    format: int64
  example_5:
    type: string
required: []
""",
        "/////3ABAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAYAAAAAAASABgACAAGAAcADAAAABAAFAASAAAAAAABEBgAAADIAAAACAAAABgAAAABAAAA0AAAAAYAAABpbWFnZXMAAAIAAABYAAAABAAAALj///8IAAAAIAAAABQAAABBUlJPVzpleHRlbnNpb246bmFtZQAAAAAYAAAAYXJyb3cuZml4ZWRfc2hhcGVfdGVuc29yAAAAAAgADAAEAAgACAAAAAgAAAAkAAAAGAAAAEFSUk9XOmV4dGVuc2lvbjptZXRhZGF0YQAAAAATAAAAeyJzaGFwZSI6WzMsMzIsMzJdfQAAAAYACAAEAAYAAAAADAAAEAAUAAgABgAHAAwAAAAQABAAAAAAAAECEAAAACAAAAAEAAAAAAAAAAQAAABpdGVtAAAAAAgADAAIAAcACAAAAAAAAAFAAAAAAAAAAA==": """
properties:
  images:
    type: array
    items:
      type: array
      items:
        type: array
        items:
          type: integer
          format: int64
        minItems: 32
        maxItems: 32
      minItems: 32
      maxItems: 32
    minItems: 3
    maxItems: 3
    x-arrow-extension:
      name: arrow.fixed_shape_tensor
      dtype: int64
      shape:
      - 3
      - 32
      - 32
required: []
""",
        "/////wgBAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAEAAAAbP///wAAARAUAAAAHAAAAAQAAAABAAAAGAAAAAUAAABpbnB1dAAAAKL///8DAAAAnP///wAAARAUAAAAHAAAAAQAAAABAAAAGAAAAAQAAABpdGVtAAAAANL///8AAQAAzP///wAAARAUAAAAIAAAAAQAAAABAAAALAAAAAQAAABpdGVtAAAGAAgABAAGAAAAAAEAABAAFAAIAAYABwAMAAAAEAAQAAAAAAABAxAAAAAcAAAABAAAAAAAAAAEAAAAaXRlbQAABgAIAAYABgAAAAAAAQA=": """
properties:
  input:
    type: array
    items:
      type: array
      items:
        type: array
        items:
          type: number
          format: float
        minItems: 256
        maxItems: 256
      minItems: 256
      maxItems: 256
    minItems: 3
    maxItems: 3
required: []
""",
        "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": """
properties:
  this_is_wrong:
    type: integer
    format: int64
  SupplierId:
    type: integer
    format: int64
  AccountId:
    type: integer
    format: int64
  ServiceType:
    type: string
  BillId:
    type: integer
    format: int64
  ServiceTypeDesc:
    type: string
  InvoiceDate:
    type: string
  ServiceFrom:
    type: string
  ServiceTo:
    type: string
  PriorPeriodAlert:
    type: number
    format: double
  Prior3MonthAlertCount:
    type: integer
    format: int64
  Prior3MonthEstimateCount:
    type: integer
    format: int64
  DailyConsumption:
    type: number
    format: double
  LastBillDailyConsumption:
    type: number
    format: double
  PriorYearDailyConsumption:
    type: number
    format: double
  ConsumptionPercentVarPriorPeriod:
    type: number
    format: double
  ConsumptionPercentVarYOY:
    type: number
    format: double
  CurrentCharges:
    type: number
    format: double
  LastBillCurrentCharges:
    type: number
    format: double
  PriorYearCurrentCharges:
    type: number
    format: double
  CurrentChargesVarYOY:
    type: number
    format: double
  CurrentServiceDays:
    type: integer
    format: int64
  PriorBillServiceDays:
    type: number
    format: double
  PriorYearServiceDays:
    type: number
    format: double
  Estimated:
    type: string
  PriorYearCDD:
    type: number
    format: double
  CurrentPrecipitation:
    type: number
    format: double
  AccountType:
    type: string
  OneSiteSiteId:
    type: number
    format: double
  AssetClass:
    type: string
  NumOfBuildings:
    type: number
    format: double
  TotalUnits:
    type: number
    format: double
  TotalSqFt:
    type: number
    format: double
  YearBuilt:
    type: number
    format: double
  NumOfStories:
    type: number
    format: double
  ClimateRegion:
    type: string
  PropertyType:
    type: string
  AssetType:
    type: string
  CommunityType:
    type: string
  MarketSegment:
    type: string
required:
- this_is_wrong
- SupplierId
- AccountId
- ServiceType
- BillId
- ServiceTypeDesc
- InvoiceDate
- ServiceFrom
- ServiceTo
- PriorPeriodAlert
- Prior3MonthAlertCount
- Prior3MonthEstimateCount
- DailyConsumption
- LastBillDailyConsumption
- PriorYearDailyConsumption
- ConsumptionPercentVarPriorPeriod
- ConsumptionPercentVarYOY
- CurrentCharges
- LastBillCurrentCharges
- PriorYearCurrentCharges
- CurrentChargesVarYOY
- CurrentServiceDays
- PriorBillServiceDays
- PriorYearServiceDays
- Estimated
- PriorYearCDD
- CurrentPrecipitation
- AccountType
- OneSiteSiteId
- AssetClass
- NumOfBuildings
- TotalUnits
- TotalSqFt
- YearBuilt
- NumOfStories
- ClimateRegion
- PropertyType
- AssetType
- CommunityType
- MarketSegment
""",
        "/////xgBAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAQAAAC8AAAAfAAAAEgAAAAEAAAAZP///wAAAQYQAAAAMAAAAAQAAAAAAAAAHAAAAGNsZWFuX3VwX3Rva2VuaXphdGlvbl9zcGFjZXMAAAAAbP///6T///8AAAEGEAAAACAAAAAEAAAAAAAAAA4AAAByZXR1cm5fdGVuc29ycwAAnP///9T///8AAAEGEAAAABwAAAAEAAAAAAAAAAsAAAByZXR1cm5fdGV4dADI////EAAUAAgABgAHAAwAAAAQABAAAAAAAAEFEAAAABwAAAAEAAAAAAAAAAYAAABpbnB1dHMAAAQABAAEAAAA": """
properties:
  inputs:
    type: string
  return_text:
    type: boolean
  return_tensors:
    type: boolean
  clean_up_tokenization_spaces:
    type: boolean
required: []
""",
        "/////9ABAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAUAAAAsAQAA0AAAAHQAAAA4AAAABAAAALj+//8AAAECEAAAABgAAAAEAAAAAAAAAAQAAABkaW0xAAAAAND///8AAAABQAAAAOj+//8AAAECEAAAACAAAAAEAAAAAAAAAAQAAABkaW0wAAAAAAgADAAIAAcACAAAAAAAAAFAAAAAIP///wAAAQwUAAAAHAAAAAQAAAABAAAAFAAAAAYAAABhcnJheTMAAFD///9M////AAABAxAAAAAYAAAABAAAAAAAAAAEAAAAaXRlbQAAAAA+////AAABAHj///8AAAEMFAAAABwAAAAEAAAAAQAAABQAAAAGAAAAYXJyYXkyAACo////pP///wAAAQMQAAAAGAAAAAQAAAAAAAAABAAAAGl0ZW0AAAAAlv///wAAAQDQ////AAABDBQAAAAgAAAABAAAAAEAAAAoAAAABgAAAGFycmF5MQAABAAEAAQAAAAQABQACAAGAAcADAAAABAAEAAAAAAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAGAAYAAAAAAAEAAAAAAA==": """
properties:
  array1:
    type: array
    items:
      type: number
      format: float
  array2:
    type: array
    items:
      type: number
      format: float
  array3:
    type: array
    items:
      type: number
      format: float
  dim0:
    type: integer
    format: int64
  dim1:
    type: integer
    format: int64
required: []
""",
        "/////xABAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAIAAABkAAAABAAAAGz///8AAAEQFAAAABwAAAAEAAAAAQAAABgAAAAHAAAAaW5wdXRfMgCi////BQAAAJz///8AAAEDEAAAABgAAAAEAAAAAAAAAAQAAABpdGVtAAAAAI7///8AAAIAyP///wAAARAUAAAAJAAAAAQAAAABAAAAMAAAAAcAAABpbnB1dF8xAAAABgAIAAQABgAAAAoAAAAQABQACAAGAAcADAAAABAAEAAAAAAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAGAAYAAAAAAAIAAAAAAA==": """
properties:
  input_1:
    type: array
    items:
      type: number
      format: double
    minItems: 10
    maxItems: 10
  input_2:
    type: array
    items:
      type: number
      format: double
    minItems: 5
    maxItems: 5
required: []
""",
        "/////2gDAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAMAAAAYAgAABAEAAAQAAAAG/v//AAABEBgAAAC8AAAACAAAABgAAAABAAAAtAAAAAYAAABhcnJheTMAAAIAAABQAAAABAAAAKz9//8oAAAABAAAABgAAABhcnJvdy5maXhlZF9zaGFwZV90ZW5zb3IAAAAAFAAAAEFSUk9XOmV4dGVuc2lvbjpuYW1lAAAAAPT9//8kAAAABAAAABYAAAB7InNoYXBlIjpbMTAwMDAsMTAwMF19AAAYAAAAQVJST1c6ZXh0ZW5zaW9uOm1ldGFkYXRhAAAAAO79//+AlpgA6P3//wAAAQMQAAAAGAAAAAQAAAAAAAAABAAAAGl0ZW0AAAAA2v3//wAAAQAC////AAABEBgAAAC8AAAACAAAABgAAAABAAAAtAAAAAYAAABhcnJheTIAAAIAAABQAAAABAAAAKj+//8oAAAABAAAABgAAABhcnJvdy5maXhlZF9zaGFwZV90ZW5zb3IAAAAAFAAAAEFSUk9XOmV4dGVuc2lvbjpuYW1lAAAAAPD+//8kAAAABAAAABYAAAB7InNoYXBlIjpbMTAwMDAsMTAwMF19AAAYAAAAQVJST1c6ZXh0ZW5zaW9uOm1ldGFkYXRhAAAAAOr+//+AlpgA5P7//wAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYABgAEAAYAAAABABIAGAAIAAYABwAMAAAAEAAUABIAAAAAAAEQGAAAAMgAAAAIAAAAGAAAAAEAAADQAAAABgAAAGFycmF5MQAAAgAAAFgAAAAEAAAAuP///ygAAAAEAAAAGAAAAGFycm93LmZpeGVkX3NoYXBlX3RlbnNvcgAAAAAUAAAAQVJST1c6ZXh0ZW5zaW9uOm5hbWUAAAAACAAMAAQACAAIAAAAJAAAAAQAAAAWAAAAeyJzaGFwZSI6WzEwMDAwLDEwMDBdfQAAGAAAAEFSUk9XOmV4dGVuc2lvbjptZXRhZGF0YQAABgAIAAQABgAAAICWmAAQABQACAAGAAcADAAAABAAEAAAAAAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAGAAYAAAAAAAEAAAAAAA==": """
properties:
  array1:
    type: array
    items:
      type: array
      items:
        type: number
        format: float
      minItems: 1000
      maxItems: 1000
    minItems: 10000
    maxItems: 10000
    x-arrow-extension:
      name: arrow.fixed_shape_tensor
      dtype: float
      shape:
      - 10000
      - 1000
  array2:
    type: array
    items:
      type: array
      items:
        type: number
        format: float
      minItems: 1000
      maxItems: 1000
    minItems: 10000
    maxItems: 10000
    x-arrow-extension:
      name: arrow.fixed_shape_tensor
      dtype: float
      shape:
      - 10000
      - 1000
  array3:
    type: array
    items:
      type: array
      items:
        type: number
        format: float
      minItems: 1000
      maxItems: 1000
    minItems: 10000
    maxItems: 10000
    x-arrow-extension:
      name: arrow.fixed_shape_tensor
      dtype: float
      shape:
      - 10000
      - 1000
required: []
""",
        "/////7AAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAEAAAAyP///wAAARAUAAAAJAAAAAQAAAABAAAAMAAAAAYAAABvdXRwdXQAAAAABgAIAAQABgAAACAAAAAQABQACAAGAAcADAAAABAAEAAAAAAAAQMQAAAAHAAAAAQAAAAAAAAABAAAAGl0ZW0AAAYACAAGAAYAAAAAAAEAAAAAAA==": """
properties:
  output:
    type: array
    items:
      type: number
      format: float
    minItems: 32
    maxItems: 32
required: []
""",
        "/////xABAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAQAAAC0AAAAdAAAADgAAAAEAAAAbP///wAAAQUQAAAAIAAAAAQAAAAAAAAADgAAAGdlbmVyYXRlZF90ZXh0AABk////nP///wAAAQMQAAAAJAAAAAQAAAAAAAAACgAAAGNvbmZpZGVuY2UAAAAABgAIAAYABgAAAAAAAQDU////AAABBRAAAAAcAAAABAAAAAAAAAAJAAAAcmVhc29uaW5nAAAAyP///xAAFAAIAAYABwAMAAAAEAAQAAAAAAABBhAAAAAcAAAABAAAAAAAAAAHAAAAaGFybWZ1bAAEAAQABAAAAA==": """
properties:
  harmful:
    type: boolean
  reasoning:
    type: string
  confidence:
    type: number
    format: float
  generated_text:
    type: string
required: []
""",
        "/////6gAAAAQAAAAAAAKAAwABgAFAAgACgAAAAABBAAMAAAACAAIAAAABAAIAAAABAAAAAEAAAAEAAAAzP///wAAAQwUAAAAJAAAAAQAAAABAAAALAAAAAoAAABwcmVkaWN0aW9uAAAEAAQABAAAABAAFAAIAAYABwAMAAAAEAAQAAAAAAABAxAAAAAcAAAABAAAAAAAAAAEAAAAaXRlbQAABgAIAAYABgAAAAAAAgA=": """
properties:
  prediction:
    type: array
    items:
      type: number
      format: double
required: []
""",
    }

    # Generate additional test cases with known schemas
    additional_test_cases = [
        # Simple integer field
        (
            pa.schema([pa.field("test", pa.int32())]),
            """properties:
  test:
    type: integer
    format: int32
required: []""",
        ),
        # Array of floats
        (
            pa.schema([pa.field("prediction", pa.list_(pa.float64()))]),
            """properties:
  prediction:
    type: array
    items:
      type: number
      format: double
required: []""",
        ),
        # Array of integers
        (
            pa.schema([pa.field("classes", pa.list_(pa.int64()))]),
            """properties:
  classes:
    type: array
    items:
      type: integer
      format: int64
required: []""",
        ),
        # Nested array structure
        (
            pa.schema([pa.field("image", pa.list_(pa.list_(pa.int32())))]),
            """properties:
  image:
    type: array
    items:
      type: array
      items:
        type: integer
        format: int32
required: []""",
        ),
        # Multiple fields
        (
            pa.schema(
                [
                    pa.field("boxes", pa.list_(pa.float32())),
                    pa.field("classes", pa.list_(pa.int64())),
                    pa.field("confidences", pa.list_(pa.float32())),
                ]
            ),
            """properties:
  boxes:
    type: array
    items:
      type: number
      format: float
  classes:
    type: array
    items:
      type: integer
      format: int64
  confidences:
    type: array
    items:
      type: number
      format: float
required: []""",
        ),
    ]

    # Test the base64-encoded case
    for base64_schema, expected_yaml in test_cases.items():
        # Decode the base64-encoded Arrow schema
        schema = decode_arrow_schema_from_base64(base64_schema)

        # Generate OpenAPI YAML from the schema
        result_yaml = arrow_schema_to_openapi_yaml(schema)

        # Compare the result with expected output (strip whitespace for comparison)
        assert (
            result_yaml.strip() == expected_yaml.strip()
        ), f"Schema test failed for: {base64_schema[:50]}..."

    # Test the generated schemas
    for schema, expected_yaml in additional_test_cases:
        # Generate OpenAPI YAML from the schema
        result_yaml = arrow_schema_to_openapi_yaml(schema)

        # Compare the result with expected output (strip whitespace for comparison)
        assert (
            result_yaml.strip() == expected_yaml.strip()
        ), f"Schema test failed for schema: {schema}"


def test_arrow_schema_to_openapi_yaml_with_indent():
    """Test arrow_schema_to_openapi_yaml function with custom indentation."""

    # Simple test schema
    schema = pa.schema([pa.field("test_field", pa.string())])

    # Test with default indent (0)
    result_no_indent = arrow_schema_to_openapi_yaml(schema, indent=0)
    assert "properties:" in result_no_indent
    assert result_no_indent.startswith("properties:")

    # Test with custom indent (2)
    result_indent = arrow_schema_to_openapi_yaml(schema, indent=2)
    # The indentation should be applied to all lines except the first one
    lines = result_indent.split("\n")
    # First line should not be indented, subsequent lines should be
    assert (
        lines[0] == "properties:"
    ), f"First line should not be indented, got: '{lines[0]}'"
    for i, line in enumerate(lines[1:], 1):
        if line.strip():  # Skip empty lines
            assert line.startswith(
                "  "
            ), f"Line {i+1} should be indented, got: '{line}'"


def test_arrow_schema_to_openapi_yaml_with_prepend_props():
    """Test arrow_schema_to_openapi_yaml function with prepend_props parameter."""

    # Simple test schema
    schema = pa.schema([pa.field("test_field", pa.string())])

    # Test with prepend_props
    result = arrow_schema_to_openapi_yaml(schema, prepend_props="prefix.")
    assert "prefix.test_field:" in result
    # When prepend_props is used, the original field name should not appear as a top-level key
    lines = result.split("\n")
    field_lines = [line for line in lines if "test_field:" in line]
    assert len(field_lines) == 1, f"Expected exactly one field line, got: {field_lines}"
    assert (
        field_lines[0].strip().startswith("prefix.test_field:")
    ), f"Expected prefixed field name, got: {field_lines[0]}"


def test_arrow_schema_to_openapi_yaml_empty_schema():
    """Test arrow_schema_to_openapi_yaml function with empty schema."""

    # Empty schema
    schema = pa.schema([])

    result = arrow_schema_to_openapi_yaml(schema)
    expected = """properties: {}
required: []"""

    assert result.strip() == expected.strip()


def test_arrow_schema_to_openapi_yaml_required_fields():
    """Test arrow_schema_to_openapi_yaml function with required fields."""

    # Schema with required and optional fields
    schema = pa.schema(
        [
            pa.field("required_field", pa.string(), nullable=False),
            pa.field("optional_field", pa.string(), nullable=True),
        ]
    )

    result = arrow_schema_to_openapi_yaml(schema)

    # Should include required field in required list
    assert "required:" in result
    assert "required_field" in result
    # Optional field should not be in required list
    assert (
        "optional_field" not in result
        or "optional_field" not in result.split("required:")[1]
    )
