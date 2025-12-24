from rdflib import Namespace

CS = Namespace("http://cs-framework.org/schema/")

# Classes
CONCEPT = CS.Concept
SYNCHRONIZATION = CS.Synchronization
ACTION = CS.Action
EVENT = CS.Event
ACTION_INVOCATION = CS.ActionInvocation
COMMAND = CS.Command  # External command for LLM interaction

# Properties
HAS_NAME = CS.hasName
HAS_STATE = CS.hasState
BELONGS_TO = CS.belongsTo
TRIGGERED_BY = CS.triggeredBy
CAUSED_BY = CS.causedBy
INVOKES = CS.invokes
HAS_CONDITION = CS.hasCondition
STATUS = CS.status

# Command-specific properties
HAS_ACTION = CS.hasAction
HAS_TARGET = CS.hasTarget
HAS_PAYLOAD = CS.hasPayload
COMMAND_STATUS = CS.commandStatus  # "pending", "processing", "done", "error"
CREATED_AT = CS.createdAt
PROCESSED_AT = CS.processedAt
ERROR_MESSAGE = CS.errorMessage
