# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Install dependencies**: `uv sync` (uses uv.lock)
- **Run the application**: `python ui.py` (launches Gradio interface)
- **Run core logic directly**: `python main.py` (for testing state machine)

## Project Architecture

This is a conversational SOP (Standard Operating Procedure) framework that implements a return processing workflow using finite state machines. The architecture consists of:

### Core Components

1. **State Machine (`main.py`)**:
   - Uses `transitions` library to implement a finite state machine
   - Defines `States` enum with 6 states: COLLECTING_ORDER_ID → CHECKING_RETURN_ELIGIBILITY → COLLECTING_RETURN_REASON → CHECKING_REASON_VALIDITY → PROCESSING_RETURN → COMPLETED
   - `ReturnProcessor` class manages state transitions and business logic
   - Integrates with `agno` AI agent framework using OpenAI GPT models

2. **UI Layer (`ui.py`)**:
   - Gradio-based chat interface that wraps the core state machine
   - `run()` function serves as the main entry point for user interactions
   - Passes conversation history and current date to the return processor

### Key Dependencies

- **agno**: AI agent framework for conversational interactions
- **transitions**: State machine implementation
- **gradio**: Web-based chat interface
- **openai**: LLM integration (currently using gpt-5-mini)

### State Flow

The return processing follows this workflow:
1. Collect order ID from user
2. Check if order is eligible for return
3. Collect return reason from user
4. Validate the return reason
5. Process the return
6. Complete the workflow

Each state has corresponding trigger methods that advance the workflow or terminate it based on business rules.

### Development Notes

- The main logic is partially implemented with some placeholder/test code (random number generation)
- The AI agent in `collect_order_id()` currently has hardcoded instructions for "loan number" capture
- State machine callbacks are configured but not all are fully implemented