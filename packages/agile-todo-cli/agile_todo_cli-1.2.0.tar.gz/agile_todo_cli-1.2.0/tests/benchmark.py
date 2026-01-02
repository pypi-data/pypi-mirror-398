"""Performance benchmarking for Todo CLI."""

import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Dict, List

from todo_cli.database import Database
from todo_cli.projects import ProjectManager
from todo_cli.models import Priority, Status


class PerformanceBenchmark:
    """Performance benchmarking framework for Todo CLI."""

    def __init__(self, db_path: Path):
        """Initialize benchmark with database path.

        Args:
            db_path: Path to test database
        """
        self.db_path = db_path
        self.db = Database(db_path)
        self.pm = ProjectManager(db_path)
        self.results: Dict[str, float] = {}

    def setup_large_dataset(self, num_tasks: int = 10000, num_projects: int = 100):
        """Create large test dataset for benchmarking.

        Args:
            num_tasks: Number of tasks to create (default 10,000)
            num_projects: Number of projects to create (default 100)
        """
        print(f"Creating {num_projects} projects...")
        projects = []
        for i in range(num_projects):
            project = self.pm.create_project(
                f"Project {i:03d}",
                description=f"Test project {i} for benchmarking"
            )
            projects.append(project)

        print(f"Creating {num_tasks} tasks...")
        task_templates = [
            "Implement feature",
            "Fix bug",
            "Write documentation",
            "Add tests",
            "Code review",
            "Deploy to production",
            "Update dependencies",
            "Refactor code",
            "Optimize performance",
            "Security audit"
        ]

        priorities = list(Priority)
        statuses = list(Status)

        # Create tasks in batches for better performance
        batch_size = 1000
        for batch_start in range(0, num_tasks, batch_size):
            batch_end = min(batch_start + batch_size, num_tasks)
            print(f"  Creating tasks {batch_start}-{batch_end}...")

            for i in range(batch_start, batch_end):
                task = random.choice(task_templates) + f" #{i:05d}"
                priority = random.choice(priorities)
                status = random.choice(statuses)

                # 80% of tasks assigned to projects
                project_id = None
                if random.random() < 0.8:
                    project_id = random.choice(projects).id

                # 30% of tasks have tags
                tags = []
                if random.random() < 0.3:
                    num_tags = random.randint(1, 3)
                    tags = [f"tag{random.randint(1, 20)}" for _ in range(num_tags)]

                # 20% of tasks have due dates
                due_date = None
                if random.random() < 0.2:
                    days_offset = random.randint(-30, 30)
                    due_date = datetime.now() + timedelta(days=days_offset)

                # Create task
                todo = self.db.add(
                    task=task,
                    priority=priority,
                    project_id=project_id,
                    tags=tags,
                    due_date=due_date
                )

                # Update status if not TODO
                if status != Status.TODO:
                    todo.status = status
                    if status == Status.DONE:
                        todo.completed_at = datetime.now()
                    self.db.update(todo)

                # Add random time spent (10% of tasks)
                if random.random() < 0.1:
                    todo.time_spent = timedelta(seconds=random.randint(300, 7200))
                    self.db.update(todo)

        print(f"Dataset created: {num_tasks} tasks across {num_projects} projects")

    def benchmark_query(self, name: str, query_func: Callable, iterations: int = 10) -> float:
        """Benchmark a query function.

        Args:
            name: Name of the benchmark
            query_func: Function to benchmark
            iterations: Number of times to run (default 10)

        Returns:
            Average execution time in milliseconds
        """
        times = []

        # Warm-up run
        query_func()

        # Benchmark runs
        for _ in range(iterations):
            start = time.perf_counter()
            query_func()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        self.results[name] = avg_time

        print(f"\n{name}:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

        return avg_time

    def verify_index_usage(self, query: str, params: tuple = ()) -> Dict:
        """Verify index usage for a query using EXPLAIN QUERY PLAN.

        Args:
            query: SQL query to analyze
            params: Query parameters

        Returns:
            Dictionary with index usage information
        """
        with self.db._get_conn() as conn:
            # Get query plan
            plan_query = f"EXPLAIN QUERY PLAN {query}"
            rows = conn.execute(plan_query, params).fetchall()

            result = {
                "query": query,
                "plan": [dict(row) for row in rows],
                "uses_index": False,
                "index_names": []
            }

            # Check if any step uses an index
            for row in rows:
                detail = row["detail"].lower()
                if "using index" in detail or "index" in detail:
                    result["uses_index"] = True
                    # Extract index name if present
                    if "index" in detail:
                        parts = detail.split("index")
                        if len(parts) > 1:
                            index_part = parts[1].strip()
                            index_name = index_part.split()[0]
                            if index_name and index_name not in result["index_names"]:
                                result["index_names"].append(index_name)

            return result

    def run_all_benchmarks(self) -> Dict[str, float]:
        """Run all standard benchmarks.

        Returns:
            Dictionary of benchmark results
        """
        print("\n" + "="*60)
        print("Running Performance Benchmarks")
        print("="*60)

        # Benchmark: List all tasks
        self.benchmark_query(
            "List all tasks (no filter)",
            lambda: self.db.list_all()
        )

        # Benchmark: List with project filter
        projects = self.pm.list_projects()
        if projects:
            project_id = projects[0].id
            self.benchmark_query(
                "List tasks by project",
                lambda: self.db.list_all(project_id=project_id)
            )

        # Benchmark: List with status filter
        self.benchmark_query(
            "List tasks by status",
            lambda: self.db.list_all(status=Status.TODO)
        )

        # Benchmark: Combined filters
        if projects:
            self.benchmark_query(
                "List tasks by project + status",
                lambda: self.db.list_all(project_id=project_id, status=Status.TODO)
            )

        # Benchmark: Project stats
        if projects:
            self.benchmark_query(
                "Get project stats",
                lambda: self.pm.get_project_stats(project_id)
            )

        # Benchmark: List all projects
        self.benchmark_query(
            "List all projects",
            lambda: self.pm.list_projects()
        )

        print("\n" + "="*60)
        print("Benchmark Summary")
        print("="*60)
        for name, avg_time in self.results.items():
            status = "✓ PASS" if avg_time < 200 else "✗ SLOW"
            print(f"{status} {name}: {avg_time:.2f}ms")

        return self.results

    def verify_all_indexes(self) -> List[Dict]:
        """Verify index usage for all critical queries.

        Returns:
            List of index verification results
        """
        print("\n" + "="*60)
        print("Verifying Index Usage")
        print("="*60)

        queries = [
            ("List all active todos", "SELECT * FROM todos WHERE status != 'done' ORDER BY priority ASC, due_date ASC NULLS LAST", ()),
            ("Filter by project_id", "SELECT * FROM todos WHERE project_id = ?", (1,)),
            ("Filter by status", "SELECT * FROM todos WHERE status = ?", ("todo",)),
            ("Get project", "SELECT * FROM projects WHERE id = ?", (1,)),
        ]

        results = []
        for name, query, params in queries:
            print(f"\n{name}:")
            result = self.verify_index_usage(query, params)
            results.append(result)

            print(f"  Uses index: {result['uses_index']}")
            if result["index_names"]:
                print(f"  Indexes: {', '.join(result['index_names'])}")

            for step in result["plan"]:
                print(f"  - {step['detail']}")

        return results
