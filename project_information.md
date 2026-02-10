Pipeline n8n alternative tool  
---

# **COMPLETE SYSTEM DEFINITION**

## **1\. Pipeline Definition (Configuration)**

{  
  "pipeline\_id": "uuid (auto-generated, immutable)",  
  "pipeline\_name": "string (required)",  
  "pipeline\_description": "string (optional)",  
  "pipeline\_definition\_version": "integer (auto-incremented) \- Increments when: checkpoint added/removed/reordered",  
  "created\_at": "timestamp (auto-generated)",  
  "updated\_at": "timestamp (auto-generated)",  
    
  "checkpoint\_order": \[  
    "checkpoint\_id\_1",  
    "checkpoint\_id\_2",  
    "checkpoint\_id\_3"  
  \],  
    
  "config": {  
    "auto\_advance": "boolean (default: false) \- Auto-start next checkpoint after completion"  
  }  
}

**Pipeline Definition Changes that Create NEW Pipeline (reset to v1 runs):**

* Adding checkpoint  
* Removing checkpoint  
* Reordering checkpoints in `checkpoint_order`

**Changes that DON'T Create New Pipeline (runs continue):**

* Editing checkpoint definition content  
* Changing checkpoint prompts, agents, validation, etc.  
* Changing pipeline name/description  
* Changing `auto_advance` setting

---

## **2\. Checkpoint Definition (Configuration)**

{  
  "checkpoint\_id": "uuid (auto-generated, immutable)",  
  "checkpoint\_name": "string (required)",  
  "checkpoint\_description": "string (required)",  
  "created\_at": "timestamp (auto-generated)",  
  "updated\_at": "timestamp (auto-generated)",  
    
  "dependencies": {  
    "required\_checkpoint\_ids": "array\<uuid\> (optional) \- User responsibility to ensure valid order"  
  },  
    
  "inputs": {  
    "include\_previous\_version": "boolean (required) \- Include previous run's same checkpoint outputs",  
    "include\_checkpoint\_outputs": \[  
      {  
        "checkpoint\_id": "uuid (required) \- Must be from current run version",  
        "artifact\_ids": "array\<uuid\> (optional) \- Specific artifacts, omit for all",  
        "use\_summarization": "boolean (optional, default: false)"  
      }  
    \]  
  },  
    
  "execution": {  
    "mode": "enum (required): 'agentic' | 'script' | 'human\_only'",  
      
    // IF mode \=== 'agentic':  
    "agent\_config": {  
      "creation\_mode": "enum (required): 'meta\_agent' | 'predefined' | 'single'",  
        
      // IF creation\_mode \=== 'meta\_agent':  
      "meta\_agent\_instructions": "string (required)",  
      "max\_agents": "integer (required)",  
        
      // IF creation\_mode \=== 'predefined':  
      "agents": \[  
        {  
          "agent\_id": "uuid (auto-generated)",  
          "name": "string (required)",  
          "role": "string (required)",  
          "system\_prompt": "string (required)",  
          "task\_prompt": "string (required)"  
        }  
      \],  
        
      // IF creation\_mode \=== 'single':  
      "agent": {  
        "name": "string (required)",  
        "system\_prompt": "string (required)",  
        "task\_prompt": "string (required)"  
      },  
        
      // For 'meta\_agent' and 'predefined':  
      "discussion\_mode": "enum (required if multiple): 'sequential' | 'council' | 'parallel' | 'debate'",  
      "max\_turns": "integer (required if multiple)",  
      "show\_conversation": "boolean (required if multiple)",  
        
      // For ALL:  
      "tools": "array\<string\> (optional): \['web\_search', 'code\_execution', 'file\_operations'\]",  
      "model": "string (optional, default: from config.py)"  
    },  
      
    // IF mode \=== 'script':  
    "script\_config": {  
      "script\_path": "string (required)",  
      "entry\_function": "string (optional, default: 'main')",  
      "requires\_user\_input": "boolean (required)",  
      "user\_input\_prompt": "string (required if requires\_user\_input \=== true)",  
      "parameters": "object (optional)"  
    },  
      
    // IF mode \=== 'human\_only':  
    "human\_only\_config": {  
      "instructions": "string (required)",  
      "input\_fields": \[  
        {  
          "field\_id": "uuid (auto-generated)",  
          "name": "string (required)",  
          "type": "enum (required): 'text' | 'number' | 'boolean' | 'file' | 'multiline\_text'",  
          "label": "string (required)",  
          "required": "boolean (required)",  
          "default": "any (optional)",  
          "validation": "string (optional)"  
        }  
      \],  
      "save\_as\_artifact": "boolean (required)",  
      "artifact\_name": "string (required if save\_as\_artifact \=== true)",  
      "artifact\_format": "enum (required if save\_as\_artifact \=== true): 'json' | 'md'"  
    },  
      
    // For ALL modes:  
    "retry\_config": {  
      "max\_auto\_retries": "integer (required, 0-5)",  
      "on\_failure": "enum (required): 'rollback\_checkpoint' | 'pause\_pipeline'",  
      "retry\_delay\_seconds": "integer (optional, default: 5)"  
    },  
      
    "timeout\_config": {  
      "enabled": "boolean (required)",  
      "timeout\_minutes": "integer (required if enabled)",  
      "on\_timeout": "enum (required if enabled): 'rollback\_checkpoint' | 'pause\_pipeline'"  
    }  
  },  
    
  "human\_interaction": {  
    "requires\_approval\_to\_start": "boolean (required)",  
    "requires\_approval\_to\_complete": "boolean (required)",  
    "max\_revision\_iterations": "integer (required) \- After max, checkpoint fails"  
  },  
    
  "output": {  
    "artifacts": \[  
      {  
        "artifact\_id": "uuid (auto-generated)",  
        "name": "string (required) \- Unique within checkpoint",  
        "format": "enum (required): 'json' | 'md' | 'mmd' | 'txt' | 'py' | 'html' | 'csv'",  
        "description": "string (optional)",  
          
        // IF format \=== 'json':  
        "schema": {  
          "type": "object (required)",  
          "properties": "object (required)",  
          "required": "array\<string\> (optional)"  
        },  
          
        // For other formats:  
        "schema": "null or object (optional)"  
      }  
    \],  
      
    "validation": {  
      "enabled": "boolean (required)",  
        
      // IF enabled \=== true:  
      "validation\_mode": "enum (required): 'llm\_schema' | 'llm\_custom' | 'both'",  
        
      // IF validation\_mode \=== 'llm\_schema' or 'both':  
      "schema\_validation\_strictness": "enum (required): 'strict' | 'lenient'",  
        
      // IF validation\_mode \=== 'llm\_custom' or 'both':  
      "custom\_validation\_prompt": "string (required)",  
        
      "on\_validation\_failure": "enum (required): 'retry' | 'ask\_human' | 'fail\_checkpoint'",  
      "max\_validation\_retries": "integer (required) \- Applies to both retry and ask\_human"  
    }  
  },  
    
  "instructions": {  
    "system\_prompt": "string (optional)",  
    "task\_prompt": "string (required for agentic/script)",  
    "examples": \[  
      {  
        "input": "object (optional)",  
        "output": "object (optional)"  
      }  
    \],  
    "injection\_points": {  
      "previous\_version\_context": "enum (required): 'before\_task\_prompt' | 'after\_task\_prompt' | 'before\_system\_prompt'",  
      "checkpoint\_references": "enum (required): 'before\_task\_prompt' | 'after\_task\_prompt'"  
    },  
    "injection\_format": {  
      "include\_file\_paths": "boolean (default: true)",  
      "include\_file\_contents": "boolean (default: true)",  
      "content\_format": "enum (default: 'markdown'): 'markdown' | 'xml' | 'json'"  
    }  
  }  
}

**Key Clarifications:**

* `include_checkpoint_outputs`: References checkpoints from **current run version only**  
* `include_previous_version`: References **same checkpoint from previous run version**  
* Script execution: If `requires_user_input: false`, script runs directly; if `true`, AI asks user first  
* Human intervention: User-defined in prompts (no system-level intervention mechanism)  
* Validation retries: Apply to BOTH `retry` and `ask_human` modes

---

## **3\. Pipeline Run (Runtime State)**

{  
  "run\_id": "uuid (auto-generated, immutable)",  
  "pipeline\_id": "uuid (required)",  
  "run\_version": "integer (auto-incremented) \- v1, v2, v3...",  
  "status": "enum (required): 'not\_started' | 'in\_progress' | 'paused' | 'completed' | 'failed'",  
    
  "current\_checkpoint\_id": "uuid (nullable)",  
  "current\_checkpoint\_position": "integer (nullable) \- Stored at execution creation, immutable",  
    
  "created\_at": "timestamp (auto-generated)",  
  "started\_at": "timestamp (nullable)",  
  "completed\_at": "timestamp (nullable)",  
  "paused\_at": "timestamp (nullable)",  
  "last\_resumed\_at": "timestamp (nullable)",  
    
  "previous\_run\_id": "uuid (nullable) \- References highest valid (non-archived) version",  
  "extends\_from\_run\_version": "integer (nullable)",  
    
  "checkpoint\_execution\_history": \[  
    "execution\_id\_1",  
    "execution\_id\_2"  
  \],  
    
  "rollback\_history": \[  
    "rollback\_event\_id\_1"  
  \],  
    
  "metadata": {  
    "total\_checkpoints": "integer",  
    "completed\_checkpoints": "integer",  
    "failed\_checkpoints": "integer",  
    "paused\_checkpoint\_position": "integer (nullable)"  
  }  
}

**Key Clarifications:**

* `current_checkpoint_position`: Stored when execution starts, never changes (even if pipeline definition updates)  
* `previous_run_id`: Always references highest valid (non-archived) run version  
* After rollback from `completed` → status becomes `in_progress`  
* After run\_level rollback (e.g., v3 → v1), the run continues as the rolled-back version (v1)

---

## **4\. Checkpoint Execution Instance (Runtime State)**

