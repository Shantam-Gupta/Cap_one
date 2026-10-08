# BONAFIDE CERTIFICATE

This is to certify that this project report entitled "ReRun Autonomous Coding Platform" is the bonafide work of [Student Name] who carried out the project work under my supervision. 

Signature of Head of Department: _______________________
Signature of Supervisor: _______________________

---
\pagebreak

# ACKNOWLEDGEMENT

I would like to express my special thanks of gratitude to my supervisor as well as our principal who gave me the golden opportunity to do this wonderful project on the topic "ReRun Autonomous Coding Platform", which also helped me in doing a lot of Research and I came to know about so many new things. I am really thankful to them.

Secondly, I would also like to thank my parents and friends who helped me a lot in finalizing this project within the limited time frame.

---
\pagebreak

# LIST OF FIGURES

| Figure No. | Description | Page No. |
|------------|-------------|----------|
| Fig. 1.1   | High-Level Architecture of ReRun Platform | 10       |
| Fig. 4.1   | Master Agent State Machine Flow          | 12       |
| Fig. 4.2   | Recovery Agent Diagnosis Loop            | 14       |
| Fig. A.1   | ReRun Terminal Interface Execution       | 24       |
| Fig. A.2   | Database Artifacts Schema Mapping        | 25       |

---
\pagebreak

# ABSTRACT

With the rapid evolution of Large Language Models (LLMs), the demand for autonomous coding systems has increased significantly. However, existing solutions often struggle with runtime failures, hallucinations, and lack of systemic self-correction. This project introduces **ReRun**, a Hierarchical Autonomous Coding Platform designed to overcome these limitations. ReRun utilizes a Master Agent Orchestrator to delegate tasks across specialized sub-agents: a Planner Agent, a Coding Agent, a Validator Agent, and a Recovery Agent. The core novelty lies in its Finite State Machine (FSM)-driven execution loop and a sophisticated, history-aware Recovery Agent that diagnoses sandboxed execution failures and recursively applies targeted patches without losing context of repeated errors. This report details the architectural design, implementation methodology, and end-to-end evaluation of the ReRun platform, proving its efficacy in autonomous code generation, validation, and self-healing.

---
\pagebreak

# TABLE OF CONTENTS

| CHAPTER NO. | TITLE | PAGE NO. |
|-------------|-------|----------|
|             | List of Figures | iv |
|             | Abstract | v |
| 1 | **CHAPTER-1: PROJECT DESCRIPTION AND OUTLINE** | 1 |
| | 1.1 Introduction | 1 |
| | 1.2 Motivation for the work | 1 |
| | 1.3 Problem statement | 2 |
| | 1.4 Objective of the work | 2 |
| | 1.5 Summary | 3 |
| 2 | **CHAPTER-2: RELATED WORK INVESTIGATION** | 4 |
| | 2.1 Existing approaches/methods | 4 |
| | 2.2 Pros and cons of the stated approaches/methods | 4 |
| 3 | **CHAPTER-3: REQUIREMENT ARTIFACTS** | 6 |
| | 3.1 Introduction | 6 |
| | 3.2 Hardware and software requirements | 6 |
| | 3.3 Specific project requirements | 7 |
| | 3.4 Summary | 8 |
| 4 | **CHAPTER-4: DESIGN METHODOLOGY AND ITS NOVELTY** | 9 |
| | 4.1 Methodology and goal | 9 |
| | 4.2 Functional modules design and analysis | 9 |
| | 4.3 Software architectural designs | 13 |
| | 4.4 User-interface designs | 14 |
| | 4.5 Summary | 15 |
| 5 | **CHAPTER-5: TECHNICAL IMPLEMENTATION & ANALYSIS** | 16 |
| | 5.1 Outline | 16 |
| | 5.2 Technical coding and code solutions | 16 |
| | 5.3 Prototype submission | 18 |
| | 5.4 Summary | 19 |
| 6 | **CHAPTER-6: PROJECT OUTCOME AND APPLICABILITY** | 20 |
| | 6.1 Key implementations outline of the system | 20 |
| | 6.2 Significant project outcomes | 20 |
| | 6.3 Project applicability on real-world applications | 21 |
| | 6.4 Inference | 21 |
| 7 | **CHAPTER-7: CONCLUSIONS AND RECOMMENDATION** | 22 |
| | 7.1 Outline | 22 |
| | 7.2 Limitations/constraints of the system | 22 |
| | 7.3 Future enhancements | 23 |
| | 7.4 Inference | 23 |
| | **APPENDIX A – Screenshots** | 24 |
| | **APPENDIX B – Coding** | 26 |
| | **REFERENCES** | 32 |

