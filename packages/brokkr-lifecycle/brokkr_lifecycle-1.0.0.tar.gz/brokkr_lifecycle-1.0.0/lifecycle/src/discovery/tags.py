import logging
import os
from dataclasses import dataclass, field

import pynetbox

logger = logging.getLogger(__name__)


@dataclass
class Tags:
    netbox: pynetbox.api
    device: object
    ids: list[int] = field(default_factory=list)

    def __post_init__(self) -> list[int]:
        logger.warning(f"Entering {os.path.basename(__file__)} class")

        # Compile list of the tag names
        tag_names = ["Compute"]

        if self.device:
            existing_tags = [tag.name for tag in self.device.tags if tag.name not in tag_names]
            if existing_tags:
                tag_names.extend(existing_tags)

        # Iterate through the list of tags, fetching their IDs and appending the id list
        for tag in tag_names:
            try:
                # Look up tag using pynetbox API
                tag_obj = self.netbox.extras.tags.get(name=tag)
                if tag_obj:
                    self.ids.append(tag_obj.id)
                else:
                    logger.warning(f"Tag {tag} not found in NetBox")
            except Exception as e:
                logger.error(f"Error retrieving {tag} tag data: {str(e)}")

        if self.ids:
            logger.info(f"Tag IDs located: {self.ids}")
        else:
            logger.warning("No Tags located")
