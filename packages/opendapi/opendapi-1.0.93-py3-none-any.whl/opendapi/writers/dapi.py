"""Dapi Writer"""

from typing import Optional

from opendapi.utils import has_underlying_model_changed
from opendapi.validators.defs import CollectedFile
from opendapi.writers.base import BaseFileWriter


class DapiFileWriter(BaseFileWriter):
    """Writer for Dapi files"""

    @staticmethod
    def _should_process_file(
        collected_file: CollectedFile, base_collected_file: Optional[CollectedFile]
    ) -> bool:  # pylint: disable=unused-argument
        """
        determine if there were material changes requiring the file to be processed

        This is necessary for organic onboarding, since otherwise features being on will
        always lead to Dapis being autoupdated, since more will be returned from
        base_template_for_autoupdate, and the content will have changed, regardless of if
        the model was updated organically

        NOTE: To work properly, needs base_collected_files - otherwise the fallback is to always
              autoupdate, which is safest, but noisiest
        """

        # the model was deleted, a write would just be the same as the original
        if not collected_file.generated:
            return False

        # neither the model nor the file existed at base,
        # so we do process
        if not base_collected_file:
            return True

        # if we ever had a file written then it was onboarded
        was_onboarded = base_collected_file.original or collected_file.original

        return (
            # the generated output allows us to compare the ORM state
            has_underlying_model_changed(
                collected_file.generated, base_collected_file.generated
            )
            # If the ORM state is the same, someone could have still edited the file manually,
            # and we need to make sure that they did it in a valid way. We therefore compare
            # the file state now versus the ORM state now, but we note that we must allow
            # for nullability changes (i.e. from the portal), as those are valid. Merged
            # uses the nullability changes from the portal, but also reflects the current
            # ORM state, and so we compare against that
            or (
                was_onboarded
                and has_underlying_model_changed(
                    collected_file.merged, collected_file.original
                )
            )
        )
