# SecurityChecksResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_id** | **int** |  | 
**total_results** | **int** |  | 
**results** | [**List[SecurityChecksResult]**](SecurityChecksResult.md) |  | 

## Example

```python
from revengai.models.security_checks_response import SecurityChecksResponse

# TODO update the JSON string below
json = "{}"
# create an instance of SecurityChecksResponse from a JSON string
security_checks_response_instance = SecurityChecksResponse.from_json(json)
# print the JSON string representation of the object
print(SecurityChecksResponse.to_json())

# convert the object into a dict
security_checks_response_dict = security_checks_response_instance.to_dict()
# create an instance of SecurityChecksResponse from a dict
security_checks_response_from_dict = SecurityChecksResponse.from_dict(security_checks_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


