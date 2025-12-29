# CommunityMatchPercentages


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_name** | **str** |  | 
**binary_id** | **int** |  | 
**matched_communities_percent** | **float** |  | 
**unmatched_communities_percent** | **float** |  | 

## Example

```python
from revengai.models.community_match_percentages import CommunityMatchPercentages

# TODO update the JSON string below
json = "{}"
# create an instance of CommunityMatchPercentages from a JSON string
community_match_percentages_instance = CommunityMatchPercentages.from_json(json)
# print the JSON string representation of the object
print(CommunityMatchPercentages.to_json())

# convert the object into a dict
community_match_percentages_dict = community_match_percentages_instance.to_dict()
# create an instance of CommunityMatchPercentages from a dict
community_match_percentages_from_dict = CommunityMatchPercentages.from_dict(community_match_percentages_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


