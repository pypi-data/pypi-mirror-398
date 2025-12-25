from typing import Annotated, Any, Optional, Union
import funcnodes as fn
from pydantic import BaseModel, Field

class Person(BaseModel):
    name: str = Field(description="The name of the person")
    age: int = Field(description="The age of the person")
    email: str = Field(description="The email of the person")

@fn.NodeDecorator(node_id="person_node", node_name="Person Node")
def person_node(person: Annotated[Optional[Union[Person, dict]], fn.InputMeta(name="person", description="The person", render_options={"type": "json_schema","schema":Person.model_json_schema()})] = None,node: fn.Node = None	) -> Person:
    if person is None:
        person = Person(name="John Doe", age=30, email="john.doe@example.com")
        if node:
            node.inputs["person"].set_value(person,does_trigger=False)
    else:
        person = Person.model_validate(person)
    return person

@fn.NodeDecorator(node_id="person_node2", node_name="Person Node 2")
def person_node2(person: Annotated[Union[Person, dict], fn.InputMeta(name="person", description="The person", render_options={"type": "json_schema","schema":Person.model_json_schema()})]) -> Person:
    return Person.model_validate(person)

NODE_SHELF = fn.Shelf(name="demo", description="Demo nodes", nodes=[person_node, person_node2], subshelves=[])