"""
Pipeline System Configuration

Configuration settings for the Pipeline n8n alternative tool.
Uses OpenAI-compatible API with custom base URI.
"""

import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# API Configuration
# =============================================================================

# OpenAI-compatible API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# LLM Configuration
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
DEFAULT_MAX_TOKENS = int(os.getenv("DEFAULT_MAX_TOKENS", "8000"))
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

# =============================================================================
# System Limits
# =============================================================================

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "200000"))
MAX_CHECKPOINT_TIMEOUT_MINUTES = int(os.getenv("MAX_CHECKPOINT_TIMEOUT_MINUTES", "480"))
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "5"))
MAX_REVISION_ITERATIONS = int(os.getenv("MAX_REVISION_ITERATIONS", "5"))

# =============================================================================
# File System Configuration
# =============================================================================

BASE_PIPELINES_PATH = os.getenv("BASE_PIPELINES_PATH", "./pipelines")
TEMP_CLEANUP_ON_NEXT_CHECKPOINT = True  # Delete after next checkpoint starts
ARCHIVE_RETENTION_DAYS = int(os.getenv("ARCHIVE_RETENTION_DAYS", "365"))
ERROR_RETENTION_DAYS = int(os.getenv("ERROR_RETENTION_DAYS", "90"))

# Directory names (relative to pipeline directory)
PIPELINE_SYSTEM_DIR = ".pipeline_system"
PIPELINE_DB_DIR = "db"
PIPELINE_DEFINITIONS_DIR = "definitions"
PIPELINE_LOGS_DIR = "logs"
PIPELINE_RUNS_DIR = "runs"
PIPELINE_TEMP_DIR = ".temp"
PIPELINE_ARCHIVED_DIR = ".archived"
PIPELINE_ERRORED_DIR = ".errored"

# Database file name
DB_FILENAME = "state.db"

# =============================================================================
# Execution Configuration
# =============================================================================

DEFAULT_RETRY_DELAY_SECONDS = int(os.getenv("DEFAULT_RETRY_DELAY_SECONDS", "5"))

# Retry on failure options
RetryOnFailure = Literal["rollback_checkpoint", "pause_pipeline"]

# Timeout actions
OnTimeout = Literal["rollback_checkpoint", "pause_pipeline"]

# =============================================================================
# Logging Configuration
# =============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_MAX_SIZE_MB = int(os.getenv("LOG_FILE_MAX_SIZE_MB", "50"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))
SYSTEM_LOG_FILENAME = "system.log"

# =============================================================================
# Database Configuration
# =============================================================================

DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_TIMEOUT_SECONDS = int(os.getenv("DB_TIMEOUT_SECONDS", "30"))

# =============================================================================
# Pipeline Run Status Enum
# =============================================================================

PipelineRunStatus = Literal["not_started", "in_progress", "paused", "completed", "failed"]

# =============================================================================
# Checkpoint Execution Status Enum
# =============================================================================

CheckpointExecutionStatus = Literal[
    "pending",
    "waiting_approval_to_start",
    "in_progress",
    "waiting_approval_to_complete",
    "completed",
    "failed"
]

# =============================================================================
# Execution Mode Enum
# =============================================================================

ExecutionMode = Literal["agentic", "script", "human_only"]

# =============================================================================
# Agent Creation Mode Enum
# =============================================================================

AgentCreationMode = Literal["meta_agent", "predefined", "single"]

# =============================================================================
# Discussion Mode Enum
# =============================================================================

DiscussionMode = Literal["sequential", "council", "parallel", "debate"]

# =============================================================================
# Validation Mode Enum
# =============================================================================

ValidationMode = Literal["llm_schema", "llm_custom", "both"]

# =============================================================================
# Schema Validation Strictness Enum
# =============================================================================

SchemaValidationStrictness = Literal["strict", "lenient"]

# =============================================================================
# On Validation Failure Enum
# =============================================================================

OnValidationFailure = Literal["retry", "ask_human", "fail_checkpoint"]

# =============================================================================
# Rollback Type Enum
# =============================================================================

RollbackType = Literal["checkpoint_level", "run_level"]

# =============================================================================
# Rollback Triggered By Enum
# =============================================================================

RollbackTriggeredBy = Literal["user_request", "checkpoint_failure"]

# =============================================================================
# Human Interaction Type Enum
# =============================================================================

HumanInteractionType = Literal[
    "approval_to_start",
    "approval_to_complete",
    "revision_request",
    "script_input",
    "validation_feedback"
]

# =============================================================================
# Input Field Type Enum
# =============================================================================

InputFieldType = Literal["text", "number", "boolean", "file", "multiline_text"]

# =============================================================================
# Artifact Format Enum
# =============================================================================

ArtifactFormat = Literal["json", "md", "mmd", "txt", "py", "html", "csv"]

# =============================================================================
# Content Format Enum
# =============================================================================

ContentFormat = Literal["markdown", "xml", "json"]

# =============================================================================
# Injection Point Enum
# =============================================================================

InjectionPoint = Literal["before_task_prompt", "after_task_prompt", "before_system_prompt"]

# =============================================================================
# Log Level Enum
# =============================================================================

LogLevel = Literal["info", "warning", "error"]
