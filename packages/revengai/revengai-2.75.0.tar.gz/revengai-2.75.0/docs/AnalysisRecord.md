# AnalysisRecord


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**analysis_id** | **int** | ID to identify analysis | 
**analysis_scope** | **str** | Scope of the analysis | 
**binary_id** | **int** | ID to identify the binary analyse | 
**model_id** | **int** | ID to identify the model used for analysis | 
**model_name** | **str** | Name of the model used for analysis | 
**status** | **str** | The current status of analysis | 
**creation** | **datetime** | The current status of analysis | 
**is_owner** | **bool** | Whether the current user is the owner of a binary | 
**binary_name** | **str** | The name of the file uploaded | 
**sha_256_hash** | **str** | The hash of the binary | 
**function_boundaries_hash** | **str** | The hash of the function boundaries | 
**binary_size** | **int** | The size of the binary | 
**username** | **str** | The username of the analysis owner | 
**dynamic_execution_status** | [**AppApiRestV2AnalysesEnumsDynamicExecutionStatus**](AppApiRestV2AnalysesEnumsDynamicExecutionStatus.md) |  | [optional] 
**dynamic_execution_task_id** | **int** |  | [optional] 
**base_address** | **int** | The base address of the binary | 

## Example

```python
from revengai.models.analysis_record import AnalysisRecord

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisRecord from a JSON string
analysis_record_instance = AnalysisRecord.from_json(json)
# print the JSON string representation of the object
print(AnalysisRecord.to_json())

# convert the object into a dict
analysis_record_dict = analysis_record_instance.to_dict()
# create an instance of AnalysisRecord from a dict
analysis_record_from_dict = AnalysisRecord.from_dict(analysis_record_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


