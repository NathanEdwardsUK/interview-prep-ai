"""
Integration tests for study plan flow: suggest -> approve -> save to DB
"""
import pytest
from sqlalchemy.orm import Session

from app.models.plan import PlanTopic, TopicProgress
from app.models.user import User


def test_suggest_new_plan_with_stub(test_client):
    """Test that suggest_new_plan returns a valid PlanResponse using stub LLM"""
    response = test_client.post(
        "/api/v1/plan/suggest_new",
        json={
            "role": "Software Engineer",
            "raw_user_context": "I have 2 years of experience in Python and want to prepare for FAANG interviews."
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "plan_overview" in data
    assert "plan_topics" in data
    
    # Verify plan_overview structure
    overview = data["plan_overview"]
    assert "target_role" in overview
    assert "total_daily_minutes" in overview
    assert "time_horizon_weeks" in overview
    assert "rationale" in overview
    
    # Verify plan_topics structure
    assert isinstance(data["plan_topics"], list)
    assert len(data["plan_topics"]) > 0
    
    # Verify each topic has required fields
    for topic in data["plan_topics"]:
        assert "name" in topic
        assert "description" in topic
        assert "priority" in topic
        assert "daily_study_minutes" in topic
        assert "expected_outcome" in topic
        assert isinstance(topic["priority"], int)
        assert isinstance(topic["daily_study_minutes"], int)


def test_approve_plan_saves_to_db(test_client, db_session: Session, test_user: User):
    """Test that approve_plan saves PlanTopic records to the database"""
    # Create a plan response (matching stub output structure)
    plan_data = {
        "plan_overview": {
            "target_role": "Software Engineer",
            "total_daily_minutes": 120,
            "time_horizon_weeks": 8,
            "rationale": "Focused plan covering core algorithms, system design, and behavioral questions over 8 weeks."
        },
        "plan_topics": [
            {
                "name": "Data Structures",
                "description": "Arrays, linked lists, trees, graphs",
                "priority": 1,
                "daily_study_minutes": 30,
                "expected_outcome": "Master core data structures"
            },
            {
                "name": "Algorithms",
                "description": "Sorting, searching, dynamic programming",
                "priority": 2,
                "daily_study_minutes": 40,
                "expected_outcome": "Solve medium difficulty problems"
            }
        ]
    }
    
    # Call approve_plan endpoint
    response = test_client.post(
        "/api/v1/plan/approve_plan",
        json={"plan": plan_data}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert "topic_ids" in result
    assert len(result["topic_ids"]) == 2
    
    # Verify topics were saved to database
    topics = db_session.query(PlanTopic).filter(
        PlanTopic.user_id == test_user.clerk_user_id
    ).all()
    
    assert len(topics) == 2
    
    # Verify first topic
    topic1 = next(t for t in topics if t.name == "Data Structures")
    assert topic1.description == "Arrays, linked lists, trees, graphs"
    assert topic1.planned_daily_study_time == 30
    assert topic1.priority == 1
    assert topic1.user_id == test_user.clerk_user_id
    
    # Verify second topic
    topic2 = next(t for t in topics if t.name == "Algorithms")
    assert topic2.description == "Sorting, searching, dynamic programming"
    assert topic2.planned_daily_study_time == 40
    assert topic2.priority == 2
    assert topic2.user_id == test_user.clerk_user_id


def test_full_flow_suggest_and_approve(test_client, db_session: Session, test_user: User):
    """Test the complete flow: suggest plan -> approve plan -> verify saved"""
    # Step 1: Suggest a new plan (uses stub LLM)
    suggest_response = test_client.post(
        "/api/v1/plan/suggest_new",
        json={
            "role": "Software Engineer",
            "raw_user_context": "I want to prepare for technical interviews."
        }
    )
    
    assert suggest_response.status_code == 200
    plan_data = suggest_response.json()
    
    # Step 2: Approve the plan
    approve_response = test_client.post(
        "/api/v1/plan/approve_plan",
        json={"plan": plan_data}
    )
    
    assert approve_response.status_code == 200
    approve_result = approve_response.json()
    assert approve_result["status"] == "success"
    
    # Step 3: Verify plan was saved correctly
    topics = db_session.query(PlanTopic).filter(
        PlanTopic.user_id == test_user.clerk_user_id
    ).all()
    
    assert len(topics) > 0
    
    # Verify topics match the suggested plan
    saved_topic_names = {t.name for t in topics}
    suggested_topic_names = {t["name"] for t in plan_data["plan_topics"]}
    assert saved_topic_names == suggested_topic_names
    
    # Verify field mappings
    for suggested_topic in plan_data["plan_topics"]:
        saved_topic = next(t for t in topics if t.name == suggested_topic["name"])
        assert saved_topic.description == suggested_topic["description"]
        assert saved_topic.planned_daily_study_time == suggested_topic["daily_study_minutes"]
        assert saved_topic.priority == suggested_topic["priority"]


def test_plan_replacement(test_client, db_session: Session, test_user: User):
    """Test that approving a new plan replaces existing plan topics"""
    # Create and approve initial plan
    initial_plan = {
        "plan_overview": {
            "target_role": "Software Engineer",
            "total_daily_minutes": 60,
            "time_horizon_weeks": 4,
            "rationale": "Initial plan"
        },
        "plan_topics": [
            {
                "name": "Topic A",
                "description": "First topic",
                "priority": 1,
                "daily_study_minutes": 30,
                "expected_outcome": "Learn A"
            }
        ]
    }
    
    test_client.post(
        "/api/v1/plan/approve_plan",
        json={"plan": initial_plan}
    )
    
    # Verify initial topic exists
    topics_before = db_session.query(PlanTopic).filter(
        PlanTopic.user_id == test_user.clerk_user_id
    ).all()
    assert len(topics_before) == 1
    assert topics_before[0].name == "Topic A"
    
    # Approve new plan with different topics
    new_plan = {
        "plan_overview": {
            "target_role": "Software Engineer",
            "total_daily_minutes": 120,
            "time_horizon_weeks": 8,
            "rationale": "Updated plan"
        },
        "plan_topics": [
            {
                "name": "Topic B",
                "description": "Second topic",
                "priority": 1,
                "daily_study_minutes": 60,
                "expected_outcome": "Learn B"
            },
            {
                "name": "Topic C",
                "description": "Third topic",
                "priority": 2,
                "daily_study_minutes": 60,
                "expected_outcome": "Learn C"
            }
        ]
    }
    
    test_client.post(
        "/api/v1/plan/approve_plan",
        json={"plan": new_plan}
    )
    
    # Verify old topic is deleted and new topics are created
    topics_after = db_session.query(PlanTopic).filter(
        PlanTopic.user_id == test_user.clerk_user_id
    ).all()
    
    assert len(topics_after) == 2
    topic_names = {t.name for t in topics_after}
    assert "Topic A" not in topic_names
    assert "Topic B" in topic_names
    assert "Topic C" in topic_names


def test_view_plan_no_topics_returns_404(test_client):
    """GET /plan/view should return 404 when user has no saved topics."""
    response = test_client.get("/api/v1/plan/view")
    assert response.status_code == 404


def test_view_plan_returns_saved_topics(test_client, db_session: Session, test_user: User):
    """GET /plan/view should return PlanResponse built from PlanTopic records."""
    # Create topics in DB
    t1 = PlanTopic(
        user_id=test_user.clerk_user_id,
        name="Algorithms",
        description="Algo practice",
        planned_daily_study_time=40,
        priority=1,
        expected_outcome="Solve medium questions",
    )
    t2 = PlanTopic(
        user_id=test_user.clerk_user_id,
        name="System Design",
        description="Design large systems",
        planned_daily_study_time=20,
        priority=2,
        expected_outcome="Explain tradeoffs",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    response = test_client.get("/api/v1/plan/view")
    assert response.status_code == 200
    data = response.json()

    assert data["plan_overview"]["total_daily_minutes"] == 60
    names = [t["name"] for t in data["plan_topics"]]
    assert set(names) == {"Algorithms", "System Design"}
    # Ensure topic_id is present and matches DB ids
    returned_ids = {t["topic_id"] for t in data["plan_topics"]}
    assert returned_ids == {t1.id, t2.id}


def test_end_session_updates_topic_progress(test_client, db_session: Session, test_user: User):
    """Ending a session should update TopicProgress for the session's topic."""
    # Create a topic and session
    topic = PlanTopic(
        user_id=test_user.clerk_user_id,
        name="Data Structures",
        description="Lists and trees",
        planned_daily_study_time=30,
        priority=1,
        expected_outcome="Be comfortable with DS",
    )
    db_session.add(topic)
    db_session.commit()
    db_session.refresh(topic)

    # Start a session via API to ensure wiring works
    start_resp = test_client.post(
        "/api/v1/study/start_session",
        params={"topic_id": topic.id, "planned_study_time": 30},
    )
    assert start_resp.status_code == 200
    session_id = start_resp.json()["id"]

    # End the session
    end_resp = test_client.put(f"/api/v1/study/end_session/{session_id}")
    assert end_resp.status_code == 200

    # Verify TopicProgress was created/updated
    progress = db_session.query(TopicProgress).filter(
        TopicProgress.user_id == test_user.clerk_user_id,
        TopicProgress.topic_id == topic.id,
    ).first()
    assert progress is not None
    assert progress.total_time_spent == 30
