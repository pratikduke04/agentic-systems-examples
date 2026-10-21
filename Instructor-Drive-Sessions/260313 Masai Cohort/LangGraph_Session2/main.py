from typing import Annotated, Literal, TypedDict  # state and route literals
from operator import add  # trace reducer
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout  # per-call timeout
from dotenv import load_dotenv  # API key
from langchain_core.messages import HumanMessage, SystemMessage  # extract prompt
from langchain_groq import ChatGroq  # Groq extractor model
from langgraph.graph import StateGraph, START, END  # builder
from langgraph.checkpoint.memory import MemorySaver  # lab persistence
from langgraph.types import RetryPolicy, interrupt, Command  # retry + HITL

load_dotenv()  # read GROQ_API_KEY
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)  # Groq extract

class DeskState(TypedDict):  # shared notebook
    request: str  # raw user text
    record_id: str  # extracted id or empty
    amount: int  # extracted amount or 0
    summary: str  # short extract
    lookup: str  # register payload or error
    route: Literal["", "clarify", "ticket", "human"]  # policy decision
    approved: bool  # set only after human resume
    ticket_id: str  # TKT- stamp or empty
    result: str  # user-facing message
    error: str  # fail-closed text
    trace: Annotated[list[str], add]  # append-only node log

DIRECTORY = {"id-104": "OPEN", "id-200": "OPEN"}  # in-memory register
ATTEMPTS = {"n": 0}  # demo counter so lookup fails once then works

def run_with_timeout(fn, seconds: float, *args):  # kitchen timer around I/O
    with ThreadPoolExecutor(max_workers=1) as pool:  # one worker
        future = pool.submit(fn, *args)  # start the call
        return future.result(timeout=seconds)  # raise if too slow

def fake_lookup(record_id: str) -> str:  # register call with one blip
    ATTEMPTS["n"] += 1  # count calls
    if ATTEMPTS["n"] == 1:  # first call in the process
        raise ConnectionError("service busy")  # transient failure for RetryPolicy
    return DIRECTORY.get(record_id, "NOT_FOUND")  # real register result

def extract(state: DeskState) -> dict:  # LLM station: structured fields only
    sys = SystemMessage(  # extract contract
        content=(  # tell the model the output shape
            "Extract record_id (id-NNN or empty), amount (integer, else 0), "  # fields
            "and a five-word summary. Reply as: ID=<id>;AMT=<n>;SUM=<text>"  # parseable line
        )
    )
    raw = llm.invoke([sys, HumanMessage(content=state["request"])]).content  # one call
    record_id, amount, summary = "", 0, raw  # defaults if parse fails
    try:  # best-effort parse of the contract line
        parts = dict(p.split("=", 1) for p in raw.strip().split(";"))  # ID/AMT/SUM
        record_id = parts.get("ID", "").strip()  # may be empty
        amount = int(parts.get("AMT", "0"))  # integer amount
        summary = parts.get("SUM", raw).strip()  # short text
    except (ValueError, KeyError):  # malformed model line
        summary = raw  # keep raw text; policy will clarify if id missing
    if record_id in ("", "empty", "none"):  # normalise empty ids
        record_id = ""  # policy treats empty as clarify
    return {  # partial update
        "record_id": record_id,  # extracted or empty
        "amount": amount,  # extracted or 0
        "summary": summary,  # extract text
        "trace": ["extract"],  # reducer append
    }

def lookup_record(state: DeskState) -> dict:  # tool station with timeout
    if not state["record_id"]:  # nothing to look up
        return {"lookup": "", "trace": ["lookup_record"]}  # skip I/O
    try:  # bounded wait
        payload = run_with_timeout(fake_lookup, 4.0, state["record_id"])  # 4s timer
        return {"lookup": payload, "error": "", "trace": ["lookup_record"]}  # store row
    except FuturesTimeout:  # too slow
        return {  # fail closed
            "lookup": "",  # no guessed row
            "error": "Lookup timed out. Please retry.",  # user-facing
            "trace": ["lookup_record"],  # still record the hop
        }