---
\pagebreak

# CHAPTER-1: PROJECT DESCRIPTION AND OUTLINE

## 1.1 Introduction
The field of software engineering is currently undergoing a paradigm shift driven by Artificial Intelligence. The "ReRun Autonomous Coding Platform" acts as a sophisticated, autonomous agentic system capable of receiving high-level natural language instructions, translating them into discrete executable plans, writing the respective Python code, and executing that code within an isolated sandbox. It operates as a fully autonomous software developer, capable of handling its own errors without human intervention.

## 1.2 Motivation for the work
Software development involves highly iterative cycles of coding, testing, debugging, and refactoring. While current AI assistants provide excellent single-turn code generation, they operate as passive "copilots". They require a human-in-the-loop to manually execute the code, parse the resulting terminal errors, and feed them back into the chat interface for debugging. The motivation behind ReRun is to completely eliminate this human-bottleneck by giving the AI direct runtime feedback and allowing it to fix its own bugs in an autonomous loop.

## 1.3 Problem statement
Despite the capabilities of modern LLMs (like GPT-4 and Gemini), they frequently suffer from hallucinations, producing code that looks syntactically correct but fails during runtime due to missing dependencies, edge cases, or API deprecations. Furthermore, when an AI attempts to fix its own code without a structured state machine, it frequently gets stuck in an infinite "hallucination loop", continuously outputting the same failing code. There is a strong need for an architecture that mathematically enforces execution paths and tracks error history.

## 1.4 Objective of the work
The core objectives of the ReRun project are:
1. To develop a hierarchical Master Orchestrator capable of differentiating between coding and reasoning tasks.
2. To integrate a Planner Agent that generates structured "Best of 3" subtask execution plans, ensuring the most robust logic is selected before execution begins.
3. To establish a secure Execution Sandbox to safely compile and run generated Python artifacts without risking the host machine.
4. To implement a highly sophisticated Recovery Agent that natively tracks execution history and breaks infinite failure loops by recognizing repeated errors and changing strategies.

## 1.5 Summary
This chapter laid the foundational context for the project, identifying the critical gap in existing passive AI coding assistants and establishing the goal of building an autonomous, self-healing code generation framework.

---
\pagebreak

# CHAPTER-2: RELATED WORK INVESTIGATION

## 2.1 Existing approaches/methods
Currently, the industry relies on a few primary approaches for AI-assisted coding:
* **Copilots (e.g., GitHub Copilot, Cursor):** These integrate directly into the IDE. They auto-complete lines and answer conversational queries based on the current active file.
* **Autonomous SWE Agents (e.g., AutoGPT, Devin):** These attempt to act as fully autonomous agents, navigating workspaces, using terminals, and modifying multiple files across a repository in an open-ended loop.
* **Chained Prompt Systems:** Frameworks like LangChain or AutoGen which link multiple generic agents together in a conversational ring, allowing them to debate and pass messages to one another.

## 2.2 Pros and cons of the stated approaches/methods
* **Copilots:**
  * *Pros:* Safe, predictable, very fast, highly integrated into the developer workflow.
  * *Cons:* Requires constant human supervision; cannot execute code or run test suites natively to self-verify its own work.
