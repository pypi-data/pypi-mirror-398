from gllm_inference.schema.message import Message as Message
from gllm_inference.schema.type_alias import MessageContent as MessageContent

LMInput = list[Message] | list[MessageContent] | str
