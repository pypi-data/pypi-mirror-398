from typing import Any, Callable, Concatenate, ParamSpec, TypeVar

from .assets import *  # noqa: F403
from .classes import *  # noqa: F403
from .definitions import *  # noqa: F403
from .fields import *  # noqa: F403
from .modules import *  # noqa: F403
from .project import *  # noqa: F403
from .queries import *  # noqa: F403
from .records import *  # noqa: F403

ReturnType = TypeVar("WrapReturnType")
ParamsType = ParamSpec("WrapRemainingParameters")


class UnicatMutate:
    def __init__(self, unicat):
        self._unicat = unicat

        self.add_language = self._wrap(add_language)  # noqa: F405
        self.remove_language = self._wrap(remove_language)  # noqa: F405
        self.create_channel = self._wrap(create_channel)  # noqa: F405
        self.delete_channel = self._wrap(delete_channel)  # noqa: F405
        self.create_ordering = self._wrap(create_ordering)  # noqa: F405
        self.delete_ordering = self._wrap(delete_ordering)  # noqa: F405
        self.create_fieldlist = self._wrap(create_fieldlist)  # noqa: F405
        self.delete_fieldlist = self._wrap(delete_fieldlist)  # noqa: F405

        self.create_definition = self._wrap(create_definition)  # noqa: F405
        self.modify_definition = self._wrap(modify_definition)  # noqa: F405
        self.modify_definition_modify_layout = self._wrap(
            modify_definition_modify_layout  # noqa: F405
        )
        self.modify_definition_add_class = self._wrap(
            modify_definition_add_class  # noqa: F405
        )
        self.modify_definition_remove_class = self._wrap(
            modify_definition_remove_class  # noqa: F405
        )
        self.modify_definition_add_field = self._wrap(
            modify_definition_add_field  # noqa: F405
        )
        self.modify_definition_remove_field = self._wrap(
            modify_definition_remove_field  # noqa: F405
        )
        self.modify_definition_fieldlist_add_field = self._wrap(
            modify_definition_fieldlist_add_field  # noqa: F405
        )
        self.modify_definition_fieldlist_remove_field = self._wrap(
            modify_definition_fieldlist_remove_field  # noqa: F405
        )
        self.modify_definition_add_childdefinition = self._wrap(
            modify_definition_add_childdefinition  # noqa: F405
        )
        self.modify_definition_remove_childdefinition = self._wrap(
            modify_definition_remove_childdefinition  # noqa: F405
        )
        self.modify_definition_set_metadata = self._wrap(
            modify_definition_set_metadata  # noqa: F405
        )
        self.modify_definition_clear_metadata = self._wrap(
            modify_definition_clear_metadata  # noqa: F405
        )
        self.commit_definition = self._wrap(commit_definition)  # noqa: F405
        self.save_as_new_definition = self._wrap(save_as_new_definition)  # noqa: F405
        self.delete_definition = self._wrap(delete_definition)  # noqa: F405

        self.create_class = self._wrap(create_class)  # noqa: F405
        self.modify_class = self._wrap(modify_class)  # noqa: F405
        self.modify_class_modify_layout = self._wrap(
            modify_class_modify_layout  # noqa: F405
        )
        self.modify_class_add_field = self._wrap(modify_class_add_field)  # noqa: F405
        self.modify_class_remove_field = self._wrap(
            modify_class_remove_field  # noqa: F405
        )
        self.modify_class_set_metadata = self._wrap(
            modify_class_set_metadata  # noqa: F405
        )
        self.modify_class_clear_metadata = self._wrap(
            modify_class_clear_metadata  # noqa: F405
        )
        self.commit_class = self._wrap(commit_class)  # noqa: F405
        self.save_as_new_class = self._wrap(save_as_new_class)  # noqa: F405
        self.delete_class = self._wrap(delete_class)  # noqa: F405

        self.create_field = self._wrap(create_field)  # noqa: F405
        self.modify_field = self._wrap(modify_field)  # noqa: F405
        self.modify_field_set_metadata = self._wrap(
            modify_field_set_metadata  # noqa: F405
        )
        self.modify_field_clear_metadata = self._wrap(
            modify_field_clear_metadata  # noqa: F405
        )
        self.commit_field = self._wrap(commit_field)  # noqa: F405
        self.save_as_new_field = self._wrap(save_as_new_field)  # noqa: F405
        self.delete_field = self._wrap(delete_field)  # noqa: F405

        self.create_record = self._wrap(create_record)  # noqa: F405
        self.set_record_definition = self._wrap(set_record_definition)  # noqa: F405
        self.extend_record_definition_add_class = self._wrap(
            extend_record_definition_add_class  # noqa: F405
        )
        self.extend_record_definition_add_field = self._wrap(
            extend_record_definition_add_field  # noqa: F405
        )
        self.extend_record_definition_add_fieldlist_field = self._wrap(
            extend_record_definition_add_fieldlist_field  # noqa: F405
        )
        self.extend_record_definition_remove_class = self._wrap(
            extend_record_definition_remove_class  # noqa: F405
        )
        self.extend_record_definition_remove_field = self._wrap(
            extend_record_definition_remove_field  # noqa: F405
        )
        self.extend_record_definition_remove_fieldlist_field = self._wrap(
            extend_record_definition_remove_fieldlist_field  # noqa: F405
        )
        self.revert_extended_record_definition = self._wrap(
            revert_extended_record_definition  # noqa: F405
        )
        self.copy_record_definition_to_siblings = self._wrap(
            copy_record_definition_to_siblings  # noqa: F405
        )

        self.update_record = self._wrap(update_record)  # noqa: F405
        self.set_record_channels = self._wrap(set_record_channels)  # noqa: F405
        self.copy_record_channels_from_parent = self._wrap(
            copy_record_channels_from_parent  # noqa: F405
        )
        self.copy_record_channels_down = self._wrap(
            copy_record_channels_down  # noqa: F405
        )
        self.copy_record_channels_up = self._wrap(copy_record_channels_up)  # noqa: F405
        self.set_record_orderings = self._wrap(set_record_orderings)  # noqa: F405
        self.link_record = self._wrap(link_record)  # noqa: F405
        self.delete_record = self._wrap(delete_record)  # noqa: F405
        self.undelete_record = self._wrap(undelete_record)  # noqa: F405
        self.permanent_delete_record = self._wrap(permanent_delete_record)  # noqa: F405

        self.upload_asset = self._wrap(upload_asset)  # noqa: F405
        self.upload_update_asset = self._wrap(upload_update_asset)  # noqa: F405
        self.create_asset = self._wrap(create_asset)  # noqa: F405
        self.update_asset = self._wrap(update_asset)  # noqa: F405
        self.delete_asset = self._wrap(delete_asset)  # noqa: F405
        self.undelete_asset = self._wrap(undelete_asset)  # noqa: F405
        self.permanent_delete_asset = self._wrap(permanent_delete_asset)  # noqa: F405

        self.create_query = self._wrap(create_query)  # noqa: F405
        self.update_query = self._wrap(update_query)  # noqa: F405
        self.delete_query = self._wrap(delete_query)  # noqa: F405

        if self._unicat._features.modules:
            self.register_module = self._wrap(register_module)  # noqa: F405
            self.unregister_module = self._wrap(unregister_module)  # noqa: F405
            self.set_module_key = self._wrap(set_module_key)  # noqa: F405
            self.set_module_keys = self._wrap(set_module_keys)  # noqa: F405
            self.clear_module_key = self._wrap(clear_module_key)  # noqa: F405
            self.clear_module_keys = self._wrap(clear_module_keys)  # noqa: F405
            self.publish_module_action = self._wrap(publish_module_action)  # noqa: F405
            self.unpublish_module_action = self._wrap(unpublish_module_action)  # noqa: F405
            self.add_module_log = self._wrap(add_module_log)  # noqa: F405

        self.create_backup = self._wrap(create_backup)  # noqa: F405
        self.update_backup = self._wrap(update_backup)  # noqa: F405
        self.restore_backup = self._wrap(restore_backup)  # noqa: F405
        self.delete_backup = self._wrap(delete_backup)  # noqa: F405
        self.delete_backups = self._wrap(delete_backups)  # noqa: F405

    def _wrap(
        self,
        function: Callable[Concatenate[Any, ParamsType], ReturnType],
    ) -> Callable[ParamsType, ReturnType]:
        """Transforms an external function to a method on the unicat.mutate property.

        The only requirement is that the external function's first param is a Unicat
        instance - that one is curried, so the signature of the method only has the
        remaining parameters.

        That's basically what the type hints say - they are added so IDE's can show
        tooltips and autocomplete info with the correct parameter info.

        Note: the Unicat instance is typed as Any to avoid circular imports.
        """

        def _inner_function(
            *args: ParamsType.args,
            **kwargs: ParamsType.kwargs,
        ) -> ReturnType:
            return function(self._unicat, *args, **kwargs)

        return _inner_function