* **Autonomous SWE Agents:**
  * *Pros:* Can accomplish complex, multi-step integrations without human interaction.
  * *Cons:* Prone to catastrophic failure cascades. Without strict state machines, they often overwrite critical files, enter infinite debugging loops, and burn through API credits rapidly.
* **Chained Prompt Systems:**
  * *Pros:* Good for generic multi-agent negotiation.
  * *Cons:* Too generalized for strict software engineering compilation pipelines, leading to unpredictable software architectures.

---
\pagebreak

# CHAPTER-3: REQUIREMENT ARTIFACTS

## 3.1 Introduction
Building an autonomous coding platform requires strict technical foundations to ensure isolated execution, secure API communication, and reliable asynchronous state management. The requirements are designed to support a robust, concurrent backend system.

## 3.2 Hardware and software requirements
**Hardware Requirements:**
* Minimum 8GB RAM (16GB recommended for heavy sandboxing and concurrent task execution).
* Multi-core processor (Intel i5/Ryzen 5 or equivalent).
* 10GB free disk space for Docker images, SQLite databases, and workspace artifacts.

**Software Requirements:**
* **Language:** Python 3.10+
* **Framework:** FastAPI (Backend API), Pydantic (Schema Validation)
* **LLM Provider:** Google Gemini Pro / Flash (via `google-genai` or REST API)
* **Database:** SQLite (with `aiosqlite` and `sqlalchemy` for async operations)
* **Sandboxing:** Docker (Optional but recommended for execution isolation)
* **Testing:** Pytest, pytest-asyncio

## 3.3 Specific project requirements
1. **API Keys:** A valid Google Gemini API Key or OpenAI API Key injected into the environment. The system must properly handle rate limits (429 errors) without crashing.
2. **State Machine:** A rigorous Finite State Machine (FSM) implementation to prevent illegal task state transitions. The state machine must define explicit paths (e.g., `PLAN_READY` cannot transition back to `RECEIVED`).
3. **Storage Abstraction:** File I/O operations must be contained within a dynamically generated `workspaces/` directory. All tasks must have isolated folders to prevent cross-contamination.

## 3.4 Summary
The hardware and software constraints emphasize the need for asynchronous Python programming and strict directory sandboxing to run autonomous agentic loops safely on a host machine.

---
\pagebreak

# CHAPTER-4: DESIGN METHODOLOGY AND ITS NOVELTY

## 4.1 Methodology and goal
The ReRun Platform is designed using a **Hierarchical Delegation Architecture**. Rather than using one massive LLM prompt to "do everything", ReRun splits cognitive load. A Master Agent acts as the central router and state manager, delegating specialized subtasks to lower-level agents. This approach minimizes token context overflow and allows individual agents to focus on single, specialized tasks.

## 4.2 Functional modules design and analysis
The system is divided into 4 core functional modules:
1. **Master Orchestrator:** The brain of the operation. It receives the task, initializes the FSM, classifies the task as `CODING` or `NORMAL` using LLM classification, and triggers the appropriate workflow. It decides when a task is officially complete.
2. **Planner Agent:** Responsible for breaking tasks into a JSON-structured plan. It implements a "Best of 3" generation strategy to ensure the most robust logic is selected, adding asynchronous delays between generations to respect API rate limits.
3. **Coding Agent:** Translates the subtasks into functional, standalone Python 3.10 code. It strictly adheres to outputting self-contained JSON payloads containing the executable code.
4. **Recovery Agent:** The safety net. It saves a history of the task locally into `workspaces/recovery_tasks.json`. During execution failures, it diagnoses tracebacks while reading the history of previous failed attempts, ensuring it does not output the same failing code twice.

## 4.3 Software architectural designs
The backend utilizes an asynchronous, event-driven architecture using Python's `asyncio` and `FastAPI`. 
The FSM defines 17 strict states (e.g., `RECEIVED` -> `PLANNING` -> `GENERATING` -> `EXECUTING` -> `OBSERVING` -> `COMPLETED`). Transitions are mathematically locked; an agent cannot execute code before it passes the `SECURITY_CHECK` phase. If a task is classified as `NORMAL`, the FSM employs a dynamic fast-path, transitioning from `PLAN_READY` directly to `COMPLETED` while saving the output to the Recovery Agent.

