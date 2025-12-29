---
id: hitl-mixin
title: HITLClientMixin
sidebar_position: 6
---

# HITLClientMixin

Provides Human-in-the-Loop (HITL) assignment management operations for the Synapse backend.

## Overview

The `HITLClientMixin` handles all operations related to human-in-the-loop workflows, including assignment management and tagging. This mixin is automatically included in the `BackendClient` and provides methods for managing human annotation and review workflows.

## Assignment Operations

### `get_assignment(pk)`

Retrieve detailed information about a specific assignment.

```python
assignment = client.get_assignment(789)
print(f"Assignment: {assignment['id']}")
print(f"Project: {assignment['project']}")
print(f"Status: {assignment['status']}")
print(f"Assignee: {assignment['assignee']}")
print(f"Data: {assignment['data']}")
```

**Parameters:**

- `pk` (int): Assignment ID

**Returns:**

- `dict`: Complete assignment information

**Assignment structure:**

- `id`: Assignment ID
- `project`: Associated project ID
- `status`: Assignment status (`pending`, `in_progress`, `completed`, `rejected`)
- `assignee`: User ID of assigned reviewer
- `data`: Assignment data and annotations
- `file`: Associated files
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `metadata`: Additional assignment metadata

### `list_assignments(params=None, url_conversion=None, list_all=False)`

List assignments with comprehensive filtering and pagination support.

```python
# List assignments for a specific project
assignments = client.list_assignments(params={'project': 123})

# List assignments by status
pending_assignments = client.list_assignments(params={
    'project': 123,
    'status': 'pending'
})

# List assignments for specific assignee
user_assignments = client.list_assignments(params={
    'assignee': 456
})

# Get all assignments (handles pagination automatically)
all_assignments = client.list_assignments(list_all=True)

# List assignments with custom URL conversion for files
assignments = client.list_assignments(
    params={'project': 123},
    url_conversion={'files': lambda url: f"https://cdn.example.com{url}"}
)
```

**Parameters:**

- `params` (dict, optional): Filtering parameters
- `url_conversion` (dict, optional): Custom URL conversion for file fields
- `list_all` (bool): If True, automatically handles pagination

**Common filtering params:**

- `project`: Filter by project ID
- `status`: Filter by assignment status
- `assignee`: Filter by assigned user ID
- `created_after`: Filter by creation date
- `updated_after`: Filter by last update date
- `priority`: Filter by assignment priority
- `search`: Text search in assignment content

**Returns:**

- `tuple`: (assignments_list, total_count) if `list_all=False`
- `list`: All assignments if `list_all=True`

### `set_tags_assignments(data, params=None)`

Set tags for multiple assignments in batch operations.

```python
# Set tags for multiple assignments
client.set_tags_assignments({
    'assignment_ids': [789, 790, 791],
    'tag_ids': [1, 2, 3]  # Tag IDs to apply
})

# Set tags with replacement option
client.set_tags_assignments(
    {
        'assignment_ids': [789, 790],
        'tag_ids': [1, 2]
    },
    params={'replace': True}  # Replace existing tags
)

# Set priority tags
client.set_tags_assignments({
    'assignment_ids': [789],
    'tag_ids': [5]  # High priority tag
})
```

**Parameters:**

- `data` (dict): Batch tagging data
- `params` (dict, optional): Additional parameters

**Data structure:**

- `assignment_ids` (list): List of assignment IDs to tag
- `tag_ids` (list): List of tag IDs to apply

**Optional params:**

- `replace` (bool): If True, replace existing tags; if False, add to existing
- `notify` (bool): If True, notify assignees of tag changes

**Returns:**

- `dict`: Tagging operation result

## HITL Workflow Examples

### Assignment Queue Management

```python
def manage_assignment_queue(project_id, max_assignments_per_user=10):
    """Manage assignment distribution and queue."""

    # Get pending assignments
    pending = client.list_assignments(params={
        'project': project_id,
        'status': 'pending'
    })

    # Get active assignments by user
    active = client.list_assignments(params={
        'project': project_id,
        'status': 'in_progress'
    })

    # Count assignments per user
    user_workload = {}
    for assignment in active[0]:
        user_id = assignment['assignee']
        user_workload[user_id] = user_workload.get(user_id, 0) + 1

    print(f"Pending assignments: {len(pending[0])}")
    print("User workload:")
    for user_id, count in user_workload.items():
        print(f"  User {user_id}: {count} assignments")

    # Find users with capacity
    available_users = [
        user_id for user_id, count in user_workload.items()
        if count < max_assignments_per_user
    ]

    return {
        'pending_count': len(pending[0]),
        'user_workload': user_workload,
        'available_users': available_users
    }

# Monitor queue
queue_status = manage_assignment_queue(123)
```

### Quality Control Workflow

