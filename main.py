from pypdf import PdfReader
from docx import Document
import sqlite3
import os

class Ris:
    
    def __init__(self):
        self.con = sqlite3.connect('ris.db')
        self.cur = self.con.cursor()
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS resume(
                Resume_id INTEGER PRIMARY KEY AUTOINCREMENT,
                Candidate_name TEXT,
                Resume_text text
                )"""
            )
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS skills(
                skills_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                skill_name TEXT,
                FOREIGN KEY(resume_id) REFERENCES resume(resume_id)
                )"""
            )
        
        self.con.commit()
        self.skill_list = [
            'python',
            'SQL',
            'pandas',
            'fastapi',
            'mongodb'
            ]
        
        self.job_skills = input("Enter required skills Separated by comma: ")
        
        self.job_skills = {
            skill.strip().lower()
            for skill in self.job_skills.split(",")
            if skill.strip()
        }
        
    def extract_pdf_text(self,file_path):
        resume_pdf = PdfReader(file_path)
        
        text = ""
        
        for page in resume_pdf.pages:
            text += page.extract_text() + "\n"
            
        return text
    
    def extract_docx_text(self,file_path):
        doc = Document(file_path)
        
        text = "\n".join(
            para.text for para in doc.paragraphs
        )
        
        return text
        
    def extract_text(self, file_path):
        
        extension = os.path.splitext(file_path)[1].lower()
        
        if extension == ".pdf":
            return self.extract_pdf_text(file_path)
        
        elif extension == '.docx':
            return self.extract_docx_text(file_path)
        
        else:
            raise ValueError("Unsupported File Format")
        
    def close(self):
        self.con.close()
    
    def add_resume(self):
        name = input("Enter the Candidate Name: ")
        resume_path = input("Enter you Resume Path: ")
        
        try:
            resume = self.extract_text(resume_path)
        except Exception as e:
            print(e)
            return
        
        
        self.cur.execute("""
            INSERT INTO resume(candidate_name, resume_text)
            VALUES(?, ?)
            """, (name, resume))
        
        self.con.commit()
        
        print("Resume Added Successfully")
        
    def view_resume(self):
        self.cur.execute("""
            SELECT * FROM resume
            """
        )
        
        Data = self.cur.fetchall()
        
        for row in Data:
            print(row)
        
    def extract_skills(self, resume_id):
        
        
        self.cur.execute("""
            SELECT resume_text
            FROM resume
            WHERE resume_id = ?
            """, (resume_id,))
        
        result = self.cur.fetchone()
        
        if result is None:
            return []
        
        resume_text = result[0]
        
        found = []
        
        resume_text = resume_text.lower()
        
        for skill in self.skill_list:
            if skill.lower() in resume_text:
                found.append(skill)
                
        return found
    
    def job_description(self, resume_id):
        
        if not self.job_skills:
            return {
                'score':0,
                'matched':[],
                'missed':[]
            }
        
        candidate_skills = [
            skill.lower() for skill in self.extract_skills(resume_id)
            ]
        
        matches = set(candidate_skills) & set(self.job_skills)
        
        score = len(matches) / len(self.job_skills)* 100
        
        score = round(score, 2)
        
        matched = list(matches)
        
        missed = list(self.job_skills - matches)
            
        compare_skills = {
            'score': score,
            'matched': matched,
            'missed': missed
        }
            
        return compare_skills
    
    def search_skills(self, skill):
        
        self.cur.execute("""
            SELECT resume_id, candidate_name
            FROM  resume
            WHERE lower(resume_text) LIKE ?
            """, (f"%{skill.lower()}%",))
        
        result = self.cur.fetchall()
        
        for row in result:
            print(row)
            
    def candidates_ranking(self):
        
        self.cur.execute("""
            SELECT resume_id, candidate_name
            FROM resume
            """)
        
        data = self.cur.fetchall()
        
        rankings = []
        
        for resume_id, name in data:
            score = self.job_description(resume_id)["score"]
            
            rankings.append((name, score))
            
            
        rankings.sort(
            key=lambda x: x[1],
            reverse=True
        )
        return rankings
    
    def statistics(self):
        
        self.cur.execute("""
            SELECT COUNT(*)
            FROM resume
            """)
        total = self.cur.fetchone()[0]
        
        self.cur.execute("""
            SELECT candidate_name, resume_id
            FROM resume
            """,)
        
        data = self.cur.fetchall()
        
        scores = []
        
        for name, resume_id in data:
            score = self.job_description(resume_id)['score']
            scores.append(score)
            
        avg_score = sum(scores) / len(scores) if scores else 0
        
        print(f"Total Resume: {total}")
        print(f"Average ATS Score: {avg_score:.2f}")            
    
    def skill_statistics(self):
        skill_count = {}
        
        for skill in self.skill_list:
            skill_count[skill] = 0
            
        self.cur.execute("""
            SELECT resume_text
            FROM resume
            """)  
        
        resumes = self.cur.fetchall()
        
        for resume in resumes:
            
            text = resume[0].lower()
            
            for skill in self.skill_list:
                if skill in text:
                    skill_count[skill] += 1
                    
        return skill_count

    
    
    
    
    
    
    
ris = Ris()
# ris.add_resume()
# ris.view_resume()
# print(ris.extract_skills())
# print(ris.job_description(1))
# ris.search_skills('python')
# ris.statistics()
print(ris.skill_statistics())
ris.close()
