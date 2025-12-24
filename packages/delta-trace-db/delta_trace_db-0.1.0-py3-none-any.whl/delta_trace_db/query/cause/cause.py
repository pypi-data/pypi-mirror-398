# coding: utf-8
from typing import Optional, Dict, Any, override
from file_state_manager.cloneable_file import CloneableFile
from delta_trace_db.db.util_copy import UtilCopy
from delta_trace_db.query.cause.actor import Actor
from delta_trace_db.query.cause.temporal_trace.temporal_trace import TemporalTrace


class Cause(CloneableFile):
    class_name = "Cause"
    version = "1"

    def __init__(self, who: Actor, when: TemporalTrace, what: str, why: str, from_: str, serial: Optional[str] = None,
                 chain_parent_serial: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                 confidence_score: float = 1.0):
        """
        (en) A class for entering a description of a query.
        If you write this class accurately, you can log queries and
        trace a nearly complete history of database operations.
        It is recommended to include this class in queries in cases with
        high security requirements.

        (ja) クエリに関する説明を入力するためのクラスです。
        このクラスを正確に記述する場合、クエリをログとして保存することで、
        データベース操作のほぼ完全な歴史を辿ることが可能になります。
        高度なセキュリティ要件があるケースではこのクラスをクエリに含めることをお勧めします。

        Parameters
        ----------
        serial: Optional[str]
            A unique identifier assigned to this operation.
        chain_parent_serial: Optional[str]
            The serial of the previous Cause, in case this operation is a chain operation.
        who: Actor
            Information about the person who performed the operation.
        when: TemporalTrace
            The "time trail" of the event.
        what: str
            An explanation of this inquiry, i.e., what kind of operation it is.
            Example: Obtaining data for a specified period on screen A.
        why: str
            An explanation of why this inquiry is being made.
            Example: Correcting a user's input error.
        from_: str
            An explanation of where the inquiry is coming from.
            Example: From mobile app A.
        context: Optional[Dict[str, Any]]
            Other more detailed information.
        confidence_score: float
            A degree of confidence expressed as 0.0 to 1.0.
            When correcting an error, this indicates the degree of confidence that
            the data entered or overwritten is correct.
            Especially in the case of automatic operation by AI,
            the AI's confidence level is entered here.
            In the case of human operation, 1.0 is always entered.
        """
        super().__init__()
        self.serial = serial
        self.chain_parent_serial = chain_parent_serial
        self.who = who
        self.when = when
        self.what = what
        self.why = why
        self.from_ = from_
        self.context = context
        self.confidence_score = confidence_score

    @classmethod
    def from_dict(cls, src: Dict[str, Any]) -> "Cause":
        return cls(
            serial=src.get("serial"),
            chain_parent_serial=src.get("chainParentSerial"),
            who=Actor.from_dict(src["who"]),
            when=TemporalTrace.from_dict(src["when"]),
            what=src["what"],
            why=src["why"],
            from_=src["from"],
            context=src.get("context"),
            confidence_score=src.get("confidenceScore", 1.0),
        )

    @override
    def clone(self) -> "Cause":
        return Cause.from_dict(self.to_dict())

    @override
    def to_dict(self) -> Dict[str, Any]:
        return {
            "className": self.class_name,
            "version": self.version,
            "serial": self.serial,
            "chainParentSerial": self.chain_parent_serial,
            "who": self.who.to_dict(),
            "when": self.when.to_dict(),
            "what": self.what,
            "why": self.why,
            "from": self.from_,
            "context": UtilCopy.jsonable_deep_copy(self.context),
            "confidenceScore": self.confidence_score,
        }