{  
  "execution\_id": "uuid (auto-generated, immutable) \- Same ID across all retry attempts",  
  "run\_id": "uuid (required)",  
  "checkpoint\_id": "uuid (required)",  
  "checkpoint\_position": "integer (required) \- Immutable, set at creation",  
    
  "status": "enum (required): 'pending' | 'waiting\_approval\_to\_start' | 'in\_progress' | 'waiting\_approval\_to\_complete' | 'completed' | 'failed'",  
    
  "created\_at": "timestamp (auto-generated)",  
  "started\_at": "timestamp (nullable)",  
  "completed\_at": "timestamp (nullable)",  
  "failed\_at": "timestamp (nullable)",  
    
  "attempt\_number": "integer (default: 1\) \- Increments with each retry, same execution\_id",  
  "max\_attempts": "integer (from checkpoint retry\_config)",  
    
  "revision\_iteration": "integer (default: 0)",  
  "max\_revision\_iterations": "integer (from checkpoint human\_interaction)",  
    
  "temp\_workspace\_path": "string (auto-generated) \- Persists across retry attempts",  
  "permanent\_output\_path": "string (auto-generated)",  
    
  "execution\_logs": \[  
    {  
      "log\_id": "uuid",  
      "timestamp": "timestamp",  
      "level": "enum: 'info' | 'warning' | 'error'",  
      "message": "string",  
      "details": "object (optional)"  
    }  
  \],  
    
  "agent\_conversation": \[  
    {  
      "message\_id": "uuid",  
      "timestamp": "timestamp",  
      "agent\_name": "string (nullable)",  
      "role": "enum: 'user' | 'assistant' | 'system'",  
      "content": "string"  
    }  
  \],  
    
  "human\_interactions": \[  
    {  
      "interaction\_id": "uuid",  
      "timestamp": "timestamp",  
      "type": "enum: 'approval\_to\_start' | 'approval\_to\_complete' | 'revision\_request' | 'script\_input' | 'validation\_feedback'",  
      "user\_input": "string",  
      "system\_response": "string"  
    }  
  \],  
    
  "artifacts\_generated": \[  
    {  
      "artifact\_id": "uuid (from checkpoint definition)",  
      "artifact\_name": "string",  
      "file\_path": "string",  
      "format": "string",  
      "created\_at": "timestamp",  
      "promoted\_to\_permanent\_at": "timestamp (nullable)",  
      "size\_bytes": "integer",  
      "checksum": "string"  
    }  
  \],  
    
  "error\_details": {  
    "error\_count": "integer (default: 0)",  
    "last\_error": {  
      "timestamp": "timestamp",  
      "error\_type": "string",  
      "error\_message": "string",  
      "stack\_trace": "string"  
    }  
  }  
}

**Key Clarifications:**

* Same `execution_id` across all retry attempts (attempt\_number increments)  
* Temp workspace persists across retries (same execution\_id \= same temp path)  
* Temp workspace deleted only after:  
  * User approves checkpoint completion AND  
  * Next checkpoint starts (or pipeline completes if last checkpoint)  
* Artifact files can be overwritten during retries (intentional, rollback handles archiving)

---

## **5\. Rollback Event (Event Tracking)**

{  
  "rollback\_id": "uuid (auto-generated, immutable)",  
  "created\_at": "timestamp (auto-generated)",  
    
  "rollback\_type": "enum (required): 'checkpoint\_level' | 'run\_level'",  
    
  "source\_run\_id": "uuid (required)",  
  "source\_run\_version": "integer (required)",  
    
  // IF rollback\_type \=== 'checkpoint\_level':  
  "target\_checkpoint\_id": "uuid (required)",  
  "target\_checkpoint\_position": "integer (required)",  
    
  // IF rollback\_type \=== 'run\_level':  
  "target\_run\_id": "uuid (required)",  
  "target\_run\_version": "integer (required)",  
  "target\_checkpoint\_id": "uuid (required)",  
  "target\_checkpoint\_position": "integer (required)",  
    
  "rolled\_back\_items": {  
    "deleted\_runs": \[  
      {  
        "run\_id": "uuid",  
        "run\_version": "integer"  
      }  
    \],  
    "deleted\_checkpoint\_executions": \[  
      {  
        "execution\_id": "uuid",  
        "checkpoint\_id": "uuid",  
        "checkpoint\_name": "string"  
      }  
    \],  
    "archived\_artifacts": \[  
      {  
        "artifact\_id": "uuid",  
        "artifact\_name": "string",  
        "original\_path": "string",  
        "archived\_path": "string",  
        "size\_bytes": "integer"  
      }  
    \]  
  },  
    
  "archive\_location": "string \- .archived/rollback\_{rollback\_id}\_{datetime}/",  
    
  "triggered\_by": "enum: 'user\_request' | 'checkpoint\_failure'",  
  "user\_reason": "string (optional)"  
}

**Key Clarifications:**

* After rollback, files/versions deleted from active system  
* Archived items moved to unique rollback folder (never looked at except for maintenance)  
* If v3 rolled back to v1, "latest version" becomes v1 (v2, v3 no longer exist)  
* Run continues from rollback point with status \= `in_progress`  
* Same artifact filename in different rollback folders \= different rollback events (no conflict)

---

## **6\. Artifact Reference Resolution Logic**

**Rule for `include_checkpoint_outputs`:**

* References checkpoints from **CURRENT run version ONLY**  
* Example: v3 checkpoint 3 referencing checkpoint 2 → uses v3's checkpoint 2 output

**Rule for `include_previous_version`:**

* References **SAME checkpoint from PREVIOUS run version**  
* Example: v3 checkpoint 3 with `include_previous_version: true` → uses v2's checkpoint 3 output

**Complete Example:**

Pipeline has checkpoints: \[0, 1, 2, 3\]

v1 completed all 4 checkpoints  
v2 starts, completes checkpoints 0, 1, 2  
v3 starts from checkpoint 0

When v3 checkpoint 3 executes:  
\- include\_previous\_version: true → Gets v2 checkpoint 3 output  
\- include\_checkpoint\_outputs: \[{checkpoint\_id: "checkpoint\_2"}\] → Gets v3 checkpoint 2 output

If v3 checkpoint 3 tries to reference checkpoint 2 but v3 hasn't run it yet:  
\- ERROR: System fails execution (user responsibility to ensure dependencies)

**After Rollback Example:**

v1, v2, v3 all completed  
Rollback v3 to v1 checkpoint 2 (deletes v2, v3 entirely)

Now "latest version" \= v1  
Starting v4:  
\- previous\_run\_id \= v1's run\_id  
\- extends\_from\_run\_version \= 1  
\- v4 checkpoint 3 with include\_previous\_version → Gets v1 checkpoint 3 output

---

## **7\. File System Structure (Per Pipeline)**

{pipeline\_id}/  
├── .pipeline\_system/  
│   ├── db/  
│   │   └── state.db                           \# SOURCE OF TRUTH  
│   ├── definitions/  
│   │   ├── pipeline.json  
│   │   └── checkpoints/  
│   │       └── {checkpoint\_id}.json  
│   └── logs/  
│       └── system.log  
│  
├── runs/                                      \# CACHE (sync'd from DB)  
│   ├── v1/  
│   │   ├── run\_info.json  
│   │   ├── checkpoint\_0\_{name}/  
│   │   │   └── outputs/  
│   │   │       └── {artifact\_name}\_{artifact\_id}\_v1.{format}  
│   │   ├── checkpoint\_1\_{name}/  
│   │   └── checkpoint\_2\_{name}/  
│   ├── v2/  
│   │   ├── run\_info.json  
│   │   └── ...  
│   └── latest \-\> v2  
│  
├── .temp/  
│   └── exec\_{execution\_id}/                   \# Same ID across retries  
│       ├── workspace/  
│       └── artifacts\_staging/  
│           └── {artifact\_name}\_{artifact\_id}.{format}  
│  
├── .archived/  
│   ├── rollback\_{rollback\_id\_1}\_{datetime}/  
│   │   ├── rollback\_metadata.json  
│   │   └── archived\_data/  
│   │       ├── v3/                            \# Entire deleted run  
│   │       └── v2\_checkpoint\_4/               \# Deleted checkpoint  
│   └── rollback\_{rollback\_id\_2}\_{datetime}/  
│       └── archived\_data/  
│           └── v2/  
│               └── checkpoint\_3/  
│                   └── outputs/  
│                       └── same\_artifact\_v2.json  \# Same name, different rollback  
│  
└── .errored/  
    └── exec\_{execution\_id}\_{datetime}/  
        ├── error\_info.json  
        └── failed\_artifacts/

**Artifact Naming:**

Temp: {artifact\_name}\_{artifact\_id}.{format}  
Permanent: {artifact\_name}\_{artifact\_id}\_v{run\_version}.{format}

Example:  
Temp: business\_objectives\_a1b2c3d4.json  
Permanent: business\_objectives\_a1b2c3d4\_v2.json

**Overwrite Behavior:**

* Retry attempt overwrites temp file → Intentional (same execution)  
* Rollback moves file to archive before deletion → No conflict  
* Different rollback events have different folders → No conflict

**Database vs File System:**

* Database \= Source of truth for all state/metadata  
* File System \= Cache for user access \+ drift detection  
* On startup, system validates DB matches file system  
* If drift detected, DB wins (file system regenerated)

---

## **8\. Temp Workspace Deletion Flow**

Checkpoint execution completes → User approves → CHECKPOINT STATUS: completed  
                                                          ↓  
                        Does next checkpoint exist?  YES → Start next checkpoint  
                                                          ↓  
                                            DELETE temp workspace of previous checkpoint  
                                                          ↓  
                                            NEXT CHECKPOINT STATUS: in\_progress  
                                                            
                        Does next checkpoint exist?  NO → Pipeline complete  
                                                          ↓  
                                            DELETE temp workspace of last checkpoint  
                                                          ↓  
                                            PIPELINE STATUS: completed

---

## **9\. Content Injection Format**

**For checkpoint 3 in v2 with:**

* `include_previous_version: true`  
* `include_checkpoint_outputs: [{checkpoint_id: "checkpoint_1"}]`

