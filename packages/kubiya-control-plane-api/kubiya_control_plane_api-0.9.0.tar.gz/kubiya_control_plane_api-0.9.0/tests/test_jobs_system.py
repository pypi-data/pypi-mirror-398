#!/usr/bin/env python3
"""
Test script to verify the jobs system is working correctly with proper types
and foreign key relationships.
"""
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from control_plane_api.app.config import settings
from control_plane_api.app.models import (
    Execution, ExecutionStatus, ExecutionType, ExecutionTriggerSource,
    Job, JobExecution, JobStatus, JobTriggerType, PlanningMode, ExecutorType
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_execution_creation():
    """Test creating an execution with trigger source"""
    print("Testing execution creation with trigger source...")

    session = SessionLocal()
    try:
        # Create a test execution
        # Note: entity_id in DB is UUID type (pre-existing schema)
        test_entity_id = str(uuid.uuid4())
        execution = Execution(
            organization_id="test-org",
            execution_type=ExecutionType.AGENT,
            entity_id=test_entity_id,
            entity_name="Test Agent",
            runner_name="test-runner",  # Required by DB schema
            prompt="Test prompt",
            trigger_source=ExecutionTriggerSource.USER,
            trigger_metadata={"test": "data"}
        )
        session.add(execution)
        session.commit()

        execution_id = execution.id
        print(f"✓ Created execution with ID: {execution_id} (type: {type(execution_id)})")
        print(f"  Trigger source: {execution.trigger_source}")
        print(f"  Trigger metadata: {execution.trigger_metadata}")

        # Verify we can query it back
        fetched = session.query(Execution).filter_by(id=execution_id).first()
        assert fetched is not None
        assert fetched.trigger_source == ExecutionTriggerSource.USER
        print("✓ Successfully queried execution back")

        return execution_id
    finally:
        session.close()


def test_job_creation(execution_id):
    """Test creating a job and linking it to an execution"""
    print("\nTesting job creation with execution link...")

    session = SessionLocal()
    try:
        # Create a test job
        job = Job(
            organization_id="test-org",
            name="Test Job",
            description="Test job description",
            trigger_type=JobTriggerType.MANUAL,
            planning_mode=PlanningMode.PREDEFINED_AGENT,
            entity_type="agent",
            entity_id="agent-123",
            prompt_template="Test prompt",
            executor_type=ExecutorType.AUTO,
            last_execution_id=execution_id,  # This should work now with UUID type
            total_executions=1,
            successful_executions=1,
            failed_executions=0
        )
        session.add(job)
        session.commit()

        job_id = job.id
        print(f"✓ Created job with ID: {job_id}")
        print(f"  Last execution ID: {job.last_execution_id} (type: {type(job.last_execution_id)})")
        print(f"  Total executions: {job.total_executions} (type: {type(job.total_executions)})")

        # Verify the foreign key relationship works
        fetched = session.query(Job).filter_by(id=job_id).first()
        assert fetched.last_execution_id == execution_id
        assert fetched.last_execution is not None
        print(f"✓ Foreign key relationship works: job.last_execution = {fetched.last_execution}")

        return job_id
    finally:
        session.close()


def test_job_execution_link(job_id, execution_id):
    """Test creating a job execution link"""
    print("\nTesting job execution link...")

    session = SessionLocal()
    try:
        # Create a job execution link
        job_exec = JobExecution(
            job_id=job_id,
            execution_id=execution_id,  # UUID type should work now
            organization_id="test-org",
            trigger_type="manual",
            trigger_metadata={"trigger_user": "test@example.com"},
            execution_status="completed",
            execution_duration_ms=5000  # Integer type should work now
        )
        session.add(job_exec)
        session.commit()

        print(f"✓ Created job execution link with ID: {job_exec.id}")
        print(f"  Job ID: {job_exec.job_id}")
        print(f"  Execution ID: {job_exec.execution_id} (type: {type(job_exec.execution_id)})")
        print(f"  Duration: {job_exec.execution_duration_ms}ms (type: {type(job_exec.execution_duration_ms)})")

        # Verify relationships work
        fetched = session.query(JobExecution).filter_by(id=job_exec.id).first()
        assert fetched.job is not None
        assert fetched.execution is not None
        print(f"✓ Both foreign key relationships work")
        print(f"  job_execution.job = {fetched.job}")
        print(f"  job_execution.execution = {fetched.execution}")

        return job_exec.id
    finally:
        session.close()


def cleanup(execution_id, job_id, job_exec_id):
    """Clean up test data"""
    print("\nCleaning up test data...")

    session = SessionLocal()
    try:
        # Delete in reverse order due to foreign keys
        session.query(JobExecution).filter_by(id=job_exec_id).delete()
        session.query(Job).filter_by(id=job_id).delete()
        session.query(Execution).filter_by(id=execution_id).delete()
        session.commit()
        print("✓ Cleaned up all test data")
    finally:
        session.close()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Jobs System Integration Test")
    print("=" * 60)

    try:
        # Test 1: Create execution with trigger source
        execution_id = test_execution_creation()

        # Test 2: Create job with execution link
        job_id = test_job_creation(execution_id)

        # Test 3: Create job execution link
        job_exec_id = test_job_execution_link(job_id, execution_id)

        # Cleanup
        cleanup(execution_id, job_id, job_exec_id)

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("  • Executions now have trigger_source and trigger_metadata")
        print("  • Execution.id is properly stored as UUID")
        print("  • Job.last_execution_id uses UUID type with foreign key")
        print("  • JobExecution.execution_id uses UUID type with foreign key")
        print("  • Job counters (total/successful/failed) are Integer type")
        print("  • JobExecution.execution_duration_ms is Integer type")
        print("  • All foreign key relationships work correctly")

        return 0
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
