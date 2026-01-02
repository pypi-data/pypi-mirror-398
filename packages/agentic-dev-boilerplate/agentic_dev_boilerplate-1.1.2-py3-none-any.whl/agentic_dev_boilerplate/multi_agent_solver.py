#!/usr/bin/env python3
"""
Multi-Agent Problem Solver

Coordinates multiple specialized agents to collaboratively solve complex problems
through orchestrated teamwork, cross-validation, and consensus building.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .tmp_manager import TmpManager, get_tmp_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentRole(Enum):
    PLANNER = "planner"
    TESTER = "tester"
    DEBUGGER = "debugger"
    DEPLOYER = "deployer"
    SYSTEMS_ENGINEER = "systems_engineer"
    DEVOPS_SPECIALIST = "devops_specialist"
    ORCHESTRATOR = "orchestrator"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    VALIDATION_REQUEST = "validation_request"
    CONSENSUS_BUILDING = "consensus_building"
    ESCALATION = "escalation"
    SOLUTION_PROPOSAL = "solution_proposal"

@dataclass
class AgentMessage:
    """Message structure for inter-agent communication."""
    sender: AgentRole
    recipient: AgentRole
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: f"msg_{int(time.time() * 1000)}")

@dataclass
class Task:
    """Represents a task in the multi-agent workflow."""
    task_id: str
    description: str
    assigned_agent: AgentRole
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

@dataclass
class MultiAgentSession:
    """Manages a multi-agent problem-solving session."""
    session_id: str
    problem_description: str
    participating_agents: List[AgentRole]
    tasks: List[Task] = field(default_factory=list)
    messages: List[AgentMessage] = field(default_factory=list)
    consensus_threshold: float = 0.8  # Percentage of agents needed for consensus
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

class AgentCoordinator:
    """Coordinates communication and task assignment between agents."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.active_sessions: Dict[str, MultiAgentSession] = {}
        self.agent_capabilities = self._load_agent_capabilities()
        self.tmp_manager = get_tmp_manager("agentic-dev-boilerplate")

    def _load_agent_capabilities(self) -> Dict[AgentRole, List[str]]:
        """Load agent capabilities from instruction files."""
        capabilities = {}
        instructions_dir = self.workspace_root / ".github" / "instructions"

        if instructions_dir.exists():
            for instruction_file in instructions_dir.glob("*.instructions.md"):
                agent_name = instruction_file.stem
                try:
                    role = AgentRole(agent_name)
                    # Parse capabilities from instruction file
                    with open(instruction_file, 'r') as f:
                        content = f.read()
                        # Extract responsibilities from the file
                        capabilities[role] = self._extract_capabilities(content)
                except ValueError:
                    continue

        return capabilities

    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract agent capabilities from instruction content."""
        capabilities = []
        lines = content.split('\n')
        in_responsibilities = False

        for line in lines:
            if "**Core Responsibilities**:" in line:
                in_responsibilities = True
                continue
            elif in_responsibilities and line.strip().startswith("- "):
                capabilities.append(line.strip()[2:])
            elif in_responsibilities and line.strip() and not line.startswith(" "):
                break

        return capabilities

    def create_session(self, problem_description: str, required_agents: List[AgentRole]) -> str:
        """Create a new multi-agent problem-solving session."""
        session_id = f"session_{int(time.time() * 1000)}"
        session = MultiAgentSession(
            session_id=session_id,
            problem_description=problem_description,
            participating_agents=required_agents
        )
        self.active_sessions[session_id] = session
        logger.info(f"Created multi-agent session {session_id} with agents: {[a.value for a in required_agents]}")
        return session_id

    def decompose_problem(self, session_id: str) -> List[Task]:
        """Decompose a complex problem into agent-specific tasks."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Use planner agent to decompose the problem
        tasks = self._call_planner_agent(session.problem_description, session.participating_agents)

        # Create task objects
        task_objects = []
        for i, task_desc in enumerate(tasks):
            # Assign task to most appropriate agent
            assigned_agent = self._assign_task_to_agent(task_desc, session.participating_agents)
            task = Task(
                task_id=f"{session_id}_task_{i}",
                description=task_desc,
                assigned_agent=assigned_agent
            )
            task_objects.append(task)

        session.tasks = task_objects
        return task_objects

    def _call_planner_agent(self, problem: str, agents: List[AgentRole]) -> List[str]:
        """Call the planner agent to decompose the problem."""
        # This would invoke the actual planner agent
        # For now, return a simple decomposition
        return [
            f"Analyze {problem} from {agents[0].value} perspective",
            f"Validate solution components",
            f"Integrate and test final solution"
        ]

    def _assign_task_to_agent(self, task_desc: str, available_agents: List[AgentRole]) -> AgentRole:
        """Assign a task to the most appropriate agent."""
        # Simple assignment logic - in practice, this would be more sophisticated
        task_lower = task_desc.lower()

        if "plan" in task_lower or "decompose" in task_lower:
            return AgentRole.PLANNER
        elif "test" in task_lower or "validate" in task_lower:
            return AgentRole.TESTER
        elif "debug" in task_lower or "fix" in task_lower:
            return AgentRole.DEBUGGER
        elif "deploy" in task_lower or "production" in task_lower:
            return AgentRole.DEPLOYER
        else:
            return available_agents[0]  # Default to first agent

    def execute_session(self, session_id: str) -> Dict[str, Any]:
        """Execute a multi-agent problem-solving session."""
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        logger.info(f"Starting execution of session {session_id}")

        # Execute tasks (in practice, this would coordinate actual agent execution)
        results = {}
        for task in session.tasks:
            logger.info(f"Executing task {task.task_id} with agent {task.assigned_agent.value}")
            task.status = TaskStatus.IN_PROGRESS

            # Simulate agent execution
            result = self._execute_agent_task(task)
            task.results = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()

            results[task.task_id] = result

        # Build consensus
        consensus = self._build_consensus(session, results)
        session.completed_at = time.time()

        return {
            "session_id": session_id,
            "results": results,
            "consensus": consensus,
            "completed_at": session.completed_at
        }

    def _execute_agent_task(self, task: Task) -> Dict[str, Any]:
        """Execute a task with the assigned agent."""
        # In practice, this would invoke the actual agent
        # For now, simulate agent execution
        time.sleep(0.1)  # Simulate processing time

        return {
            "agent": task.assigned_agent.value,
            "task": task.description,
            "result": f"Completed {task.description}",
            "confidence": 0.9,
            "timestamp": time.time()
        }

    def _build_consensus(self, session: MultiAgentSession, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build consensus from agent results."""
        # Simple consensus building - in practice, this would be more sophisticated
        total_confidence = sum(result.get("confidence", 0) for result in results.values())
        avg_confidence = total_confidence / len(results) if results else 0

        consensus_reached = avg_confidence >= session.consensus_threshold

        return {
            "consensus_reached": consensus_reached,
            "average_confidence": avg_confidence,
            "participant_count": len(session.participating_agents),
            "recommendation": "Proceed with solution" if consensus_reached else "Require additional review"
        }

    def send_message(self, message: AgentMessage) -> None:
        """Send a message between agents."""
        session = self._find_session_for_agents(message.sender, message.recipient)
        if session:
            session.messages.append(message)
            logger.info(f"Message {message.message_id} sent from {message.sender.value} to {message.recipient.value}")

    def _find_session_for_agents(self, agent1: AgentRole, agent2: AgentRole) -> Optional[MultiAgentSession]:
        """Find a session that includes both agents."""
        for session in self.active_sessions.values():
            if agent1 in session.participating_agents and agent2 in session.participating_agents:
                return session
        return None

def main():
    """Main entry point for the multi-agent solver."""
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Agent Problem Solver")
    parser.add_argument("--workspace", "-w", type=Path, default=Path.cwd(),
                       help="Workspace root directory")
    parser.add_argument("--problem", "-p", required=True,
                       help="Problem description")
    parser.add_argument("--agents", "-a", nargs="+",
                       choices=[role.value for role in AgentRole],
                       default=[role.value for role in AgentRole],
                       help="Participating agents")
    parser.add_argument("--consensus-threshold", "-t", type=float, default=0.8,
                       help="Consensus threshold (0.0-1.0)")

    args = parser.parse_args()

    # Convert agent strings to AgentRole enums
    agents = [AgentRole(agent) for agent in args.agents]

    # Create coordinator
    coordinator = AgentCoordinator(args.workspace)

    # Create and execute session
    session_id = coordinator.create_session(args.problem, agents)
    tasks = coordinator.decompose_problem(session_id)

    print(f"Created session {session_id} with {len(tasks)} tasks:")
    for task in tasks:
        print(f"  - {task.description} (assigned to {task.assigned_agent.value})")

    # Execute the session
    result = coordinator.execute_session(session_id)

    print(f"\nSession completed. Consensus reached: {result['consensus']['consensus_reached']}")
    print(f"Average confidence: {result['consensus']['average_confidence']:.2f}")

if __name__ == "__main__":
    main()