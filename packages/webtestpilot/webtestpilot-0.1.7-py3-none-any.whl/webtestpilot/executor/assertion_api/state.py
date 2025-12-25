from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from baml_py import Image, ClientRegistry, Collector
from xml.etree.ElementTree import Element as XMLElement

from webtestpilot.baml_client.sync_client import b
from webtestpilot.baml_client.type_builder import TypeBuilder
from webtestpilot.baml_client.types import ExtractedData
from webtestpilot.executor.assertion_api.pydantic_schema import build_from_pydantic
from webtestpilot.executor.assertion_api.type_utils import convert_extracted_data


if TYPE_CHECKING:
    from webtestpilot.executor.assertion_api.session import Session
    from webtestpilot.executor.assertion_api.element import Element


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class State:
    page_id: str
    description: str
    layout: str

    url: str
    title: str
    content: str
    screenshot: str
    elements: dict[int, "Element"]
    prev_action: Optional[str]

    xml_tree: list[XMLElement]

    _cr_assertion_api: ClientRegistry
    _collector: Collector

    def extract(self, instruction: str, schema: ExtractedData) -> ExtractedData:
        """
        Extract structured data from the state using a schema.

        Args:
            instruction (str):
                A natural language description of the information to extract.
                Example: `"get product detail"` or `"extract cart summary"`.
            schema (ExtractedData):
                A BaseModel class, primitive type, or collection type defining the expected output.

        Returns:
            ExtractedData:
                An instance of the provided `schema` type containing validated extracted data.

        Example:
            >>> class Product(BaseModel):
            ...     title: str
            ...     price: float
            ...
            >>> data = session.extract("get product detail", schema=Product)
            >>> text = session.extract("get visible text", schema=str)
            >>> items = session.extract("get all items", schema=list)
            >>> data
            {'title': 'Sample Item', 'price': 9.99}
        """
        tb = TypeBuilder()
        field_type = build_from_pydantic(schema, tb)
        tb.Output.add_property("schema", field_type)
        # TODO: Check BAML if possible to dynamic type both @@ and others.

        screenshot = Image.from_base64("image/png", self.screenshot)
        output = b.ExtractFromState(
            screenshot,
            instruction,
            baml_options={
                "tb": tb,
                "client_registry": self._cr_assertion_api,
                "collector": self._collector,
            },
        )
        data = convert_extracted_data(schema, output)
        logger.info(f"Extracted data: {data}")
        return data


class StateFactory:
    def __init__(self, session: "Session"):
        self.assertion_api: ClientRegistry = session.config.assertion_api
        self.collector: Collector = session.collector

    def create(
        self,
        page_id: str,
        description: str,
        layout: str,
        url: str,
        title: str,
        content: str,
        screenshot: str,
        elements: dict[int, "Element"],
        prev_action: Optional[str] = None,
        xml_tree: Optional[list[XMLElement]] = None,
    ) -> State:
        xml_tree = xml_tree if xml_tree is not None else []
        return State(
            page_id=page_id,
            description=description,
            layout=layout,
            url=url,
            title=title,
            content=content,
            screenshot=screenshot,
            elements=elements,
            prev_action=prev_action,
            xml_tree=xml_tree,
            _cr_assertion_api=self.assertion_api,
            _collector=self.collector,
        )
