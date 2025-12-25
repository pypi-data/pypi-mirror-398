# Custom Callbacks

Examples of using custom callbacks with batch evaluation.

## Basic Callback

```python
from rait_connector import RAITClient

client = RAITClient()

def my_callback(summary):
    print(f"Evaluation complete: {summary['successful']}/{summary['total']}")

client.evaluate_batch(prompts, on_complete=my_callback)
```

## Logging Callback

```python
import logging

logger = logging.getLogger(__name__)

def log_results(summary):
    logger.info(f"Batch evaluation completed")
    logger.info(f"Total: {summary['total']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")

    for error in summary['errors']:
        logger.error(f"Failed {error['prompt_id']}: {error['error']}")

client.evaluate_batch(prompts, on_complete=log_results)
```

## Database Storage Callback

```python
import sqlite3

def save_to_database(summary):
    conn = sqlite3.connect('evaluations.db')
    cursor = conn.cursor()

    for result in summary['results']:
        cursor.execute("""
            INSERT INTO evaluations (prompt_id, model_name, timestamp, status)
            VALUES (?, ?, ?, ?)
        """, (
            result['prompt_id'],
            result['model_name'],
            result['timestamp'],
            'success'
        ))

    for error in summary['errors']:
        cursor.execute("""
            INSERT INTO evaluations (prompt_id, status, error_message)
            VALUES (?, ?, ?)
        """, (
            error['prompt_id'],
            'failed',
            error['error']
        ))

    conn.commit()
    conn.close()

client.evaluate_batch(prompts, on_complete=save_to_database)
```

## Notification Callback

```python
import requests

def send_notification(summary):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    message = {
        "text": f"Batch evaluation complete: {summary['successful']}/{summary['total']} successful"
    }

    if summary['failed'] > 0:
        message["text"] += f"\n{summary['failed']} evaluations failed"

    requests.post(webhook_url, json=message)

client.evaluate_batch(prompts, on_complete=send_notification)
```

## Metrics Aggregation Callback

```python
from collections import defaultdict

def aggregate_metrics(summary):
    metric_scores = defaultdict(list)

    for result in summary['results']:
        for dimension in result['ethical_dimensions']:
            for metric in dimension['dimension_metrics']:
                metric_name = metric['metric_name']
                metadata = metric.get('metric_metadata', {})

                # Extract scores
                for key, value in metadata.items():
                    if 'score' in key and isinstance(value, (int, float)):
                        metric_scores[metric_name].append(value)

    # Calculate averages
    print("\nAverage Scores:")
    for metric_name, scores in metric_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            print(f"  {metric_name}: {avg_score:.2f}")

client.evaluate_batch(prompts, on_complete=aggregate_metrics)
```

## File Export Callback

```python
import json
from datetime import datetime

def export_results(summary):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_results_{timestamp}.json"

    with open(filename, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Results exported to {filename}")

client.evaluate_batch(prompts, on_complete=export_results)
```

## Error Handling in Callbacks

```python
import logging

logger = logging.getLogger(__name__)

def safe_callback(summary):
    try:
        # Your callback logic here
        process_results(summary)
        send_notifications(summary)
        save_to_database(summary)
    except Exception as e:
        logger.error(f"Callback error: {e}")
        # Don't raise - callback errors are logged but don't stop execution

client.evaluate_batch(prompts, on_complete=safe_callback)
```

## Multiple Actions Callback

```python
def multi_action_callback(summary):
    # 1. Log results
    print(f"Completed: {summary['successful']}/{summary['total']}")

    # 2. Save to file
    with open('latest_results.json', 'w') as f:
        json.dump(summary, f, indent=2)

    # 3. Update metrics dashboard
    update_dashboard(summary)

    # 4. Send alert if failures
    if summary['failed'] > 0:
        send_alert(f"{summary['failed']} evaluations failed")

    # 5. Archive results
    archive_results(summary)

client.evaluate_batch(prompts, on_complete=multi_action_callback)
```

## Conditional Callback

```python
def conditional_callback(summary):
    success_rate = summary['successful'] / summary['total']

    if success_rate < 0.9:
        # Alert on low success rate
        send_alert(f"Low success rate: {success_rate:.1%}")

    if summary['failed'] > 10:
        # Special handling for many failures
        investigate_failures(summary['errors'])

    # Always log
    log_summary(summary)

client.evaluate_batch(prompts, on_complete=conditional_callback)
```

## Class-Based Callback

```python
class EvaluationMonitor:
    def __init__(self):
        self.total_evaluations = 0
        self.total_failures = 0

    def __call__(self, summary):
        self.total_evaluations += summary['total']
        self.total_failures += summary['failed']

        print(f"Batch complete: {summary['successful']}/{summary['total']}")
        print(f"Overall: {self.total_evaluations} total, {self.total_failures} failed")

monitor = EvaluationMonitor()

# Use same monitor across multiple batches
client.evaluate_batch(batch1, on_complete=monitor)
client.evaluate_batch(batch2, on_complete=monitor)
client.evaluate_batch(batch3, on_complete=monitor)

print(f"\nFinal stats: {monitor.total_evaluations} evaluations, {monitor.total_failures} failures")
```
