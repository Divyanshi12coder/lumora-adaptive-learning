"""initial schema: users, curriculum, learning analytics, RAG (pgvector), AI and ML audit tables

Revision ID: 0001
Revises: 
Create Date: 2026-10-03 09:59:07.576376

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.config import get_settings
from app.db.types import EmbeddingVector

EMBEDDING_DIM = get_settings().embedding_dim


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    is_pg = op.get_bind().dialect.name == "postgresql"
    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('subjects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('description', sa.String(length=300), nullable=False),
    sa.Column('icon', sa.String(length=30), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_subjects')),
    sa.UniqueConstraint('slug', name=op.f('uq_subjects_slug'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('display_name', sa.String(length=60), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('token_version', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('courses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('subject_id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('description', sa.String(length=400), nullable=False),
    sa.Column('level', sa.String(length=20), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], name=op.f('fk_courses_subject_id_subjects'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_courses')),
    sa.UniqueConstraint('slug', name=op.f('uq_courses_slug'))
    )
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_courses_subject_id'), ['subject_id'], unique=False)

    op.create_table('learning_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('explanation_length', sa.String(length=10), nullable=False),
    sa.Column('prefers_visuals', sa.Boolean(), nullable=False),
    sa.Column('prefers_examples', sa.Boolean(), nullable=False),
    sa.Column('pace', sa.String(length=10), nullable=False),
    sa.Column('read_aloud', sa.Boolean(), nullable=False),
    sa.Column('readable_font', sa.Boolean(), nullable=False),
    sa.Column('text_scale', sa.Float(), nullable=False),
    sa.Column('line_spacing', sa.Float(), nullable=False),
    sa.Column('reduced_motion', sa.Boolean(), nullable=False),
    sa.Column('focus_mode', sa.Boolean(), nullable=False),
    sa.Column('high_contrast', sa.Boolean(), nullable=False),
    sa.Column('length_bias', sa.Float(), nullable=False),
    sa.Column('difficulty_bias', sa.Float(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_preferences_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_preferences')),
    sa.UniqueConstraint('user_id', name=op.f('uq_learning_preferences_user_id'))
    )
    op.create_table('learning_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('event_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_sessions'))
    )
    with op.batch_alter_table('learning_sessions', schema=None) as batch_op:
        batch_op.create_index('ix_learning_sessions_user_started', ['user_id', 'started_at'], unique=False)

    op.create_table('model_predictions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('model_name', sa.String(length=60), nullable=False),
    sa.Column('model_version', sa.String(length=60), nullable=False),
    sa.Column('features', sa.JSON(), nullable=False),
    sa.Column('prediction', sa.Float(), nullable=False),
    sa.Column('label', sa.String(length=60), nullable=True),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('detail', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_model_predictions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_predictions'))
    )
    with op.batch_alter_table('model_predictions', schema=None) as batch_op:
        batch_op.create_index('ix_model_predictions_user_model', ['user_id', 'model_name'], unique=False)

    op.create_table('student_profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('avatar', sa.String(length=30), nullable=False),
    sa.Column('grade_band', sa.String(length=20), nullable=True),
    sa.Column('favorite_subject_id', sa.Integer(), nullable=True),
    sa.Column('learner_cluster', sa.String(length=40), nullable=True),
    sa.Column('weekly_goal_days', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['favorite_subject_id'], ['subjects.id'], name=op.f('fk_student_profiles_favorite_subject_id_subjects'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_student_profiles_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_student_profiles')),
    sa.UniqueConstraint('user_id', name=op.f('uq_student_profiles_user_id'))
    )
    op.create_table('topics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=80), nullable=False),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('summary', sa.String(length=400), nullable=False),
    sa.Column('icon', sa.String(length=30), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('prerequisite_topic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_topics_course_id_courses'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['prerequisite_topic_id'], ['topics.id'], name=op.f('fk_topics_prerequisite_topic_id_topics'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_topics')),
    sa.UniqueConstraint('slug', name=op.f('uq_topics_slug'))
    )
    with op.batch_alter_table('topics', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_topics_course_id'), ['course_id'], unique=False)

    op.create_table('adaptive_strategies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('context', sa.String(length=20), nullable=False),
    sa.Column('support_score', sa.Float(), nullable=False),
    sa.Column('strategy', sa.JSON(), nullable=False),
    sa.Column('signals', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_adaptive_strategies_topic_id_topics'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_adaptive_strategies_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_adaptive_strategies'))
    )
    with op.batch_alter_table('adaptive_strategies', schema=None) as batch_op:
        batch_op.create_index('ix_adaptive_strategies_user_created', ['user_id', 'created_at'], unique=False)

    op.create_table('ai_conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_ai_conversations_topic_id_topics'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ai_conversations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_conversations'))
    )
    with op.batch_alter_table('ai_conversations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ai_conversations_user_id'), ['user_id'], unique=False)

    op.create_table('documents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('content_type', sa.String(length=80), nullable=False),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('char_count', sa.Integer(), nullable=False),
    sa.Column('chunk_count', sa.Integer(), nullable=False),
    sa.Column('error', sa.String(length=500), nullable=True),
    sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_documents_owner_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_documents_topic_id_topics'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_documents'))
    )
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_documents_owner_id'), ['owner_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_documents_topic_id'), ['topic_id'], unique=False)

    op.create_table('learning_goals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('target_mastery', sa.Float(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_learning_goals_topic_id_topics'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_learning_goals_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_goals'))
    )
    with op.batch_alter_table('learning_goals', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_goals_user_id'), ['user_id'], unique=False)

    op.create_table('lessons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=160), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('estimated_minutes', sa.Integer(), nullable=False),
    sa.Column('content', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_lessons_topic_id_topics'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lessons'))
    )
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lessons_topic_id'), ['topic_id'], unique=False)

    op.create_table('mastery_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('p_mastery', sa.Float(), nullable=False),
    sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_mastery_history_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mastery_history_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mastery_history'))
    )
    with op.batch_alter_table('mastery_history', schema=None) as batch_op:
        batch_op.create_index('ix_mastery_history_user_recorded', ['user_id', 'recorded_at'], unique=False)

    op.create_table('mastery_scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('p_mastery', sa.Float(), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('correct', sa.Integer(), nullable=False),
    sa.Column('last_practiced_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_mastery_scores_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_mastery_scores_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_mastery_scores')),
    sa.UniqueConstraint('user_id', 'topic_id', name='uq_mastery_user_topic')
    )
    with op.batch_alter_table('mastery_scores', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_mastery_scores_user_id'), ['user_id'], unique=False)

    op.create_table('questions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=False),
    sa.Column('qtype', sa.String(length=20), nullable=False),
    sa.Column('options', sa.JSON(), nullable=False),
    sa.Column('correct_index', sa.Integer(), nullable=False),
    sa.Column('explanation', sa.Text(), nullable=False),
    sa.Column('hint', sa.Text(), nullable=False),
    sa.Column('difficulty', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('correct_index >= 0', name=op.f('ck_questions_correct_index_positive')),
    sa.CheckConstraint('difficulty BETWEEN 1 AND 3', name=op.f('ck_questions_difficulty_range')),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_questions_topic_id_topics'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_questions'))
    )
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_questions_topic_id'), ['topic_id'], unique=False)

    op.create_table('quiz_attempts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('difficulty', sa.String(length=10), nullable=False),
    sa.Column('strategy', sa.JSON(), nullable=False),
    sa.Column('question_ids', sa.JSON(), nullable=False),
    sa.Column('score', sa.Float(), nullable=True),
    sa.Column('correct_count', sa.Integer(), nullable=False),
    sa.Column('total', sa.Integer(), nullable=False),
    sa.Column('mastery_before', sa.Float(), nullable=True),
    sa.Column('mastery_after', sa.Float(), nullable=True),
    sa.Column('next_difficulty', sa.String(length=10), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_quiz_attempts_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_quiz_attempts_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quiz_attempts'))
    )
    with op.batch_alter_table('quiz_attempts', schema=None) as batch_op:
        batch_op.create_index('ix_quiz_attempts_user_topic', ['user_id', 'topic_id'], unique=False)

    op.create_table('ai_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=12), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('intent', sa.String(length=30), nullable=True),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('strategy', sa.JSON(), nullable=True),
    sa.Column('sources', sa.JSON(), nullable=False),
    sa.Column('provider', sa.String(length=30), nullable=True),
    sa.Column('is_demo', sa.Boolean(), nullable=False),
    sa.Column('safety_flags', sa.JSON(), nullable=False),
    sa.Column('feedback', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], name=op.f('fk_ai_messages_conversation_id_ai_conversations'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_messages'))
    )
    with op.batch_alter_table('ai_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ai_messages_conversation_id'), ['conversation_id'], unique=False)

    op.create_table('answers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('attempt_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('selected_index', sa.Integer(), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=False),
    sa.Column('skipped', sa.Boolean(), nullable=False),
    sa.Column('response_ms', sa.Integer(), nullable=False),
    sa.Column('hints_used', sa.Integer(), nullable=False),
    sa.Column('answer_changes', sa.Integer(), nullable=False),
    sa.Column('confidence', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('response_ms >= 0', name=op.f('ck_answers_response_ms_positive')),
    sa.ForeignKeyConstraint(['attempt_id'], ['quiz_attempts.id'], name=op.f('fk_answers_attempt_id_quiz_attempts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name=op.f('fk_answers_question_id_questions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_answers_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_answers')),
    sa.UniqueConstraint('attempt_id', 'question_id', name='uq_answer_attempt_question')
    )
    with op.batch_alter_table('answers', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_answers_attempt_id'), ['attempt_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_answers_user_id'), ['user_id'], unique=False)

    op.create_table('document_chunks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('word_count', sa.Integer(), nullable=False),
    sa.Column('embedding', EmbeddingVector(EMBEDDING_DIM), nullable=True),
    sa.Column('meta', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name=op.f('fk_document_chunks_document_id_documents'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_document_chunks')),
    sa.UniqueConstraint('document_id', 'chunk_index', name='uq_chunk_doc_index')
    )
    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.create_index('ix_document_chunks_document_id', ['document_id'], unique=False)

    op.create_table('interaction_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=True),
    sa.Column('event_type', sa.String(length=40), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.Column('lesson_id', sa.Integer(), nullable=True),
    sa.Column('question_id', sa.Integer(), nullable=True),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_interaction_events_lesson_id_lessons'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['question_id'], ['questions.id'], name=op.f('fk_interaction_events_question_id_questions'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], name=op.f('fk_interaction_events_session_id_learning_sessions'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_interaction_events_topic_id_topics'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_interaction_events_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_interaction_events'))
    )
    with op.batch_alter_table('interaction_events', schema=None) as batch_op:
        batch_op.create_index('ix_interaction_events_type', ['event_type'], unique=False)
        batch_op.create_index('ix_interaction_events_user_created', ['user_id', 'created_at'], unique=False)

    op.create_table('recommendations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('topic_id', sa.Integer(), nullable=False),
    sa.Column('lesson_id', sa.Integer(), nullable=True),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.Column('factors', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], name=op.f('fk_recommendations_lesson_id_lessons'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], name=op.f('fk_recommendations_topic_id_topics'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_recommendations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_recommendations'))
    )
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.create_index('ix_recommendations_user_status', ['user_id', 'status'], unique=False)

    if is_pg:
        # Approximate-nearest-neighbour index for cosine similarity search.
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
            "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    with op.batch_alter_table('recommendations', schema=None) as batch_op:
        batch_op.drop_index('ix_recommendations_user_status')

    op.drop_table('recommendations')
    with op.batch_alter_table('interaction_events', schema=None) as batch_op:
        batch_op.drop_index('ix_interaction_events_user_created')
        batch_op.drop_index('ix_interaction_events_type')

    op.drop_table('interaction_events')
    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.drop_index('ix_document_chunks_document_id')

    op.drop_table('document_chunks')
    with op.batch_alter_table('answers', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_answers_user_id'))
        batch_op.drop_index(batch_op.f('ix_answers_attempt_id'))

    op.drop_table('answers')
    with op.batch_alter_table('ai_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ai_messages_conversation_id'))

    op.drop_table('ai_messages')
    with op.batch_alter_table('quiz_attempts', schema=None) as batch_op:
        batch_op.drop_index('ix_quiz_attempts_user_topic')

    op.drop_table('quiz_attempts')
    with op.batch_alter_table('questions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_questions_topic_id'))

    op.drop_table('questions')
    with op.batch_alter_table('mastery_scores', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_mastery_scores_user_id'))

    op.drop_table('mastery_scores')
    with op.batch_alter_table('mastery_history', schema=None) as batch_op:
        batch_op.drop_index('ix_mastery_history_user_recorded')

    op.drop_table('mastery_history')
    with op.batch_alter_table('lessons', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_lessons_topic_id'))

    op.drop_table('lessons')
    with op.batch_alter_table('learning_goals', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_goals_user_id'))

    op.drop_table('learning_goals')
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_documents_topic_id'))
        batch_op.drop_index(batch_op.f('ix_documents_owner_id'))

    op.drop_table('documents')
    with op.batch_alter_table('ai_conversations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ai_conversations_user_id'))

    op.drop_table('ai_conversations')
    with op.batch_alter_table('adaptive_strategies', schema=None) as batch_op:
        batch_op.drop_index('ix_adaptive_strategies_user_created')

    op.drop_table('adaptive_strategies')
    with op.batch_alter_table('topics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_topics_course_id'))

    op.drop_table('topics')
    op.drop_table('student_profiles')
    with op.batch_alter_table('model_predictions', schema=None) as batch_op:
        batch_op.drop_index('ix_model_predictions_user_model')

    op.drop_table('model_predictions')
    with op.batch_alter_table('learning_sessions', schema=None) as batch_op:
        batch_op.drop_index('ix_learning_sessions_user_started')

    op.drop_table('learning_sessions')
    op.drop_table('learning_preferences')
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_courses_subject_id'))

    op.drop_table('courses')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    op.drop_table('subjects')
