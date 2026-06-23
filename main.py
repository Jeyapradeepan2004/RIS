# ==========================
# Imports
# ==========================

from pypdf import PdfReader
from docx import Document
import sqlite3
import os

# ==========================
# Resume Intelligence System
# ==========================
class RIS:

# ==========================
# Constructor
# ==========================
    def __init__(self):

        self.con = sqlite3.connect("ris.db")
        self.cur = self.con.cursor()

        self.create_tables()

        self.skill_list = [
            "python",
            "sql",
            "pandas",
            "fastapi",
            "mongodb"
        ]
        
        self.job_skills = input(
        "Enter required skills (comma separated): "
        )

        self.job_skills = {
            skill.strip().lower()
            for skill in self.job_skills.split(",")
            if skill.strip()
        }

# ==========================
# Database Setup
# ==========================
    def create_tables(self):

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS resume(
            resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            resume_text TEXT
        )""")

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS skills(
            skills_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER,
            skill_name TEXT,
            FOREIGN KEY(resume_id)
                REFERENCES resume(resume_id)
        )""")

        self.con.commit()

# ==========================
# File Extraction Methods
# ==========================

    def extract_pdf_text(self, file_path):
        pdf_reader = PdfReader(file_path)

        text = ""

        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        return text

    def extract_docx_text(self, file_path):
        document = Document(file_path)

        return "\n".join(
            para.text
            for para in document.paragraphs
        )

    def extract_text(self, file_path):
        extension = os.path.splitext(
            file_path
        )[1].lower()

        if extension == ".pdf":
            return self.extract_pdf_text(file_path)

        if extension == ".docx":
            return self.extract_docx_text(file_path)

        raise ValueError(
            "Unsupported File Format"
        )

# ==========================
# Resume Management
# ==========================

    def add_resume(self):
        candidate_name = input(
            "Enter Candidate Name: "
        )

        resume_path = input(
            "Enter Resume Path: "
        )

        try:
            resume_text = self.extract_text(
                resume_path
            )

        except Exception as e:
            print(e)
            return

        self.cur.execute("""
            INSERT INTO resume(
                candidate_name,
                resume_text
            )
            VALUES (?, ?)
        """, (candidate_name, resume_text))

        resume_id = self.cur.lastrowid

        detected_skills = []

        text = resume_text.lower()

        for skill in self.skill_list:

            if skill in text:
                detected_skills.append(skill)

        for skill in detected_skills:

            self.cur.execute("""
                INSERT INTO skills(
                    resume_id,
                    skill_name
                )
                VALUES (?, ?)
            """, (resume_id, skill))

        self.con.commit()

        print(
            "Resume Added Successfully"
        )

    def view_resume(self):
        self.cur.execute("""
            SELECT
                resume_id,
                candidate_name
            FROM resume
        """)

        resumes = self.cur.fetchall()

        for row in resumes:
            print(row)

# ==========================
# Skill Processing
# ==========================

    def extract_skills(
        self,
        resume_id
    ):

        self.cur.execute("""
            SELECT skill_name
            FROM skills
            WHERE resume_id = ?
        """, (resume_id,))

        result = self.cur.fetchone()

        if result is None:
            return []

        resume_text = result[0].lower()

        found_skills = []

        for skill in self.skill_list:
            
            if skill in resume_text:
                found_skills.append(skill)
        return found_skills

    def search_skills(
        self,
        skill
    ):

        self.cur.execute("""
            SELECT
                resume_id,
                candidate_name
            FROM resume
            WHERE lower(
                resume_text
            ) LIKE ?
        """, (
            f"%{skill.lower()}%",
        ))

        candidates = self.cur.fetchall()

        for row in candidates:
            print(row)

# ==========================
# ATS Scoring
# ==========================

    def job_description(
        self,
        resume_id
    ):

        if not self.job_skills:
            
            return {
                "score": 0,
                "matched": [],
                "missed": []
            }
            
        candidate_skills = [
            skill.lower()
            for skill in self.extract_skills(
                resume_id
            )
        ]

        matches = (
            set(candidate_skills)
            & self.job_skills
        )

        score = (
            len(matches)
            / len(self.job_skills)
        ) * 100

        score = round(score, 2)

        return {
            "score": score,
            "matched": list(matches),
            "missed": list(
                self.job_skills - matches
            )
        }

    def candidates_ranking(self):

        self.cur.execute("""
            SELECT
                resume_id,
                candidate_name
            FROM resume
        """)

        candidates = self.cur.fetchall()

        rankings = []

        for (
            resume_id,
            candidate_name
        ) in candidates:

            score = (
                self.job_description(
                    resume_id
                )["score"]
            )

            rankings.append(
                (
                    candidate_name,
                    score
                )
            )

        rankings.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return rankings

# ==========================
# Statistics
# ==========================

    def statistics(self):

        self.cur.execute("""
            SELECT COUNT(*)
            FROM resume
        """)

        total_resumes = (
            self.cur.fetchone()[0]
        )

        self.cur.execute("""
            SELECT
                candidate_name,
                resume_id
            FROM resume
        """)

        candidates = (
            self.cur.fetchall()
        )

        scores = []

        for (
            candidate_name,
            resume_id
        ) in candidates:

            score = (
                self.job_description(
                    resume_id
                )["score"]
            )

            scores.append(score)

        average_score = (
            sum(scores)
            / len(scores)
            if scores
            else 0
        )

        print(
            f"Total Resumes: "
            f"{total_resumes}"
        )

        print(
            f"Average ATS Score: "
            f"{average_score:.2f}"
        )

    def skill_statistics(self):

        skill_count = {
            skill: 0
            for skill in self.skill_list
        }

        self.cur.execute("""
            SELECT resume_text
            FROM resume
        """)

        resumes = (
            self.cur.fetchall()
        )

        for resume in resumes:

            text = resume[0].lower()

            for skill in self.skill_list:
                if skill in text:
                    skill_count[
                        skill
                    ] += 1

        return skill_count

# ==========================
# Utility
# ==========================

    def close(self):
        self.con.close()


# ==========================
# Main Program
# ==========================

ris = RIS()

# ris.add_resume()

ris.view_resume()

# print(ris.extract_skills(1))

# print(ris.job_description(1))

# ris.search_skills("python")

# ris.statistics()

ris.close()
