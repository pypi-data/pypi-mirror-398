from typing import Dict, List, Iterator, Tuple
import copy
import os
import numpy as np
import cv2
from functools import reduce
from tqdm import tqdm

from blueness import module
from bluer_options.logger import log_list
from bluer_objects import file
from bluer_objects import README
from bluer_objects.README.consts import assets_path, assets_url
from bluer_objects.logger.image import log_image_grid

from bluer_sbc.host import signature
from bluer_sbc import NAME
from bluer_sbc.parts.classes.part import Part
from bluer_sbc.logger import logger

NAME = module.name(__file__, NAME)


class PartDB:
    def __init__(self):
        self._db: Dict[str, Part] = {}

        suffix = "bluer-sbc/parts"
        self.url_prefix = assets_url(
            suffix=suffix,
            volume=2,
        )
        self.path = assets_path(
            suffix=suffix,
            volume=2,
        )

    def __iter__(self):
        return iter(self._db.values())

    def __setitem__(
        self,
        name: str,
        part: Part,
    ):
        assert isinstance(part, Part)

        self._db[name] = copy.deepcopy(part)
        self._db[name].name = name

    def __getitem__(self, name: str) -> Part:
        return self._db[name]

    def items(self) -> Iterator[Tuple[str, Part]]:
        return self._db.items()

    @property
    def README(self) -> List[str]:
        return sorted(
            [
                "1. [{}](./{}.md).".format(
                    part.info[0],
                    part.name,
                )
                for part in self
            ]
        )

    def adjust(
        self,
        generate_grid: bool = True,
        dryrun: bool = True,
        verbose: bool = False,
    ) -> bool:
        logger.info(
            "{}.adjust{}".format(
                NAME,
                " [dryrun]" if dryrun else "",
            )
        )

        list_of_filenames = reduce(
            lambda x, y: x + y,
            [
                [part.images[0]]
                for part_name, part in self._db.items()
                if part_name != "template" and part.images
            ],
            [],
        )
        log_list(logger, "adjusting", list_of_filenames, "images")

        if generate_grid:
            if not log_image_grid(
                items=[
                    {
                        "filename": os.path.join(self.path, part.images[0]),
                        "title": part_name,
                    }
                    for part_name, part in self._db.items()
                    if part_name != "template" and part.images
                ],
                filename=assets_path(
                    suffix="bluer-sbc/parts/grid.png",
                    volume=2,
                ),
                scale=3,
                header=[
                    "{} part(s)".format(len(self._db) - 1),
                ],
                footer=signature(),
            ):
                return False

        max_width = 0
        max_height = 0
        for filename in tqdm(list_of_filenames):
            success, image = file.load_image(
                os.path.join(self.path, filename),
                log=verbose,
            )
            if not success:
                return success

            max_height = max(max_height, image.shape[0])
            max_width = max(max_width, image.shape[1])

        logger.info(f"size: {max_height} x {max_width}")

        for filename in tqdm(list_of_filenames):
            success, image = file.load_image(
                os.path.join(self.path, filename),
                log=verbose,
            )
            if not success:
                return success

            if image.shape[0] == max_height and image.shape[1] == max_width:
                logger.info("✅")
                continue

            image = image[:, :, :3]

            scale = min(
                max_height / image.shape[0],
                max_width / image.shape[1],
            )
            image = cv2.resize(
                image,
                dsize=(
                    int(scale * image.shape[1]),
                    int(scale * image.shape[0]),
                ),
                interpolation=cv2.INTER_LINEAR,
            )

            padded_image = (
                np.ones(
                    (max_height, max_width, 3),
                    dtype=np.uint8,
                )
                * 255
            )

            y_offset = (max_height - image.shape[0]) // 2
            x_offset = (max_width - image.shape[1]) // 2

            padded_image[
                y_offset : y_offset + image.shape[0],
                x_offset : x_offset + image.shape[1],
            ] = image

            if not dryrun:
                if not file.save_image(
                    os.path.join(self.path, filename),
                    padded_image,
                    log=verbose,
                ):
                    return False

        return True

    def as_images(
        self,
        dict_of_parts: Dict[str, str],
        reference: str = "../../parts",
    ) -> List[str]:
        return README.Items(
            [
                {
                    "name": self._db[part_name].info[0],
                    "marquee": self._db[part_name].image_url(
                        url_prefix=self.url_prefix
                    ),
                    "description": description,
                    "url": f"{reference}/{part_name}.md",
                }
                for part_name, description in dict_of_parts.items()
            ],
            sort=True,
        )

    def as_list(
        self,
        dict_of_parts: Dict[str, str],
        reference: str = "../../parts",
        log: bool = True,
    ) -> List[str]:
        if log:
            logger.info(
                "{}.as_list: {}".format(
                    self.__class__.__name__,
                    ", ".join(dict_of_parts.keys()),
                )
            )

        for part_name in dict_of_parts:
            if part_name not in self._db:
                logger.error(f"{part_name}: part not found.")
                assert False

        return sorted(
            [
                (
                    "1. [{}]({}){}.".format(
                        self._db[part_name].info[0],
                        f"{reference}/{part_name}.md",
                        ": {}".format(description) if description else "",
                    )
                )
                for part_name, description in dict_of_parts.items()
            ]
        )
