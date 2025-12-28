"""
MCP 工具注册表

负责：
- 工具定义
- 工具列表管理
"""

from typing import Dict, Any, List


class ToolsRegistry:
    """MCP 工具注册表"""
    
    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """获取所有工具定义"""
        return [
            # 项目上下文
            {
                "name": "get_project_context",
                "description": "Get project context including basic info and current tasks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_tasks": {
                            "type": "boolean",
                            "description": "Whether to include task list",
                            "default": True
                        }
                    }
                }
            },
            {
                "name": "get_project_summary",
                "description": "Get lightweight project overview: milestone stats, task distribution, recent activity, suggested next tasks. Use as initial overview to reduce token consumption.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            
            # 里程碑管理
            {
                "name": "list_project_milestones",
                "description": "List milestones with task statistics. Filter by status: pending/in_progress/completed. Returns task counts and progress.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "description": "Filter milestones by status. Leave empty to get all milestones."
                        }
                    }
                }
            },
            {
                "name": "get_milestone_detail",
                "description": "Get milestone details with task summary (id, task_id, title, status, priority). Use get_task_detail for full task info.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "milestone_id": {"type": "integer", "description": "Milestone ID"},
                        "include_tasks": {"type": "boolean", "description": "Include task list (default: true)", "default": True}
                    },
                    "required": ["milestone_id"]
                }
            },
            {
                "name": "create_milestone",
                "description": "Create milestone with optional tasks. RECOMMENDED: create with tasks together. acceptance_criteria: use single string with \\n separators.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Milestone name (required)"},
                        "description": {"type": "string", "description": "Milestone description (optional)"},
                        "tasks": {
                            "type": "array",
                            "description": "List of tasks to create with milestone (optional)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Task title (required)"},
                                    "description": {"type": "string", "description": "Task description (optional)"},
                                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority (optional, default: medium)"},
                                    "acceptance_criteria": {
                                        "type": "string",
                                        "description": "Acceptance criteria as a SINGLE STRING (optional). System will auto-convert to list. Use \\n to separate multiple criteria."
                                    }
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "create_milestone_tasks",
                "description": "Batch create tasks for a milestone. Auto-generates task IDs (M1-T1, M1-T2...). Create ALL tasks at once.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "milestone_id": {"type": "integer", "description": "Milestone ID"},
                        "tasks": {
                            "type": "array",
                            "description": "List of tasks to create",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Task title (required)"},
                                    "description": {"type": "string", "description": "Task description (optional)"},
                                    "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority (optional, default: medium)"},
                                    "acceptance_criteria": {
                                        "type": "string", 
                                        "description": "Acceptance criteria as a single string (optional). System will automatically convert it to a list. Use newlines to separate multiple criteria if needed."
                                    }
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["milestone_id", "tasks"]
                }
            },
            {
                "name": "delete_milestone_task",
                "description": "Delete a task (cascades to subtasks). WARNING: Cannot be undone.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID to delete"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "delete_milestone",
                "description": "Delete a milestone (cascades to all tasks/subtasks). WARNING: Cannot be undone.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "milestone_id": {"type": "integer", "description": "Milestone ID to delete"}
                    },
                    "required": ["milestone_id"]
                }
            },
            {
                "name": "get_task_detail",
                "description": "Get full task details: description, acceptance_criteria, subtasks, notes, lock status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID (database primary key)"}
                    },
                    "required": ["task_id"]
                }
            },
            
            # 任务管理
            {
                "name": "list_project_tasks",
                "description": "List tasks (summary by default). Use include_details=true for full info, or get_task_detail for specific task.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "cancelled"],
                            "description": "Filter by task status (optional)"
                        },
                        "milestone_id": {
                            "type": "integer",
                            "description": "Filter by milestone ID (optional)"
                        },
                        "title_keyword": {
                            "type": "string",
                            "description": "Filter by title keyword (optional, supports fuzzy search)"
                        },
                        "include_subtasks": {
                            "type": "boolean",
                            "description": "Include subtask details (default: false)",
                            "default": False
                        },
                        "include_details": {
                            "type": "boolean",
                            "description": "Include full task details like description, notes, acceptance_criteria (default: false)",
                            "default": False
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (default: 50, max: 100)",
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "get_my_tasks",
                "description": "Get my assigned/available tasks. Filter by status_filter: pending/in_progress/completed.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status_filter": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed", "cancelled"],
                            "description": "Filter tasks by status. Options: 'pending' (TODO), 'in_progress' (currently working on), 'completed', 'cancelled'. Leave empty to get all tasks."
                        }
                    }
                }
            },
            {
                "name": "claim_task",
                "description": "Claim a task and acquire lock (default 120 minutes)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID"},
                        "lock_duration_minutes": {"type": "integer", "description": "Lock duration in minutes", "default": 120}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "update_task_status",
                "description": "Update task status. REQUIRED: When status='completed', provide summary in 'notes' (accomplishments, files changed, test status).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Task ID"},
                        "status": {"type": "string", "description": "New status", "enum": ["pending", "in_progress", "completed", "cancelled", "postponed"]},
                        "version": {"type": "integer", "description": "Version number for optimistic locking"},
                        "notes": {"type": "string", "description": "Task notes. **REQUIRED when status='completed'** - provide a summary report of what was accomplished"}
                    },
                    "required": ["task_id", "status", "version"]
                }
            },
            {
                "name": "split_task_into_subtasks",
                "description": "Split a main task into multiple subtasks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Main task ID"},
                        "subtasks": {
                            "type": "array",
                            "description": "List of subtasks",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "description": "Subtask title"},
                                    "description": {"type": "string", "description": "Subtask description"},
                                    "estimated_hours": {"type": "number", "description": "Estimated hours"}
                                },
                                "required": ["title"]
                            }
                        }
                    },
                    "required": ["task_id", "subtasks"]
                }
            },
            
            # 子任务管理
            {
                "name": "get_task_subtasks",
                "description": "Get all subtasks of a task",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "description": "Parent task ID"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "update_subtask_status",
                "description": "Update subtask status. REQUIRED: When status='completed', provide summary in 'notes'.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "subtask_id": {"type": "integer", "description": "Subtask ID"},
                        "status": {"type": "string", "description": "New status", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                        "notes": {"type": "string", "description": "Subtask notes. **REQUIRED when status='completed'** - provide a summary report of what was accomplished"}
                    },
                    "required": ["subtask_id", "status"]
                }
            },
            
            # 文档管理
            {
                "name": "get_document_categories",
                "description": "Get available document categories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_document_category",
                "description": "Create document category. Code: lowercase with underscores (e.g. 'custom_api').",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Category code (unique identifier, e.g., 'custom_api')"
                        },
                        "name": {
                            "type": "string",
                            "description": "Category name (e.g., 'Custom API Documentation')"
                        },
                        "description": {
                            "type": "string",
                            "description": "Category description (optional)"
                        },
                        "icon": {
                            "type": "string",
                            "description": "Icon (emoji or icon class name, optional)"
                        },
                        "color": {
                            "type": "string",
                            "description": "Color for tag display (optional)"
                        },
                        "sort_order": {
                            "type": "integer",
                            "description": "Sort order (smaller number appears first, default: 0)"
                        }
                    },
                    "required": ["code", "name"]
                }
            },
            {
                "name": "list_documents",
                "description": "List documents. Filter by title_keyword/category. Default limit: 20.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title_keyword": {
                            "type": "string", 
                            "description": "Filter by title keyword (optional, supports fuzzy search). Example: 'API' will match 'API Documentation', 'User API Guide', etc."
                        },
                        "category": {
                            "type": "string", 
                            "description": "Filter by category code (optional). Use get_document_categories to see available categories."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of documents to return (default: 20, max: 100)",
                            "default": 20
                        }
                    }
                }
            },
            {
                "name": "search_documents",
                "description": "Search documents by keyword",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword"},
                        "category": {"type": "string", "description": "Category filter (optional)"},
                        "limit": {"type": "integer", "description": "Result limit (default: 10)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_document",
                "description": "Create document. For required docs, pass template_id from get_project_context.missing_required[].",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Document title"},
                        "content": {"type": "string", "description": "Document content (Markdown format)"},
                        "category": {"type": "string", "description": "Category code (get from get_document_categories)"},
                        "template_id": {"type": "integer", "description": "Template ID - ONLY pass this when filling a MISSING required document. Get from missing_required[].template_id in get_project_context response. Do NOT pass for regular documents or if all required documents are complete."}
                    },
                    "required": ["title", "content", "category"]
                }
            },
            {
                "name": "get_document_by_id",
                "description": "Get document content by ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "integer", "description": "Document ID (from list_documents)"}
                    },
                    "required": ["document_id"]
                }
            },
            {
                "name": "update_document_by_id",
                "description": "Update document (creates new version).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "integer", "description": "Document ID (from list_documents)"},
                        "content": {"type": "string", "description": "New content"},
                        "change_summary": {"type": "string", "description": "Change summary (optional)"}
                    },
                    "required": ["document_id", "content"]
                }
            },
            {
                "name": "delete_document_by_id",
                "description": "Delete document by ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "integer", "description": "Document ID (from list_documents)"}
                    },
                    "required": ["document_id"]
                }
            },
            {
                "name": "get_document_versions",
                "description": "Get all versions of a document by title",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Document title"}
                    },
                    "required": ["title"]
                }
            },
            
            # Rules 管理
            {
                "name": "get_rules_content",
                "description": "Get project Rules content. Optionally specify ide_type for IDE-specific rules.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ide_type": {
                            "type": "string",
                            "description": "IDE type identifier (optional, e.g., 'cursor', 'windsurf', 'vscode', 'trae', or any custom IDE name). If not specified, returns generic Rules content."
                        }
                    }
                }
            }
        ]
