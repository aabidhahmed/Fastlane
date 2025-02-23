from django import forms

class InventorySearchForm(forms.Form):
    query = forms.CharField(label='Search Inventory', max_length=255, required=False)