```python
def quality_control_workflow(project_id):
    """Implement quality control for completed assignments."""

    # Get completed assignments
    completed = client.list_assignments(params={
        'project': project_id,
        'status': 'completed'
    })

    quality_results = []

    for assignment in completed[0]:
        assignment_id = assignment['id']

        # Get detailed assignment data
        detailed = client.get_assignment(assignment_id)

        # Perform quality checks (custom logic)
        quality_score = calculate_quality_score(detailed)

        if quality_score >= 0.9:
            # High quality - approve
            tag_name = 'approved'
            tag_id = get_tag_id(tag_name)  # Custom function

            client.set_tags_assignments({
                'assignment_ids': [assignment_id],
                'tag_ids': [tag_id]
            })

        elif quality_score >= 0.7:
            # Medium quality - needs review
            tag_name = 'needs_review'
            tag_id = get_tag_id(tag_name)

            client.set_tags_assignments({
                'assignment_ids': [assignment_id],
                'tag_ids': [tag_id]
            })

        else:
            # Low quality - reject
            tag_name = 'rejected'
            tag_id = get_tag_id(tag_name)

            client.set_tags_assignments({
                'assignment_ids': [assignment_id],
                'tag_ids': [tag_id]
            })

        quality_results.append({
            'assignment_id': assignment_id,
            'quality_score': quality_score,
            'action': tag_name
        })

    return quality_results

def calculate_quality_score(assignment):
    """Calculate quality score for an assignment (custom implementation)."""
    # Implement your quality scoring logic here
    # This could include annotation completeness, consistency, etc.
    import random
    return random.uniform(0.5, 1.0)  # Placeholder

def get_tag_id(tag_name):
    """Get tag ID by name (custom implementation)."""
    # You might want to cache tag mappings or use a lookup service
    tag_mapping = {
        'approved': 1,
        'needs_review': 2,
        'rejected': 3,
        'high_priority': 4,
        'low_priority': 5
    }
    return tag_mapping.get(tag_name, 1)

# Run quality control
quality_results = quality_control_workflow(123)
print(f"Processed {len(quality_results)} assignments")
```

### Assignment Analytics

```python
def assignment_analytics(project_id, days=30):
    """Generate analytics for assignment performance."""
    from datetime import datetime, timedelta

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Get assignments in date range
    assignments = client.list_assignments(params={
        'project': project_id,
        'created_after': start_date.isoformat()
    }, list_all=True)

    # Calculate metrics
    analytics = {
        'total_assignments': len(assignments),
        'status_breakdown': {},
        'assignee_performance': {},
        'completion_rate': 0,
        'average_time_to_complete': 0
    }

    completion_times = []

    for assignment in assignments:
        # Status breakdown
        status = assignment['status']
        analytics['status_breakdown'][status] = \
            analytics['status_breakdown'].get(status, 0) + 1

        # Assignee performance
        assignee = assignment.get('assignee')
        if assignee:
            if assignee not in analytics['assignee_performance']:
                analytics['assignee_performance'][assignee] = {
                    'total': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'pending': 0
                }

            analytics['assignee_performance'][assignee]['total'] += 1
            analytics['assignee_performance'][assignee][status] += 1

        # Calculate completion time
        if status == 'completed':
            created = datetime.fromisoformat(assignment['created_at'].replace('Z', '+00:00'))
            updated = datetime.fromisoformat(assignment['updated_at'].replace('Z', '+00:00'))
            completion_time = (updated - created).total_seconds() / 3600  # hours
            completion_times.append(completion_time)

    # Calculate rates
    completed_count = analytics['status_breakdown'].get('completed', 0)
    analytics['completion_rate'] = completed_count / analytics['total_assignments'] if analytics['total_assignments'] > 0 else 0
    analytics['average_time_to_complete'] = sum(completion_times) / len(completion_times) if completion_times else 0

    return analytics

# Generate analytics
analytics = assignment_analytics(123, days=30)
print(f"Assignment Analytics:")
print(f"  Total assignments: {analytics['total_assignments']}")
print(f"  Completion rate: {analytics['completion_rate']:.2%}")
print(f"  Average completion time: {analytics['average_time_to_complete']:.1f} hours")
print(f"  Status breakdown: {analytics['status_breakdown']}")
```

### Batch Assignment Operations

```python
def batch_assignment_operations(project_id):
    """Perform batch operations on assignments."""

    # Get assignments that need batch processing
    assignments = client.list_assignments(params={
        'project': project_id,
        'status': 'completed'
    }, list_all=True)

    # Group assignments by assignee for performance review
    assignee_groups = {}
    for assignment in assignments:
        assignee = assignment.get('assignee')
        if assignee:
            if assignee not in assignee_groups:
                assignee_groups[assignee] = []
            assignee_groups[assignee].append(assignment['id'])

    # Apply performance-based tags
    for assignee, assignment_ids in assignee_groups.items():
        assignment_count = len(assignment_ids)

        if assignment_count >= 50:
            # High performer
            tag_id = get_tag_id('high_performer')
        elif assignment_count >= 20:
            # Regular performer
            tag_id = get_tag_id('regular_performer')
        else:
            # New contributor
            tag_id = get_tag_id('new_contributor')

        # Apply tags in batch
        client.set_tags_assignments({
            'assignment_ids': assignment_ids,
            'tag_ids': [tag_id]
        })

        print(f"Tagged {assignment_count} assignments for user {assignee}")

    return assignee_groups

# Run batch operations
assignee_groups = batch_assignment_operations(123)
```

