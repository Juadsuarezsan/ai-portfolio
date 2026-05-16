"""Hand-written DAGs for the validation + execution harness."""
from __future__ import annotations

GOOD_DAGS = [
    {
        "id": "good-summary",
        "expect_valid": True,
        "expect_run_success": True,
        "dag": {
            "goal": "Summarize a repo and post the summary to Slack.",
            "nodes": [
                {"id": "n1", "name": "Repo summary", "tool": "github", "action": "get_repo_summary",
                 "params": {"repo": "anthropics/claude-code"}, "requires_approval": False, "depends_on": []},
                {"id": "n2", "name": "Post to Slack", "tool": "slack", "action": "post_message",
                 "params": {"channel": "#ai", "text": "{{n1.repo}} has {{n1.open_issues_count}} open issues."},
                 "requires_approval": True, "depends_on": ["n1"]},
            ],
            "estimated_duration_minutes": 2,
        },
    },
    {
        "id": "good-parallel-fanout",
        "expect_valid": True,
        "expect_run_success": True,
        "dag": {
            "goal": "Fetch two issues in parallel and post a roll-up.",
            "nodes": [
                {"id": "i1", "name": "Issue 1", "tool": "github", "action": "get_issue",
                 "params": {"repo": "anthropics/claude-code", "number": 42},
                 "requires_approval": False, "depends_on": []},
                {"id": "i2", "name": "Issue 2", "tool": "github", "action": "get_issue",
                 "params": {"repo": "anthropics/claude-code", "number": 99},
                 "requires_approval": False, "depends_on": []},
                {"id": "post", "name": "Post roll-up", "tool": "slack", "action": "post_message",
                 "params": {"channel": "#ai", "text": "Issues: {{i1.title}} and {{i2.title}}"},
                 "requires_approval": True, "depends_on": ["i1", "i2"]},
            ],
            "estimated_duration_minutes": 3,
        },
    },
    {
        "id": "good-no-approval-needed",
        "expect_valid": True,
        "expect_run_success": True,
        "dag": {
            "goal": "Just read repo state.",
            "nodes": [
                {"id": "n1", "name": "Repo summary", "tool": "github", "action": "get_repo_summary",
                 "params": {"repo": "x/y"}, "requires_approval": False, "depends_on": []},
            ],
            "estimated_duration_minutes": 1,
        },
    },
    {
        "id": "good-chain",
        "expect_valid": True,
        "expect_run_success": True,
        "dag": {
            "goal": "Read issue, create a follow-up.",
            "nodes": [
                {"id": "read", "name": "Read", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 7},
                 "requires_approval": False, "depends_on": []},
                {"id": "create", "name": "Create follow-up", "tool": "github", "action": "create_issue",
                 "params": {"repo": "x/y", "title": "Follow-up to {{read.title}}", "body": "ref #{{read.number}}"},
                 "requires_approval": True, "depends_on": ["read"]},
            ],
            "estimated_duration_minutes": 2,
        },
    },
    {
        "id": "good-three-level",
        "expect_valid": True,
        "expect_run_success": True,
        "dag": {
            "goal": "Read, post, then a derived post.",
            "nodes": [
                {"id": "r", "name": "Read", "tool": "github", "action": "get_repo_summary",
                 "params": {"repo": "a/b"}, "requires_approval": False, "depends_on": []},
                {"id": "p1", "name": "Post 1", "tool": "slack", "action": "post_message",
                 "params": {"channel": "#a", "text": "{{r.open_issues_count}} issues"},
                 "requires_approval": True, "depends_on": ["r"]},
                {"id": "p2", "name": "Post 2", "tool": "slack", "action": "post_message",
                 "params": {"channel": "#b", "text": "Posted in #a"},
                 "requires_approval": True, "depends_on": ["p1"]},
            ],
            "estimated_duration_minutes": 3,
        },
    },
]

BAD_DAGS = [
    {
        "id": "bad-cycle",
        "expect_valid": False,
        "expect_run_success": False,
        "reason": "cycle",
        "dag": {
            "goal": "Cycle: a -> b -> a",
            "nodes": [
                {"id": "a", "name": "A", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 1},
                 "requires_approval": False, "depends_on": ["b"]},
                {"id": "b", "name": "B", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 2},
                 "requires_approval": False, "depends_on": ["a"]},
            ],
        },
    },
    {
        "id": "bad-unknown-tool",
        "expect_valid": False,
        "expect_run_success": False,
        "reason": "unknown_tool",
        "dag": {
            "goal": "Use a fictional tool.",
            "nodes": [
                {"id": "n1", "name": "X", "tool": "linkedin", "action": "post_update",
                 "params": {"text": "hello"}, "requires_approval": True, "depends_on": []},
            ],
        },
    },
    {
        "id": "bad-missing-dep",
        "expect_valid": False,
        "expect_run_success": False,
        "reason": "missing_dependency",
        "dag": {
            "goal": "Reference n5 from n2 without listing it.",
            "nodes": [
                {"id": "n1", "name": "1", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 1}, "requires_approval": False, "depends_on": []},
                {"id": "n2", "name": "2", "tool": "slack", "action": "post_message",
                 "params": {"channel": "#x", "text": "{{n5.title}}"},   # n5 not in depends_on
                 "requires_approval": True, "depends_on": ["n1"]},
            ],
        },
    },
    {
        "id": "bad-self-ref",
        "expect_valid": False,
        "expect_run_success": False,
        "reason": "self_reference",
        "dag": {
            "goal": "Self-reference.",
            "nodes": [
                {"id": "n1", "name": "1", "tool": "github", "action": "create_issue",
                 "params": {"repo": "x/y", "title": "{{n1.title}}"},
                 "requires_approval": True, "depends_on": []},
            ],
        },
    },
    {
        "id": "bad-duplicate-ids",
        "expect_valid": False,
        "expect_run_success": False,
        "reason": "duplicate_ids",
        "dag": {
            "goal": "Duplicate ids.",
            "nodes": [
                {"id": "n1", "name": "1", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 1}, "requires_approval": False, "depends_on": []},
                {"id": "n1", "name": "1b", "tool": "github", "action": "get_issue",
                 "params": {"repo": "x/y", "number": 2}, "requires_approval": False, "depends_on": []},
            ],
        },
    },
]
