from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field




class MemoryType(str, Enum):
    USER = "user"
    USER_PROFILE = "user_profile"
    AGENT = "agent"
    TEAM = "team"
    WORKSPACE = "workspace"


@dataclass
class UserMemory:
    """Model for User Memories"""

    memory: str
    memory_id: Optional[str] = None
    memory_type: Optional[MemoryType] = field(default=MemoryType.USER)
    topics: Optional[List[str]] = None
    facts: Optional[List[str]] = None
    user_id: Optional[str] = None
    input: Optional[str] = None
    updated_at: Optional[datetime] = None
    feedback: Optional[str] = None

    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    workspace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        _dict = {
            "memory_id": self.memory_id,
            "memory": self.memory,
            "topics": self.topics,
            "facts": self.facts,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "input": self.input,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "team_id": self.team_id,
            "feedback": self.feedback,
            "workspace_id": self.workspace_id,
            "memory_type": self.memory_type,
            "metadata": self.metadata or {},
        }
        return {k: v for k, v in _dict.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserMemory":
        data = dict(data)

        # Convert updated_at to datetime
        if updated_at := data.get("updated_at"):

            if isinstance(updated_at, (int, float)):
                try:
                    data["updated_at"] = datetime.fromtimestamp(updated_at, tz=timezone.utc)
                except (ValueError):
                    data["updated_at"] = datetime.fromtimestamp(updated_at/1000, tz=timezone.utc)
            else:
                data["updated_at"] = datetime.fromisoformat(updated_at)

        return cls(**data)


class WorkExperience(BaseModel):
    """Work experience entry for user profile"""
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class EducationEntry(BaseModel):
    """Education entry for user profile"""
    name: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class CoreIdentity(BaseModel):
    """Core identity information for user profile"""
    name: Optional[str] = None
    age: Optional[int] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    nationality: Optional[str] = None
    pronouns: Optional[str] = None


class ProfessionalLife(BaseModel):
    """Professional life information for user profile"""
    current_job: Optional[str] = None
    work_history: Optional[List[WorkExperience]] = Field(default_factory=list)
    industry: Optional[str] = None
    skills: Optional[List[str]] = Field(default_factory=list)
    career_goals: Optional[str] = None
    salary_range: Optional[str] = None
    work_style: Optional[str] = None


class EducationalBackground(BaseModel):
    """Educational background for user profile"""
    highest_education: Optional[str] = None
    institutions: Optional[List[EducationEntry]] = Field(default_factory=list)
    certifications: Optional[List[str]] = Field(default_factory=list)
    learning_interests: Optional[List[str]] = Field(default_factory=list)
    languages: Optional[List[str]] = Field(default_factory=list)


class PersonalLife(BaseModel):
    """Personal life information for user profile"""
    relationship_status: Optional[str] = None
    family: Optional[str] = None
    living_situation: Optional[str] = None
    pets: Optional[List[str]] = Field(default_factory=list)
    hobbies: Optional[List[str]] = Field(default_factory=list)
    interests: Optional[List[str]] = Field(default_factory=list)
    values: Optional[List[str]] = Field(default_factory=list)


class RelationshipBase(BaseModel):
    """Base relationship details"""
    name: Optional[str] = None
    duration: Optional[int] = None  # Duration in months
    context: Optional[str] = None   


class CurrentRomantic(RelationshipBase):
    """Current romantic relationship details"""
    pass


class Ex(RelationshipBase):
    """Ex-partner details"""
    ended_reason: Optional[str] = None


class TalkingStage(RelationshipBase):
    """Talking stage relationship details"""
    pass


class Situationship(RelationshipBase):
    """Situationship details"""
    pass


class Crush(RelationshipBase):
    """Crush details"""
    pass        


class RomanticHistory(BaseModel):
    """Romantic history sub-object for relationships"""
    exes: Optional[List[Ex]] = Field(default_factory=list)
    talking_stages: Optional[List[TalkingStage]] = Field(default_factory=list)
    situationships: Optional[List[Situationship]] = Field(default_factory=list)
    crushes: Optional[List[Crush]] = Field(default_factory=list)


class Relationships(BaseModel):
    """Relationship information for user profile"""
    current_romantic: Optional[CurrentRomantic] = None
    romantic_history: Optional[RomanticHistory] = Field(default_factory=RomanticHistory)
    relationship_patterns: Optional[str] = None
    relationship_goals: Optional[str] = None
    dating_preferences: Optional[List[str]] = Field(default_factory=list)


class RecentContext(BaseModel):
    """Recent context and current situation for user profile"""
    current_events: Optional[List[str]] = Field(default_factory=list)
    recent_activities: Optional[List[str]] = Field(default_factory=list)
    current_challenges: Optional[List[str]] = Field(default_factory=list)
    current_goals: Optional[List[str]] = Field(default_factory=list)
    upcoming_events: Optional[List[str]] = Field(default_factory=list)
    recent_travels: Optional[List[str]] = Field(default_factory=list)


class HealthWellness(BaseModel):
    """Health and wellness information for user profile"""
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    fitness_routine: Optional[str] = None
    health_conditions: Optional[List[str]] = Field(default_factory=list)
    mental_health: Optional[str] = None
    wellness_goals: Optional[List[str]] = Field(default_factory=list)


class PreferencesLikes(BaseModel):
    """User preferences and likes for user profile"""
    food_preferences: Optional[List[str]] = Field(default_factory=list)
    entertainment_preferences: Optional[List[str]] = Field(default_factory=list)
    music_preferences: Optional[List[str]] = Field(default_factory=list)
    movie_preferences: Optional[List[str]] = Field(default_factory=list)
    book_preferences: Optional[List[str]] = Field(default_factory=list)
    travel_preferences: Optional[List[str]] = Field(default_factory=list)
    shopping_preferences: Optional[List[str]] = Field(default_factory=list)
    brand_preferences: Optional[List[str]] = Field(default_factory=list)
    dislikes: Optional[List[str]] = Field(default_factory=list)


class UserMemoryProfile(BaseModel):
    """Comprehensive user profile schema for memory storage"""
    
    # Core sections
    core_identity: Optional[CoreIdentity] = Field(default_factory=CoreIdentity)
    professional_life: Optional[ProfessionalLife] = Field(default_factory=ProfessionalLife)
    educational_background: Optional[EducationalBackground] = Field(default_factory=EducationalBackground)
    personal_life: Optional[PersonalLife] = Field(default_factory=PersonalLife)
    relationships: Optional[Relationships] = Field(default_factory=Relationships)
    recent_context: Optional[RecentContext] = Field(default_factory=RecentContext)
    health_wellness: Optional[HealthWellness] = Field(default_factory=HealthWellness)
    preferences_likes: Optional[PreferencesLikes] = Field(default_factory=PreferencesLikes)
    
    # # Metadata
    # profile_id: Optional[str] = None
    # user_id: Optional[str] = None
    # workspace_id: Optional[str] = None
    # created_at: Optional[datetime] = None
    # updated_at: Optional[datetime] = None
    # version: Optional[str] = "1.0"
    # confidence_score: Optional[float] = None  # AI confidence in the profile data
    # last_memory_update: Optional[str] = None  # ID of the last memory that updated this profile
    
    # Additional custom fields
    # custom_fields: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary representation"""
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserMemoryProfile":
        """Create a UserMemoryProfile from a dictionary"""
        return cls.model_validate(data)

    
    def format(self) -> str:
        """Format the user profile into a readable summary"""
        return self._format_user_profile()
    
    def _format_user_profile(self) -> str:
        """
        Format a user profile dictionary into a clean, readable summary.
        
        Args:
            profile: User profile dictionary with structured data
            
        Returns:
            Formatted string representation of the user profile
        """
        
        fmt_parts = []
        
        # Core Identity Section
        if self.core_identity:
            fmt_parts.append("=== CORE IDENTITY ===")
            if self.core_identity.name:
                fmt_parts.append(f"Name: {self.core_identity.name}")
            if self.core_identity.age:
                fmt_parts.append(f"Age: {self.core_identity.age}")
            if self.core_identity.birth_date:
                fmt_parts.append(f"Birth Date: {self.core_identity.birth_date}")
            if self.core_identity.gender:
                fmt_parts.append(f"Gender: {self.core_identity.gender}")
            if self.core_identity.location:
                fmt_parts.append(f"Location: {self.core_identity.location}")
            fmt_parts.append("")
        
        # Professional Life Section
        if self.professional_life:
            fmt_parts.append("=== PROFESSIONAL LIFE ===")
            if self.professional_life.current_job:
                fmt_parts.append(f"Current Job: {self.professional_life.current_job}")
            if self.professional_life.industry:
                fmt_parts.append(f"Industry: {self.professional_life.industry}")
            if self.professional_life.skills:
                skills = self.professional_life.skills
                if isinstance(skills, list):
                    fmt_parts.append(f"Skills: {', '.join(skills)}")
                else:
                    fmt_parts.append(f"Skills: {skills}")
            if self.professional_life.career_goals:
                fmt_parts.append(f"Career Goals: {self.professional_life.career_goals}")
            
            # Work History
            if self.professional_life.work_history:
                fmt_parts.append("Work History:")
                for job in self.professional_life.work_history:
                    job_line = f"  • {job.position if job.position else 'Unknown Position'}"
                    if job.company:
                        job_line += f" at {job.company}"
                    if job.start_date and job.end_date:
                        job_line += f" ({job.start_date} - {job.end_date})"
                    elif job.start_date:
                        job_line += f" (since {job.start_date})"
                    fmt_parts.append(job_line)
            fmt_parts.append("")
        
        # Educational Background Section
        if self.educational_background:
            fmt_parts.append("=== EDUCATION ===")
            if self.educational_background.highest_education:
                fmt_parts.append(f"Highest Education: {self.educational_background.highest_education}")
            
            if self.educational_background.institutions:
                fmt_parts.append("Institutions:")
                for inst in self.educational_background.institutions:
                    inst_line = f"  • {inst.name if inst.name else 'Unknown Institution'}"
                    if inst.degree and inst.field:
                        inst_line += f" - {inst.degree} in {inst.field}"
                    elif inst.degree:
                        inst_line += f" - {inst.degree}"
                    if inst.start_date and inst.end_date:
                        inst_line += f" ({inst.start_date} - {inst.end_date})"
                    fmt_parts.append(inst_line)
            
            if self.educational_background.certifications:
                certs = self.educational_background.certifications
                if isinstance(certs, list):
                    fmt_parts.append(f"Certifications: {', '.join(certs)}")
                else:
                    fmt_parts.append(f"Certifications: {certs}")
            
            if self.educational_background.learning_interests:
                interests = self.educational_background.learning_interests
                if isinstance(interests, list):
                    fmt_parts.append(f"Learning Interests: {', '.join(interests)}")
                else:
                    fmt_parts.append(f"Learning Interests: {interests}")
            fmt_parts.append("")
        
        # Personal Life Section
        if self.personal_life:
            fmt_parts.append("=== PERSONAL LIFE ===")
            if self.personal_life.relationship_status:
                fmt_parts.append(f"Relationship Status: {self.personal_life.relationship_status}")
            if self.personal_life.family:
                fmt_parts.append(f"Family: {self.personal_life.family}")
            if self.personal_life.living_situation:
                fmt_parts.append(f"Living Situation: {self.personal_life.living_situation}")
            fmt_parts.append("")
        
        # Relationships Section
        if self.relationships:
            fmt_parts.append("=== RELATIONSHIPS ===")
            
            # Current Romantic
            if self.relationships.current_romantic:
                current = self.relationships.current_romantic
                current_line = f"Current Romantic: {current.name or 'Unknown'}"
                if current.duration:
                    current_line += f" ({current.duration} months)"
                if current.context:
                    current_line += f" - {current.context}"
                fmt_parts.append(current_line)
            
            if self.relationships.relationship_goals:
                fmt_parts.append(f"Relationship Goals: {self.relationships.relationship_goals}")
            if self.relationships.relationship_patterns:
                fmt_parts.append(f"Relationship Patterns: {self.relationships.relationship_patterns}")
            
            # Romantic History
            if self.relationships.romantic_history:
                history = self.relationships.romantic_history
                
                # Exes
                if history.exes:
                    fmt_parts.append("Exes:")
                    for ex in history.exes:
                        ex_line = f"  • {ex.name or 'Unknown'}"
                        if ex.duration:
                            ex_line += f" ({ex.duration} months)"
                        if ex.context:
                            ex_line += f" - {ex.context}"
                        if ex.ended_reason:
                            ex_line += f" | Ended: {ex.ended_reason}"
                        fmt_parts.append(ex_line)
                
                # Talking Stages
                if history.talking_stages:
                    fmt_parts.append("Talking Stages:")
                    for stage in history.talking_stages:
                        stage_line = f"  • {stage.name or 'Unknown'}"
                        if stage.duration:
                            stage_line += f" ({stage.duration} months)"
                        if stage.context:
                            stage_line += f" - {stage.context}"
                        fmt_parts.append(stage_line)
                
                # Situationships
                if history.situationships:
                    fmt_parts.append("Situationships:")
                    for situation in history.situationships:
                        situation_line = f"  • {situation.name or 'Unknown'}"
                        if situation.duration:
                            situation_line += f" ({situation.duration} months)"
                        if situation.context:
                            situation_line += f" - {situation.context}"
                        fmt_parts.append(situation_line)
                
                # Crushes
                if history.crushes:
                    fmt_parts.append("Crushes:")
                    for crush in history.crushes:
                        crush_line = f"  • {crush.name or 'Unknown'}"
                        if crush.context:
                            crush_line += f" - {crush.context}"
                        fmt_parts.append(crush_line)
            
            fmt_parts.append("")
        
        # Recent Context Section
        if self.recent_context:
            fmt_parts.append("=== RECENT CONTEXT ===")
            if self.recent_context.current_events:
                events = self.recent_context.current_events
                if isinstance(events, list):
                    fmt_parts.append(f"Current Events: {', '.join(events)}")
                else:
                    fmt_parts.append(f"Current Events: {events}")
            if self.recent_context.recent_activities:
                activities = self.recent_context.recent_activities
                if isinstance(activities, list):
                    fmt_parts.append(f"Recent Activities: {', '.join(activities)}")
                else:
                    fmt_parts.append(f"Recent Activities: {activities}")
            if self.recent_context.current_challenges:
                challenges = self.recent_context.current_challenges
                if isinstance(challenges, list):
                    fmt_parts.append(f"Current Challenges: {', '.join(challenges)}")
                else:
                    fmt_parts.append(f"Current Challenges: {challenges}")
            if self.recent_context.current_goals:
                goals = self.recent_context.current_goals
                if isinstance(goals, list):
                    fmt_parts.append(f"Current Goals: {', '.join(goals)}")
                else:
                    fmt_parts.append(f"Current Goals: {goals}")
            fmt_parts.append("")
        
        # Add any additional fields that might exist
        # excluded_keys = {
        #     'core_identity', 'professional_life', 'educational_background', 
        #     'personal_life', 'relationships', 'recent_context'
        # }
        # additional_fields = {k: v for k, v in data.items() if k not in excluded_keys and v}
        
        # if additional_fields:
        #     fmt_parts.append("=== ADDITIONAL INFORMATION ===")
        #     for key, value in additional_fields.items():
        #         fmt_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        #     fmt_parts.append("")
        
        # Join all parts and clean up
        result = "\n".join(fmt_parts).strip()
        
        # If no content was formatted, provide a default message
        if not result or result == "":
            return "User profile exists but contains no formatted data"
        
        return result

