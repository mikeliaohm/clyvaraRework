# Removed Models — March 2026

These SQLAlchemy models (and their database tables) were removed from
`backend/database.py` because they had **no backend router and no frontend
API call** — they were never wired up end-to-end.

The removal migration is `d1e2f3a4b5c6_consolidate_to_public_schema`.

## Schema consolidation

All remaining active tables were moved from `main`, `user_data`, and
`dashboard` schemas into the default `public` schema.  The `main`,
`user_data`, and `dashboard` schemas were dropped.

## Removed models

| Model class | Table name | Former schema | Purpose (planned) |
|---|---|---|---|
| Session | sessions | public | Express session store |
| DashboardLayout | dashboard_layouts | dashboard | Custom dashboard layouts |
| Widget | widgets | dashboard | Dashboard widget registry |
| UserWidget | user_widgets | dashboard | Per-user widget placement |
| UserPreference | user_preferences | dashboard | Theme/timezone prefs |
| AnalyticsData | analytics_data | dashboard | Dashboard metrics |
| Waitlist | waitlist | public | Pre-launch waitlist |
| Course | courses | main | LMS course sync |
| CourseItem | course_items | public | LMS assignments/quizzes |
| PlanCourse | plan_courses | public | Study plan ↔ course link |
| Topic | topics | main | Granular topic tracking |
| LearningModule | learning_modules | main | Interactive learning modules |
| Test | tests | main | Adaptive/mastery tests |
| TestResult | test_results | public | Test attempt results |
| StudyActivity | study_activity | public | Per-session study logs |
| WeeklyInsight | weekly_insights | public | Weekly analytics rollups |
| BoardExamTopic | board_exam_topics | public | Board exam topic bank |
| ContentGeneration | content_generation | public | AI content generation jobs |
| AnesthesiaCarePlan | anesthesia_care_plans | public | Legacy care plan format |
| BiometricData | biometric_data | public | Wearable biometric data |
| LearningPreference | learning_preferences | public | VARK style prefs |
| StudyPlan | study_plans | public | Agent-generated study plans |
| ProactiveQuiz | proactive_quizzes | public | Agent-generated quizzes |
| VarkContent | vark_content | public | VARK-adapted content |
| BehavioralAnalysis | behavioral_analysis | public | Engagement analysis |
| AgentNotification | agent_notifications | public | Agent push notifications |
| Flashcard | flashcards | main | Spaced-repetition flashcards |
| LibraryContent | library_content | public | Case studies/audio/guides |
| VisualGuide | visual_guides | public | Interactive visual guides |
| BiometricDevice | biometric_devices | public | Wearable device connections |
| OAuthState | oauth_states | public | LMS OAuth CSRF state |
| OAuthToken | oauth_tokens | public | LMS OAuth tokens |
| AcademicStudyPlan | academic_study_plans | public | Syllabus-based study plans |
| PasswordReset | password_resets | public | Password reset tokens |
| ContactMessage | contact_messages | public | Contact form submissions |
| Artifact | artifacts | public | Multi-agent learning artifacts |
| NotificationQueue | notification_queue | public | Scheduled notifications |
| AgentExecutionLog | agent_execution_logs | public | Agent run logs |
| RagRetrievalLog | rag_retrieval_logs | public | RAG query logs |
| FederationUpdate | federation_updates | public | Federated learning updates |
| MasteryScore | mastery_scores | public | Concept mastery tracking |
| ModalityPreference | modality_preferences | public | Content modality prefs |
| AgentState | agent_states | public | Multi-agent state store |

## Restoring a removed model

If you need any of these again, copy the class definition from git history
(commit before this change) back into `database.py` and create a new Alembic
migration.