### Assignment Workflow Automation

```python
def automate_assignment_workflow(project_id):
    """Automate assignment workflow based on rules."""

    # Get all assignments that need processing
    assignments = client.list_assignments(params={
        'project': project_id
    }, list_all=True)

    automation_actions = []

    for assignment in assignments:
        assignment_id = assignment['id']
        status = assignment['status']
        created_at = datetime.fromisoformat(assignment['created_at'].replace('Z', '+00:00'))
        age_hours = (datetime.now(created_at.tzinfo) - created_at).total_seconds() / 3600

        actions = []

        # Rule 1: Mark old pending assignments as urgent
        if status == 'pending' and age_hours > 24:
            urgent_tag_id = get_tag_id('urgent')
            client.set_tags_assignments({
                'assignment_ids': [assignment_id],
                'tag_ids': [urgent_tag_id]
            })
            actions.append('marked_urgent')

        # Rule 2: Escalate very old in-progress assignments
        if status == 'in_progress' and age_hours > 72:
            escalation_tag_id = get_tag_id('escalated')
            client.set_tags_assignments({
                'assignment_ids': [assignment_id],
                'tag_ids': [escalation_tag_id]
            })
            actions.append('escalated')

        # Rule 3: Archive very old completed assignments
        if status == 'completed' and age_hours > 168:  # 1 week
            archive_tag_id = get_tag_id('archived')
            client.set_tags_assignments({
                'assignment_ids': [assignment_id],
                'tag_ids': [archive_tag_id]
            })
            actions.append('archived')

        if actions:
            automation_actions.append({
                'assignment_id': assignment_id,
                'actions': actions,
                'age_hours': age_hours
            })

    return automation_actions

# Run automation
automation_results = automate_assignment_workflow(123)
print(f"Automated {len(automation_results)} assignments")
```

## Error Handling

```python
from synapse_sdk.clients.exceptions import ClientError

def robust_assignment_operations():
    """Example of robust assignment operations with error handling."""

    try:
        # Try to get assignment
        assignment = client.get_assignment(999)
    except ClientError as e:
        if e.status_code == 404:
            print("Assignment not found")
            return None
        elif e.status_code == 403:
            print("Permission denied - insufficient access rights")
            return None
        else:
            print(f"Error getting assignment: {e}")
            raise

    try:
        # Try to set tags
        client.set_tags_assignments({
            'assignment_ids': [999],
            'tag_ids': [1, 2, 3]
        })
    except ClientError as e:
        if e.status_code == 400:
            print(f"Invalid tagging data: {e.response}")
        elif e.status_code == 404:
            print("Assignment or tags not found")
        else:
            print(f"Error setting tags: {e}")

    return assignment

# Use robust operations
assignment = robust_assignment_operations()
```

## Complete HITL Workflow

```python
def complete_hitl_workflow(project_id):
    """Complete HITL workflow from assignment creation to quality control."""

    print("=== HITL Workflow Started ===")

    # 1. Analyze current assignment status
    print("1. Analyzing assignment status...")
    queue_status = manage_assignment_queue(project_id)
    print(f"Pending assignments: {queue_status['pending_count']}")

    # 2. Run quality control on completed assignments
    print("2. Running quality control...")
    quality_results = quality_control_workflow(project_id)
    print(f"Quality control processed: {len(quality_results)} assignments")

    # 3. Generate analytics
    print("3. Generating analytics...")
    analytics = assignment_analytics(project_id)
    print(f"Completion rate: {analytics['completion_rate']:.2%}")

    # 4. Run automation rules
    print("4. Running automation...")
    automation_results = automate_assignment_workflow(project_id)
    print(f"Automated actions: {len(automation_results)}")

    # 5. Summary
    print("5. Workflow Summary:")
    print(f"  - Total assignments processed: {analytics['total_assignments']}")
    print(f"  - Quality control actions: {len(quality_results)}")
    print(f"  - Automation actions: {len(automation_results)}")

    print("=== HITL Workflow Completed ===")

    return {
        'queue_status': queue_status,
        'quality_results': quality_results,
        'analytics': analytics,
        'automation_results': automation_results
    }

# Run complete workflow
if __name__ == "__main__":
    workflow_results = complete_hitl_workflow(123)
```

## See Also

- [BackendClient](./backend.md) - Main backend client
- [AnnotationClientMixin](./annotation-mixin.md) - Task and annotation management
- [IntegrationClientMixin](./integration-mixin.md) - Plugin and job management
