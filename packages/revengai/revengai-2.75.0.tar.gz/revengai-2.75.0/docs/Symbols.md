# Symbols


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**base_address** | **int** | The starting address of the execution | 
**function_boundaries** | [**List[FunctionBoundary]**](FunctionBoundary.md) | List of user defined function boundaries | [optional] [default to []]

## Example

```python
from revengai.models.symbols import Symbols

# TODO update the JSON string below
json = "{}"
# create an instance of Symbols from a JSON string
symbols_instance = Symbols.from_json(json)
# print the JSON string representation of the object
print(Symbols.to_json())

# convert the object into a dict
symbols_dict = symbols_instance.to_dict()
# create an instance of Symbols from a dict
symbols_from_dict = Symbols.from_dict(symbols_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


