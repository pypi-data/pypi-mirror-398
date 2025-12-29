# Vulnerabilities


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**vulnerabilities** | [**List[Vulnerability]**](Vulnerability.md) |  | 

## Example

```python
from revengai.models.vulnerabilities import Vulnerabilities

# TODO update the JSON string below
json = "{}"
# create an instance of Vulnerabilities from a JSON string
vulnerabilities_instance = Vulnerabilities.from_json(json)
# print the JSON string representation of the object
print(Vulnerabilities.to_json())

# convert the object into a dict
vulnerabilities_dict = vulnerabilities_instance.to_dict()
# create an instance of Vulnerabilities from a dict
vulnerabilities_from_dict = Vulnerabilities.from_dict(vulnerabilities_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