def policy(state: DeskState) -> dict:  # Python gates — not the model
    if state.get("error"):  # timeout already set a message
        return {"route": "clarify", "result": state["error"], "trace": ["policy"]}
    if not state["record_id"] or state["lookup"] in ("", "NOT_FOUND"):  # missing / unknown
        return {  # cannot ticket
            "route": "clarify",  # blocked path
            "result": "Please resend with a valid record id such as id-104.",  # ask
            "trace": ["policy"],  # hop
        }
    if state["amount"] >= 5000:  # high-risk money
        return {"route": "human", "trace": ["policy"]}  # must pause
    return {"route": "ticket", "trace": ["policy"]}  # auto path

def route_after_policy(state: DeskState) -> str:  # edge router
    return {"clarify": "clarify", "human": "human_approve", "ticket": "create_ticket"}[
        state["route"]
    ]  # map flag to node name

def human_approve(state: DeskState) -> dict:  # planned pause
    decision = interrupt(  # stop; payload is shown to the operator
        {  # inspectable payload
            "record_id": state["record_id"],  # what they are signing
            "amount": state["amount"],  # money at risk
            "summary": state["summary"],  # short extract
            "ask": "Approve ticket? Resume with true or false.",  # operator prompt
        }
    )
    approved = bool(decision)  # resume payload
    if not approved:  # supervisor said no
        return {  # reject path
            "approved": False,  # stamp
            "result": "Request rejected by reviewer.",  # user message
            "trace": ["human_approve"],  # hop
        }
    return {"approved": True, "trace": ["human_approve"]}  # continue to ticket

def after_human(state: DeskState) -> str:  # edge after the stamp
    if state.get("approved"):  # only a true stamp
        return "create_ticket"  # allowed to stamp a ticket
    return "clarify"  # reuse clarify/END path via result already set

def create_ticket(state: DeskState) -> dict:  # stamp — never invent without a route
    tid = "TKT-" + state["record_id"].replace("id-", "")  # deterministic id
    return {  # success payload
        "ticket_id": tid,  # visible stamp
        "result": "Ticket " + tid + " created.",  # user message
        "trace": ["create_ticket"],  # hop
    }

def clarify(state: DeskState) -> dict:  # terminal helper if result already set
    msg = state["result"] or "Please resend with a valid record id."  # fallback
    return {"result": msg, "trace": ["clarify"]}  # ensure result exists

builder = StateGraph(DeskState)  # shell
builder.add_node("extract", extract)  # LLM
builder.add_node(  # lookup with bounded retries
    "lookup_record",  # name
    lookup_record,  # function
    retry_policy=RetryPolicy(max_attempts=3, initial_interval=0.5, backoff_factor=2.0),  # blip
)
builder.add_node("policy", policy)  # Python gates
builder.add_node("human_approve", human_approve)  # interrupt
builder.add_node("create_ticket", create_ticket)  # stamp
builder.add_node("clarify", clarify)  # blocked terminal
builder.add_edge(START, "extract")  # always extract first
builder.add_edge("extract", "lookup_record")  # then register
builder.add_edge("lookup_record", "policy")  # then gates
builder.add_conditional_edges("policy", route_after_policy)  # three-way
builder.add_conditional_edges(  # after human
    "human_approve",  # from interrupt node
    after_human,  # approved → ticket else clarify
)
builder.add_edge("create_ticket", END)  # success ends
builder.add_edge("clarify", END)  # blocked ends
desk = builder.compile(checkpointer=MemorySaver())  # persist + HITL

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "demo-1"}}

    out = desk.invoke({"request": "Refund 7000 for id-104, laptop broke",
                       "record_id": "", "amount": 0, "summary": "", "lookup": "",
                       "route": "", "approved": False, "ticket_id": "",
                       "result": "", "error": "", "trace": []}, config)

    if "__interrupt__" in out:
        info = out["__interrupt__"][0].value
        print("\n--- APPROVAL NEEDED ---")
        print(f"Record : {info['record_id']}")
        print(f"Amount : {info['amount']}")
        print(f"Summary: {info['summary']}")

        answer = input(info["ask"].replace("true or false", "y or n") + " ").strip().lower()
        decision = answer in ("y", "yes", "true")

        out = desk.invoke(Command(resume=decision), config)  # same thread_id

    print("\nResult:", out["result"])
    print("Trace :", out["trace"])