from decimal import Decimal
from django.utils import timezone

class MockModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if not hasattr(self, 'pk'):
            self.pk = kwargs.get('id', 1)
        if not hasattr(self, 'id'):
            self.id = self.pk

    def __str__(self):
        return getattr(self, 'name', str(self.pk))
    
    def save(self, *args, **kwargs):
        pass
    
    def delete(self, *args, **kwargs):
        pass

class MockQuerySet:
    def __init__(self, items=None, model_class=None):
        self.items = items or []
        self.model_class = model_class

    def all(self):
        return self

    def filter(self, **kwargs):
        filtered = self.items
        for k, v in kwargs.items():
            if '__in' in k:
                attr = k.replace('__in', '')
                filtered = [i for i in filtered if getattr(i, attr, None) in v]
            elif '__iexact' in k:
                attr = k.replace('__iexact', '')
                val = getattr(filtered[0], attr, None) if filtered else None
                filtered = [i for i in filtered if str(getattr(i, attr, '')).lower() == str(v).lower()]
            elif '__icontains' in k:
                attr = k.replace('__icontains', '')
                filtered = [i for i in filtered if str(v).lower() in str(getattr(i, attr, '')).lower()]
            else:
                filtered = [i for i in filtered if getattr(i, k, None) == v]
        return MockQuerySet(filtered, self.model_class)

    def exclude(self, **kwargs):
        return self # Simple mock

    def count(self):
        return len(self.items)

    def first(self):
        return self.items[0] if self.items else None

    def last(self):
        return self.items[-1] if self.items else None

    def exists(self):
        return len(self.items) > 0

    def order_by(self, *args):
        return self

    def select_related(self, *args):
        return self

    def prefetch_related(self, *args):
        return self

    def distinct(self):
        return self

    def values(self, *args):
        return self # Simplified

    def values_list(self, *args, **kwargs):
        # Simplified: return a list of values for the first arg
        if args and kwargs.get('flat'):
            return [getattr(i, args[0], None) for i in self.items]
        return self

    def aggregate(self, **kwargs):
        result = {}
        for key, agg in kwargs.items():
            # Very simple mock for Sum
            if 'Sum' in str(agg) or 'total' in key:
                result[key] = sum(getattr(i, 'amount', getattr(i, 'total_amount', Decimal('0'))) for i in self.items)
            else:
                result[key] = 0
        return result

    def __iter__(self):
        return iter(self.items)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return MockQuerySet(self.items[k], self.model_class)
        return self.items[k]

    def __len__(self):
        return len(self.items)

    def __bool__(self):
        return bool(self.items)
