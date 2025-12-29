# AnalysisCreateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**filename** | **str** | The name of the file | 
**sha_256_hash** | **str** | The name of the file | 
**tags** | [**List[Tag]**](Tag.md) | List of community tags to assign to an analysis | [optional] [default to []]
**analysis_scope** | [**AnalysisScope**](AnalysisScope.md) | The scope of the analysis determines who can access it | [optional] 
**symbols** | [**Symbols**](Symbols.md) |  | [optional] 
**debug_hash** | **str** |  | [optional] 
**analysis_config** | [**AnalysisConfig**](AnalysisConfig.md) | The analysis config enables the configuration of optional analysis stages | [optional] 
**binary_config** | [**BinaryConfig**](BinaryConfig.md) | The binary config can override automatically determined values such as ISA, Platform, File Format, etc | [optional] 

## Example

```python
from revengai.models.analysis_create_request import AnalysisCreateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisCreateRequest from a JSON string
analysis_create_request_instance = AnalysisCreateRequest.from_json(json)
# print the JSON string representation of the object
print(AnalysisCreateRequest.to_json())

# convert the object into a dict
analysis_create_request_dict = analysis_create_request_instance.to_dict()
# create an instance of AnalysisCreateRequest from a dict
analysis_create_request_from_dict = AnalysisCreateRequest.from_dict(analysis_create_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


