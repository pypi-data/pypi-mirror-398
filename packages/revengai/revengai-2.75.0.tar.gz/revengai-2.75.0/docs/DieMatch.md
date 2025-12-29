# DieMatch


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | Canonical name of the matched signature/technology (e.g., &#39;UPX&#39;, &#39;GCC&#39;, &#39;MSVC&#39;). | 
**type** | **str** | Category assigned by DIE for the match (e.g., &#39;compiler&#39;, &#39;packer&#39;, &#39;file&#39;). | 
**display** | **str** | Human-readable description from DIE&#39;s &#39;string&#39; field; suitable for UI/logs, not for parsing. | 
**version** | **str** | Extracted version string when available; may be empty/None if unknown. | 

## Example

```python
from revengai.models.die_match import DieMatch

# TODO update the JSON string below
json = "{}"
# create an instance of DieMatch from a JSON string
die_match_instance = DieMatch.from_json(json)
# print the JSON string representation of the object
print(DieMatch.to_json())

# convert the object into a dict
die_match_dict = die_match_instance.to_dict()
# create an instance of DieMatch from a dict
die_match_from_dict = DieMatch.from_dict(die_match_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


