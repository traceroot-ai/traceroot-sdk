import json
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

import traceroot
from traceroot.tracer import TraceOptions, trace

logger = traceroot.get_logger()


class DoctorRecommendation(BaseModel):
    """Model for doctor recommendations based on patient needs"""
    doctor_id: str = Field(
        description="Unique identifier for the recommended doctor")
    name: str = Field(description="Doctor's full name")
    specialty: str = Field(description="Doctor's primary specialty")
    sub_specialty: str = Field(description="Doctor's sub-specialty if any")
    next_available: str = Field(description="Next available appointment time")
    languages: List[str] = Field(description="Languages spoken by the doctor")
    reason: str = Field(description="Reason for recommending this doctor")


class SchedulingAgent:
    """Agent for recommending doctors and handling appointment scheduling"""

    def __init__(
        self,
        doctors_file: str = "examples/healthcare_voice_agent/data/doctors.json"
    ):
        self.doctors_file = doctors_file
        self.doctors_data = self._load_doctors_data()
        logger.info(f"Scheduling Agent initialized with "
                    f"{len(self.doctors_data['doctors'])} doctors")

    def _load_doctors_data(self) -> Dict:
        """Load doctors data from JSON file"""
        try:
            with open(self.doctors_file) as f:
                data = json.load(f)
                logger.info(
                    f"Loaded doctors database from: {self.doctors_file}")
                return data
        except FileNotFoundError:
            logger.error(f"Doctors database not found at {self.doctors_file}")
            raise Exception(
                f"Doctors database not found at {self.doctors_file}")

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def find_available_doctors(
            self,
            specialty: Optional[str] = None,
            symptoms: List[str] = None,
            preferred_language: Optional[str] = None,
            preferred_days: List[str] = None) -> List[DoctorRecommendation]:
        """
        Find available doctors based on patient preferences and symptoms

        Args:
            specialty: Preferred medical specialty
            symptoms: List of patient symptoms
            preferred_language: Preferred consultation language
            preferred_days: List of preferred appointment days

        Returns:
            List of recommended doctors with availability
        """
        logger.info(
            f"Finding doctors - Specialty: {specialty}, Symptoms: {symptoms}")
        logger.info(f"Preferred language: {preferred_language}, "
                    f"Preferred days: {preferred_days}")

        recommendations = []

        for doctor in self.doctors_data["doctors"]:
            if not doctor["accepting_new_patients"]:
                continue

            # Check specialty match if specified
            if specialty and specialty.lower(
            ) not in doctor["specialty"].lower():
                continue

            # Check language preference if specified
            if preferred_language and preferred_language not in doctor[
                    "languages"]:
                continue

            # Check day availability if specified
            if preferred_days:
                has_preferred_day = False
                for day in preferred_days:
                    if day.lower() in doctor["availability"]:
                        has_preferred_day = True
                        break
                if not has_preferred_day:
                    continue

            # Create recommendation with matching reason
            reason = self._generate_recommendation_reason(
                doctor, specialty, symptoms, preferred_language)

            recommendations.append(
                DoctorRecommendation(doctor_id=doctor["id"],
                                     name=doctor["name"],
                                     specialty=doctor["specialty"],
                                     sub_specialty=doctor["sub_specialty"],
                                     next_available=doctor["next_available"],
                                     languages=doctor["languages"],
                                     reason=reason))

        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: datetime.strptime(x.next_available, "%Y-%m-%d %H:%M"
                                            ))
        logger.info(f"Found {len(sorted_recommendations)} matching doctors")

        return sorted_recommendations

    def _generate_recommendation_reason(
            self, doctor: Dict, specialty: Optional[str],
            symptoms: Optional[List[str]],
            preferred_language: Optional[str]) -> str:
        """Generate a personalized reason for recommending a doctor"""
        reasons = []

        if specialty and specialty.lower() in doctor["specialty"].lower():
            reasons.append(f"Specializes in {doctor['specialty']}")

        if doctor["sub_specialty"]:
            reasons.append(f"Expert in {doctor['sub_specialty']}")

        if preferred_language and preferred_language in doctor["languages"]:
            reasons.append(f"Speaks {preferred_language}")

        if len(doctor["languages"]) > 1:
            reasons.append(f"Multilingual: {', '.join(doctor['languages'])}")

        next_available = datetime.strptime(doctor["next_available"],
                                           "%Y-%m-%d %H:%M")
        if next_available <= datetime.now():
            reasons.append("Immediately available")

        return " • ".join(reasons)

    @trace(TraceOptions(trace_params=True, trace_return_value=True))
    def get_doctor_availability(self, doctor_id: str) -> Dict:
        """
        Get detailed availability for a specific doctor

        Args:
            doctor_id: Unique identifier for the doctor

        Returns:
            Dictionary with doctor's availability schedule
        """
        logger.info(f"Getting availability for doctor ID: {doctor_id}")
        for doctor in self.doctors_data["doctors"]:
            if doctor["id"] == doctor_id:
                logger.info(f"Found doctor: {doctor['name']}")
                return {
                    "name": doctor["name"],
                    "availability": doctor["availability"],
                    "next_available": doctor["next_available"]
                }
        logger.error(f"Doctor with ID {doctor_id} not found")
        raise ValueError(f"Doctor with ID {doctor_id} not found")


def create_scheduling_agent():
    return SchedulingAgent()
