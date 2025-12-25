from formset.collection import BaseFormCollection, FormCollectionMeta


class StepperCollectionMeta(FormCollectionMeta):
    def __new__(cls, *args, **kwargs):
        new_class = super().__new__(cls, *args, **kwargs)
        for holder in new_class.declared_holders.values():
            setattr(holder, 'induce_activate', getattr(holder, 'induce_activate', None))
            setattr(holder, 'step_label', getattr(holder, 'step_label', ''))
        return new_class


class StepperCollection(BaseFormCollection, metaclass=StepperCollectionMeta):
    template_name = 'formset/default/stepper_collection.html'

    def iter_many(self):
        raise NotImplementedError("StepperCollection can not be used with siblings")

    def render(self, template_name=None, context=None, renderer=None):
        context = context or {}
        return super().render(template_name, context, renderer)

    __str__ = render
    __html__ = render