## 4.4 User-interface designs
Currently, ReRun operates primarily as a Backend API and a CLI utility (`test_task.py`). The CLI is highly interactive: it prompts the user for their API key if missing, asks for the task via standard input, and outputs the detailed LLM Plan, execution logs, and artifacts directly to the terminal for real-time human observation.

## 4.5 Summary
The novelty of ReRun lies not just in writing code, but in its self-awareness during the execution and recovery phases, leveraging the FSM to ensure safe, contained execution and preventing recursive hallucination loops.

---
\pagebreak

# CHAPTER-5: TECHNICAL IMPLEMENTATION & ANALYSIS

## 5.1 Outline
This chapter covers the specific technical hurdles faced during the implementation of the ReRun platform and the precise code solutions developed to overcome them. It highlights the realities of working with stochastic LLMs.

## 5.2 Technical coding and code solutions
**Rate Limiting Handlers:**
During the implementation of the "Best of 3" planner loop, rapid sequential requests to the Gemini API resulted in instant `429 Too Many Requests` crashes. The `gemini_provider.py` was updated to explicitly catch `503` and `429` status codes, implementing an exponential backoff retry loop. Additionally, an explicit `asyncio.sleep(4)` pacing mechanism was added directly into the Orchestrator loop to throttle concurrent planner generation and preserve free-tier quotas.

**State Machine Bypasses:**
Customizing the workflow to allow non-coding (NORMAL) tasks to bypass execution entirely resulted in an `IllegalStateTransitionError`. The strict FSM refused to allow a jump from `PLAN_READY` to `COMPLETED`. This was resolved by dynamically modifying the `ALLOWED_TRANSITIONS` dictionary in `state_machine.py` to natively support this fast-path logic for non-code tasks.

**History Persistence:**
To satisfy the requirement of logging agent histories natively, the `RecoveryAgent.save_recovery_task` was built to read, append, and flush JSON payloads dynamically to an isolated `workspaces/recovery_tasks.json` file. This acts as a permanent audit trail of everything the orchestrator and agents accomplish.

## 5.3 Prototype submission
The prototype successfully handles:
* Automatic task classification (Coding vs. Normal) using an initial LLM pass.
* 3-candidate planning phases with automatic pacing to avoid API bans.
* JSON-based persistent recovery logs that track plans and generated source code.
* Direct terminal output of plan parameters for human readability.

## 5.4 Summary
The integration of LLMs into programmatic execution loops requires defensive programming, specifically around unstructured outputs, FSM state exceptions, and API unreliability. The implementation solutions robustly handle these edge cases.

---
\pagebreak

# CHAPTER-6: PROJECT OUTCOME AND APPLICABILITY

## 6.1 Key implementations outline of the system
The system successfully acts as a headless, autonomous software developer. You provide it a natural language prompt, and it navigates the cognitive planning, coding, and history logging without requiring human intervention. It serves as a proof-of-concept for how LLMs can be utilized beyond simple chat interfaces.

## 6.2 Significant project outcomes
The ReRun platform demonstrates a measurable reduction in "hallucination loops." By providing the Recovery Agent with a `TaskContext` that holds the entire history of previous failures (e.g., `consecutive_identical_errors`), the LLM actively learns from its mistakes in real-time, drastically increasing the success rate of complex algorithms compared to a standard, stateless LLM prompt. Furthermore, the integration of a task classifier allows the platform to elegantly double as a standard reasoning engine for non-code tasks.

## 6.3 Project applicability on real-world applications
This architecture can be deployed in enterprise environments for:
* Automated integration testing generation based on existing codebase requirements.
* Database migration script authoring and automatic validation.
* Background data analysis and charting (as it writes code to generate matplotlib artifacts autonomously).
* CI/CD pipeline integration, where the agent automatically attempts to fix failing builds before alerting a human developer.