**Injected Context:**

\=== PREVIOUS VERSION: Checkpoint 3 from v1 \===  
File: business\_analysis\_def789\_v1.md  
Path: runs/v1/checkpoint\_2\_business\_analysis/outputs/business\_analysis\_def789\_v1.md

Content:  
\`\`\`markdown  
\# Business Analysis  
Key findings from v1...

\=== REFERENCED OUTPUT: Checkpoint 1 from v2 \=== File: requirements\_abc123\_v2.json Path: runs/v2/checkpoint\_0\_requirements/outputs/requirements\_abc123\_v2.json

Content:

{  
  "requirements": \["Feature A", "Feature B"\]  
}

\=== YOUR TASK \=== \[task\_prompt from checkpoint definition\]

\---

\#\# 10\. System Configuration (config.py)

\`\`\`python  
import os  
from dotenv import load\_dotenv

load\_dotenv()

\# API Keys  
ANTHROPIC\_API\_KEY \= os.getenv("ANTHROPIC\_API\_KEY")

\# LLM  
DEFAULT\_MODEL \= "claude-sonnet-4-5-20250929"  
DEFAULT\_MAX\_TOKENS \= 8000  
DEFAULT\_TEMPERATURE \= 0.7

\# Limits  
MAX\_FILE\_SIZE\_MB \= 100  
MAX\_CONTEXT\_LENGTH \= 200000  
MAX\_CHECKPOINT\_TIMEOUT\_MINUTES \= 480  
MAX\_RETRY\_ATTEMPTS \= 5

\# File System  
BASE\_PIPELINES\_PATH \= "./pipelines"  
TEMP\_CLEANUP\_ON\_NEXT\_CHECKPOINT \= True  \# Delete after next checkpoint starts  
ARCHIVE\_RETENTION\_DAYS \= 365  
ERROR\_RETENTION\_DAYS \= 90

\# Execution  
DEFAULT\_RETRY\_DELAY\_SECONDS \= 5

\# Logging  
LOG\_LEVEL \= "INFO"  
LOG\_FILE\_MAX\_SIZE\_MB \= 50  
LOG\_BACKUP\_COUNT \= 5

\# Database  
DB\_TYPE \= "sqlite"  
DB\_POOL\_SIZE \= 5  
DB\_TIMEOUT\_SECONDS \= 30

---

## **11\. Complete State Transitions**

### **Pipeline Run States:**

not\_started → in\_progress → completed  
                ↓              ↑  
            paused ────────────┘  
                ↓  
            failed

After rollback from completed:  
completed → in\_progress (at rollback point)

### **Checkpoint Execution States:**

pending → waiting\_approval\_to\_start → in\_progress → waiting\_approval\_to\_complete → completed  
                                            ↓  
                                    failed (after max retries)  
                                            ↓  
                                    User decides: retry OR rollback

---

---

# **System Documentation \- Mermaid Diagrams**

## **1\. System Architecture Overview**

graph TB  
    subgraph "User Interface Layer"  
        UI\[Web Frontend\]  
    end  
      
    subgraph "Backend Layer"  
        API\[REST API\]  
        PipelineEngine\[Pipeline Orchestrator\]  
        CheckpointEngine\[Checkpoint Executor\]  
        RollbackEngine\[Rollback Manager\]  
        FileManager\[File System Manager\]  
    end  
      
    subgraph "Storage Layer"  
        DB\[(SQLite Database\<br/\>SOURCE OF TRUTH)\]  
        FS\[File System\<br/\>CACHE\]  
    end  
      
    subgraph "External Services"  
        LLM\[Anthropic API\<br/\>Claude\]  
    end  
      
    UI \--\> API  
    API \--\> PipelineEngine  
    API \--\> RollbackEngine  
      
    PipelineEngine \--\> CheckpointEngine  
    PipelineEngine \--\> DB  
      
    CheckpointEngine \--\> FileManager  
    CheckpointEngine \--\> LLM  
    CheckpointEngine \--\> DB  
      
    RollbackEngine \--\> FileManager  
    RollbackEngine \--\> DB  
      
    FileManager \--\> FS  
    FileManager \--\> DB  
      
    DB \-.sync.-\> FS  
      
    style DB fill:\#e1f5ff  
    style FS fill:\#fff4e1  
    style LLM fill:\#ffe1f5

---

## **2\. Pipeline & Checkpoint Relationship**

erDiagram  
    PIPELINE ||--o{ CHECKPOINT\_DEFINITION : contains  
    PIPELINE ||--o{ PIPELINE\_RUN : executes  
    PIPELINE\_RUN ||--o{ CHECKPOINT\_EXECUTION : contains  
    CHECKPOINT\_DEFINITION ||--o{ CHECKPOINT\_EXECUTION : instantiates  
    PIPELINE\_RUN ||--o{ ROLLBACK\_EVENT : "may trigger"  
    CHECKPOINT\_EXECUTION ||--o{ ARTIFACT : generates  
    PIPELINE\_RUN ||--o| PIPELINE\_RUN : "extends from"  
      
    PIPELINE {  
        uuid pipeline\_id PK  
        string pipeline\_name  
        int pipeline\_definition\_version  
        array checkpoint\_order  
        bool auto\_advance  
    }  
      
    CHECKPOINT\_DEFINITION {  
        uuid checkpoint\_id PK  
        string checkpoint\_name  
        enum mode  
        json inputs  
        json execution  
        json human\_interaction  
        json output  
        json instructions  
    }  
      
    PIPELINE\_RUN {  
        uuid run\_id PK  
        uuid pipeline\_id FK  
        int run\_version  
        enum status  
        uuid previous\_run\_id FK  
        uuid current\_checkpoint\_id FK  
    }  
      
    CHECKPOINT\_EXECUTION {  
        uuid execution\_id PK  
        uuid run\_id FK  
        uuid checkpoint\_id FK  
        int checkpoint\_position  
        enum status  
        int attempt\_number  
        string temp\_workspace\_path  
    }  
      
    ROLLBACK\_EVENT {  
        uuid rollback\_id PK  
        uuid source\_run\_id FK  
        enum rollback\_type  
        uuid target\_run\_id FK  
        string archive\_location  
    }  
      
    ARTIFACT {  
        uuid artifact\_id PK  
        uuid execution\_id FK  
        string artifact\_name  
        string file\_path  
        timestamp promoted\_at  
    }

---

## **3\. Pipeline Run Lifecycle**

stateDiagram-v2  
    \[\*\] \--\> not\_started: Pipeline Created  
      
    not\_started \--\> in\_progress: User starts run  
      
    in\_progress \--\> paused: User pauses\<br/\>(between checkpoints)  
    paused \--\> in\_progress: User resumes  
      
    in\_progress \--\> completed: All checkpoints done  
    in\_progress \--\> failed: Checkpoint fails\<br/\>(after max retries)  
      
    completed \--\> in\_progress: Rollback from completed  
    in\_progress \--\> in\_progress: Rollback within run  
      
    completed \--\> \[\*\]  
    failed \--\> \[\*\]  
      
    note right of in\_progress  
        Executing checkpoints  
        sequentially  
    end note  
      
    note right of paused  
        Can only pause  
        between checkpoints  
    end note  
      
    note right of completed  
        Rollback changes  
        status to in\_progress  
    end note

---

## **4\. Checkpoint Execution Lifecycle**

stateDiagram-v2  
    \[\*\] \--\> pending: Execution created  
      
    pending \--\> waiting\_approval\_to\_start: Checkpoint ready  
      
    waiting\_approval\_to\_start \--\> in\_progress: User approves  
    waiting\_approval\_to\_start \--\> pending: User rejects  
      
    in\_progress \--\> in\_progress: Retry attempt\<br/\>(same execution\_id)  
      
    in\_progress \--\> failed: Max retries exceeded  
    in\_progress \--\> waiting\_approval\_to\_complete: Execution successful  
      
    waiting\_approval\_to\_complete \--\> in\_progress: User requests revision  
    waiting\_approval\_to\_complete \--\> failed: Max revisions exceeded  
    waiting\_approval\_to\_complete \--\> completed: User approves  
      
    completed \--\> \[\*\]: Temp → Permanent\<br/\>Next checkpoint starts  
    failed \--\> \[\*\]: Move to .errored/  
      
    note right of in\_progress  
        attempt\_number increments  
        Same execution\_id  
        Same temp workspace  
    end note  
      
    note right of completed  
        Temp deleted when  
        next checkpoint starts  
        (or pipeline completes)  
    end note

---

## **5\. Checkpoint Execution Flow (Detailed)**

flowchart TD  
    Start(\[Checkpoint Execution Starts\]) \--\> CheckMode{Execution\<br/\>Mode?}  
      
    CheckMode \--\>|agentic| AgenticFlow\[Agentic Execution\]  
    CheckMode \--\>|script| ScriptFlow\[Script Execution\]  
    CheckMode \--\>|human\_only| HumanFlow\[Human Input Form\]  
      
    subgraph "Agentic Flow"  
        AgenticFlow \--\> LoadInputs\[Load Referenced Artifacts\<br/\>& Previous Version\]  
        LoadInputs \--\> InjectContext\[Inject into Prompt Context\]  
        InjectContext \--\> CheckCreation{Creation\<br/\>Mode?}  
          
        CheckCreation \--\>|meta\_agent| MetaAgent\[Meta-Agent Creates Agents\]  
        CheckCreation \--\>|predefined| PredefinedAgents\[Load Predefined Agents\]  
        CheckCreation \--\>|single| SingleAgent\[Single Agent\]  
          
        MetaAgent \--\> ExecuteAgents\[Execute Agent Discussion\]  
        PredefinedAgents \--\> ExecuteAgents  
        SingleAgent \--\> ExecuteAgents  
          
        ExecuteAgents \--\> AgentsWrite\[Agents Write to\<br/\>artifacts\_staging/\]  
    end  
      
    subgraph "Script Flow"  
        ScriptFlow \--\> NeedInput{Requires\<br/\>User Input?}  
        NeedInput \--\>|yes| AIAsksUser\[AI Asks User\<br/\>for Script Params\]  
        NeedInput \--\>|no| DirectRun\[Run Script Directly\]  
        AIAsksUser \--\> RunScript\[Execute Script\]  
        DirectRun \--\> RunScript  
        RunScript \--\> ScriptOutput\[Script Writes Output File\]  
    end  
      
    subgraph "Human Flow"  
        HumanFlow \--\> ShowForm\[Display Input Form\]  
        ShowForm \--\> UserFills\[User Fills Form\]  
        UserFills \--\> SaveForm{Save as\<br/\>Artifact?}  
        SaveForm \--\>|yes| FormToArtifact\[Save Form Data as Artifact\]  
        SaveForm \--\>|no| FormDone\[Form Data Only in Metadata\]  
    end  
      
    AgentsWrite \--\> Validate  
    ScriptOutput \--\> Validate  
    FormToArtifact \--\> Validate  
    FormDone \--\> Validate  
      
    Validate{Validation\<br/\>Enabled?} \--\>|yes| RunValidation\[LLM Schema/Custom Validation\]  
    Validate \--\>|no| WaitApproval  
      
    RunValidation \--\> ValidationPass{Validation\<br/\>Passes?}  
    ValidationPass \--\>|yes| WaitApproval\[Wait for Human Approval\]  
    ValidationPass \--\>|no| CheckRetries{Retries\<br/\>Left?}  
      
    CheckRetries \--\>|yes| RetryType{On Failure\<br/\>Action?}  
    CheckRetries \--\>|no| Failed(\[Checkpoint Failed\])  
      
    RetryType \--\>|retry| IncrementAttempt\[Increment attempt\_number\]  
    RetryType \--\>|ask\_human| AskHumanFix\[Ask Human for Fix\]  
      
    IncrementAttempt \--\> AgenticFlow  
    AskHumanFix \--\> MoreRetries{Max\<br/\>Retries?}  
    MoreRetries \--\>|no| AgenticFlow  
    MoreRetries \--\>|yes| Failed  
      
    WaitApproval \--\> UserApproves{User\<br/\>Approves?}  
    UserApproves \--\>|yes| Promote\[Promote Temp → Permanent\]  
    UserApproves \--\>|no| RevisionCheck{Revisions\<br/\>Left?}  
      
    RevisionCheck \--\>|yes| IncrementRevision\[Increment revision\_iteration\]  
    RevisionCheck \--\>|no| Failed  
      
    IncrementRevision \--\> AgenticFlow  
      
    Promote \--\> NextCheckpoint{Next\<br/\>Checkpoint\<br/\>Exists?}  
    NextCheckpoint \--\>|yes| DeleteTemp\[Delete Temp Workspace\]  
    NextCheckpoint \--\>|no| PipelineDone\[Pipeline Complete\]  
      
    DeleteTemp \--\> StartNext\[Start Next Checkpoint\]  
    PipelineDone \--\> DeleteTemp  
      
    StartNext \--\> End(\[Checkpoint Completed\])  
    DeleteTemp \--\> End  
    Failed \--\> MoveToErrored\[Move to .errored/\]  
    MoveToErrored \--\> End  
      
    style Failed fill:\#ffcccc  
    style End fill:\#ccffcc

---

## **6\. Rollback Flow**

flowchart TD  
    Start(\[User Initiates Rollback\]) \--\> RollbackType{Rollback\<br/\>Type?}  
      
    RollbackType \--\>|checkpoint\_level| SameRun\[Rollback within Same Run\]  
    RollbackType \--\>|run\_level| DiffRun\[Rollback to Different Run\]  
      
    subgraph "Checkpoint-Level Rollback"  
        SameRun \--\> IdentifyCP\[Identify Target Checkpoint Position\]  
        IdentifyCP \--\> CalcDelete1\[Calculate: Delete checkpoints\<br/\>AFTER target position\]  
        CalcDelete1 \--\> Example1\["Example: At checkpoint 5,\<br/\>rollback to 2\<br/\>→ Delete 3, 4, 5"\]  
    end  
      
    subgraph "Run-Level Rollback"  
        DiffRun \--\> IdentifyRun\[Identify Target Run & Checkpoint\]  
        IdentifyRun \--\> CalcDelete2\[Calculate: Delete all runs\<br/\>AFTER target run\]  
        CalcDelete2 \--\> Example2\["Example: At v3,\<br/\>rollback to v1 checkpoint 2\<br/\>→ Delete all of v2, v3"\]  
    end  
      
    Example1 \--\> CreateArchive  
    Example2 \--\> CreateArchive  
      
    CreateArchive\[Generate rollback\_id UUID\] \--\> ArchiveFolder\[Create Archive Folder\<br/\>.archived/rollback\_{id}\_{datetime}/\]  
      
    ArchiveFolder \--\> MoveFiles\[Move Deleted Items to Archive\]  
      
    MoveFiles \--\> DeleteDB\[Delete from Database\<br/\>- Runs\<br/\>- Checkpoint Executions\<br/\>- Artifacts metadata\]  
      
    DeleteDB \--\> DeleteFS\[Delete from File System\<br/\>- runs/vX/\<br/\>- .temp/ (if active)\]  
      
    DeleteFS \--\> UpdateRun{Was Run\<br/\>Completed?}  
      
    UpdateRun \--\>|yes| ChangeStatus\[Change Run Status:\<br/\>completed → in\_progress\]  
    UpdateRun \--\>|no| KeepStatus\[Keep Current Status\]  
      
    ChangeStatus \--\> UpdateLatest  
    KeepStatus \--\> UpdateLatest  
      
    UpdateLatest\[Update 'latest' Symlink\<br/\>to New Highest Version\]  
      
    UpdateLatest \--\> LogEvent\[Create Rollback Event Record\]  
      
    LogEvent \--\> Done(\[Rollback Complete\<br/\>System continues from rollback point\])  
      
    style Done fill:\#ccffcc  
      
    note right of CreateArchive  
        Archive is NEVER  
        accessed by system  
        (only for maintenance)  
    end note  
      
    note right of UpdateLatest  
        "Latest version" now points  
        to highest valid (non-archived)  
        version  
    end note

---

## **7\. Artifact Resolution Logic**

flowchart TD  
    Start(\[Checkpoint Needs Input\]) \--\> CheckPrev{include\_previous\_version\<br/\>= true?}  
      
    CheckPrev \--\>|yes| FindPrevRun\[Find Previous Run Version\]  
    CheckPrev \--\>|no| CheckRefs  
      
    FindPrevRun \--\> GetPrevVersion\[Get: previous\_run\_id\<br/\>from current run\]  
    GetPrevVersion \--\> LoadPrevArtifacts\[Load Artifacts from:\<br/\>runs/v{prev}/checkpoint\_{pos}/outputs/\]  
      
    LoadPrevArtifacts \--\> CheckRefs{include\_checkpoint\_outputs\<br/\>exists?}  
      
    CheckRefs \--\>|yes| IterateRefs\[For Each Referenced Checkpoint\]  
    CheckRefs \--\>|no| InjectAll  
      
    IterateRefs \--\> ValidateRef{Referenced Checkpoint\<br/\>Completed in Current Run?}  
      
    ValidateRef \--\>|yes| LoadCurrentArtifacts\[Load Artifacts from:\<br/\>runs/v{current}/checkpoint\_{ref\_pos}/outputs/\]  
    ValidateRef \--\>|no| Error(\[ERROR: Dependency Not Met\<br/\>User Responsibility\])  
      
    LoadCurrentArtifacts \--\> SpecificArtifacts{artifact\_ids\<br/\>specified?}  
      
    SpecificArtifacts \--\>|yes| LoadSpecific\[Load Only Specified Artifacts\]  
    SpecificArtifacts \--\>|no| LoadAll\[Load All Artifacts\]  
      
    LoadSpecific \--\> Summarize{use\_summarization\<br/\>= true?}  
    LoadAll \--\> Summarize  
      
    Summarize \--\>|yes| SummarizeContent\[LLM Summarizes Content\]  
    Summarize \--\>|no| FullContent\[Use Full Content\]  
      
    SummarizeContent \--\> InjectAll  
    FullContent \--\> InjectAll  
      
    InjectAll\[Inject All Loaded Content\<br/\>into Prompt Context\]  
      
    InjectAll \--\> Format\[Format per injection\_points config:\<br/\>- before\_system\_prompt\<br/\>- before\_task\_prompt\<br/\>- after\_task\_prompt\]  
      
    Format \--\> Ready(\[Context Ready for Execution\])  
      
    style Error fill:\#ffcccc  
    style Ready fill:\#ccffcc  
      
    note right of LoadPrevArtifacts  
        Example:  
        v3 checkpoint 2 loads  
        v2 checkpoint 2 outputs  
    end note  
      
    note right of LoadCurrentArtifacts  
        Example:  
        v3 checkpoint 2 loads  
        v3 checkpoint 1 outputs  
    end note

---

## **8\. File System Structure**

graph TB  
    Root\["{pipeline\_id}/"\]  
      
    Root \--\> System\[".pipeline\_system/"\]  
    Root \--\> Runs\["runs/"\]  
    Root \--\> Temp\[".temp/"\]  
    Root \--\> Archived\[".archived/"\]  
    Root \--\> Errored\[".errored/"\]  
      
    subgraph "System Internals (Hidden)"  
        System \--\> DB\["db/state.db\<br/\>\<b\>SOURCE OF TRUTH\</b\>"\]  
        System \--\> Defs\["definitions/\<br/\>- pipeline.json\<br/\>- checkpoints/{id}.json"\]  
        System \--\> Logs\["logs/system.log"\]  
    end  
      
    subgraph "Active Runs (User Visible)"  
        Runs \--\> V1\["v1/\<br/\>run\_info.json"\]  
        Runs \--\> V2\["v2/\<br/\>run\_info.json"\]  
        Runs \--\> Latest\["latest → v2"\]  
          
        V1 \--\> CP0\_V1\["checkpoint\_0\_{name}/\<br/\>outputs/"\]  
        V1 \--\> CP1\_V1\["checkpoint\_1\_{name}/\<br/\>outputs/"\]  
          
        CP0\_V1 \--\> Art1\["artifact\_a1b2\_v1.json"\]  
        CP1\_V1 \--\> Art2\["artifact\_c3d4\_v1.md"\]  
          
        V2 \--\> CP0\_V2\["checkpoint\_0\_{name}/\<br/\>outputs/"\]  
        CP0\_V2 \--\> Art3\["artifact\_a1b2\_v2.json"\]  
    end  
      
    subgraph "Temp Workspace (Hidden)"  
        Temp \--\> ExecTemp\["exec\_{execution\_id}/\<br/\>\<i\>Persists across retries\</i\>"\]  
        ExecTemp \--\> Workspace\["workspace/\<br/\>\<i\>Agent work area\</i\>"\]  
        ExecTemp \--\> Staging\["artifacts\_staging/\<br/\>artifact\_a1b2.json\<br/\>\<i\>Pre-promotion\</i\>"\]  
    end  
      
    subgraph "Archives (Hidden)"  
        Archived \--\> RB1\["rollback\_{uuid\_1}\_{datetime}/\<br/\>rollback\_metadata.json"\]  
        Archived \--\> RB2\["rollback\_{uuid\_2}\_{datetime}/"\]  
          
        RB1 \--\> RBData1\["archived\_data/\<br/\>- v3/\<br/\>- v2\_checkpoint\_4/"\]  
        RB2 \--\> RBData2\["archived\_data/\<br/\>- v2/checkpoint\_3/"\]  
    end  
      
    subgraph "Failed Executions (Hidden)"  
        Errored \--\> Exec1\["exec\_{execution\_id}\_{datetime}/\<br/\>- error\_info.json\<br/\>- error\_logs.txt\<br/\>- failed\_artifacts/"\]  
    end  
      
    style DB fill:\#e1f5ff  
    style Latest fill:\#ccffcc  
    style Staging fill:\#fff4e1

---

## **9\. Checkpoint Definition Structure**

graph TB  
    CheckpointDef\[Checkpoint Definition\]  
      
    CheckpointDef \--\> Meta\[Metadata\]  
    CheckpointDef \--\> Deps\[Dependencies\]  
    CheckpointDef \--\> Inputs\[Inputs\]  
    CheckpointDef \--\> Execution\[Execution\]  
    CheckpointDef \--\> HumanInt\[Human Interaction\]  
    CheckpointDef \--\> Output\[Output\]  
    CheckpointDef \--\> Instructions\[Instructions\]  
      
    Meta \--\> MetaFields\["- checkpoint\_id: uuid\<br/\>- checkpoint\_name: string\<br/\>- checkpoint\_description: string\<br/\>- created\_at: timestamp\<br/\>- updated\_at: timestamp"\]  
      
    Deps \--\> DepsFields\["- required\_checkpoint\_ids: array\<uuid\>"\]  
      
    Inputs \--\> InputsFields\["- include\_previous\_version: bool\<br/\>- include\_checkpoint\_outputs: array"\]  
    InputsFields \--\> RefDetails\["Each reference:\<br/\>- checkpoint\_id\<br/\>- artifact\_ids (optional)\<br/\>- use\_summarization"\]  
      
    Execution \--\> ExecMode{mode}  
    ExecMode \--\>|agentic| AgenticConfig\[agent\_config\]  
    ExecMode \--\>|script| ScriptConfig\[script\_config\]  
    ExecMode \--\>|human\_only| HumanConfig\[human\_only\_config\]  
      
    AgenticConfig \--\> CreationMode{creation\_mode}  
    CreationMode \--\>|meta\_agent| MetaFields\["- meta\_agent\_instructions\<br/\>- max\_agents\<br/\>- discussion\_mode\<br/\>- max\_turns\<br/\>- show\_conversation"\]  
    CreationMode \--\>|predefined| PredefFields\["- agents: array\<br/\>  \- agent\_id\<br/\>  \- name, role\<br/\>  \- system\_prompt\<br/\>  \- task\_prompt\<br/\>- discussion\_mode\<br/\>- max\_turns\<br/\>- show\_conversation"\]  
    CreationMode \--\>|single| SingleFields\["- agent:\<br/\>  \- name\<br/\>  \- system\_prompt\<br/\>  \- task\_prompt"\]  
      
    AgenticConfig \--\> CommonAgent\["Common:\<br/\>- tools: array\<br/\>- model: string"\]  
      
    ScriptConfig \--\> ScriptFields\["- script\_path: string\<br/\>- entry\_function: string\<br/\>- requires\_user\_input: bool\<br/\>- user\_input\_prompt: string\<br/\>- parameters: object"\]  
      
    HumanConfig \--\> HumanFields\["- instructions: string\<br/\>- input\_fields: array\<br/\>  \- field\_id, name, type\<br/\>  \- label, required\<br/\>  \- default, validation\<br/\>- save\_as\_artifact: bool\<br/\>- artifact\_name: string\<br/\>- artifact\_format: enum"\]  
      
    Execution \--\> RetryConfig\["retry\_config:\<br/\>- max\_auto\_retries\<br/\>- on\_failure\<br/\>- retry\_delay\_seconds"\]  
      
    Execution \--\> TimeoutConfig\["timeout\_config:\<br/\>- enabled\<br/\>- timeout\_minutes\<br/\>- on\_timeout"\]  
      
    HumanInt \--\> HumanIntFields\["- requires\_approval\_to\_start: bool\<br/\>- requires\_approval\_to\_complete: bool\<br/\>- max\_revision\_iterations: int"\]  
      
    Output \--\> Artifacts\["artifacts: array"\]  
    Artifacts \--\> ArtifactFields\["Each artifact:\<br/\>- artifact\_id: uuid\<br/\>- name: string\<br/\>- format: enum\<br/\>- description: string\<br/\>- schema: object (for json)"\]  
      
    Output \--\> Validation\["validation:\<br/\>- enabled: bool\<br/\>- validation\_mode: enum\<br/\>- schema\_validation\_strictness\<br/\>- custom\_validation\_prompt\<br/\>- on\_validation\_failure\<br/\>- max\_validation\_retries"\]  
      
    Instructions \--\> InstFields\["- system\_prompt: string\<br/\>- task\_prompt: string\<br/\>- examples: array\<br/\>- injection\_points:\<br/\>  \- previous\_version\_context\<br/\>  \- checkpoint\_references\<br/\>- injection\_format:\<br/\>  \- include\_file\_paths\<br/\>  \- include\_file\_contents\<br/\>  \- content\_format"\]  
      
    style CheckpointDef fill:\#e1f5ff  
    style ExecMode fill:\#fff4e1  
    style CreationMode fill:\#ffe1f5

---

## **10\. Version Extension Flow**

sequenceDiagram  
    participant User  
    participant System  
    participant DB  
    participant FS as File System  
      
    User-\>\>System: Start New Run (v2)  
    System-\>\>DB: Query: Get latest valid run  
    DB--\>\>System: Returns v1 (run\_id, run\_version)  
      
    System-\>\>DB: Create Pipeline Run v2  
    Note over DB: run\_id: new UUID\<br/\>run\_version: 2\<br/\>previous\_run\_id: v1's UUID\<br/\>extends\_from\_run\_version: 1  
      
    System-\>\>FS: Create runs/v2/ directory  
    System-\>\>FS: Update latest symlink → v2  
      
    User-\>\>System: Start Checkpoint 0  
    System-\>\>DB: Create Checkpoint Execution  
    System-\>\>FS: Create .temp/exec\_{id}/  
      
    Note over System: Load Previous Version?  
    System-\>\>FS: Read runs/v1/checkpoint\_0/outputs/\*  
    Note over System: Load Referenced Checkpoints?\<br/\>(None for checkpoint 0\)  
      
    System-\>\>System: Inject context into prompt  
    System-\>\>System: Execute checkpoint  
    System-\>\>FS: Write to .temp/exec\_{id}/artifacts\_staging/  
      
    User-\>\>System: Approve checkpoint 0  
    System-\>\>FS: Move artifacts\_staging → runs/v2/checkpoint\_0/outputs/  
    Note over FS: Files named: artifact\_v2.json  
      
    System-\>\>DB: Update execution status: completed  
      
    User-\>\>System: Start Checkpoint 1  
    System-\>\>FS: Delete .temp/exec\_{prev\_id}/  
    System-\>\>DB: Create new Checkpoint Execution  
    System-\>\>FS: Create .temp/exec\_{new\_id}/  
      
    Note over System: Load Previous Version?  
    System-\>\>FS: Read runs/v1/checkpoint\_1/outputs/\*  
    Note over System: Load Referenced Checkpoints?  
    System-\>\>FS: Read runs/v2/checkpoint\_0/outputs/\*  
      
    System-\>\>System: Execute checkpoint 1...  
      
    Note over User,FS: Process continues for all checkpoints...  
      
    User-\>\>System: Complete all checkpoints  
    System-\>\>DB: Update run status: completed  
    System-\>\>FS: Delete last temp workspace  
      
    Note over System: v2 now becomes "latest valid version"\<br/\>Future v3 will extend from v2

---

## **11\. Retry Mechanism Flow**

sequenceDiagram  
    participant System  
    participant Checkpoint as Checkpoint Executor  
    participant LLM  
    participant FS as File System  
    participant DB  
      
    System-\>\>DB: Create Checkpoint Execution  
    Note over DB: execution\_id: abc-123\<br/\>attempt\_number: 1  
      
    System-\>\>FS: Create .temp/exec\_abc-123/  
      
    Checkpoint-\>\>LLM: Execute attempt 1  
    LLM--\>\>Checkpoint: Execution fails  
      
    Checkpoint-\>\>Checkpoint: Check: retries left?  
    Note over Checkpoint: max\_auto\_retries: 2\<br/\>attempt\_number: 1\<br/\>→ YES, retry  
      
    Checkpoint-\>\>DB: Update: attempt\_number \= 2  
    Note over DB: SAME execution\_id: abc-123\<br/\>attempt\_number: 2  
      
    Note over FS: SAME temp workspace:\<br/\>.temp/exec\_abc-123/\<br/\>(files may be overwritten)  
      
    Checkpoint-\>\>LLM: Execute attempt 2  
    LLM--\>\>Checkpoint: Execution fails again  
      
    Checkpoint-\>\>Checkpoint: Check: retries left?  
    Note over Checkpoint: max\_auto\_retries: 2\<br/\>attempt\_number: 2\<br/\>→ YES, retry  
      
    Checkpoint-\>\>DB: Update: attempt\_number \= 3  
      
    Checkpoint-\>\>LLM: Execute attempt 3  
    LLM--\>\>Checkpoint: Success\!  
      
    Checkpoint-\>\>FS: Write to artifacts\_staging/  
    Checkpoint-\>\>System: Request human approval  
      
    alt User Approves  
        System-\>\>FS: Promote: artifacts\_staging/ → outputs/  
        System-\>\>DB: Update: status \= completed  
        System-\>\>FS: Delete .temp/exec\_abc-123/  
    else User Rejects (Revision)  
        System-\>\>Checkpoint: Check: revisions left?  
        Note over Checkpoint: revision\_iteration: 0\<br/\>max\_revision\_iterations: 3\<br/\>→ YES  
        System-\>\>DB: Update: revision\_iteration \= 1  
        Note over System: SAME execution\_id\<br/\>SAME temp workspace  
        Checkpoint-\>\>LLM: Execute with revision feedback  
    else Max Retries Exceeded Earlier  
        System-\>\>DB: Update: status \= failed  
        System-\>\>FS: Move .temp/exec\_abc-123/ → .errored/  
        System-\>\>System: Trigger on\_failure action  
    end

---

## **12\. Database Schema**

erDiagram  
    PIPELINES ||--o{ CHECKPOINT\_DEFINITIONS : "contains"  
    PIPELINES ||--o{ PIPELINE\_RUNS : "executes"  
    PIPELINE\_RUNS ||--o{ CHECKPOINT\_EXECUTIONS : "contains"  
    PIPELINE\_RUNS ||--o| PIPELINE\_RUNS : "extends\_from"  
    PIPELINE\_RUNS ||--o{ ROLLBACK\_EVENTS : "triggers"  
    CHECKPOINT\_DEFINITIONS ||--o{ CHECKPOINT\_EXECUTIONS : "instantiates"  
    CHECKPOINT\_EXECUTIONS ||--o{ EXECUTION\_LOGS : "records"  
    CHECKPOINT\_EXECUTIONS ||--o{ HUMAN\_INTERACTIONS : "records"  
    CHECKPOINT\_EXECUTIONS ||--o{ ARTIFACTS : "generates"  
    ROLLBACK\_EVENTS ||--o{ ARCHIVED\_ITEMS : "archives"  
    PIPELINES ||--o{ EVENTS : "logs"  
    PIPELINE\_RUNS ||--o{ EVENTS : "logs"  
    CHECKPOINT\_EXECUTIONS ||--o{ EVENTS : "logs"  
      
    PIPELINES {  
        uuid pipeline\_id PK  
        string pipeline\_name  
        string pipeline\_description  
        int pipeline\_definition\_version  
        json checkpoint\_order  
        bool auto\_advance  
        timestamp created\_at  
        timestamp updated\_at  
    }  
      
    CHECKPOINT\_DEFINITIONS {  
        uuid checkpoint\_id PK  
        uuid pipeline\_id FK  
        string checkpoint\_name  
        string checkpoint\_description  
        json dependencies  
        json inputs  
        json execution  
        json human\_interaction  
        json output  
        json instructions  
        timestamp created\_at  
        timestamp updated\_at  
    }  
      
    PIPELINE\_RUNS {  
        uuid run\_id PK  
        uuid pipeline\_id FK  
        int run\_version  
        enum status  
        uuid current\_checkpoint\_id FK  
        int current\_checkpoint\_position  
        uuid previous\_run\_id FK  
        int extends\_from\_run\_version  
        timestamp created\_at  
        timestamp started\_at  
        timestamp completed\_at  
        timestamp paused\_at  
        timestamp last\_resumed\_at  
    }  
      
    CHECKPOINT\_EXECUTIONS {  
        uuid execution\_id PK  
        uuid run\_id FK  
        uuid checkpoint\_id FK  
        int checkpoint\_position  
        enum status  
        int attempt\_number  
        int max\_attempts  
        int revision\_iteration  
        int max\_revision\_iterations  
        string temp\_workspace\_path  
        string permanent\_output\_path  
        timestamp created\_at  
        timestamp started\_at  
        timestamp completed\_at  
        timestamp failed\_at  
    }  
      
    EXECUTION\_LOGS {  
        uuid log\_id PK  
        uuid execution\_id FK  
        timestamp timestamp  
        enum level  
        string message  
        json details  
    }  
      
    HUMAN\_INTERACTIONS {  
        uuid interaction\_id PK  
        uuid execution\_id FK  
        timestamp timestamp  
        enum type  
        string user\_input  
        string system\_response  
    }  
      
    ARTIFACTS {  
        uuid artifact\_record\_id PK  
        uuid execution\_id FK  
        uuid artifact\_id  
        string artifact\_name  
        string file\_path  
        string format  
        int size\_bytes  
        string checksum  
        timestamp created\_at  
        timestamp promoted\_to\_permanent\_at  
    }  
      
    ROLLBACK\_EVENTS {  
        uuid rollback\_id PK  
        uuid source\_run\_id FK  
        int source\_run\_version  
        enum rollback\_type  
        uuid target\_run\_id FK  
        uuid target\_checkpoint\_id FK  
        int target\_checkpoint\_position  
        string archive\_location  
        enum triggered\_by  
        string user\_reason  
        timestamp created\_at  
    }  
      
    ARCHIVED\_ITEMS {  
        uuid archive\_item\_id PK  
        uuid rollback\_id FK  
        enum item\_type  
        uuid item\_id  
        string original\_path  
        string archived\_path  
        int size\_bytes  
    }  
      
    EVENTS {  
        uuid event\_id PK  
        enum event\_type  
        uuid pipeline\_id FK  
        uuid run\_id FK  
        uuid execution\_id FK  
        uuid checkpoint\_id FK  
        uuid rollback\_id FK  
        timestamp timestamp  
        string description  
        json metadata  
    }

---

## **13\. Pipeline Definition Changes Decision Tree**

flowchart TD  
    Start(\[User Modifies Pipeline/Checkpoint\]) \--\> WhatChanged{What Changed?}  
      
    WhatChanged \--\>|Checkpoint Order| NewPipeline\[Create New Pipeline\]  
    WhatChanged \--\>|Add Checkpoint| NewPipeline  
    WhatChanged \--\>|Remove Checkpoint| NewPipeline  
    WhatChanged \--\>|Pipeline Name| SamePipeline\[Update Existing Pipeline\]  
    WhatChanged \--\>|Pipeline Description| SamePipeline  
    WhatChanged \--\>|auto\_advance Setting| SamePipeline  
    WhatChanged \--\>|Checkpoint Definition| CheckpointUpdate\[Update Checkpoint Definition\]  
      
    NewPipeline \--\> Increment\[Increment pipeline\_definition\_version\]  
    Increment \--\> ResetRuns\[Reset run\_version to 1\]  
    ResetRuns \--\> NewPipelineID{Generate New\<br/\>pipeline\_id?}  
      
    NewPipelineID \--\>|Option A: Yes| CreateNewID\[New Pipeline Entity\<br/\>Fresh start\]  
    NewPipelineID \--\>|Option B: No| SameID\[Same Pipeline Entity\<br/\>Version increment\<br/\>Runs reset to v1\]  
      
    SamePipeline \--\> UpdateMeta\[Update pipeline metadata\<br/\>Keep pipeline\_definition\_version\]  
    UpdateMeta \--\> ContinueRuns\[Existing runs continue normally\]  
      
    CheckpointUpdate \--\> UpdateCheckpoint\[Update checkpoint JSON\]  
    UpdateCheckpoint \--\> UserResponsibility\[User Responsibility:\<br/\>Ensure dependencies still valid\]  
    UserResponsibility \--\> ContinueRuns  
      
    CreateNewID \--\> Done(\[Complete\])  
    SameID \--\> Done  
    ContinueRuns \--\> Done  
      
    style NewPipeline fill:\#ffcccc  
    style SamePipeline fill:\#ccffcc  
    style CheckpointUpdate fill:\#fff4cc  
      
    note right of NewPipelineID  
        DECISION NEEDED:  
        Should checkpoint order changes  
        create entirely new pipeline  
        or just version the same one?  
          
        Recommended: Same pipeline\_id,  
        version increment, runs reset  
    end note

---

## **14\. Complete User Journey**

journey  
    title Complete Pipeline Workflow Journey  
    section Pipeline Setup  
      Create Pipeline: 5: User  
      Define Checkpoints: 4: User  
      Configure Execution: 3: User  
      Review Configuration: 4: User  
    section First Run (v1)  
      Start Pipeline Run v1: 5: User  
      Approve Checkpoint 0 Start: 4: User  
      Wait for Execution: 2: System  
      Review Checkpoint 0 Output: 4: User  
      Approve Checkpoint 0 Complete: 5: User  
      Repeat for All Checkpoints: 3: User, System  
      Complete Pipeline v1: 5: User  
    section Second Run (v2)  
      Start Pipeline Run v2: 5: User  
      System Loads v1 Outputs: 5: System  
      Execute Checkpoints with Context: 4: System  
      Review Enhanced Outputs: 5: User  
      Complete Pipeline v2: 5: User  
    section Rollback Scenario  
      Identify Issue in v2: 2: User  
      Initiate Rollback to v1 CP2: 3: User  
      System Archives v2 Data: 5: System  
      Continue from v1 CP2: 4: User  
      Fix and Re-execute: 4: User, System  
    section Maintenance  
      Review Execution Logs: 4: User  
      Check Archived Data: 3: Maintainer  
      Verify DB Integrity: 5: System

---

## **15\. API Endpoints Overview**

graph LR  
    subgraph "Pipeline Management"  
        P1\[POST /api/pipelines\<br/\>Create Pipeline\]  
        P2\[GET /api/pipelines\<br/\>List Pipelines\]  
        P3\[GET /api/pipelines/:id\<br/\>Get Pipeline Details\]  
        P4\[PUT /api/pipelines/:id\<br/\>Update Pipeline\]  
        P5\[DELETE /api/pipelines/:id\<br/\>Delete Pipeline\]  
    end  
      
    subgraph "Checkpoint Management"  
        C1\[POST /api/checkpoints\<br/\>Create Checkpoint\]  
        C2\[GET /api/checkpoints/:id\<br/\>Get Checkpoint\]  
        C3\[PUT /api/checkpoints/:id\<br/\>Update Checkpoint\]  
        C4\[DELETE /api/checkpoints/:id\<br/\>Delete Checkpoint\]  
    end  
      
    subgraph "Pipeline Runs"  
        R1\[POST /api/runs\<br/\>Start New Run\]  
        R2\[GET /api/runs\<br/\>List Runs\]  
        R3\[GET /api/runs/:id\<br/\>Get Run Details\]  
        R4\[POST /api/runs/:id/pause\<br/\>Pause Run\]  
        R5\[POST /api/runs/:id/resume\<br/\>Resume Run\]  
    end  
      
    subgraph "Checkpoint Execution"  
        E1\[POST /api/executions/start\<br/\>Start Checkpoint\]  
        E2\[GET /api/executions/:id\<br/\>Get Execution Status\]  
        E3\[POST /api/executions/:id/approve\<br/\>Approve Checkpoint\]  
        E4\[POST /api/executions/:id/reject\<br/\>Request Revision\]  
        E5\[GET /api/executions/:id/logs\<br/\>Get Execution Logs\]  
        E6\[GET /api/executions/:id/conversation\<br/\>Get Agent Conversation\]  
    end  
      
    subgraph "Rollback"  
        RB1\[POST /api/rollback\<br/\>Initiate Rollback\]  
        RB2\[GET /api/rollback/:id\<br/\>Get Rollback Details\]  
        RB3\[GET /api/rollback\<br/\>List Rollback History\]  
    end  
      
    subgraph "Artifacts"  
        A1\[GET /api/artifacts/:id\<br/\>Download Artifact\]  
        A2\[GET /api/artifacts/list\<br/\>List Artifacts\]  
    end  
      
    style P1 fill:\#e1f5ff  
    style R1 fill:\#ccffcc  
    style E1 fill:\#fff4cc  
    style RB1 fill:\#ffcccc

---

The implementation will happen into **small, testable, incremental slices**. Each slice will deliver a working feature that can be tested end-to-end.

---

# **Implementation Plan \- Incremental Slices**

## **Phase 1: Foundation & Core Infrastructure (Slices 1-5)**

### **Slice 1: Project Setup & Database Foundation**

**Goal:** Basic project structure with database models

**Backend:**

* Set up Python project structure (Flask/FastAPI)  
* Create `config.py` with environment variables  
* Set up SQLite database connection  
* Create SQLAlchemy models for:  
  * `Pipeline`  
  * `CheckpointDefinition` (basic fields only)  
* Create database migrations (Alembic)  
* Add basic logging setup

**Frontend:**

* Set up React project (Vite \+ React)  
* Create basic routing structure  
* Add Tailwind CSS  
* Create layout components (Header, Sidebar, Main)

**API Endpoints:**

* `GET /api/health` \- Health check

**Testing:**

* Database connection works  
* Models can be created and queried  
* Frontend loads and displays basic UI

**Deliverable:** Empty app that connects to DB and shows a homepage

---

### **Slice 2: Create & List Pipelines**

**Goal:** User can create and view pipelines

**Backend:**

* API: `POST /api/pipelines` \- Create pipeline  
* API: `GET /api/pipelines` \- List all pipelines  
* API: `GET /api/pipelines/:id` \- Get single pipeline  
* Implement pipeline creation logic  
* Create file system structure for new pipeline

**Frontend:**

* Page: Pipeline list view  
* Page: Create pipeline form  
* Component: Pipeline card  
* Form validation

**Testing:**

* Create a pipeline via UI  
* See it in the list  
* Click to view details  
* Verify file system structure created

**Deliverable:** Can create and view pipelines (no checkpoints yet)

---

### **Slice 3: Update & Delete Pipelines**

**Goal:** Full CRUD for pipelines

**Backend:**

* API: `PUT /api/pipelines/:id` \- Update pipeline  
* API: `DELETE /api/pipelines/:id` \- Delete pipeline  
* Implement soft delete (move to archive)  
* Handle file system cleanup

**Frontend:**

* Edit pipeline form  
* Delete confirmation modal  
* Update pipeline list after changes

**Testing:**

* Edit pipeline name/description  
* Delete a pipeline  
* Verify files archived correctly

**Deliverable:** Complete pipeline management

---

### **Slice 4: Create Simple Checkpoint Definitions**

**Goal:** Add checkpoints to pipelines (simple mode only)

**Backend:**

* API: `POST /api/pipelines/:id/checkpoints` \- Create checkpoint  
* API: `GET /api/checkpoints/:id` \- Get checkpoint  
* Implement checkpoint model with:  
  * Basic metadata (name, description)  
  * Execution mode: `human_only` ONLY (simplest to start)  
  * Human-only config (form fields)  
  * Output artifacts (basic)  
  * NO validation, NO retries, NO agents yet

**Frontend:**

* Page: Checkpoint creation form (simple mode)  
* Component: Checkpoint list in pipeline view  
* Form field builder for `human_only` mode

**Testing:**

* Create a pipeline  
* Add 2-3 human\_only checkpoints to it  
* View checkpoint definitions  
* Verify saved in DB and file system

**Deliverable:** Pipelines with simple human\_only checkpoints

---

### **Slice 5: Update & Delete Checkpoints \+ Reorder**

**Goal:** Full CRUD for checkpoints \+ ordering

**Backend:**

* API: `PUT /api/checkpoints/:id` \- Update checkpoint  
* API: `DELETE /api/checkpoints/:id` \- Delete checkpoint  
* API: `PUT /api/pipelines/:id/checkpoint-order` \- Reorder checkpoints  
* Update `checkpoint_order` array in pipeline

**Frontend:**

* Edit checkpoint form  
* Delete checkpoint with confirmation  
* Drag-and-drop to reorder checkpoints  
* Visual order indicator

**Testing:**

* Edit a checkpoint  
* Delete a checkpoint  
* Reorder checkpoints via drag-drop  
* Verify order saved correctly

**Deliverable:** Complete checkpoint definition management

---

## **Phase 2: Pipeline Execution Engine (Slices 6-10)**

### **Slice 6: Start Pipeline Run (Human-Only Checkpoints)**

**Goal:** Execute pipeline with human\_only checkpoints

**Backend:**

* Create `PipelineRun` model  
* Create `CheckpointExecution` model  
* API: `POST /api/runs` \- Start new run  
* API: `GET /api/runs/:id` \- Get run status  
* Implement run creation logic:  
  * Create run record (v1)  
  * Create first checkpoint execution  
  * Create temp workspace  
  * Set status to `waiting_approval_to_start`

**Frontend:**

* Page: Run execution view  
* Component: Run status display  
* Button: "Start Pipeline Run"  
* Display: Current checkpoint info

**Testing:**

* Start a run for a pipeline  
* Verify run record created (v1)  
* Verify first checkpoint execution created  
* Verify temp workspace created  
* See status in UI

**Deliverable:** Can initiate pipeline runs

---

### **Slice 7: Execute Human-Only Checkpoints**

**Goal:** Complete flow for human\_only checkpoints

**Backend:**

* API: `POST /api/executions/:id/approve-start` \- Approve checkpoint start  
* API: `POST /api/executions/:id/submit` \- Submit human form data  
* API: `POST /api/executions/:id/approve-complete` \- Approve checkpoint completion  
* Implement execution flow:  
  * User approves start  
  * Show form to user  
  * User submits form data  
  * Save to temp workspace  
  * User approves completion  
  * Promote temp → permanent  
  * Move to next checkpoint

**Frontend:**

* Page: Checkpoint execution view  
* Component: Approval buttons  
* Component: Dynamic form renderer (based on checkpoint config)  
* Component: Artifact preview  
* Status transitions displayed

**Testing:**

* Start a run  
* Approve checkpoint 0 start  
* Fill form with data  
* Submit form  
* Approve completion  
* Verify artifact saved to permanent  
* Verify next checkpoint waiting  
* Repeat for all checkpoints  
* Complete entire pipeline

**Deliverable:** Full pipeline execution with human\_only checkpoints

---

### **Slice 8: Pause & Resume Runs**

**Goal:** Ability to pause between checkpoints

**Backend:**

* API: `POST /api/runs/:id/pause` \- Pause run  
* API: `POST /api/runs/:id/resume` \- Resume run  
* Implement pause logic (only between checkpoints)  
* Store pause state

**Frontend:**

* Button: "Pause Pipeline" (only enabled between checkpoints)  
* Button: "Resume Pipeline"  
* Visual indicator: Pipeline paused

**Testing:**

* Start a run  
* Complete checkpoint 0  
* Click "Pause" before starting checkpoint 1  
* Close browser  
* Reopen and see paused state  
* Click "Resume"  
* Continue execution

**Deliverable:** Pause/resume functionality

---

### **Slice 9: View Run History & Artifacts**

**Goal:** See past runs and their outputs

**Backend:**

* API: `GET /api/pipelines/:id/runs` \- List runs for pipeline  
* API: `GET /api/runs/:id/checkpoints` \- List checkpoint executions  
* API: `GET /api/artifacts/:id/download` \- Download artifact

**Frontend:**

* Page: Run history list  
* Page: Run details view  
* Component: Checkpoint execution timeline  
* Component: Artifact list with download  
* Component: Artifact preview (JSON, Markdown)

**Testing:**

* Complete multiple runs (v1, v2)  
* View run history  
* Click on a run to see details  
* View each checkpoint's status  
* Download artifacts  
* Preview artifacts in UI

**Deliverable:** Full run history and artifact viewing

---

### **Slice 10: Extend Previous Run (Version Extension)**

**Goal:** v2 builds on v1 outputs

**Backend:**

* Modify run creation to:  
  * Find previous run (highest valid version)  
  * Set `previous_run_id` and `extends_from_run_version`  
  * Load previous version artifacts when checkpoint starts  
  * Inject into context (for human\_only, show as reference)

**Frontend:**

* When starting new run, show: "This will be v2, extending from v1"  
* Display previous version artifacts as reference  
* Show version number in UI

**Testing:**

* Complete v1 run  
* Start v2 run  
* Verify v2 checkpoint 0 shows v1 checkpoint 0 output as reference  
* Complete v2  
* Verify v2 artifacts different from v1  
* Verify file naming: `artifact_v1.json` vs `artifact_v2.json`

**Deliverable:** Version extension works

---

## **Phase 3: Rollback System (Slices 11-12)**

### **Slice 11: Checkpoint-Level Rollback**

**Goal:** Rollback within same run

**Backend:**

* Create `RollbackEvent` model  
* API: `POST /api/rollback` \- Initiate rollback  
* Implement rollback logic:  
  * Identify checkpoints to delete  
  * Move to archive with UUID  
  * Delete from DB and file system  
  * Update run status if needed  
  * Create rollback event record

**Frontend:**

* Component: Rollback button in run view  
* Modal: "Rollback to checkpoint X?"  
* Display: Available rollback points  
* Show: Rollback history

**Testing:**

* Complete checkpoints 0, 1, 2  
* Rollback to checkpoint 1  
* Verify checkpoint 2 deleted  
* Verify files in `.archived/rollback_{uuid}/`  
* Verify run status \= `in_progress`  
* Continue from checkpoint 1  
* Complete checkpoint 2 again

**Deliverable:** Checkpoint-level rollback

---

### **Slice 12: Run-Level Rollback**

**Goal:** Rollback to previous version

**Backend:**

* Extend rollback API for run-level  
* Implement logic:  
  * Delete entire runs (v2, v3)  
  * Update "latest version" pointer  
  * Archive deleted runs

**Frontend:**

* Option: "Rollback to v1 checkpoint 2"  
* Show: Cross-version rollback confirmation  
* Display: Impact preview (what will be deleted)

**Testing:**

* Complete v1, v2, v3  
* Rollback to v1 checkpoint 2  
* Verify v2 and v3 deleted  
* Verify "latest" \= v1  
* Start v4, verify it extends from v1  
* Verify archived data structure

**Deliverable:** Full rollback system

---

## **Phase 4: Agent Execution (Slices 13-17)**

### **Slice 13: Single Agent Execution**

**Goal:** Simplest agentic checkpoint (single agent)

**Backend:**

* Implement agent execution:  
  * Load checkpoint with `mode: 'agentic'`, `creation_mode: 'single'`  
  * Call Anthropic API with system/task prompts  
  * Provide `file_operations` tool  
  * Agent writes to `artifacts_staging/`  
  * Return result

**Frontend:**

* Form: Create agentic checkpoint (single agent mode)  
* Display: Agent conversation in real-time (streaming)  
* Component: File operations log

**Testing:**

* Create checkpoint with single agent  
* Agent task: "Create a JSON file with project summary"  
* Start execution  
* Watch agent conversation  
* Agent calls file\_operations to write JSON  
* Approve completion  
* Verify artifact promoted

**Deliverable:** Single agent execution

---

### **Slice 14: Predefined Multi-Agent Execution**

**Goal:** Multiple agents with predefined roles

**Backend:**

* Implement predefined multi-agent:  
  * Load agent definitions  
  * Execute discussion (sequential mode first)  
  * Track conversation between agents  
  * Agents write outputs

**Frontend:**

* Form: Define multiple agents (roles, prompts)  
* Display: Multi-agent conversation with speaker labels  
* Component: Discussion mode selector

**Testing:**

* Create checkpoint with 2 agents:  
  * Agent A: "Business Analyst"  
  * Agent B: "Technical Architect"  
* Agents discuss and create artifacts  
* Verify conversation flow  
* Verify both agents' outputs

**Deliverable:** Multi-agent (predefined) execution

---

### **Slice 15: Meta-Agent Creation**

**Goal:** Meta-agent spawns other agents

**Backend:**

* Implement meta-agent:  
  * Meta-agent receives instructions  
  * Meta-agent creates agent definitions  
  * Spawned agents execute task  
  * Return results

**Frontend:**

* Form: Meta-agent instructions  
* Display: Show meta-agent creating agents  
* Display: Show spawned agents working

**Testing:**

* Create checkpoint with meta-agent  
* Instructions: "Create 3 agents for designing a mobile app"  
* Meta-agent spawns: UX Designer, Backend Dev, Frontend Dev  
* Agents collaborate  
* Verify outputs

**Deliverable:** Meta-agent system

---

### **Slice 16: Artifact Input Injection**

**Goal:** Agents can read previous checkpoint outputs

**Backend:**

* Implement input injection:  
  * Load referenced checkpoint artifacts  
  * Load previous version artifacts  
  * Format as Markdown/XML/JSON  
  * Inject into agent prompt

**Frontend:**

* Checkpoint config: Select which checkpoints to reference  
* Display: Show injected context to user (preview)

**Testing:**

* Create checkpoint 1: generates `requirements.json`  
* Create checkpoint 2: references checkpoint 1  
* Start execution  
* Verify checkpoint 2 agent receives `requirements.json` content  
* Agent uses it to create next artifact

**Deliverable:** Full artifact context injection

---

### **Slice 17: Retry & Validation**

**Goal:** Handle failures and validate outputs

**Backend:**

* Implement retry mechanism:  
  * Catch execution failures  
  * Increment `attempt_number`  
  * Retry with same `execution_id`  
  * Same temp workspace  
* Implement validation:  
  * LLM schema validation  
  * LLM custom validation  
  * Retry on validation failure

**Frontend:**

* Display: Retry attempts counter  
* Display: Validation status  
* Component: Validation error messages

**Testing:**

* Create checkpoint with validation  
* Force failure (bad schema)  
* Watch auto-retry  
* Exceed max retries → checkpoint fails  
* Verify moved to `.errored/`

**Deliverable:** Retry and validation system

---

## **Phase 5: Script Execution & Polish (Slices 18-20)**

### **Slice 18: Script Execution Mode**

**Goal:** Run Python scripts as checkpoints

**Backend:**

* Implement script execution:  
  * If `requires_user_input`, AI asks user  
  * Execute script with parameters  
  * Capture stdout/stderr  
  * Handle success/failure  
  * Return output file

**Frontend:**

* Form: Configure script checkpoint  
* Display: Script execution logs  
* Component: Script output viewer

**Testing:**

* Create checkpoint: `mode: 'script'`  
* Script: `generate_report.py`  
* Script writes `report.pdf`  
* Execute checkpoint  
* Verify script runs  
* Verify output artifact

**Deliverable:** Script execution

---

### **Slice 19: Event System & Audit Trail**

**Goal:** Track all events for debugging

**Backend:**

* Create `Event` model  
* Log all events:  
  * Pipeline created/updated/deleted  
  * Run started/paused/resumed/completed  
  * Checkpoint started/completed/failed  
  * Rollback initiated/completed  
  * Artifacts created/promoted/archived  
* API: `GET /api/events` \- Query events

**Frontend:**

* Page: Event log viewer  
* Filters: By type, date, pipeline  
* Component: Event timeline

**Testing:**

* Perform various actions  
* View event log  
* Filter by pipeline  
* See complete audit trail

**Deliverable:** Full event tracking

---

### **Slice 20: Advanced Features & UI Polish**

**Goal:** Final touches

**Backend:**

* Implement summarization option  
* Add discussion modes (council, parallel, debate)  
* Add timeout handling  
* Improve error messages  
* Add database integrity checks

**Frontend:**

* Add loading states everywhere  
* Add error boundaries  
* Improve form validation  
* Add keyboard shortcuts  
* Add dark mode  
* Responsive design  
* Add notifications/toasts

**Testing:**

* Full end-to-end tests  
* Test all edge cases  
* Performance testing  
* UI/UX review

**Deliverable:** Production-ready system

---

## **Summary of Slices**

| Phase | Slices | Focus | Testable Outcome |
| ----- | ----- | ----- | ----- |
| 1 | 1-5 | Foundation | Create pipelines with human\_only checkpoints |
| 2 | 6-10 | Execution | Run pipelines, view history, extend versions |
| 3 | 11-12 | Rollback | Rollback checkpoints and runs |
| 4 | 13-17 | Agents | Execute agentic checkpoints with context |
| 5 | 18-20 | Polish | Scripts, events, final touches |

---

## **Technology Stack Recommendation**

**Backend:**

* **FastAPI** (Python) \- Fast, modern, async support  
* **SQLAlchemy** \- ORM for database  
* **Alembic** \- Database migrations  
* **Anthropic Python SDK** \- LLM calls  
* **Pydantic** \- Data validation

**Frontend:**

* **React** \+ **TypeScript** \- Type safety  
* **Vite** \- Fast build tool  
* **TanStack Query** \- Data fetching/caching  
* **Tailwind CSS** \- Styling  
* **shadcn/ui** \- Component library  
* **React Router** \- Routing  
* **Zustand** \- State management

**Database:**

* **SQLite** \- Development & production (simple, file-based)

**File Storage:**

* Local file system (as designed)

---

## **Development Approach**

For each slice:

1. **Backend first** \- Implement API and logic  
2. **Test with curl/Postman** \- Ensure backend works  
3. **Frontend** \- Build UI for the feature  
4. **Integration test** \- Test end-to-end  
5. **Commit** \- Version control checkpoint  
6. **Demo** \- Show working feature

---

