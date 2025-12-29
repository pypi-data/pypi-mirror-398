# BaseResponseVulnerabilities


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**Vulnerabilities**](Vulnerabilities.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_vulnerabilities import BaseResponseVulnerabilities

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseVulnerabilities from a JSON string
base_response_vulnerabilities_instance = BaseResponseVulnerabilities.from_json(json)
# print the JSON string representation of the object
print(BaseResponseVulnerabilities.to_json())

# convert the object into a dict
base_response_vulnerabilities_dict = base_response_vulnerabilities_instance.to_dict()
# create an instance of BaseResponseVulnerabilities from a dict
base_response_vulnerabilities_from_dict = BaseResponseVulnerabilities.from_dict(base_response_vulnerabilities_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


