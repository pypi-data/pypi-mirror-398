# SecurityChecksResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** |  | 
**function_name** | **str** |  | 
**name** | **str** |  | 
**vuln_class** | [**VulnerabilityType**](VulnerabilityType.md) |  | 
**description** | **str** |  | 
**remediation** | **str** |  | 
**confidence** | [**ConfidenceType**](ConfidenceType.md) |  | 
**severity** | [**SeverityType**](SeverityType.md) |  | 

## Example

```python
from revengai.models.security_checks_result import SecurityChecksResult

# TODO update the JSON string below
json = "{}"
# create an instance of SecurityChecksResult from a JSON string
security_checks_result_instance = SecurityChecksResult.from_json(json)
# print the JSON string representation of the object
print(SecurityChecksResult.to_json())

# convert the object into a dict
security_checks_result_dict = security_checks_result_instance.to_dict()
# create an instance of SecurityChecksResult from a dict
security_checks_result_from_dict = SecurityChecksResult.from_dict(security_checks_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


