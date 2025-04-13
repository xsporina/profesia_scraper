from datetime import datetime
import re
from sqlalchemy.orm import Session
from models.models import Contract, Job, Position, Technology


class DatabaseManager:
    def __init__(self):
        pass

    # @staticmethod
    def save_job_data(self, session: Session, data: dict):
        """
        Creates a job object,
        handles many-to-many relationships
        
        """
        # Job creation logic
        job = Job(
            ps_id=int(data['ps_id']),
            posted_at=datetime.strptime(data['posted_at'], '%d.%m.%Y'),
            location=data.get('location'),
            company=data.get('company'),
            salary_min=float(data['salary_min']) if data.get('salary_min') else None,
            salary_max=float(data['salary_max']) if data.get('salary_max') else None,
            salary_unit=data.get('salary_unit'),
            job_title=data.get('job_title'),
            home_office=data.get('home_office'),
            url=data.get('url')
        )

        # Handle relationships
        self._handle_relationships(session, job, data.get('position', []), Position, 'position')
        self._handle_relationships(session, job, data.get('contract_type', []), Contract, 'contract_type')
        self._handle_relationships(session, job, data.get('technologies', []), Technology, 'technologies')
        
        session.add(job)
        session.commit()
        return job
    
    def _handle_relationships(self, session: Session, job: Job, items: list, model: type, relation_attr: str):
        """
        Check if each model is already registered in database
        
        """
        seen = set()
        relationship = getattr(job, relation_attr)

        for item_name in items:
            if item_name in seen:
                continue
            seen.add(item_name)

            db_item = session.query(model).filter_by(name=item_name).first()
            if not db_item:
                db_item = model(name=item_name)
                session.add(db_item)
                session.flush()

            if db_item not in relationship:
                relationship.append(db_item)

    def check_duplicate(self, session: Session, url: str) -> bool:
        """
        Checks for a duplicate ps_id in database
        
        """
        # Extract ps_id from url
        match = re.search(r'/O(\d+)\?', url)

        # Check if ps_id already in database
        if match:
            ps_id = int(match.group(1))
            existing_job = session.query(Job).filter_by(ps_id=ps_id).first()
            if existing_job:
                print(f"Job with ps_id {ps_id} already exists, skipping.")
                return True
        
        return False