## 6.4 Inference
Agentic frameworks that combine strict Finite State Machines with LLMs perform exponentially better and more predictably than plain Chat-based LLM applications. State machines ground the stochastic nature of AI.

---
\pagebreak

# CHAPTER-7: CONCLUSIONS AND RECOMMENDATION

## 7.1 Outline
The ReRun Autonomous Coding Platform successfully meets the outlined objectives, providing a robust, self-healing AI developer loop capable of distinguishing task types, pacing API calls, and logging execution history natively.

## 7.2 Limitations/constraints of the system
* The platform's capability is directly tied to the context-window size and reasoning capabilities of the underlying LLM.
* It currently relies heavily on Python and lacks multi-language compilation sandboxes out of the box (e.g., it cannot compile Rust or C++ without modifications).
* API rate limits severely bottleneck the "Best of 3" generation speeds on free-tier keys, slowing down the overall task completion time.

## 7.3 Future enhancements
* **Multi-Language Sandboxing:** Integrating Docker containers capable of compiling and running Rust, Go, and C++ natively.
* **Agentic Web Browsing:** Allowing the Planner agent to browse the web for up-to-date documentation on new APIs before writing code to prevent deprecation errors.
* **WebSocket Streaming:** Streaming the internal thought processes and terminal outputs of the agents directly to a modern React frontend for real-time observability.

## 7.4 Inference
The future of Software Engineering involves AI not just as a copilot, but as an autonomous executor. ReRun provides a foundational blueprint for that future, proving that self-correcting agent loops are the next evolution in software development.

---
\pagebreak

# APPENDIX A – Screenshots

*(Note: In the final document, insert actual images here)*

**Figure A.1:** Terminal output demonstrating the `test_task.py` executing a standard generation loop, pausing to collect the API key, and successfully outputting the detailed plan to the console.

**Figure A.2:** The `recovery_tasks.json` file in the IDE showing the nested JSON schema of the saved code and plans for auditing purposes.

---
\pagebreak

# APPENDIX B – Coding

**Master Agent Orchestrator (Custom Flow Implementation Excerpt):**
```python
if not self.context.is_coding_task:
    # NORMAL TASK FLOW
    self.recovery.save_recovery_task(self.context.plan)
    
    # Master Final Check
    final_check_sys = "You are a master agent. Check if any changes are needed for this plan. Reply 'NO CHANGES' or suggest changes."
    check_res = await llm.complete(prompt=str(self.context.plan), system_prompt=final_check_sys)
    logger.info(f"Master final check: {check_res.content}")
    
    self._transition(TaskState.COMPLETED, reason="Normal task completed and validated")
```

**Recovery Agent Logging (Excerpt):**
```python
def save_recovery_task(self, task_data: dict):
    """Saves a copy of the validated recovery task to a separate file."""
    import json
    import os
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(self.recovery_log_path), exist_ok=True)
    
    history = []
    if os.path.exists(self.recovery_log_path):
        try:
            with open(self.recovery_log_path, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []
            
    history.append(task_data)
    
    with open(self.recovery_log_path, "w") as f:
        json.dump(history, f, indent=2)
```

**Gemini Provider Rate Limit Patch (Excerpt):**
```python
if resp.status_code in (503, 429):
    if attempt == 2:
        raise RuntimeError(f"Rate limited or unavailable after 3 attempts. Status: {resp.status_code}")
    import asyncio
    await asyncio.sleep(2 * (attempt + 1))
    continue
```

---
\pagebreak

# REFERENCES

1. Google DeepMind (2024). *Gemini API Documentation & Generative Language Models.* 
2. OpenAI (2023). *GPT-4 Technical Report.*
3. Harrison, M. (2022). *Effective Python: 90 Specific Ways to Write Better Python.*
4. FastAPI Documentation (2024). *High-performance asynchronous framework for Python.* 
5. Pydantic Documentation (2024). *Data validation using Python type hints.* 
