# Communities


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_functions** | **int** | The total number of matched community functions | 
**total_matched_functions** | **int** | The total number of functions in the binary | 
**direct_community_match_percentages** | [**List[CommunityMatchPercentages]**](CommunityMatchPercentages.md) | The list of directly matched communities | 
**top_components** | **List[Dict[str, object]]** | The top components of the binary | 

## Example

```python
from revengai.models.communities import Communities

# TODO update the JSON string below
json = "{}"
# create an instance of Communities from a JSON string
communities_instance = Communities.from_json(json)
# print the JSON string representation of the object
print(Communities.to_json())

# convert the object into a dict
communities_dict = communities_instance.to_dict()
# create an instance of Communities from a dict
communities_from_dict = Communities.from_dict(communities_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


